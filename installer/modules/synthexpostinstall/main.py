#!/usr/bin/env python3
# =============================================================================
# Calamares Module: synthexpostinstall
# Runs immediately after Calamares finishes writing the target system.
# Applies profile, installs Flatpak apps, configures GPU, themes, services.
# =============================================================================

import os
import sys
import json
import shutil
import subprocess
import time
from pathlib import Path

import libcalamares

# ── Module metadata ────────────────────────────────────────────────────────────
SYNTHEX_STATE_DIR   = Path("/var/lib/synthex")
INSTALL_PROFILE_KEY = "synthex_install_profile"
OOBE_APPS_KEY       = "synthex_oobe_apps"
SYNTHEX_LIBEXEC     = Path("/usr/libexec/synthex")

def _run(cmd: list, chroot: bool = True, check: bool = False) -> int:
    """Run a command, optionally inside the install target chroot."""
    if chroot:
        root = libcalamares.globalstorage.value("rootMountPoint") or "/mnt/synthex"
        full_cmd = ["chroot", root] + cmd
    else:
        full_cmd = cmd

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            libcalamares.utils.debug(
                f"[synthexpostinstall] Command failed ({result.returncode}): "
                f"{' '.join(cmd)}\nSTDERR: {result.stderr[:500]}"
            )
        return result.returncode
    except subprocess.TimeoutExpired:
        libcalamares.utils.warning(f"[synthexpostinstall] Timeout: {' '.join(cmd)}")
        return -1
    except Exception as exc:
        libcalamares.utils.warning(f"[synthexpostinstall] Error: {exc}")
        return -1


def _chroot_path(rel: str) -> Path:
    root = libcalamares.globalstorage.value("rootMountPoint") or "/mnt/synthex"
    return Path(root) / rel.lstrip("/")


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Write install profile to target
# ─────────────────────────────────────────────────────────────────────────────
def write_profile() -> None:
    profile_data = libcalamares.globalstorage.value(INSTALL_PROFILE_KEY) or {}
    if not profile_data:
        profile_data = {
            "edition":  "plasma",
            "profile":  "classic",
            "version":  "2026.10",
            "variant":  "v3",
        }

    state_dir = _chroot_path(str(SYNTHEX_STATE_DIR))
    _write_json(state_dir / "install-profile.json", profile_data)
    libcalamares.utils.debug(
        f"[synthexpostinstall] Profile written: {profile_data.get('profile', 'unknown')}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Write OOBE app selections
# ─────────────────────────────────────────────────────────────────────────────
def write_oobe_apps() -> None:
    apps_data = libcalamares.globalstorage.value(OOBE_APPS_KEY) or {}
    state_dir = _chroot_path(str(SYNTHEX_STATE_DIR))
    _write_json(state_dir / "oobe-apps.json", apps_data)
    libcalamares.utils.debug("[synthexpostinstall] OOBE app selections written")


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Detect GPU and write driver hints
# ─────────────────────────────────────────────────────────────────────────────
def detect_gpu() -> str:
    """Return 'nvidia', 'amd', 'intel', or 'unknown'."""
    try:
        out = subprocess.check_output(["lspci"], text=True, timeout=10)
    except Exception:
        return "unknown"

    low = out.lower()
    if "nvidia" in low:
        return "nvidia"
    elif "amd" in low or "ati" in low:
        return "amd"
    elif "intel" in low:
        return "intel"
    return "unknown"


def configure_gpu(gpu: str) -> None:
    state_dir = _chroot_path(str(SYNTHEX_STATE_DIR))
    hw_info = {"gpu_vendor": gpu, "detected_at": "calamares-postinstall"}
    _write_json(state_dir / "hwdetect.json", hw_info)

    if gpu == "nvidia":
        # Enable NVIDIA DRM kernel parameter
        grub_path = _chroot_path("/etc/default/grub")
        if grub_path.exists():
            text = grub_path.read_text()
            if "nvidia-drm.modeset" not in text:
                text = text.replace(
                    'quiet splash',
                    'quiet splash nvidia-drm.modeset=1 nvidia.NVreg_PreserveVideoMemoryAllocations=1'
                )
                grub_path.write_text(text)

        # Enable NVIDIA services
        _run(["systemctl", "enable", "nvidia-powerd.service"])
        _run(["systemctl", "enable", "nvidia-suspend.service"])
        _run(["systemctl", "enable", "nvidia-hibernate.service"])
        libcalamares.utils.debug("[synthexpostinstall] NVIDIA configuration applied")

    elif gpu == "amd":
        # AMD: enable amdgpu, disable nouveau
        dracut_extra = _chroot_path("/etc/dracut.conf.d/91-synthex-amd.conf")
        dracut_extra.parent.mkdir(parents=True, exist_ok=True)
        dracut_extra.write_text(
            'add_drivers+=" amdgpu radeon "\n'
            'omit_drivers+=" nouveau "\n'
        )
        libcalamares.utils.debug("[synthexpostinstall] AMD GPU configuration applied")

    elif gpu == "intel":
        dracut_extra = _chroot_path("/etc/dracut.conf.d/91-synthex-intel.conf")
        dracut_extra.parent.mkdir(parents=True, exist_ok=True)
        dracut_extra.write_text('add_drivers+=" i915 xe "\n')
        libcalamares.utils.debug("[synthexpostinstall] Intel GPU configuration applied")


# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Apply SDDM theme
# ─────────────────────────────────────────────────────────────────────────────
def apply_sddm_theme() -> None:
    sddm_conf_d = _chroot_path("/etc/sddm.conf.d")
    sddm_conf_d.mkdir(parents=True, exist_ok=True)
    synthex_sddm = sddm_conf_d / "synthex.conf"
    synthex_sddm.write_text(
        "[Theme]\nCurrent=synthex\n\n"
        "[General]\nDisplayServer=wayland\n"
    )
    libcalamares.utils.debug("[synthexpostinstall] SDDM theme set to 'synthex'")


# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Configure Plymouth
# ─────────────────────────────────────────────────────────────────────────────
def apply_plymouth() -> None:
    plymouth_default = _chroot_path("/etc/plymouth/plymouthd.conf")
    plymouth_default.parent.mkdir(parents=True, exist_ok=True)
    if not plymouth_default.exists():
        plymouth_default.write_text("[Daemon]\nTheme=synthex\nShowDelay=0\n")
    else:
        text = plymouth_default.read_text()
        if "Theme=" not in text:
            text += "\n[Daemon]\nTheme=synthex\n"
        else:
            import re
            text = re.sub(r"Theme=.*", "Theme=synthex", text)
        plymouth_default.write_text(text)

    # Rebuild initramfs with Plymouth
    _run(["dracut", "--force", "--quiet"])
    libcalamares.utils.debug("[synthexpostinstall] Plymouth theme applied + initramfs rebuilt")


# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Enable SynthOS systemd services
# ─────────────────────────────────────────────────────────────────────────────
def enable_services() -> None:
    enable = [
        "synthex-firstboot.service",
        "synthex-system-daemon.service",
        "synthex-hwdaemon.service",
        "sddm.service",
        "NetworkManager.service",
        "bluetooth.service",
        "fstrim.timer",
        "irqbalance.service",
        "firewalld.service",
    ]
    disable = [
        "initial-setup.service",
        "initial-setup-graphical.service",
    ]

    for svc in enable:
        _run(["systemctl", "enable", svc])

    for svc in disable:
        _run(["systemctl", "disable", svc])

    libcalamares.utils.debug(f"[synthexpostinstall] Enabled {len(enable)} services")


# ─────────────────────────────────────────────────────────────────────────────
# Step 7: Rebuild GRUB
# ─────────────────────────────────────────────────────────────────────────────
def rebuild_grub() -> None:
    grub_cfg = "/boot/grub2/grub.cfg"
    if _chroot_path("/sys/firmware/efi").exists():
        grub_cfg = "/boot/efi/EFI/synthex/grub.cfg"

    _run(["grub2-mkconfig", "-o", grub_cfg])
    libcalamares.utils.debug(f"[synthexpostinstall] GRUB rebuilt → {grub_cfg}")


# ─────────────────────────────────────────────────────────────────────────────
# Step 8: Add Flathub remote (apps installed by OOBE on first login)
# ─────────────────────────────────────────────────────────────────────────────
def setup_flatpak() -> None:
    _run(["flatpak", "remote-add", "--if-not-exists", "--system",
          "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo"])
    libcalamares.utils.debug("[synthexpostinstall] Flathub remote added")


# ─────────────────────────────────────────────────────────────────────────────
# Main entrypoint called by Calamares
# ─────────────────────────────────────────────────────────────────────────────
def run():
    """Calamares calls this function to execute the module."""
    libcalamares.utils.debug("[synthexpostinstall] Starting SynthOS post-install module")

    steps = [
        ("Writing install profile",   write_profile),
        ("Writing OOBE app selections", write_oobe_apps),
        ("Detecting GPU",              lambda: configure_gpu(detect_gpu())),
        ("Applying SDDM theme",        apply_sddm_theme),
        ("Configuring Plymouth",       apply_plymouth),
        ("Enabling services",          enable_services),
        ("Rebuilding GRUB",            rebuild_grub),
        ("Setting up Flatpak/Flathub", setup_flatpak),
    ]

    total = len(steps)
    for idx, (label, fn) in enumerate(steps):
        progress = (idx + 1) / total
        libcalamares.job.setProgress(progress)
        libcalamares.utils.debug(f"[synthexpostinstall] [{idx+1}/{total}] {label}...")
        try:
            fn()
        except Exception as exc:
            libcalamares.utils.warning(
                f"[synthexpostinstall] Step '{label}' failed: {exc}"
            )
            # Non-fatal — log and continue

    libcalamares.utils.debug("[synthexpostinstall] All post-install steps complete ✓")
    return None  # None = success in Calamares
