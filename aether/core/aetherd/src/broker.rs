//! Capability broker — the security kernel of AETHER CORE.
//!
//! Agents cannot touch the system directly. Every privileged operation must go
//! through the broker, which validates the request against the agent's granted
//! capabilities, enforces rate limits, records an immutable audit entry, and —
//! for sensitive tokens — routes the request into an approval workflow.

use std::collections::{HashMap, HashSet};

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// The set of privileged capabilities an agent can be granted.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CapabilityToken {
    ReadFile,
    WriteFile,
    SearchCode,
    ExecuteCommand,
    AccessDatabase,
    UseBrowser,
    UseGit,
    UseDocker,
    UseKubernetes,
    NetworkAccess,
    SystemControl,
}

impl CapabilityToken {
    pub fn as_str(&self) -> &'static str {
        match self {
            CapabilityToken::ReadFile => "ReadFile",
            CapabilityToken::WriteFile => "WriteFile",
            CapabilityToken::SearchCode => "SearchCode",
            CapabilityToken::ExecuteCommand => "ExecuteCommand",
            CapabilityToken::AccessDatabase => "AccessDatabase",
            CapabilityToken::UseBrowser => "UseBrowser",
            CapabilityToken::UseGit => "UseGit",
            CapabilityToken::UseDocker => "UseDocker",
            CapabilityToken::UseKubernetes => "UseKubernetes",
            CapabilityToken::NetworkAccess => "NetworkAccess",
            CapabilityToken::SystemControl => "SystemControl",
        }
    }

    /// Tokens considered dangerous enough to require explicit approval.
    pub fn is_sensitive(&self) -> bool {
        matches!(
            self,
            CapabilityToken::ExecuteCommand
                | CapabilityToken::SystemControl
                | CapabilityToken::UseKubernetes
        )
    }
}

/// A request from an agent to exercise a capability.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityRequest {
    pub agent_id: String,
    pub token: CapabilityToken,
    pub resource: String,
    pub reason: String,
}

/// The broker's decision on a request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Decision {
    Granted,
    Denied(String),
    PendingApproval,
}

/// An immutable audit record.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditEntry {
    pub at: DateTime<Utc>,
    pub agent_id: String,
    pub token: CapabilityToken,
    pub resource: String,
    pub decision: Decision,
}

/// Sliding-window rate limit bookkeeping.
#[derive(Debug, Clone)]
struct RateState {
    window_start: DateTime<Utc>,
    count: u32,
}

/// The capability broker.
pub struct Broker {
    /// Capabilities granted per agent.
    grants: HashMap<String, HashSet<CapabilityToken>>,
    /// Append-only audit log.
    audit: Vec<AuditEntry>,
    /// Per (agent, token) rate state.
    rates: HashMap<(String, CapabilityToken), RateState>,
    /// Pending approval queue (request id -> request).
    pending: HashMap<String, CapabilityRequest>,
    /// Max requests per token per window.
    rate_limit: u32,
    /// Window length in seconds.
    window_secs: i64,
    /// If true, sensitive tokens require approval; else auto-grant.
    require_approval: bool,
}

impl Broker {
    pub fn new(rate_limit: u32, window_secs: i64, require_approval: bool) -> Self {
        Self {
            grants: HashMap::new(),
            audit: Vec::new(),
            rates: HashMap::new(),
            pending: HashMap::new(),
            rate_limit: rate_limit.max(1),
            window_secs: window_secs.max(1),
            require_approval,
        }
    }

    /// Grant a capability to an agent.
    pub fn grant(&mut self, agent_id: &str, token: CapabilityToken) {
        self.grants
            .entry(agent_id.to_string())
            .or_default()
            .insert(token);
    }

    /// Revoke a capability from an agent.
    pub fn revoke(&mut self, agent_id: &str, token: CapabilityToken) {
        if let Some(set) = self.grants.get_mut(agent_id) {
            set.remove(&token);
        }
    }

    pub fn audit_log(&self) -> &[AuditEntry] {
        &self.audit
    }

    pub fn pending_count(&self) -> usize {
        self.pending.len()
    }

    fn record(&mut self, req: &CapabilityRequest, decision: Decision) -> Decision {
        self.audit.push(AuditEntry {
            at: Utc::now(),
            agent_id: req.agent_id.clone(),
            token: req.token,
            resource: req.resource.clone(),
            decision: decision.clone(),
        });
        decision
    }

    /// Validate a capability request. Records an audit entry for every outcome.
    pub fn validate(&mut self, req: &CapabilityRequest) -> Decision {
        // 1. Must be granted.
        let granted = self
            .grants
            .get(&req.agent_id)
            .map(|s| s.contains(&req.token))
            .unwrap_or(false);
        if !granted {
            return self.record(
                req,
                Decision::Denied(format!(
                    "agent '{}' lacks capability {}",
                    req.agent_id,
                    req.token.as_str()
                )),
            );
        }

        // 2. Rate limit (sliding window).
        let now = Utc::now();
        let key = (req.agent_id.clone(), req.token);
        let over = {
            let st = self.rates.entry(key).or_insert(RateState {
                window_start: now,
                count: 0,
            });
            if (now - st.window_start).num_seconds() >= self.window_secs {
                st.window_start = now;
                st.count = 0;
            }
            st.count += 1;
            st.count > self.rate_limit
        };
        if over {
            return self.record(
                req,
                Decision::Denied(format!(
                    "rate limit exceeded for {} ({}/{}s)",
                    req.token.as_str(),
                    self.rate_limit,
                    self.window_secs
                )),
            );
        }

        // 3. Approval workflow for sensitive tokens.
        if self.require_approval && req.token.is_sensitive() {
            let rid = uuid::Uuid::new_v4().to_string();
            self.pending.insert(rid, req.clone());
            return self.record(req, Decision::PendingApproval);
        }

        self.record(req, Decision::Granted)
    }

    /// Approve a pending request by its queue id. Returns the request if found.
    pub fn approve(&mut self, request_id: &str) -> Option<CapabilityRequest> {
        let req = self.pending.remove(request_id)?;
        self.record(&req, Decision::Granted);
        Some(req)
    }

    /// Deny a pending request.
    pub fn deny(&mut self, request_id: &str, reason: &str) -> Option<CapabilityRequest> {
        let req = self.pending.remove(request_id)?;
        self.record(&req, Decision::Denied(reason.to_string()));
        Some(req)
    }
}

