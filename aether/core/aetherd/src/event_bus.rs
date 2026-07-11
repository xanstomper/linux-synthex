//! In-process event bus.
//!
//! Stands in for a distributed message broker (NATS/JetStream in the full
//! design). Every subsystem inside `aetherd` — and every agent, indirectly —
//! communicates by publishing and subscribing to [`Event`]s. Agents never talk
//! to each other directly; they emit events and the daemon routes them.
//!
//! Implemented on top of `tokio::sync::broadcast` so any number of subscribers
//! each receive their own copy of every event.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::sync::broadcast;

/// The canonical event vocabulary understood by the daemon.
///
/// Serialised with an internally-tagged representation so it is stable on the
/// wire (`{"type":"FileCreated","data":{...}}`).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum Event {
    FileCreated { path: String },
    FileModified { path: String },
    TaskCompleted { task_id: String, success: bool },
    AgentStarted { agent_id: String },
    AgentStopped { agent_id: String },
    GoalCreated { goal_id: String, description: String },
    MemoryAdded { memory_id: String },
    ToolUsed { agent_id: String, tool: String },
    ErrorOccurred { source: String, message: String },
    PlanUpdated { plan_id: String },
}

impl Event {
    /// Short, stable kind label used for logging and metrics.
    pub fn kind(&self) -> &'static str {
        match self {
            Event::FileCreated { .. } => "FileCreated",
            Event::FileModified { .. } => "FileModified",
            Event::TaskCompleted { .. } => "TaskCompleted",
            Event::AgentStarted { .. } => "AgentStarted",
            Event::AgentStopped { .. } => "AgentStopped",
            Event::GoalCreated { .. } => "GoalCreated",
            Event::MemoryAdded { .. } => "MemoryAdded",
            Event::ToolUsed { .. } => "ToolUsed",
            Event::ErrorOccurred { .. } => "ErrorOccurred",
            Event::PlanUpdated { .. } => "PlanUpdated",
        }
    }
}

/// An event with delivery metadata (timestamp + monotonic sequence number).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Envelope {
    pub seq: u64,
    pub at: DateTime<Utc>,
    pub event: Event,
}

/// Publish/subscribe hub. Cheap to `clone` — all clones share the same channel.
#[derive(Clone)]
pub struct EventBus {
    tx: broadcast::Sender<Envelope>,
    seq: std::sync::Arc<std::sync::atomic::AtomicU64>,
}

impl EventBus {
    /// Create a bus with the given per-subscriber buffer capacity.
    pub fn new(capacity: usize) -> Self {
        let (tx, _rx) = broadcast::channel(capacity.max(1));
        Self {
            tx,
            seq: std::sync::Arc::new(std::sync::atomic::AtomicU64::new(0)),
        }
    }

    /// Publish an event to all current subscribers. Returns the number of
    /// subscribers that received it (0 is not an error — nobody is listening).
    pub fn publish(&self, event: Event) -> usize {
        let seq = self
            .seq
            .fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let env = Envelope {
            seq,
            at: Utc::now(),
            event,
        };
        self.tx.send(env).unwrap_or(0)
    }

    /// Obtain a fresh subscriber handle. Only events published *after* the call
    /// are delivered.
    pub fn subscribe(&self) -> broadcast::Receiver<Envelope> {
        self.tx.subscribe()
    }

    /// Number of active subscribers.
    pub fn subscriber_count(&self) -> usize {
        self.tx.receiver_count()
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new(1024)
    }
}
