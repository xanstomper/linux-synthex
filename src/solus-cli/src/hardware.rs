// Hardware detection module for solus-cli

use anyhow::Result;
use serde::Serialize;
use std::fmt;

#[derive(Serialize)]
pub struct HardwareInfo {
    pub cpu: String,
    pub cores: usize,
    pub threads: usize,
    pub memory_gb: f64,
    pub gpus: Vec<GpuEntry>,
    pub disks: Vec<DiskEntry>,
    pub kernel: String,
    pub hostname: String,
}

#[derive(Serialize)]
pub struct GpuEntry {
    pub vendor: String,
    pub device: String,
    pub driver: String,
}

#[derive(Serialize)]
pub struct DiskEntry {
    pub mount: String,
    pub total_gb: f64,
    pub used_gb: f64,
    pub fs: String,
}

impl fmt::Display for HardwareInfo {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "Hostname: {}", self.hostname)?;
        writeln!(f, "Kernel:   {}", self.kernel)?;
        writeln!(f, "CPU:      {} ({} cores, {} threads)", self.cpu, self.cores, self.threads)?;
        writeln!(f, "Memory:   {:.1} GB", self.memory_gb)?;
        writeln!(f, "GPUs:")?;
        for gpu in &self.gpus {
            writeln!(f, "  ├ {vendor} {device} ({driver})",
                vendor = gpu.vendor,
                device = gpu.device,
                driver = gpu.driver,
            )?;
        }
        writeln!(f, "Disks:")?;
        for disk in &self.disks {
            writeln!(f, "  ├ {mount}  {used:.1}/{total:.1} GB  ({fs})",
                mount = disk.mount,
                used = disk.used_gb,
                total = disk.total_gb,
                fs = disk.fs,
            )?;
        }
        Ok(())
    }
}

pub fn detect_hardware() -> Result<HardwareInfo> {
    let mut sys = sysinfo::System::new_all();
    sys.refresh_all();

    let cpus = sys.cpus();
    let cpu_brand = cpus.first().map(|c| c.brand()).unwrap_or("Unknown");

    let total_mem = sys.total_memory() as f64 / 1024.0 / 1024.0;

    let mut gpus = Vec::new();

    // Read from hwdaemon cache if available
    if let Ok(json) = std::fs::read_to_string("/run/solus/hardware.json") {
        if let Ok(profile) = serde_json::from_str::<serde_json::Value>(&json) {
            if let Some(gpu_arr) = profile["gpus"].as_array() {
                for gpu in gpu_arr {
                    gpus.push(GpuEntry {
                        vendor: gpu["vendor"].as_str().unwrap_or("Unknown").to_string(),
                        device: gpu["device"].as_str().unwrap_or("").to_string(),
                        driver: gpu["driver"].as_str().unwrap_or("unknown").to_string(),
                    });
                }
            }
        }
    }

    // Fallback: try lspci
    if gpus.is_empty() {
        if let Ok(out) = std::process::Command::new("lspci").output() {
            let stdout = String::from_utf8_lossy(&out.stdout);
            for line in stdout.lines() {
                if line.contains("VGA") || line.contains("3D") || line.contains("Display") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    let vendor = if line.contains("AMD") || line.contains("ATI") {
                        "AMD"
                    } else if line.contains("Intel") {
                        "Intel"
                    } else if line.contains("NVIDIA") {
                        "NVIDIA"
                    } else {
                        "Unknown"
                    };
                    let desc = parts.get(2..).map(|s| s.join(" ")).unwrap_or_default();
                    gpus.push(GpuEntry {
                        vendor: vendor.to_string(),
                        device: desc,
                        driver: "unknown".to_string(),
                    });
                }
            }
        }
    }

    let mut disks = Vec::new();
    if let Ok(entries) = std::fs::read_dir("/sys/class/block") {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with("sd") || name.starts_with("nvme") || name.starts_with("vd") {
                let size_path = format!("/sys/class/block/{name}/size");
                if let Ok(size_str) = std::fs::read_to_string(&size_path) {
                    if let Ok(sectors) = size_str.trim().parse::<u64>() {
                        let total_gb = (sectors * 512) as f64 / 1e9;
                        if total_gb > 1.0 {
                            disks.push(DiskEntry {
                                mount: format!("/dev/{name}"),
                                total_gb,
                                used_gb: 0.0,
                                fs: "block".to_string(),
                            });
                        }
                    }
                }
            }
        }
    }

    Ok(HardwareInfo {
        cpu: cpu_brand.to_string(),
        cores: sys.physical_core_count().unwrap_or(0),
        threads: cpus.len(),
        memory_gb: total_mem,
        gpus,
        disks,
        kernel: System::kernel_version().unwrap_or_default(),
        hostname: System::host_name().unwrap_or_default(),
    })
}

use sysinfo::System;
