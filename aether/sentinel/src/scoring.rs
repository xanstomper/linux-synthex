//! Threat correlation + multi-lane scoring.
//!
//! [`correlate`] groups findings by actor, fuses per-lane scores with
//! [`ThreatScore::fuse`], and emits one [`Threat`] per actor.

use crate::types::*;
use std::collections::BTreeMap;

/// Correlate a flat list of findings into per-actor [`Threat`]s.
///
/// Findings without an `agent_id` are attributed to the synthetic `"system"`
/// actor so host-originated telemetry is still scored.
pub fn correlate(findings: &[Finding]) -> Vec<Threat> {
    if findings.is_empty() {
        return Vec::new();
    }

    let mut by_actor: BTreeMap<String, Vec<&Finding>> = BTreeMap::new();
    for f in findings {
        let actor = f.agent_id.clone().unwrap_or_else(|| "system".to_string());
        by_actor.entry(actor).or_default().push(f);
    }

    let mut threats = Vec::new();
    for (actor, fs) in by_actor {
        let sig = fs
            .iter()
            .map(|f| if f.lane == DetectionLane::Signature { f.confidence } else { 0.0 })
            .fold(0.0_f64, f64::max);
        let beh = fs
            .iter()
            .map(|f| if f.lane == DetectionLane::Behavioral { f.confidence } else { 0.0 })
            .fold(0.0_f64, f64::max);
        let ai = fs
            .iter()
            .map(|f| if f.lane == DetectionLane::AiAnomaly { f.confidence } else { 0.0 })
            .fold(0.0_f64, f64::max);
        let impact = fs.iter().map(|f| f.impact).fold(0.0_f64, f64::max);
        // Agent standing risk scales with the worst impact and how many
        // findings this actor produced (saturating at 3).
        let agent_risk = clamp01(impact * ((fs.len() as f64).min(3.0) / 3.0));
        let score = ThreatScore::fuse(sig, beh, ai, agent_risk, 0.5);

        let narrative = format!(
            "Actor '{actor}' produced {} finding(s): sig={:.2} beh={:.2} ai={:.2} -> risk={:.2} ({})",
            fs.len(),
            sig,
            beh,
            ai,
            score.risk,
            score.priority
        );

        let collected: Vec<Finding> = fs.iter().map(|f| (*f).clone()).collect();
        threats.push(Threat::new(
            format!("Correlated threat from {actor}"),
            collected,
            score,
            narrative,
        ));
    }
    threats
}
