#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexhardwaredetect
# Detects GPU, CPU, RAM, audio, network cards and writes to globalStorage
# so later modules (packages, synthexpostinstall) can pick the right drivers.

import os, re, subprocess, json

try:
    import calamares
    from calamares.utils import debug, warning
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {}
            @classmethod
            def value(cls, k, d=None): return cls._d.get(k, d)
            @classmethod
            def insert(cls, k, v): cls._d[k] = v
        @staticmethod
        def prettyStatus(m): print(f"[hwdetect] {m}")
    calamares = _FakeCal()
    def debug(m):   print(f"[hwdetect] {m}")
    def warning(m): print(f"[hwdetect] WARN: {m}")


def _run(cmd: list[str], timeout: int = 8) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def detect_gpu() -> dict:
    info = {"vendor": "unknown", "model": "", "driver": "nouveau", "packages": []}
    lspci = _run(["lspci", "-nn"])

    # NVIDIA
    m = re.search(r"(VGA|3D).*NVIDIA.*\[([^\]]+)\]", lspci, re.I)
    if m:
        info["vendor"]  = "nvidia"
        info["model"]   = m.group(2)
        # Check if proprietary driver is available
        info["driver"]  = "nvidia"
        info["packages"] = [
            "akmod-nvidia", "xorg-x11-drv-nvidia",
            "xorg-x11-drv-nvidia-cuda", "nvidia-settings",
            "synthex-nvidia-installer"
        ]
        debug(f"NVIDIA GPU detected: {info['model']}")
        return info

    # AMD
    m = re.search(r"(VGA|3D).*(AMD|ATI|Radeon).*\[([^\]]+)\]", lspci, re.I)
    if m:
        info["vendor"]  = "amd"
        info["model"]   = m.group(3)
        info["driver"]  = "amdgpu"
        info["packages"] = ["xf86-video-amdgpu", "mesa-dri-drivers",
                            "mesa-vulkan-drivers", "vulkan-tools"]
        debug(f"AMD GPU detected: {info['model']}")
        return info

    # Intel
    m = re.search(r"(VGA|3D).*Intel.*\[([^\]]+)\]", lspci, re.I)
    if m:
        info["vendor"]  = "intel"
        info["model"]   = m.group(2)
        info["driver"]  = "i915"
        info["packages"] = ["mesa-dri-drivers", "intel-media-driver",
                            "mesa-vulkan-drivers"]
        debug(f"Intel GPU detected: {info['model']}")
        return info

    warning("Could not detect GPU vendor")
    return info


def detect_cpu() -> dict:
    info = {"vendor": "unknown", "model": "", "cores": 1, "threads": 1}
    try:
        cpuinfo = open("/proc/cpuinfo").read()
        # Model name
        m = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        if m:
            info["model"] = m.group(1).strip()
        # Vendor
        if re.search(r"GenuineIntel", cpuinfo):
            info["vendor"] = "intel"
        elif re.search(r"AuthenticAMD", cpuinfo):
            info["vendor"] = "amd"
        # Cores / threads
        info["threads"] = cpuinfo.count("processor\t:")
        phys = set(re.findall(r"physical id\s*:\s*(\d+)", cpuinfo))
        siblings = re.search(r"siblings\s*:\s*(\d+)", cpuinfo)
        cores_per = re.search(r"cpu cores\s*:\s*(\d+)", cpuinfo)
        if cores_per:
            info["cores"] = int(cores_per.group(1)) * max(len(phys), 1)
        else:
            info["cores"] = info["threads"]
        debug(f"CPU: {info['model']} ({info['cores']}c/{info['threads']}t)")
    except Exception as e:
        warning(f"CPU detection failed: {e}")
    return info


def detect_ram() -> dict:
    info = {"total_mb": 0, "num_slots": 0}
    try:
        meminfo = open("/proc/meminfo").read()
        m = re.search(r"MemTotal:\s+(\d+)", meminfo)
        if m:
            info["total_mb"] = int(m.group(1)) // 1024
        debug(f"RAM: {info['total_mb']} MB")
    except Exception as e:
        warning(f"RAM detection failed: {e}")
    return info


def detect_network() -> dict:
    info = {"has_wifi": False, "has_ethernet": True, "wifi_driver": "", "packages": []}
    lspci = _run(["lspci", "-nn"])

    # WiFi
    wifi_patterns = [
        (r"Intel.*Wireless|Intel.*WiFi|Intel.*Wi-Fi", "iwlwifi", ["linux-firmware"]),
        (r"Realtek.*RTL8.*Wireless",                   "rtl8xxxu", ["realtek-firmware"]),
        (r"Qualcomm.*Atheros.*QCA",                    "ath10k",   ["linux-firmware"]),
        (r"Broadcom.*BCM",                             "wl",       ["broadcom-wl"]),
        (r"MediaTek.*MT",                              "mt76",     ["linux-firmware"]),
    ]
    for pat, drv, pkgs in wifi_patterns:
        if re.search(pat, lspci, re.I):
            info["has_wifi"]    = True
            info["wifi_driver"] = drv
            info["packages"]    = pkgs
            debug(f"WiFi: {drv}")
            break

    return info


def detect_audio() -> dict:
    info = {"has_audio": False, "driver": "snd_hda_intel", "packages": []}
    lspci = _run(["lspci", "-nn"])
    if re.search(r"Audio|Sound", lspci, re.I):
        info["has_audio"] = True
        info["packages"]  = ["pipewire", "pipewire-pulse", "pipewire-alsa",
                             "wireplumber", "pavucontrol"]
        debug("Audio device detected → PipeWire packages queued")
    return info


def detect_storage() -> dict:
    info = {"type": "hdd", "nvme": False, "ssd": False}
    # Check for NVMe
    nvme = _run(["ls", "/dev/nvme0n1"])
    if nvme:
        info["nvme"] = True
        info["type"] = "nvme"
        debug("Storage: NVMe detected")
        return info
    # Check rotational flag
    for dev in ["sda", "vda"]:
        rot_path = f"/sys/block/{dev}/queue/rotational"
        if os.path.exists(rot_path):
            rot = open(rot_path).read().strip()
            if rot == "0":
                info["ssd"]  = True
                info["type"] = "ssd"
                debug(f"Storage: SSD detected (/dev/{dev})")
            else:
                debug(f"Storage: HDD detected (/dev/{dev})")
            break
    return info


def detect_vm() -> dict:
    """Detect if running in a virtual machine."""
    info = {"is_vm": False, "hypervisor": ""}
    virt = _run(["systemd-detect-virt", "--vm"])
    if virt and virt != "none":
        info["is_vm"]      = True
        info["hypervisor"] = virt
        debug(f"VM detected: {virt}")
    return info


def pretty_name() -> str:
    return "Hardware Detection"


def run() -> None | str:
    calamares.prettyStatus("Detecting hardware…")

    hw = {
        "gpu":     detect_gpu(),
        "cpu":     detect_cpu(),
        "ram":     detect_ram(),
        "network": detect_network(),
        "audio":   detect_audio(),
        "storage": detect_storage(),
        "vm":      detect_vm(),
    }

    # ── Build driver package list ─────────────────────────────────────────────
    driver_pkgs: list[str] = []
    driver_pkgs.extend(hw["gpu"]["packages"])
    driver_pkgs.extend(hw["network"]["packages"])
    driver_pkgs.extend(hw["audio"]["packages"])
    # Deduplicate
    driver_pkgs = list(dict.fromkeys(driver_pkgs))

    debug(f"Driver packages to install: {driver_pkgs}")

    # ── Write to globalStorage ────────────────────────────────────────────────
    calamares.globalstorage.insert("synthexHW",             hw)
    calamares.globalstorage.insert("synthexGPUVendor",      hw["gpu"]["vendor"])
    calamares.globalstorage.insert("synthexGPUDriver",      hw["gpu"]["driver"])
    calamares.globalstorage.insert("synthexCPUVendor",      hw["cpu"]["vendor"])
    calamares.globalstorage.insert("synthexDriverPackages", driver_pkgs)
    calamares.globalstorage.insert("synthexIsVM",           hw["vm"]["is_vm"])
    calamares.globalstorage.insert("synthexHypervisor",     hw["vm"]["hypervisor"])

    # Recommend profile adjustments based on HW
    profile = calamares.globalstorage.value("synthexProfile") or "classic"
    ram_mb  = hw["ram"]["total_mb"]

    if ram_mb > 0 and ram_mb < 4096 and profile not in ("lite",):
        warning(f"Low RAM ({ram_mb} MB) — recommending 'lite' profile")
        calamares.globalstorage.insert("synthexLowRAMWarning", True)

    if hw["vm"]["is_vm"]:
        debug("VM detected — disabling GPU acceleration packages")
        vm_stripped = [p for p in driver_pkgs if "nvidia" not in p and "amdgpu" not in p]
        calamares.globalstorage.insert("synthexDriverPackages", vm_stripped)
        calamares.globalstorage.insert("synthexVMPackages", ["open-vm-tools", "spice-vdagent"])

    debug(f"HW detection complete: GPU={hw['gpu']['vendor']} CPU={hw['cpu']['vendor']} "
          f"RAM={ram_mb}MB VM={hw['vm']['is_vm']}")
    return None
