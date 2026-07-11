// SPDX-License-Identifier: MIT OR Apache-2.0
//! Multi-agent coordinator.
//!
//! Coordinates multiple AI agents across virtual workspaces:
//!
//! - Agent registration with workspace assignment
//! - Inter-agent message passing via the Brain daemon's memory store
//! - Task delegation: one agent hands work off to another on a different workspace
//! - Conflict resolution: two agents competing for the same resource
//! - Shared clipboard namespace: agents exchange data via tagged Brain memories
//! - Agent bus: tokio broadcast channel used as a pub/sub event bus for workspace events
//!
//! The coordinator runs as a long-lived async actor.  External callers interact
//! with it through an [`CoordinatorHandle`] which is backed by an mpsc channel.

use std::{
    collections::{HashMap, VecDeque},
    sync::Arc,
    time::Duration,
};

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::{
    sync::{broadcast, mpsc, Mutex, RwLock},
    time::timeout,
};
use tracing::{debug, info, warn, error};
use uuid::Uuid;
use zbus::Connection;

// ─── Public event type (agent bus) ────────────────────────────────────────────

/// Events broadcast on the agent bus.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WorkspaceEvent {
    /// An agent switched to a different workspace.
    AgentMoved { agent_id: String, from: u32, to: u32 },
    /// A task was delegated between agents.
    TaskDelegated {
        task_id: String,
        from_agent: String,
        to_agent: String,
        workspace: u32,
    },
    /// A workspace context was updated.
    ContextUpdated { workspace: u32, by: String },
    /// An application was launched on a workspace.
    AppLaunched { workspace: u32, pid: u32, command: String },
    /// A resource conflict was detected.
    ConflictDetected {
        resource: String,
        agents: Vec<String>,
        resolution: ConflictResolution,
    },
    /// Arbitrary agent-to-agent message.
    AgentMessage {
        from: String,
        to: Option<String>, // None = broadcast
        payload: serde_json::Value,
    },
    /// Shared clipboard entry was written by an agent.
    ClipboardWrite { tag: String, by: String },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ConflictResolution {
    /// The higher-priority agent wins.
    PriorityWins { winner: String },
    /// The first agent to lock the resource keeps it.
    FirstComeFirstServed { winner: String },
    /// Both agents are asked to retry after a random back-off.
    Backoff,
}

// ─── Task delegation ──────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DelegationTask {
    pub id: String,
    pub from_agent: String,
    pub to_agent: String,
    pub workspace: u32,
    pub description: String,
    pub payload: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub status: TaskStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum TaskStatus {
    Pending,
    Accepted,
    InProgress,
    Completed,
    Failed,
    Cancelled,
}

// ─── Agent registry entry ─────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentRecord {
    pub id: String,
    pub workspace: u32,
    /// Priority (higher = preferred in conflicts).
    pub priority: u8,
    pub capabilities: Vec<String>,
    pub registered_at: DateTime<Utc>,
    pub last_seen: DateTime<Utc>,
}

// ─── Shared clipboard ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClipboardEntry {
    pub tag: String,
    pub content: String,
    pub written_by: String,
    pub written_at: DateTime<Utc>,
}

// ─── Resource lock ────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
struct ResourceLock {
    resource: String,
    holder: String,
    acquired_at: DateTime<Utc>,
}

// ─── Coordinator state ────────────────────────────────────────────────────────

struct CoordinatorState {
    agents: HashMap<String, AgentRecord>,
    tasks: HashMap<String, DelegationTask>,
    clipboard: HashMap<String, ClipboardEntry>,
    resource_locks: HashMap<String, ResourceLock>,
    event_tx: broadcast::Sender<WorkspaceEvent>,
}

impl CoordinatorState {
    fn new(event_tx: broadcast::Sender<WorkspaceEvent>) -> Self {
        Self {
            agents: HashMap::new(),
            tasks: HashMap::new(),
            clipboard: HashMap::new(),
            resource_locks: HashMap::new(),
            event_tx,
        }
    }

    fn broadcast(&self, event: WorkspaceEvent) {
        let _ = self.event_tx.send(event);
    }
}

// ─── Commands sent to the coordinator actor ───────────────────────────────────

enum CoordCmd {
    RegisterAgent {
        record: AgentRecord,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    UnregisterAgent {
        agent_id: String,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    AssignWorkspace {
        agent_id: String,
        workspace: u32,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    GetAgentWorkspace {
        agent_id: String,
        reply: tokio::sync::oneshot::Sender<Option<u32>>,
    },
    DelegateTask {
        task: DelegationTask,
        reply: tokio::sync::oneshot::Sender<Result<String>>,
    },
    UpdateTaskStatus {
        task_id: String,
        status: TaskStatus,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    GetTask {
        task_id: String,
        reply: tokio::sync::oneshot::Sender<Option<DelegationTask>>,
    },
    SendMessage {
        from: String,
        to: Option<String>,
        payload: serde_json::Value,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    WriteClipboard {
        tag: String,
        content: String,
        by: String,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    ReadClipboard {
        tag: String,
        reply: tokio::sync::oneshot::Sender<Option<ClipboardEntry>>,
    },
    AcquireResource {
        resource: String,
        agent_id: String,
        reply: tokio::sync::oneshot::Sender<Result<bool>>,
    },
    ReleaseResource {
        resource: String,
        agent_id: String,
        reply: tokio::sync::oneshot::Sender<Result<()>>,
    },
    ListAgents {
        reply: tokio::sync::oneshot::Sender<Vec<AgentRecord>>,
    },
    BroadcastEvent {
        event: WorkspaceEvent,
        reply: tokio::sync::oneshot::Sender<()>,
    },
}

// ─── Coordinator actor ────────────────────────────────────────────────────────

async fn coordinator_actor(mut rx: mpsc::Receiver<CoordCmd>, mut state: CoordinatorState) {
    while let Some(cmd) = rx.recv().await {
        match cmd {
            CoordCmd::RegisterAgent { record, reply } => {
                info!(agent_id = %record.id, workspace = record.workspace, "registering agent");
                state.agents.insert(record.id.clone(), record);
                let _ = reply.send(Ok(()));
            }

            CoordCmd::UnregisterAgent { agent_id, reply } => {
                state.agents.remove(&agent_id);
                // Release all locks held by this agent.
                state.resource_locks.retain(|_, l| l.holder != agent_id);
                info!(agent_id, "unregistered agent");
                let _ = reply.send(Ok(()));
            }

            CoordCmd::AssignWorkspace { agent_id, workspace, reply } => {
                if let Some(record) = state.agents.get_mut(&agent_id) {
                    let from = record.workspace;
                    record.workspace = workspace;
                    state.broadcast(WorkspaceEvent::AgentMoved {
                        agent_id: agent_id.clone(),
                        from,
                        to: workspace,
                    });
                    let _ = reply.send(Ok(()));
                } else {
                    let _ = reply.send(Err(anyhow::anyhow!("agent {agent_id} not registered")));
                }
            }

            CoordCmd::GetAgentWorkspace { agent_id, reply } => {
                let ws = state.agents.get(&agent_id).map(|r| r.workspace);
                let _ = reply.send(ws);
            }

            CoordCmd::DelegateTask { task, reply } => {
                let id = task.id.clone();
                // Verify both agents exist.
                if !state.agents.contains_key(&task.to_agent) {
                    let _ = reply.send(Err(anyhow::anyhow!(
                        "target agent {} not registered",
                        task.to_agent
                    )));
                    continue;
                }
                state.broadcast(WorkspaceEvent::TaskDelegated {
                    task_id: id.clone(),
                    from_agent: task.from_agent.clone(),
                    to_agent: task.to_agent.clone(),
                    workspace: task.workspace,
                });
                // Persist the delegation as a Brain memory.
                let payload = serde_json::to_string(&task).unwrap_or_default();
                let task_id_clone = id.clone();
                tokio::spawn(async move {
                    let _ = store_brain_memory(
                        &payload,
                        &[
                            format!("task:{task_id_clone}"),
                            "delegation".to_string(),
                        ],
                    )
                    .await;
                });
                state.tasks.insert(id.clone(), task);
                let _ = reply.send(Ok(id));
            }

            CoordCmd::UpdateTaskStatus { task_id, status, reply } => {
                match state.tasks.get_mut(&task_id) {
                    Some(task) => {
                        task.status = status;
                        let _ = reply.send(Ok(()));
                    }
                    None => {
                        let _ = reply.send(Err(anyhow::anyhow!("task {task_id} not found")));
                    }
                }
            }

            CoordCmd::GetTask { task_id, reply } => {
                let _ = reply.send(state.tasks.get(&task_id).cloned());
            }

            CoordCmd::SendMessage { from, to, payload, reply } => {
                state.broadcast(WorkspaceEvent::AgentMessage {
                    from,
                    to,
                    payload,
                });
                let _ = reply.send(Ok(()));
            }

            CoordCmd::WriteClipboard { tag, content, by, reply } => {
                state.clipboard.insert(
                    tag.clone(),
                    ClipboardEntry {
                        tag: tag.clone(),
                        content,
                        written_by: by.clone(),
                        written_at: Utc::now(),
                    },
                );
                state.broadcast(WorkspaceEvent::ClipboardWrite { tag, by });
                let _ = reply.send(Ok(()));
            }

            CoordCmd::ReadClipboard { tag, reply } => {
                let _ = reply.send(state.clipboard.get(&tag).cloned());
            }

            CoordCmd::AcquireResource { resource, agent_id, reply } => {
                // Clone out of the borrow before mutating — the presence check
                // must not hold an immutable borrow across the .insert below.
                let existing_lock = state.resource_locks.get(&resource).cloned();
                let result = if let Some(existing) = existing_lock {
                    if existing.holder == agent_id {
                        // Re-entrant — same agent.
                        true
                    } else {
                        // Conflict: determine resolution by priority.
                        let existing_priority = state
                            .agents
                            .get(&existing.holder)
                            .map(|r| r.priority)
                            .unwrap_or(0);
                        let new_priority = state
                            .agents
                            .get(&agent_id)
                            .map(|r| r.priority)
                            .unwrap_or(0);

                        if new_priority > existing_priority {
                            // Preempt: give lock to higher-priority agent.
                            let winner = agent_id.clone();
                            state.resource_locks.insert(
                                resource.clone(),
                                ResourceLock {
                                    resource: resource.clone(),
                                    holder: agent_id.clone(),
                                    acquired_at: Utc::now(),
                                },
                            );
                            state.broadcast(WorkspaceEvent::ConflictDetected {
                                resource: resource.clone(),
                                agents: vec![existing.holder.clone(), agent_id],
                                resolution: ConflictResolution::PriorityWins { winner },
                            });
                            true
                        } else {
                            // Deny — first-come-first-served.
                            state.broadcast(WorkspaceEvent::ConflictDetected {
                                resource: resource.clone(),
                                agents: vec![existing.holder.clone(), agent_id],
                                resolution: ConflictResolution::FirstComeFirstServed {
                                    winner: existing.holder.clone(),
                                },
                            });
                            false
                        }
                    }
                } else {
                    state.resource_locks.insert(
                        resource.clone(),
                        ResourceLock {
                            resource,
                            holder: agent_id,
                            acquired_at: Utc::now(),
                        },
                    );
                    true
                };
                let _ = reply.send(Ok(result));
            }

            CoordCmd::ReleaseResource { resource, agent_id, reply } => {
                match state.resource_locks.get(&resource) {
                    Some(lock) if lock.holder == agent_id => {
                        state.resource_locks.remove(&resource);
                        let _ = reply.send(Ok(()));
                    }
                    Some(_) => {
                        let _ = reply.send(Err(anyhow::anyhow!(
                            "agent {agent_id} does not hold resource {resource}"
                        )));
                    }
                    None => {
                        let _ = reply.send(Ok(())); // already released
                    }
                }
            }

            CoordCmd::ListAgents { reply } => {
                let agents: Vec<AgentRecord> = state.agents.values().cloned().collect();
                let _ = reply.send(agents);
            }

            CoordCmd::BroadcastEvent { event, reply } => {
                state.broadcast(event);
                let _ = reply.send(());
            }
        }
    }
}

// ─── Handle ───────────────────────────────────────────────────────────────────

/// Cloneable handle used by callers to interact with the coordinator actor.
#[derive(Clone)]
pub struct CoordinatorHandle {
    tx: mpsc::Sender<CoordCmd>,
    pub event_rx: Arc<broadcast::Sender<WorkspaceEvent>>,
}

impl CoordinatorHandle {
    pub async fn register_agent(&self, record: AgentRecord) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx.send(CoordCmd::RegisterAgent { record, reply: tx }).await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn unregister_agent(&self, agent_id: &str) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::UnregisterAgent {
                agent_id: agent_id.to_string(),
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn assign_workspace(&self, agent_id: &str, workspace: u32) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::AssignWorkspace {
                agent_id: agent_id.to_string(),
                workspace,
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn get_agent_workspace(&self, agent_id: &str) -> Option<u32> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        let _ = self
            .tx
            .send(CoordCmd::GetAgentWorkspace {
                agent_id: agent_id.to_string(),
                reply: tx,
            })
            .await;
        rx.await.ok().flatten()
    }

    pub async fn delegate_task(
        &self,
        from_agent: &str,
        to_agent: &str,
        workspace: u32,
        description: &str,
        payload: serde_json::Value,
    ) -> Result<String> {
        let task = DelegationTask {
            id: Uuid::new_v4().to_string(),
            from_agent: from_agent.to_string(),
            to_agent: to_agent.to_string(),
            workspace,
            description: description.to_string(),
            payload,
            created_at: Utc::now(),
            status: TaskStatus::Pending,
        };
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx.send(CoordCmd::DelegateTask { task, reply: tx }).await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn update_task_status(&self, task_id: &str, status: TaskStatus) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::UpdateTaskStatus {
                task_id: task_id.to_string(),
                status,
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn get_task(&self, task_id: &str) -> Option<DelegationTask> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        let _ = self
            .tx
            .send(CoordCmd::GetTask {
                task_id: task_id.to_string(),
                reply: tx,
            })
            .await;
        rx.await.ok().flatten()
    }

    pub async fn send_agent_message(
        &self,
        from: &str,
        to: Option<&str>,
        payload: serde_json::Value,
    ) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::SendMessage {
                from: from.to_string(),
                to: to.map(str::to_string),
                payload,
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn write_clipboard(&self, tag: &str, content: String, by: &str) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::WriteClipboard {
                tag: tag.to_string(),
                content,
                by: by.to_string(),
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn read_clipboard(&self, tag: &str) -> Option<ClipboardEntry> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        let _ = self
            .tx
            .send(CoordCmd::ReadClipboard {
                tag: tag.to_string(),
                reply: tx,
            })
            .await;
        rx.await.ok().flatten()
    }

    pub async fn acquire_resource(&self, resource: &str, agent_id: &str) -> Result<bool> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::AcquireResource {
                resource: resource.to_string(),
                agent_id: agent_id.to_string(),
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn release_resource(&self, resource: &str, agent_id: &str) -> Result<()> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        self.tx
            .send(CoordCmd::ReleaseResource {
                resource: resource.to_string(),
                agent_id: agent_id.to_string(),
                reply: tx,
            })
            .await?;
        rx.await.context("coordinator dropped")?
    }

    pub async fn list_agents(&self) -> Vec<AgentRecord> {
        let (tx, rx) = tokio::sync::oneshot::channel();
        let _ = self.tx.send(CoordCmd::ListAgents { reply: tx }).await;
        rx.await.unwrap_or_default()
    }

    pub async fn broadcast_event(&self, event: WorkspaceEvent) {
        let (tx, rx) = tokio::sync::oneshot::channel();
        let _ = self
            .tx
            .send(CoordCmd::BroadcastEvent { event, reply: tx })
            .await;
        let _ = rx.await;
    }

    /// Subscribe to the agent event bus.  Each receiver gets every event.
    pub fn subscribe(&self) -> broadcast::Receiver<WorkspaceEvent> {
        self.event_rx.subscribe()
    }
}

// ─── Spawn ────────────────────────────────────────────────────────────────────

/// Spawn the coordinator actor and return a handle to it.
pub fn spawn_coordinator() -> CoordinatorHandle {
    let (event_tx, _) = broadcast::channel(1024);
    let (cmd_tx, cmd_rx) = mpsc::channel(256);

    let state = CoordinatorState::new(event_tx.clone());
    tokio::spawn(coordinator_actor(cmd_rx, state));

    CoordinatorHandle {
        tx: cmd_tx,
        event_rx: Arc::new(event_tx),
    }
}

// ─── Brain helpers ────────────────────────────────────────────────────────────

async fn store_brain_memory(content: &str, tags: &[String]) -> Result<()> {
    let conn = Connection::session()
        .await
        .context("session bus")?;
    conn.call_method(
        Some("org.synthex.Brain"),
        "/org/synthex/Brain",
        Some("org.synthex.Brain"),
        "StoreMemory",
        &(content, tags),
    )
    .await
    .context("StoreMemory call")?;
    Ok(())
}
