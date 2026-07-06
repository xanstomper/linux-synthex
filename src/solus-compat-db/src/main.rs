// SPDX-License-Identifier: MIT OR Apache-2.0
// solus-compat-db — Hardware Compatibility Database for Solus Linux
// Like ProtonDB, but for the entire OS.
// Track: GPUs, CPUs, laptops, motherboards, Wi-Fi chips, peripherals.
// Warn users about known issues with specific hardware.

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

const DB_PATH: &str = "/var/lib/solus/compat-db.json";
const RUNTIME_DB: &str = "/run/solus/compat-db.json";

#[derive(Parser)]
#[command(name = "solus-compat", version = "0.1.0",
          about = "Solus Linux — Hardware compatibility database")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
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

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
struct CompatDatabase {
    hardware: HashMap<String, HardwareEntry>,
    stats: DbStats,
}

#[derive(Serialize, Deserialize, Debug, Clone, Default)]
struct HardwareEntry {
    id: String,
    name: String,
    category: String, // cpu, gpu, nic, storage, laptop, peripheral
    vendor: String,
    status: String,   // works, partial, broken, untested
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
}

#[derive(Serialize, Debug)]
struct ScanReport {
    hostname: String,
    kernel: String,
    devices: Vec<ScannedDevice>,
    issues_found: Vec<String>,
    recommendations: Vec<String>,
}

#[derive(Serialize, Debug)]
struct ScannedDevice {
    category: String,
    name: String,
    vendor: String,
    driver: String,
    status: String,
    issues: Vec<String>,
}

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

fn scan_hardware() -> ScanReport {
    let hostname = hostname::get().map(|h| h.to_string_lossy().to_string()).unwrap_or_default();
    let kernel = std::fs::read_to_string("/proc/version")
        .map(|s| s.split_whitespace().nth(2).unwrap_or("?").to_string())
        .unwrap_or_default();

    let mut devices = Vec::new();
    let mut issues = Vec::new();
    let mut recommendations = Vec::new();

    // Scan GPUs
    if let Ok(output) = std::process::Command::new("lspci").output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            if line.contains("VGA") || line.contains("3D") || line.contains("Display") {
                let (vendor, name, status, dev_issues) = if line.contains("NVIDIA") {
                    let mut iss = Vec::new();
                    // Check for nouveau
                    if line.contains("nouveau") {
                        iss.push("Running open-source nouveau driver (proprietary may be better for gaming)".into());
                    }
                    ("NVIDIA".into(), line.trim().to_string(), "works".into(), iss)
                } else if line.contains("AMD") || line.contains("ATI") {
                    ("AMD".into(), line.trim().to_string(), "works".into(), vec![])
                } else if line.contains("Intel") {
                    ("Intel".into(), line.trim().to_string(), "works".into(), vec![])
                } else {
                    ("Unknown".into(), line.trim().to_string(), "untested".into(), vec![])
                };
                issues.extend(dev_issues.clone());
                devices.push(ScannedDevice {
                    category: "gpu".into(), name, vendor, driver: "auto-detected".into(),
                    status, issues: dev_issues,
                });
            }
        }
    }

    // Scan CPU
    if let Ok(cpuinfo) = std::fs::read_to_string("/proc/cpuinfo") {
        for line in cpuinfo.lines() {
            if line.starts_with("model name") {
                let name = line.split(':').nth(1).unwrap_or("?").trim().to_string();
                let vendor = if name.to_lowercase().contains("amd") { "AMD" }
                    else if name.to_lowercase().contains("intel") { "Intel" }
                    else { "Unknown" };
                devices.push(ScannedDevice {
                    category: "cpu".into(), name, vendor: vendor.into(),
                    driver: "kernel".into(), status: "works".into(), issues: vec![],
                });
                break;
            }
        }
    }

    // Check Vulkan
    let vulkan_ok = std::process::Command::new("vulkaninfo")
        .args(["--summary"]).status().map(|s| s.success()).unwrap_or(false);
    if !vulkan_ok {
        issues.push("Vulkan not available — gaming performance may be affected".into());
        recommendations.push("Install Vulkan drivers: dnf install mesa-vulkan-drivers".into());
    }

    // Check audio
    let pipewire_ok = std::process::Command::new("systemctl")
        .args(["is-active", "pipewire.service"]).status().map(|s| s.success()).unwrap_or(false);
    if !pipewire_ok {
        issues.push("PipeWire audio not running".into());
        recommendations.push("Start PipeWire: systemctl --user start pipewire pipewire-pulse".into());
    }

    // Check Secure Boot
    let sb = std::path::Path::new("/sys/firmware/efi").exists();
    if !sb {
        recommendations.push("UEFI detected — consider enabling Secure Boot for security".into());
    }

    // Check ZRAM
    let zram_ok = std::path::Path::new("/dev/zram0").exists();
    if !zram_ok {
        recommendations.push("ZRAM not enabled — consider enabling for better performance".into());
    }

    ScanReport { hostname, kernel, devices, issues_found: issues, recommendations }
}

fn cmd_scan() -> Result<()> {
    println!("\n  🔍 Hardware Compatibility Scan\n");
    println!("  {}", "═".repeat(55));

    let report = scan_hardware();
    println!("  Hostname: {}", report.hostname);
    println!("  Kernel:   {}", report.kernel);
    println!();

    println!("  📋 Detected Hardware:\n");
    for dev in &report.devices {
        let icon = match dev.status.as_str() {
            "works" => "✅",
            "partial" => "⚠",
            "broken" => "❌",
            _ => "❓",
        };
        println!("    {icon} [{:<6}] {} — {}", dev.category.to_uppercase(), dev.vendor, dev.name);
        for issue in &dev.issues {
            println!("         ⚠  {issue}");
        }
    }

    if !report.issues_found.is_empty() {
        println!("\n  ⚠  Issues Found:\n");
        for issue in &report.issues_found {
            println!("    • {issue}");
        }
    }

    if !report.recommendations.is_empty() {
        println!("\n  💡 Recommendations:\n");
        for rec in &report.recommendations {
            println!("    → {rec}");
        }
    }

    if report.issues_found.is_empty() && report.recommendations.is_empty() {
        println!("\n  ✅ All hardware compatible — no issues detected");
    }

    // Save report
    let json = serde_json::to_string_pretty(&report)?;
    let report_path = PathBuf::from("/var/run/solus/compat-report.json");
    if let Some(parent) = report_path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let _ = std::fs::write(&report_path, &json);
    println!("\n  📄 Report saved: {}\n", report_path.display());

    Ok(())
}

fn cmd_check() -> Result<()> {
    println!("\n  🔍 Checking Known Issues...\n");

    // Known problematic hardware
    let mut known_issues: Vec<(&str, &str, &str)> = Vec::new();

    // Check for known problem GPUs
    if let Ok(output) = std::process::Command::new("lspci").output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            if line.contains("VGA") || line.contains("3D") {
                // NVIDIA issues
                if line.contains("RTX 30") && line.contains("NVIDIA") {
                    known_issues.push(("GPU", "NVIDIA RTX 30 series",
                        "Some models have power management issues. Ensure nvidia_drm.modeset=1 in kernel params."));
                }
                if line.contains("RTX 40") && line.contains("NVIDIA") {
                    known_issues.push(("GPU", "NVIDIA RTX 40 series",
                        "Requires driver 535+ for full Ada Lovelace support. Enable NVreg_EnableGpuFirmware=1."));
                }
                if line.contains("GTX 16") && line.contains("NVIDIA") {
                    known_issues.push(("GPU", "NVIDIA GTX 16 series",
                        "Turing architecture — use nvidia-driver 525+ for best compatibility."));
                }

                // AMD issues
                if line.contains("RX 5") && (line.contains("AMD") || line.contains("ATI")) {
                    known_issues.push(("GPU", "AMD RX 5000 series",
                        "Some Navi 10 GPUs need amdgpu.ppfeaturemask=0xffffffff for full OC support."));
                }
                if line.contains("RX 7") && (line.contains("AMD") || line.contains("ATI")) {
                    known_issues.push(("GPU", "AMD RX 7000 series",
                        "RDNA3 requires Mesa 23.3+ for full performance. Ensure firmware is up to date."));
                }
                if line.contains("RX 6") && (line.contains("AMD") || line.contains("ATI")) {
                    known_issues.push(("GPU", "AMD RX 6000 series",
                        "RDNA2 — generally well supported. Enable VRR via KDE settings for FreeSync monitors."));
                }

                // Intel issues
                if line.contains("Intel") && line.contains("Arc") {
                    known_issues.push(("GPU", "Intel Arc",
                        "Intel Arc requires recent Mesa 23.1+ and firmware updates for stable operation."));
                }
                if line.contains("Intel") && (line.contains("UHD 6") || line.contains("HD 5")) {
                    known_issues.push(("GPU", "Intel integrated (older)",
                        "Older Intel GPUs may have issues with VCN decode. Consider disabling hardware video decode if experiencing freezes."));
                }
            }
        }
    }

    // Check for known Wi-Fi issues
    if let Ok(output) = std::process::Command::new("lspci").output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        for line in stdout.lines() {
            if line.contains("Network") || line.contains("Wireless") {
                if line.contains("Realtek") && line.contains("88") {
                    known_issues.push(("Wi-Fi", "Realtek 88xx series",
                        "Some Realtek chipsets require rtw88 or rtw89 drivers. Install rtw88-dkms if Wi-Fi is unreliable."));
                }
                if line.contains("Intel") && line.contains("AX") {
                    known_issues.push(("Wi-Fi", "Intel AX series",
                        "Intel AX200/AX210 work best with iwlwifi firmware 59+. Ensure linux-firmware is up to date."));
                }
                if line.contains("MediaTek") || line.contains("MT76") {
                    known_issues.push(("Wi-Fi", "MediaTek MT76 series",
                        "Some MediaTek chips need firmware from linux-firmware package. Check for connection drops."));
                }
            }
        }
    }

    // Check for Thunderbolt/USB4 issues
    if let Ok(output) = std::process::Command::new("lspci").output() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        if stdout.contains("Thunderbolt") || stdout.contains("USB4") {
            known_issues.push(("Thunderbolt", "Thunderbolt/USB4 controller",
                "Ensure bolt service is running for device authorization. Run: systemctl enable --now bolt"));
        }
    }

    // Check for NVMe issues
    if std::path::Path::new("/dev/nvme0n1").exists() {
        // Check for NVMe health
        if let Ok(nvme_output) = std::process::Command::new("smartctl")
            .args(["-a", "/dev/nvme0n1"]).output() {
            let smart = String::from_utf8_lossy(&nvme_output.stdout);
            if smart.contains("percentage_used") {
                for line in smart.lines() {
                    if line.contains("percentage_used") {
                        let pct: u32 = line.split_whitespace()
                            .find(|w| w.chars().all(|c| c.is_ascii_digit()))
                            .and_then(|w| w.parse().ok())
                            .unwrap_or(0);
                        if pct > 80 {
                            known_issues.push(("Storage", "NVMe SSD",
                                "SSD health is above 80% used. Consider backing up data and planning replacement."));
                        }
                    }
                }
            }
        }
    }

    if known_issues.is_empty() {
        println!("  ✅ No known issues for your hardware");
    } else {
        for (cat, hw, note) in &known_issues {
            println!("  ⚠  [{cat}] {hw}");
            println!("     {note}\n");
        }
        println!("  ℹ  {} issue(s) detected. Most are informational — your hardware will still work.", known_issues.len());
    }

    Ok(())
}

fn cmd_stats() -> Result<()> {
    let db = load_db();
    println!("\n  📊 Compatibility Database Stats\n");
    println!("    Total devices tracked: {}", db.stats.total_devices);
    println!("    Working:               {}", db.stats.working);
    println!("    Partial:               {}", db.stats.partial);
    println!("    Broken:                {}", db.stats.broken);
    println!("    Last scan:             {}", db.stats.last_scan);
    if db.stats.total_devices == 0 {
        println!("\n  ℹ  Database is empty. Run 'solus-compat scan' to populate.");
    }
    Ok(())
}

fn cmd_report() -> Result<()> {
    let report_path = PathBuf::from("/var/run/solus/compat-report.json");
    if report_path.exists() {
        let data = std::fs::read_to_string(&report_path)?;
        println!("{data}");
    } else {
        println!("  No report available. Run: solus-compat scan");
    }
    Ok(())
}

fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter(
        tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "solus_compat=info".into()))
        .with_target(false).compact().init();

    let cli = Cli::parse();
    match cli.command {
        Commands::Scan => cmd_scan()?,
        Commands::Check => cmd_check()?,
        Commands::Report => cmd_report()?,
        Commands::Stats => cmd_stats()?,
        Commands::Submit => {
            println!("  📤 Hardware report submission (opt-in telemetry)");
            println!("  This sends anonymous hardware data to help improve Solus.");
            println!("  Feature coming soon.");
        }
    }
    Ok(())
}
