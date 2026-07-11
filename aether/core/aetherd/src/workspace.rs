//! Workspace graph — a live model of the user's world.
//!
//! Where [`crate::memory`] holds cognition, the workspace graph holds the
//! *structure* the daemon reasons about: projects, repos, files, tasks, goals,
//! agents, conversations, documents, people and services, plus the typed edges
//! between them (reusing [`RelationKind`]). It answers structural questions such
//! as "what depends on X" and "what is blocked".

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::memory::RelationKind;

/// The kind of entity a workspace node represents.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkspaceKind {
    Project,
    Repo,
    File,
    Task,
    Goal,
    Agent,
    Conversation,
    Document,
    Person,
    Service,
}

impl WorkspaceKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            WorkspaceKind::Project => "Project",
            WorkspaceKind::Repo => "Repo",
            WorkspaceKind::File => "File",
            WorkspaceKind::Task => "Task",
            WorkspaceKind::Goal => "Goal",
            WorkspaceKind::Agent => "Agent",
            WorkspaceKind::Conversation => "Conversation",
            WorkspaceKind::Document => "Document",
            WorkspaceKind::Person => "Person",
            WorkspaceKind::Service => "Service",
        }
    }
}

/// A node in the workspace graph.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceNode {
    pub id: String,
    pub kind: WorkspaceKind,
    pub name: String,
    /// Free-form attributes (path, url, status, …).
    pub attrs: HashMap<String, String>,
}

impl WorkspaceNode {
    pub fn new(kind: WorkspaceKind, name: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            kind,
            name: name.into(),
            attrs: HashMap::new(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceEdge {
    pub from_id: String,
    pub to_id: String,
    pub kind: RelationKind,
}

/// The workspace graph itself. Purely in-memory for the MVP.
#[derive(Default)]
pub struct WorkspaceGraph {
    nodes: HashMap<String, WorkspaceNode>,
    edges: Vec<WorkspaceEdge>,
}

impl WorkspaceGraph {
    pub fn new() -> Self {
        Self::default()
    }

    /// Add a node, returning its id.
    pub fn add(&mut self, node: WorkspaceNode) -> String {
        let id = node.id.clone();
        self.nodes.insert(id.clone(), node);
        id
    }

    pub fn get(&self, id: &str) -> Option<&WorkspaceNode> {
        self.nodes.get(id)
    }

    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }

    /// Connect two nodes with a typed edge.
    pub fn relate(&mut self, from_id: &str, to_id: &str, kind: RelationKind) {
        self.edges.push(WorkspaceEdge {
            from_id: from_id.to_string(),
            to_id: to_id.to_string(),
            kind,
        });
    }

    /// "What depends on X" — every node that has a `DEPENDS_ON` edge pointing
    /// at `id`.
    pub fn dependents_of(&self, id: &str) -> Vec<&WorkspaceNode> {
        self.edges
            .iter()
            .filter(|e| e.kind == RelationKind::DependsOn && e.to_id == id)
            .filter_map(|e| self.nodes.get(&e.from_id))
            .collect()
    }

    /// The inverse: everything `id` depends on.
    pub fn dependencies_of(&self, id: &str) -> Vec<&WorkspaceNode> {
        self.edges
            .iter()
            .filter(|e| e.kind == RelationKind::DependsOn && e.from_id == id)
            .filter_map(|e| self.nodes.get(&e.to_id))
            .collect()
    }

    /// "What is blocked" — every node on the `from` side of a `BLOCKED_BY` edge.
    pub fn blocked(&self) -> Vec<&WorkspaceNode> {
        let mut out: Vec<&WorkspaceNode> = self
            .edges
            .iter()
            .filter(|e| e.kind == RelationKind::BlockedBy)
            .filter_map(|e| self.nodes.get(&e.from_id))
            .collect();
        out.sort_by(|a, b| a.id.cmp(&b.id));
        out.dedup_by(|a, b| a.id == b.id);
        out
    }

    /// All nodes of a given kind.
    pub fn of_kind(&self, kind: WorkspaceKind) -> Vec<&WorkspaceNode> {
        self.nodes.values().filter(|n| n.kind == kind).collect()
    }
}
