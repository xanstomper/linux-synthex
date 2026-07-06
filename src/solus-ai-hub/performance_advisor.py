#!/usr/bin/env python3
"""solus AI Performance Advisor — analyze hardware and recommend tuning.

Reads the hw profile, sizes ZRAM, recommends a kernel variant, governor,
graphics settings, and game-specific tweaks.

Usage:
    solus-ai-assistant performance
    solus-ai-assistant performance --json
    solus-ai-assistant performance --apply     # writes sysctl + zram config
"""
import json
import os
import re
import subprocess
import sys

PROFILE = "/var/run/solus-hw-profile.json"


def load_profile():
    if not os.path.exists(PROFILE):
        return None
    try:
        with open(PROFILE) as fh:
            return json.load(fh)
    except Exception:
        return None


def cpu_supports_v4():
    try:
        with open("/proc/cpuinfo") as fh:
            data = fh.read()
        return "avx512" in data.lower()
    except Exception:
        return False


def ram_kb():
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    return int(line.split()[1])
    except Exception:
        pass
    return 0


def recommend(profile):
    ram = ram_kb()
    ram_gb = ram / 1048576

    kernel = "v3"
    if cpu_supports_v4():
        kernel = "v4"

    zram_size = "ram"  # full RAM by default
    if ram_gb >= 32:
        zram_size = "ram / 2"
    elif ram_gb >= 16:
        zram_size = "ram * 0.75"

    vendor = (profile or {}).get("gpu", {}).get("vendor", "unknown").upper()
    gpu_tips = {
        "NVIDIA": ["Enable NVREG_PreserveVideoMemoryAllocations=1",
                   "Set __GL_SHADER_DISK_CACHE=1",
                   "Use nvidia-prime for hybrid laptops"],
        "AMD": ["Set RADV_PERFTEST=gpl for faster pipeline",
                "Enable mesa shader cache (MESA_SHADER_CACHE_DIR)",
                "Use power_dpm_force_performance_level=high for gaming"],
        "INTEL": ["Set ANV debug options only if needed",
                  "Use intel-media-driver for VAAPI"],
    }

    return {
        "kernel_variant": kernel,
        "zram_size": zram_size,
        "ram_gb": round(ram_gb, 1),
        "cpu_governor_gaming": "performance",
        "cpu_governor_daily": "schedutil",
        "gpu_tips": gpu_tips.get(vendor, ["Install correct GPU drivers first"]),
        "game_tweaks": [
            "WINEESYNC=1 WINEFSYNC=1 (kernel supports futex2)",
            "DXVK_STATE_CACHE=1 for shader caching",
            "MANGOHUD=1 for overlay monitoring",
            "gamemoderun for CPU/IO priority",
        ],
        "sysctl": {
            "vm.swappiness": 10,
            "vm.max_map_count": 16777216,
            "net.ipv4.tcp_congestion_control": "bbr",
        },
    }


def apply_sysctl(values):
    conf = "/etc/sysctl.d/99-solus-advisor.conf"
    try:
        with open(conf, "w") as fh:
            for k, v in values.items():
                fh.write(f"{k} = {v}\n")
        subprocess.run(["sysctl", "--system"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def main(argv):
    as_json = "--json" in argv
    do_apply = "--apply" in argv

    profile = load_profile()
    rec = recommend(profile)

    if as_json:
        print(json.dumps(rec, indent=2))
        return 0

    print(f"RAM: {rec['ram_gb']} GB")
    print(f"Recommended kernel variant: x86-64-{rec['kernel_variant']}")
    print(f"Recommended ZRAM size: {rec['zram_size']}")
    print(f"Gaming governor: {rec['cpu_governor_gaming']}  "
          f"Daily governor: {rec['cpu_governor_daily']}")
    print("\nGPU tips:")
    for t in rec["gpu_tips"]:
        print(f"  • {t}")
    print("\nGame tweaks:")
    for t in rec["game_tweaks"]:
        print(f"  • {t}")
    if do_apply:
        ok = apply_sysctl(rec["sysctl"])
        print(f"\n--apply: sysctl written {'ok' if ok else 'failed (need root)'}")
    else:
        print(f"\nRun with --apply to write sysctl, or:")
        print("  sudo solus-layout set gaming")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
