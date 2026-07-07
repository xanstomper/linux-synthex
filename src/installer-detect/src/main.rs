// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-installer-detect — SynthOS hardware auto-detection for Calamares
//
// Detects system hardware and generates JSON configuration recommendations
// that Calamares shell scripts consume during installation. This replaces
// Python-based Calamares modules with a fast, single-purpose Rust binary.
//
// Output JSON schema:
// {
//   "system": { "cpu": "...", "ram_mb": 8192, "cores": 4, "virtualized": false },
//   "firmware": { "type": "uefi", "secure_boot": false },
//   "form_factor": "laptop" | "desktop" | "tablet" | "server" | "vm",
//   "gpus": [{ "vendor": "nvidia|amd|intel", "driver": "...", "recommended": true }],
//   "disks": [{ "name": "sda", "size_gb": 500, "type": "ssd|hdd|nvme", ... }],
//   "edition_recommendation": {
//     "desktop": "plasma|gnome|hyprland",
//     "reason": "NVIDIA GPU detected — KDE Plasma recommended"
//   },
//   "filesystem_recommendation": {
//     "fs": "btrfs|ext4|xfs",
//     "compress": "zstd|none",
//     "snapshots": true|false,
//     "reason": "..."
//   },
//   "swap_recommendation": {
//     "type": "file|partition|zram|none",
//     "size_mb": 4096,
//     "reason": "..."
//   },
//   "gpu_driver": {
//     "driver": "nvidia-proprietary|nvidia-open|amdgpu|intel|nouveau",
//     "open_source": true|false,
//     "reason": "..."
//   },
//   "kernel_recommendation": {
//     "kernel": "kernel-zen|kernel-core|kernel-stable",
//     "extra_params": "nvidia-drm.modeset=1 ...",
//     "reason": "..."
//   }
// }

use anyhow::Result;
use serde::Serialize;
use std::fs;
use std::path::Path;

// ─── Hardware Detection Structures ────────────────────────────────────

#[derive(Serialize, Debug)]
struct DetectionReport {
    system: SystemInfo,
    firmware: FirmwareInfo,
    form_factor: String,
    gpus: Vec<GpuInfo>,
    disks: Vec<DiskInfo>,
    edition_recommendation: EditionRec,
    filesystem_recommendation: FsRec,
    swap_recommendation: SwapRec,
    gpu_driver: GpuDriverRec,
    kernel_recommendation: KernelRec,
}

#[derive(Serialize, Debug)]
struct SystemInfo {
    cpu_model: String,
    cpu_cores: usize,
    ram_mb: u64,
    virtualized: bool,
    hostname: String,
}

#[derive(Serialize, Debug)]
struct FirmwareInfo {
    firmware_type: String, // "uefi" | "bios" | "unknown"
    secure_boot: bool,
}

#[derive(Serialize, Debug)]
struct GpuInfo {
    vendor: String,         // "nvidia" | "amd" | "intel" | "unknown" | "apple"
    model: String,
    driver: String,         // "nvidia" | "amdgpu" | "nouveau" | "i915" | "xe" | "unknown"
    pci_id: String,
    vram_mb: u64,
    recommended: bool,
}

#[derive(Serialize, Debug)]
struct DiskInfo {
    name: String,            // "sda", "nvme0n1"
    model: String,
    size_gb: u64,
    disk_type: String,       // "ssd" | "hdd" | "nvme" | "unknown"
    rotational: bool,
    removable: bool,
}

#[derive(Serialize, Debug)]
struct EditionRec {
    desktop: String,         // "plasma" | "gnome" | "hyprland"
    reason: String,
}

#[derive(Serialize, Debug)]
struct FsRec {
    fs: String,              // "btrfs" | "ext4" | "xfs"
    compress: String,
    snapshots: bool,
    reason: String,
}

#[derive(Serialize, Debug)]
struct SwapRec {
    swap_type: String,       // "file" | "partition" | "zram" | "none"
    size_mb: u64,
    reason: String,
}

#[derive(Serialize, Debug)]
struct GpuDriverRec {
    driver: String,
    open_source: bool,
    reason: String,
}

#[derive(Serialize, Debug)]
struct KernelRec {
    kernel: String,
    extra_params: String,
    reason: String,
}

// ─── Implementations ──────────────────────────────────────────────────

impl DetectionReport {
    fn detect() -> Result<Self> {
        let system = Self::detect_system()?;
        let firmware = Self::detect_firmware()?;
        let form_factor = Self::detect_form_factor();
        let gpus = Self::detect_gpus()?;
        let disks = Self::detect_disks()?;
        let ram_mb = system.ram_mb;
        let _total_ram_gb = ram_mb / 1024;

        // Generate recommendations based on detected hardware
        let edition_recommendation = Self::recommend_edition(&gpus);
        let filesystem_recommendation = Self::recommend_filesystem(&disks, &form_factor);
        let swap_recommendation = Self::recommend_swap(ram_mb);
        let gpu_driver = Self::recommend_gpu_driver(&gpus);
        let kernel_recommendation = Self::recommend_kernel(&gpus, &form_factor);

        Ok(DetectionReport {
            system,
            firmware,
            form_factor,
            gpus,
            disks,
            edition_recommendation,
            filesystem_recommendation,
            swap_recommendation,
            gpu_driver,
            kernel_recommendation,
        })
    }

    // ── System ──────────────────────────────────────────────────────

    fn detect_system() -> Result<SystemInfo> {
        // CPU info
        let cpuinfo = fs::read_to_string("/proc/cpuinfo").unwrap_or_default();
        let cpu_model = cpuinfo.lines()
            .find(|l| l.starts_with("model name"))
            .and_then(|l| l.split(':').nth(1))
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|| "Unknown".to_string());

        let cpu_cores = cpuinfo.lines()
            .filter(|l| l.starts_with("processor"))
            .count();

        // RAM
        let meminfo = fs::read_to_string("/proc/meminfo").unwrap_or_default();
        let ram_kb = meminfo.lines()
            .find(|l| l.starts_with("MemTotal"))
            .and_then(|l| l.split_whitespace().nth(1))
            .and_then(|s| s.parse::<u64>().ok())
            .unwrap_or(2097152); // Fallback 2GB
        let ram_mb = ram_kb / 1024;

        // Virtualization detection via DMI or CPU flags
        let virtualized = Self::check_virtualized();

        let hostname = sysinfo::System::host_name().unwrap_or_else(|| "synthex-pc".to_string());

        Ok(SystemInfo {
            cpu_model,
            cpu_cores,
            ram_mb,
            virtualized,
            hostname,
        })
    }

    fn check_virtualized() -> bool {
        // Check DMI for hypervisor
        if let Ok(dmi) = fs::read_to_string("/sys/devices/virtual/dmi/id/product_name") {
            let dmi = dmi.trim().to_lowercase();
            if dmi.contains("vmware") || dmi.contains("virtualbox") || dmi.contains("qemu")
                || dmi.contains("kvm") || dmi.contains("xen") || dmi.contains("hyper-v") {
                return true;
            }
        }
        // Check CPU flags for hypervisor
        if let Ok(cpuinfo) = fs::read_to_string("/proc/cpuinfo") {
            if cpuinfo.lines().any(|l| l.contains("hypervisor")) {
                return true;
            }
        }
        false
    }

    // ── Firmware ────────────────────────────────────────────────────

    fn detect_firmware() -> Result<FirmwareInfo> {
        let firmware_type = if Path::new("/sys/firmware/efi").exists() {
            "uefi".to_string()
        } else if Path::new("/sys/firmware/efi/fw_platform_size").exists() {
            "uefi".to_string()
        } else {
            "bios".to_string()
        };

        let secure_boot = fs::read_to_string("/sys/kernel/security/securelevel")
            .ok()
            .and_then(|s| s.trim().parse::<i32>().ok())
            .map(|level| level > 0)
            .unwrap_or(false);

        Ok(FirmwareInfo { firmware_type, secure_boot })
    }

    // ── Form Factor ─────────────────────────────────────────────────

    fn detect_form_factor() -> String {
        // DMI chassis type is the most reliable indicator
        let chassis = fs::read_to_string("/sys/devices/virtual/dmi/id/chassis_type")
            .or_else(|_| fs::read_to_string("/sys/class/dmi/id/chassis_type"))
            .ok();

        if let Some(ch) = chassis {
            let ch = ch.trim();
            match ch {
                "3" | "4" | "5" | "6" | "7" | "15" | "16" => return "desktop".to_string(),
                "8" | "9" | "10" | "11" | "12" | "14" | "31" => return "laptop".to_string(),
                "13" | "30" | "23" => return "server".to_string(),
                "17" | "21" | "32" => return "tablet".to_string(),
                _ => {}
            }
        }

        // Fallback: check for battery
        let has_battery = Path::new("/sys/class/power_supply/BAT0").exists()
            || Path::new("/sys/class/power_supply/BAT1").exists();
        if has_battery {
            return "laptop".to_string();
        }

        "desktop".to_string()
    }

    // ── GPU Detection ───────────────────────────────────────────────

    fn detect_gpus() -> Result<Vec<GpuInfo>> {
        let mut gpus = Vec::new();

        // Scan /sys/class/drm for DRM devices
        if let Ok(entries) = fs::read_dir("/sys/class/drm") {
            for entry in entries.flatten() {
                let name = entry.file_name();
                let name_str = name.to_string_lossy();

                // Skip render nodes and control devices
                if !name_str.starts_with("card") || name_str.contains("-") {
                    continue;
                }

                let dev_path = entry.path();

                // Read PCI device for this GPU
                let _device_str = name_str.trim_start_matches("card");
                if let Ok(pci_path) = fs::canonicalize(dev_path.join("device")) {
                    let vendor = Self::read_pci_attr(&pci_path, "vendor");
                    let device = Self::read_pci_attr(&pci_path, "device");

                    let (vendor_name, driver) = Self::gpu_vendor_info(&vendor);

                    // Get GPU model from subsystem
                    let model = Self::read_pci_attr(&pci_path, "subsystem_device");

                    // VRAM from device info
                    let vram_mb = Self::detect_vram(&vendor);

                    // Determine if this is the primary/recommended GPU
                    let is_recommended = match &vendor_name[..] {
                        "nvidia" => true,
                        "amd" => true,
                        "intel" => true,
                        _ => false,
                    };

                    eprintln!("  GPU detected: vendor={} model={} driver={} vram={}MiB",
                        vendor_name, 
                        if model.is_empty() { "unknown" } else { &model },
                        driver,
                        vram_mb);

                    gpus.push(GpuInfo {
                        vendor: vendor_name,
                        model,
                        driver: driver.to_string(),
                        pci_id: format!("{}:{}", vendor, device),
                        vram_mb,
                        recommended: is_recommended,
                    });
                }
            }
        }

        // Fallback: parse /proc/bus/pci/devices
        if gpus.is_empty() {
            eprintln!("  No GPUs detected via DRM, trying PCI scan...");
            // Use lspci if available
            if let Ok(output) = std::process::Command::new("lspci")
                .args(["-nn"])
                .output()
            {
                let stdout = String::from_utf8_lossy(&output.stdout);
                for line in stdout.lines() {
                    // Match VGA compatible controller or 3D controller
                    let lower = line.to_lowercase();
                    if (lower.contains("vga") || lower.contains("3d controller") || lower.contains("display"))
                        && !lower.contains("bridge")
                    {
                        let vendor = if lower.contains("nvidia") || lower.contains("nvidia") {
                            "nvidia".to_string()
                        } else if lower.contains("amd") || lower.contains("advanced micro devices") || lower.contains("radeon") {
                            "amd".to_string()
                        } else if lower.contains("intel") || lower.contains("iris") {
                            "intel".to_string()
                        } else {
                            "unknown".to_string()
                        };

                        let vram_mb = Self::detect_vram(&vendor);
                        eprintln!("  GPU detected via lspci: vendor={} vram={}MiB", vendor, vram_mb);

                        gpus.push(GpuInfo {
                            driver: match vendor.as_str() {
                                "nvidia" => "nvidia".to_string(),
                                "amd" => "amdgpu".to_string(),
                                "intel" => "xe".to_string(),
                                _ => "unknown".to_string(),
                            },
                            vendor,
                            model: line.to_string(),
                            pci_id: String::new(),
                            vram_mb,
                            recommended: true,
                        });
                    }
                }
            }
        }

        if gpus.is_empty() {
            eprintln!("  No GPUs detected — falling back to unknown");
            gpus.push(GpuInfo {
                vendor: "unknown".to_string(),
                model: "Unknown GPU".to_string(),
                driver: "modesetting".to_string(),
                pci_id: String::new(),
                vram_mb: 0,
                recommended: true,
            });
        }

        Ok(gpus)
    }

    fn read_pci_attr(pci_path: &Path, attr: &str) -> String {
        let path = pci_path.join(attr);
        fs::read_to_string(&path)
            .ok()
            .map(|s| s.trim().to_string())
            .unwrap_or_default()
    }

    fn gpu_vendor_info(vendor_id: &str) -> (String, String) {
        match vendor_id {
            "0x10de" => ("nvidia".to_string(), "nvidia".to_string()),
            "0x1002" | "0x1022" => ("amd".to_string(), "amdgpu".to_string()),
            "0x8086" => ("intel".to_string(), "xe".to_string()),
            "0x106b" => ("apple".to_string(), "unknown".to_string()),
            _ => ("unknown".to_string(), "modesetting".to_string()),
        }
    }

    fn detect_vram(vendor: &str) -> u64 {
        match vendor {
            "nvidia" => {
                // Try nvidia-smi first
                if let Ok(output) = std::process::Command::new("nvidia-smi")
                    .args(["--query-gpu=memory.total", "--format=csv,noheader,nounits"])
                    .output()
                {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    if let Ok(mb) = stdout.trim().parse::<u64>() {
                        return mb;
                    }
                }
                8192 // Default if nvidia-smi unavailable
            }
            "amd" => {
                // Try /sys/class/drm/*/device/mem_info_vram_total
                if let Ok(entries) = fs::read_dir("/sys/class/drm") {
                    for entry in entries.flatten() {
                        let path = entry.path().join("device").join("mem_info_vram_total");
                        if let Ok(val) = fs::read_to_string(&path) {
                            if let Ok(bytes) = val.trim().parse::<u64>() {
                                return bytes / (1024 * 1024);
                            }
                        }
                    }
                }
                8192 // Default
            }
            "intel" => {
                // Intel integrated typically shares system RAM
                0 // Shared memory
            }
            _ => 0,
        }
    }

    // ── Disk Detection ──────────────────────────────────────────────

    fn detect_disks() -> Result<Vec<DiskInfo>> {
        let mut disks = Vec::new();

        if let Ok(entries) = fs::read_dir("/sys/block") {
            for entry in entries.flatten() {
                let name = entry.file_name();
                let name_str = name.to_string_lossy().to_string();

                // Skip virtual devices, loop, ram, zram, md, dm
                if name_str.starts_with("loop") || name_str.starts_with("ram")
                    || name_str.starts_with("zram") || name_str.starts_with("dm-")
                    || name_str.starts_with("md") || name_str.starts_with("sr")
                    || name_str.starts_with("fd")
                {
                    continue;
                }

                let dev_path = entry.path();

                // Check if removable
                let removable = fs::read_to_string(dev_path.join("removable"))
                    .ok()
                    .and_then(|s| s.trim().parse::<u8>().ok())
                    .map(|v| v == 1)
                    .unwrap_or(false);

                if removable {
                    continue; // Skip USB sticks, SD cards
                }

                // Rotational (0 = SSD, 1 = HDD)
                let rotational = fs::read_to_string(dev_path.join("queue/rotational"))
                    .ok()
                    .and_then(|s| s.trim().parse::<u8>().ok())
                    .map(|v| v == 1)
                    .unwrap_or(false);

                // Disk type
                let disk_type = if name_str.starts_with("nvme") {
                    "nvme"
                } else if rotational {
                    "hdd"
                } else {
                    "ssd"
                };

                // Size
                let size_sectors = fs::read_to_string(dev_path.join("size"))
                    .ok()
                    .and_then(|s| s.trim().parse::<u64>().ok())
                    .unwrap_or(0);
                let size_gb = size_sectors * 512 / (1024 * 1024 * 1024);

                // Model
                let model = fs::read_to_string(dev_path.join("device/model"))
                    .or_else(|_| fs::read_to_string(dev_path.join("model")))
                    .ok()
                    .map(|s| s.trim().to_string())
                    .unwrap_or_default();

                eprintln!("  Disk detected: {} type={} size={}GB model={}",
                    name_str, disk_type, size_gb,
                    if model.is_empty() { "unknown" } else { &model });

                disks.push(DiskInfo {
                    name: name_str,
                    model,
                    size_gb,
                    disk_type: disk_type.to_string(),
                    rotational,
                    removable,
                });
            }
        }

        if disks.is_empty() {
            eprintln!("  No disks detected!");
        }

        // Sort by size descending (largest first = likely system disk)
        disks.sort_by(|a, b| b.size_gb.cmp(&a.size_gb));
        Ok(disks)
    }

    // ── Recommendations ─────────────────────────────────────────────

    fn recommend_edition(gpus: &[GpuInfo]) -> EditionRec {
        for gpu in gpus {
            match gpu.vendor.as_str() {
                "nvidia" => {
                    // NVIDIA + modern GPU recommends Plasma (best Wayland support)
                    if gpu.vram_mb >= 8192 {
                        return EditionRec {
                            desktop: "plasma".to_string(),
                            reason: format!(
                                "NVIDIA GPU detected ({} MB VRAM) — KDE Plasma recommended for best Wayland + gaming experience",
                                gpu.vram_mb
                            ),
                        };
                    } else {
                        return EditionRec {
                            desktop: "plasma".to_string(),
                            reason: "NVIDIA GPU detected — KDE Plasma recommended for best NVIDIA support".to_string(),
                        };
                    }
                }
                "amd" => {
                    if gpu.vram_mb >= 12288 {
                        return EditionRec {
                            desktop: "plasma".to_string(),
                            reason: format!(
                                "AMD GPU detected with {} MB VRAM — KDE Plasma recommended for gaming + creator workflows",
                                gpu.vram_mb
                            ),
                        };
                    }
                    return EditionRec {
                        desktop: "plasma".to_string(),
                        reason: "AMD GPU detected — KDE Plasma recommended for best Wayland + gaming experience".to_string(),
                    };
                }
                "intel" => {
                    return EditionRec {
                        desktop: "plasma".to_string(),
                        reason: "Intel GPU detected — KDE Plasma recommended for Wayland efficiency".to_string(),
                    };
                }
                _ => {}
            }
        }

        EditionRec {
            desktop: "plasma".to_string(),
            reason: "Defaulting to KDE Plasma — our flagship desktop environment".to_string(),
        }
    }

    fn recommend_filesystem(disks: &[DiskInfo], form_factor: &str) -> FsRec {
        let has_ssd = disks.iter().any(|d| d.disk_type == "ssd" || d.disk_type == "nvme");
        let has_hdd = disks.iter().any(|d| d.disk_type == "hdd");
        let largest = disks.first().map(|d| d.size_gb).unwrap_or(256);

        if has_ssd && largest >= 128 {
            FsRec {
                fs: "btrfs".to_string(),
                compress: "zstd:3".to_string(),
                snapshots: true,
                reason: format!(
                    "SSD/NVMe detected (largest disk: {} GB) — BTRFS with zstd compression recommended for CoW snapshots and space efficiency",
                    largest
                ),
            }
        } else if has_ssd {
            FsRec {
                fs: "ext4".to_string(),
                compress: "none".to_string(),
                snapshots: false,
                reason: format!(
                    "SSD detected with limited space ({} GB) — ext4 recommended for minimal overhead",
                    largest
                ),
            }
        } else if has_hdd && form_factor != "laptop" {
            FsRec {
                fs: "btrfs".to_string(),
                compress: "zstd:3".to_string(),
                snapshots: true,
                reason: "HDD detected — BTRFS with compression recommended to reduce I/O and enable snapshots".to_string(),
            }
        } else if has_hdd {
            // Laptop + HDD — prioritise battery
            FsRec {
                fs: "ext4".to_string(),
                compress: "none".to_string(),
                snapshots: false,
                reason: "HDD detected on laptop — ext4 recommended for battery efficiency".to_string(),
            }
        } else {
            FsRec {
                fs: "btrfs".to_string(),
                compress: "zstd".to_string(),
                snapshots: true,
                reason: "Default recommendation — BTRFS for modern snapshot support".to_string(),
            }
        }
    }

    fn recommend_swap(ram_mb: u64) -> SwapRec {
        let ram_gb = ram_mb / 1024;

        if ram_gb <= 4 {
            SwapRec {
                swap_type: "partition".to_string(),
                size_mb: ram_mb, // Swap = RAM for low-memory systems
                reason: format!(
                    "Limited RAM ({} GB) — dedicated swap partition recommended for hibernation support",
                    ram_gb
                ),
            }
        } else if ram_gb <= 8 {
            SwapRec {
                swap_type: "zram".to_string(),
                size_mb: ram_mb / 2, // ZRAM = 50% RAM
                reason: format!(
                    "Moderate RAM ({} GB) — ZRAM swap recommended for compressed in-memory swapping",
                    ram_gb
                ),
            }
        } else if ram_gb <= 16 {
            SwapRec {
                swap_type: "zram".to_string(),
                size_mb: 4096, // ZRAM = 4 GB fixed
                reason: format!(
                    "Adequate RAM ({} GB) — 4 GB ZRAM swap for occasional pressure",
                    ram_gb
                ),
            }
        } else {
            SwapRec {
                swap_type: "zram".to_string(),
                size_mb: 2048, // Minimal ZRAM for safety
                reason: format!(
                    "Plentiful RAM ({} GB) — minimum 2 GB ZRAM swap recommended for kernel safety",
                    ram_gb
                ),
            }
        }
    }

    fn recommend_gpu_driver(gpus: &[GpuInfo]) -> GpuDriverRec {
        for gpu in gpus {
            match gpu.vendor.as_str() {
                "nvidia" => {
                    // Check if it's a modern GPU (Turing+ supports nvidia-open)
                    if gpu.vram_mb >= 6144 {
                        return GpuDriverRec {
                            driver: "nvidia-open".to_string(),
                            open_source: true,
                            reason: format!(
                                "Modern NVIDIA GPU detected ({} MB VRAM, Turing+) — nvidia-open kernel driver recommended for Wayland + GSP firmware",
                                gpu.vram_mb
                            ),
                        };
                    }
                    return GpuDriverRec {
                        driver: "nvidia-proprietary".to_string(),
                        open_source: false,
                        reason: format!(
                            "NVIDIA GPU detected ({} MB VRAM, pre-Turing) — proprietary nvidia driver recommended",
                            gpu.vram_mb
                        ),
                    };
                }
                "amd" => {
                    return GpuDriverRec {
                        driver: "amdgpu".to_string(),
                        open_source: true,
                        reason: "AMD GPU detected — open-source amdgpu kernel driver with ROCm support".to_string(),
                    };
                }
                "intel" => {
                    return GpuDriverRec {
                        driver: "xe".to_string(),
                        open_source: true,
                        reason: "Intel GPU detected — Xe kernel driver for Arc+ / i915 for legacy".to_string(),
                    };
                }
                _ => {}
            }
        }

        GpuDriverRec {
            driver: "modesetting".to_string(),
            open_source: true,
            reason: "No dedicated GPU detected — kernel modesetting driver".to_string(),
        }
    }

    fn recommend_kernel(gpus: &[GpuInfo], form_factor: &str) -> KernelRec {
        let mut params = Vec::new();
        let mut reasons = Vec::new();

        for gpu in gpus {
            match gpu.vendor.as_str() {
                "nvidia" => {
                    params.push("nvidia-drm.modeset=1".to_string());
                    params.push("nvidia.NVreg_EnableGSP_Firmware=0".to_string());
                    params.push("nvidia.NVreg_UsePageAttributeTable=1".to_string());
                    params.push("nvidia.NVreg_InitializeSystemMemoryAllocations=0".to_string());
                    params.push("nvidia.NVreg_DynamicPowerManagement=0x02".to_string());
                    if form_factor == "laptop" {
                        params.push("nvidia.NVreg_PreserveVideoMemoryAllocations=1".to_string());
                    }
                    reasons.push("NVIDIA GPU detected".to_string());
                }
                "amd" => {
                    params.push("amdgpu.pcie_gen3_support=1".to_string());
                    params.push("amdgpu.ppfeaturemask=0xffffffff".to_string());
                    reasons.push("AMD GPU detected".to_string());
                }
                "intel" => {
                    params.push("i915.enable_psr=1".to_string());
                    params.push("i915.enable_fbc=1".to_string());
                    if gpu.model.contains("Arc") || (gpu.vram_mb == 0 && form_factor == "laptop") {
                        params.push("xe.force_probe=*".to_string());
                        reasons.push("Intel discrete GPU detected".to_string());
                    }
                    reasons.push("Intel GPU detected".to_string());
                }
                _ => {}
            }
        }

        // Kernel selection — chosen based on hardware and form factor
        let kernel = if reasons.is_empty() {
            reasons.push("Standard hardware — kernel-core recommended".to_string());
            "kernel-core"
        } else if form_factor == "laptop" {
            reasons.push("Laptop detected — kernel-zen for better power management + BORE scheduler".to_string());
            "kernel-zen"
        } else if gpus.iter().any(|g| g.vendor == "nvidia" || g.vendor == "amd") {
            reasons.push("Gaming hardware detected — kernel-zen for BORE scheduler + performance optimizations".to_string());
            "kernel-zen"
        } else {
            reasons.push("Desktop hardware — kernel-core for stability".to_string());
            "kernel-core"
        };

        // Virtualization
        if gpus.iter().any(|g| g.vendor == "nvidia") {
            params.push("kvm.ignore_msrs=1".to_string());
        }

        if form_factor == "laptop" {
            params.push("acpi_osi=Linux".to_string());
        }

        // Deduplicate
        params.sort();
        params.dedup();

        KernelRec {
            kernel: kernel.to_string(),
            extra_params: params.join(" "),
            reason: reasons.join("; "),
        }
    }
}

// ─── Main ──────────────────────────────────────────────────────────────

fn main() -> Result<()> {
    eprintln!("🔍 Synthex Hardware Detector v0.1.0");
    eprintln!("{}", "═".repeat(50));

    let report = DetectionReport::detect()?;

    println!("{}", serde_json::to_string_pretty(&report)?);

    eprintln!("{}", "═".repeat(50));
    eprintln!("✅ Detection complete — JSON output above");

    Ok(())
}
