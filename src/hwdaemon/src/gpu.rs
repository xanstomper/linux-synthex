// SPDX-License-Identifier: MIT OR Apache-2.0
// GPU detection module for solus-hwdaemon

use anyhow::Result;
use crate::GpuInfo;

/// Detect GPUs by reading /sys/class/drm and /proc/driver/nvidia
pub fn detect_gpus() -> Result<Vec<GpuInfo>> {
    let mut gpus = Vec::new();

    // AMD/Intel GPUs via /sys/class/drm
    if let Ok(entries) = std::fs::read_dir("/sys/class/drm") {
        for entry in entries.flatten() {
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.contains("card") || name.contains("-") {
                continue;
            }

            let devices = std::fs::read_dir(entry.path()).ok();
            let card_path = format!("/sys/class/drm/{name}/device");
            let vendor = std::fs::read_to_string(format!("{card_path}/vendor"))
                .unwrap_or_default()
                .trim()
                .to_string();
            let device = std::fs::read_to_string(format!("{card_path}/device"))
                .unwrap_or_default()
                .trim()
                .to_string();

            if vendor.is_empty() {
                continue;
            }

            let (vendor_name, driver) = match vendor.as_str() {
                "0x1002" => ("AMD", "amdgpu"),
                "0x8086" => ("Intel", "i915"),
                "0x10de" => ("NVIDIA", "nvidia"),
                "0x1ae0" => ("Google", "virtio-gpu"),
                _ => (&vendor, "unknown"),
            };

            gpus.push(GpuInfo {
                vendor: vendor_name.to_string(),
                device: device.clone(),
                driver: driver.to_string(),
                memory_mb: 0,
                pci_slot: card_path
                    .trim_start_matches("/sys/class/drm/")
                    .to_string(),
            });
        }
    }

    // Try PCI ID-based detection via lspci
    if gpus.is_empty() {
        if let Ok(output) = std::process::Command::new("lspci")
            .args(["-nn"])
            .output()
        {
            let stdout = String::from_utf8_lossy(&output.stdout);
            for line in stdout.lines() {
                if line.contains("VGA") || line.contains("3D") || line.contains("Display") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() >= 3 {
                        let vendor = if line.contains("AMD") || line.contains("ATI") || line.contains("1002") {
                            "AMD"
                        } else if line.contains("Intel") || line.contains("8086") {
                            "Intel"
                        } else if line.contains("NVIDIA") || line.contains("10de") {
                            "NVIDIA"
                        } else {
                            "Unknown"
                        };
                        gpus.push(GpuInfo {
                            vendor: vendor.to_string(),
                            device: parts.iter().skip(2).cloned().collect::<Vec<_>>().join(" "),
                            driver: "unknown".to_string(),
                            memory_mb: 0,
                            pci_slot: parts[0].trim_end(':').to_string(),
                        });
                    }
                }
            }
        }
    }

    Ok(gpus)
}
