//! Reflection engine — after-action review.
//!
//! After a task, goal, or agent run finishes, the reflection engine analyses
//! what happened, extracts patterns, and produces recommendations. The output
//! is intended to be stored back as a [`crate::memory::MemoryKind::Reflection`]
//! memory so the daemon learns over time.
//!
//! The analysis here is a heuristic stub; the full design routes the transcript
//! through an LLM.

use serde::{Deserialize, Serialize};

/// The structured result of an after-action review.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReflectionReport {
    pub subject: String,
    pub success: bool,
    /// Concrete observations extracted from the run.
    pub findings: Vec<String>,
    /// Recurring patterns worth remembering.
    pub patterns: Vec<String>,
    /// Actionable improvements for next time.
    pub recommendations: Vec<String>,
}

impl ReflectionReport {
    /// Render the report as a single memory-friendly string.
    pub fn to_memory_content(&self) -> String {
        let mut s = format!(
            "AAR for '{}' ({}):\n",
            self.subject,
            if self.success { "SUCCESS" } else { "FAILURE" }
        );
        for f in &self.findings {
            s.push_str(&format!("  finding: {f}\n"));
        }
        for p in &self.patterns {
            s.push_str(&format!("  pattern: {p}\n"));
        }
        for r in &self.recommendations {
            s.push_str(&format!("  recommend: {r}\n"));
        }
        s
    }
}

#[derive(Default)]
pub struct ReflectionEngine;

impl ReflectionEngine {
    pub fn new() -> Self {
        Self
    }

    /// Perform an after-action review.
    ///
    /// `details` are free-form lines describing what happened (log excerpts,
    /// error messages, step outcomes). The heuristic scans them for signals.
    pub fn after_action_review(
        &self,
        subject: impl Into<String>,
        success: bool,
        details: &[String],
    ) -> ReflectionReport {
        let subject = subject.into();
        let mut findings = Vec::new();
        let mut patterns = Vec::new();
        let mut recommendations = Vec::new();

        let mut error_count = 0usize;
        let mut retry_count = 0usize;
        for line in details {
            let l = line.to_lowercase();
            if l.contains("error") || l.contains("fail") || l.contains("panic") {
                error_count += 1;
                findings.push(format!("error signal: {line}"));
            }
            if l.contains("retry") || l.contains("again") {
                retry_count += 1;
            }
            if l.contains("timeout") {
                patterns.push("operations are hitting timeouts".into());
                recommendations.push("increase timeout budget or parallelise".into());
            }
            if l.contains("permission") || l.contains("denied") {
                patterns.push("capability/permission gaps".into());
                recommendations
                    .push("request the required capability token up front".into());
            }
        }

        if success {
            findings.push("objective achieved".into());
            if error_count == 0 {
                patterns.push("clean run — approach is reliable".into());
                recommendations.push("promote this approach to procedural memory".into());
            }
        } else {
            findings.push("objective not achieved".into());
            recommendations.push("decompose the goal into smaller steps".into());
        }

        if retry_count >= 2 {
            patterns.push("repeated retries indicate a flaky dependency".into());
            recommendations.push("add a stability check before retrying".into());
        }
        if error_count >= 3 {
            patterns.push("high error density".into());
            recommendations.push("pause and escalate for human review".into());
        }

        patterns.sort();
        patterns.dedup();
        recommendations.sort();
        recommendations.dedup();

        ReflectionReport {
            subject,
            success,
            findings,
            patterns,
            recommendations,
        }
    }
}
