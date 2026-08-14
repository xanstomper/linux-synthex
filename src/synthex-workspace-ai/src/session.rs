// SPDX-License-Identifier: MIT OR Apache-2.0
//! Workspace session persistence and restore.
//!
//! A *session* is a named, versioned snapshot of which apps are running on each
//! virtual workspace, with enough information to faithfully re-open them after a
//! reboot.
//!
//! Storage layout:
//!   /var/lib/synthex/sessions/
//!     <session-id>/
//!       meta.json          ← SessionMeta
//!       workspace-<n>.json ← Vec<SavedApp> for workspace n
//!
//! An auto-save of the "last session" runs every 5 minutes; it writes to the
//! special session ID `__autosave__`.

use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
    time::Duration,
};

use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::{process::Command, time::sleep};
use tracing::{debug, error, info};
use uuid::Uuid;

use crate::kwin_bridge::KwinBridge;
use crate::snapshot::{WindowSnapshot, WorkspaceSnapshot};

// ─── Constants ────────────────────────────────────────────────────────────────

const SESSIONS_BASE: &str = "/var/lib/synthex/sessions";
const AUTOSAVE_ID: &str = "__autosave__";
const AUTOSAVE_INTERVAL: Duration = Duration::from_secs(5 * 60);
/// How long to wait for a relaunched app to map a window before giving up.
#[allow(dead_code)]
const LAUNCH_TIMEOUT: Duration = Duration::from_secs(10);

// ─── Data model ───────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionMeta {
    pub id: String,
    pub name: String,
    pub description: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    /// Total number of workspaces captured.
    pub workspace_count: u32,
}

/// Everything needed to re-launch a single application window.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SavedApp {
    /// Human-readable name (from WM_CLASS or process name).
    pub name: String,
    /// Full command line as found in `/proc/<pid>/cmdline`.
    pub cmdline: Vec<String>,
    /// The executable's resolved path.
    pub exe: PathBuf,
    /// Working directory at time of save.
    pub working_dir: Option<PathBuf>,
    /// Window geometry at save time.
    pub geometry: SavedGeometry,
    /// Files the process had open — used to re-open documents in editors.
    pub open_files: Vec<PathBuf>,
    /// Environment variables that differ from the system default (subset).
    pub env_overrides: HashMap<String, String>,
    /// Original X11 window ID (for reference; will change on restore).
    pub original_window_id: u64,
    /// Target workspace number.
    pub workspace_n: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SavedGeometry {
    pub x: i16,
    pub y: i16,
    pub width: u16,
    pub height: u16,
}

/// Result of a restore attempt for a single app.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RestoreResult {
    pub app_name: String,
    pub workspace_n: u32,
    pub success: bool,
    pub pid: Option<u32>,
    pub error: Option<String>,
}

// ─── Session store helpers ────────────────────────────────────────────────────

fn session_dir(id: &str) -> PathBuf {
    PathBuf::from(SESSIONS_BASE).join(id)
}

fn meta_path(id: &str) -> PathBuf {
    session_dir(id).join("meta.json")
}

fn workspace_apps_path(session_id: &str, n: u32) -> PathBuf {
    session_dir(session_id).join(format!("workspace-{n}.json"))
}

async fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<()> {
    let json = serde_json::to_string_pretty(value).context("serialize")?;
    if let Some(parent) = path.parent() {
        tokio::fs::create_dir_all(parent).await.context("mkdir")?;
    }
    tokio::fs::write(path, json).await.context("write json")
}

async fn read_json<T: for<'de> Deserialize<'de>>(path: &Path) -> Result<T> {
    let bytes = tokio::fs::read(path)
        .await
        .with_context(|| format!("read {}", path.display()))?;
    serde_json::from_slice(&bytes).context("deserialize json")
}

// ─── Save ─────────────────────────────────────────────────────────────────────

/// Capture the current session state for all workspaces and persist it.
pub async fn save_session(
    name: &str,
    description: &str,
    snapshots: &[WorkspaceSnapshot],
) -> Result<String> {
    let id = Uuid::new_v4().to_string();
    save_session_with_id(&id, name, description, snapshots).await?;
    Ok(id)
}

/// Internal: save (or overwrite) a session by explicit ID.
pub async fn save_session_with_id(
    id: &str,
    name: &str,
    description: &str,
    snapshots: &[WorkspaceSnapshot],
) -> Result<()> {
    info!(session_id = id, name, "saving workspace session");

    let now = Utc::now();
    let workspace_count = snapshots.len() as u32;

    let meta = SessionMeta {
        id: id.to_string(),
        name: name.to_string(),
        description: description.to_string(),
        created_at: now,
        updated_at: now,
        workspace_count,
    };

    write_json(&meta_path(id), &meta).await?;

    for snap in snapshots {
        let apps: Vec<SavedApp> = snap
            .windows
            .iter()
            .filter_map(|w| window_to_saved_app(w, snap.workspace_n))
            .collect();

        write_json(&workspace_apps_path(id, snap.workspace_n), &apps).await?;
        debug!(
            session_id = id,
            workspace = snap.workspace_n,
            count = apps.len(),
            "saved apps for workspace",
        );
    }

    info!(session_id = id, "session saved successfully");
    Ok(())
}

/// Convert a window snapshot into a SavedApp by reading /proc metadata.
fn window_to_saved_app(w: &WindowSnapshot, workspace_n: u32) -> Option<SavedApp> {
    let pid = w.pid?;

    // cmdline
    let cmdline_raw = fs::read(format!("/proc/{pid}/cmdline")).ok()?;
    let cmdline: Vec<String> = cmdline_raw
        .split(|&b| b == 0)
        .filter(|s| !s.is_empty())
        .map(|s| String::from_utf8_lossy(s).to_string())
        .collect();
    if cmdline.is_empty() {
        return None;
    }

    // exe
    let exe = fs::read_link(format!("/proc/{pid}/exe")).ok()?;

    // env overrides (filter to a small relevant subset)
    let env_overrides = read_proc_env(pid);

    Some(SavedApp {
        name: if !w.class.is_empty() {
            w.class.clone()
        } else {
            w.process_name.clone().unwrap_or_else(|| cmdline[0].clone())
        },
        cmdline,
        exe,
        working_dir: w.working_directory.clone(),
        geometry: SavedGeometry {
            x: w.geometry.x,
            y: w.geometry.y,
            width: w.geometry.width,
            height: w.geometry.height,
        },
        open_files: w.open_files.clone(),
        env_overrides,
        original_window_id: w.window_id,
        workspace_n,
    })
}

fn read_proc_env(pid: u32) -> HashMap<String, String> {
    const INTERESTING: &[&str] = &[
        "DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS",
        "XDG_RUNTIME_DIR", "HOME", "LANG", "PATH",
    ];
    let raw = match fs::read(format!("/proc/{pid}/environ")) {
        Ok(r) => r,
        Err(_) => return HashMap::new(),
    };
    raw.split(|&b| b == 0)
        .filter_map(|entry| {
            let s = std::str::from_utf8(entry).ok()?;
            let (k, v) = s.split_once('=')?;
            if INTERESTING.contains(&k) {
                Some((k.to_string(), v.to_string()))
            } else {
                None
            }
        })
        .collect()
}

// ─── Restore ──────────────────────────────────────────────────────────────────

/// Restore a named session: re-launch all saved apps on their workspaces.
pub async fn restore_session(
    session_id: &str,
    bridge: &KwinBridge,
) -> Result<Vec<RestoreResult>> {
    info!(session_id, "restoring workspace session");

    let meta: SessionMeta = read_json(&meta_path(session_id))
        .await
        .with_context(|| format!("session {session_id} not found"))?;

    let mut results = Vec::new();

    for n in 0..meta.workspace_count {
        let apps_path = workspace_apps_path(session_id, n);
        if !apps_path.exists() {
            continue;
        }

        let apps: Vec<SavedApp> = read_json(&apps_path).await?;

        // Switch to the target workspace.
        let _ = bridge.set_current_desktop(n as i32).await;

        for app in apps {
            let result = relaunch_app(&app).await;
            results.push(result);
        }
    }

    info!(
        session_id,
        restored = results.iter().filter(|r| r.success).count(),
        failed = results.iter().filter(|r| !r.success).count(),
        "session restore complete",
    );

    Ok(results)
}

async fn relaunch_app(app: &SavedApp) -> RestoreResult {
    debug!(name = %app.name, exe = %app.exe.display(), "relaunching app");

    // Build command: use saved cmdline if exe still exists, else try app name.
    let (program, args) = if app.exe.exists() {
        (
            app.exe.to_string_lossy().to_string(),
            app.cmdline.iter().skip(1).cloned().collect::<Vec<_>>(),
        )
    } else if !app.cmdline.is_empty() {
        (
            app.cmdline[0].clone(),
            app.cmdline[1..].to_vec(),
        )
    } else {
        return RestoreResult {
            app_name: app.name.clone(),
            workspace_n: app.workspace_n,
            success: false,
            pid: None,
            error: Some("no executable to launch".into()),
        };
    };

    let mut cmd = Command::new(&program);
    cmd.args(&args)
        .envs(&app.env_overrides)
        .stdin(std::process::Stdio::null())
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null());

    if let Some(wd) = &app.working_dir {
        if wd.exists() {
            cmd.current_dir(wd);
        }
    }

    match cmd.spawn() {
        Ok(child) => {
            let pid = child.id();
            // Give the app a moment to map a window.
            sleep(Duration::from_millis(500)).await;
            RestoreResult {
                app_name: app.name.clone(),
                workspace_n: app.workspace_n,
                success: true,
                pid,
                error: None,
            }
        }
        Err(e) => RestoreResult {
            app_name: app.name.clone(),
            workspace_n: app.workspace_n,
            success: false,
            pid: None,
            error: Some(e.to_string()),
        },
    }
}

// ─── List / delete ────────────────────────────────────────────────────────────

pub async fn list_sessions() -> Result<Vec<SessionMeta>> {
    let mut sessions = Vec::new();
    let mut entries = match tokio::fs::read_dir(SESSIONS_BASE).await {
        Ok(e) => e,
        Err(_) => return Ok(vec![]),
    };

    while let Some(entry) = entries.next_entry().await? {
        let meta_file = entry.path().join("meta.json");
        if let Ok(meta) = read_json::<SessionMeta>(&meta_file).await {
            sessions.push(meta);
        }
    }

    sessions.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
    Ok(sessions)
}

#[allow(dead_code)]
pub async fn delete_session(session_id: &str) -> Result<()> {
    // Disallow deleting the autosave unless explicitly named.
    let dir = session_dir(session_id);
    tokio::fs::remove_dir_all(&dir)
        .await
        .with_context(|| format!("delete session {session_id}"))
}

// ─── Auto-save loop ───────────────────────────────────────────────────────────

/// Spawn a background task that auto-saves every `AUTOSAVE_INTERVAL`.
/// Requires a closure that, when called, yields the current set of workspace
/// snapshots (so the caller can run captures).
pub fn spawn_autosave_task<F, Fut>(capture_fn: F)
where
    F: Fn() -> Fut + Send + Sync + 'static,
    Fut: std::future::Future<Output = Vec<WorkspaceSnapshot>> + Send + 'static,
{
    tokio::spawn(async move {
        loop {
            sleep(AUTOSAVE_INTERVAL).await;
            info!("auto-saving last workspace session");
            let snapshots = capture_fn().await;
            match save_session_with_id(AUTOSAVE_ID, "Last Session", "Auto-saved session", &snapshots).await {
                Ok(()) => info!("auto-save complete"),
                Err(e) => error!("auto-save failed: {e}"),
            }
        }
    });
}
