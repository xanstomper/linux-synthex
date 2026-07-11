//! synthex-brain — SynthOS AI Consciousness Daemon
//!
//! Exposes:
//!   • DBus service   `org.synthex.Brain` at `/org/synthex/Brain`
//!   • Unix IPC socket `/run/synthex/brain.sock` (newline-delimited JSON)
//!
//! Architecture:
//!   ┌──────────────────────────────────────────────────────┐
//!   │  BrainState (Arc-shared between DBus & IPC tasks)   │
//!   │  ┌─────────────┐  ┌──────────────┐  ┌───────────┐  │
//!   │  │ MemoryStore │  │ContextMonitor│  │  Agents   │  │
//!   │  │  (SQLite)   │  │  (2 s poll)  │  │  Tasks    │  │
//!   │  └─────────────┘  └──────────────┘  └───────────┘  │
//!   └──────────────────────────────────────────────────────┘

use std::{
    collections::HashMap,
    path::Path,
    sync::Arc,
    time::Duration,
};

use anyhow::{Context as _, Result};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    net::UnixListener,
    sync::RwLock,
    time,
};
use tracing::{error, info, warn};
use uuid::Uuid;
use zbus::interface;

mod context;
mod memory;
mod security;

use context::ContextMonitor;
use memory::{MemoryNode, MemoryStore};

// ── Shared brain state ────────────────────────────────────────────────────────

/// Everything that must be shared between the DBus interface instance and the
/// IPC socket handler.  Cheap to `Arc::clone`.
#[derive(Debug)]
struct BrainState {
    memory:  Arc<MemoryStore>,
    context: Arc<ContextMonitor>,
    agents:  RwLock<HashMap<String, AgentInfo>>,
    tasks:   RwLock<HashMap<String, TaskHandle>>,
    enc_key: [u8; 32],
}

impl BrainState {
    fn new(memory: Arc<MemoryStore>, context: Arc<ContextMonitor>, enc_key: [u8; 32]) -> Self {
        Self {
            memory,
            context,
            agents:  RwLock::new(HashMap::new()),
            tasks:   RwLock::new(HashMap::new()),
            enc_key,
        }
    }
}

// ── Agent registry ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentInfo {
    pub id:             String,
    pub name:           String,
    pub capabilities:   Vec<String>,
    /// PID at registration time — re-verified on every call.
    pub pid:            u32,
    pub registered_at:  String,
}

/// Verify that the registered PID still exists under `/proc`.
fn pid_alive(pid: u32) -> bool {
    Path::new(&format!("/proc/{}", pid)).exists()
}

// ── Task coordination ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskHandle {
    pub id:             String,
    pub task:           String,
    pub assigned_agent: String,
    /// `"pending"` | `"running"` | `"done"` | `"failed"`
    pub status:         String,
    pub created_at:     String,
}

// ── DBus wrapper ──────────────────────────────────────────────────────────────

/// zbus requires a single concrete type; we wrap the shared `Arc<BrainState>`.
struct BrainDbus(Arc<BrainState>);

#[interface(name = "org.synthex.Brain")]
impl BrainDbus {
    // ── Memory ────────────────────────────────────────────────────────────────

    /// Store a value.  `value` must be valid JSON.
    /// `ttl_secs = 0` means no expiry.
    /// Returns the opaque memory ID.
    async fn remember(
        &self,
        key:      String,
        value:    String,
        ttl_secs: u64,
        tags:     Vec<String>,
    ) -> zbus::fdo::Result<String> {
        // Validate JSON
        serde_json::from_str::<serde_json::Value>(&value)
            .map_err(|e| zbus::fdo::Error::InvalidArgs(e.to_string()))?;
        let enc = security::encrypt_value(&self.0.enc_key, &value);
        let ttl = (ttl_secs > 0).then_some(ttl_secs);
        self.0
            .memory
            .remember(&key, &enc, ttl, &tags)
            .await
            .map_err(dbus_err)
    }

    /// Full-text search over keys and tags.  Returns JSON array of MemoryNode.
    async fn recall(&self, query: String, limit: u32) -> zbus::fdo::Result<String> {
        let nodes = self.0.memory.recall(&query, limit as usize).await.map_err(dbus_err)?;
        json_ok(decrypt_nodes(nodes, &self.0.enc_key))
    }

    /// Return all memories with the given tag.  Returns JSON array of MemoryNode.
    async fn recall_by_tag(&self, tag: String) -> zbus::fdo::Result<String> {
        let nodes = self.0.memory.recall_by_tag(&tag).await.map_err(dbus_err)?;
        json_ok(decrypt_nodes(nodes, &self.0.enc_key))
    }

    /// Delete a memory by ID.
    async fn forget(&self, id: String) -> zbus::fdo::Result<()> {
        self.0.memory.forget(&id).await.map_err(dbus_err)
    }

    // ── Context ───────────────────────────────────────────────────────────────

    /// Return current system context as a JSON object.
    async fn get_context(&self) -> zbus::fdo::Result<String> {
        json_ok(self.0.context.snapshot().await)
    }

    /// Override a single context field (`field` = JSON-encoded value).
    async fn update_context(&self, field: String, value: String) -> zbus::fdo::Result<()> {
        let v: serde_json::Value = serde_json::from_str(&value)
            .map_err(|e| zbus::fdo::Error::InvalidArgs(e.to_string()))?;
        self.0.context.update_field(&field, v).await.map_err(dbus_err)
    }

    // ── Agent registry ────────────────────────────────────────────────────────

    /// Register an agent.  `pid` must be a currently-running process.
    /// Returns the new agent ID.
    async fn register_agent(
        &self,
        name:         String,
        capabilities: Vec<String>,
        pid:          u32,
    ) -> zbus::fdo::Result<String> {
        if !pid_alive(pid) {
            return Err(zbus::fdo::Error::InvalidArgs(
                format!("PID {pid} does not exist"),
            ));
        }
        let id = Uuid::new_v4().to_string();
        let agent = AgentInfo {
            id: id.clone(),
            name,
            capabilities,
            pid,
            registered_at: Utc::now().to_rfc3339(),
        };
        self.0.agents.write().await.insert(id.clone(), agent);
        info!(agent_id = %id, pid, "agent registered");
        Ok(id)
    }

    /// List live agents (dead PIDs are pruned automatically).
    async fn list_agents(&self) -> zbus::fdo::Result<String> {
        let mut agents = self.0.agents.write().await;
        agents.retain(|_, a| pid_alive(a.pid));
        json_ok(agents.values().collect::<Vec<_>>())
    }

    // ── Task coordination ─────────────────────────────────────────────────────

    /// Assign a task.  `preferred_agent` may be empty to auto-select.
    /// Returns the task handle ID as a JSON string.
    async fn coordinate_task(
        &self,
        task:            String,
        preferred_agent: String,
    ) -> zbus::fdo::Result<String> {
        let agents = self.0.agents.read().await;
        let assigned = select_agent(&agents, &preferred_agent)?;
        drop(agents);

        let handle = TaskHandle {
            id:             Uuid::new_v4().to_string(),
            task:           task.clone(),
            assigned_agent: assigned,
            status:         "pending".into(),
            created_at:     Utc::now().to_rfc3339(),
        };
        let id = handle.id.clone();
        self.0.tasks.write().await.insert(id.clone(), handle);

        // Persist task in memory with 24 h TTL
        let enc = security::encrypt_value(
            &self.0.enc_key,
            &format!(r#"{{"task":{},"id":{:?}}}"#, serde_json::json!(task), id),
        );
        let _ = self.0.memory.remember(&format!("task:{id}"), &enc, Some(86_400), &["task".into()]).await;

        json_ok(id)
    }

    // ── Workspace ─────────────────────────────────────────────────────────────

    /// Return workspace list as JSON array.  Falls back to context if KWin unavailable.
    async fn get_workspace_state(&self) -> zbus::fdo::Result<String> {
        match query_workspaces().await {
            Ok(ws)  => json_ok(ws),
            Err(e)  => {
                warn!("KWin workspace query failed: {e}");
                let snap = self.0.context.snapshot().await;
                json_ok(vec![serde_json::json!({
                    "number":  snap.current_workspace,
                    "name":    format!("Workspace {}", snap.current_workspace),
                    "windows": [{ "id": 0, "title": snap.active_window_title,
                                  "app": snap.active_window_app, "pid": snap.active_window_pid }],
                })])
            }
        }
    }

    /// Switch to workspace N (1-based).
    async fn switch_workspace(&self, n: u32) -> zbus::fdo::Result<()> {
        xdotool_set_desktop(n).await.map_err(dbus_err)
    }

    /// Move window `window_id` to workspace `workspace` (1-based).
    async fn move_window_to_workspace(
        &self,
        window_id: u64,
        workspace: u32,
    ) -> zbus::fdo::Result<()> {
        tokio::process::Command::new("xdotool")
            .args(["set_desktop_for_window", &window_id.to_string(),
                   &workspace.saturating_sub(1).to_string()])
            .status()
            .await
            .map_err(|e| dbus_err(anyhow::anyhow!(e)))?;
        Ok(())
    }

    // ── Clipboard ─────────────────────────────────────────────────────────────

    /// Return clipboard as JSON `{"text":"…","mime_type":"text/plain"}`.
    async fn get_clipboard(&self) -> zbus::fdo::Result<String> {
        let text = clipboard_get().await.unwrap_or_default();
        json_ok(serde_json::json!({ "text": text, "mime_type": "text/plain" }))
    }

    /// Set clipboard text.
    async fn set_clipboard(&self, content: String) -> zbus::fdo::Result<()> {
        clipboard_set(&content).await.map_err(dbus_err)
    }
}

// ── Helper fns for the interface ──────────────────────────────────────────────

fn dbus_err(e: anyhow::Error) -> zbus::fdo::Error {
    zbus::fdo::Error::Failed(e.to_string())
}

fn json_ok<T: Serialize>(v: T) -> zbus::fdo::Result<String> {
    serde_json::to_string(&v).map_err(|e| zbus::fdo::Error::Failed(e.to_string()))
}

fn select_agent<'a>(
    agents: &'a HashMap<String, AgentInfo>,
    preferred: &str,
) -> zbus::fdo::Result<String> {
    if !preferred.is_empty() {
        if let Some(a) = agents.get(preferred) {
            if pid_alive(a.pid) {
                return Ok(preferred.to_string());
            }
        }
    }
    // Pick any live agent
    agents
        .values()
        .find(|a| pid_alive(a.pid))
        .map(|a| a.id.clone())
        .ok_or_else(|| zbus::fdo::Error::Failed("No live agents available".into()))
}

fn decrypt_nodes(nodes: Vec<MemoryNode>, key: &[u8; 32]) -> Vec<serde_json::Value> {
    nodes
        .into_iter()
        .map(|n| {
            let value_str = security::decrypt_value(key, &n.value_enc)
                .ok()
                .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
                .unwrap_or(serde_json::Value::Null);
            serde_json::json!({
                "id":           n.id,
                "key":          n.key,
                "value":        value_str,
                "created_at":   n.created_at,
                "accessed_at":  n.accessed_at,
                "access_count": n.access_count,
                "weight":       n.weight,
                "ttl_secs":     n.ttl_secs,
                "tags":         n.tags,
            })
        })
        .collect()
}

// ── Workspace helpers ─────────────────────────────────────────────────────────

async fn query_workspaces() -> Result<Vec<serde_json::Value>> {
    // Ask xdotool for all visible windows
    let out = tokio::process::Command::new("xdotool")
        .args(["search", "--onlyvisible", "--name", ""])
        .output()
        .await
        .context("xdotool unavailable")?;

    let ws_num = xdotool_desktop().await.unwrap_or(1);
    let mut windows = Vec::new();

    for id_str in String::from_utf8_lossy(&out.stdout).lines() {
        let id_str = id_str.trim();
        if id_str.is_empty() { continue; }
        let Ok(id) = id_str.parse::<u64>() else { continue };

        let title_out = tokio::process::Command::new("xdotool")
            .args(["getwindowname", id_str])
            .output().await.ok();
        let title = title_out
            .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
            .unwrap_or_default();

        let pid_out = tokio::process::Command::new("xdotool")
            .args(["getwindowpid", id_str])
            .output().await.ok();
        let pid: u32 = pid_out
            .and_then(|o| String::from_utf8_lossy(&o.stdout).trim().parse().ok())
            .unwrap_or(0);

        let app = (pid > 0)
            .then(|| std::fs::read_to_string(format!("/proc/{pid}/comm"))
                .unwrap_or_default()
                .trim()
                .to_string())
            .unwrap_or_default();

        windows.push(serde_json::json!({ "id": id, "title": title, "app": app, "pid": pid }));
    }

    Ok(vec![serde_json::json!({
        "number":  ws_num,
        "name":    format!("Workspace {ws_num}"),
        "windows": windows,
    })])
}

async fn xdotool_desktop() -> Option<u32> {
    let out = tokio::process::Command::new("xdotool")
        .args(["get_desktop"])
        .output().await.ok()?;
    let n: u32 = String::from_utf8_lossy(&out.stdout).trim().parse().ok()?;
    Some(n + 1)
}

async fn xdotool_set_desktop(n: u32) -> Result<()> {
    tokio::process::Command::new("xdotool")
        .args(["set_desktop", &n.saturating_sub(1).to_string()])
        .status()
        .await
        .context("xdotool set_desktop failed")?;
    Ok(())
}

// ── Clipboard helpers ─────────────────────────────────────────────────────────

async fn clipboard_get() -> Result<String> {
    // Try xclip first, fall back to xsel
    let out = tokio::process::Command::new("xclip")
        .args(["-selection", "clipboard", "-o"])
        .output()
        .await
        .or_else(|_| {
            std::process::Command::new("xsel")
                .args(["--clipboard", "--output"])
                .output()
        })
        .context("xclip/xsel not available")?;
    Ok(String::from_utf8_lossy(&out.stdout).into_owned())
}

async fn clipboard_set(text: &str) -> Result<()> {
    let text = text.to_string();
    let mut child = tokio::process::Command::new("xclip")
        .args(["-selection", "clipboard"])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .or_else(|_| {
            tokio::process::Command::new("xsel")
                .args(["--clipboard", "--input"])
                .stdin(std::process::Stdio::piped())
                .spawn()
        })
        .context("xclip/xsel not available")?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(text.as_bytes()).await?;
    }
    child.wait().await?;
    Ok(())
}

// ── Unix IPC socket ───────────────────────────────────────────────────────────

/// Newline-delimited JSON protocol:
///   Request:  `{"method":"<name>","params":{…}}\n`
///   Response: `{"ok":true,"result":<value>}\n`
///          or `{"ok":false,"error":"<msg>"}\n`
async fn run_ipc_socket(state: Arc<BrainState>) -> Result<()> {
    let path = "/run/synthex/brain.sock";
    let _ = std::fs::remove_file(path); // remove stale socket if any
    std::fs::create_dir_all("/run/synthex")
        .context("Failed to create /run/synthex")?;

    let listener = UnixListener::bind(path)
        .with_context(|| format!("Failed to bind IPC socket at {path}"))?;
    info!(path, "IPC socket ready");

    loop {
        match listener.accept().await {
            Ok((stream, _)) => {
                let st = Arc::clone(&state);
                tokio::spawn(async move {
                    if let Err(e) = handle_ipc(stream, st).await {
                        warn!("IPC client error: {e}");
                    }
                });
            }
            Err(e) => error!("IPC accept: {e}"),
        }
    }
}

async fn handle_ipc(stream: tokio::net::UnixStream, state: Arc<BrainState>) -> Result<()> {
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();

    while let Some(line) = lines.next_line().await? {
        let resp = match serde_json::from_str::<IpcRequest>(&line) {
            Err(e) => ipc_err(format!("JSON parse error: {e}")),
            Ok(req) => dispatch_ipc(req, &state).await,
        };
        let mut out = serde_json::to_string(&resp)?;
        out.push('\n');
        writer.write_all(out.as_bytes()).await?;
    }
    Ok(())
}

#[derive(Deserialize)]
struct IpcRequest {
    method: String,
    #[serde(default)]
    params: serde_json::Value,
}

#[derive(Serialize)]
struct IpcResponse {
    ok:     bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error:  Option<String>,
}

fn ipc_ok(v: serde_json::Value) -> IpcResponse {
    IpcResponse { ok: true, result: Some(v), error: None }
}
fn ipc_err(msg: String) -> IpcResponse {
    IpcResponse { ok: false, result: None, error: Some(msg) }
}

async fn dispatch_ipc(req: IpcRequest, state: &BrainState) -> IpcResponse {
    macro_rules! try_ipc {
        ($expr:expr) => {
            match $expr {
                Ok(v)  => v,
                Err(e) => return ipc_err(e.to_string()),
            }
        };
    }

    match req.method.as_str() {
        "remember" => {
            let key  = req.params["key"].as_str().unwrap_or("").to_string();
            let val  = req.params["value"].to_string();
            let ttl  = req.params["ttl_secs"].as_u64().unwrap_or(0);
            let tags: Vec<String> = req.params["tags"]
                .as_array()
                .map(|a| a.iter().filter_map(|v| v.as_str().map(String::from)).collect())
                .unwrap_or_default();
            let enc  = security::encrypt_value(&state.enc_key, &val);
            let id   = try_ipc!(state.memory.remember(&key, &enc, (ttl>0).then_some(ttl), &tags).await);
            ipc_ok(serde_json::json!(id))
        }
        "recall" => {
            let q     = req.params["query"].as_str().unwrap_or("").to_string();
            let limit = req.params["limit"].as_u64().unwrap_or(10) as usize;
            let nodes = try_ipc!(state.memory.recall(&q, limit).await);
            ipc_ok(serde_json::json!(decrypt_nodes(nodes, &state.enc_key)))
        }
        "recall_by_tag" => {
            let tag   = req.params["tag"].as_str().unwrap_or("").to_string();
            let nodes = try_ipc!(state.memory.recall_by_tag(&tag).await);
            ipc_ok(serde_json::json!(decrypt_nodes(nodes, &state.enc_key)))
        }
        "forget" => {
            let id = req.params["id"].as_str().unwrap_or("").to_string();
            try_ipc!(state.memory.forget(&id).await);
            ipc_ok(serde_json::json!(null))
        }
        "get_context" => {
            let snap = state.context.snapshot().await;
            ipc_ok(try_ipc!(serde_json::to_value(snap).map_err(anyhow::Error::from)))
        }
        "list_agents" => {
            let agents = state.agents.read().await;
            let live: Vec<_> = agents.values().filter(|a| pid_alive(a.pid)).collect();
            ipc_ok(try_ipc!(serde_json::to_value(&live).map_err(anyhow::Error::from)))
        }
        other => ipc_err(format!("Unknown method: {other}")),
    }
}

// ── Consolidation loop ────────────────────────────────────────────────────────

async fn consolidation_loop(memory: Arc<MemoryStore>) {
    let mut interval = time::interval(Duration::from_secs(600)); // 10 min
    interval.set_missed_tick_behavior(time::MissedTickBehavior::Skip);
    loop {
        interval.tick().await;
        match memory.consolidate().await {
            Ok(stats) => info!(
                expired  = stats.expired,
                forgotten = stats.forgotten,
                remaining = stats.remaining,
                "memory consolidation complete"
            ),
            Err(e) => error!("Memory consolidation error: {e}"),
        }
    }
}

// ── Entry point ───────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    // ── Logging ───────────────────────────────────────────────────────────────
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("synthex_brain=info".parse()?)
                .add_directive("warn".parse()?),
        )
        .with_target(false)
        .init();

    info!(
        version = env!("CARGO_PKG_VERSION"),
        "SynthOS Brain daemon starting"
    );

    // ── Encryption key ────────────────────────────────────────────────────────
    let enc_key = security::derive_machine_key();
    info!("Encryption key derived from machine identity");

    // ── Memory store ──────────────────────────────────────────────────────────
    let db_path = "/var/lib/synthex/brain/memory.db";
    if let Some(parent) = Path::new(db_path).parent() {
        std::fs::create_dir_all(parent)
            .with_context(|| format!("Cannot create DB dir {}", parent.display()))?;
    }
    let memory = Arc::new(
        MemoryStore::open(db_path).context("Failed to open memory database")?,
    );

    // ── Context monitor ───────────────────────────────────────────────────────
    let context = Arc::new(ContextMonitor::new());
    {
        let ctx = Arc::clone(&context);
        tokio::spawn(async move { ctx.run_poll_loop().await });
    }

    // ── Shared state ──────────────────────────────────────────────────────────
    let state = Arc::new(BrainState::new(
        Arc::clone(&memory),
        Arc::clone(&context),
        enc_key,
    ));

    // ── Background tasks ──────────────────────────────────────────────────────
    tokio::spawn(consolidation_loop(Arc::clone(&memory)));

    {
        let st = Arc::clone(&state);
        tokio::spawn(async move {
            if let Err(e) = run_ipc_socket(st).await {
                error!("IPC socket fatal: {e}");
            }
        });
    }

    // ── DBus service ──────────────────────────────────────────────────────────
    // BrainDbus wraps a second Arc clone — identical underlying data.
    let dbus_iface = BrainDbus(Arc::clone(&state));

    let _conn = zbus::connection::Builder::system()
        .context("Cannot connect to system DBus")?
        .name("org.synthex.Brain")
        .context("Cannot claim org.synthex.Brain")?
        .serve_at("/org/synthex/Brain", dbus_iface)
        .context("Cannot serve at /org/synthex/Brain")?
        .build()
        .await
        .context("Failed to build DBus connection")?;

    info!("DBus service live: org.synthex.Brain → /org/synthex/Brain");

    // ── Wait for shutdown ─────────────────────────────────────────────────────
    tokio::signal::ctrl_c().await?;
    info!("SIGINT received — shutting down cleanly");
    Ok(())
}
