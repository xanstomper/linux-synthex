//! The [`Daemon`] — the shared state of the Central Consciousness Daemon.
//!
//! Every subsystem lives here behind interior mutability so it can be shared
//! (`Arc<Daemon>`) across the API server and background cognition tasks. We use
//! `std::sync` locks because all critical sections are short and synchronous —
//! no lock is ever held across an `.await`.

use std::sync::{Arc, RwLock};

use crate::agent::AgentRegistry;
use crate::broker::Broker;
use crate::cognitive::{AttentionEngine, CuriosityEngine, MemoryConsolidator};
use crate::event_bus::EventBus;
use crate::memory::MemoryGraph;
use crate::planning::PlanningEngine;
use crate::reflection::ReflectionEngine;

/// The permanent intelligence substrate. Cheap to share via `Arc`.
pub struct Daemon {
    pub event_bus: EventBus,
    pub memory: Arc<MemoryGraph>,
    pub workspace: RwLock<crate::workspace::WorkspaceGraph>,
    pub planning: RwLock<PlanningEngine>,
    pub reflection: ReflectionEngine,
    pub broker: RwLock<Broker>,
    pub agents: RwLock<AgentRegistry>,
    pub attention: RwLock<AttentionEngine>,
    pub curiosity: CuriosityEngine,
    pub consolidator: MemoryConsolidator,
}

impl Daemon {
    /// Build the daemon around an already-opened memory graph.
    pub fn new(memory: Arc<MemoryGraph>) -> Self {
        Self {
            event_bus: EventBus::new(1024),
            memory,
            workspace: RwLock::new(crate::workspace::WorkspaceGraph::new()),
            planning: RwLock::new(PlanningEngine::new()),
            reflection: ReflectionEngine::new(),
            // 20 requests / 60s window; sensitive tokens require approval.
            broker: RwLock::new(Broker::new(20, 60, true)),
            agents: RwLock::new(AgentRegistry::new()),
            attention: RwLock::new(AttentionEngine::new()),
            curiosity: CuriosityEngine::new(),
            consolidator: MemoryConsolidator::new(),
        }
    }
}
