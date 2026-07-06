// SPDX-License-Identifier: MIT OR Apache-2.0
// SPDX-FileCopyrightText: 2026 Solus Linux Team <dev@solus.org>
//
// solus-hwdaemon — Hardware detection daemon for Solus Linux
//
// Detects system hardware (CPU, GPU, RAM, disks, network) and exposes
// results via D-Bus for use by the control center and other tools.
// This is the Rust rewrite of the original C daemon.

use anyhow::{Context, Result};
use serde::Serialize;
use std::collections::HashMap;
use sysinfo::System;
use tracing::{error, info, warn};

mod dbus;
mod gpu;

#[derive(Serialize, Debug, Clone)]
pub struct HardwareProfile {
    pub cpu: CpuInfo,
    pub gpus: Vec<GpuInfo>,
    pub memory: MemoryInfo,
    pub disks: Vec<DiskInfo>,
    pub network: Vec<NetworkInfo>,
    pub kernel: String,
    pub hostname: String,
    pub os_name: String,
    pub os_version: String,
}

#[derive(Serialize, Debug, Clone)]
pub struct CpuInfo {
    pub brand: String,
    pub vendor_id: String,
    pub cores: usize,
    pub threads: usize,
    pub frequency_mhz: u64,
    pub architecture: String,
    pub flags: Vec<String>,
}

#[derive(Serialize, Debug, Clone)]
pub struct GpuInfo {
    pub vendor: String,
    pub device: String,
    pub driver: String,
    pub memory_mb: u64,
    pub pci_slot: String,
}

#[derive(Serialize, Debug, Clone)]
pub struct MemoryInfo {
    pub total_kb: u64,
    pub used_kb: u64,
    pub swap_total_kb: u64,
    pub swap_used_kb: u64,
}

#[derive(Serialize, Debug, Clone)]
pub struct DiskInfo {
    pub device: String,
    pub mount: String,
    pub total_bytes: u64,
    pub used_bytes: u64,
    pub filesystem: String,
    pub disk_type: String,
}

#[derive(Serialize, Debug, Clone)]
pub struct NetworkInfo {
    pub interface: String,
    pub mac: String,
    pub ipv4: Vec<String>,
    pub ipv6: Vec<String>,
    pub speed_mbps: Option<u64>,
}

impl HardwareProfile {
    pub fn detect() -> Result<Self> {
        let mut sys = System::new_all();
        sys.refresh_all();

        let cpu = Self::detect_cpu(&sys)?;
        let gpus = gpu::detect_gpus()?;
        let memory = Self::detect_memory(&sys);
        let disks = Self::detect_disks(&sys);
        let network = Self::detect_network()?;

        Ok(Self {
            cpu,
            gpus,
            memory,
            disks,
            network,
            kernel: System::kernel_version().unwrap_or_default(),
            hostname: System::host_name().unwrap_or_default(),
            os_name: System::name().unwrap_or_default(),
            os_version: System::os_version().unwrap_or_default(),
        })
    }

    fn detect_cpu(sys: &System) -> Result<CpuInfo> {
        let cpus = sys.cpus();
        let first = cpus.first().context("No CPU detected")?;

        let flags_path = "/proc/cpuinfo";
        let flags = std::fs::read_to_string(flags_path)
            .unwrap_or_default()
            .lines()
            .find(|l| l.starts_with("flags"))
            .map(|l| {
                l.split(':')
                    .nth(1)
                    .unwrap_or("")
                    .split_whitespace()
                    .map(String::from)
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();

        Ok(CpuInfo {
            brand: first.brand().to_string(),
            vendor_id: first.vendor_id().to_string(),
            cores: sys.physical_core_count().unwrap_or(0),
            threads: cpus.len(),
            frequency_mhz: first.frequency(),
            architecture: std::env::consts::ARCH.to_string(),
            flags,
        })
    }

    fn detect_memory(sys: &System) -> MemoryInfo {
        MemoryInfo {
            total_kb: sys.total_memory(),
            used_kb: sys.used_memory(),
            swap_total_kb: sys.total_swap(),
            swap_used_kb: sys.used_swap(),
        }
    }

    fn detect_disks(sys: &System) -> Vec<DiskInfo> {
        use sysinfo::Disks;
        let disks = Disks::new_with_refreshed_list();
        disks
            .list()
            .iter()
            .map(|d| DiskInfo {
                device: d.name().to_string_lossy().to_string(),
                mount: d.mount_point().to_string_lossy().to_string(),
                total_bytes: d.total_space(),
                used_bytes: d.total_space() - d.available_space(),
                filesystem: String::from_utf8_lossy(d.file_system()).to_string(),
                disk_type: format!("{:?}", d.kind()),
            })
            .collect()
    }

    fn detect_network() -> Result<Vec<NetworkInfo>> {
        let mut infos = Vec::new();
        let net_path = "/sys/class/net/";

        if let Ok(entries) = std::fs::read_dir(net_path) {
            for entry in entries.flatten() {
                let iface = entry.file_name().to_string_lossy().to_string();
                if iface == "lo" {
                    continue;
                }

                let mac = std::fs::read_to_string(
                    format!("/sys/class/net/{iface}/address"),
                )
                .unwrap_or_default()
                .trim()
                .to_string();

                infos.push(NetworkInfo {
                    interface: iface,
                    mac,
                    ipv4: Vec::new(),
                    ipv6: Vec::new(),
                    speed_mbps: None,
                });
            }
        }

        Ok(infos)
    }

    pub fn to_json(&self) -> Result<String> {
        Ok(serde_json::to_string_pretty(self)?)
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "solus_hwdaemon=info".into()),
        )
        .init();

    info!("Solus Hardware Daemon starting");

    // Quick hardware detection on startup
    match HardwareProfile::detect() {
        Ok(profile) => {
            info!(
                "Detected: {} CPU cores, {} GPUs, {} RAM total",
                profile.cpu.threads,
                profile.gpus.len(),
                profile.memory.total_kb / 1024 / 1024
            );
            // Export JSON for other tools
            if let Ok(json) = profile.to_json() {
                let hwdb_path = "/run/solus/hardware.json";
                if let Some(parent) = std::path::Path::new(hwdb_path).parent() {
                    let _ = std::fs::create_dir_all(parent);
                }
                if let Err(e) = std::fs::write(hwdb_path, &json) {
                    warn!("Failed to write hardware JSON: {e}");
                }
            }
        }
        Err(e) => {
            error!("Hardware detection failed: {e:#}");
        }
    }

    // Start D-Bus service
    if let Err(e) = dbus::run_service().await {
        error!("D-Bus service exited: {e:#}");
    }

    Ok(())
}
