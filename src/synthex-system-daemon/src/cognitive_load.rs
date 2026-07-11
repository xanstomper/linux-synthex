// SPDX-License-Identifier: GPL-3.0-or-later
//! Cognitive Load Monitor
//!
//! Tracks four axes of user cognitive pressure and aggregates them into a
//! 0–100 "cognitive load score":
//!
//!  • Open window/surface count  (via wmctrl, hyprctl, or /proc fd walk)
//!  • Input-event rate           (keyboard + mouse IRQ deltas from /proc/interrupts)
//!  • CPU pressure               (/proc/stat delta)
//!  • RAM pressure               (/proc/meminfo)
//!  • Time since last break      (penalises long uninterrupted sessions)
//!
//! Exposed as D-Bus interface  org.synthex.CognitiveLoad
//!                             /org/synthex/CognitiveLoad
//!
//! When score ≥ BREAK_THRESHOLD the daemon sends a desktop notification and
//! optionally dims secondary monitors via xrandr / wlr-randr.

use anyhow::{Context, Result};
use std::{sync::Arc, time::{Duration, Instant}};
use tokio::{fs, sync::RwLock, time::sleep};
use tracing::{debug, info, warn};
use zbus::interface;

// ─── tunables ────────────────────────────────────────────────────────────────

/// How often the monitor re-samples all metrics.
const POLL_MS: u64 = 5_000;

/// Score at or above which a break is recommended.
const BREAK_THRESHOLD: u32 = 75;

/// Seconds of near-zero input that count as "a break has been taken".
const BREAK_RESET_SECS: u64 = 300;

/// Maximum tracked input events/second — clamps the input axis to [0, 1].
const MAX_EPS: f64 = 20.0;

// ─── shared state ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Default)]
pub struct CogLoad {
    pub window_count:      u32,
    pub input_eps:         f64,  // events/second, clamped to [0, MAX_EPS]
    pub cpu_pressure:      f64,  // [0.0, 1.0]
    pub ram_pressure:      f64,  // [0.0, 1.0]
    pub secs_since_break:  u64,
    pub score:             u32,  // [0, 100]
    pub break_recommended: bool,
}

pub type SharedCogLoad = Arc<RwLock<CogLoad>>;

pub fn new_shared() -> SharedCogLoad {
    Arc::new(RwLock::new(CogLoad::default()))
}

// ─── D-Bus interface ──────────────────────────────────────────────────────────

pub struct CognitiveLoadIface {
    state: SharedCogLoad,
}

impl CognitiveLoadIface {
    pub fn new(state: SharedCogLoad) -> Self {
        Self { state }
    }
}

#[interface(name = "org.synthex.CognitiveLoad")]
impl CognitiveLoadIface {
    /// Composite cognitive load score, 0 (calm) – 100 (overwhelmed).
    async fn get_score(&self) -> u32 {
        self.state.read().await.score
    }

    async fn get_window_count(&self) -> u32 {
        self.state.read().await.window_count
    }

    /// Input event rate in events/second (keyboard + mouse combined).
    async fn get_input_rate(&self) -> f64 {
        self.state.read().await.input_eps
    }

    /// CPU utilisation [0.0, 1.0].
    async fn get_cpu_pressure(&self) -> f64 {
        self.state.read().await.cpu_pressure
    }

    /// RAM utilisation [0.0, 1.0].
    async fn get_ram_pressure(&self) -> f64 {
        self.state.read().await.ram_pressure
    }

    /// Seconds elapsed since the last detected break (≥5 min of idle input).
    async fn get_secs_since_break(&self) -> u64 {
        self.state.read().await.secs_since_break
    }

    async fn is_break_recommended(&self) -> bool {
        self.state.read().await.break_recommended
    }

    /// All metrics as a JSON object for tray / applet consumers.
    async fn get_snapshot_json(&self) -> String {
        let s = self.state.read().await.clone();
        serde_json::json!({
            "score":             s.score,
            "window_count":      s.window_count,
            "input_eps":         s.input_eps,
            "cpu_pressure":      s.cpu_pressure,
            "ram_pressure":      s.ram_pressure,
            "secs_since_break":  s.secs_since_break,
            "break_recommended": s.break_recommended,
        })
        .to_string()
    }
}

// ─── window count ─────────────────────────────────────────────────────────────

/// Count open windows/surfaces across X11 and Wayland compositors.
async fn count_windows() -> u32 {
    // 1. wmctrl (X11)
    if let Ok(out) = tokio::process::Command::new("wmctrl")
        .arg("-l")
        .output()
        .await
    {
        if out.status.success() {
            return out.stdout.iter().filter(|&&b| b == b'\n').count() as u32;
        }
    }

    // 2. hyprctl (Hyprland / wlroots Wayland)
    if let Ok(out) = tokio::process::Command::new("hyprctl")
        .args(["clients", "-j"])
        .output()
        .await
    {
        if out.status.success() {
            if let Ok(serde_json::Value::Array(arr)) =
                serde_json::from_slice::<serde_json::Value>(&out.stdout)
            {
                return arr.len() as u32;
            }
        }
    }

    // 3. Walk /proc/*/fd for display-socket symlinks (best-effort fallback).
    count_display_processes().await.unwrap_or(0)
}

async fn count_display_processes() -> Result<u32> {
    let mut count = 0u32;
    let mut rd = fs::read_dir("/proc").await.context("open /proc")?;
    while let Some(entry) = rd.next_entry().await? {
        let name = entry.file_name();
        if !name.to_string_lossy().bytes().all(|b| b.is_ascii_digit()) {
            continue;
        }
        let fd_dir = entry.path().join("fd");
        let Ok(mut fds) = fs::read_dir(&fd_dir).await else { continue };
        while let Ok(Some(fd)) = fds.next_entry().await {
            if let Ok(target) = fs::read_link(fd.path()).await {
                let t = target.to_string_lossy();
                if t.contains("wayland") || t.contains("/tmp/.X") {
                    count += 1;
                    break; // one counter per process
                }
            }
        }
    }
    Ok(count)
}

// ─── input event sampler ─────────────────────────────────────────────────────

struct InputSampler {
    last_count: u64,
    last_time:  Instant,
}

impl InputSampler {
    fn new() -> Self {
        Self { last_count: 0, last_time: Instant::now() }
    }

    async fn sample_eps(&mut self) -> f64 {
        let now   = Instant::now();
        let count = read_input_events().await;
        let dt    = now.duration_since(self.last_time).as_secs_f64().max(0.001);
        let diff  = count.saturating_sub(self.last_count) as f64;
        self.last_count = count;
        self.last_time  = now;
        (diff / dt).min(MAX_EPS)
    }
}

/// Sum interrupt counts for keyboard / mouse lines in /proc/interrupts.
async fn read_input_events() -> u64 {
    let Ok(text) = fs::read_to_string("/proc/interrupts").await else {
        return 0;
    };
    let mut total = 0u64;
    for line in text.lines() {
        let lower = line.to_ascii_lowercase();
        if lower.contains("keyboard")
            || lower.contains("mouse")
            || lower.contains("i8042")
        {
            // columns after the IRQ label are per-CPU counts
            for tok in line.split_whitespace().skip(1) {
                if let Ok(n) = tok.parse::<u64>() {
                    total += n;
                } else {
                    break; // hit the text description
                }
            }
        }
    }
    total
}

// ─── CPU pressure ─────────────────────────────────────────────────────────────

struct CpuSampler {
    prev_idle:  u64,
    prev_total: u64,
}

impl CpuSampler {
    fn new() -> Self {
        Self { prev_idle: 0, prev_total: 0 }
    }

    async fn sample(&mut self) -> f64 {
        let Ok(text) = fs::read_to_string("/proc/stat").await else {
            return 0.0;
        };
        let line = text.lines().next().unwrap_or("");
        let nums: Vec<u64> = line
            .split_whitespace()
            .skip(1) // skip "cpu" label
            .filter_map(|s| s.parse().ok())
            .collect();
        if nums.len() < 4 {
            return 0.0;
        }
        let idle:  u64 = nums[3];
        let total: u64 = nums.iter().sum();
        let d_idle  = idle.saturating_sub(self.prev_idle);
        let d_total = total.saturating_sub(self.prev_total);
        self.prev_idle  = idle;
        self.prev_total = total;
        if d_total == 0 {
            return 0.0;
        }
        1.0 - (d_idle as f64 / d_total as f64)
    }
}

// ─── RAM pressure ─────────────────────────────────────────────────────────────

async fn ram_pressure() -> f64 {
    let Ok(text) = fs::read_to_string("/proc/meminfo").await else {
        return 0.0;
    };
    let mut total     = 0u64;
    let mut available = 0u64;
    for line in text.lines() {
        if line.starts_with("MemTotal:") {
            total = parse_meminfo_kb(line);
        } else if line.starts_with("MemAvailable:") {
            available = parse_meminfo_kb(line);
        }
    }
    if total == 0 {
        return 0.0;
    }
    (1.0 - (available as f64 / total as f64)).clamp(0.0, 1.0)
}

fn parse_meminfo_kb(line: &str) -> u64 {
    line.split_whitespace()
        .nth(1)
        .and_then(|s| s.parse().ok())
        .unwrap_or(0)
}

// ─── score computation ────────────────────────────────────────────────────────

fn compute_score(
    windows:         u32,
    input_eps:       f64,
    cpu:             f64,
    ram:             f64,
    secs_no_break:   u64,
) -> u32 {
    // Each axis normalised to [0.0, 1.0]
    let w = (windows as f64 / 20.0).min(1.0);          // 20 windows = max
    let i = (input_eps / MAX_EPS).min(1.0);
    let b = (secs_no_break as f64 / 3_600.0).min(1.0); // 1 h = max break penalty

    let score = 0.25 * w + 0.20 * i + 0.20 * cpu + 0.15 * ram + 0.20 * b;
    (score * 100.0).round().clamp(0.0, 100.0) as u32
}

// ─── secondary monitor dimming ────────────────────────────────────────────────

async fn set_secondary_monitor_brightness(dim: bool) {
    let brightness = if dim { "0.4" } else { "1.0" };

    // xrandr path (X11)
    if let Ok(out) = tokio::process::Command::new("xrandr").output().await {
        let text = String::from_utf8_lossy(&out.stdout);
        for line in text.lines() {
            if line.contains(" connected") && !line.contains("primary") {
                if let Some(output) = line.split_whitespace().next() {
                    let _ = tokio::process::Command::new("xrandr")
                        .args(["--output", output, "--brightness", brightness])
                        .status()
                        .await;
                    debug!(%output, brightness, "set xrandr brightness");
                }
            }
        }
        return;
    }

    // wlr-randr path (wlroots Wayland)
    // wlr-randr --output <name> --brightness <val>  (not universally supported)
    // We log rather than fail silently.
    warn!("xrandr not available; Wayland display dimming may not be supported");
}

// ─── desktop notification ─────────────────────────────────────────────────────

async fn notify_break() {
    let _ = tokio::process::Command::new("notify-send")
        .args([
            "--urgency=low",
            "--icon=preferences-desktop-screensaver",
            "--app-name=SynthOS",
            "Time for a break",
            "Your cognitive load score is high.\n\
             Consider stepping away for 5–10 minutes.",
        ])
        .status()
        .await;
}

// ─── main poll loop ───────────────────────────────────────────────────────────

pub async fn run_cognitive_monitor(state: SharedCogLoad) -> Result<()> {
    info!("Cognitive Load Monitor starting (poll={}ms, threshold={})", POLL_MS, BREAK_THRESHOLD);

    let mut cpu_sampler   = CpuSampler::new();
    let mut input_sampler = InputSampler::new();
    let mut last_break    = Instant::now();
    let mut last_input_at = Instant::now(); // last time input_eps was non-zero
    let mut notified      = false;
    let mut dimmed        = false;

    // Warm-up: prime the delta samplers so first real reading is meaningful.
    let _ = cpu_sampler.sample().await;
    let _ = input_sampler.sample_eps().await;
    sleep(Duration::from_millis(POLL_MS)).await;

    loop {
        let windows   = count_windows().await;
        let input_eps = input_sampler.sample_eps().await;
        let cpu       = cpu_sampler.sample().await;
        let ram       = ram_pressure().await;

        // ── break detection ───────────────────────────────────────────────
        if input_eps > 0.1 {
            last_input_at = Instant::now();
        } else if last_input_at.elapsed() >= Duration::from_secs(BREAK_RESET_SECS) {
            // User has been idle long enough — treat as a break.
            last_break  = Instant::now();
            notified    = false;
            if dimmed {
                set_secondary_monitor_brightness(false).await;
                dimmed = false;
            }
            debug!("Break detected — cognitive load timer reset");
        }

        let secs_since_break  = last_break.elapsed().as_secs();
        let score             = compute_score(windows, input_eps, cpu, ram, secs_since_break);
        let break_recommended = score >= BREAK_THRESHOLD;

        {
            let mut s          = state.write().await;
            s.window_count     = windows;
            s.input_eps        = input_eps;
            s.cpu_pressure     = cpu;
            s.ram_pressure     = ram;
            s.secs_since_break = secs_since_break;
            s.score            = score;
            s.break_recommended = break_recommended;
        }

        debug!(score, windows, input_eps, cpu, ram, secs_since_break,
               "CognLoad poll");

        if break_recommended && !notified {
            info!(score, "Cognitive overload — sending break notification");
            notify_break().await;
            set_secondary_monitor_brightness(true).await;
            dimmed   = true;
            notified = true;
        }

        sleep(Duration::from_millis(POLL_MS)).await;
    }
}
