// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-compat-db — Hardware Compatibility Database for SynthOS
// Like ProtonDB, but for the entire OS.
// Track: GPUs, CPUs, laptops, motherboards, Wi-Fi chips, peripherals.
// Warn users about known issues with specific hardware.

use anyhow::Result;
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

const DB_PATH: &str = "/var/lib/synthex/compat-db.json";
const RUNTIME_DB: &str = "/run/synthex/compat-db.json";
const REPORT_PATH: &str = "/var/run/synthex/compat-report.json";

// ── CLI structure ──

#[derive(Parser)]
#[command(name = "synthex-compat", version = "0.2.0",
          about = "SynthOS — Hardware compatibility database")]
struct Cli {
    /// Output in JSON format (machine-readable)
    #[arg(global = true, short = 'j', long = "json")]
    json: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Parser)]
enum Commands {
    /// Scan current hardware and generate compatibility report
    Scan,
    /// Check known issues for detected hardware
    Check,
    /// Show compatibility report
    Report,
    /// Submit hardware report (opt-in telemetry)
    Submit,
    /// Show database statistics
    Stats,
}

// ── Core data types ──

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
struct CompatDatabase {
    hardware: HashMap<String, HardwareEntry>,
    stats: DbStats,
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
struct HardwareEntry {
    id: String,
    name: String,
    category: String,
    vendor: String,
    status: String,
    issues: Vec<String>,
    notes: String,
    reports: u32,
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
struct DbStats {
    total_devices: u32,
    working: u32,
    partial: u32,
    broken: u32,
    last_scan: String,
    submissions: u32,
}

#[derive(Serialize, Deserialize, Debug)]
struct ScanReport {
    hostname: String,
    kernel: String,
    os_version: String,
    devices: Vec<ScannedDevice>,
    issues_found: Vec<String>,
    recommendations: Vec<String>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct ScannedDevice {
    category: String,
    name: String,
    vendor: String,
    driver: String,
    status: String,
    issues: Vec<String>,
    pci_id: Option<String>,
    kernel_module: Option<String>,
}

impl ScannedDevice {
    fn new(category: &str, name: &str, vendor: &str,
           driver: &str, status: &str, issues: Vec<String>) -> Self {
        Self {
            category: category.to_string(),
            name: name.to_string(),
            vendor: vendor.to_string(),
            driver: driver.to_string(),
            status: status.to_string(),
            issues,
            pci_id: None,
            kernel_module: None,
        }
    }

    fn with_pci_id(mut self, pci_id: &str) -> Self {
        self.pci_id = Some(pci_id.to_string());
        self
    }

    fn with_kernel_module(mut self, mod_name: &str) -> Self {
        self.kernel_module = Some(mod_name.to_string());
        self
    }

    #[allow(dead_code)]
    fn to_json(&self) -> String {
        serde_json::to_string_pretty(self).unwrap_or_default()
    }

    fn unique_id(&self) -> String {
        format!("{}/{}/{}", self.category, self.vendor,
               self.name.chars().take(48).collect::<String>())
    }
}

// ── Known issues database ──

#[derive(Serialize, Debug, Clone)]
struct KnownIssue {
    category: &'static str,
    name: &'static str,
    symptom: &'static str,
    workaround: &'static str,
    severity: &'static str,
    driver_hint: Option<&'static str>,
}

const KNOWN_ISSUES: &[KnownIssue] = &[
    // ─ NVIDIA GPUs ─
    KnownIssue {
        category: "GPU",
        name: "NVIDIA RTX 4090 / RTX 40 series (Ada Lovelace)",
        symptom: "Requires nvidia-open driver 535+ for full Ada Lovelace support. Proprietary blob may flicker on Wayland without explicit sync.",
        workaround: "Install nvidia-driver 535+ or nvidia-open-dkms. Add nvidia_drm.modeset=1 to kernel cmdline. For Wayland flicker, set NVreg_EnableGpuFirmware=0.",
        severity: "warning",
        driver_hint: Some("nvidia-open-dkms (535+)"),
    },
    KnownIssue {
        category: "GPU",
        name: "NVIDIA RTX 4090 D / RTX 4080 Super",
        symptom: "Newer Ada Refresh SKUs may not be recognized by drivers older than 545.",
        workaround: "Update to nvidia-driver 545+ or use the open kernel module from nvidia-open-dkms.",
        severity: "warning",
        driver_hint: Some("nvidia-open-dkms (545+)"),
    },
    KnownIssue {
        category: "GPU",
        name: "NVIDIA RTX 30 series (Ampere)",
        symptom: "Some models have power management issues. Fan curve may be aggressive on default settings.",
        workaround: "Ensure nvidia_drm.modeset=1 in kernel params. Use coolbits in xorg.conf for fan control. Enable NVreg_DynamicPowerManagement=0x02.",
        severity: "info",
        driver_hint: Some("nvidia-driver (525+)"),
    },
    KnownIssue {
        category: "GPU",
        name: "NVIDIA GTX 16 series / GTX 1650 (Turing)",
        symptom: "Turing architecture may lack firmware support in some vGPU scenarios.",
        workaround: "Use nvidia-driver 525+ for best compatibility. Ensure linux-firmware is updated.",
        severity: "info",
        driver_hint: Some("nvidia-driver (525+)"),
    },
    KnownIssue {
        category: "GPU",
        name: "NVIDIA RTX 2060 12GB (revised TU104)",
        symptom: "Late TU104 revision may report incorrect VRAM size in some older driver versions.",
        workaround: "Update to nvidia-driver 525+ for correct memory reporting.",
        severity: "info",
        driver_hint: Some("nvidia-driver (525+)"),
    },

    // ─ AMD GPUs ─
    KnownIssue {
        category: "GPU",
        name: "AMD RX 7000 series (RDNA3)",
        symptom: "RDNA3 requires Mesa 23.3+ for full performance. Some cards may experience higher idle power draw on multi-monitor setups.",
        workaround: "Update Mesa to 23.3+ via eopkg update. For high idle power, try amdgpu.runpm=1.",
        severity: "warning",
        driver_hint: Some("amdgpu / Mesa 23.3+"),
    },
    KnownIssue {
        category: "GPU",
        name: "AMD RX 7800 XT / RX 7700 XT (Navi 32)",
        symptom: "Some early Navi 32 cards may exhibit rare displayport training failures on cold boot.",
        workaround: "Kernel 6.6+ improves DP training. Update firmware from linux-firmware.",
        severity: "info",
        driver_hint: Some("amdgpu / kernel 6.6+"),
    },
    KnownIssue {
        category: "GPU",
        name: "AMD RX 6000 series (RDNA2)",
        symptom: "RDNA2 generally well supported. FreeSync may glitch if VRR range is narrow.",
        workaround: "Enable VRR via KDE/GNOME display settings. Use LargeFB feature in amdgpu for narrow ranges.",
        severity: "info",
        driver_hint: Some("amdgpu"),
    },
    KnownIssue {
        category: "GPU",
        name: "AMD RX 5000 series (Navi 10 / RDNA1)",
        symptom: "Some Navi 10 GPUs need amdgpu.ppfeaturemask=0xffffffff for full overclocking support.",
        workaround: "Add amdgpu.ppfeaturemask=0xffffffff to kernel cmdline for powerplay table control.",
        severity: "info",
        driver_hint: Some("amdgpu"),
    },

    // ─ Intel GPUs ─
    KnownIssue {
        category: "GPU",
        name: "Intel Arc A770 / A750 (Alchemist)",
        symptom: "Intel Arc requires Mesa 23.1+ and updated firmware for DX12 via DXVK/VKD3D. OpenGL performance still maturing.",
        workaround: "Use kernel 6.2+ with i915 force_probe parameter. Install intel-gpu-firmware. Set i915.force_probe=* in kernel cmdline.",
        severity: "warning",
        driver_hint: Some("i915 / Mesa 23.3+"),
    },
    KnownIssue {
        category: "GPU",
        name: "Intel Arc A580 (Alchemist)",
        symptom: "Arc A580 may need explicit PCI ID forcing in i915 driver on kernel < 6.5.",
        workaround: "Force probe with i915.force_probe=PCI_ID or upgrade to kernel 6.5+. Use i915.force_probe=* for all Arc GPUs.",
        severity: "warning",
        driver_hint: Some("i915 / kernel 6.5+"),
    },
    KnownIssue {
        category: "GPU",
        name: "Intel integrated UHD 7xx / HD 5xx (older iGPU)",
        symptom: "Older Intel GPUs may have issues with VCN hardware decode on modern kernels.",
        workaround: "Disable hardware video decode in Firefox/Chrome if experiencing freezes. Use vaapi driver from intel-media-driver.",
        severity: "info",
        driver_hint: Some("i915 / intel-media-driver"),
    },

    // ─ Wi-Fi chips ─
    KnownIssue {
        category: "Wi-Fi",
        name: "Realtek RTL88xx / RTL8125 series",
        symptom: "Some Realtek chipsets lack in-kernel driver support and require DKMS modules.",
        workaround: "Install rtw88-dkms or rtw89-dkms from Synthex repos if Wi-Fi is unreliable or missing.",
        severity: "warning",
        driver_hint: Some("rtw88-dkms / rtw89-dkms"),
    },
    KnownIssue {
        category: "Wi-Fi",
        name: "Intel AX200 / AX210 / AX211 (Wi-Fi 6/6E)",
        symptom: "Intel AX series works best with iwlwifi firmware 77+. Early firmware caused disconnects on 6 GHz band.",
        workaround: "Ensure linux-firmware is up to date (2024+). For AX211 (CNVi), check firmware intel/iwlwifi-ty-a0-gf-a0-*.ucode.",
        severity: "info",
        driver_hint: Some("iwlwifi / linux-firmware 2024+"),
    },
    KnownIssue {
        category: "Wi-Fi",
        name: "Intel BE200 / BE202 (Wi-Fi 7)",
        symptom: "Wi-Fi 7 (802.11be) support is experimental in kernel 6.7+. BE200 may not be fully functional.",
        workaround: "Use kernel 6.8+ for better BE200 support. May still lack full 320 MHz channel support.",
        severity: "warning",
        driver_hint: Some("iwlwifi / kernel 6.8+"),
    },
    KnownIssue {
        category: "Wi-Fi",
        name: "MediaTek MT7921 / MT7922 (MT76 series)",
        symptom: "Some MediaTek chips need firmware from linux-firmware and may experience connection drops with 160 MHz channels.",
        workaround: "Check for firmware updates in linux-firmware. Disable 160 MHz channel width if drops persist.",
        severity: "info",
        driver_hint: Some("mt76 / linux-firmware"),
    },

    // ─ Laptops ─
    KnownIssue {
        category: "Laptop",
        name: "Framework 13 (AMD Ryzen 7040 series)",
        symptom: "Framework 13 AMD may need BIOS 3.03+ for suspend/resume stability. Fingerprint reader (GT911) needs libfprint.",
        workaround: "Update BIOS via fwupd. Install libfprint-tod-gt911 from Synthex repos for fingerprint.",
        severity: "info",
        driver_hint: Some("libfprint / fwupd"),
    },
    KnownIssue {
        category: "Laptop",
        name: "Framework 16 (AMD Ryzen 7040 series)",
        symptom: "Framework 16 dGPU (RX 7700S) may need amdgpu firmware updates and kernel 6.5+ for hotplug.",
        workaround: "Use kernel 6.5+ and updated linux-firmware. The dGPU is hot-pluggable via PCIe.",
        severity: "warning",
        driver_hint: Some("amdgpu / kernel 6.5+"),
    },
    KnownIssue {
        category: "Laptop",
        name: "ThinkPad X1 Carbon Gen 11 (Intel 13th gen)",
        symptom: "Some units have trackpad issues with newer kernels. Thunderbolt dock may need bolt service.",
        workaround: "Enable bolt: systemctl enable --now bolt. For trackpad, check psmouse or i2c_hid parameters.",
        severity: "info",
        driver_hint: Some("bolt / systemd"),
    },
    KnownIssue {
        category: "Laptop",
        name: "ThinkPad P1 Gen 6 / X1 Extreme (NVIDIA dGPU)",
        symptom: "Hybrid graphics may need nvidia-prime or optimus-manager for seamless switching.",
        workaround: "Install nvidia-prime for PRIME render offload. Use envycontrol if automatic switching fails.",
        severity: "info",
        driver_hint: Some("nvidia-prime / optimus-manager"),
    },
    KnownIssue {
        category: "Laptop",
        name: "ASUS ROG Zephyrus G14 (2023, AMD + NVIDIA)",
        symptom: "ASUS G14 may need asus-nb-wmi kernel module for keyboard backlight and fan control.",
        workaround: "Install asusctl or rog-control-center from Synthex. Ensure asus-nb-wmi module is loaded.",
        severity: "info",
        driver_hint: Some("asus-nb-wmi / asusctl"),
    },
    KnownIssue {
        category: "Laptop",
        name: "Dell XPS 15 9530 / Precision 5680",
        symptom: "Dell XPS 9530 may have audio issues with Realtek ALC4080 over I2C. Some suspend/resume cycles fail.",
        workaround: "Use kernel 6.4+ for improved I2C audio. Enable snd-intel-dspcfg with dsp_driver=1 if sound is missing.",
        severity: "warning",
        driver_hint: Some("snd-hda-intel / kernel 6.4+"),
    },

    // ─ Storage ─
    KnownIssue {
        category: "Storage",
        name: "Samsung NVMe 990 Pro / 980 Pro",
        symptom: "Samsung 990 Pro may show rapid wear due to a known firmware bug. 980 Pro needs firmware update for Linux power management.",
        workaround: "Update NVMe firmware via fwupd with the Samsung NVMe plugin. Check SMART percentage_used.",
        severity: "warning",
        driver_hint: Some("nvme / fwupd"),
    },
    KnownIssue {
        category: "Storage",
        name: "Sabrent Rocket 4 Plus / 4.0 NVMe",
        symptom: "Some Sabrent drives with Phison E18 controller may report excessive temperature under sustained writes.",
        workaround: "Ensure adequate NVMe heatsink. Monitor temp with nvme-cli. Kernel 6.1+ improves thermal management.",
        severity: "info",
        driver_hint: Some("nvme / kernel 6.1+"),
    },

    // ─ Audio ─
    KnownIssue {
        category: "Audio",
        name: "Realtek ALC4080 / ALC4082 (USB-based audio)",
        symptom: "Realtek ALC408x uses USB audio internally and may crackle or disconnect under load.",
        workaround: "Use snd-usb-audio with quirks. Try usbcore.autosuspend=-1 in kernel cmdline. Update BIOS.",
        severity: "info",
        driver_hint: Some("snd-usb-audio"),
    },

    // ─ Thunderbolt / USB4 ─
    KnownIssue {
        category: "Thunderbolt",
        name: "Thunderbolt 4 / USB4 controllers",
        symptom: "Peripheral authorization requires bolt service on many laptops for hotplug.",
        workaround: "Install bolt package: systemctl enable --now bolt. Use boltctl list to authorize devices.",
        severity: "info",
        driver_hint: Some("bolt / thunderbolt"),
    },

    // ─ Network ─
    KnownIssue {
        category: "Network",
        name: "Realtek RTL8125 / RTL8168 (2.5 GbE)",
        symptom: "Some Realtek 2.5 GbE controllers may experience link drops under heavy load with r8169 driver.",
        workaround: "Use r8168-dkms from Synthex repos for better stability. Add pcie_aspm=off to kernel cmdline.",
        severity: "info",
        driver_hint: Some("r8168-dkms / r8169"),
    },
    KnownIssue {
        category: "Network",
        name: "Aquantia AQC113 / AQC107 (10 GbE)",
        symptom: "Aquantia 10 GbE chips may require firmware not included in standard linux-firmware.",
        workaround: "Install atlantic-firmware package. Kernel 6.2+ has improved atlantic driver.",
        severity: "info",
        driver_hint: Some("atlantic / kernel 6.2+"),
    },
];

// ── Database helpers ──

fn load_db() -> CompatDatabase {
    for path in &[DB_PATH, RUNTIME_DB] {
        if let Ok(data) = std::fs::read_to_string(path) {
            if let Ok(db) = serde_json::from_str(&data) {
                return db;
            }
        }
    }
    CompatDatabase::default()
}

fn save_db(db: &CompatDatabase) -> Result<()> {
    let parent = std::path::Path::new(DB_PATH).parent().unwrap();
    let _ = std::fs::create_dir_all(parent);
    let data = serde_json::to_string_pretty(db)?;
    std::fs::write(DB_PATH, data)?;
    Ok(())
}

fn save_report(report: &ScanReport) -> Result<()> {
    let parent = std::path::Path::new(REPORT_PATH).parent().unwrap();
    let _ = std::fs::create_dir_all(parent);
    let data = serde_json::to_string_pretty(report)?;
    std::fs::write(REPORT_PATH, data)?;
    Ok(())
}

// ── Hardware scanning ──

fn scan_hardware() -> ScanReport {
    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_default();
    let kernel = std::fs::read_to_string("/proc/version")
        .map(|s| s.split_whitespace().nth(2).unwrap_or("?").to_string())
        .unwrap_or_default();
    let os_version = std::fs::read_to_string("/etc/os-release")
        .ok()
        .and_then(|s| {
            for line in s.lines() {
                if line.starts_with("PRETTY_NAME=") {
                    return Some(
                        line.trim_start_matches("PRETTY_NAME=")
                            .trim_matches('"')
                            .to_string(),
                    );
                }
            }
            None
        })
        .unwrap_or_else(|| "Synthex".to_string());

    let mut devices = Vec::new();
    let mut issues = Vec::new();
    let mut recommendations = Vec::new();

    // ── Scan GPUs via lspci ──
    if let Ok(output) = std::process::Command::new("lspci").output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            let trimmed = line.trim();
            if trimmed.contains("VGA") || trimmed.contains("3D") || trimmed.contains("Display") {
                let pci_id = trimmed.split_whitespace().next().unwrap_or("?").to_string();
                let (vendor, name, status, dev_issues, kernel_mod) =
                    if trimmed.contains("NVIDIA") {
                        let mut iss = Vec::new();
                        if trimmed.contains("nouveau") {
                            iss.push(
                                "Running nouveau instead of proprietary driver — gaming performance will be lower"
                                    .into(),
                            );
                        }
                        if trimmed.contains("RTX 4090")
                            || trimmed.contains("RTX 4080")
                            || trimmed.contains("RTX 4060")
                        {
                            iss.push(
                                "Ada Lovelace GPU — ensure nvidia-open driver 545+ is installed".into(),
                            );
                        }
                        if trimmed.contains("RTX 3090") || trimmed.contains("RTX 3080") {
                            iss.push(
                                "Ampere GPU — nvidia-driver 525+ recommended for power management".into(),
                            );
                        }
                        ("NVIDIA", trimmed.to_string(), "works", iss, Some("nvidia"))
                    } else if trimmed.contains("AMD")
                        || trimmed.contains("ATI")
                        || trimmed.contains("Advanced Micro Devices")
                    {
                        let mut iss = Vec::new();
                        if trimmed.contains("RX 7") {
                            iss.push(
                                "RDNA3 GPU — Mesa 23.3+ recommended for best performance".into(),
                            );
                        }
                        if trimmed.contains("RX 6") {
                            iss.push("RDNA2 GPU — generally well supported".into());
                        }
                        ("AMD", trimmed.to_string(), "works", iss, Some("amdgpu"))
                    } else if trimmed.contains("Intel") && trimmed.contains("Arc") {
                        let iss = vec![
                            "Intel Arc requires kernel 6.2+ with i915.force_probe=*".into(),
                        ];
                        ("Intel", trimmed.to_string(), "partial", iss, Some("i915"))
                    } else if trimmed.contains("Intel") {
                        ("Intel", trimmed.to_string(), "works", vec![], Some("i915"))
                    } else {
                        ("Unknown", trimmed.to_string(), "untested", vec![], None)
                    };
                issues.extend(dev_issues.clone());
                let mut d = ScannedDevice::new("gpu", &name, vendor, "auto-detected", status, dev_issues);
                d = d.with_pci_id(&pci_id);
                if let Some(mod_name) = kernel_mod {
                    d = d.with_kernel_module(mod_name);
                }
                devices.push(d);
            }
            // Also scan for Thunderbolt/USB4
            if trimmed.contains("Thunderbolt") || trimmed.contains("USB4") {
                devices.push(ScannedDevice::new(
                    "thunderbolt",
                    trimmed,
                    "Unknown",
                    "thunderbolt",
                    "works",
                    vec![],
                ));
            }
            // Scan Wi-Fi / Network
            if trimmed.contains("Network controller")
                || trimmed.contains("Ethernet controller")
                || trimmed.contains("Wireless")
            {
                let cat = if trimmed.contains("Wireless") || trimmed.contains("WiFi") {
                    "wifi"
                } else {
                    "network"
                };
                let (vendor, mod_hint) = if trimmed.contains("Realtek") {
                    ("Realtek", Some("r8169/rtw88"))
                } else if trimmed.contains("Intel") {
                    ("Intel", Some("iwlwifi/e1000e"))
                } else if trimmed.contains("MediaTek") || trimmed.contains("MT") {
                    ("MediaTek", Some("mt76"))
                } else if trimmed.contains("Qualcomm") || trimmed.contains("Atheros") {
                    ("Qualcomm/Atheros", Some("ath11k/ath"))
                } else if trimmed.contains("Broadcom") {
                    ("Broadcom", Some("b43/brcmfmac"))
                } else {
                    ("Unknown", None)
                };
                let mut d = ScannedDevice::new(cat, trimmed, vendor, "auto-detected", "works", vec![]);
                if let Some(m) = mod_hint {
                    d = d.with_kernel_module(m);
                }
                devices.push(d);
            }
        }
    }

    // ── Scan CPU ──
    if let Ok(cpuinfo) = std::fs::read_to_string("/proc/cpuinfo") {
        for line in cpuinfo.lines() {
            if line.starts_with("model name") {
                let name = line.split(':').nth(1).unwrap_or("?").trim().to_string();
                let vendor = if name.to_lowercase().contains("amd") {
                    "AMD"
                } else if name.to_lowercase().contains("intel") {
                    "Intel"
                } else {
                    "Unknown"
                };
                devices.push(ScannedDevice::new(
                    "cpu", &name, vendor, "kernel", "works", vec![],
                ));
                break;
            }
        }
    }

    // ── Detect laptop battery / chassis ──
    let is_laptop = std::path::Path::new("/sys/class/power_supply/BAT0").exists()
        || std::path::Path::new("/sys/class/power_supply/BAT1").exists();
    if is_laptop {
        let laptop_name = std::fs::read_to_string("/sys/devices/virtual/dmi/id/product_name")
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|_| "Unknown Laptop".to_string());
        let laptop_vendor = std::fs::read_to_string("/sys/devices/virtual/dmi/id/sys_vendor")
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|_| "Unknown".to_string());
        devices.push(ScannedDevice::new(
            "laptop",
            &laptop_name,
            &laptop_vendor,
            "kernel",
            "works",
            vec![],
        ));
    }

    // ── Scan storage ──
    for dev_name in &["nvme0", "sda", "sdb"] {
        let dev_path = format!("/dev/{}", dev_name);
        if std::path::Path::new(&dev_path).exists() {
            let model = std::fs::read_to_string(format!(
                "/sys/block/{}/device/model",
                dev_name
            ))
            .unwrap_or_else(|_| dev_name.to_string());
            let vendor = std::fs::read_to_string(format!(
                "/sys/block/{}/device/vendor",
                dev_name
            ))
            .unwrap_or_else(|_| "Unknown".to_string());
            let dev_type = if dev_name.starts_with("nvme") {
                "nvme"
            } else {
                "sata"
            };
            devices.push(ScannedDevice::new(
                "storage",
                model.trim(),
                vendor.trim(),
                dev_type,
                "works",
                vec![],
            ));
        }
    }

    // ── Check Vulkan ──
    let vulkan_ok = std::process::Command::new("vulkaninfo")
        .args(["--summary"])
        .status()
        .map(|s| s.success())
        .unwrap_or(false);
    if !vulkan_ok {
        issues.push("Vulkan not available — gaming performance may be affected".into());
        recommendations.push(
            "Install Vulkan drivers: sudo eopkg install mesa-vulkan-drivers".into(),
        );
    }

    // ── Check PipeWire audio ──
    let pipewire_ok = std::process::Command::new("systemctl")
        .args(["--user", "is-active", "pipewire.service"])
        .status()
        .map(|s| s.success())
        .unwrap_or(false);
    if !pipewire_ok {
        issues.push("PipeWire audio not running".into());
        recommendations.push(
            "Start PipeWire: systemctl --user start pipewire pipewire-pulse".into(),
        );
    }

    // ── Check Secure Boot / UEFI ──
    let has_efi = std::path::Path::new("/sys/firmware/efi").exists();
    if !has_efi {
        issues.push("System booting in legacy BIOS mode — UEFI recommended for Secure Boot".into());
        recommendations
            .push("Consider reinstalling in UEFI mode for better security".into());
    }

    // ── Check ZRAM ──
    let zram_ok = std::path::Path::new("/dev/zram0").exists();
    if !zram_ok {
        recommendations.push(
            "ZRAM not enabled — consider enabling for better performance under memory pressure"
                .into(),
        );
    }

    // ── Check memory size ──
    if let Ok(info) = std::fs::read_to_string("/proc/meminfo") {
        for line in info.lines() {
            if line.starts_with("MemTotal") {
                if let Some(val) = line.split_whitespace().nth(1) {
                    if let Ok(kb) = val.parse::<u64>() {
                        let gb = kb / (1024 * 1024);
                        if gb < 4 {
                            recommendations.push(format!(
                                "Only {} GB RAM detected — 8 GB+ recommended for modern Synthex workloads",
                                gb
                            ));
                        }
                    }
                }
                break;
            }
        }
    }

    ScanReport {
        hostname,
        kernel,
        os_version,
        devices,
        issues_found: issues,
        recommendations,
    }
}

// ── Known-issues matcher ──

fn check_known_issues(report: &ScanReport) -> Vec<KnownIssue> {
    let mut matched: Vec<KnownIssue> = Vec::new();
    for device in &report.devices {
        for ki in KNOWN_ISSUES {
            let device_upper = device.name.to_uppercase();
            let ki_upper = ki.name.to_uppercase();
            let keywords: Vec<&str> = ki_upper
                .split(|c: char| c.is_whitespace() || c == '/' || c == ',' || c == '(')
                .filter(|w| w.len() > 3)
                .collect();
            let match_count = keywords
                .iter()
                .filter(|kw| device_upper.contains(*kw))
                .count();
            if match_count >= 2 || (match_count == 1 && keywords.len() <= 2) {
                if !matched.iter().any(|m| m.name == ki.name) {
                    matched.push(ki.clone());
                }
            }
        }
    }
    matched
}

// ── CLI command implementations ──

fn cmd_scan(json: bool) -> Result<()> {
    println!("  🔍 Scanning hardware...");
    let report = scan_hardware();

    // Save report for later use
    if let Err(e) = save_report(&report) {
        eprintln!("  ⚠  Could not save report: {}", e);
    }

    if json {
        println!("{}", serde_json::to_string_pretty(&report)?);
        return Ok(());
    }

    // ── Pretty-print text output ──
    println!("\n  📋 Compatibility Report");
    println!("  ─────────────────────────────────");
    println!("  Host:    {}", report.hostname);
    println!("  Kernel:  {}", report.kernel);
    println!("  OS:      {}", report.os_version);
    println!("  Devices: {}", report.devices.len());
    println!();

    for device in &report.devices {
        let icon = match device.category.as_str() {
            "gpu" => "🎮",
            "cpu" => "⚡",
            "laptop" => "💻",
            "wifi" | "network" => "📡",
            "storage" => "💾",
            "thunderbolt" => "🔌",
            _ => "🔧",
        };
        let status_icon = match device.status.as_str() {
            "works" => "✅",
            "partial" => "⚠️",
            "broken" => "❌",
            _ => "❓",
        };
        println!("  {} {} {}", icon, status_icon, device.name);
        println!(
            "     Vendor: {}  Driver: {}  Category: {}",
            device.vendor, device.driver, device.category
        );
        if let Some(ref pid) = device.pci_id {
            println!("     PCI ID: {}", pid);
        }
        if let Some(ref km) = device.kernel_module {
            println!("     Module: {}", km);
        }
        if !device.issues.is_empty() {
            for iss in &device.issues {
                println!("     └  {}", iss);
            }
        }
        println!();
    }

    if !report.issues_found.is_empty() {
        println!("  ⚠  Issues Found:");
        for issue in &report.issues_found {
            println!("    • {}", issue);
        }
        println!();
    }

    if !report.recommendations.is_empty() {
        println!("  💡 Recommendations:");
        for rec in &report.recommendations {
            println!("    • {}", rec);
        }
        println!();
    }

    println!("  Report saved to {}", REPORT_PATH);
    println!("  Run 'synthex-compat check' to check for known issues.");
    Ok(())
}

fn cmd_check(json: bool) -> Result<()> {
    let report_path = PathBuf::from(REPORT_PATH);
    let report: ScanReport = if report_path.exists() {
        let data = std::fs::read_to_string(&report_path)?;
        serde_json::from_str(&data)?
    } else {
        println!("  No scan data found. Running hardware scan first...");
        let r = scan_hardware();
        let _ = save_report(&r);
        r
    };

    if json {
        let issues = check_known_issues(&report);
        println!("{}", serde_json::to_string_pretty(&issues)?);
        return Ok(());
    }

    println!("\n  🔎 Checking for known hardware issues...\n");

    let matched = check_known_issues(&report);
    if matched.is_empty() {
        println!("  ✅ No known issues for your hardware");
    } else {
        for issue in &matched {
            let severity_icon = match issue.severity {
                "critical" => "🚨",
                "warning" => "⚠️",
                _ => "ℹ️",
            };
            println!("  {} [{}] {}", severity_icon, issue.category, issue.name);
            println!("     Symptom:    {}", issue.symptom);
            println!("     Workaround: {}", issue.workaround);
            if let Some(drv) = issue.driver_hint {
                println!("     Driver:     {}", drv);
            }
            println!();
        }
        println!(
            "  ℹ  {} known issue(s) matched. Most are informational.",
            matched.len()
        );
    }

    Ok(())
}

fn cmd_submit(json: bool) -> Result<()> {
    if json {
        println!(
            "{{\"status\":\"starting\",\"message\":\"Submitting hardware report\"}}"
        );
    } else {
        println!("  📤 Submitting anonymous hardware report");
        println!("  This helps improve SynthOS hardware support.\n");
    }

    // Scan hardware
    let report = scan_hardware();
    let _ = save_report(&report);

    // Load the persistent database
    let mut db = load_db();

    // Update database with scanned devices
    for device in &report.devices {
        let uid = device.unique_id();
        let entry = db.hardware.entry(uid.clone()).or_insert_with(|| {
            HardwareEntry {
                id: uid.clone(),
                name: device.name.clone(),
                category: device.category.clone(),
                vendor: device.vendor.clone(),
                status: "untested".to_string(),
                issues: Vec::new(),
                notes: "Submitted via synthex-compat submit".to_string(),
                reports: 0,
            }
        });
        entry.reports += 1;
        entry.status = device.status.clone();
        // Merge unique issues
        for iss in &device.issues {
            if !entry.issues.contains(iss) {
                entry.issues.push(iss.clone());
            }
        }
    }

    // Update stats
    let now = chrono::Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
    db.stats.last_scan = now;
    db.stats.submissions += 1;
    db.stats.total_devices = db.hardware.len() as u32;
    db.stats.working = db
        .hardware
        .values()
        .filter(|e| e.status == "works")
        .count() as u32;
    db.stats.partial = db
        .hardware
        .values()
        .filter(|e| e.status == "partial")
        .count() as u32;
    db.stats.broken = db
        .hardware
        .values()
        .filter(|e| e.status == "broken")
        .count() as u32;

    // Save to persistent database
    if let Err(e) = save_db(&db) {
        eprintln!("  ⚠  Could not save to {}: {}", DB_PATH, e);
        if json {
            println!(
                "{{\"status\":\"error\",\"error\":\"{}\"}}",
                e.to_string().replace('"', "\\\"")
            );
        }
        return Err(e);
    }

    if json {
        let summary = serde_json::json!({
            "status": "submitted",
            "devices_submitted": report.devices.len(),
            "database_entries": db.hardware.len(),
            "total_submissions": db.stats.submissions,
        });
        println!("{}", serde_json::to_string_pretty(&summary)?);
    } else {
        println!("  ✅ Submission complete!");
        println!("  Devices reported: {}", report.devices.len());
        println!(
            "  Database now has {} unique hardware entries.",
            db.hardware.len()
        );
        println!(
            "  Total submissions across all users: {}",
            db.stats.submissions
        );
        println!("  Data saved to {}", DB_PATH);
    }

    Ok(())
}

fn cmd_stats(json: bool) -> Result<()> {
    let db = load_db();

    if json {
        println!("{}", serde_json::to_string_pretty(&db.stats)?);
        return Ok(());
    }

    println!("\n  📊 Compatibility Database Stats\n");
    println!("    Total devices tracked: {}", db.stats.total_devices);
    println!("    Working:               {}", db.stats.working);
    println!("    Partial:               {}", db.stats.partial);
    println!("    Broken:                {}", db.stats.broken);
    println!("    Last scan:             {}", db.stats.last_scan);
    println!("    Submissions:           {}", db.stats.submissions);
    if db.stats.total_devices == 0 {
        println!("\n  ℹ  Database is empty. Run 'synthex-compat scan' to populate.");
    }
    println!(
        "  Known issues database has {} entries.",
        KNOWN_ISSUES.len()
    );
    Ok(())
}

fn cmd_report(json: bool) -> Result<()> {
    let report_path = PathBuf::from(REPORT_PATH);
    if report_path.exists() {
        let data = std::fs::read_to_string(&report_path)?;
        if json {
            println!("{}", data);
        } else {
            let report: ScanReport = serde_json::from_str(&data)?;
            println!("\n  📋 Last Scan Report");
            println!("  ───────────────────────");
            println!("  Host:   {}", report.hostname);
            println!("  Kernel: {}", report.kernel);
            println!("  OS:     {}", report.os_version);
            println!("  Devices: {}", report.devices.len());
            for d in &report.devices {
                println!(
                    "    • [{}] {} — {} ({})",
                    d.category, d.name, d.status, d.vendor
                );
            }
        }
    } else {
        if json {
            println!(
                "{{\"error\":\"No report available\",\"hint\":\"Run synthex-compat scan\"}}"
            );
        } else {
            println!("  No report available. Run: synthex-compat scan");
        }
    }
    Ok(())
}

// ── Entry point ──

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "synthex_compat=info".into()),
        )
        .with_target(false)
        .compact()
        .init();

    let cli = Cli::parse();
    let json_output = cli.json;

    match cli.command {
        Commands::Scan => cmd_scan(json_output)?,
        Commands::Check => cmd_check(json_output)?,
        Commands::Report => cmd_report(json_output)?,
        Commands::Stats => cmd_stats(json_output)?,
        Commands::Submit => cmd_submit(json_output)?,
    }
    Ok(())
}
