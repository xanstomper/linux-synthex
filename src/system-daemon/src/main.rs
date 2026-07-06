// SPDX-License-Identifier: MIT OR Apache-2.0
//
// solus-system-daemon — System performance auto-tuner for Solus Linux
//
// Auto-detects hardware capabilities and configures optimal performance:
//   - Form factor (laptop/desktop/VM) → power profile
//   - Display capabilities (VRR, HDR, max refresh rate) → KWin config
//   - CPU governor + scheduler → mode + AC/battery aware
//   - TDP management → laptop power limits
//   - ACPI power source monitoring → auto-switch modes
//   - GPU power management → amdgpu/nvidia/i915 power levels

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::time::Duration;
use tokio::time;
use tracing::{error, info, warn};

// ─── Modes ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum PerformanceMode {
    Gaming,
    Creator,
    Balanced,
    Battery,
    Idle,
}

impl std::fmt::Display for PerformanceMode {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PerformanceMode::Gaming => write!(f, "gaming"),
            PerformanceMode::Creator => write!(f, "creator"),
            PerformanceMode::Balanced => write!(f, "balanced"),
            PerformanceMode::Battery => write!(f, "battery"),
            PerformanceMode::Idle => write!(f, "idle"),
        }
    }
}

impl PerformanceMode {
    pub fn from_str(s: &str) -> Option<Self> {
        match s {
            "gaming" => Some(Self::Gaming),
            "creator" => Some(Self::Creator),
            "balanced" => Some(Self::Balanced),
            "battery" => Some(Self::Battery),
            "idle" => Some(Self::Idle),
            _ => None,
        }
    }

    /// CPU governor for this mode (AC power)
    pub fn governor_ac(&self) -> &'static str {
        match self {
            Self::Gaming => "performance",
            Self::Creator => "performance",
            Self::Balanced => "ondemand",
            Self::Battery => "powersave",
            Self::Idle => "powersave",
        }
    }

    /// CPU governor for this mode (battery power)
    pub fn governor_battery(&self) -> &'static str {
        match self {
            Self::Gaming => "ondemand",
            Self::Creator => "ondemand",
            Self::Balanced => "powersave",
            Self::Battery => "powersave",
            Self::Idle => "powersave",
        }
    }

    /// GPU power level for this mode
    pub fn gpu_level(&self) -> &'static str {
        match self {
            Self::Gaming => "high",
            Self::Creator => "high",
            Self::Balanced => "auto",
            Self::Battery => "low",
            Self::Idle => "low",
        }
    }

    /// Should compositor be suspended?
    pub fn suspend_compositor(&self) -> bool {
        matches!(self, Self::Gaming)
    }

    /// Should GameMode be enabled?
    pub fn enable_gamemode(&self) -> bool {
        matches!(self, Self::Gaming)
    }

    /// Energy_performance_preference for Intel
    pub fn energy_preference(&self) -> &'static str {
        match self {
            Self::Gaming => "performance",
            Self::Creator => "performance",
            Self::Balanced => "normal",
            Self::Battery => "powersave",
            Self::Idle => "powersave",
        }
    }
}

// ─── Form Factor ───────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum FormFactor {
    Laptop,
    Desktop,
    Server,
    VirtualMachine,
    Unknown,
}

impl std::fmt::Display for FormFactor {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Laptop => write!(f, "laptop"),
            Self::Desktop => write!(f, "desktop"),
            Self::Server => write!(f, "server"),
            Self::VirtualMachine => write!(f, "vm"),
            Self::Unknown => write!(f, "unknown"),
        }
    }
}

/// Detect system form factor from DMI/chassis info
pub fn detect_form_factor() -> FormFactor {
    // Check for VM first
    let cpuinfo = std::fs::read_to_string("/proc/cpuinfo").unwrap_or_default();
    if cpuinfo.contains("hypervisor") {
        return FormFactor::VirtualMachine;
    }

    // Check DMI chassis type
    let chassis = std::fs::read_to_string("/sys/class/dmi/id/chassis_type")
        .or_else(|_| std::fs::read_to_string("/sys/devices/virtual/dmi/id/chassis_type"))
        .unwrap_or_default();
    let chassis = chassis.trim();

    match chassis {
        "9" | "10" | "14" | "30" | "31" => FormFactor::Laptop,  // Notebook, Laptop, Notebook, Convertible, Detachable
        "3" | "4" | "5" | "6" | "7" | "8" |
        "11" | "13" | "15" | "16" | "17" |
        "18" | "21" | "22" | "23" | "24" |
        "32" | "33" | "34" | "35" |
        "36" | "37" | "38" | "39" | "40" | "41" => FormFactor::Desktop,
        _ => {
            // Check battery presence as laptop heuristic
            let has_battery = Path::new("/sys/class/power_supply/BAT0").exists()
                || Path::new("/sys/class/power_supply/BAT1").exists();
            if has_battery {
                FormFactor::Laptop
            } else {
                FormFactor::Desktop
            }
        }
    }
}

// ─── Power Source ──────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum PowerSource {
    Ac,
    Battery,
}

/// Detect current power source
pub fn detect_power_source() -> PowerSource {
    let ac_path = "/sys/class/power_supply/AC0/online";
    let ac_path2 = "/sys/class/power_supply/ADP1/online";

    for path in &[ac_path, ac_path2] {
        if let Ok(val) = std::fs::read_to_string(path) {
            if val.trim() == "1" {
                return PowerSource::Ac;
            }
        }
    }
    // If no AC adapter found, assume desktop = always AC
    if detect_form_factor() == FormFactor::Desktop {
        PowerSource::Ac
    } else {
        PowerSource::Battery
    }
}

// ─── Display Capabilities ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayCapabilities {
    pub outputs: Vec<OutputInfo>,
    pub vrr_available: bool,
    pub vrr_enabled: bool,
    pub hdr_available: bool,
    pub max_refresh_rate: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OutputInfo {
    pub name: String,
    pub connected: bool,
    pub width: u32,
    pub height: u32,
    pub refresh_rate: f64,
    pub vrr_capable: bool,
    pub hdr_capable: bool,
    pub edid: Option<String>,
}

/// Detect display capabilities by reading DRM/KMS sysfs
pub fn detect_displays() -> DisplayCapabilities {
    let mut outputs = Vec::new();
    let mut vrr_available = false;
    let mut hdr_available = false;
    let mut max_refresh = 0u32;

    let drm_path = "/sys/class/drm";
    if let Ok(entries) = std::fs::read_dir(drm_path) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            // Only look at connector directories (card0-HDMI-A-1, etc.)
            if !name.contains('-') || !name.starts_with("card") {
                continue;
            }

            let status_path = entry.path().join("status");
            let connected = std::fs::read_to_string(&status_path)
                .map(|s| s.trim() == "connected")
                .unwrap_or(false);

            if !connected {
                outputs.push(OutputInfo {
                    name: name.clone(),
                    connected: false,
                    width: 0, height: 0,
                    refresh_rate: 0.0,
                    vrr_capable: false,
                    hdr_capable: false,
                    edid: None,
                });
                continue;
            }

            // Get modes from the connector's modes file
            let modes_path = entry.path().join("modes");
            let mut refresh = 60.0;
            if let Ok(modes) = std::fs::read_to_string(&modes_path) {
                for line in modes.lines() {
                    // Mode format: "3840x2160" or "3840x2160-60"
                    if let Some(rate) = parse_refresh_rate(line) {
                        if rate > refresh {
                            refresh = rate;
                        }
                    }
                }
            }

            // Get resolution from modes
            let (width, height) = get_resolution(&entry.path());

            // Check VRR capability via EDID
            let edid_path = entry.path().join("edid");
            let vrr = check_vrr_capable(&entry.path());
            let hdr = check_hdr_capable(&entry.path());

            if vrr { vrr_available = true; }
            if hdr { hdr_available = true; }
            max_refresh = max_refresh.max(refresh as u32);

            outputs.push(OutputInfo {
                name,
                connected: true,
                width,
                height,
                refresh_rate: refresh,
                vrr_capable: vrr,
                hdr_capable: hdr,
                edid: None,
            });
        }
    }

    DisplayCapabilities {
        outputs,
        vrr_available,
        vrr_enabled: vrr_available,  // enable if available
        hdr_available,
        max_refresh_rate: max_refresh,
    }
}

fn parse_refresh_rate(mode: &str) -> Option<f64> {
    // Modes: "3840x2160" (60Hz implied) or "3840x2160-144.00"
    if let Some(rate_str) = mode.split('-').nth(1) {
        rate_str.parse::<f64>().ok()
    } else {
        Some(60.0)  // default 60Hz
    }
}

fn get_resolution(connector_path: &Path) -> (u32, u32) {
    // Parse from the modes file — first mode is preferred
    let modes_path = connector_path.join("modes");
    if let Ok(content) = std::fs::read_to_string(&modes_path) {
        for line in content.lines() {
            if let Some((w, h)) = parse_resolution(line) {
                return (w, h);
            }
        }
    }
    (0, 0)
}

fn parse_resolution(mode: &str) -> Option<(u32, u32)> {
    let base = mode.split('-').next().unwrap_or(mode);
    let mut parts = base.split('x');
    let w = parts.next()?.parse::<u32>().ok()?;
    let h = parts.next()?.parse::<u32>().ok()?;
    Some((w, h))
}

/// Check VRR capability via EDID or driver caps
fn check_vrr_capable(connector_path: &Path) -> bool {
    // Check kernel driver VRR cap
    let vrr_cap = connector_path.join("vrr_capable");
    if let Ok(val) = std::fs::read_to_string(&vrr_cap) {
        if val.trim() == "1" {
            return true;
        }
    }

    // Check EDID for FreeSync / AdaptiveSync
    // AMD: check amdgpu connector caps
    let dpms = connector_path.join("dpms");
    if let Ok(val) = std::fs::read_to_string(&dpms) {
        if val.trim() == "on" {
            // Only advanced connectors (DP/HDMI 2.1+) can do VRR
            let name = connector_path.file_name()
                .unwrap_or_default()
                .to_string_lossy();
            if name.contains("DP") || name.contains("HDMI") {
                return true;  // assume modern connector can VRR
            }
        }
    }

    false
}

/// Check HDR capability via EDID
fn check_hdr_capable(connector_path: &Path) -> bool {
    // Check for HDR static metadata in EDID
    // Kernel 6.14+ exposes hdr_metadata blob
    let hdr_path = connector_path.join("hdr_metadata");
    if hdr_path.exists() {
        if let Ok(meta) = std::fs::read_to_string(&hdr_path) {
            if meta.trim().len() > 10 {  // non-empty metadata exists
                return true;
            }
        }
    }

    // Fallback: check if connector supports HDR via driver
    let name = connector_path.file_name()
        .unwrap_or_default()
        .to_string_lossy();

    // HDMI 2.0+ and DP 1.4+ can support HDR
    if name.contains("HDMI") || name.contains("DP") {
        // Check for high resolution (4K+ is likely HDR-capable)
        let modes_path = connector_path.join("modes");
        if let Ok(modes) = std::fs::read_to_string(&modes_path) {
            for line in modes.lines() {
                if let Some((w, _)) = parse_resolution(line) {
                    if w >= 3840 {
                        return true;  // 4K+ panel likely HDR
                    }
                }
            }
        }
    }

    false
}

// ─── CPU Tuning ────────────────────────────────────────────────────────

/// Available CPU governors
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CpuGovernor {
    Performance,
    Ondemand,
    Conservative,
    Powersave,
    Schedutil,
}

impl std::fmt::Display for CpuGovernor {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Performance => write!(f, "performance"),
            Self::Ondemand => write!(f, "ondemand"),
            Self::Conservative => write!(f, "conservative"),
            Self::Powersave => write!(f, "powersave"),
            Self::Schedutil => write!(f, "schedutil"),
        }
    }
}

/// Set CPU governor for all cores
pub fn set_cpu_governor(governor: &str) -> Result<()> {
    let governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor";
    if !Path::new(governor_path).exists() {
        warn!("CPU frequency scaling not available on this system");
        return Ok(());
    }

    // Count available cores
    let cpu_count = std::fs::read_dir("/sys/devices/system/cpu")
        .map(|d| d.filter_map(|e| {
            let name = e.ok()?.file_name();
            let s = name.to_string_lossy();
            s.starts_with("cpu") && s[3..].parse::<u32>().is_ok()
        }).count())
        .unwrap_or(0);

    for i in 0..cpu_count {
        let path = format!("/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_governor");
        if let Err(e) = std::fs::write(&path, format!("{governor}\n")) {
            warn!("Failed to set governor on CPU {i}: {e}");
        }
    }

    info!("CPU governor set to: {governor} (over {cpu_count} cores)");
    Ok(())
}

/// Set energy performance preference (Intel only)
pub fn set_energy_preference(pref: &str) -> Result<()> {
    let path = "/sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference";
    if !Path::new(path).exists() {
        return Ok(());  // not Intel or unavailable
    }

    let cpu_count = std::fs::read_dir("/sys/devices/system/cpu")
        .map(|d| d.filter_map(|e| {
            let name = e.ok()?.file_name();
            let s = name.to_string_lossy();
            s.starts_with("cpu") && s[3..].parse::<u32>().is_ok()
        }).count())
        .unwrap_or(0);

    for i in 0..cpu_count {
        let path = format!("/sys/devices/system/cpu/cpu{i}/cpufreq/energy_performance_preference");
        let _ = std::fs::write(&path, format!("{pref}\n"));
    }

    info!("Energy preference set to: {pref}");
    Ok(())
}

/// Set TDP (power limits) on laptops via RAPL
pub fn set_tdp_limit(mode: PerformanceMode, is_battery: bool) -> Result<()> {
    // RAPL: /sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw
    let rapl_path = "/sys/class/powercap/intel-rapl:0";
    if !Path::new(rapl_path).exists() {
        return Ok(());  // no RAPL (not Intel or old hardware)
    }

    // Values: gaming=65W, balanced=35W, battery=15W
    let limit_uw = match (mode, is_battery) {
        (PerformanceMode::Gaming, _) => 65000000u64,
        (PerformanceMode::Creator, _) => 45000000,
        (PerformanceMode::Balanced, false) => 35000000,
        (PerformanceMode::Balanced, true) => 20000000,
        (PerformanceMode::Battery, _) => 15000000,
        (PerformanceMode::Idle, _) => 10000000,
    };

    let constraint_path = format!("{rapl_path}/constraint_0_power_limit_uw");
    if let Err(e) = std::fs::write(&constraint_path, format!("{limit_uw}\n")) {
        warn!("Failed to set RAPL power limit: {e}");
    }

    let long_path = format!("{rapl_path}/constraint_1_power_limit_uw");
    let _ = std::fs::write(&long_path, format!("{}\n", limit_uw * 8 / 10));

    info!("TDP limit set to {}W (mode={mode}, battery={is_battery})", limit_uw / 1000000);
    Ok(())
}

// ─── GPU Tuning ────────────────────────────────────────────────────────

/// Set GPU power level (amdgpu, nouveau)
pub fn set_gpu_power_level(level: &str) -> Result<()> {
    let drm_path = "/sys/class/drm";
    if let Ok(entries) = std::fs::read_dir(drm_path) {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.contains("card") || name.contains('-') {
                continue;
            }
            let dpm_path = entry.path().join("device/power_dpm_force_performance_level");
            if dpm_path.exists() {
                let _ = std::fs::write(&dpm_path, format!("{level}\n"));
                info!("GPU DPM level set to {level} for {name}");
            }
        }
    }
    Ok(())
}

// ─── KWin / Compositor ─────────────────────────────────────────────────

/// Apply KWin compositor settings for VRR, HDR, and performance
pub fn apply_kwin_config(displays: &DisplayCapabilities, mode: PerformanceMode) -> Result<()> {
    let config_dir = dirs_config().join("kwin");
    std::fs::create_dir_all(&config_dir)?;

    // Build KWin config
    let mut config = String::new();
    config.push_str("[Compositing]\n");
    config.push_str(&format!("Enabled={}\n", !mode.suspend_compositor()));
    config.push_str("Backend=Wayland\n");
    config.push_str(&format!("MaxRefreshRate={}\n", displays.max_refresh_rate));
    config.push_str("LatencyPolicy=ExtremelyLow\n");

    // VRR (Adaptive Sync)
    if displays.vrr_available {
        // KWin: AdaptiveSyncEnabled
        config.push_str(&format!("AdaptiveSyncEnabled={}\n",
            if displays.vrr_enabled { "true" } else { "false" }
        ));
        config.push_str("AdaptiveSyncPolicy=Automatic\n");
        info!("VRR enabled for {} display(s)", displays.outputs.len());
    } else {
        config.push_str("AdaptiveSyncEnabled=false\n");
    }

    config.push_str("\n[NightColor]\n");
    config.push_str("Active=true\n");
    config.push_str("Mode=Auto\n");

    config.push_str("\n[Wayland]\n");
    config.push_str("CompositingEnabled=true\n");
    config.push_str("InputMethod=internal\n");

    // Write KWin config
    let kwinrc_path = config_dir.join("kwinrc");
    std::fs::write(&kwinrc_path, &config)?;

    // Apply via qdbus if KWin is running
    let _ = std::process::Command::new("qdbus6")
        .args(["org.kde.KWin", "/Compositor", if mode.suspend_compositor() { "suspend" } else { "resume" }])
        .status();

    info!("KWin config applied: VRR={}, HDR={}, max_refresh={}Hz",
        displays.vrr_enabled,
        displays.hdr_available,
        displays.max_refresh_rate,
    );
    Ok(())
}

/// Configure KDE VRR/HDR settings
pub fn apply_kde_display_config(displays: &DisplayCapabilities) -> Result<()> {
    let config_dir = dirs_config().join("kdeglobals");
    let mut config = String::new();

    config.push_str("[KScreen]\n");
    for (i, output) in displays.outputs.iter().enumerate() {
        if output.connected {
            config.push_str(&format!(
                "Output_{}_VRR={}\n",
                i,
                if output.vrr_capable { "AdaptiveSync" } else { "None" }
            ));
        }
    }

    config.push_str("\n[General]\n");
    config.push_str("ColorScheme=BreezeDark\n");
    if displays.hdr_available {
        config.push_str("HDRMode=AlwaysEnabled\n");
        config.push_str(&format!("SDRBrightness=200\n"));
    }

    let _ = std::fs::create_dir_all(dirs_config());
    std::fs::write(&config_dir, &config)?;
    Ok(())
}

// ─── GameMode ──────────────────────────────────────────────────────────

fn enable_gamemode(enabled: bool) {
    if enabled {
        let _ = std::process::Command::new("systemctl")
            .args(["start", "gamemoded"])
            .status();
        info!("GameMode enabled");
    } else {
        let _ = std::process::Command::new("systemctl")
            .args(["stop", "gamemoded"])
            .status();
    }
}

// ─── Background Services ──────────────────────────────────────────────

fn manage_services(mode: PerformanceMode) {
    let stop_services = match mode {
        PerformanceMode::Gaming => vec!["bluetooth", "cups", "geoclue", "packagekit", "tracker-miner-fs"],
        PerformanceMode::Battery => vec!["geoclue", "tracker-miner-fs"],
        _ => return,  // don't mess with services in other modes
    };

    for svc in stop_services {
        let _ = std::process::Command::new("systemctl")
            .args(["stop", svc])
            .status();
    }
}

// ─── State Persistence ─────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemState {
    pub form_factor: FormFactor,
    pub mode: PerformanceMode,
    pub power_source: PowerSource,
    pub displays: DisplayCapabilities,
    pub cpu_governor: String,
    pub tdp_watts: u32,
}

impl SystemState {
    fn load() -> Result<Self> {
        let path = state_path();
        if path.exists() {
            let content = std::fs::read_to_string(&path)?;
            Ok(serde_json::from_str(&content)?)
        } else {
            Ok(SystemState {
                form_factor: detect_form_factor(),
                mode: PerformanceMode::Balanced,
                power_source: detect_power_source(),
                displays: DisplayCapabilities {
                    outputs: vec![],
                    vrr_available: false,
                    vrr_enabled: false,
                    hdr_available: false,
                    max_refresh_rate: 60,
                },
                cpu_governor: "ondemand".into(),
                tdp_watts: 35,
            })
        }
    }

    fn save(&self) -> Result<()> {
        let path = state_path();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&path, serde_json::to_string_pretty(self)?)?;
        Ok(())
    }
}

fn state_path() -> std::path::PathBuf {
    std::path::PathBuf::from("/run/solus/system-daemon/state.json")
}

fn dirs_config() -> std::path::PathBuf {
    std::env::var("XDG_CONFIG_HOME")
        .map(std::path::PathBuf::from)
        .unwrap_or_else(|_| std::path::PathBuf::from("/etc/xdg"))
}

// ─── ACPI Monitor ──────────────────────────────────────────────────────

async fn monitor_power_source(current_state: &mut SystemState) {
    let ac_path = "/sys/class/power_supply/AC0/online";
    let ac_path2 = "/sys/class/power_supply/ADP1/online";

    loop {
        time::sleep(Duration::from_secs(5)).await;

        let new_source = detect_power_source();
        if new_source != current_state.power_source {
            info!("Power source changed: {:?} -> {:?}", current_state.power_source, new_source);
            current_state.power_source = new_source;

            // Re-apply tuning with the right governor
            let governor = current_state.mode.governor_ac();
            let _ = set_cpu_governor(governor);
            let _ = set_tdp_limit(current_state.mode, new_source == PowerSource::Battery);
            let _ = current_state.save();
        }
    }
}

// ─── Main ──────────────────────────────────────────────────────────────

fn print_header(state: &SystemState) {
    println!("╔══════════════════════════════════════════════╗");
    println!("║        Solus System Daemon v0.1.0           ║");
    println!("╠══════════════════════════════════════════════╣");
    println!("║  Form Factor:    {:24} ║", state.form_factor);
    println!("║  Mode:           {:24} ║", state.mode);
    println!("║  Power:          {:24} ║",
        if state.power_source == PowerSource::Ac { "AC" } else { "Battery" });
    println!("║  CPU Governor:   {:24} ║", state.cpu_governor);
    println!("║  TDP Limit:      {:>4}W                   ║", state.tdp_watts);
    println!("║  VRR Available:  {:24} ║", state.displays.vrr_available);
    println!("║  HDR Available:  {:24} ║", state.displays.hdr_available);
    println!("║  Max Refresh:    {:>4}Hz                 ║", state.displays.max_refresh_rate);
    println!("║  GPU Power:      {:24} ║", state.mode.gpu_level());
    println!("║  GameMode:       {:24} ║", state.mode.enable_gamemode());
    println!("╚══════════════════════════════════════════════╝");
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "solus_system_daemon=info".into()),
        )
        .with_target(false)
        .compact()
        .init();

    info!("Solus System Daemon starting");

    // ── Step 1: Detect everything ──────────────────────────────────────

    let form_factor = detect_form_factor();
    let power_source = detect_power_source();
    let displays = detect_displays();

    info!("Form factor: {form_factor}");
    info!("Power source: {power_source:?}");
    info!("VRR: {}, HDR: {}, max_refresh: {}Hz",
        displays.vrr_available,
        displays.hdr_available,
        displays.max_refresh_rate,
    );

    // ── Step 2: Choose optimal mode ────────────────────────────────────

    let mode = match (form_factor.clone(), power_source) {
        (FormFactor::Laptop, PowerSource::Battery) => {
            info!("Laptop on battery → Battery mode");
            PerformanceMode::Battery
        }
        (FormFactor::Laptop, PowerSource::Ac) => {
            info!("Laptop on AC → Balanced mode");
            PerformanceMode::Balanced
        }
        _ => {
            info!("Desktop/server → Balanced mode");
            PerformanceMode::Balanced
        }
    };

    // ── Step 3: Apply tuning ───────────────────────────────────────────

    let governor = if power_source == PowerSource::Ac {
        mode.governor_ac()
    } else {
        mode.governor_battery()
    };

    set_cpu_governor(governor)?;
    set_energy_preference(mode.energy_preference())?;
    set_tdp_limit(mode, power_source == PowerSource::Battery)?;
    set_gpu_power_level(mode.gpu_level())?;
    apply_kwin_config(&displays, mode)?;
    apply_kde_display_config(&displays)?;
    enable_gamemode(mode.enable_gamemode());
    manage_services(mode);

    // ── Step 4: Save state ────────────────────────────────────────────

    let mut state = SystemState {
        form_factor,
        mode,
        power_source,
        displays,
        cpu_governor: governor.into(),
        tdp_watts: match mode {
            PerformanceMode::Gaming => 65,
            PerformanceMode::Creator => 45,
            PerformanceMode::Balanced => 35,
            PerformanceMode::Battery => 15,
            PerformanceMode::Idle => 10,
        },
    };
    state.save()?;

    print_header(&state);

    // ── Step 5: Monitor and react ─────────────────────────────────────

    info!("Entering monitoring loop (poll power every 5s)");
    tokio::select! {
        _ = monitor_power_source(&mut state) => {}
        _ = tokio::signal::ctrl_c() => {
            info!("Shutting down");
        }
    }

    Ok(())
}
