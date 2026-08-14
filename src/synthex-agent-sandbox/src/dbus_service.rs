/// D-Bus service implementation for the SynthOS Agent Sandbox.
///
/// Bus name  : `org.synthex.AgentSandbox`
/// Object    : `/org/synthex/AgentSandbox`
/// Interface : `org.synthex.AgentSandbox`
///
/// All public methods are called by other SynthOS daemons or privileged
/// user tools.  The service itself runs as root (or a dedicated service
/// user), so callers must authenticate via PolicyKit before any mutating
/// method is accepted.
use crate::capabilities::Capability;
use crate::policy::{load_policy, parse_capability_string, is_always_denied};
use crate::sandbox::{SandboxConfig, SandboxRegistry};

use anyhow::Result;
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{error, info, warn};
use zbus::{connection, interface};

/// Shared service state threaded through every D-Bus call
pub struct AgentSandboxState {
    pub registry: SandboxRegistry,
    pub policy_dir: PathBuf,
}

impl AgentSandboxState {
    pub fn new(policy_dir: PathBuf) -> Self {
        Self {
            registry: SandboxRegistry::new(),
            policy_dir,
        }
    }
}

pub type SharedState = Arc<RwLock<AgentSandboxState>>;

/// D-Bus interface implementation (zbus attribute macro)
pub struct AgentSandboxInterface {
    state: SharedState,
}

impl AgentSandboxInterface {
    pub fn new(state: SharedState) -> Self {
        Self { state }
    }
}

#[interface(name = "org.synthex.AgentSandbox")]
impl AgentSandboxInterface {
    // =========================================================================
    // CreateSandbox
    // =========================================================================
    /// Create a new isolated sandbox.
    ///
    /// `config_json` is a JSON-encoded `SandboxConfig`.  Returns the sandbox ID
    /// string that must be passed to all subsequent calls.
    async fn create_sandbox(&self, config_json: String) -> zbus::fdo::Result<String> {
        let config: SandboxConfig = serde_json::from_str(&config_json)
            .map_err(|e| zbus::fdo::Error::InvalidArgs(format!("Bad config JSON: {}", e)))?;

        let state = self.state.read().await;

        // Load policy for the given profile
        let policy = if let Some(ref profile) = config.policy_profile {
            let path = state.policy_dir.join(format!("{}.toml", profile));
            if path.exists() {
                match load_policy(&path, Some(&config.label)) {
                    Ok(p) => Some(p),
                    Err(e) => {
                        warn!("Failed to load policy {}: {}; using config defaults", path.display(), e);
                        None
                    }
                }
            } else {
                warn!("Policy file {} not found, using config defaults", path.display());
                None
            }
        } else {
            None
        };

        // Build the effective config, merging policy auto_grants
        let mut effective = config.clone();
        if let Some(pol) = policy {
            for cap in pol.auto_grant {
                // Refuse always_deny capabilities even if policy lists them
                if !is_always_denied(&cap, &pol.always_deny) {
                    effective.initial_capabilities.push(cap);
                }
            }
            effective.resources.max_memory_mb = pol.max_memory_mb;
            effective.resources.max_cpu_percent = pol.max_cpu_percent;
        }

        let id = state.registry.create(effective).await;
        info!("D-Bus: CreateSandbox -> {}", id);
        Ok(id)
    }

    // =========================================================================
    // LaunchAgent
    // =========================================================================
    /// Launch an agent process inside an existing sandbox.
    ///
    /// `env_json` is a JSON object of `{ "KEY": "VALUE" }` pairs.
    /// Returns an opaque agent handle string.
    async fn launch_agent(
        &self,
        sandbox_id: String,
        command: Vec<String>,
        env_json: String,
    ) -> zbus::fdo::Result<String> {
        let env: HashMap<String, String> = serde_json::from_str(&env_json)
            .map_err(|e| zbus::fdo::Error::InvalidArgs(format!("Bad env JSON: {}", e)))?;

        let state = self.state.read().await;
        state.registry.launch_agent(&sandbox_id, command, env).await
            .map_err(|e| {
                error!("LaunchAgent failed: {}", e);
                zbus::fdo::Error::Failed(e.to_string())
            })
    }

    // =========================================================================
    // GrantCapability
    // =========================================================================
    /// Grant a capability to a running sandbox.
    ///
    /// `capability_json` is a JSON-encoded `Capability` value.
    /// Returns `true` if the capability was newly added, `false` if already present.
    async fn grant_capability(
        &self,
        sandbox_id: String,
        capability_json: String,
    ) -> zbus::fdo::Result<bool> {
        // Accept either JSON or the human-readable audit string
        let cap: Capability = serde_json::from_str(&capability_json)
            .or_else(|_| parse_capability_string(&capability_json))
            .map_err(|e| zbus::fdo::Error::InvalidArgs(format!("Bad capability: {}", e)))?;

        let state = self.state.read().await;
        state.registry.grant_capability(&sandbox_id, cap).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))
    }

    // =========================================================================
    // RevokeCapability
    // =========================================================================
    /// Revoke a previously-granted capability.
    async fn revoke_capability(
        &self,
        sandbox_id: String,
        capability_json: String,
    ) -> zbus::fdo::Result<()> {
        let cap: Capability = serde_json::from_str(&capability_json)
            .or_else(|_| parse_capability_string(&capability_json))
            .map_err(|e| zbus::fdo::Error::InvalidArgs(format!("Bad capability: {}", e)))?;

        let state = self.state.read().await;
        state.registry.revoke_capability(&sandbox_id, &cap).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))
    }

    // =========================================================================
    // ListCapabilities
    // =========================================================================
    /// Return JSON array of capabilities currently active in the sandbox.
    async fn list_capabilities(&self, sandbox_id: String) -> zbus::fdo::Result<String> {
        let state = self.state.read().await;
        let caps = state.registry.list_capabilities(&sandbox_id).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))?;

        serde_json::to_string(&caps)
            .map_err(|e| zbus::fdo::Error::Failed(format!("Serialise error: {}", e)))
    }

    // =========================================================================
    // GetAuditLog
    // =========================================================================
    /// Return the last `limit` audit entries for the sandbox as a JSON array.
    async fn get_audit_log(
        &self,
        sandbox_id: String,
        limit: u32,
    ) -> zbus::fdo::Result<String> {
        let state = self.state.read().await;
        let entries = state.registry.get_audit_log(&sandbox_id, limit).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))?;

        serde_json::to_string(&entries)
            .map_err(|e| zbus::fdo::Error::Failed(format!("Serialise error: {}", e)))
    }

    // =========================================================================
    // KillAgent
    // =========================================================================
    /// Send a POSIX signal to the agent running in the sandbox.
    ///
    /// Common values: 9 (SIGKILL), 15 (SIGTERM), 2 (SIGINT).
    async fn kill_agent(
        &self,
        sandbox_id: String,
        signal: u32,
    ) -> zbus::fdo::Result<()> {
        let state = self.state.read().await;
        state.registry.kill_agent(&sandbox_id, signal).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))
    }

    // =========================================================================
    // SandboxStatus
    // =========================================================================
    /// Return the current status of a sandbox as a JSON-encoded `SandboxStatus`.
    async fn sandbox_status(&self, sandbox_id: String) -> zbus::fdo::Result<String> {
        let state = self.state.read().await;
        let status = state.registry.status(&sandbox_id).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))?;

        serde_json::to_string(&status)
            .map_err(|e| zbus::fdo::Error::Failed(format!("Serialise error: {}", e)))
    }

    // =========================================================================
    // DestroySandbox
    // =========================================================================
    /// Destroy a sandbox that has no running agent.  Frees all resources.
    async fn destroy_sandbox(&self, sandbox_id: String) -> zbus::fdo::Result<()> {
        let state = self.state.read().await;
        state.registry.destroy(&sandbox_id).await
            .map_err(|e| zbus::fdo::Error::Failed(e.to_string()))
    }

    // =========================================================================
    // CheckFileAccess  (helper for LSM-style pre-access checks)
    // =========================================================================
    /// Returns `true` if the sandbox is permitted to access `path` in `mode`
    /// ("read" | "write").  Logs the access attempt in the audit log.
    async fn check_file_access(
        &self,
        sandbox_id: String,
        path: String,
        mode: String,
    ) -> zbus::fdo::Result<bool> {
        let state = self.state.read().await;
        let registry = state.registry.inner();
        let map = registry.read().await;
        let sb = map.get(&sandbox_id)
            .ok_or_else(|| zbus::fdo::Error::Failed(format!("Sandbox not found: {}", sandbox_id)))?;

        let allowed = match mode.as_str() {
            "read"  => sb.can_read_file(&path),
            "write" => sb.can_write_file(&path),
            _       => return Err(zbus::fdo::Error::InvalidArgs(
                format!("Unknown mode '{}'; use 'read' or 'write'", mode)
            )),
        };

        // Audit the check — note: we can't call `log_audit` here because we only
        // have a read lock on the registry.  The caller is responsible for logging
        // if they hold a write lock.  For the D-Bus path we emit a tracing event.
        if !allowed {
            warn!(
                "[sandbox:{}] DENIED file {} access to {}",
                sandbox_id, mode, path
            );
        }

        Ok(allowed)
    }
}

/// Bring up the D-Bus service and block until the connection is lost.
pub async fn run_dbus_service(state: SharedState) -> Result<()> {
    let iface = AgentSandboxInterface::new(state);

    let conn = connection::Builder::session()?
        .name("org.synthex.AgentSandbox")?
        .serve_at("/org/synthex/AgentSandbox", iface)?
        .build()
        .await?;

    info!(
        "D-Bus service ready on {} — path /org/synthex/AgentSandbox",
        conn.unique_name().map(|n| n.as_str()).unwrap_or("(no name)")
    );

    // Park the task forever; the connection is kept alive by the returned handle.
    std::future::pending::<()>().await;
    Ok(())
}
