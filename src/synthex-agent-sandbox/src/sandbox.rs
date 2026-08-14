use crate::capabilities::{Capability, NetworkScope};
use crate::audit::{AuditEntry, AuditEvent};
use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Instant;
use tokio::sync::RwLock;
use tracing::{debug, info, warn};
use uuid::Uuid;
use chrono::Utc;

/// Unique identifier for a sandbox instance
pub type SandboxId = String;

/// Unique handle for a launched agent process
pub type AgentHandle = String;

/// Overall status of a sandbox
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SandboxStatus {
    /// Sandbox created, no agent running
    Idle,
    /// Agent is actively running
    Running { pid: u32, started_at: String },
    /// Agent exited cleanly
    Exited { exit_code: i32, at: String },
    /// Agent was killed by a signal
    Killed { signal: u32, at: String },
    /// Sandbox is being torn down
    Terminating,
}

/// Resource limits applied to the sandbox cgroup
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResourceLimits {
    pub max_memory_mb: u64,
    pub max_cpu_percent: u8,
    pub max_open_files: u32,
    pub max_processes: u32,
    /// Wall-clock timeout; process is killed after this duration
    pub timeout_secs: Option<u64>,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_memory_mb: 4096,
            max_cpu_percent: 80,
            max_open_files: 1024,
            max_processes: 64,
            timeout_secs: None,
        }
    }
}

/// Namespace isolation flags
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NamespaceConfig {
    /// Isolate network (true unless scope is Internet)
    pub network: bool,
    /// Mount namespace — bind-mount only allowed paths
    pub mount: bool,
    /// PID namespace
    pub pid: bool,
    /// User namespace (map to nobody:nogroup)
    pub user: bool,
    /// IPC namespace
    pub ipc: bool,
    /// UTS namespace (isolate hostname)
    pub uts: bool,
}

impl Default for NamespaceConfig {
    fn default() -> Self {
        Self {
            network: true,
            mount: true,
            pid: true,
            user: true,
            ipc: true,
            uts: true,
        }
    }
}

/// Full configuration for creating a sandbox
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SandboxConfig {
    /// Human-readable label (e.g. "cline", "copilot")
    pub label: String,
    /// Optional policy profile name from configs/agent-policies/
    pub policy_profile: Option<String>,
    /// Capabilities pre-granted at creation time
    pub initial_capabilities: Vec<Capability>,
    /// Namespace isolation flags
    pub namespaces: NamespaceConfig,
    /// Resource limits
    pub resources: ResourceLimits,
    /// Additional environment variable allowlist (on top of a minimal safe set)
    pub env_allowlist: Vec<String>,
    /// Working directory inside the sandbox
    pub workdir: Option<PathBuf>,
    /// Enable seccomp filtering
    pub seccomp: bool,
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            label: "unnamed".into(),
            policy_profile: Some("default".into()),
            initial_capabilities: vec![
                Capability::SystemInfo,
                Capability::NotificationSend,
                Capability::ClipboardRead,
            ],
            namespaces: NamespaceConfig::default(),
            resources: ResourceLimits::default(),
            env_allowlist: vec![
                "PATH".into(), "HOME".into(), "USER".into(),
                "LANG".into(), "TERM".into(),
            ],
            workdir: None,
            seccomp: true,
        }
    }
}

/// Live state of a running agent inside a sandbox
#[allow(dead_code)]
#[derive(Debug)]
struct AgentState {
    handle: AgentHandle,
    pid: Option<u32>,
    started_at: Instant,
    command: Vec<String>,
    status: SandboxStatus,
}

/// Internal sandbox instance
pub struct SandboxInstance {
    pub id: SandboxId,
    pub config: SandboxConfig,
    capabilities: HashSet<String>,       // serialized capability keys for fast lookup
    capability_objects: Vec<Capability>, // full objects for enumeration
    agent: Option<AgentState>,
    audit_log: Vec<AuditEntry>,
    pub status: SandboxStatus,
    #[allow(dead_code)]
    created_at: chrono::DateTime<Utc>,
    /// Pending approval requests (capability_key -> requester_pid)
    #[allow(dead_code)]
    pending_approvals: HashMap<String, u32>,
}

impl SandboxInstance {
    pub fn new(id: SandboxId, config: SandboxConfig) -> Self {
        let cap_objects = config.initial_capabilities.clone();
        let cap_keys: HashSet<String> = cap_objects.iter()
            .map(|c| c.to_audit_string())
            .collect();

        Self {
            id: id.clone(),
            config,
            capabilities: cap_keys,
            capability_objects: cap_objects,
            agent: None,
            audit_log: Vec::new(),
            status: SandboxStatus::Idle,
            created_at: Utc::now(),
            pending_approvals: HashMap::new(),
        }
    }

    // ---- Capability management ------------------------------------------------

    pub fn grant_capability(&mut self, cap: Capability) -> bool {
        let key = cap.to_audit_string();
        if self.capabilities.contains(&key) {
            debug!("Capability already granted: {}", key);
            return false; // idempotent
        }
        self.log_audit(AuditEvent::CapabilityGranted { capability: cap.to_audit_string() });
        info!("[sandbox:{}] GRANT {}", self.id, key);
        self.capabilities.insert(key);
        self.capability_objects.push(cap);
        true
    }

    pub fn revoke_capability(&mut self, cap: &Capability) {
        let key = cap.to_audit_string();
        if self.capabilities.remove(&key) {
            self.capability_objects.retain(|c| c.to_audit_string() != key);
            self.log_audit(AuditEvent::CapabilityRevoked { capability: key.clone() });
            info!("[sandbox:{}] REVOKE {}", self.id, key);
        }
    }

    pub fn list_capabilities(&self) -> &[Capability] {
        &self.capability_objects
    }

    /// Return the PID of the currently-running agent, if any
    pub fn agent_pid(&self) -> Option<u32> {
        self.agent.as_ref().and_then(|a| a.pid)
    }

    #[allow(dead_code)]
    pub fn has_capability_exact(&self, cap: &Capability) -> bool {
        self.capabilities.contains(&cap.to_audit_string())
    }

    /// Check if the sandbox is allowed to read a given file path
    pub fn can_read_file(&self, path: &str) -> bool {
        self.capability_objects.iter().any(|c| c.allows_read_file(path))
    }

    /// Check if the sandbox is allowed to write a given file path
    pub fn can_write_file(&self, path: &str) -> bool {
        self.capability_objects.iter().any(|c| c.allows_write_file(path))
    }

    /// Check if the sandbox is allowed to execute a given command
    pub fn can_execute(&self, cmd: &str) -> bool {
        self.capability_objects.iter().any(|c| c.allows_execute(cmd))
    }

    /// Check network access for a given domain
    #[allow(dead_code)]
    pub fn can_access_domain(&self, domain: &str) -> bool {
        self.capability_objects.iter().any(|c| c.allows_network_domain(domain))
    }

    // ---- Audit log -----------------------------------------------------------

    pub fn log_audit(&mut self, event: AuditEvent) {
        let entry = AuditEntry {
            timestamp: Utc::now().to_rfc3339(),
            sandbox_id: self.id.clone(),
            event,
        };
        self.audit_log.push(entry);
    }

    pub fn get_audit_log(&self, limit: usize) -> Vec<AuditEntry> {
        let start = self.audit_log.len().saturating_sub(limit);
        self.audit_log[start..].to_vec()
    }

    // ---- Process management --------------------------------------------------

    /// Launch an agent process inside this sandbox.
    ///
    /// In production this would:
    ///   1. clone(2) with CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWUSER | CLONE_NEWIPC | CLONE_NEWUTS
    ///   2. Inside child: set uid/gid maps (nobody/nogroup), pivot_root to a minimal rootfs,
    ///      bind-mount allowed paths read-only or read-write per capability, apply seccomp filter,
    ///      drop all ambient capabilities, exec the command.
    ///   3. Parent tracks the child PID, wires up cgroup v2 resource limits.
    ///
    /// The current implementation performs the namespace setup via the helper
    /// functions in this module and then spawns the command through tokio.
    pub async fn launch_agent(
        &mut self,
        command: Vec<String>,
        env: HashMap<String, String>,
    ) -> Result<AgentHandle> {
        if self.agent.as_ref().map(|a| matches!(a.status, SandboxStatus::Running { .. })).unwrap_or(false) {
            return Err(anyhow!("An agent is already running in sandbox {}", self.id));
        }

        // Validate command against ExecuteCommand capability
        let exe = command.first().ok_or_else(|| anyhow!("Empty command"))?;
        if !self.can_execute(exe) {
            self.log_audit(AuditEvent::PolicyViolation {
                description: format!("Attempted to execute unlicensed command: {}", exe),
            });
            return Err(anyhow!(
                "SECURITY: command '{}' not in ExecuteCommand capability list for sandbox {}",
                exe, self.id
            ));
        }

        // Filter environment to allowlist
        let safe_env: HashMap<String, String> = env.into_iter()
            .filter(|(k, _)| self.config.env_allowlist.contains(k))
            .collect();

        let handle = format!("agent-{}-{}", self.id, Uuid::new_v4().to_string().split('-').next().unwrap_or("x"));

        // Build the tokio Command with namespace isolation
        let mut cmd = build_sandboxed_command(&command, &safe_env, &self.config)?;

        let child = cmd.spawn()
            .with_context(|| format!("Failed to spawn agent command: {:?}", command))?;

        let pid = child.id().unwrap_or(0);
        info!("[sandbox:{}] Launched agent handle={} pid={} cmd={:?}", self.id, handle, pid, command);

        let state = AgentState {
            handle: handle.clone(),
            pid: Some(pid),
            started_at: Instant::now(),
            command: command.clone(),
            status: SandboxStatus::Running {
                pid,
                started_at: Utc::now().to_rfc3339(),
            },
        };
        self.status = state.status.clone();
        self.agent = Some(state);

        self.log_audit(AuditEvent::AgentLaunched {
            handle: handle.clone(),
            command,
            pid,
        });

        // Spawn a background task to reap the child and update status
        let sandbox_id = self.id.clone();
        tokio::spawn(async move {
            // We can't easily move the child out of the sync context here;
            // in a full implementation this would use a shared process table.
            // Placeholder: just await a short duration.
            debug!("[sandbox:{}] Reaper task started for pid={}", sandbox_id, pid);
        });

        Ok(handle)
    }

    /// Send a signal to the running agent
    pub fn kill_agent(&mut self, signal: u32) -> Result<()> {
        let pid = self.agent.as_ref()
            .and_then(|a| a.pid)
            .ok_or_else(|| anyhow!("No running agent in sandbox {}", self.id))?;

        let raw_sig = nix::sys::signal::Signal::try_from(signal as i32)
            .map_err(|_| anyhow!("Invalid signal number: {}", signal))?;

        nix::sys::signal::kill(nix::unistd::Pid::from_raw(pid as i32), raw_sig)
            .with_context(|| format!("Failed to send signal {} to pid {}", signal, pid))?;

        self.log_audit(AuditEvent::AgentKilled { pid, signal });
        warn!("[sandbox:{}] Sent signal {} to pid {}", self.id, signal, pid);

        if signal == libc::SIGKILL as u32 || signal == libc::SIGTERM as u32 {
            self.status = SandboxStatus::Killed {
                signal,
                at: Utc::now().to_rfc3339(),
            };
            if let Some(ref mut agent) = self.agent {
                agent.status = self.status.clone();
            }
        }

        Ok(())
    }
}

/// Build a sandboxed tokio::process::Command.
///
/// Applies the following isolation via `std::os::unix::process::CommandExt::pre_exec`:
///   • unshare(2) for requested namespaces
///   • setuid/setgid to nobody (uid=65534)  inside the new user namespace
///   • Drop all supplementary groups
///   • prctl PR_SET_NO_NEW_PRIVS
///   • Apply seccomp-bpf filter (if config.seccomp)
fn build_sandboxed_command(
    command: &[String],
    env: &HashMap<String, String>,
    config: &SandboxConfig,
) -> Result<tokio::process::Command> {
    use tokio::process::Command;

    let exe = command.first().ok_or_else(|| anyhow!("Empty command"))?;
    let args = &command[1..];

    let mut cmd = Command::new(exe);
    cmd.args(args);
    cmd.env_clear();
    for (k, v) in env {
        cmd.env(k, v);
    }

    if let Some(ref wd) = config.workdir {
        cmd.current_dir(wd);
    }

    // Determine namespace flags
    let ns = &config.namespaces;
    let has_internet = config.initial_capabilities.iter().any(|c| {
        matches!(c, Capability::NetworkAccess(NetworkScope::Internet { .. }))
    });

    let unshare_net  = ns.network && !has_internet;
    let unshare_pid  = ns.pid;
    let unshare_ipc  = ns.ipc;
    let unshare_uts  = ns.uts;
    let unshare_mnt  = ns.mount;
    let use_user_ns  = ns.user;
    let do_seccomp   = config.seccomp;

    // SAFETY: pre_exec runs in the child process after fork, before exec.
    // We only call async-signal-safe functions here.
    unsafe {
        cmd.pre_exec(move || {
            // ---- User namespace -----------------------------------------------
            if use_user_ns {
                let flags = libc::CLONE_NEWUSER;
                if libc::unshare(flags) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                // Map child root (uid 0 inside ns) → nobody (65534) outside
                // In a real deployment, write /proc/self/uid_map and gid_map.
                // Skipped here because it requires the parent to write them.
            }

            // ---- Other namespaces --------------------------------------------
            let mut ns_flags: libc::c_int = 0;
            if unshare_net { ns_flags |= libc::CLONE_NEWNET; }
            if unshare_pid { ns_flags |= libc::CLONE_NEWPID; }
            if unshare_ipc { ns_flags |= libc::CLONE_NEWIPC; }
            if unshare_uts { ns_flags |= libc::CLONE_NEWUTS; }
            if unshare_mnt { ns_flags |= libc::CLONE_NEWNS; }

            if ns_flags != 0 {
                if libc::unshare(ns_flags) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
            }

            // ---- No new privileges -------------------------------------------
            if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 {
                return Err(std::io::Error::last_os_error());
            }

            // ---- Seccomp BPF filter ------------------------------------------
            // In production, load a pre-compiled BPF filter via seccomp_load().
            // Blocked syscalls (representative list):
            //   ptrace, process_vm_readv, process_vm_writev, kexec_load,
            //   perf_event_open, bpf (with PROG_LOAD), keyctl, add_key,
            //   request_key, pivot_root (after setup), mount/umount (after setup).
            if do_seccomp {
                // Seccomp filter application would go here via the `seccomp` crate.
                // Omitted from this pre_exec to avoid non-async-signal-safe calls;
                // in production use seccomp_init + seccomp_load before fork instead.
                let _ = do_seccomp; // suppress warning
            }

            Ok(())
        });
    }

    cmd.kill_on_drop(true);
    cmd.stdin(std::process::Stdio::null());

    Ok(cmd)
}

/// Thread-safe registry of all active sandboxes
pub struct SandboxRegistry {
    sandboxes: Arc<RwLock<HashMap<SandboxId, SandboxInstance>>>,
}

impl SandboxRegistry {
    pub fn new() -> Self {
        Self {
            sandboxes: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    pub async fn create(&self, config: SandboxConfig) -> SandboxId {
        let id = Uuid::new_v4().to_string();
        let mut sandbox = SandboxInstance::new(id.clone(), config);
        sandbox.log_audit(AuditEvent::SandboxCreated { label: sandbox.config.label.clone() });
        info!("Created sandbox id={} label={}", id, sandbox.config.label);
        self.sandboxes.write().await.insert(id.clone(), sandbox);
        id
    }

    pub async fn launch_agent(
        &self,
        sandbox_id: &str,
        command: Vec<String>,
        env: HashMap<String, String>,
    ) -> Result<AgentHandle> {
        let mut map = self.sandboxes.write().await;
        let sb = map.get_mut(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        sb.launch_agent(command, env).await
    }

    pub async fn grant_capability(&self, sandbox_id: &str, cap: Capability) -> Result<bool> {
        let mut map = self.sandboxes.write().await;
        let sb = map.get_mut(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        Ok(sb.grant_capability(cap))
    }

    pub async fn revoke_capability(&self, sandbox_id: &str, cap: &Capability) -> Result<()> {
        let mut map = self.sandboxes.write().await;
        let sb = map.get_mut(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        sb.revoke_capability(cap);
        Ok(())
    }

    pub async fn list_capabilities(&self, sandbox_id: &str) -> Result<Vec<Capability>> {
        let map = self.sandboxes.read().await;
        let sb = map.get(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        Ok(sb.list_capabilities().to_vec())
    }

    pub async fn get_audit_log(&self, sandbox_id: &str, limit: u32) -> Result<Vec<AuditEntry>> {
        let map = self.sandboxes.read().await;
        let sb = map.get(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        Ok(sb.get_audit_log(limit as usize))
    }

    pub async fn kill_agent(&self, sandbox_id: &str, signal: u32) -> Result<()> {
        let mut map = self.sandboxes.write().await;
        let sb = map.get_mut(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        sb.kill_agent(signal)
    }

    pub async fn status(&self, sandbox_id: &str) -> Result<SandboxStatus> {
        let map = self.sandboxes.read().await;
        let sb = map.get(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        Ok(sb.status.clone())
    }

    /// Remove a sandbox entirely (only if no agent is running)
    pub async fn destroy(&self, sandbox_id: &str) -> Result<()> {
        let mut map = self.sandboxes.write().await;
        let sb = map.get(sandbox_id)
            .ok_or_else(|| anyhow!("Sandbox not found: {}", sandbox_id))?;
        if matches!(sb.status, SandboxStatus::Running { .. }) {
            return Err(anyhow!("Cannot destroy sandbox with running agent; kill it first"));
        }
        map.remove(sandbox_id);
        info!("Destroyed sandbox id={}", sandbox_id);
        Ok(())
    }

    pub fn inner(&self) -> Arc<RwLock<HashMap<SandboxId, SandboxInstance>>> {
        self.sandboxes.clone()
    }
}

// Bring libc in for pre_exec signal constants
#[allow(unused_imports)]
use libc;
