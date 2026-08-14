use anyhow::{Context, Result};
use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use tracing::{debug, info, warn};
use uuid::Uuid;

use crate::providers::Message;

// ── Session model ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub messages: Vec<Message>,
    pub created_at: DateTime<Utc>,
    pub last_active: DateTime<Utc>,
    pub token_count: u32,
}

impl Session {
    pub fn new() -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            messages: Vec::new(),
            created_at: now,
            last_active: now,
            token_count: 0,
        }
    }

    pub fn push_message(&mut self, role: impl Into<String>, content: impl Into<String>) {
        self.messages.push(Message {
            role: role.into(),
            content: content.into(),
        });
        self.last_active = Utc::now();
    }

    pub fn add_tokens(&mut self, count: u32) {
        self.token_count = self.token_count.saturating_add(count);
    }

    pub fn is_expired(&self, max_age: Duration) -> bool {
        Utc::now() - self.last_active > max_age
    }
}

impl Default for Session {
    fn default() -> Self {
        Self::new()
    }
}

// ── Storage ───────────────────────────────────────────────────────────────────

pub struct SessionStore {
    dir: PathBuf,
}

impl SessionStore {
    pub fn new(dir: impl Into<PathBuf>) -> Self {
        Self { dir: dir.into() }
    }

    fn session_path(&self, id: &str) -> PathBuf {
        self.dir.join(format!("{id}.json"))
    }

    /// Ensure the storage directory exists.
    pub async fn init(&self) -> Result<()> {
        tokio::fs::create_dir_all(&self.dir)
            .await
            .with_context(|| format!("creating session dir {:?}", self.dir))
    }

    /// Persist a session to disk.
    pub async fn save(&self, session: &Session) -> Result<()> {
        let path = self.session_path(&session.id);
        let json = serde_json::to_string_pretty(session).context("serialising session")?;
        tokio::fs::write(&path, json)
            .await
            .with_context(|| format!("writing session to {path:?}"))?;
        debug!("saved session {} to {path:?}", session.id);
        Ok(())
    }

    /// Load a session by ID.
    pub async fn load(&self, id: &str) -> Result<Session> {
        let path = self.session_path(id);
        let json = tokio::fs::read_to_string(&path)
            .await
            .with_context(|| format!("reading session from {path:?}"))?;
        let session: Session = serde_json::from_str(&json)
            .with_context(|| format!("deserialising session from {path:?}"))?;
        Ok(session)
    }

    /// Return IDs of all stored sessions.
    pub async fn list_ids(&self) -> Result<Vec<String>> {
        let mut ids = Vec::new();
        let mut entries = tokio::fs::read_dir(&self.dir)
            .await
            .context("reading session directory")?;
        while let Some(entry) = entries.next_entry().await.context("iterating session dir")? {
            let name = entry.file_name();
            let name = name.to_string_lossy();
            if name.ends_with(".json") {
                ids.push(name.trim_end_matches(".json").to_string());
            }
        }
        Ok(ids)
    }

    /// Delete a session file.
    pub async fn delete(&self, id: &str) -> Result<()> {
        let path = self.session_path(id);
        tokio::fs::remove_file(&path)
            .await
            .with_context(|| format!("deleting session {path:?}"))?;
        info!("deleted session {id}");
        Ok(())
    }

    /// Remove sessions that have not been active for longer than `max_age`.
    pub async fn cleanup_expired(&self, max_age: Duration) -> Result<usize> {
        let ids = self.list_ids().await?;
        let mut removed = 0usize;
        for id in ids {
            match self.load(&id).await {
                Ok(session) if session.is_expired(max_age) => {
                    if let Err(e) = self.delete(&id).await {
                        warn!("cleanup: failed to delete session {id}: {e:#}");
                    } else {
                        removed += 1;
                    }
                }
                Ok(_) => {}
                Err(e) => {
                    warn!("cleanup: could not load session {id}: {e:#}");
                }
            }
        }
        if removed > 0 {
            info!("cleanup: removed {removed} expired sessions");
        }
        Ok(removed)
    }
}
