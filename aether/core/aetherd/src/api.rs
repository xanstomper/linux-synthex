//! Daemon API surface.
//!
//! MVP transport: newline-delimited JSON over TCP (no tonic/prost dependency).
//! The in-process contract is the [`DaemonApi`] trait, implemented for
//! [`Daemon`]; the TCP server is a thin adapter that parses [`ApiRequest`]s and
//! serialises [`ApiResponse`]s.

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::TcpListener;
use tracing::{debug, error, info};

use crate::agent::AgentIdentity;
use crate::daemon::Daemon;
use crate::event_bus::Event;
use crate::memory::{MemoryKind, MemoryNode};

/// The in-process API contract. Synchronous by design — every method touches
/// only short, non-blocking critical sections.
pub trait DaemonApi: Send + Sync {
    fn add_memory(
        &self,
        kind: MemoryKind,
        content: String,
        importance: Option<f32>,
    ) -> Result<String>;
    fn query_memory(&self, query: &str, limit: usize) -> Result<Vec<MemoryNode>>;
    fn create_goal(&self, description: String) -> Result<String>;
    fn list_agents(&self) -> Result<Vec<AgentIdentity>>;
    fn publish_event(&self, event: Event) -> Result<usize>;
}

impl DaemonApi for Daemon {
    fn add_memory(
        &self,
        kind: MemoryKind,
        content: String,
        importance: Option<f32>,
    ) -> Result<String> {
        let mut node = MemoryNode::new(kind, content);
        if let Some(i) = importance {
            node.importance = i.clamp(0.0, 1.0);
        }
        let id = self.memory.add(node)?;
        self.event_bus.publish(Event::MemoryAdded {
            memory_id: id.clone(),
        });
        Ok(id)
    }

    fn query_memory(&self, query: &str, limit: usize) -> Result<Vec<MemoryNode>> {
        Ok(self.memory.query(query, None, limit))
    }

    fn create_goal(&self, description: String) -> Result<String> {
        let gid = {
            let mut planning = self.planning.write().unwrap();
            let gid = planning.create_goal(description.clone());
            planning.decompose(&gid);
            gid
        };
        self.event_bus.publish(Event::GoalCreated {
            goal_id: gid.clone(),
            description,
        });
        Ok(gid)
    }

    fn list_agents(&self) -> Result<Vec<AgentIdentity>> {
        Ok(self.agents.read().unwrap().list())
    }

    fn publish_event(&self, event: Event) -> Result<usize> {
        Ok(self.event_bus.publish(event))
    }
}

// ── Wire protocol ───────────────────────────────────────────────────────────

/// A request over the JSON-line protocol.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum ApiRequest {
    Ping,
    AddMemory {
        kind: MemoryKind,
        content: String,
        #[serde(default)]
        importance: Option<f32>,
    },
    QueryMemory {
        query: String,
        #[serde(default)]
        limit: Option<usize>,
    },
    CreateGoal {
        description: String,
    },
    ListAgents,
    PublishEvent {
        event: Event,
    },
    Stats,
}

/// A response over the JSON-line protocol.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum ApiResponse {
    Pong,
    Ok { data: serde_json::Value },
    Error { message: String },
}

impl ApiResponse {
    fn ok<T: Serialize>(v: T) -> Self {
        match serde_json::to_value(v) {
            Ok(data) => ApiResponse::Ok { data },
            Err(e) => ApiResponse::Error {
                message: e.to_string(),
            },
        }
    }
}

/// Dispatch a single parsed request against the daemon.
pub fn dispatch(daemon: &Daemon, req: ApiRequest) -> ApiResponse {
    let result: Result<ApiResponse> = (|| {
        Ok(match req {
            ApiRequest::Ping => ApiResponse::Pong,
            ApiRequest::AddMemory {
                kind,
                content,
                importance,
            } => {
                let id = daemon.add_memory(kind, content, importance)?;
                ApiResponse::ok(serde_json::json!({ "memory_id": id }))
            }
            ApiRequest::QueryMemory { query, limit } => {
                let nodes = daemon.query_memory(&query, limit.unwrap_or(10))?;
                ApiResponse::ok(nodes)
            }
            ApiRequest::CreateGoal { description } => {
                let id = daemon.create_goal(description)?;
                ApiResponse::ok(serde_json::json!({ "goal_id": id }))
            }
            ApiRequest::ListAgents => ApiResponse::ok(daemon.list_agents()?),
            ApiRequest::PublishEvent { event } => {
                let n = daemon.publish_event(event)?;
                ApiResponse::ok(serde_json::json!({ "receivers": n }))
            }
            ApiRequest::Stats => ApiResponse::ok(serde_json::json!({
                "memories": daemon.memory.len(),
                "agents": daemon.agents.read().unwrap().len(),
                "goals": daemon.planning.read().unwrap().goals().len(),
                "workspace_nodes": daemon.workspace.read().unwrap().len(),
                "subscribers": daemon.event_bus.subscriber_count(),
            })),
        })
    })();

    match result {
        Ok(r) => r,
        Err(e) => ApiResponse::Error {
            message: e.to_string(),
        },
    }
}

/// Run the newline-delimited JSON TCP server until the process ends.
pub async fn serve(daemon: Arc<Daemon>, addr: &str) -> Result<()> {
    let listener = TcpListener::bind(addr).await?;
    info!(%addr, "AETHER API listening (newline-JSON over TCP)");
    loop {
        let (stream, peer) = match listener.accept().await {
            Ok(v) => v,
            Err(e) => {
                error!("accept failed: {e}");
                continue;
            }
        };
        let daemon = daemon.clone();
        tokio::spawn(async move {
            debug!(%peer, "client connected");
            let (rd, mut wr) = stream.into_split();
            let mut lines = BufReader::new(rd).lines();
            loop {
                match lines.next_line().await {
                    Ok(Some(line)) => {
                        if line.trim().is_empty() {
                            continue;
                        }
                        let resp = match serde_json::from_str::<ApiRequest>(&line) {
                            Ok(req) => dispatch(&daemon, req),
                            Err(e) => ApiResponse::Error {
                                message: format!("bad request: {e}"),
                            },
                        };
                        let mut out = serde_json::to_string(&resp).unwrap_or_else(|_| {
                            "{\"status\":\"error\",\"message\":\"serialize\"}".into()
                        });
                        out.push('\n');
                        if wr.write_all(out.as_bytes()).await.is_err() {
                            break;
                        }
                    }
                    Ok(None) => break, // client closed
                    Err(e) => {
                        debug!(%peer, "read error: {e}");
                        break;
                    }
                }
            }
            debug!(%peer, "client disconnected");
        });
    }
}
