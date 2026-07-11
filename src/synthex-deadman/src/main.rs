// SPDX-License-Identifier: GPL-3.0-or-later
//! synthex-deadman — Dead Man's Switch daemon for SynthOS.
//!
//! The companion `synthex-checkin` binary is run periodically (e.g. from a
//! systemd timer or your session) to prove the machine is still attended.
//! If no check-in arrives within `checkin_interval_secs + grace_secs`, the
//! switch is considered TRIPPED and the daemon:
//!   1. runs the configured `lockdown_command` (default: lock all sessions),
//!   2. sends webhook alerts to every configured `webhook_urls` endpoint.
//!
//! State lives in /run/synthex-deadman/last_checkin (epoch seconds).

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

const STATE_DIR: &str = "/run/synthex-deadman";
const STATE_FILE: &str = "/run/synthex-deadman/last_checkin";
const CONFIG_PATH: &str = "/etc/synthex/deadman.toml";

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Config {
    checkin_interval_secs: u64,
    grace_secs: u64,
    webhook_urls: Vec<String>,
    lockdown_command: String,
    arm_on_start: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            checkin_interval_secs: 300,
            grace_secs: 60,
            webhook_urls: vec![],
            lockdown_command: "loginctl lock-sessions".into(),
            arm_on_start: false,
        }
    }
}

impl Config {
    fn load() -> Config {
        match std::fs::read_to_string(CONFIG_PATH) {
            Ok(s) => toml::from_str(&s).unwrap_or_else(|e| {
                warn!("bad deadman config ({}), using defaults: {}", CONFIG_PATH, e);
                Config::default()
            }),
            Err(_) => Config::default(),
        }
    }
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

fn read_last_checkin() -> Option<u64> {
    std::fs::read_to_string(STATE_FILE)
        .ok()
        .and_then(|s| s.trim().parse().ok())
}

fn write_last_checkin(t: u64) -> Result<()> {
    std::fs::create_dir_all(STATE_DIR).ok();
    std::fs::write(STATE_FILE, t.to_string()).context("write last check-in")
}

fn hostname() -> String {
    std::fs::read_to_string("/etc/hostname")
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "unknown".into())
}

async fn send_alerts(cfg: &Config, msg: &str) {
    for url in &cfg.webhook_urls {
        let payload = serde_json::json!({
            "text": msg,
            "source": "synthex-deadman",
            "host": hostname(),
            "time": now_secs(),
        });
        match reqwest::Client::new().post(url).json(&payload).send().await {
            Ok(_) => info!("webhook alert sent to {}", url),
            Err(e) => warn!("webhook alert to {} failed: {}", url, e),
        }
    }
}

fn trigger_lockdown(cfg: &Config) {
    warn!("DEAD MAN'S SWITCH TRIPPED — initiating lockdown");
    match std::process::Command::new("sh")
        .arg("-c")
        .arg(&cfg.lockdown_command)
        .status()
    {
        Ok(s) if s.success() => info!("lockdown command succeeded"),
        Ok(s) => warn!("lockdown command exited with {}", s),
        Err(e) => warn!("failed to run lockdown command: {}", e),
    }
}

async fn run_daemon(cfg: Arc<Config>, armed: Arc<AtomicBool>) -> Result<()> {
    if cfg.arm_on_start {
        armed.store(true, Ordering::SeqCst);
        write_last_checkin(now_secs())?;
        info!("deadman armed; interval={}s grace={}s", cfg.checkin_interval_secs, cfg.grace_secs);
    } else {
        info!("deadman NOT armed (arm_on_start=false). Use 'synthex-deadman arm' to arm.");
    }

    loop {
        if armed.load(Ordering::SeqCst) {
            let limit = cfg.checkin_interval_secs + cfg.grace_secs;
            if let Some(last) = read_last_checkin() {
                if now_secs().saturating_sub(last) > limit {
                    trigger_lockdown(&cfg);
                    send_alerts(&cfg, "🔒 SynthOS Dead Man's Switch tripped — system locked down.").await;
                    // Disarm after a trip to avoid repeated alerts until re-armed.
                    armed.store(false, Ordering::SeqCst);
                    info!("lockdown complete; deadman disarmed. Re-arm with 'synthex-deadman arm'.");
                }
            }
        }
        tokio::time::sleep(Duration::from_secs(5)).await;
    }
}

fn cmd_arm() -> Result<()> {
    std::fs::create_dir_all(STATE_DIR).ok();
    write_last_checkin(now_secs())?;
    // touch a flag file the daemon reads
    std::fs::write("/run/synthex-deadman/armed", "").ok();
    println!("[deadman] armed; last check-in updated.");
    Ok(())
}

fn cmd_disarm() -> Result<()> {
    std::fs::remove_file("/run/synthex-deadman/armed").ok();
    println!("[deadman] disarmed.");
    Ok(())
}

fn cmd_status(cfg: &Config) -> Result<()> {
    let armed_flag = std::path::Path::new("/run/synthex-deadman/armed").exists();
    let last = read_last_checkin();
    println!("SynthOS Dead Man's Switch");
    println!("  Armed            : {}", armed_flag);
    println!("  Last check-in    : {}", last.map(|t| t.to_string()).unwrap_or_else(|| "never".into()));
    println!("  Interval + grace : {}s", cfg.checkin_interval_secs + cfg.grace_secs);
    println!("  Webhooks         : {}", cfg.webhook_urls.len());
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env().add_directive("synthex_deadman=info".parse().unwrap()),
        )
        .init();
    let cfg = Arc::new(Config::load());
    let armed = Arc::new(AtomicBool::new(false));
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("arm") => cmd_arm(),
        Some("disarm") => cmd_disarm(),
        Some("status") => cmd_status(&cfg),
        Some("test") => {
            trigger_lockdown(&cfg);
            send_alerts(&cfg, "🔒 SynthOS Dead Man's Switch TEST — lockdown executed.").await;
            Ok(())
        }
        _ => run_daemon(cfg, armed).await,
    }
}
