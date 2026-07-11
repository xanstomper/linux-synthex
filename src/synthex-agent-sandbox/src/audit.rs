use serde::{Deserialize, Serialize};

/// Individual events that can appear in an audit log
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum AuditEvent {
    SandboxCreated {
        label: String,
    },
    AgentLaunched {
        handle: String,
        command: Vec<String>,
        pid: u32,
    },
    AgentKilled {
        pid: u32,
        signal: u32,
    },
    AgentExited {
        pid: u32,
        exit_code: i32,
    },
    CapabilityGranted {
        capability: String,
    },
    CapabilityRevoked {
        capability: String,
    },
    CapabilityRequested {
        capability: String,
        granted: bool,
    },
    PolicyViolation {
        description: String,
    },
    FileAccess {
        path: String,
        mode: String, // "read" | "write"
        allowed: bool,
    },
    NetworkAccess {
        domain: String,
        allowed: bool,
    },
    CommandExecution {
        command: String,
        allowed: bool,
    },
    DBusCall {
        service: String,
        method: String,
        allowed: bool,
    },
    HijackAttempt {
        description: String,
        mitigation: String,
    },
    SandboxDestroyed,
}

/// A single entry in the audit log, with timestamp and sandbox context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    pub timestamp: String,
    pub sandbox_id: String,
    pub event: AuditEvent,
}

impl AuditEntry {
    /// Format as a human-readable log line
    pub fn to_log_line(&self) -> String {
        let event_str = match &self.event {
            AuditEvent::SandboxCreated { label } =>
                format!("SANDBOX_CREATED label={}", label),
            AuditEvent::AgentLaunched { handle, command, pid } =>
                format!("AGENT_LAUNCHED handle={} pid={} cmd={}", handle, pid, command.join(" ")),
            AuditEvent::AgentKilled { pid, signal } =>
                format!("AGENT_KILLED pid={} signal={}", pid, signal),
            AuditEvent::AgentExited { pid, exit_code } =>
                format!("AGENT_EXITED pid={} exit_code={}", pid, exit_code),
            AuditEvent::CapabilityGranted { capability } =>
                format!("CAP_GRANTED {}", capability),
            AuditEvent::CapabilityRevoked { capability } =>
                format!("CAP_REVOKED {}", capability),
            AuditEvent::CapabilityRequested { capability, granted } =>
                format!("CAP_REQUESTED {} granted={}", capability, granted),
            AuditEvent::PolicyViolation { description } =>
                format!("POLICY_VIOLATION {}", description),
            AuditEvent::FileAccess { path, mode, allowed } =>
                format!("FILE_ACCESS mode={} allowed={} path={}", mode, allowed, path),
            AuditEvent::NetworkAccess { domain, allowed } =>
                format!("NET_ACCESS allowed={} domain={}", allowed, domain),
            AuditEvent::CommandExecution { command, allowed } =>
                format!("CMD_EXEC allowed={} cmd={}", allowed, command),
            AuditEvent::DBusCall { service, method, allowed } =>
                format!("DBUS_CALL allowed={} {}.{}", allowed, service, method),
            AuditEvent::HijackAttempt { description, mitigation } =>
                format!("HIJACK_ATTEMPT desc={} mitigation={}", description, mitigation),
            AuditEvent::SandboxDestroyed =>
                "SANDBOX_DESTROYED".to_string(),
        };
        format!("[{}] [{}] {}", self.timestamp, self.sandbox_id, event_str)
    }
}
