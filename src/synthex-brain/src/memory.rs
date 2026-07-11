//! Memory graph with SQLite back-end.
//!
//! # Schema
//! ```
//! memories(id, key, value_enc, created_at, accessed_at, access_count, weight, ttl_secs, expires_at)
//! memory_tags(memory_id FK, tag)
//! memory_edges(from_id FK, to_id FK, weight, edge_type)
//! ```
//!
//! # Thread-safety
//! `rusqlite::Connection` is `Send` but not `Sync`.  We wrap it in
//! `Arc<Mutex<Connection>>` and dispatch every write through
//! `tokio::task::spawn_blocking` so the async executor is never blocked.

use std::sync::{Arc, Mutex};

use anyhow::{Context as _, Result};
use chrono::{DateTime, Duration, Utc};
use rusqlite::{params, Connection};
use serde::{Deserialize, Serialize};
use tracing::info;
use uuid::Uuid;

// ── Public types ──────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryNode {
    pub id: String,
    pub key: String,
    /// Encrypted JSON payload (use `security::decrypt_value` before exposing).
    pub value_enc: String,
    pub created_at: DateTime<Utc>,
    pub accessed_at: DateTime<Utc>,
    pub access_count: i64,
    /// Hebbian-style recency/frequency weight; decays over time, grows on access.
    pub weight: f64,
    pub ttl_secs: Option<u64>,
    pub tags: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryEdge {
    pub from_id: String,
    pub to_id: String,
    pub weight: f64,
    pub edge_type: String,
}

// ── MemoryStore ───────────────────────────────────────────────────────────────

pub struct MemoryStore {
    db: Arc<Mutex<Connection>>,
}

// SAFETY: rusqlite::Connection is Send; we never allow concurrent access (Mutex).
unsafe impl Sync for MemoryStore {}

impl MemoryStore {
    /// Open (or create) the SQLite database and apply the schema.
    pub fn open(path: &str) -> Result<Self> {
        let conn = Connection::open(path)
            .with_context(|| format!("Failed to open SQLite DB at {path}"))?;

        // Performance pragmas
        conn.execute_batch(
            "PRAGMA journal_mode = WAL;
             PRAGMA synchronous   = NORMAL;
             PRAGMA foreign_keys  = ON;
             PRAGMA cache_size    = -8192;",  // 8 MiB page cache
        )?;

        conn.execute_batch(
            r#"
            CREATE TABLE IF NOT EXISTS memories (
                id           TEXT    PRIMARY KEY,
                key          TEXT    NOT NULL,
                value_enc    TEXT    NOT NULL,
                created_at   TEXT    NOT NULL,
                accessed_at  TEXT    NOT NULL,
                access_count INTEGER NOT NULL DEFAULT 0,
                weight       REAL    NOT NULL DEFAULT 1.0,
                ttl_secs     INTEGER,
                expires_at   TEXT
            );

            CREATE TABLE IF NOT EXISTS memory_tags (
                memory_id TEXT NOT NULL
                          REFERENCES memories(id) ON DELETE CASCADE,
                tag       TEXT NOT NULL,
                PRIMARY KEY (memory_id, tag)
            );

            CREATE TABLE IF NOT EXISTS memory_edges (
                from_id   TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                to_id     TEXT NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
                weight    REAL NOT NULL DEFAULT 1.0,
                edge_type TEXT NOT NULL DEFAULT 'related',
                PRIMARY KEY (from_id, to_id)
            );

            CREATE INDEX IF NOT EXISTS idx_mem_key     ON memories(key);
            CREATE INDEX IF NOT EXISTS idx_mem_expires ON memories(expires_at);
            CREATE INDEX IF NOT EXISTS idx_tag_tag     ON memory_tags(tag);
            "#,
        )?;

        info!("Memory DB opened at {path}");
        Ok(Self { db: Arc::new(Mutex::new(conn)) })
    }

    // ── Write operations ──────────────────────────────────────────────────────

    /// Store a memory.  Returns the new memory ID.
    pub async fn remember(
        &self,
        key: &str,
        value_enc: &str,
        ttl_secs: Option<u64>,
        tags: &[String],
    ) -> Result<String> {
        let id = Uuid::new_v4().to_string();
        let now = Utc::now().to_rfc3339();
        let expires_at = ttl_secs.map(|t| {
            (Utc::now() + Duration::seconds(t as i64)).to_rfc3339()
        });

        let id2 = id.clone();
        let key = key.to_string();
        let value_enc = value_enc.to_string();
        let tags = tags.to_vec();
        let db = Arc::clone(&self.db);

        tokio::task::spawn_blocking(move || -> Result<()> {
            let conn = lock_db(&db)?;
            conn.execute(
                "INSERT INTO memories
                     (id, key, value_enc, created_at, accessed_at, access_count, weight, ttl_secs, expires_at)
                 VALUES (?1, ?2, ?3, ?4, ?4, 0, 1.0, ?5, ?6)",
                params![id2, key, value_enc, now, ttl_secs.map(|t| t as i64), expires_at],
            )?;
            for tag in &tags {
                conn.execute(
                    "INSERT OR IGNORE INTO memory_tags (memory_id, tag) VALUES (?1, ?2)",
                    params![id2, tag],
                )?;
            }
            Ok(())
        })
        .await
        .context("spawn_blocking panicked")??;

        Ok(id)
    }

    /// Delete a memory by ID (cascade-deletes tags and edges).
    pub async fn forget(&self, id: &str) -> Result<()> {
        let id = id.to_string();
        let db = Arc::clone(&self.db);
        tokio::task::spawn_blocking(move || -> Result<()> {
            let conn = lock_db(&db)?;
            conn.execute("DELETE FROM memories WHERE id = ?1", params![id])?;
            Ok(())
        })
        .await
        .context("spawn_blocking panicked")??;
        Ok(())
    }

    /// Record a weighted edge between two memory nodes.
    pub async fn link(
        &self,
        from: &str,
        to: &str,
        weight: f64,
        edge_type: &str,
    ) -> Result<()> {
        let (from, to, edge_type) = (from.to_string(), to.to_string(), edge_type.to_string());
        let db = Arc::clone(&self.db);
        tokio::task::spawn_blocking(move || -> Result<()> {
            let conn = lock_db(&db)?;
            conn.execute(
                "INSERT INTO memory_edges (from_id, to_id, weight, edge_type)
                 VALUES (?1, ?2, ?3, ?4)
                 ON CONFLICT(from_id, to_id) DO UPDATE
                     SET weight = (weight + ?3) / 2.0",
                params![from, to, weight, edge_type],
            )?;
            Ok(())
        })
        .await
        .context("spawn_blocking panicked")??;
        Ok(())
    }

    // ── Read operations ───────────────────────────────────────────────────────

    /// Search memories whose key or tags contain `query` (case-insensitive).
    /// Bumps access stats on every hit (Hebbian strengthening).
    pub async fn recall(&self, query: &str, limit: usize) -> Result<Vec<MemoryNode>> {
        let pattern = format!("%{}%", query.to_lowercase());
        let limit = limit as i64;
        let now = Utc::now().to_rfc3339();
        let bump_ts = now.clone();
        let db = Arc::clone(&self.db);

        tokio::task::spawn_blocking(move || -> Result<Vec<MemoryNode>> {
            let conn = lock_db(&db)?;

            let mut stmt = conn.prepare(
                "SELECT DISTINCT m.id, m.key, m.value_enc, m.created_at, m.accessed_at,
                        m.access_count, m.weight, m.ttl_secs
                 FROM memories m
                 LEFT JOIN memory_tags t ON t.memory_id = m.id
                 WHERE (m.expires_at IS NULL OR m.expires_at > ?1)
                   AND (LOWER(m.key) LIKE ?2 OR t.tag LIKE ?2)
                 ORDER BY m.weight DESC, m.accessed_at DESC
                 LIMIT ?3",
            )?;

            let ids_and_rows: Vec<_> = stmt
                .query_map(params![now, pattern, limit], row_to_partial)?
                .collect::<rusqlite::Result<_>>()?;

            let mut nodes = Vec::with_capacity(ids_and_rows.len());
            for (id, key, value_enc, created_s, accessed_s, count, weight, ttl) in ids_and_rows {
                let tags = tags_for(&conn, &id)?;
                // Strengthen: each recall multiplies weight by 1.05 (capped at 100)
                conn.execute(
                    "UPDATE memories
                     SET access_count = access_count + 1,
                         accessed_at  = ?1,
                         weight       = MIN(weight * 1.05, 100.0)
                     WHERE id = ?2",
                    params![bump_ts, id],
                )?;
                nodes.push(build_node(id, key, value_enc, created_s, accessed_s, count, weight, ttl, tags));
            }
            Ok(nodes)
        })
        .await
        .context("spawn_blocking panicked")?
    }

    /// Return all non-expired memories carrying the given tag.
    pub async fn recall_by_tag(&self, tag: &str) -> Result<Vec<MemoryNode>> {
        let tag = tag.to_string();
        let now = Utc::now().to_rfc3339();
        let db = Arc::clone(&self.db);

        tokio::task::spawn_blocking(move || -> Result<Vec<MemoryNode>> {
            let conn = lock_db(&db)?;

            let mut stmt = conn.prepare(
                "SELECT m.id, m.key, m.value_enc, m.created_at, m.accessed_at,
                        m.access_count, m.weight, m.ttl_secs
                 FROM memories m
                 JOIN memory_tags t ON t.memory_id = m.id
                 WHERE t.tag = ?1
                   AND (m.expires_at IS NULL OR m.expires_at > ?2)
                 ORDER BY m.weight DESC, m.accessed_at DESC",
            )?;

            let rows: Vec<_> = stmt
                .query_map(params![tag, now], row_to_partial)?
                .collect::<rusqlite::Result<_>>()?;

            rows.into_iter()
                .map(|(id, key, enc, cs, as_, cnt, w, ttl)| {
                    let tags = tags_for(&conn, &id)?;
                    Ok(build_node(id, key, enc, cs, as_, cnt, w, ttl, tags))
                })
                .collect()
        })
        .await
        .context("spawn_blocking panicked")?
    }

    /// Return edges originating from `from_id`, ordered by weight descending.
    pub async fn neighbours(&self, from_id: &str) -> Result<Vec<MemoryEdge>> {
        let from_id = from_id.to_string();
        let db = Arc::clone(&self.db);
        tokio::task::spawn_blocking(move || -> Result<Vec<MemoryEdge>> {
            let conn = lock_db(&db)?;
            let mut stmt = conn.prepare(
                "SELECT to_id, weight, edge_type FROM memory_edges
                 WHERE from_id = ?1 ORDER BY weight DESC LIMIT 20",
            )?;
            stmt.query_map(params![from_id], |r| {
                Ok(MemoryEdge {
                    from_id: from_id.clone(),
                    to_id: r.get(0)?,
                    weight: r.get(1)?,
                    edge_type: r.get(2)?,
                })
            })
            .map(|rows| rows.collect::<rusqlite::Result<_>>())?
            .map_err(Into::into)
        })
        .await
        .context("spawn_blocking panicked")?
    }

    // ── Consolidation ─────────────────────────────────────────────────────────

    /// Scheduled maintenance pass (every 10 minutes):
    ///   - Delete expired memories
    ///   - Decay weight of memories idle > 1 hour (×0.95 per cycle)
    ///   - Hard-forget anything with weight < 0.01
    pub async fn consolidate(&self) -> Result<ConsolidationStats> {
        let db = Arc::clone(&self.db);
        tokio::task::spawn_blocking(move || -> Result<ConsolidationStats> {
            let conn = lock_db(&db)?;
            let now = Utc::now().to_rfc3339();
            let idle_cutoff = (Utc::now() - Duration::hours(1)).to_rfc3339();

            let expired = conn.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at <= ?1",
                params![now],
            )?;

            conn.execute(
                "UPDATE memories
                 SET weight = weight * 0.95
                 WHERE accessed_at < ?1 AND weight >= 0.01",
                params![idle_cutoff],
            )?;

            let forgotten = conn.execute(
                "DELETE FROM memories WHERE weight < 0.01",
                params![],
            )?;

            // Prune orphaned edges (foreign-key cascade should handle this, but be explicit)
            conn.execute(
                "DELETE FROM memory_edges
                 WHERE from_id NOT IN (SELECT id FROM memories)
                    OR to_id   NOT IN (SELECT id FROM memories)",
                params![],
            )?;

            let remaining: i64 = conn.query_row(
                "SELECT COUNT(*) FROM memories", params![], |r| r.get(0),
            )?;

            Ok(ConsolidationStats { expired, forgotten, remaining: remaining as u64 })
        })
        .await
        .context("spawn_blocking panicked")?
    }
}

#[derive(Debug)]
pub struct ConsolidationStats {
    pub expired: usize,
    pub forgotten: usize,
    pub remaining: u64,
}

// ── Private helpers ───────────────────────────────────────────────────────────

type PartialRow = (String, String, String, String, String, i64, f64, Option<i64>);

fn row_to_partial(r: &rusqlite::Row<'_>) -> rusqlite::Result<PartialRow> {
    Ok((
        r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?,
        r.get(4)?, r.get(5)?, r.get(6)?, r.get(7)?,
    ))
}

fn build_node(
    id: String, key: String, value_enc: String,
    created_s: String, accessed_s: String,
    count: i64, weight: f64, ttl: Option<i64>,
    tags: Vec<String>,
) -> MemoryNode {
    MemoryNode {
        id,
        key,
        value_enc,
        created_at:   created_s.parse().unwrap_or_else(|_| Utc::now()),
        accessed_at:  accessed_s.parse().unwrap_or_else(|_| Utc::now()),
        access_count: count,
        weight,
        ttl_secs:     ttl.map(|t| t as u64),
        tags,
    }
}

fn tags_for(conn: &Connection, id: &str) -> Result<Vec<String>> {
    let mut stmt = conn.prepare_cached(
        "SELECT tag FROM memory_tags WHERE memory_id = ?1",
    )?;
    stmt.query_map(params![id], |r| r.get(0))
        .map(|rows| rows.collect::<rusqlite::Result<Vec<String>>>())?
        .map_err(Into::into)
}

fn lock_db(db: &Mutex<Connection>) -> Result<std::sync::MutexGuard<'_, Connection>> {
    db.lock().map_err(|_| anyhow::anyhow!("DB mutex poisoned"))
}
