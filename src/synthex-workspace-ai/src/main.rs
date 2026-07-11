// SPDX-License-Identifier: MIT OR Apache-2.0
//! synthex-workspace-ai — Multi-workspace AI consciousness daemon for SynthOS.
//!
//! Exposes a D-Bus service at:
//!   name:    org.synthex.WorkspaceAI
//!   path:    /org/synthex/WorkspaceAI
//!   iface:   org.synthex.WorkspaceAI
//!
//! See the individual sub-modules for implementation details.

mod ai_context_sync;
mod kwin_bridge;
mod multi_agent_coordinator;
mod session;
mod snapshot;

use std::{
    collections::HashMap,
    sync::Arc,
};

use anyhow::{Context, Result};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use tracing::{error, info};
use tracing_subscriber::{fmt, EnvFilter};
use zbus::{connection, interface};

use ai_context_sync::{
    AgentRegistry, IsolationLevel, WorkspaceContext, WorkspaceHistoryEntry, WorkspaceSnapshot,
    apply_presets, load_all_contexts, load_context, load_history, save_context,
    sync_context_to_brain,
};
use kwin_bridge::KwinBridge;
use multi_agent_coordinator::{
    AgentRecord, ClipboardEntry, CoordinatorHandle, DelegationTask, TaskStatus, WorkspaceEvent,
    spawn_coordinator,
};
use session::{SessionMeta, RestoreResult, list_sessions, restore_session, save_session};
use snapshot::{WorkspaceSnapshot as WsSnapshot, capture_workspace, load_latest_snapshot};

// ─── Daemon state ─────────────────────────────────────────────────────────────

struct DaemonState {
    /// Per-workspace AI contexts (index = workspace number, 0-based).
    contexts: HashMap<u32, WorkspaceContext>,
    /// Agent → workspace registry.
    agent_registry: AgentRegistry,
    /// KWin bridge (may be unavailable in headless environments).
    kwin: Option<KwinBridge>,
    /// Multi-agent coordinator handle.
    coordinator: CoordinatorHandle,
}

type SharedState = Arc<RwLock<DaemonState>>;

// ─── D-Bus interface implementation ───────────────────────────────────────────

struct WorkspaceAI {
    state: SharedState,
}

#[interface(name = "org.synthex.WorkspaceAI")]
impl WorkspaceAI {
    // ── Context management ────────────────────────────────────────────────────

    /// Set the AI context for virtual workspace `n`.
    async fn set_workspace_context(&self, n: u32, ctx_json: String) -> bool {
        let ctx: WorkspaceContext = match serde_json::from_str(&ctx_json) {
            Ok(c) => c,
            Err(e) => {
                error!("SetWorkspaceContext: invalid JSON: {e}");
                return false;
            }
        };

        let kwin = self.state.read().await.kwin.clone();

        // Apply visual changes through KWin.
        if let Some(ref bridge) = kwin {
            let _ = bridge.set_desktop_name(n, &ctx.name).await;
            let _ = bridge
                .set_desktop_background_color(n, &ctx.background_color)
                .await;
        }

        // Sync to Brain daemon.
        let _ = sync_context_to_brain(n, &ctx).await;

        // Persist.
        match save_context(n, &ctx, "dbus-call", "SetWorkspaceContext").await {
            Ok(()) => {
                let mut state = self.state.write().await;
                state.contexts.insert(n, ctx);
                true
            }
            Err(e) => {
                error!("SetWorkspaceContext persist error: {e}");
                false
            }
        }
    }

    /// Retrieve the AI context for workspace `n` as a JSON string.
    async fn get_workspace_context(&self, n: u32) -> String {
        let state = self.state.read().await;
        let ctx = state
            .contexts
            .get(&n)
            .cloned()
            .unwrap_or_default();
        serde_json::to_string(&ctx).unwrap_or_else(|_| "{}".into())
    }

    /// Return lightweight snapshots of all 10 workspaces as a JSON array.
    async fn get_all_workspaces(&self) -> String {
        let state = self.state.read().await;
        let mut snapshots: Vec<WorkspaceSnapshot> = Vec::new();
        for n in 0..10u32 {
            let ctx = state.contexts.get(&n).cloned().unwrap_or_default();
            let active_agent = state
                .coordinator
                .list_agents()
                .await
                .into_iter()
                .find(|a| a.workspace == n)
                .map(|a| a.id);
            snapshots.push(WorkspaceSnapshot {
                n,
                context: ctx,
                window_count: 0, // filled async — omit here for responsiveness
                active_agent,
            });
        }
        serde_json::to_string(&snapshots).unwrap_or_else(|_| "[]".into())
    }

    // ── Screenshots ───────────────────────────────────────────────────────────

    /// Capture a PNG screenshot of workspace `n` and return it base64-encoded.
    /// Returns an empty string on failure.
    async fn capture_workspace_screenshot(&self, n: u32) -> String {
        match capture_workspace(n).await {
            Ok(snap) => snap.screenshot_png_b64,
            Err(e) => {
                error!("CaptureWorkspaceScreenshot({n}): {e}");
                String::new()
            }
        }
    }

    // ── Window list ───────────────────────────────────────────────────────────

    /// Return the list of windows on workspace `n` as a JSON array.
    async fn get_workspace_window_list(&self, n: u32) -> String {
        // Try the cached latest snapshot first; take a live capture if missing.
        let snap = match load_latest_snapshot(n).await {
            Ok(s) => s,
            Err(_) => match capture_workspace(n).await {
                Ok(s) => s,
                Err(e) => {
                    error!("GetWorkspaceWindowList({n}): {e}");
                    return "[]".into();
                }
            },
        };
        serde_json::to_string(&snap.windows).unwrap_or_else(|_| "[]".into())
    }

    // ── Workspace switching ───────────────────────────────────────────────────

    /// Switch the active virtual desktop to `n`.
    async fn switch_to_workspace(&self, n: u32) -> bool {
        let kwin = self.state.read().await.kwin.clone();
        match kwin {
            Some(bridge) => bridge.set_current_desktop(n as i32).await.unwrap_or(false),
            None => {
                // Fallback: try wmctrl.
                std::process::Command::new("wmctrl")
                    .args(["-s", &n.to_string()])
                    .status()
                    .map(|s| s.success())
                    .unwrap_or(false)
            }
        }
    }

    // ── App launch ────────────────────────────────────────────────────────────

    /// Launch `command` on workspace `n` with optional environment overrides
    /// (JSON object string → HashMap<String,String>).
    /// Returns the PID of the spawned process, or 0 on failure.
    async fn launch_on_workspace(
        &self,
        n: u32,
        command: String,
        env_json: String,
    ) -> u32 {
        let env: HashMap<String, String> =
            serde_json::from_str(&env_json).unwrap_or_default();

        let kwin = self.state.read().await.kwin.clone();

        let pid = match kwin {
            Some(bridge) => bridge.launch_on_workspace(n, &command, &env).await.unwrap_or(0),
            None => {
                // Headless fallback.
                let parts: Vec<&str> = command.split_whitespace().collect();
                if parts.is_empty() {
                    return 0;
                }
                tokio::process::Command::new(parts[0])
                    .args(&parts[1..])
                    .envs(&env)
                    .stdin(std::process::Stdio::null())
                    .stdout(std::process::Stdio::null())
                    .stderr(std::process::Stdio::null())
                    .spawn()
                    .map(|c| c.id().unwrap_or(0))
                    .unwrap_or(0)
            }
        };

        // Broadcast launch event.
        self.state
            .read()
            .await
            .coordinator
            .broadcast_event(WorkspaceEvent::AppLaunched {
                workspace: n,
                pid,
                command,
            })
            .await;

        pid
    }

    // ── Window management ─────────────────────────────────────────────────────

    /// Move X11 window `window_id` to virtual desktop `n`.
    async fn move_window_to_workspace(&self, window_id: u64, n: u32) -> bool {
        let kwin = self.state.read().await.kwin.clone();
        match kwin {
            Some(bridge) => bridge
                .move_window_to_desktop(window_id, n)
                .await
                .map(|_| true)
                .unwrap_or(false),
            None => false,
        }
    }

    // ── Agent assignment ──────────────────────────────────────────────────────

    /// Register `agent_id` as the active agent for workspace `n`.
    async fn assign_agent_to_workspace(&self, agent_id: String, workspace_n: u32) -> bool {
        let mut state = self.state.write().await;

        // Upsert in registry.
        let record = if let Some(existing) = state.coordinator
            .list_agents()
            .await
            .into_iter()
            .find(|a| a.id == agent_id)
        {
            existing
        } else {
            AgentRecord {
                id: agent_id.clone(),
                workspace: workspace_n,
                priority: 5,
                capabilities: vec![],
                registered_at: Utc::now(),
                last_seen: Utc::now(),
            }
        };

        drop(state); // release write lock before async calls

        let _ = self.state.read().await.coordinator.register_agent(record).await;
        let ok = self
            .state
            .read()
            .await
            .coordinator
            .assign_workspace(&agent_id, workspace_n)
            .await
            .is_ok();

        // Persist.
        {
            let mut state = self.state.write().await;
            state.agent_registry.assign(&agent_id, workspace_n);
            let _ = state.agent_registry.persist().await;
        }

        ok
    }

    /// Return the workspace number the given agent is assigned to, or u32::MAX
    /// if the agent is not registered.
    async fn get_agent_workspace(&self, agent_id: String) -> u32 {
        self.state
            .read()
            .await
            .coordinator
            .get_agent_workspace(&agent_id)
            .await
            .unwrap_or(u32::MAX)
    }

    // ── Events ────────────────────────────────────────────────────────────────

    /// Broadcast a JSON-encoded [`WorkspaceEvent`] to all subscribers on the
    /// agent bus.  Returns `true` on success.
    async fn broadcast_to_workspace(&self, _n: u32, event_json: String) -> bool {
        let event: WorkspaceEvent = match serde_json::from_str(&event_json) {
            Ok(e) => e,
            Err(e) => {
                error!("BroadcastToWorkspace: invalid event JSON: {e}");
                return false;
            }
        };
        self.state
            .read()
            .await
            .coordinator
            .broadcast_event(event)
            .await;
        true
    }

    // ── Sessions ──────────────────────────────────────────────────────────────

    /// Capture the current workspace state and save it as a named session.
    /// Returns the new session ID, or an empty string on failure.
    async fn create_workspace_session(&self, name: String, description: String) -> String {
        // Capture all workspaces.
        let mut snaps = Vec::new();
        for n in 0..10u32 {
            if let Ok(snap) = capture_workspace(n).await {
                snaps.push(snap);
            }
        }

        match save_session(&name, &description, &snaps).await {
            Ok(id) => {
                info!(session_id = %id, name, "created workspace session");
                id
            }
            Err(e) => {
                error!("CreateWorkspaceSession: {e}");
                String::new()
            }
        }
    }

    /// Restore a previously saved session.  Returns JSON array of restore results.
    async fn restore_workspace_session(&self, session_id: String) -> String {
        let kwin = self.state.read().await.kwin.clone();
        // We need a bridge for restore; if KWin is unavailable the restore
        // still attempts launches but won't switch desktops.
        let bridge_owned: Option<KwinBridge>;
        if let Some(ref b) = kwin {
            bridge_owned = Some(b.clone());
        } else {
            bridge_owned = None;
        }

        let results = match &bridge_owned {
            Some(b) => restore_session(&session_id, b).await,
            None => {
                // Create a temporary no-op bridge.
                match KwinBridge::new().await {
                    Ok(b) => restore_session(&session_id, &b).await,
                    Err(e) => {
                        error!("RestoreWorkspaceSession: no KWin bridge: {e}");
                        return "[]".into();
                    }
                }
            }
        };

        match results {
            Ok(r) => serde_json::to_string(&r).unwrap_or_else(|_| "[]".into()),
            Err(e) => {
                error!("RestoreWorkspaceSession({session_id}): {e}");
                "[]".into()
            }
        }
    }

    /// Return a JSON array of all saved sessions (metadata only).
    async fn list_workspace_sessions(&self) -> String {
        match list_sessions().await {
            Ok(sessions) => serde_json::to_string(&sessions).unwrap_or_else(|_| "[]".into()),
            Err(e) => {
                error!("ListWorkspaceSessions: {e}");
                "[]".into()
            }
        }
    }

    // ── History ───────────────────────────────────────────────────────────────

    /// Return up to 100 history entries for workspace `n` (newest first).
    async fn get_workspace_history(&self, n: u32) -> String {
        match load_history(n, 100).await {
            Ok(entries) => serde_json::to_string(&entries).unwrap_or_else(|_| "[]".into()),
            Err(e) => {
                error!("GetWorkspaceHistory({n}): {e}");
                "[]".into()
            }
        }
    }

    // ── Agent coordination ────────────────────────────────────────────────────

    /// Delegate a task from `from_agent` to `to_agent` on workspace `n`.
    /// `payload_json` is an arbitrary JSON value attached to the task.
    /// Returns the new task ID, or empty string on failure.
    async fn delegate_task(
        &self,
        from_agent: String,
        to_agent: String,
        workspace: u32,
        description: String,
        payload_json: String,
    ) -> String {
        let payload: serde_json::Value =
            serde_json::from_str(&payload_json).unwrap_or(serde_json::Value::Null);
        match self
            .state
            .read()
            .await
            .coordinator
            .delegate_task(&from_agent, &to_agent, workspace, &description, payload)
            .await
        {
            Ok(id) => id,
            Err(e) => {
                error!("DelegateTask: {e}");
                String::new()
            }
        }
    }

    /// List all registered agents as a JSON array.
    async fn list_agents(&self) -> String {
        let agents = self.state.read().await.coordinator.list_agents().await;
        serde_json::to_string(&agents).unwrap_or_else(|_| "[]".into())
    }

    /// Write to the shared agent clipboard namespace.
    /// `tag` is the key; `content` is the value (arbitrary string).
    async fn write_agent_clipboard(&self, tag: String, content: String, by: String) -> bool {
        self.state
            .read()
            .await
            .coordinator
            .write_clipboard(&tag, content, &by)
            .await
            .is_ok()
    }

    /// Read a tagged clipboard entry; returns empty string if not found.
    async fn read_agent_clipboard(&self, tag: String) -> String {
        match self
            .state
            .read()
            .await
            .coordinator
            .read_clipboard(&tag)
            .await
        {
            Some(entry) => entry.content,
            None => String::new(),
        }
    }

    /// Try to acquire a named resource lock for an agent.
    /// Returns `true` if the lock was granted.
    async fn acquire_resource(&self, resource: String, agent_id: String) -> bool {
        self.state
            .read()
            .await
            .coordinator
            .acquire_resource(&resource, &agent_id)
            .await
            .unwrap_or(false)
    }

    /// Release a resource lock.
    async fn release_resource(&self, resource: String, agent_id: String) -> bool {
        self.state
            .read()
            .await
            .coordinator
            .release_resource(&resource, &agent_id)
            .await
            .is_ok()
    }
}

// ─── Entry point ──────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    // Logging.
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .with_target(false)
        .compact()
        .init();

    info!("synthex-workspace-ai starting");

    // ── Load presets ──────────────────────────────────────────────────────────
    let presets_path = "/etc/synthex/workspace-presets.json";
    let presets_json = tokio::fs::read_to_string(presets_path)
        .await
        .unwrap_or_else(|_| {
            info!("workspace-presets.json not found at {presets_path}; using defaults");
            include_str!("../../configs/workspace-presets.json").to_string()
        });

    let presets: serde_json::Value =
        serde_json::from_str(&presets_json).unwrap_or(serde_json::json!({"workspaces":[]}));

    if let Some(arr) = presets["workspaces"].as_array() {
        apply_presets(arr).await.ok();
    }

    // ── Load contexts ─────────────────────────────────────────────────────────
    let contexts = load_all_contexts().await;

    // ── Agent registry ────────────────────────────────────────────────────────
    let agent_registry = AgentRegistry::load().await.unwrap_or_default();

    // ── KWin bridge ───────────────────────────────────────────────────────────
    let kwin = match KwinBridge::new().await {
        Ok(b) => {
            // Ensure KWin has at least 10 virtual desktops.
            let _ = b.ensure_desktop_count(10).await;
            // Set desktop names from contexts.
            for (n, ctx) in &contexts {
                let _ = b.set_desktop_name(*n, &ctx.name).await;
            }
            info!("KWin bridge connected");
            Some(b)
        }
        Err(e) => {
            info!("KWin not available ({e}); running in headless mode");
            None
        }
    };

    // ── Coordinator ───────────────────────────────────────────────────────────
    let coordinator = spawn_coordinator();

    // Re-register agents from the persisted registry.
    for (agent_id, &workspace) in agent_registry.all() {
        let record = AgentRecord {
            id: agent_id.clone(),
            workspace,
            priority: 5,
            capabilities: vec![],
            registered_at: Utc::now(),
            last_seen: Utc::now(),
        };
        let _ = coordinator.register_agent(record).await;
    }

    // ── Shared state ──────────────────────────────────────────────────────────
    let state: SharedState = Arc::new(RwLock::new(DaemonState {
        contexts,
        agent_registry,
        kwin,
        coordinator: coordinator.clone(),
    }));

    // ── Auto-save task ────────────────────────────────────────────────────────
    {
        let _state = Arc::clone(&state);
        session::spawn_autosave_task(move || {
            let state = Arc::clone(&_state);
            async move {
                let mut snaps = Vec::new();
                for n in 0..10u32 {
                    if let Ok(snap) = capture_workspace(n).await {
                        snaps.push(snap);
                    }
                }
                snaps
            }
        });
    }

    // ── D-Bus service ─────────────────────────────────────────────────────────
    let _conn = connection::Builder::session()
        .context("build D-Bus connection")?
        .name("org.synthex.WorkspaceAI")
        .context("request D-Bus name")?
        .serve_at(
            "/org/synthex/WorkspaceAI",
            WorkspaceAI {
                state: Arc::clone(&state),
            },
        )
        .context("serve WorkspaceAI interface")?
        .build()
        .await
        .context("establish D-Bus connection")?;

    info!("synthex-workspace-ai listening on org.synthex.WorkspaceAI");

    // Run forever until signalled.
    std::future::pending::<()>().await;
    Ok(())
}
