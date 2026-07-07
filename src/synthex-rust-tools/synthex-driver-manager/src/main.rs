use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use tracing_subscriber::EnvFilter;

/// Synthex Driver Manager — auto-detect and install graphics drivers
///
/// Detects GPU hardware (NVIDIA, AMD, Intel) and installs the appropriate
/// driver stack with recommended configuration for optimal performance.
#[derive(Parser, Debug)]
#[command(name = "synthex-driver-manager", version = "0.1.0", about)]
enum Cli {
    /// Detect and display GPU hardware
    Detect,
    /// Install recommended drivers
    Install {
        /// Force specific driver: nvidia, amd, intel, mesa
        #[arg(short, long)]
        driver: Option<String>,
        /// Non-interactive mode
        #[arg(short, long)]
        yes: bool,
    },
    /// Remove drivers
    Remove {
        /// Driver to remove
        driver: String,
    },
    /// List installed drivers
    List,
    /// Check for driver updates
    Check,
    /// Switch between GPU modes (NVIDIA Optimus)
    Switch {
        /// Mode: integrated, nvidia, hybrid, compute
        mode: String,
    },
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
enum GpuVendor {
    Nvidia,
    Amd,
    Intel,
    Unknown,
}

#[derive(Debug, Serialize, Deserialize)]
struct GpuInfo {
    vendor: GpuVendor,
    model: String,
    pci_id: String,
    driver: Option<String>,
    driver_version: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct DriverState {
    gpus: Vec<GpuInfo>,
    installed_drivers: Vec<String>,
    optimus_capable: bool,
}

impl DriverState {
    fn state_path() -> PathBuf {
        dirs_config()
            .join("synthex")
            .join("driver-manager")
            .join("state.json")
    }

    fn load() -> Result<Self> {
        let path = Self::state_path();
        if path.exists() {
            let content = std::fs::read_to_string(&path)?;
            Ok(serde_json::from_str(&content)?)
        } else {
            Ok(Self {
                gpus: vec![],
                installed_drivers: vec![],
                optimus_capable: false,
            })
        }
    }

    fn save(&self) -> Result<()> {
        let path = Self::state_path();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&path, serde_json::to_string_pretty(self)?)?;
        Ok(())
    }
}

fn dirs_config() -> PathBuf {
    std::env::var("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("/etc"))
}

fn detect_gpus() -> Result<Vec<GpuInfo>> {
    let mut gpus = vec![];

    // Parse lspci for VGA/3D controllers
    let output = Command::new("lspci")
        .args(["-nnk"])
        .output()
        .context("lspci not found — is pciutils installed?")?
        .stdout;
    let text = String::from_utf8_lossy(&output);

    let mut current_gpu: Option<GpuInfo> = None;
    for line in text.lines() {
        if line.contains("VGA compatible") || line.contains("3D controller") {
            // Flush previous GPU
            if let Some(gpu) = current_gpu.take() {
                gpus.push(gpu);
            }
            let model = line
                .split(':')
                .nth(1)
                .unwrap_or("Unknown")
                .trim()
                .to_string();
            let pci_id = line
                .split_whitespace()
                .next()
                .unwrap_or("")
                .trim_end_matches(':')
                .to_string();

            let vendor = if line.to_lowercase().contains("nvidia") {
                GpuVendor::Nvidia
            } else if line.to_lowercase().contains("amd")
                || line.to_lowercase().contains("advanced micro")
            {
                GpuVendor::Amd
            } else if line.to_lowercase().contains("intel")
                || line.to_lowercase().contains("arc")
            {
                GpuVendor::Intel
            } else {
                GpuVendor::Unknown
            };

            current_gpu = Some(GpuInfo {
                vendor,
                model,
                pci_id,
                driver: None,
                driver_version: None,
            });
        } else if let Some(ref mut gpu) = current_gpu {
            if line.contains("Kernel driver in use:") {
                let driver = line
                    .split(':')
                    .nth(1)
                    .map(|s| s.trim().to_string());
                gpu.driver = driver;
            }
        }
    }
    // Flush last GPU
    if let Some(gpu) = current_gpu {
        gpus.push(gpu);
    }

    Ok(gpus)
}

fn install_nvidia_drivers(yes: bool) -> Result<()> {
    let pkgs = [
        "akmod-nvidia",
        "xorg-x11-drv-nvidia-cuda",
        "nvidia-settings",
        "nvidia-modprobe",
        "nvidia-persistenced",
        "nvidia-gpu-firmware",
    ];
    install_packages(&pkgs, yes, "NVIDIA")
}

fn install_amd_drivers(yes: bool) -> Result<()> {
    let pkgs = [
        "mesa-dri-drivers",
        "mesa-libGL",
        "mesa-va-drivers",
        "mesa-vdpau-drivers",
        "vulkan-loader",
        "vulkan-tools",
        "amdvlk",
        "amd-gpu-firmware",
        "rocm-opencl",
        "rocm-runtime",
    ];
    install_packages(&pkgs, yes, "AMD")
}

fn install_intel_drivers(yes: bool) -> Result<()> {
    let pkgs = [
        "mesa-dri-drivers",
        "mesa-libGL",
        "intel-media-driver",
        "intel-gpu-tools",
        "vulkan-loader",
        "vulkan-intel",
        "level-zero",
        "intel-gmmlib",
        "intel-vaapi-driver",
    ];
    install_packages(&pkgs, yes, "Intel")
}

fn install_mesa_drivers(yes: bool) -> Result<()> {
    let pkgs = [
        "mesa-dri-drivers",
        "mesa-libGL",
        "mesa-va-drivers",
        "vulkan-loader",
        "vulkan-tools",
    ];
    install_packages(&pkgs, yes, "Mesa")
}

fn install_packages(pkgs: &[&str], yes: bool, label: &str) -> Result<()> {
    println!("📦 Installing {label} drivers...");
    for pkg in pkgs {
        print!("  {pkg}... ");
        std::io::Write::flush(&mut std::io::stdout())?;
        let mut cmd = Command::new("dnf5");
        cmd.args(["install", pkg]);
        if yes {
            cmd.arg("-y");
        }
        match cmd.status() {
            Ok(s) if s.success() => println!("✓"),
            Ok(_) => println!("⚠ failed"),
            Err(e) => println!("⚠ error: {e}"),
        }
    }
    println!("✅ {label} driver installation complete");
    Ok(())
}

fn detect() -> Result<()> {
    let gpus = detect_gpus()?;
    if gpus.is_empty() {
        println!("❌ No GPUs detected (check lspci)");
        return Ok(());
    }

    println!("=== GPU Detection ===");
    for gpu in &gpus {
        println!("  Vendor: {:?}", gpu.vendor);
        println!("  Model:  {}", gpu.model);
        println!("  PCI:    {}", gpu.pci_id);
        println!(
            "  Driver: {}",
            gpu.driver.as_deref().unwrap_or("none")
        );
        println!();
    }

    // Save state
    let mut state = DriverState::load()?;
    state.gpus = gpus;
    state.optimus_capable = {
        let vendors: Vec<_> = state.gpus.iter().map(|g| &g.vendor).collect();
        vendors.contains(&&GpuVendor::Nvidia) && vendors.contains(&&GpuVendor::Intel)
    };
    state.save()?;

    // Recommendation
    let has_nvidia = state.gpus.iter().any(|g| g.vendor == GpuVendor::Nvidia);
    let has_amd = state.gpus.iter().any(|g| g.vendor == GpuVendor::Amd);
    let has_intel = state.gpus.iter().any(|g| g.vendor == GpuVendor::Intel);

    println!("=== Recommendation ===");
    if has_nvidia {
        println!("  → Install NVIDIA proprietary drivers: synthex-driver-manager install -d nvidia");
    }
    if has_amd {
        println!("  → Install AMD drivers: synthex-driver-manager install -d amd");
    }
    if has_intel && !has_nvidia && !has_amd {
        println!("  → Install Intel drivers: synthex-driver-manager install -d intel");
    }
    if state.optimus_capable {
        println!(
            "  → NVIDIA Optimus detected! Switch modes with: synthex-driver-manager switch <mode>"
        );
    }

    Ok(())
}

fn install(driver: Option<String>, yes: bool) -> Result<()> {
    let gpus = detect_gpus()?;

    match driver.as_deref() {
        Some("nvidia") => install_nvidia_drivers(yes)?,
        Some("amd") => install_amd_drivers(yes)?,
        Some("intel") => install_intel_drivers(yes)?,
        Some("mesa") => install_mesa_drivers(yes)?,
        None => {
            // Auto-detect
            for gpu in &gpus {
                match gpu.vendor {
                    GpuVendor::Nvidia => install_nvidia_drivers(yes)?,
                    GpuVendor::Amd => install_amd_drivers(yes)?,
                    GpuVendor::Intel => install_intel_drivers(yes)?,
                    GpuVendor::Unknown => install_mesa_drivers(yes)?,
                }
            }
        }
        Some(other) => anyhow::bail!("Unknown driver: {other}. Use: nvidia, amd, intel, mesa"),
    }

    let mut state = DriverState::load()?;
    state.installed_drivers.push(driver.unwrap_or_else(|| "auto".into()));
    state.save()?;

    println!("\n⚠ A reboot is recommended to load the new driver.");
    Ok(())
}

fn remove_driver(driver: &str) -> Result<()> {
    println!("🗑 Removing {driver} drivers...");
    let pkg = format!("akmod-{driver}");
    let mut cmd = Command::new("dnf5");
    cmd.args(["remove", "-y", &pkg]);
    let output = cmd.output().context("Failed to remove driver")?;
    if output.status.success() {
        println!("✅ {driver} drivers removed");
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Failed to remove {driver}: {stderr}");
    }
    Ok(())
}

fn list_drivers() -> Result<()> {
    let state = DriverState::load()?;

    println!("=== Installed Drivers ===");
    if state.installed_drivers.is_empty() {
        println!("  No drivers installed via synthex-driver-manager");
    } else {
        for drv in &state.installed_drivers {
            println!("  • {drv}");
        }
    }

    println!("\n=== Detected GPUs ===");
    for gpu in &state.gpus {
        println!("  {:?} — {} ({})", gpu.vendor, gpu.model, gpu.pci_id);
    }

    // Check currently loaded kernel modules
    println!("\n=== Loaded GPU Modules ===");
    let output = Command::new("lsmod")
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
        .unwrap_or_default();
    for line in output.lines().filter(|l| {
        l.contains("nvidia") || l.contains("amdgpu") || l.contains("i915") || l.contains("nouveau")
    }) {
        println!("  {line}");
    }

    Ok(())
}

fn check_updates() -> Result<()> {
    let output = Command::new("dnf5")
        .args(["check-update", "--quiet"])
        .arg("nvidia*")
        .arg("mesa*")
        .arg("amd*")
        .arg("intel*")
        .arg("vulkan*")
        .arg("akmod*")
        .output()
        .context("Failed to check driver updates")?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    if stdout.trim().is_empty() {
        println!("✅ All drivers up to date");
    } else {
        println!("📦 Driver updates available:");
        for line in stdout.lines().filter(|l| !l.is_empty()) {
            println!("  {line}");
        }
    }
    Ok(())
}

fn switch_mode(mode: &str) -> Result<()> {
    match mode {
        "integrated" | "intel" => {
            println!("🔌 Switching to integrated GPU...");
            Command::new("supergfxctl")
                .args(["-m", "Integrated"])
                .status()
                .context("supergfxctl not available — install supergfxctl for Optimus support")?;
        }
        "nvidia" => {
            println!("🔌 Switching to NVIDIA GPU...");
            Command::new("supergfxctl")
                .args(["-m", "Nvidia"])
                .status()?;
        }
        "hybrid" => {
            println!("🔌 Switching to hybrid mode...");
            Command::new("supergfxctl")
                .args(["-m", "Hybrid"])
                .status()?;
        }
        "compute" => {
            println!("🔌 Switching to compute mode...");
            Command::new("supergfxctl")
                .args(["-m", "Compute"])
                .status()?;
        }
        other => anyhow::bail!("Unknown mode: {other}. Use: integrated, nvidia, hybrid, compute"),
    }

    println!("⚠ Log out and back in for the change to take effect.");
    Ok(())
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .with_target(false)
        .compact()
        .init();

    let cli = Cli::parse();

    match cli {
        Cli::Detect => detect(),
        Cli::Install { driver, yes } => install(driver, yes),
        Cli::Remove { driver } => remove_driver(&driver),
        Cli::List => list_drivers(),
        Cli::Check => check_updates(),
        Cli::Switch { mode } => switch_mode(&mode),
    }
}
