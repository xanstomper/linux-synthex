// SPDX-License-Identifier: MIT OR Apache-2.0
// D-Bus service for solus-hwdaemon — exposes hardware info via org.solus.Hardware

use anyhow::Result;
use tracing::info;
use zbus::connection::Builder;
use zbus::interface;

struct HardwareInterface;

#[interface(name = "org.solus.Hardware")]
impl HardwareInterface {
    /// Returns the cached hardware profile as JSON
    #[zbus(property, name = "HardwareJson")]
    async fn hardware_json(&self) -> String {
        std::fs::read_to_string("/run/solus/hardware.json").unwrap_or_default()
    }

    /// Returns the number of CPU threads
    #[zbus(property, name = "CpuThreads")]
    async fn cpu_threads(&self) -> u32 {
        std::fs::read_to_string("/sys/devices/system/cpu/online")
            .ok()
            .and_then(|s| {
                let parts: Vec<&str> = s.trim().split('-').collect();
                parts.last().and_then(|p| p.parse::<u32>().ok())
            })
            .map(|n| n + 1)
            .unwrap_or(0)
    }

    /// Returns total memory in MB
    #[zbus(property, name = "MemoryMb")]
    async fn memory_mb(&self) -> u64 {
        let info = proc_info();
        info.total_kb / 1024
    }

    /// Re-runs hardware detection
    #[zbus(name = "Rescan")]
    async fn rescan(&self) -> String {
        match crate::HardwareProfile::detect() {
            Ok(profile) => {
                if let Ok(json) = serde_json::to_string_pretty(&profile) {
                    let _ = std::fs::write("/run/solus/hardware.json", &json);
                }
                "ok".to_string()
            }
            Err(e) => format!("error: {e}"),
        }
    }
}

fn proc_info() -> crate::MemoryInfo {
    let mut sys = sysinfo::System::new();
    sys.refresh_memory();
    crate::MemoryInfo {
        total_kb: sys.total_memory(),
        used_kb: sys.used_memory(),
        swap_total_kb: sys.total_swap(),
        swap_used_kb: sys.used_swap(),
    }
}

pub async fn run_service() -> Result<()> {
    let _connection = Builder::session()?
        .name("org.solus.Hardware")?
        .serve_at("/org/solus/Hardware", HardwareInterface)?
        .build()
        .await?;

    info!("solus-hwdaemon D-Bus service running on org.solus.Hardware");

    // Block forever
    std::future::pending::<()>().await;

    Ok(())
}
