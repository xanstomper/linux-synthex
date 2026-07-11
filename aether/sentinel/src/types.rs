//! Core security domain types for AETHER SENTINEL.
//!
//! These types are the lingua franca between every Sentinel subsystem: the
//! telemetry collectors emit [`TelemetrySample`]s, the detection engine turns
//! them into [`Finding`]s, the scoring engine derives a [`ThreatScore`], and
//! the agent monitor and defense controller consume scores to make policy
//! decisions. All scores are normalised to `0.0..=1.0` so they can be fused
//! linearly (see [`crate::scoring`]).

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;
use std::collections::BTreeSet;
use uuid::Uuid;

/// Clamp a raw score into the canonical `0.0..=1.0` range.
pub fn clamp01(x: f64) -> f64 {
    if x < 0.0 {
        0.0
    } else if x > 1.0 {
        1.0
    } else {
        x
    }
}

/// Qualitative severity band of a finding.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Severity {
    Info,
    Low,
    Medium,
    High,
    Critical,
}

impl Severity {
    /// Numeric weight (also the midpoint of the band) for fusion math.
    pub fn weight(&self) -> f64 {
        match self {
            Severity::Info => 0.1,
            Severity::Low => 0.3,
            Severity::Medium => 0.5,
            Severity::High => 0.75,
            Severity::Critical => 0.95,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Severity::Info => "info",
            Severity::Low => "low",
            Severity::Medium => "medium",
            Severity::High => "high",
            Severity::Critical => "critical",
        }
    }
}

impl fmt::Display for Severity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// Operational priority derived from a [`ThreatScore`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum Priority {
    /// No action required.
    P5,
    P4,
    P3,
    P2,
    /// Immediate response.
    P1,
}

impl Priority {
    pub fn from_risk(risk: f64) -> Self {
        match clamp01(risk) {
            r if r >= 0.85 => Priority::P1,
            r if r >= 0.65 => Priority::P2,
            r if r >= 0.45 => Priority::P3,
            r if r >= 0.25 => Priority::P4,
            _ => Priority::P5,
        }
    }

    pub fn as_str(&self) -> &'static str {
        match self {
            Priority::P5 => "P5",
            Priority::P4 => "P4",
            Priority::P3 => "P3",
            Priority::P2 => "P2",
            Priority::P1 => "P1",
        }
    }
}

impl fmt::Display for Priority {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

/// The kind of telemetry a sample originated from.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TelemetrySource {
    Filesystem,
    Process,
    Network,
    Agent,
    Memory,
    SystemCall,
    Auth,
    Container,
    Package,
}

impl TelemetrySource {
    pub fn as_str(&self) -> &'static str {
        match self {
            TelemetrySource::Filesystem => "filesystem",
            TelemetrySource::Process => "process",
            TelemetrySource::Network => "network",
            TelemetrySource::Agent => "agent",
            TelemetrySource::Memory => "memory",
            TelemetrySource::SystemCall => "syscall",
            TelemetrySource::Auth => "auth",
            TelemetrySource::Container => "container",
            TelemetrySource::Package => "package",
        }
    }
}

/// A single observation from a telemetry source.
///
/// The `payload` is a free-form JSON object produced by the collector; the
/// detection engine treats it as the corpus for signature and behavioral
/// matching, while the source and the agent (if any) carry the routing
/// context.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetrySample {
    pub id: String,
    pub at: DateTime<Utc>,
    pub source: TelemetrySource,
    /// Originating agent id, when the sample comes from agent activity.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    /// Free-form observation content (JSON). Also searchable as text.
    pub payload: serde_json::Value,
}

impl TelemetrySample {
    pub fn new(source: TelemetrySource, payload: serde_json::Value) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            at: Utc::now(),
            source,
            agent_id: None,
            payload,
        }
    }

    pub fn for_agent(source: TelemetrySource, agent_id: impl Into<String>, payload: serde_json::Value) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            at: Utc::now(),
            source,
            agent_id: Some(agent_id.into()),
            payload,
        }
    }

    /// Flatten the payload into a single lowercased string for signature
    /// matching. Stable enough for stub matching without a full JSON walker.
    pub fn text(&self) -> String {
        match &self.payload {
            serde_json::Value::String(s) => s.clone(),
            other => other.to_string(),
        }
        .to_lowercase()
    }
}


/// Which detection lane produced a [`Finding`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum DetectionLane {
    Signature,
    Behavioral,
    AiAnomaly,
}

impl DetectionLane {
    pub fn as_str(&self) -> &'static str {
        match self {
            DetectionLane::Signature => "signature",
            DetectionLane::Behavioral => "behavioral",
            DetectionLane::AiAnomaly => "ai_anomaly",
        }
    }
}

/// A single detection produced by one of the three lanes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Finding {
    pub id: String,
    pub at: DateTime<Utc>,
    pub lane: DetectionLane,
    /// Human-readable rule / heuristic name.
    pub rule: String,
    /// Why the detector fired (evidence string).
    pub detail: String,
    /// 0..=1 confidence in the positive.
    pub confidence: f64,
    /// 0..=1 estimated impact of the underlying activity.
    pub impact: f64,
    /// Originating telemetry sample id.
    pub sample_id: String,
    pub source: TelemetrySource,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
}

impl Finding {
    pub fn new(
        lane: DetectionLane,
        rule: impl Into<String>,
        detail: impl Into<String>,
        confidence: f64,
        impact: f64,
        sample: &TelemetrySample,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            at: Utc::now(),
            lane,
            rule: rule.into(),
            detail: detail.into(),
            confidence: clamp01(confidence),
            impact: clamp01(impact),
            sample_id: sample.id.clone(),
            source: sample.source,
            agent_id: sample.agent_id.clone(),
        }
    }
}

/// The composite, fused score for an event or incident.
///
/// `risk = clamp(w_sig*sig + w_beh*beh + w_ai*ai + w_agent*agent_risk - w_trust*trust)`
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct ThreatScore {
    /// 0..=1 per-lane signature contribution.
    pub signature: f64,
    /// 0..=1 per-lane behavioral contribution.
    pub behavioral: f64,
    /// 0..=1 per-lane AI-anomaly contribution.
    pub ai_anomaly: f64,
    /// 0..=1 risk attributed to the originating agent's standing.
    pub agent_risk: f64,
    /// 0..=1 trust of the originating agent (reduces risk).
    pub trust: f64,
    /// Fused composite in `0..=1`.
    pub risk: f64,
    /// Derived operational priority.
    pub priority: Priority,
}

impl ThreatScore {
    /// Fuse independent lane scores + agent standing into a composite risk.
    ///
    /// Weights are the Sentinel defaults; see [`crate::scoring::ThreatScorer`]
    /// if you need to tune them at runtime.
    pub fn fuse(signature: f64, behavioral: f64, ai_anomaly: f64, agent_risk: f64, trust: f64) -> Self {
        let w_sig = 0.30f64;
        let w_beh = 0.30f64;
        let w_ai = 0.20f64;
        let w_agent = 0.15f64;
        let w_trust = 0.15f64;
        let risk = clamp01(
            w_sig * clamp01(signature)
                + w_beh * clamp01(behavioral)
                + w_ai * clamp01(ai_anomaly)
                + w_agent * clamp01(agent_risk)
                - w_trust * clamp01(trust),
        );
        let priority = Priority::from_risk(risk);
        Self {
            signature: clamp01(signature),
            behavioral: clamp01(behavioral),
            ai_anomaly: clamp01(ai_anomaly),
            agent_risk: clamp01(agent_risk),
            trust: clamp01(trust),
            risk,
            priority,
        }
    }
}

/// A correlated, scored threat: one or more findings fused with agent
/// standing into a single narrative the operator and Copilot can act on.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Threat {
    pub id: String,
    pub at: DateTime<Utc>,
    pub title: String,
    pub score: ThreatScore,
    pub findings: Vec<Finding>,
    /// Free-form narrative constructed by [`crate::scoring::correlate`].
    pub narrative: String,
    /// Affected agent ids (deduped).
    pub agents: Vec<String>,
    /// Machine tags (e.g. "privesc", "cred-theft") for triage.
    pub tags: Vec<String>,
}

impl Threat {
    pub fn new(title: impl Into<String>, findings: Vec<Finding>, score: ThreatScore, narrative: impl Into<String>) -> Self {
        let agents: Vec<String> = findings
            .iter()
            .filter_map(|f| f.agent_id.clone())
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        Self {
            id: Uuid::new_v4().to_string(),
            at: Utc::now(),
            title: title.into(),
            score,
            findings,
            narrative: narrative.into(),
            agents,
            tags: Vec::new(),
        }
    }
}

