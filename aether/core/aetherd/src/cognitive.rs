//! Lightweight cognitive engines.
//!
//! * [`AttentionEngine`] — a priority queue scoring items by importance,
//!   urgency and novelty so the daemon knows what to think about next.
//! * [`CuriosityEngine`] — periodically scans for gaps and emits investigation
//!   tasks (as events).
//! * [`MemoryConsolidator`] — periodic summarisation that compresses raw
//!   episodic memory into higher-level reflections.

use serde::{Deserialize, Serialize};

use crate::event_bus::Event;
use crate::memory::{MemoryGraph, MemoryKind};

// ── Attention ──────────────────────────────────────────────────────────────

/// A candidate the daemon could focus on.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AttentionItem {
    pub id: String,
    pub description: String,
    pub importance: f32,
    pub urgency: f32,
    pub novelty: f32,
    /// Combined salience score (computed by the engine).
    pub score: f32,
}

/// A salience-ordered attention queue.
#[derive(Default)]
pub struct AttentionEngine {
    items: Vec<AttentionItem>,
}

impl AttentionEngine {
    pub fn new() -> Self {
        Self::default()
    }

    /// Salience weighting: importance dominates, urgency next, novelty a spice.
    fn salience(importance: f32, urgency: f32, novelty: f32) -> f32 {
        0.5 * importance + 0.35 * urgency + 0.15 * novelty
    }

    /// Push a scored item and keep the queue ordered by descending salience.
    pub fn push(
        &mut self,
        id: impl Into<String>,
        description: impl Into<String>,
        importance: f32,
        urgency: f32,
        novelty: f32,
    ) {
        let score = Self::salience(importance, urgency, novelty);
        self.items.push(AttentionItem {
            id: id.into(),
            description: description.into(),
            importance,
            urgency,
            novelty,
            score,
        });
        self.items
            .sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap_or(std::cmp::Ordering::Equal));
    }

    /// Peek the current focus (highest salience) without removing it.
    pub fn focus(&self) -> Option<&AttentionItem> {
        self.items.first()
    }

    /// Pop and return the highest-salience item.
    pub fn next_focus(&mut self) -> Option<AttentionItem> {
        if self.items.is_empty() {
            None
        } else {
            Some(self.items.remove(0))
        }
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}

// ── Curiosity ──────────────────────────────────────────────────────────────

/// Scans the memory graph for gaps and proposes investigations.
#[derive(Default)]
pub struct CuriosityEngine;

impl CuriosityEngine {
    pub fn new() -> Self {
        Self
    }

    /// A single scan pass. Returns investigation tasks encoded as
    /// [`Event::GoalCreated`] events the daemon can publish. The heuristic:
    /// if there are episodic memories but few reflections, suggest reflecting.
    pub fn scan(&self, memory: &MemoryGraph) -> Vec<Event> {
        let episodic = memory.query("", Some(MemoryKind::Episodic), 1000).len();
        let reflections = memory.query("", Some(MemoryKind::Reflection), 1000).len();
        let mut out = Vec::new();
        if episodic > 0 && reflections * 5 < episodic {
            out.push(Event::GoalCreated {
                goal_id: uuid::Uuid::new_v4().to_string(),
                description: format!(
                    "Investigate: {episodic} episodic memories but only {reflections} \
                     reflections — consolidate learnings"
                ),
            });
        }
        out
    }
}

// ── Consolidation ──────────────────────────────────────────────────────────

/// Compresses raw memory into summaries (nightly/periodic).
#[derive(Default)]
pub struct MemoryConsolidator;

impl MemoryConsolidator {
    pub fn new() -> Self {
        Self
    }

    /// Consolidate: summarise the top episodic memories and store the result
    /// back as a reflection memory. Returns the new reflection's id, if any.
    pub fn consolidate(&self, memory: &MemoryGraph) -> anyhow::Result<Option<String>> {
        if memory.query("", Some(MemoryKind::Episodic), 1).is_empty() {
            return Ok(None);
        }
        let summary = memory.summarize(MemoryKind::Episodic, 20);
        let mut node = crate::memory::MemoryNode::new(MemoryKind::Reflection, summary);
        node.importance = 0.7;
        node.confidence = 0.6;
        let id = memory.add(node)?;
        Ok(Some(id))
    }
}
