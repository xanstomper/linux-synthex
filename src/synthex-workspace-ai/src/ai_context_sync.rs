// SPDX-License-Identifier: MIT OR Apache-2.0
//! AI context persistence layer.
//!
//! Each of the 10 virtual workspaces carries a [`WorkspaceContext`] that
//! describes its purpose, the AI agent assigned to it, which tools it owns,
//! and what the AI should remember when working on it.
//!
//! Contexts are stored under:
//!   /var/lib/synthex/workspace-contexts/workspace-<n>.json
//!
//! They are also written into the SynthOS Brain daemon's memory store via the
//! Brain D-Bus interface so that agents can recall context by tag.
//!
//! History: every time a context is mutated a timestamped entry is appended to
//!   /var/lib/synthex/workspace-contexts/workspace-<n>.history.jsonl

use std::{
    collections::HashMap,
    path::{Path, PathBuf},
};

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::fs;
use tracing::{debug, info, warn};
use zbus::Connection;

// ─── Types ────────────────────────────────────────────────────────────────────

/// Isolation level of a workspace — controls whether AI tool calls from one
/// workspace can affect the process namespace of another.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
#[serde(rename_all = "PascalCase")]
pub enum IsolationLevel {
    /// No isolation — all workspaces share the same OS-level namespaces.
    #[default]
    None,
    /// Each workspace's launched processes are placed into their own cgroup and
    /// optionally a PID namespace so they can be bulk-killed when leaving.
    Process,
    /// Full Linux namespace isolation: PID + mount + network + IPC.  Requires
    /// the synthex-namespace-helper setuid binary.
    Namespace,
}

/// Full context assigned to a virtual workspace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceContext {
    /// Short machine-readable name, e.g. `"coding"`.
    pub name: String,
    /// Human-readable purpose.
    pub purpose: String,
    /// Optional agent ID currently assigned to this workspace.
    pub assigned_agent: Option<String>,
    /// KWin background color hint (CSS hex or named color).
    pub background_color: String,
    /// Taskbar icon (XDG icon name or absolute path).
    pub icon: String,
    /// Brain memory tags: when the agent is on this workspace, it recalls
    /// memories tagged with these strings first.
    pub memory_tags: Vec<String>,
    /// Which tool/app categories belong here (informational).
    pub tools: Vec<String>,
    /// Commands to auto-launch when the user switches to this workspace.
    pub auto_launch: Vec<String>,
    /// Isolation policy.
    pub isolation_level: IsolationLevel,
    /// Arbitrary key→value metadata for this workspace.
    pub meta: HashMap<String, String>,
    /// When this context was last modified.
    pub updated_at: DateTime<Utc>,
}

impl Default for WorkspaceContext {
    fn default() -> Self {
        Self {
            name: String::from("unnamed"),
            purpose: String::new(),
            assigned_agent: None,
            background_color: String::from("#1e1e2e"),
            icon: String::from("applications-other"),
            memory_tags: vec![],
            tools: vec![],
            auto_launch: vec![],
            isolation_level: IsolationLevel::None,
            meta: HashMap::new(),
            updated_at: Utc::now(),
        }
    }
}

/// A point-in-time history entry for a workspace's context changes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceHistoryEntry {
    pub timestamp: DateTime<Utc>,
    pub changed_by: String, // "user" | agent_id | "system"
    pub description: String,
    pub context_snapshot: WorkspaceContext,
}

/// Lightweight snapshot used by `GetAllWorkspaces`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceSnapshot {
    pub n: u32,
    pub context: WorkspaceContext,
    pub window_count: usize,
    pub active_agent: Option<String>,
}

// ─── Storage paths ────────────────────────────────────────────────────────────

const CONTEXT_BASE: &str = "/var/lib/synthex/workspace-contexts";

fn context_path(n: u32) -> PathBuf {
    PathBuf::from(CONTEXT_BASE).join(format!("workspace-{n}.json"))
}

fn history_path(n: u32) -> PathBuf {
    PathBuf::from(CONTEXT_BASE).join(format!("workspace-{n}.history.jsonl"))
}

// ─── Read / write ─────────────────────────────────────────────────────────────

/// Load the context for workspace `n`, returning a default if none is stored.
pub async fn load_context(n: u32) -> Result<WorkspaceContext> {
    let path = context_path(n);
    if !path.exists() {
        return Ok(WorkspaceContext::default());
    }
    let bytes = fs::read(&path)
        .await
        .with_context(|| format!("read context for workspace {n}"))?;
    serde_json::from_slice(&bytes).context("deserialize WorkspaceContext")
}

/// Persist context for workspace `n` and append a history entry.
pub async fn save_context(
    n: u32,
    ctx: &WorkspaceContext,
    changed_by: &str,
    description: &str,
) -> Result<()> {
    fs::create_dir_all(CONTEXT_BASE)
        .await
        .context("create context dir")?;

    let mut ctx = ctx.clone();
    ctx.updated_at = Utc::now();

    let json = serde_json::to_string_pretty(&ctx).context("serialize context")?;
    fs::write(context_path(n), json)
        .await
        .context("write context file")?;

    // Append to history log.
    let entry = WorkspaceHistoryEntry {
        timestamp: ctx.updated_at,
        changed_by: changed_by.to_string(),
        description: description.to_string(),
        context_snapshot: ctx.clone(),
    };
    let mut line = serde_json::to_string(&entry).context("serialize history entry")?;
    line.push('\n');
    use tokio::io::AsyncWriteExt as _;
    let mut file = tokio::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(history_path(n))
        .await
        .context("open history file")?;
    file.write_all(line.as_bytes())
        .await
        .context("append history")?;

    debug!(workspace = n, "context saved");
    Ok(())
}

/// Load the full history for workspace `n` (newest first).
pub async fn load_history(n: u32, limit: usize) -> Result<Vec<WorkspaceHistoryEntry>> {
    let path = history_path(n);
    if !path.exists() {
        return Ok(vec![]);
    }
    let content = fs::read_to_string(&path)
        .await
        .context("read history file")?;
    let mut entries: Vec<WorkspaceHistoryEntry> = content
        .lines()
        .filter(|l| !l.trim().is_empty())
        .filter_map(|l| serde_json::from_str(l).ok())
        .collect();
    entries.sort_by(|a, b| b.timestamp.cmp(&a.timestamp));
    entries.truncate(limit);
    Ok(entries)
}

// ─── Agent ↔ workspace registry ───────────────────────────────────────────────

/// In-memory registry of agent_id → workspace_n assignments.
/// Backed by a JSON file so assignments survive daemon restarts.
#[derive(Debug, Default)]
pub struct AgentRegistry {
    map: HashMap<String, u32>,
    path: PathBuf,
}

const AGENT_REGISTRY_PATH: &str = "/var/lib/synthex/agent-workspace-registry.json";

impl AgentRegistry {
    pub async fn load() -> Result<Self> {
        let path = PathBuf::from(AGENT_REGISTRY_PATH);
        let map = if path.exists() {
            let bytes = fs::read(&path).await.context("read agent registry")?;
            serde_json::from_slice(&bytes).context("deserialize agent registry")?
        } else {
            HashMap::new()
        };
        Ok(Self { map, path })
    }

    pub fn assign(&mut self, agent_id: &str, workspace_n: u32) {
        self.map.insert(agent_id.to_string(), workspace_n);
    }

    pub fn get(&self, agent_id: &str) -> Option<u32> {
        self.map.get(agent_id).copied()
    }

    pub fn all(&self) -> &HashMap<String, u32> {
        &self.map
    }

    pub async fn persist(&self) -> Result<()> {
        fs::create_dir_all(
            self.path.parent().unwrap_or(Path::new("/")),
        )
        .await
        .context("mkdir for agent registry")?;
        let json = serde_json::to_string_pretty(&self.map).context("serialize")?;
        fs::write(&self.path, json).await.context("write agent registry")
    }
}

// ─── Brain D-Bus sync ─────────────────────────────────────────────────────────

/// Push a workspace context into the Brain daemon's memory store.
///
/// Uses the Brain's `StoreMemory` D-Bus method
/// (interface `org.synthex.Brain`, path `/org/synthex/Brain`).
/// Tags are set to the workspace's `memory_tags` plus a synthetic
/// `workspace:<n>` tag so agents can query by workspace number.
pub async fn sync_context_to_brain(n: u32, ctx: &WorkspaceContext) -> Result<()> {
    let conn = match Connection::session().await {
        Ok(c) => c,
        Err(e) => {
            warn!("can't reach session bus to sync Brain: {e}");
            return Ok(());
        }
    };

    // Build the memory payload.
    let payload = serde_json::json!({
        "workspace": n,
        "name": ctx.name,
        "purpose": ctx.purpose,
        "assigned_agent": ctx.assigned_agent,
        "tools": ctx.tools,
        "auto_launch": ctx.auto_launch,
        "isolation_level": ctx.isolation_level,
        "meta": ctx.meta,
    });

    let mut tags = ctx.memory_tags.clone();
    tags.push(format!("workspace:{n}"));
    tags.push("workspace-context".to_string());

    // Call StoreMemory(content: s, tags: as) → id: s
    let reply = conn
        .call_method(
            Some("org.synthex.Brain"),
            "/org/synthex/Brain",
            Some("org.synthex.Brain"),
            "StoreMemory",
            &(payload.to_string(), tags),
        )
        .await;

    match reply {
        Ok(_) => {
            debug!(workspace = n, "synced context to Brain daemon");
        }
        Err(e) => {
            warn!("Brain sync failed (workspace {n}): {e}");
        }
    }

    Ok(())
}

// ─── Initialisation helpers ───────────────────────────────────────────────────

/// Load contexts for all 10 workspaces, returning a map n → context.
pub async fn load_all_contexts() -> HashMap<u32, WorkspaceContext> {
    let mut map = HashMap::new();
    for n in 0..10u32 {
        match load_context(n).await {
            Ok(ctx) => {
                map.insert(n, ctx);
            }
            Err(e) => {
                warn!("failed to load context for workspace {n}: {e}");
                map.insert(n, WorkspaceContext::default());
            }
        }
    }
    map
}

/// Apply a set of preset contexts (from configs/workspace-presets.json) to
/// workspaces that don't yet have a stored context.
pub async fn apply_presets(presets: &[serde_json::Value]) -> Result<()> {
    for preset in presets {
        let n = preset["n"].as_u64().unwrap_or(99) as u32;
        if n > 9 {
            continue;
        }
        let path = context_path(n);
        if path.exists() {
            // Don't overwrite user-customised contexts.
            continue;
        }
        let ctx = WorkspaceContext {
            name: preset["name"].as_str().unwrap_or("unnamed").to_string(),
            purpose: preset["purpose"].as_str().unwrap_or("").to_string(),
            auto_launch: preset["auto_launch"]
                .as_array()
                .unwrap_or(&vec![])
                .iter()
                .filter_map(|v| v.as_str().map(str::to_string))
                .collect(),
            isolation_level: match preset["isolation_level"].as_str() {
                Some("Process") => IsolationLevel::Process,
                Some("Namespace") => IsolationLevel::Namespace,
                _ => IsolationLevel::None,
            },
            ..Default::default()
        };
        save_context(n, &ctx, "system", "preset initialisation").await?;
    }
    Ok(())
}
