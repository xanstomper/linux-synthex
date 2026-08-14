mod providers;
mod session;
mod tools;

use anyhow::{Context, Result};
use chrono::Duration as ChronoDuration;
use providers::{AutoProvider, ChatRequest, Message};
use serde::Serialize;
use session::{Session, SessionStore};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::io::AsyncWriteExt;
use tokio::signal::unix::{signal, SignalKind};
use tokio::sync::RwLock;
use tools::{ToolCall, ToolRegistry};
use tracing::{info, warn};
use zbus::{connection, interface};

// ── Audit logging ─────────────────────────────────────────────────────────────

const AUDIT_LOG: &str = "/var/log/synthex/hermes-audit.log";
const SESSION_DIR: &str = "/var/lib/synthex/hermes/sessions";
const SESSION_MAX_AGE_HOURS: i64 = 24;

async fn audit_log(entry: impl serde::Serialize) {
    let line = match serde_json::to_string(&entry) {
        Ok(s) => format!("{s}\n"),
        Err(e) => {
            warn!("audit: serialise error: {e}");
            return;
        }
    };

    // Best-effort: ignore errors (don't crash the daemon)
    match tokio::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(AUDIT_LOG)
        .await
    {
        Ok(mut file) => {
            if let Err(e) = file.write_all(line.as_bytes()).await {
                warn!("audit: write error: {e}");
            }
        }
        Err(e) => warn!("audit: open {AUDIT_LOG} failed: {e}"),
    }
}

#[derive(Serialize)]
struct AuditEntry<'a> {
    timestamp: String,
    event: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    session_id: Option<&'a str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    tool: Option<&'a str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    detail: Option<&'a str>,
}

impl<'a> AuditEntry<'a> {
    fn new(event: &'a str) -> Self {
        Self {
            timestamp: chrono::Utc::now().to_rfc3339(),
            event,
            session_id: None,
            tool: None,
            detail: None,
        }
    }
    fn session(mut self, id: &'a str) -> Self {
        self.session_id = Some(id);
        self
    }
    fn tool(mut self, name: &'a str) -> Self {
        self.tool = Some(name);
        self
    }
    fn detail(mut self, d: &'a str) -> Self {
        self.detail = Some(d);
        self
    }
}

// ── Shared daemon state ───────────────────────────────────────────────────────

struct HermesState {
    provider: AutoProvider,
    sessions: RwLock<HashMap<String, Session>>,
    store: SessionStore,
}

impl HermesState {
    fn new() -> Self {
        let ollama_url = std::env::var("OLLAMA_URL")
            .unwrap_or_else(|_| "http://localhost:11434".to_string());
        let anthropic_key = std::env::var("ANTHROPIC_API_KEY").ok();

        if anthropic_key.is_none() {
            warn!("ANTHROPIC_API_KEY not set — Anthropic fallback disabled");
        }

        Self {
            provider: AutoProvider::new(ollama_url, anthropic_key),
            sessions: RwLock::new(HashMap::new()),
            store: SessionStore::new(SESSION_DIR),
        }
    }
}

// ── DBus interface ────────────────────────────────────────────────────────────

struct HermesInterface {
    state: Arc<HermesState>,
}

#[interface(name = "org.synthex.Hermes1")]
impl HermesInterface {
    /// Create a new chat session; returns the session ID.
    async fn new_session(&self) -> zbus::fdo::Result<String> {
        let session = Session::new();
        let id = session.id.clone();
        info!("new_session: {id}");

        self.state
            .sessions
            .write()
            .await
            .insert(id.clone(), session.clone());

        if let Err(e) = self.state.store.save(&session).await {
            warn!("new_session: could not persist session {id}: {e:#}");
        }

        audit_log(AuditEntry::new("new_session").session(&id)).await;
        Ok(id)
    }

    /// End a session and remove it from memory (file kept for 24 h).
    async fn end_session(&self, session_id: &str) -> zbus::fdo::Result<bool> {
        let removed = self
            .state
            .sessions
            .write()
            .await
            .remove(session_id)
            .is_some();
        info!("end_session: {session_id} removed={removed}");
        audit_log(AuditEntry::new("end_session").session(session_id)).await;
        Ok(removed)
    }

    /// Send a chat message; returns the assistant reply.
    ///
    /// `session_id`  – ID from new_session (use "" to create an ephemeral session)
    /// `user_message` – the user turn text
    /// `model`        – optional model override (use "" for auto)
    async fn chat(
        &self,
        session_id: &str,
        user_message: &str,
        model: &str,
    ) -> zbus::fdo::Result<String> {
        // Resolve session
        let sid = if session_id.is_empty() {
            let s = Session::new();
            let id = s.id.clone();
            self.state.sessions.write().await.insert(id.clone(), s);
            id
        } else {
            session_id.to_string()
        };

        info!("chat: session={sid} msg_len={}", user_message.len());
        audit_log(
            AuditEntry::new("chat")
                .session(&sid)
                .detail(&format!("len={}", user_message.len())),
        )
        .await;

        // Build message list
        let messages: Vec<Message> = {
            let mut sessions = self.state.sessions.write().await;
            let session = sessions.entry(sid.clone()).or_insert_with(Session::new);
            session.push_message("user", user_message);
            session.messages.clone()
        };

        let req = ChatRequest {
            messages,
            model: if model.is_empty() {
                None
            } else {
                Some(model.to_string())
            },
            stream: true,
        };

        let response = self
            .state
            .provider
            .chat_stream(req)
            .await
            .map_err(|e| zbus::fdo::Error::Failed(format!("provider error: {e:#}")))?;

        // Store assistant turn
        {
            let mut sessions = self.state.sessions.write().await;
            if let Some(session) = sessions.get_mut(&sid) {
                session.push_message("assistant", &response.content);
                let tokens = response
                    .input_tokens
                    .unwrap_or(0)
                    .saturating_add(response.output_tokens.unwrap_or(0));
                session.add_tokens(tokens);
                if let Err(e) = self.state.store.save(session).await {
                    warn!("chat: could not persist session {sid}: {e:#}");
                }
            }
        }

        Ok(response.content)
    }

    /// Execute a registered tool by name.
    ///
    /// `tool_name`  – e.g. "ReadFile"
    /// `params_json` – JSON object of parameters
    ///
    /// Returns a JSON-encoded ToolResult.
    async fn execute_tool(
        &self,
        session_id: &str,
        tool_name: &str,
        params_json: &str,
    ) -> zbus::fdo::Result<String> {
        info!("execute_tool: session={session_id} tool={tool_name}");
        audit_log(
            AuditEntry::new("execute_tool")
                .session(session_id)
                .tool(tool_name),
        )
        .await;

        let params: HashMap<String, serde_json::Value> =
            serde_json::from_str(params_json).unwrap_or_default();

        let call = ToolCall {
            tool: tool_name.to_string(),
            params,
        };

        let result = ToolRegistry::execute(&call).await;

        audit_log(
            AuditEntry::new("tool_result")
                .session(session_id)
                .tool(tool_name)
                .detail(if result.success { "ok" } else { "error" }),
        )
        .await;

        serde_json::to_string(&result)
            .map_err(|e| zbus::fdo::Error::Failed(format!("serialise error: {e}")))
    }

    /// Return a JSON array of available tool descriptors.
    async fn get_available_tools(&self) -> zbus::fdo::Result<String> {
        let tools = ToolRegistry::available_tools();
        serde_json::to_string(&tools)
            .map_err(|e| zbus::fdo::Error::Failed(format!("serialise error: {e}")))
    }

    /// Return a JSON object with daemon status.
    async fn get_status(&self) -> zbus::fdo::Result<String> {
        let session_count = self.state.sessions.read().await.len();
        let provider_healthy = self.state.provider.health_check().await;

        #[derive(Serialize)]
        struct Status {
            version: &'static str,
            active_sessions: usize,
            provider_healthy: bool,
            timestamp: String,
        }

        let status = Status {
            version: env!("CARGO_PKG_VERSION"),
            active_sessions: session_count,
            provider_healthy,
            timestamp: chrono::Utc::now().to_rfc3339(),
        };

        serde_json::to_string(&status)
            .map_err(|e| zbus::fdo::Error::Failed(format!("serialise error: {e}")))
    }
}

// Use `providers::AIProvider` in health_check above
use providers::AIProvider as _;

// ── Background tasks ──────────────────────────────────────────────────────────

/// Periodically evict expired sessions from memory and disk.
async fn session_cleanup_task(state: Arc<HermesState>) {
    let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(3600));
    let max_age = ChronoDuration::hours(SESSION_MAX_AGE_HOURS);
    loop {
        interval.tick().await;
        info!("session cleanup: running");

        // Evict from memory
        {
            let mut sessions = state.sessions.write().await;
            sessions.retain(|_, s| !s.is_expired(max_age));
        }

        // Evict from disk
        if let Err(e) = state.store.cleanup_expired(max_age).await {
            warn!("session cleanup: disk cleanup error: {e:#}");
        }
    }
}

// ── Entry point ───────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    // Logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_env("RUST_LOG")
                .add_directive(tracing::Level::INFO.into()),
        )
        .init();

    info!(
        "synthex-hermes {} starting",
        env!("CARGO_PKG_VERSION")
    );

    // Ensure log dir exists (best-effort)
    if let Some(log_dir) = std::path::Path::new(AUDIT_LOG).parent() {
        if let Err(e) = std::fs::create_dir_all(log_dir) {
            warn!("cannot create log dir {log_dir:?}: {e}");
        }
    }

    // Shared state
    let state = Arc::new(HermesState::new());

    // Init session store
    state
        .store
        .init()
        .await
        .context("initialising session store")?;

    audit_log(AuditEntry::new("daemon_start")).await;

    // Spawn background cleanup
    tokio::spawn(session_cleanup_task(Arc::clone(&state)));

    // Build DBus interface
    let iface = HermesInterface {
        state: Arc::clone(&state),
    };

    info!("connecting to session bus as org.synthex.Hermes");
    let conn = connection::Builder::session()
        .context("connecting to session bus")?
        .name("org.synthex.Hermes")
        .context("requesting bus name")?
        .serve_at("/org/synthex/Hermes", iface)
        .context("serving DBus interface")?
        .build()
        .await
        .context("building DBus connection")?;

    info!("DBus service up at org.synthex.Hermes /org/synthex/Hermes");

    // Signal handling
    let mut sigterm =
        signal(SignalKind::terminate()).context("registering SIGTERM handler")?;
    let mut sighup =
        signal(SignalKind::hangup()).context("registering SIGHUP handler")?;

    loop {
        tokio::select! {
            _ = sigterm.recv() => {
                info!("SIGTERM received — shutting down gracefully");
                audit_log(AuditEntry::new("daemon_stop").detail("SIGTERM")).await;
                // Persist all in-memory sessions before exit
                let sessions = state.sessions.read().await;
                for (_, session) in sessions.iter() {
                    if let Err(e) = state.store.save(session).await {
                        warn!("shutdown: could not persist session {}: {e:#}", session.id);
                    }
                }
                break;
            }
            _ = sighup.recv() => {
                info!("SIGHUP received — reloading config");
                audit_log(AuditEntry::new("config_reload")).await;
                // Re-read env vars that can change at runtime
                if std::env::var("ANTHROPIC_API_KEY").is_ok() {
                    info!("ANTHROPIC_API_KEY present after reload");
                }
            }
            // Keep the connection alive
            _ = tokio::time::sleep(tokio::time::Duration::from_secs(60)) => {}
        }
    }

    // Drop connection explicitly so the bus name is released cleanly
    drop(conn);
    info!("synthex-hermes stopped");
    Ok(())
}
