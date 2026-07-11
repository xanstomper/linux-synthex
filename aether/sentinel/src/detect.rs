//! Signature + behavioral detection lanes.
//!
//! The MVP detector matches a fixed set of signature rules against the
//! lowercased telemetry text and tracks per-agent sample volume to surface
//! behavioural bursts. In production these lanes are fed by the AETHER event
//! bus and by host telemetry collectors.

use crate::types::*;
use std::collections::HashMap;

/// A single signature rule over lowercased telemetry text.
#[derive(Debug, Clone, Copy)]
struct Rule {
    name: &'static str,
    pattern: &'static str,
    confidence: f64,
    impact: f64,
}

const RULES: &[Rule] = &[
    Rule { name: "pipe-to-shell",     pattern: "| sh",      confidence: 0.7, impact: 0.6 },
    Rule { name: "pipe-to-shell-bash", pattern: "| bash",   confidence: 0.7, impact: 0.6 },
    Rule { name: "base64-decode",     pattern: "base64 -d", confidence: 0.5, impact: 0.4 },
    Rule { name: "shadow-read",       pattern: "/etc/shadow", confidence: 0.8, impact: 0.7 },
    Rule { name: "chmod-world-write", pattern: "chmod 777", confidence: 0.5, impact: 0.5 },
    Rule { name: "reverse-shell-nc",  pattern: "nc -e",     confidence: 0.8, impact: 0.8 },
    Rule { name: "ssh-key-read",      pattern: "id_rsa",    confidence: 0.6, impact: 0.7 },
];

/// Stateful detector: holds the rule set + per-agent burst counters.
pub struct Detector {
    rules: Vec<Rule>,
    per_agent: HashMap<String, usize>,
    burst_threshold: usize,
}

impl Default for Detector {
    fn default() -> Self {
        Self::new()
    }
}

impl Detector {
    pub fn new() -> Self {
        Self {
            rules: RULES.to_vec(),
            per_agent: HashMap::new(),
            burst_threshold: 25,
        }
    }

    /// Scan one telemetry sample, returning any findings it produces.
    pub fn scan(&mut self, sample: &TelemetrySample) -> Vec<Finding> {
        let mut out = Vec::new();
        let text = sample.text();

        for r in &self.rules {
            if text.contains(r.pattern) {
                out.push(Finding::new(
                    DetectionLane::Signature,
                    r.name,
                    format!("telemetry matched signature '{}'", r.pattern),
                    r.confidence,
                    r.impact,
                    sample,
                ));
            }
        }

        // Behavioral lane: burst detection per actor.
        let actor = sample.agent_id.clone().unwrap_or_else(|| "system".to_string());
        let n = self
            .per_agent
            .entry(actor.clone())
            .and_modify(|c| *c += 1)
            .or_insert(1);
        if *n == self.burst_threshold {
            out.push(Finding::new(
                DetectionLane::Behavioral,
                "agent-burst",
                format!("agent '{actor}' emitted {n} samples in a short window"),
                0.5,
                0.4,
                sample,
            ));
        }

        out
    }
}
