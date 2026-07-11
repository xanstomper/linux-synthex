use crate::capabilities::{Capability, NetworkScope, PathPattern};
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;
use tracing::{debug, warn};

/// A raw TOML-parsed policy file
#[derive(Debug, Deserialize)]
struct RawPolicy {
    #[serde(rename = "default_policy")]
    default: Option<RawPolicyBlock>,
    #[serde(rename = "agent")]
    agents: Option<toml::Table>,
}

#[derive(Debug, Deserialize)]
struct RawPolicyBlock {
    auto_grant: Option<Vec<String>>,
    require_approval: Option<Vec<String>>,
    always_deny: Option<Vec<String>>,
    max_memory_mb: Option<u64>,
    max_cpu_percent: Option<u8>,
    network_default: Option<String>,
    workspace_control: Option<Vec<u32>>,
    #[serde(rename = "network")]
    network_override: Option<toml::Value>,
}

/// Parsed, resolved policy for a single agent
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ResolvedPolicy {
    /// Capabilities automatically granted to the sandbox at creation
    pub auto_grant: Vec<Capability>,
    /// Capability kinds that must receive one-time user approval
    pub require_approval: Vec<String>,
    /// Capabilities that are always denied, regardless of user action
    pub always_deny: Vec<String>,
    pub max_memory_mb: u64,
    pub max_cpu_percent: u8,
    pub network_scope: NetworkScope,
    pub workspace_control: Vec<u32>,
}

impl Default for NetworkScope {
    fn default() -> Self {
        NetworkScope::LocalOnly
    }
}

/// Load and resolve a policy from a TOML file, optionally scoped to an agent label.
pub fn load_policy(policy_path: &Path, agent_label: Option<&str>) -> Result<ResolvedPolicy> {
    let text = std::fs::read_to_string(policy_path)
        .with_context(|| format!("Reading policy file: {}", policy_path.display()))?;

    let raw: RawPolicy = toml::from_str(&text)
        .with_context(|| format!("Parsing policy TOML: {}", policy_path.display()))?;

    // Start from defaults
    let mut resolved = ResolvedPolicy {
        max_memory_mb: 4096,
        max_cpu_percent: 80,
        network_scope: NetworkScope::LocalOnly,
        ..Default::default()
    };

    // Apply default_policy block
    if let Some(block) = &raw.default {
        apply_block(&mut resolved, block)?;
    }

    // Apply per-agent override if present
    if let Some(label) = agent_label {
        if let Some(agents_table) = &raw.agents {
            if let Some(agent_val) = agents_table.get(label) {
                debug!("Applying agent-specific policy for '{}'", label);
                let agent_block: RawPolicyBlock = agent_val.clone().try_into()
                    .with_context(|| format!("Parsing agent policy block for '{}'", label))?;
                apply_block(&mut resolved, &agent_block)?;
            } else {
                debug!("No agent-specific policy found for '{}', using defaults", label);
            }
        }
    }

    Ok(resolved)
}

fn apply_block(resolved: &mut ResolvedPolicy, block: &RawPolicyBlock) -> Result<()> {
    if let Some(grants) = &block.auto_grant {
        for cap_str in grants {
            match parse_capability_string(cap_str) {
                Ok(cap) => resolved.auto_grant.push(cap),
                Err(e) => warn!("Ignoring unknown auto_grant capability '{}': {}", cap_str, e),
            }
        }
    }

    if let Some(approvals) = &block.require_approval {
        resolved.require_approval = approvals.clone();
    }

    if let Some(denies) = &block.always_deny {
        resolved.always_deny = denies.clone();
    }

    if let Some(mem) = block.max_memory_mb {
        resolved.max_memory_mb = mem;
    }

    if let Some(cpu) = block.max_cpu_percent {
        resolved.max_cpu_percent = cpu;
    }

    if let Some(ref net_str) = block.network_default {
        resolved.network_scope = parse_network_scope(net_str, None)?;
    }

    // Inline [network] table overrides network_default
    if let Some(net_val) = &block.network_override {
        if let Some(net_table) = net_val.as_table() {
            let kind = net_table.get("type")
                .and_then(|v| v.as_str())
                .unwrap_or("LocalOnly");
            let domains: Vec<String> = net_table.get("allowed_domains")
                .and_then(|v| v.as_array())
                .map(|arr| arr.iter().filter_map(|x| x.as_str().map(str::to_string)).collect())
                .unwrap_or_default();
            resolved.network_scope = parse_network_scope(kind, Some(domains))?;
        }
    }

    if let Some(ws) = &block.workspace_control {
        resolved.workspace_control = ws.clone();
    }

    Ok(())
}

/// Parse a human-readable capability string like:
///   "SystemInfo"
///   "ReadFile(/home/**)"
///   "ExecuteCommand(cargo,npm,git)"
///   "NetworkAccess(LocalOnly)"
///   "WorkspaceControl(2,3,4)"
pub fn parse_capability_string(s: &str) -> Result<Capability> {
    // Strip outer quotes if present
    let s = s.trim().trim_matches('"');

    // Split on first '('
    if let Some(paren_pos) = s.find('(') {
        let kind = &s[..paren_pos];
        let inner = s[paren_pos + 1..].trim_end_matches(')');

        match kind {
            "ReadFile" => Ok(Capability::ReadFile(PathPattern::new(inner))),
            "WriteFile" => Ok(Capability::WriteFile(PathPattern::new(inner))),
            "ExecuteCommand" => {
                let cmds = inner.split(',').map(|c| c.trim().to_string()).collect();
                Ok(Capability::ExecuteCommand(cmds))
            }
            "NetworkAccess" => {
                let scope = parse_network_scope(inner, None)?;
                Ok(Capability::NetworkAccess(scope))
            }
            "WorkspaceControl" => {
                let nums: Vec<u32> = inner.split(',')
                    .filter_map(|n| n.trim().parse().ok())
                    .collect();
                Ok(Capability::WorkspaceControl(nums))
            }
            "SpawnProcess" => {
                let exes = inner.split(',').map(|e| e.trim().to_string()).collect();
                Ok(Capability::SpawnProcess(exes))
            }
            "DBusCall" => {
                let mut parts = inner.splitn(2, ',');
                let service = parts.next().unwrap_or("").trim().to_string();
                let method = parts.next().unwrap_or("*").trim().to_string();
                Ok(Capability::DBusCall { service, method_pattern: method })
            }
            "KeychainRead" => {
                let keys = inner.split(',').map(|k| k.trim().to_string()).collect();
                Ok(Capability::KeychainRead(keys))
            }
            _ => anyhow::bail!("Unknown capability kind with args: {}", kind),
        }
    } else {
        // No parentheses — bare capability name
        match s {
            "ScreenRead"         => Ok(Capability::ScreenRead),
            "ScreenWrite"        => Ok(Capability::ScreenWrite),
            "ClipboardRead"      => Ok(Capability::ClipboardRead),
            "ClipboardWrite"     => Ok(Capability::ClipboardWrite),
            "SystemInfo"         => Ok(Capability::SystemInfo),
            "NotificationSend"   => Ok(Capability::NotificationSend),
            "AudioPlay"          => Ok(Capability::AudioPlay),
            _ => anyhow::bail!("Unknown bare capability: {}", s),
        }
    }
}

fn parse_network_scope(s: &str, domains_override: Option<Vec<String>>) -> Result<NetworkScope> {
    match s.trim() {
        "None" | "none" => Ok(NetworkScope::None),
        "LocalOnly" | "local_only" | "local" => Ok(NetworkScope::LocalOnly),
        "Internet" | "internet" => Ok(NetworkScope::Internet {
            allowed_domains: domains_override.unwrap_or_default(),
        }),
        other => anyhow::bail!("Unknown network scope: {}", other),
    }
}

/// Check whether a capability string is in the always-deny list.
/// Supports prefix matching (e.g. "SpawnProcess(/bin/sh)" matches "SpawnProcess").
pub fn is_always_denied(cap: &Capability, always_deny: &[String]) -> bool {
    let audit_str = cap.to_audit_string();
    let kind = cap.kind_name();

    always_deny.iter().any(|deny| {
        deny == &audit_str
            || deny == kind
            || audit_str.starts_with(deny.as_str())
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_bare_capabilities() {
        assert!(matches!(parse_capability_string("SystemInfo").unwrap(), Capability::SystemInfo));
        assert!(matches!(parse_capability_string("ScreenRead").unwrap(), Capability::ScreenRead));
        assert!(matches!(parse_capability_string("ClipboardRead").unwrap(), Capability::ClipboardRead));
    }

    #[test]
    fn test_parse_parametric_capabilities() {
        let cap = parse_capability_string("ReadFile(/home/**)").unwrap();
        assert!(matches!(cap, Capability::ReadFile(_)));

        let cap = parse_capability_string("ExecuteCommand(cargo,npm,git)").unwrap();
        if let Capability::ExecuteCommand(cmds) = cap {
            assert_eq!(cmds, vec!["cargo", "npm", "git"]);
        } else {
            panic!("wrong variant");
        }

        let cap = parse_capability_string("WorkspaceControl(2,3,4)").unwrap();
        if let Capability::WorkspaceControl(ws) = cap {
            assert_eq!(ws, vec![2, 3, 4]);
        } else {
            panic!("wrong variant");
        }
    }

    #[test]
    fn test_always_deny_matching() {
        let cap = Capability::SpawnProcess(vec!["/bin/sh".into()]);
        let denies = vec!["SpawnProcess(/bin/sh)".to_string()];
        assert!(is_always_denied(&cap, &denies));
    }
}
