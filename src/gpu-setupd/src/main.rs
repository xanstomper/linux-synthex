// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-gpu-setupd — GPU driver installation and configuration daemon
//
// Auto-detects GPU hardware and installs appropriate drivers:
// - AMD: amdgpu (in-kernel, mesa)
// - Intel: i915 (in-kernel, mesa)
// - NVIDIA: nvidia (proprietary/akmod or nouveau)
// Handles Secure Boot key enrollment for signed modules.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::Path;
use tracing::{error, info, warn};

#[derive(Serialize, Deserialize, Debug, Clone, PartialEq)]
pub enum GpuVendor {
    Amd,
    Intel,
    Nvidia,
    Virtio,
    Unknown,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct GpuSetupState {
    pub vendor: GpuVendor,
    pub driver: String,
    pub driver_installed: bool,
    pub mesa_installed: bool,
    pub secure_boot_enrolled: bool,
    pub open_source: bool,
    pub vulkan_support: bool,
}

impl Default for GpuSetupState {
    fn default() -> Self {
        Self {
            vendor: GpuVendor::Unknown,
            driver: "unknown".into(),
            driver_installed: false,
            mesa_installed: false,
            secure_boot_enrolled: false,
            open_source: true,
            vulkan_support: false,
        }
    }
}

pub struct GpuSetupDaemon {
    state: GpuSetupState,
}

impl GpuSetupDaemon {
    pub fn new() -> Self {
        Self {
            state: GpuSetupState::default(),
        }
    }

    pub fn detect_and_setup(&mut self) -> Result<GpuSetupState> {
        info!("Detecting GPU hardware...");

        // Read from hwdaemon cache
        let vendor = self.detect_vendor()?;
        self.state.vendor = vendor.clone();

        match vendor {
            GpuVendor::Amd => self.setup_amd(),
            GpuVendor::Intel => self.setup_intel(),
            GpuVendor::Nvidia => self.setup_nvidia(),
            GpuVendor::Virtio => self.setup_virtio(),
            GpuVendor::Unknown => {
                warn!("Unknown GPU vendor — skipping driver setup");
                Ok(self.state.clone())
            }
        }
    }

    fn detect_vendor(&self) -> Result<GpuVendor> {
        // Check hwdaemon cache first
        if let Ok(json) = std::fs::read_to_string("/run/synthex/hardware.json") {
            if let Ok(profile) = serde_json::from_str::<serde_json::Value>(&json) {
                if let Some(gpus) = profile["gpus"].as_array() {
                    for gpu in gpus {
                        let vendor = gpu["vendor"].as_str().unwrap_or("");
                        return match vendor {
                            "AMD" => Ok(GpuVendor::Amd),
                            "Intel" => Ok(GpuVendor::Intel),
                            "NVIDIA" => Ok(GpuVendor::Nvidia),
                            "Google" => Ok(GpuVendor::Virtio),
                            _ => continue,
                        };
                    }
                }
            }
        }

        // Fallback: lspci
        if let Ok(output) = std::process::Command::new("lspci").output() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.contains("VGA") || line.contains("3D") {
                    if line.contains("AMD") || line.contains("ATI") || line.contains("1002") {
                        return Ok(GpuVendor::Amd);
                    }
                    if line.contains("Intel") || line.contains("8086") {
                        return Ok(GpuVendor::Intel);
                    }
                    if line.contains("NVIDIA") || line.contains("10de") {
                        return Ok(GpuVendor::Nvidia);
                    }
                }
            }
        }

        Ok(GpuVendor::Unknown)
    }

    fn setup_amd(&mut self) -> Result<GpuSetupState> {
        info!("Setting up AMD GPU...");

        // Install mesa + AMD vulkan + firmware
        let pkgs = ["mesa", "mesa-vulkan-drivers", "amd-gpu-firmware", "libva-mesa-driver"];
        for pkg in &pkgs {
            let status = std::process::Command::new("dnf")
                .args(["install", "-y", pkg])
                .status()
                .context(format!("Failed to install {pkg}"))?;
            if status.success() {
                info!("Installed: {pkg}");
            }
        }

        self.state.driver = "amdgpu".into();
        self.state.driver_installed = true;
        self.state.mesa_installed = true;
        self.state.open_source = true;
        self.state.vulkan_support = true;

        // Write AMD-specific config
        let config = "\
# AMD GPU configuration for SynthOS
# Enables AMD FSR, Adaptive Sync, and performance mode
RADV_PERFTEST=nggc
RADV_FORCE_VRS=2
AMD_VULKAN_ICD=RADV
";
        let _ = std::fs::create_dir_all("/run/synthex/gpu");
        let _ = std::fs::write("/run/synthex/gpu/amd.conf", config);

        Ok(self.state.clone())
    }

    fn setup_intel(&mut self) -> Result<GpuSetupState> {
        info!("Setting up Intel GPU...");

        let pkgs = ["mesa", "mesa-vulkan-drivers", "intel-media-driver", "libva-intel-driver"];
        for pkg in &pkgs {
            let status = std::process::Command::new("dnf")
                .args(["install", "-y", pkg])
                .status()
                .context(format!("Failed to install {pkg}"))?;
            if status.success() {
                info!("Installed: {pkg}");
            }
        }

        self.state.driver = "i915".into();
        self.state.driver_installed = true;
        self.state.mesa_installed = true;
        self.state.open_source = true;
        self.state.vulkan_support = true;

        Ok(self.state.clone())
    }

    fn setup_nvidia(&mut self) -> Result<GpuSetupState> {
        info!("Setting up NVIDIA GPU...");

        // Detect card generation for driver version selection
        let is_turing_or_newer = self.detect_nvidia_gen()?;

        let driver = if is_turing_or_newer { "nvidia" } else { "nvidia-470" };
        let pkgs = if is_turing_or_newer {
            vec!["nvidia-driver", "nvidia-driver-cuda", "nvidia-driver-NvFBCOpenGL", "nvidia-modprobe"]
        } else {
            vec!["nvidia-470-driver"]
        };

        for pkg in &pkgs {
            let status = std::process::Command::new("dnf")
                .args(["install", "-y", pkg])
                .status()
                .context(format!("Failed to install {pkg}"))?;
            if status.success() {
                info!("Installed: {pkg}");
            }
        }

        self.state.driver = driver.into();
        self.state.driver_installed = true;
        self.state.mesa_installed = true;
        self.state.open_source = false;
        self.state.vulkan_support = true;

        // Check Secure Boot
        self.state.secure_boot_enrolled = self.check_secure_boot();

        // Generate NVIDIA config
        let config = format!("\
# NVIDIA driver configuration for SynthOS
# Driver: {driver}
# Optimus: Use synthex-gpu-switch to toggle modes
# Secure Boot: {}
options nvidia NVreg_UsePageAttributeTable=1
options nvidia NVreg_InitializeSystemMemoryAllocations=0
options nvidia NVreg_DynamicPowerManagement=0x02
options nvidia NVreg_EnableGpuFirmware=1
",
            if self.state.secure_boot_enrolled { "enrolled" } else { "not enrolled" }
        );
        let _ = std::fs::create_dir_all("/run/synthex/gpu");
        let _ = std::fs::write("/run/synthex/gpu/nvidia.conf", config);

        Ok(self.state.clone())
    }

    fn setup_virtio(&mut self) -> Result<GpuSetupState> {
        info!("Setting up VirtIO GPU...");
        self.state.driver = "virtio-gpu".into();
        self.state.driver_installed = true;
        self.state.mesa_installed = true;
        self.state.open_source = true;
        self.state.vulkan_support = false;
        Ok(self.state.clone())
    }

    fn detect_nvidia_gen(&self) -> Result<bool> {
        if let Ok(output) = std::process::Command::new("lspci").args(["-nn"]).output() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.contains("NVIDIA") || line.contains("10de") {
                    // Turing = 1.8x, Ampere = 2.0x, Ada = 2.1x+
                    if line.contains("TU") || line.contains("GA") || line.contains("AD") || line.contains("GB") {
                        return Ok(true);
                    }
                }
            }
        }
        // Default to new driver
        Ok(true)
    }

    fn check_secure_boot(&self) -> bool {
        Path::new("/sys/firmware/efi").exists()
            && std::fs::read_to_string("/sys/kernel/security/lockdown")
                .map(|s| s.trim() == "confidentiality")
                .unwrap_or(false)
    }

    pub fn get_state(&self) -> &GpuSetupState {
        &self.state
    }
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "synthex_gpu_setupd=info".into()),
        )
        .init();

    info!("Synthex GPU Setup Daemon starting");
    let mut daemon = GpuSetupDaemon::new();

    match daemon.detect_and_setup() {
        Ok(state) => {
            info!(
                "GPU setup complete: {} with {}{}",
                state.driver,
                if state.open_source { "open-source" } else { "proprietary" },
                if state.vulkan_support { " + Vulkan" } else { "" },
            );
            // Write state JSON
            let _ = std::fs::create_dir_all("/run/synthex/gpu");
            if let Ok(json) = serde_json::to_string_pretty(&state) {
                let _ = std::fs::write("/run/synthex/gpu/state.json", json);
            }
        }
        Err(e) => {
            error!("GPU setup failed: {e:#}");
        }
    }

    // Daemon runs until terminated (systemd service)
    info!("synthex-gpu-setupd initialized. Watching for GPU changes...");
    loop {
        std::thread::sleep(std::time::Duration::from_secs(300));
        // Re-detect every 5 min for hotplug events
        if let Ok(new_vendor) = daemon.detect_vendor() {
            if new_vendor != daemon.state.vendor {
                info!("GPU change detected! Re-running setup...");
                let _ = daemon.detect_and_setup();
            }
        }
    }
}
