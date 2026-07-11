//! Agent runtime — identities and registry.
//!
//! Agents are *temporary workers*; the daemon is the permanent substrate. An
//! agent has a scoped identity ([`AgentIdentity`]) describing exactly what it is
//! allowed to see and do. Agents never communicate with one another directly —
//! they publish/subscribe on the [`crate::event_bus`] and request privileges
//! through the [`crate::broker`]. The [`AgentRegistry`] is the daemon's roster
//! of live agents.

use std::collections::HashMap;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::broker::CapabilityToken;

/// How much the daemon trusts an agent. Higher levels widen what the broker
/// will auto-approve.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum TrustLevel {
    Untrusted,
    Low,
    Medium,
    High,
    System,
}

/// A scoped, auditable agent identity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentIdentity {
    pub id: String,
    pub name: String,
    /// What the agent is specialised for (e.g. "code-review", "research").
    pub specialization: String,
    /// Capabilities the agent may request from the broker.
    pub capabilities: Vec<CapabilityToken>,
    /// Memory kinds/tags this agent may read (empty = daemon default scope).
    pub memory_scope: Vec<String>,
    /// Workspace node ids this agent may touch (empty = none).
    pub workspace_scope: Vec<String>,
    pub trust_level: TrustLevel,
    /// Human-readable audit trail of notable events.
    pub audit_trail: Vec<String>,
    /// History of executed actions.
    pub execution_history: Vec<String>,
    pub started_at: DateTime<Utc>,
}

impl AgentIdentity {
    pub fn new(name: impl Into<String>, specialization: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            name: name.into(),
            specialization: specialization.into(),
            capabilities: Vec::new(),
            memory_scope: Vec::new(),
            workspace_scope: Vec::new(),
            trust_level: TrustLevel::Low,
            audit_trail: Vec::new(),
            execution_history: Vec::new(),
            started_at: Utc::now(),
        }
    }

    pub fn with_capabilities(mut self, caps: Vec<CapabilityToken>) -> Self {
        self.capabilities = caps;
        self
    }

    pub fn with_trust(mut self, trust: TrustLevel) -> Self {
        self.trust_level = trust;
        self
    }

    pub fn note(&mut self, msg: impl Into<String>) {
        self.audit_trail
            .push(format!("{} {}", Utc::now().to_rfc3339(), msg.into()));
    }

    pub fn record_execution(&mut self, msg: impl Into<String>) {
        self.execution_history
            .push(format!("{} {}", Utc::now().to_rfc3339(), msg.into()));
    }
}

/// The daemon's roster of live agents.
#[derive(Default)]
pub struct AgentRegistry {
    agents: HashMap<String, AgentIdentity>,
}

impl AgentRegistry {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register (spawn) an agent. Returns its id.
    pub fn register(&mut self, agent: AgentIdentity) -> String {
        let id = agent.id.clone();
        self.agents.insert(id.clone(), agent);
        id
    }

    /// Deregister (stop) an agent. Returns the removed identity.
    pub fn deregister(&mut self, id: &str) -> Option<AgentIdentity> {
        self.agents.remove(id)
    }

    pub fn get(&self, id: &str) -> Option<&AgentIdentity> {
        self.agents.get(id)
    }

    pub fn get_mut(&mut self, id: &str) -> Option<&mut AgentIdentity> {
        self.agents.get_mut(id)
    }

    pub fn list(&self) -> Vec<AgentIdentity> {
        self.agents.values().cloned().collect()
    }

    pub fn len(&self) -> usize {
        self.agents.len()
    }

    pub fn is_empty(&self) -> bool {
        self.agents.is_empty()
    }
}
