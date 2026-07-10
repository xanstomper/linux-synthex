// SPDX-License-Identifier: GPL-3.0-or-later
// SynthOS System Daemon (synthos-system-daemon)
// Core system service: IPC bus, hardware monitoring, profile management,
// service health checks, fan control, power events, OSD notifications
// ============================================================================

use std::{
    collections::HashMap,
    fs,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use tokio::{
    sync::broadcast,
    time::sleep,
};
use tracing::{debug, error, info, warn};
use zbus::{connection, interface};

// ── Constants ────────────────────────────────────────────────────────────────
const SERVICE_NAME:     &str = "org.synthos.System";
const OBJECT_PATH:      &str = "/org/synthos/System";
const STATE_DIR:        &str = "/var/lib/synthex";
const CONFIG_PATH:      &str = "/etc/synthex/system-daemon.toml";
const POLL_INTERVAL_MS: u64  = 2000;

// ── Config ───────────────────────────────────────────────────────────────────
#[derive(Debug, Clone, Deserialize)]
struct Config {
    #[serde(default = "default_poll_ms")]
    poll_interval_ms: u64,
    #[serde(default = "default_true")]
    enable_fan_control: bool,
    #[serde(default = "default_true")]
    enable_power_events: bool,
    #[serde(default = "default_true")]
    enable_hw_monitoring: bool,
    #[serde(default)]
    thermal_thresholds: ThermalThresholds,
    #[serde(default)]
    fan_curves: HashMap<String, Vec<(u8, u8)>>,
}

#[derive(Debug, Clone, Deserialize, Default)]
struct ThermalThresholds {
    warn_celsius:  f32,  // default 80°C
    crit_celsius:  f32,  // default 90°C — throttle/notify
    emergency_c:   f32,  // default 100°C — emergency shutdown
}

impl Default for Config {
    fn default() -> Self {
        Self {
            poll_interval_ms:    POLL_INTERVAL_MS,
            enable_fan_control:  true,
            enable_power_events: true,
            enable_hw_monitoring: true,
            thermal_thresholds:  ThermalThresholds {
                warn_celsius:  80.0,
                crit_celsius:  90.0,
                emergency_c:   100.0,
            },
            fan_curves: HashMap::new(),
        }
    }
}

fn default_poll_ms() -> u64 { POLL_INTERVAL_MS }
fn default_true()    -> bool { true }

// ── Hardware snapshot ─────────────────────────────────────────────────────────
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct HwSnapshot {
    cpu_usage_pct:    f32,
    cpu_temp_celsius: f32,
    ram_total_mb:     u64,
    ram_used_mb:      u64,
    gpu_temp_celsius: f32,
    gpu_usage_pct:    f32,
    gpu_vram_used_mb: u64,
    gpu_vram_total_mb: u64,
    battery_pct:      Option<i32>,
    battery_charging: Option<bool>,
    fan_rpm:          Vec<u32>,
    timestamp_ms:     u64,
}

// ── Profile state ─────────────────────────────────────────────────────────────
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct ProfileState {
    active_profile:  String,
    look_and_feel:   String,
    color_scheme:    String,
    version:         String,
}

// ── D-Bus interface ───────────────────────────────────────────────────────────
struct SynthOSSystemIface {
    config:   Config,
    snapshot: Arc<Mutex<HwSnapshot>>,
    profile:  Arc<Mutex<ProfileState>>,
    tx:       broadcast::Sender<String>,
}

#[interface(name = "org.synthos.System1")]
impl SynthOSSystemIface {
    // ── Hardware monitoring ──────────────────────────────────────────────────
    async fn get_hw_snapshot(&self) -> String {
        let snap = self.snapshot.lock().unwrap().clone();
        serde_json::to_string(&snap).unwrap_or_default()
    }

    async fn get_cpu_temp(&self) -> f32 {
        self.snapshot.lock().unwrap().cpu_temp_celsius
    }

    async fn get_gpu_temp(&self) -> f32 {
        self.snapshot.lock().unwrap().gpu_temp_celsius
    }

    async fn get_ram_usage(&self) -> (u64, u64) {
        let s = self.snapshot.lock().unwrap();
        (s.ram_used_mb, s.ram_total_mb)
    }

    async fn get_battery(&self) -> String {
        let s = self.snapshot.lock().unwrap();
        match (s.battery_pct, s.battery_charging) {
            (Some(pct), Some(chg)) => format!("{{\"pct\":{},\"charging\":{}}}", pct, chg),
            _ => "{\"present\":false}".to_string(),
        }
    }

    // ── Profile management ───────────────────────────────────────────────────
    async fn get_active_profile(&self) -> String {
        self.profile.lock().unwrap().active_profile.clone()
    }

    async fn set_profile(&self, profile: &str) -> bool {
        info!("Switching profile to: {}", profile);
        let script = format!("/usr/lib/synthex/apply-profile.sh {}", profile);
        match std::process::Command::new("bash").arg("-c").arg(&script).spawn() {
            Ok(_) => {
                self.profile.lock().unwrap().active_profile = profile.to_string();
                let _ = self.tx.send(format!("profile_changed:{}", profile));
                true
            }
            Err(e) => { error!("Failed to apply profile: {}", e); false }
        }
    }

    // ── Service management ───────────────────────────────────────────────────
    async fn is_service_active(&self, unit: &str) -> bool {
        let out = std::process::Command::new("systemctl")
            .args(["is-active", "--quiet", unit])
            .output();
        matches!(out, Ok(o) if o.status.success())
    }

    async fn set_service_enabled(&self, unit: &str, enable: bool) -> bool {
        let action = if enable { "enable" } else { "disable" };
        let out = std::process::Command::new("systemctl")
            .args([action, "--now", unit])
            .output();
        matches!(out, Ok(o) if o.status.success())
    }

    // ── Power management ─────────────────────────────────────────────────────
    async fn suspend(&self) -> bool {
        info!("Initiating system suspend");
        std::process::Command::new("systemctl")
            .arg("suspend")
            .spawn().is_ok()
    }

    async fn shutdown(&self) -> bool {
        info!("Initiating system shutdown");
        std::process::Command::new("systemctl")
            .arg("poweroff")
            .spawn().is_ok()
    }

    async fn reboot(&self) -> bool {
        info!("Initiating system reboot");
        std::process::Command::new("systemctl")
            .arg("reboot")
            .spawn().is_ok()
    }

    async fn set_power_profile(&self, profile: &str) -> bool {
        // Sets powerprofilesctl profile: power-saver, balanced, performance
        let valid = ["power-saver", "balanced", "performance"];
        if !valid.contains(&profile) { return false; }
        let out = std::process::Command::new("powerprofilesctl")
            .args(["set", profile])
            .output();
        let ok = matches!(out, Ok(o) if o.status.success());
        if ok {
            info!("Power profile set to: {}", profile);
            let _ = self.tx.send(format!("power_profile:{}", profile));
        }
        ok
    }

    async fn get_power_profile(&self) -> String {
        let out = std::process::Command::new("powerprofilesctl")
            .arg("get")
            .output();
        match out {
            Ok(o) => String::from_utf8_lossy(&o.stdout).trim().to_string(),
            Err(_) => "balanced".to_string(),
        }
    }

    // ── Fan control ──────────────────────────────────────────────────────────
    async fn get_fan_speeds(&self) -> Vec<u32> {
        self.snapshot.lock().unwrap().fan_rpm.clone()
    }

    async fn set_fan_mode(&self, mode: &str) -> bool {
        // mode: "auto" | "max" | "silent" | "custom"
        info!("Fan mode: {}", mode);
        match mode {
            "max"    => write_fan_pwm(255),
            "silent" => write_fan_pwm(64),
            "auto"   => restore_fan_auto(),
            _        => false,
        }
    }

    // ── Notifications ────────────────────────────────────────────────────────
    async fn send_osd(&self, title: &str, body: &str, urgency: u8) -> bool {
        let urgency_str = match urgency {
            0 => "low", 1 => "normal", _ => "critical"
        };
        std::process::Command::new("notify-send")
            .args(["-u", urgency_str, "-i", "computer", title, body])
            .spawn().is_ok()
    }

    // ── System info ──────────────────────────────────────────────────────────
    async fn get_version(&self) -> &str { "2026.10" }
    async fn get_hostname(&self) -> String {
        hostname::get().map(|h| h.to_string_lossy().to_string()).unwrap_or_default()
    }
    async fn get_uptime_seconds(&self) -> u64 {
        fs::read_to_string("/proc/uptime")
            .ok()
            .and_then(|s| s.split_whitespace().next()
                         .and_then(|v| v.parse::<f64>().ok()))
            .map(|f| f as u64)
            .unwrap_or(0)
    }

    // ── Event subscribe (returns event stream ticket) ─────────────────────────
    async fn subscribe_events(&self) -> u32 {
        // In a real impl: return a handle the client polls
        // Here we just confirm subscription
        42
    }
}

// ── Fan helpers ───────────────────────────────────────────────────────────────
fn write_fan_pwm(value: u8) -> bool {
    // Find hwmon fan PWM controls
    let hwmon = Path::new("/sys/class/hwmon");
    if !hwmon.exists() { return false; }
    let mut wrote = false;
    if let Ok(entries) = fs::read_dir(hwmon) {
        for entry in entries.flatten() {
            let base = entry.path();
            for i in 1..=4u8 {
                let enable = base.join(format!("pwm{}_enable", i));
                let pwm    = base.join(format!("pwm{}", i));
                if pwm.exists() {
                    let _ = fs::write(&enable, "1");
                    let _ = fs::write(&pwm, value.to_string());
                    wrote = true;
                }
            }
        }
    }
    wrote
}

fn restore_fan_auto() -> bool {
    let hwmon = Path::new("/sys/class/hwmon");
    if !hwmon.exists() { return false; }
    let mut ok = false;
    if let Ok(entries) = fs::read_dir(hwmon) {
        for entry in entries.flatten() {
            let base = entry.path();
            for i in 1..=4u8 {
                let enable = base.join(format!("pwm{}_enable", i));
                if enable.exists() {
                    let _ = fs::write(&enable, "2"); // 2 = automatic
                    ok = true;
                }
            }
        }
    }
    ok
}

// ── Hardware poller ───────────────────────────────────────────────────────────
async fn hw_poll_loop(
    snap:     Arc<Mutex<HwSnapshot>>,
    config:   Config,
    tx:       broadcast::Sender<String>,
) {
    let interval = Duration::from_millis(config.poll_interval_ms);
    let mut last_warn = Instant::now() - Duration::from_secs(60);

    loop {
        sleep(interval).await;

        let mut s = HwSnapshot::default();
        s.timestamp_ms = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis() as u64;

        // ── CPU usage ──
        if let Ok(stat) = fs::read_to_string("/proc/stat") {
            if let Some(line) = stat.lines().next() {
                let vals: Vec<u64> = line.split_whitespace()
                    .skip(1).take(7)
                    .filter_map(|v| v.parse().ok())
                    .collect();
                if vals.len() >= 4 {
                    let idle  = vals[3];
                    let total: u64 = vals.iter().sum();
                    if total > 0 {
                        s.cpu_usage_pct = 100.0 * (1.0 - idle as f32 / total as f32);
                    }
                }
            }
        }

        // ── CPU temperature ──
        s.cpu_temp_celsius = read_thermal("cpu")
            .or_else(|| read_thermal("x86_pkg_temp"))
            .or_else(|| read_hwmon_temp("coretemp"))
            .unwrap_or(0.0);

        // ── RAM ──
        if let Ok(meminfo) = fs::read_to_string("/proc/meminfo") {
            let map: HashMap<&str, u64> = meminfo.lines()
                .filter_map(|l| {
                    let mut it = l.split_whitespace();
                    let key = it.next()?.trim_end_matches(':');
                    let val = it.next()?.parse::<u64>().ok()?;
                    Some((key, val))
                })
                .collect();
            let total    = map.get("MemTotal").copied().unwrap_or(0);
            let free     = map.get("MemFree").copied().unwrap_or(0);
            let cached   = map.get("Cached").copied().unwrap_or(0);
            let buffers  = map.get("Buffers").copied().unwrap_or(0);
            s.ram_total_mb = total / 1024;
            s.ram_used_mb  = (total - free - cached - buffers) / 1024;
        }

        // ── GPU (NVIDIA) ──
        if let Ok(out) = std::process::Command::new("nvidia-smi")
            .args(["--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
                   "--format=csv,noheader,nounits"])
            .output()
        {
            let line = String::from_utf8_lossy(&out.stdout);
            let parts: Vec<f32> = line.trim().split(',')
                .filter_map(|v| v.trim().parse().ok())
                .collect();
            if parts.len() >= 4 {
                s.gpu_temp_celsius = parts[0];
                s.gpu_usage_pct    = parts[1];
                s.gpu_vram_used_mb = parts[2] as u64;
                s.gpu_vram_total_mb= parts[3] as u64;
            }
        }
        // AMD GPU fallback via hwmon
        if s.gpu_temp_celsius == 0.0 {
            s.gpu_temp_celsius = read_hwmon_temp("amdgpu").unwrap_or(0.0);
        }

        // ── Battery ──
        let bat_path = Path::new("/sys/class/power_supply/BAT0");
        if bat_path.exists() {
            let cap     = read_sysfs_u32(bat_path.join("capacity"));
            let status  = fs::read_to_string(bat_path.join("status"))
                              .unwrap_or_default();
            s.battery_pct      = cap.map(|v| v as i32);
            s.battery_charging = Some(status.trim() == "Charging");
        }

        // ── Fans ──
        s.fan_rpm = read_fan_speeds();

        // ── Thermal alerts ──
        let cpu_t = s.cpu_temp_celsius;
        if cpu_t >= config.thermal_thresholds.emergency_c && last_warn.elapsed() > Duration::from_secs(10) {
            error!("🚨 EMERGENCY THERMAL: CPU {}°C — initiating suspend!", cpu_t);
            let _ = tx.send(format!("thermal_emergency:{}", cpu_t));
            let _ = std::process::Command::new("systemctl").arg("suspend").spawn();
            last_warn = Instant::now();
        } else if cpu_t >= config.thermal_thresholds.crit_celsius && last_warn.elapsed() > Duration::from_secs(30) {
            warn!("⚠ Critical CPU temp: {}°C", cpu_t);
            let _ = tx.send(format!("thermal_critical:{}", cpu_t));
            let _ = std::process::Command::new("notify-send")
                .args(["-u", "critical", "-i", "temperature-warm",
                       "SynthOS — Thermal Warning",
                       &format!("CPU temperature: {}°C — system may throttle", cpu_t)])
                .spawn();
            last_warn = Instant::now();
        } else if cpu_t >= config.thermal_thresholds.warn_celsius && last_warn.elapsed() > Duration::from_secs(60) {
            warn!("CPU temp elevated: {}°C", cpu_t);
            let _ = tx.send(format!("thermal_warn:{}", cpu_t));
            last_warn = Instant::now();
        }

        *snap.lock().unwrap() = s;
        debug!("HW poll: CPU={:.1}% {:.1}°C  RAM={}/{} MB", snap.lock().unwrap().cpu_usage_pct, cpu_t, snap.lock().unwrap().ram_used_mb, snap.lock().unwrap().ram_total_mb);
    }
}

// ── sysfs helpers ─────────────────────────────────────────────────────────────
fn read_thermal(zone_type: &str) -> Option<f32> {
    let base = Path::new("/sys/class/thermal");
    for i in 0..16u8 {
        let zone = base.join(format!("thermal_zone{}", i));
        if let Ok(t) = fs::read_to_string(zone.join("type")) {
            if t.trim() == zone_type {
                if let Ok(temp) = fs::read_to_string(zone.join("temp")) {
                    return temp.trim().parse::<f32>().ok().map(|v| v / 1000.0);
                }
            }
        }
    }
    None
}

fn read_hwmon_temp(name: &str) -> Option<f32> {
    let base = Path::new("/sys/class/hwmon");
    for entry in fs::read_dir(base).ok()?.flatten() {
        let n = fs::read_to_string(entry.path().join("name"))
            .unwrap_or_default();
        if n.trim() == name {
            // Read temp1_input (millidegrees)
            if let Ok(v) = fs::read_to_string(entry.path().join("temp1_input")) {
                return v.trim().parse::<f32>().ok().map(|x| x / 1000.0);
            }
        }
    }
    None
}

fn read_sysfs_u32(path: PathBuf) -> Option<u32> {
    fs::read_to_string(path).ok()?.trim().parse().ok()
}

fn read_fan_speeds() -> Vec<u32> {
    let mut speeds = Vec::new();
    if let Ok(entries) = fs::read_dir("/sys/class/hwmon") {
        for entry in entries.flatten() {
            for i in 1..=4u8 {
                let p = entry.path().join(format!("fan{}_input", i));
                if let Some(v) = read_sysfs_u32(p) {
                    speeds.push(v);
                }
            }
        }
    }
    speeds
}

// ── Main ──────────────────────────────────────────────────────────────────────
#[tokio::main]
async fn main() -> Result<()> {
    // Init logging
    tracing_subscriber::fmt()
        .with_env_filter(
            std::env::var("RUST_LOG")
                .unwrap_or_else(|_| "synthex_system_daemon=info".to_string())
        )
        .init();

    info!("SynthOS System Daemon v{} starting…", "2026.10");

    // Load config
    let config = if Path::new(CONFIG_PATH).exists() {
        let raw = fs::read_to_string(CONFIG_PATH)
            .context("reading config")?;
        toml::from_str::<Config>(&raw).unwrap_or_default()
    } else {
        Config::default()
    };

    // Load profile state
    let profile_path = Path::new(STATE_DIR).join("install-profile.json");
    let profile = if profile_path.exists() {
        let raw = fs::read_to_string(&profile_path).unwrap_or_default();
        serde_json::from_str::<ProfileState>(&raw).unwrap_or_default()
    } else {
        ProfileState { active_profile: "classic".to_string(), ..Default::default() }
    };

    info!("Active profile: {}", profile.active_profile);

    // Shared state
    let snapshot = Arc::new(Mutex::new(HwSnapshot::default()));
    let profile  = Arc::new(Mutex::new(profile));
    let (tx, _rx) = broadcast::channel::<String>(128);

    // Start HW poller
    if config.enable_hw_monitoring {
        let snap_c  = Arc::clone(&snapshot);
        let cfg_c   = config.clone();
        let tx_c    = tx.clone();
        tokio::spawn(async move {
            hw_poll_loop(snap_c, cfg_c, tx_c).await;
        });
        info!("Hardware monitoring started ({}ms interval)", config.poll_interval_ms);
    }

    // Build D-Bus connection
    let iface = SynthOSSystemIface {
        config:   config.clone(),
        snapshot: Arc::clone(&snapshot),
        profile:  Arc::clone(&profile),
        tx:       tx.clone(),
    };

    let conn = connection::Builder::system()?
        .name(SERVICE_NAME)?
        .serve_at(OBJECT_PATH, iface)?
        .build()
        .await
        .context("connecting to D-Bus system bus")?;

    info!("D-Bus service registered: {} at {}", SERVICE_NAME, OBJECT_PATH);

    // Handle SIGTERM / SIGINT gracefully
    tokio::signal::ctrl_c().await?;
    info!("Shutting down SynthOS System Daemon");
    drop(conn);
    Ok(())
}
