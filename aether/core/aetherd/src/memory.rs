//! Memory graph — the long-term substrate of AETHER CORE.
//!
//! Memories are typed nodes ([`MemoryKind`]) connected by typed relations
//! ([`RelationKind`]). Everything is persisted in SQLite (via `rusqlite`) and
//! mirrored in an in-memory index for fast traversal and retrieval.
//!
//! # Thread-safety
//! `rusqlite::Connection` is `Send` but not `Sync`; wrapping it in a `Mutex`
//! makes the whole [`MemoryGraph`] `Sync`. Operations are short and run under
//! the lock, which is fine for the MVP's throughput.

use std::collections::HashMap;
use std::sync::{Mutex, RwLock};

use anyhow::{Context as _, Result};
use chrono::{DateTime, Duration, Utc};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// The category of a memory, mirroring cognitive-science memory systems.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MemoryKind {
    /// Time-stamped record of something that happened.
    Episodic,
    /// General facts and knowledge.
    Semantic,
    /// How-to knowledge / skills.
    Procedural,
    /// Short-lived scratch space for the current task.
    Working,
    /// Meta-cognition: insights derived from reviewing other memories.
    Reflection,
}

impl MemoryKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            MemoryKind::Episodic => "Episodic",
            MemoryKind::Semantic => "Semantic",
            MemoryKind::Procedural => "Procedural",
            MemoryKind::Working => "Working",
            MemoryKind::Reflection => "Reflection",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        Some(match s {
            "Episodic" => MemoryKind::Episodic,
            "Semantic" => MemoryKind::Semantic,
            "Procedural" => MemoryKind::Procedural,
            "Working" => MemoryKind::Working,
            "Reflection" => MemoryKind::Reflection,
            _ => return None,
        })
    }
}

/// Typed edges between memory nodes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum RelationKind {
    BelongsTo,
    DependsOn,
    RelatedTo,
    CreatedBy,
    DiscoveredBy,
    Mentions,
    Supersedes,
    PartOf,
    References,
    BlockedBy,
    Enables,
}

impl RelationKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            RelationKind::BelongsTo => "BELONGS_TO",
            RelationKind::DependsOn => "DEPENDS_ON",
            RelationKind::RelatedTo => "RELATED_TO",
            RelationKind::CreatedBy => "CREATED_BY",
            RelationKind::DiscoveredBy => "DISCOVERED_BY",
            RelationKind::Mentions => "MENTIONS",
            RelationKind::Supersedes => "SUPERSEDES",
            RelationKind::PartOf => "PART_OF",
            RelationKind::References => "REFERENCES",
            RelationKind::BlockedBy => "BLOCKED_BY",
            RelationKind::Enables => "ENABLES",
        }
    }

    pub fn parse(s: &str) -> Option<Self> {
        Some(match s {
            "BELONGS_TO" => RelationKind::BelongsTo,
            "DEPENDS_ON" => RelationKind::DependsOn,
            "RELATED_TO" => RelationKind::RelatedTo,
            "CREATED_BY" => RelationKind::CreatedBy,
            "DISCOVERED_BY" => RelationKind::DiscoveredBy,
            "MENTIONS" => RelationKind::Mentions,
            "SUPERSEDES" => RelationKind::Supersedes,
            "PART_OF" => RelationKind::PartOf,
            "REFERENCES" => RelationKind::References,
            "BLOCKED_BY" => RelationKind::BlockedBy,
            "ENABLES" => RelationKind::Enables,
            _ => return None,
        })
    }
}

/// A single memory.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryNode {
    pub id: String,
    pub kind: MemoryKind,
    pub content: String,
    /// Optional dense vector for semantic retrieval.
    pub embedding: Option<Vec<f32>>,
    pub timestamp: DateTime<Utc>,
    /// 0.0..=1.0 — how important this memory is; decays with age.
    pub importance: f32,
    /// 0.0..=1.0 — how confident the daemon is in this memory's correctness.
    pub confidence: f32,
}

impl MemoryNode {
    /// Convenience constructor with a fresh UUID and current timestamp.
    pub fn new(kind: MemoryKind, content: impl Into<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            kind,
            content: content.into(),
            embedding: None,
            timestamp: Utc::now(),
            importance: 0.5,
            confidence: 0.5,
        }
    }
}

/// A typed relation between two memories.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Relation {
    pub from_id: String,
    pub to_id: String,
    pub kind: RelationKind,
    pub weight: f32,
}


/// The persistent, in-memory-indexed memory graph.
pub struct MemoryGraph {
    db: Mutex<Connection>,
    index: RwLock<HashMap<String, MemoryNode>>,
    edges: RwLock<Vec<Relation>>,
}

impl MemoryGraph {
    /// Open (or create) the SQLite database, apply the schema, and warm the
    /// in-memory index from disk.
    pub fn open(path: &str) -> Result<Self> {
        let conn = Connection::open(path)
            .with_context(|| format!("open memory DB at {path}"))?;
        conn.execute_batch(
            r#"
            PRAGMA journal_mode = WAL;
            PRAGMA synchronous  = NORMAL;
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS memory_nodes (
                id          TEXT PRIMARY KEY,
                kind        TEXT NOT NULL,
                content     TEXT NOT NULL,
                embedding   TEXT,
                timestamp   TEXT NOT NULL,
                importance  REAL NOT NULL DEFAULT 0.5,
                confidence  REAL NOT NULL DEFAULT 0.5
            );

            CREATE TABLE IF NOT EXISTS memory_edges (
                from_id  TEXT NOT NULL REFERENCES memory_nodes(id) ON DELETE CASCADE,
                to_id    TEXT NOT NULL REFERENCES memory_nodes(id) ON DELETE CASCADE,
                kind     TEXT NOT NULL,
                weight   REAL NOT NULL DEFAULT 1.0,
                PRIMARY KEY (from_id, to_id, kind)
            );
            CREATE INDEX IF NOT EXISTS idx_nodes_kind ON memory_nodes(kind);
            "#,
        )
        .context("apply memory schema")?;

        let graph = Self {
            db: Mutex::new(conn),
            index: RwLock::new(HashMap::new()),
            edges: RwLock::new(Vec::new()),
        };
        graph.warm_index()?;
        Ok(graph)
    }

    /// Load all nodes and edges from disk into the in-memory index.
    fn warm_index(&self) -> Result<()> {
        let conn = self.db.lock().unwrap();
        let mut nodes = HashMap::new();
        {
            let mut stmt = conn.prepare(
                "SELECT id, kind, content, embedding, timestamp, importance, confidence \
                 FROM memory_nodes",
            )?;
            let rows = stmt.query_map([], |r| {
                let kind: String = r.get(1)?;
                let emb: Option<String> = r.get(3)?;
                let ts: String = r.get(4)?;
                Ok(MemoryNode {
                    id: r.get(0)?,
                    kind: MemoryKind::parse(&kind).unwrap_or(MemoryKind::Semantic),
                    content: r.get(2)?,
                    embedding: emb.and_then(|s| serde_json::from_str(&s).ok()),
                    timestamp: DateTime::parse_from_rfc3339(&ts)
                        .map(|d| d.with_timezone(&Utc))
                        .unwrap_or_else(|_| Utc::now()),
                    importance: r.get(5)?,
                    confidence: r.get(6)?,
                })
            })?;
            for n in rows {
                let n = n?;
                nodes.insert(n.id.clone(), n);
            }
        }

        let mut edges = Vec::new();
        {
            let mut stmt =
                conn.prepare("SELECT from_id, to_id, kind, weight FROM memory_edges")?;
            let rows = stmt.query_map([], |r| {
                let kind: String = r.get(2)?;
                Ok(Relation {
                    from_id: r.get(0)?,
                    to_id: r.get(1)?,
                    kind: RelationKind::parse(&kind).unwrap_or(RelationKind::RelatedTo),
                    weight: r.get(3)?,
                })
            })?;
            for e in rows {
                edges.push(e?);
            }
        }
        drop(conn);
        *self.index.write().unwrap() = nodes;
        *self.edges.write().unwrap() = edges;
        Ok(())
    }

    /// Insert (or replace) a memory node. Returns its id.
    pub fn add(&self, mut node: MemoryNode) -> Result<String> {
        if node.id.is_empty() {
            node.id = Uuid::new_v4().to_string();
        }
        let emb = node
            .embedding
            .as_ref()
            .map(serde_json::to_string)
            .transpose()?;
        {
            let conn = self.db.lock().unwrap();
            conn.execute(
                "INSERT OR REPLACE INTO memory_nodes \
                 (id, kind, content, embedding, timestamp, importance, confidence) \
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![
                    node.id,
                    node.kind.as_str(),
                    node.content,
                    emb,
                    node.timestamp.to_rfc3339(),
                    node.importance,
                    node.confidence,
                ],
            )?;
        }
        self.index.write().unwrap().insert(node.id.clone(), node.clone());
        Ok(node.id)
    }

    /// Fetch a node by id from the in-memory index.
    pub fn get(&self, id: &str) -> Option<MemoryNode> {
        self.index.read().unwrap().get(id).cloned()
    }

    /// Total number of stored memories.
    pub fn len(&self) -> usize {
        self.index.read().unwrap().len()
    }

    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Create a typed relation between two existing nodes.
    pub fn relate(
        &self,
        from_id: &str,
        to_id: &str,
        kind: RelationKind,
        weight: f32,
    ) -> Result<()> {
        {
            let conn = self.db.lock().unwrap();
            conn.execute(
                "INSERT OR REPLACE INTO memory_edges (from_id, to_id, kind, weight) \
                 VALUES (?1, ?2, ?3, ?4)",
                params![from_id, to_id, kind.as_str(), weight],
            )?;
        }
        self.edges.write().unwrap().push(Relation {
            from_id: from_id.to_string(),
            to_id: to_id.to_string(),
            kind,
            weight,
        });
        Ok(())
    }

    /// Simple substring query over content, optionally filtered by kind.
    /// Results are ordered by importance (desc).
    pub fn query(&self, text: &str, kind: Option<MemoryKind>, limit: usize) -> Vec<MemoryNode> {
        let needle = text.to_lowercase();
        let idx = self.index.read().unwrap();
        let mut hits: Vec<MemoryNode> = idx
            .values()
            .filter(|n| kind.map(|k| k == n.kind).unwrap_or(true))
            .filter(|n| needle.is_empty() || n.content.to_lowercase().contains(&needle))
            .cloned()
            .collect();
        hits.sort_by(|a, b| {
            b.importance
                .partial_cmp(&a.importance)
                .unwrap_or(std::cmp::Ordering::Equal)
        });
        hits.truncate(limit);
        hits
    }

    /// Breadth-first traversal from `start`, following outgoing edges, up to
    /// `max_depth`. Returns the visited node ids in discovery order.
    pub fn traverse(&self, start: &str, max_depth: usize) -> Vec<String> {
        let edges = self.edges.read().unwrap();
        let mut visited = vec![start.to_string()];
        let mut frontier = vec![start.to_string()];
        for _ in 0..max_depth {
            let mut next = Vec::new();
            for node in &frontier {
                for e in edges.iter().filter(|e| &e.from_id == node) {
                    if !visited.contains(&e.to_id) {
                        visited.push(e.to_id.clone());
                        next.push(e.to_id.clone());
                    }
                }
            }
            if next.is_empty() {
                break;
            }
            frontier = next;
        }
        visited
    }

    /// Hybrid retrieval: combine cosine similarity over embeddings (when a
    /// query vector is supplied) with a lexical importance-weighted score.
    /// Returns `(node, score)` pairs sorted by descending score.
    pub fn retrieve(
        &self,
        query_vec: Option<&[f32]>,
        query_text: &str,
        limit: usize,
    ) -> Vec<(MemoryNode, f32)> {
        let needle = query_text.to_lowercase();
        let idx = self.index.read().unwrap();
        let mut scored: Vec<(MemoryNode, f32)> = idx
            .values()
            .map(|n| {
                let sem = match (query_vec, n.embedding.as_ref()) {
                    (Some(q), Some(e)) => cosine(q, e),
                    _ => 0.0,
                };
                let lex = if !needle.is_empty() && n.content.to_lowercase().contains(&needle) {
                    1.0
                } else {
                    0.0
                };
                // Blend semantic + lexical + intrinsic importance.
                let score = 0.6 * sem + 0.3 * lex + 0.1 * n.importance;
                (n.clone(), score)
            })
            .filter(|(_, s)| *s > 0.0)
            .collect();
        scored.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(limit);
        scored
    }

    /// Memory aging: decay importance based on elapsed time using an
    /// exponential half-life, boosted slightly by confidence. Persists the
    /// updated importance values. Returns the number of nodes updated.
    pub fn age(&self, half_life: Duration) -> Result<usize> {
        let now = Utc::now();
        let hl = half_life.num_seconds().max(1) as f32;
        let updates: Vec<(String, f32)> = {
            let idx = self.index.read().unwrap();
            idx.values()
                .map(|n| {
                    let elapsed = (now - n.timestamp).num_seconds().max(0) as f32;
                    let decay = 0.5f32.powf(elapsed / hl);
                    // Confidence resists decay; keep a small floor.
                    let new_imp = (n.importance * decay + 0.05 * n.confidence).clamp(0.0, 1.0);
                    (n.id.clone(), new_imp)
                })
                .collect()
        };
        {
            let conn = self.db.lock().unwrap();
            let mut idx = self.index.write().unwrap();
            for (id, imp) in &updates {
                conn.execute(
                    "UPDATE memory_nodes SET importance = ?1 WHERE id = ?2",
                    params![imp, id],
                )?;
                if let Some(n) = idx.get_mut(id) {
                    n.importance = *imp;
                }
            }
        }
        Ok(updates.len())
    }

    /// Summarisation stub: produce a short textual digest of the most
    /// important memories of a given kind. In the full design this would call
    /// an LLM; here it deterministically concatenates the top items.
    pub fn summarize(&self, kind: MemoryKind, top_n: usize) -> String {
        let items = self.query("", Some(kind), top_n);
        if items.is_empty() {
            return format!("No {} memories to summarize.", kind.as_str());
        }
        let bullets: Vec<String> = items
            .iter()
            .map(|n| format!("- ({:.2}) {}", n.importance, truncate(&n.content, 120)))
            .collect();
        format!(
            "Summary of {} {} memories:\n{}",
            items.len(),
            kind.as_str(),
            bullets.join("\n")
        )
    }
}

/// Cosine similarity between two equal-length vectors. Returns 0.0 on mismatch.
pub fn cosine(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    let mut dot = 0.0f32;
    let mut na = 0.0f32;
    let mut nb = 0.0f32;
    for i in 0..a.len() {
        dot += a[i] * b[i];
        na += a[i] * a[i];
        nb += b[i] * b[i];
    }
    if na == 0.0 || nb == 0.0 {
        return 0.0;
    }
    dot / (na.sqrt() * nb.sqrt())
}

fn truncate(s: &str, max: usize) -> String {
    if s.chars().count() <= max {
        s.to_string()
    } else {
        let t: String = s.chars().take(max).collect();
        format!("{t}…")
    }
}

