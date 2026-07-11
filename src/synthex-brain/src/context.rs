//! System context monitor — polls live OS state every 2 seconds.
//!
//! Data collected per cycle:
//!   • Active window (title, app, PID) via `xdotool`
//!   • Current KDE/X11 workspace number
//!   • Recent shell commands from `~/.bash_history`
//!   • CPU usage (delta between successive `/proc/stat` readings)
//!   • RAM usage from `/proc/meminfo`
//!   • TCP connection count from `/proc/net/tcp{,6}`
//!   • Open-file sample across all processes via `/proc/*/fd`

use std::{
    collections::{HashMap, HashSet},
    path::Path,
    time::Duration,
};

use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::{sync::RwLock, time};
use tracing::{trace, warn};

// ── Public snapshot type ──────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ContextSnapshot {
    pub active_window_title: String,
    pub active_window_app:   String,
    pub active_window_pid:   u32,
    /// Representative sample of open files across all processes (≤50 paths).
    pub open_files:          Vec<String>,
    /// Last 20 non-comment lines from `~/.bash_history`.
    pub recent_commands:     Vec<String>,
    pub cpu_usage_pct:       f32,
    pub ram_used_mb:         u64,
    pub ram_total_mb:        u64,
    pub net_connections:     u32,
    pub current_workspace:   u32,
    /// Caller-settable extra fields (via `UpdateContext`).
    #[serde(default)]
    pub extra:               HashMap<String, serde_json::Value>,
    pub updated_at:          DateTime<Utc>,
}

// ── Monitor ───────────────────────────────────────────────────────────────────

pub struct ContextMonitor {
    state:    RwLock<ContextSnapshot>,
    /// Previous `/proc/stat` totals for CPU-delta calculation.
    prev_cpu: RwLock<Option<CpuStat>>,
}

impl ContextMonitor {
    pub fn new() -> Self {
        Self {
            state: RwLock::new(ContextSnapshot {
                current_workspace: 1,
                updated_at: Utc::now(),
                ..Default::default()
            }),
            prev_cpu: RwLock::new(None),
        }
    }

    /// Clone the latest snapshot (lock-free read after the initial write).
    pub async fn snapshot(&self) -> ContextSnapshot {
        self.state.read().await.clone()
    }

    /// Update a single named field, preserving all others.
    pub async fn update_field(&self, field: &str, value: serde_json::Value) -> Result<()> {
        let mut snap = self.state.write().await;
        match field {
            "active_window_title" => {
                snap.active_window_title = value.as_str().unwrap_or("").to_string();
            }
            "active_window_app" => {
                snap.active_window_app = value.as_str().unwrap_or("").to_string();
            }
            "active_window_pid" => {
                snap.active_window_pid = value.as_u64().unwrap_or(0) as u32;
            }
            "current_workspace" => {
                snap.current_workspace = value.as_u64().unwrap_or(1) as u32;
            }
            _ => {
                snap.extra.insert(field.to_string(), value);
            }
        }
        snap.updated_at = Utc::now();
        Ok(())
    }

    /// Long-running poll loop.  Spawn this in a dedicated `tokio::spawn`.
    pub async fn run_poll_loop(&self) {
        let mut interval = time::interval(Duration::from_secs(2));
        interval.set_missed_tick_behavior(time::MissedTickBehavior::Skip);

        loop {
            interval.tick().await;

            // Gather new data outside the write lock where possible.
            let window  = get_active_window().await;
            let ws      = get_current_workspace().await;
            let cmds    = get_recent_commands();
            let files   = sample_open_files(50);
            let ram     = read_ram_usage();
            let net     = count_net_connections();
            let cpu_new = read_cpu_stat();

            // Compute CPU delta.
            let cpu_pct = {
                let prev = self.prev_cpu.read().await.clone();
                if let (Some(p), Some(c)) = (prev, cpu_new) {
                    let dt = c.total.saturating_sub(p.total) as f32;
                    let di = c.idle.saturating_sub(p.idle)   as f32;
                    let pct = if dt > 0.0 { 100.0 * (1.0 - di / dt) } else { 0.0 };
                    *self.prev_cpu.write().await = Some(c);
                    pct.clamp(0.0, 100.0)
                } else {
                    if let Some(s) = read_cpu_stat() {
                        *self.prev_cpu.write().await = Some(s);
                    }
                    0.0
                }
            };

            // Commit to shared state.
            let mut snap = self.state.write().await;
            if let Some((title, app, pid)) = window {
                snap.active_window_title = title;
                snap.active_window_app   = app;
                snap.active_window_pid   = pid;
            }
            if let Some(n) = ws {
                snap.current_workspace = n;
            }
            if let Some(c) = cmds  { snap.recent_commands  = c; }
            snap.open_files = files;
            if let Some((used, total)) = ram {
                snap.ram_used_mb  = used;
                snap.ram_total_mb = total;
            }
            if let Some(n) = net { snap.net_connections = n; }
            snap.cpu_usage_pct = cpu_pct;
            snap.updated_at    = Utc::now();

            trace!(
                cpu  = snap.cpu_usage_pct,
                ram  = snap.ram_used_mb,
                ws   = snap.current_workspace,
                win  = snap.active_window_app,
                "context poll"
            );
        }
    }
}

// ── CPU stat ──────────────────────────────────────────────────────────────────

#[derive(Clone)]
struct CpuStat {
    total: u64,
    idle:  u64,
}

fn read_cpu_stat() -> Option<CpuStat> {
    let content = std::fs::read_to_string("/proc/stat").ok()?;
    let line = content.lines().next()?;
    // cpu  user nice system idle iowait irq softirq steal guest guest_nice
    let fields: Vec<u64> = line
        .split_whitespace()
        .skip(1)
        .filter_map(|s| s.parse().ok())
        .collect();
    let total: u64 = fields.iter().sum();
    let idle: u64 = fields.get(3).copied().unwrap_or(0)  // idle
                  + fields.get(4).copied().unwrap_or(0); // iowait
    Some(CpuStat { total, idle })
}

// ── Active window (xdotool / AT-SPI2 fallback) ───────────────────────────────

async fn get_active_window() -> Option<(String, String, u32)> {
    // Primary: xdotool
    let id_out = tokio::process::Command::new("xdotool")
        .args(["getactivewindow"])
        .output()
        .await
        .ok()?;
    let win_id = String::from_utf8_lossy(&id_out.stdout).trim().to_string();
    if win_id.is_empty() {
        return None;
    }

    let title = xdotool_str(&["getwindowname", &win_id]).await;
    let pid_s = xdotool_str(&["getwindowpid", &win_id]).await;
    let pid: u32 = pid_s.trim().parse().unwrap_or(0);

    let app = if pid > 0 {
        std::fs::read_to_string(format!("/proc/{pid}/comm"))
            .unwrap_or_default()
            .trim()
            .to_string()
    } else {
        String::new()
    };

    Some((title.trim().to_string(), app, pid))
}

async fn xdotool_str(args: &[&str]) -> String {
    tokio::process::Command::new("xdotool")
        .args(args)
        .output()
        .await
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default()
}

// ── Workspace ─────────────────────────────────────────────────────────────────

async fn get_current_workspace() -> Option<u32> {
    let out = tokio::process::Command::new("xdotool")
        .args(["get_desktop"])
        .output()
        .await
        .ok()?;
    let n: u32 = String::from_utf8_lossy(&out.stdout)
        .trim()
        .parse()
        .ok()?;
    Some(n + 1) // xdotool reports 0-based; we use 1-based
}

// ── Shell history ─────────────────────────────────────────────────────────────

fn get_recent_commands() -> Option<Vec<String>> {
    let home = std::env::var("HOME").ok()?;
    let hist = std::fs::read_to_string(format!("{home}/.bash_history")).ok()?;
    let cmds: Vec<String> = hist
        .lines()
        .filter(|l| !l.starts_with('#') && !l.is_empty())
        .rev()
        .take(20)
        .map(|s| s.trim().to_string())
        .collect();
    Some(cmds)
}

// ── RAM ───────────────────────────────────────────────────────────────────────

fn read_ram_usage() -> Option<(u64, u64)> {
    let content = std::fs::read_to_string("/proc/meminfo").ok()?;
    let mut total_kb = 0u64;
    let mut avail_kb = 0u64;

    for line in content.lines() {
        if line.starts_with("MemTotal:") {
            total_kb = parse_kb(line);
        } else if line.starts_with("MemAvailable:") {
            avail_kb = parse_kb(line);
        }
    }

    let used_kb = total_kb.saturating_sub(avail_kb);
    Some((used_kb / 1024, total_kb / 1024))
}

fn parse_kb(line: &str) -> u64 {
    line.split_whitespace()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(0)
}

// ── Network connections ───────────────────────────────────────────────────────

fn count_net_connections() -> Option<u32> {
    let tcp  = count_lines("/proc/net/tcp");
    let tcp6 = count_lines("/proc/net/tcp6");
    Some(tcp + tcp6)
}

fn count_lines(path: &str) -> u32 {
    std::fs::read_to_string(path)
        .map(|s| s.lines().count().saturating_sub(1) as u32) // subtract header
        .unwrap_or(0)
}

// ── Open-file sample ──────────────────────────────────────────────────────────

/// Walk `/proc/*/fd` and collect up to `limit` real file paths
/// (skipping /proc, /dev, /sys and anonymous FDs such as sockets and pipes).
fn sample_open_files(limit: usize) -> Vec<String> {
    let mut seen: HashSet<String> = HashSet::new();

    let Ok(proc) = std::fs::read_dir("/proc") else {
        return vec![];
    };

    'pids: for entry in proc.filter_map(|e| e.ok()) {
        if !entry
            .file_name()
            .to_string_lossy()
            .chars()
            .all(|c| c.is_ascii_digit())
        {
            continue;
        }
        let fd_dir = entry.path().join("fd");
        let Ok(fds) = std::fs::read_dir(&fd_dir) else {
            continue;
        };
        for fd in fds.filter_map(|e| e.ok()) {
            if let Ok(target) = std::fs::read_link(fd.path()) {
                let s = target.to_string_lossy();
                if s.starts_with('/')
                    && !s.starts_with("/proc")
                    && !s.starts_with("/dev")
                    && !s.starts_with("/sys")
                    && !s.contains("socket:[")
                    && !s.contains("pipe:[")
                {
                    seen.insert(s.into_owned());
                    if seen.len() >= limit {
                        break 'pids;
                    }
                }
            }
        }
    }

    seen.into_iter().take(limit).collect()
}
