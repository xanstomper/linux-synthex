#!/usr/bin/env python3
"""synthex AI Driver Assistant — detect hardware and recommend exact drivers.

Reads the hw profile produced by synthex-hwdaemon, maps it to driver packages,
explains what each does, and offers to install them via dnf.

Usage:
    synthex-ai-assistant driver                # interactive
    synthex-ai-assistant driver --json          # machine-readable
    synthex-ai-assistant driver --install       # apply recommendations
"""
import json
import os
import subprocess
import sys

PROFILE = "/var/run/synthex-hw-profile.json"
LEGACY = "/var/lib/synthex/hardware-profile"

DRIVER_MAP = {
    "NVIDIA": {
        "packages": ["akmod-nvidia", "xorg-x11-drv-nvidia-cuda",
                     "nvidia-persistenced", "nvidia-settings",
                     "nvidia-utils", "nvidia-compute-utils",
                     "libva-nvidia-driver"],
        "note": "Proprietary driver with CUDA, NVENC/NVDEC hardware encode/decode, and persistence daemon.",
    },
    "AMD": {
        "packages": ["mesa-dri-drivers", "mesa-vulkan-drivers",
                     "mesa-va-drivers", "mesa-vdpau-drivers",
                     "libva", "libva-utils", "linux-firmware-amd"],
        "note": "Open Mesa stack: RADV Vulkan, VAAPI hardware video, AMD firmware.",
    },
    "Intel": {
        "packages": ["mesa-dri-drivers", "mesa-vulkan-drivers",
                     "intel-media-driver", "intel-vaapi-driver",
                     "intel-compute-runtime", "vulkan-intel",
                     "linux-firmware-intel"],
        "note": "Mesa (ANV Vulkan) + Intel media/VAAPI + compute runtime + firmware.",
    },
}


def load_profile():
    for p in (PROFILE, LEGACY):
        if os.path.exists(p):
            try:
                with open(p) as fh:
                    return json.load(fh)
            except Exception:
                pass
    return None


def detect_vendor(profile):
    if not profile:
        return None
    gpu = profile.get("gpu", {})
    vendor = (gpu.get("vendor") or "").upper()
    vid = gpu.get("vendorId", "")
    if "NVIDIA" in vendor or vid == "0x10de":
        return "NVIDIA"
    if "AMD" in vendor or vid == "0x1002":
        return "AMD"
    if "INTEL" in vendor or vid == "0x8086":
        return "Intel"
    return None


def installed_packages():
    try:
        out = subprocess.run(["rpm", "-qa", "--queryformat", "%{NAME}\n"],
                             capture_output=True, text=True, timeout=30)
        return set(out.stdout.splitlines())
    except Exception:
        return set()


def recommend(vendor):
    info = DRIVER_MAP.get(vendor)
    if not info:
        return None
    have = installed_packages()
    to_install = [p for p in info["packages"] if p not in have]
    return {
        "vendor": vendor,
        "missing": to_install,
        "already_installed": [p for p in info["packages"] if p in have],
        "note": info["note"],
    }


def main(argv):
    as_json = "--json" in argv
    do_install = "--install" in argv

    profile = load_profile()
    vendor = detect_vendor(profile)
    if not vendor:
        msg = "No GPU vendor detected in hardware profile."
        if as_json:
            print(json.dumps({"error": msg}))
        else:
            print(msg)
        return 1

    rec = recommend(vendor)
    if as_json:
        print(json.dumps(rec, indent=2))
        return 0

    print(f"Detected GPU vendor: {vendor}")
    print(f"  {rec['note']}\n")
    if rec["already_installed"]:
        print("Already installed:")
        for p in rec["already_installed"]:
            print(f"  ✓ {p}")
    if rec["missing"]:
        print("\nRecommended to install:")
        for p in rec["missing"]:
            print(f"  + {p}")
        if do_install:
            print("\nInstalling…")
            subprocess.run(["dnf", "install", "-y"] + rec["missing"], check=False)
        else:
            print("\nRun with --install to apply, or:")
            print(f"  sudo dnf install {' '.join(rec['missing'])}")
    else:
        print("\nAll recommended drivers are already installed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
