use serde::{Deserialize, Serialize};
use std::fmt;

/// Pattern for matching file paths (glob-style)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct PathPattern(pub String);

impl PathPattern {
    pub fn new(pattern: impl Into<String>) -> Self {
        Self(pattern.into())
    }

    /// Returns true if the given path matches this glob pattern
    pub fn matches(&self, path: &str) -> bool {
        glob::Pattern::new(&self.0)
            .map(|p| p.matches(path))
            .unwrap_or(false)
    }
}

impl fmt::Display for PathPattern {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Network access scope for an agent
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum NetworkScope {
    /// No network access whatsoever
    None,
    /// Loopback + LAN only (127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    LocalOnly,
    /// Full internet with domain allowlist
    Internet { allowed_domains: Vec<String> },
}

impl fmt::Display for NetworkScope {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            NetworkScope::None => write!(f, "None"),
            NetworkScope::LocalOnly => write!(f, "LocalOnly"),
            NetworkScope::Internet { allowed_domains } => {
                write!(f, "Internet({})", allowed_domains.join(","))
            }
        }
    }
}

/// Fine-grained capability granted to an agent sandbox
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Capability {
    /// Read files matching a glob pattern, e.g. "/home/user/projects/**"
    ReadFile(PathPattern),

    /// Write files matching a glob pattern
    WriteFile(PathPattern),

    /// Execute from a whitelist of allowed commands (base name or full path)
    ExecuteCommand(Vec<String>),

    /// Network access with specified scope
    NetworkAccess(NetworkScope),

    /// Read screen content / take screenshots
    ScreenRead,

    /// Control mouse and keyboard
    ScreenWrite,

    /// Read from the clipboard
    ClipboardRead,

    /// Write to the clipboard
    ClipboardWrite,

    /// Control specific workspace numbers on the window manager
    WorkspaceControl(Vec<u32>),

    /// Call a specific D-Bus service/method pattern
    DBusCall {
        service: String,
        method_pattern: String,
    },

    /// Spawn processes from an executable allowlist
    SpawnProcess(Vec<String>),

    /// Read /proc and /sys (system information)
    SystemInfo,

    /// Send desktop notifications (libnotify)
    NotificationSend,

    /// Play audio output
    AudioPlay,

    /// Read specific keychain entries by name
    KeychainRead(Vec<String>),
}

impl Capability {
    /// Human-readable name of this capability variant
    pub fn kind_name(&self) -> &'static str {
        match self {
            Capability::ReadFile(_) => "ReadFile",
            Capability::WriteFile(_) => "WriteFile",
            Capability::ExecuteCommand(_) => "ExecuteCommand",
            Capability::NetworkAccess(_) => "NetworkAccess",
            Capability::ScreenRead => "ScreenRead",
            Capability::ScreenWrite => "ScreenWrite",
            Capability::ClipboardRead => "ClipboardRead",
            Capability::ClipboardWrite => "ClipboardWrite",
            Capability::WorkspaceControl(_) => "WorkspaceControl",
            Capability::DBusCall { .. } => "DBusCall",
            Capability::SpawnProcess(_) => "SpawnProcess",
            Capability::SystemInfo => "SystemInfo",
            Capability::NotificationSend => "NotificationSend",
            Capability::AudioPlay => "AudioPlay",
            Capability::KeychainRead(_) => "KeychainRead",
        }
    }

    /// Returns true if this capability grants access to the given file path for reading
    pub fn allows_read_file(&self, path: &str) -> bool {
        if let Capability::ReadFile(pattern) = self {
            return pattern.matches(path);
        }
        false
    }

    /// Returns true if this capability grants access to the given file path for writing
    pub fn allows_write_file(&self, path: &str) -> bool {
        if let Capability::WriteFile(pattern) = self {
            return pattern.matches(path);
        }
        false
    }

    /// Returns true if this capability allows executing the given command
    pub fn allows_execute(&self, command: &str) -> bool {
        if let Capability::ExecuteCommand(cmds) = self {
            return cmds.iter().any(|c| c == command || {
                // match on basename too
                std::path::Path::new(command)
                    .file_name()
                    .and_then(|n| n.to_str())
                    .map(|n| n == c.as_str())
                    .unwrap_or(false)
            });
        }
        false
    }

    /// Returns true if this capability allows spawning the given executable
    #[allow(dead_code)]
    pub fn allows_spawn(&self, exe: &str) -> bool {
        if let Capability::SpawnProcess(exes) = self {
            return exes.iter().any(|e| e == exe);
        }
        false
    }

    /// Returns true if this capability allows the given network domain
    pub fn allows_network_domain(&self, domain: &str) -> bool {
        if let Capability::NetworkAccess(scope) = self {
            return match scope {
                NetworkScope::None => false,
                NetworkScope::LocalOnly => false, // domains aren't local
                NetworkScope::Internet { allowed_domains } => {
                    allowed_domains.iter().any(|d| {
                        d == domain || domain.ends_with(&format!(".{}", d))
                    })
                }
            };
        }
        false
    }

    /// Serialize capability to a concise display string for audit logs
    pub fn to_audit_string(&self) -> String {
        match self {
            Capability::ReadFile(p) => format!("ReadFile({})", p),
            Capability::WriteFile(p) => format!("WriteFile({})", p),
            Capability::ExecuteCommand(cmds) => format!("ExecuteCommand({})", cmds.join(",")),
            Capability::NetworkAccess(s) => format!("NetworkAccess({})", s),
            Capability::ScreenRead => "ScreenRead".into(),
            Capability::ScreenWrite => "ScreenWrite".into(),
            Capability::ClipboardRead => "ClipboardRead".into(),
            Capability::ClipboardWrite => "ClipboardWrite".into(),
            Capability::WorkspaceControl(ws) => {
                format!("WorkspaceControl({})", ws.iter().map(|n| n.to_string()).collect::<Vec<_>>().join(","))
            }
            Capability::DBusCall { service, method_pattern } => {
                format!("DBusCall({},{})", service, method_pattern)
            }
            Capability::SpawnProcess(exes) => format!("SpawnProcess({})", exes.join(",")),
            Capability::SystemInfo => "SystemInfo".into(),
            Capability::NotificationSend => "NotificationSend".into(),
            Capability::AudioPlay => "AudioPlay".into(),
            Capability::KeychainRead(keys) => format!("KeychainRead({})", keys.join(",")),
        }
    }
}

impl fmt::Display for Capability {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_audit_string())
    }
}
