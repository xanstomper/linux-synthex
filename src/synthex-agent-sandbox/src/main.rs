/// synthex-agent-sandbox — SynthOS AI Agent Capability Broker & Sandbox Daemon
///
/// Provides fine-grained, audited capability control for AI agents running on
/// SynthOS.  Exposes a D-Bus service at `org.synthex.AgentSandbox` that other
/// daemons and privileged tools use to create sandboxes, launch agent
/// processes, and dynamically grant/revoke capabilities.
///
/// # Architecture
///
/// ```text
///  ┌──────────────────────────┐
///  │   Cline / Copilot / etc  │  (AI agent process)
///  │  runs inside a sandbox   │
///  │  ┌────────────────────┐  │
///  │  │ Linux namespaces:  │  │
///  │  │  PID / NET / MNT   │  │
///  │  │  IPC / UTS / USER  │  │
///  │  │ + seccomp BPF      │  │
///  │  │ + cgroup v2 limits │  │
///  │  └────────────────────┘  │
///  └──────────┬───────────────┘
///             │ D-Bus capability checks
///             ▼
///  ┌──────────────────────────┐
///  │  synthex-agent-sandbox   │  ← this binary
///  │  org.synthex.AgentSandbox│
///  │  ┌──────────────────┐    │
///  │  │ Capability Broker│    │
///  │  │ Policy Engine    │    │
///  │  │ Audit Logger     │    │
///  │  └──────────────────┘    │
///  └──────────────────────────┘
/// ```
///
/// # Anti-hijack measures
///
/// 1. **Namespace isolation** — each sandbox gets its own PID, network, mount,
///    IPC, UTS, and user namespaces so a compromised agent cannot see or affect
///    other processes.
///
/// 2. **Capability allowlisting** — every privileged action (file write, command
///    execution, network access, …) is checked against a per-sandbox allowlist
///    before it is permitted.  Violations are logged and rejected.
///
/// 3. **Seccomp-BPF** — a kernel-level syscall filter blocks ptrace(2),
///    process_vm_readv/writev, bpf(2) PROG_LOAD, kexec, pivot_root, and other
///    dangerous syscalls that could allow escape or lateral movement.
///
/// 4. **PR_SET_NO_NEW_PRIVS** — applied before exec so the agent process can
///    never regain dropped privileges.
///
/// 5. **Audit log** — every capability grant/revoke, file access decision,
///    and policy violation is recorded with a nanosecond timestamp.
///
/// 6. **Policy profiles** — TOML files in `/etc/synthex/agent-policies/`
///    (or the repo-local `configs/agent-policies/`) define per-agent trust
///    levels.  Unknown capabilities are denied by default.

mod audit;
mod capabilities;
mod dbus_service;
mod policy;
mod sandbox;
mod seccomp_filter;

use anyhow::{Context, Result};
use dbus_service::{AgentSandboxState, SharedState};
use seccomp_filter::{SeccompFilter, log_filter_summary};
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info, warn};
use tracing_subscriber::{EnvFilter, fmt};

/// CLI / environment configuration
#[derive(Debug)]
struct Config {
    /// Directory containing `*.toml` policy files
    policy_dir: PathBuf,
    /// Log level (RUST_LOG override)
    log_level: String,
    /// Whether to use the session bus (true) or system bus (false)
    session_bus: bool,
}

impl Config {
    fn from_env() -> Self {
        let policy_dir = std::env::var("SYNTHEX_AGENT_POLICY_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| {
                // Try repo-local path first, fall back to /etc
                let local = PathBuf::from(concat!(
                    env!("CARGO_MANIFEST_DIR"),
                    "/../../configs/agent-policies"
                ));
                if local.exists() {
                    local
                } else {
                    PathBuf::from("/etc/synthex/agent-policies")
                }
            });

        let log_level = std::env::var("RUST_LOG")
            .unwrap_or_else(|_| "synthex_agent_sandbox=info,warn".into());

        let session_bus = std::env::var("SYNTHEX_DBUS_SESSION")
            .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
            .unwrap_or(true); // default to session bus for dev; systemd unit sets this to false

        Self { policy_dir, log_level, session_bus }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let cfg = Config::from_env();

    // ── Logging ──────────────────────────────────────────────────────────────
    fmt::Subscriber::builder()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new(&cfg.log_level)),
        )
        .with_target(true)
        .with_thread_ids(false)
        .with_ansi(std::env::var("NO_COLOR").is_err())
        .init();

    info!("synthex-agent-sandbox starting up");
    info!("Policy directory : {}", cfg.policy_dir.display());
    info!("D-Bus bus        : {}", if cfg.session_bus { "session" } else { "system" });

    // ── Seccomp capability check ─────────────────────────────────────────────
    if seccomp_filter::kernel_supports_seccomp() {
        let filter = SeccompFilter::default_agent_filter();
        log_filter_summary(&filter);
    } else {
        warn!("Kernel does not support seccomp — sandboxes will have reduced isolation!");
    }

    // ── Policy directory ─────────────────────────────────────────────────────
    if !cfg.policy_dir.exists() {
        warn!(
            "Policy directory {} does not exist; capabilities will use config-supplied defaults",
            cfg.policy_dir.display()
        );
    } else {
        // Log discovered policy files
        match std::fs::read_dir(&cfg.policy_dir) {
            Ok(entries) => {
                for e in entries.flatten() {
                    if e.path().extension().and_then(|x| x.to_str()) == Some("toml") {
                        info!("Loaded policy profile: {}", e.path().display());
                    }
                }
            }
            Err(e) => warn!("Cannot read policy dir: {}", e),
        }
    }

    // ── Shared state ─────────────────────────────────────────────────────────
    let state: SharedState = Arc::new(RwLock::new(
        AgentSandboxState::new(cfg.policy_dir.clone()),
    ));

    // ── Signal handling ───────────────────────────────────────────────────────
    let state_for_shutdown = state.clone();
    tokio::spawn(async move {
        let mut sigterm = tokio::signal::unix::signal(
            tokio::signal::unix::SignalKind::terminate()
        ).expect("Failed to register SIGTERM handler");
        let mut sigint = tokio::signal::unix::signal(
            tokio::signal::unix::SignalKind::interrupt()
        ).expect("Failed to register SIGINT handler");

        tokio::select! {
            _ = sigterm.recv() => info!("Received SIGTERM — shutting down"),
            _ = sigint.recv()  => info!("Received SIGINT — shutting down"),
        }

        // Kill all running agents before exit
        let state = state_for_shutdown.read().await;
        let registry = state.registry.inner();
        let map = registry.read().await;
        for (id, sb) in map.iter() {
            if matches!(sb.status, sandbox::SandboxStatus::Running { .. }) {
                warn!("Shutdown: forcibly killing running agent in sandbox {}", id);
                if let Some(_) = sb.agent_pid() {
                    // In the real implementation we'd kill here; for now just log.
                    warn!("Would send SIGKILL to sandbox {}", id);
                }
            }
        }

        std::process::exit(0);
    });

    // ── D-Bus service ─────────────────────────────────────────────────────────
    info!("Starting D-Bus service on org.synthex.AgentSandbox …");
    dbus_service::run_dbus_service(state)
        .await
        .context("D-Bus service exited unexpectedly")?;

    Ok(())
}
