#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexservices
# Enables/disables systemd services for the installed SynthOS system

import os, subprocess, libcalamares

# Services to ENABLE on new install
ENABLE_SERVICES = [
    # Core SynthOS daemons
    "synthex-firstboot.service",
    "synthex-hardware-detect.service",
    "synthex-system-daemon.service",
    "synthex-update-manager.service",
    "synthex-security-scan.timer",
    "synthex-backup.timer",

    # Desktop / Display
    "sddm.service",
    "bluetooth.service",
    "cups.service",
    "avahi-daemon.service",
    "NetworkManager.service",

    # Audio
    "pipewire.socket",
    "pipewire-pulse.socket",
    "wireplumber.service",

    # Security
    "ufw.service",
    "auditd.service",
    "fstrim.timer",
    "logrotate.timer",
    "systemd-oomd.service",

    # Gaming (optional — only on profiles that include it)
    # "synthex-gaming-mode.service",  # enabled on demand

    # Performance
    "synthex-cpu-governor.service",
    "irqbalance.service",
    "earlyoom.service",

    # Hardware
    "thermald.service",
    "power-profiles-daemon.service",

    # Containers (if installed)
    # "docker.service",   # user must opt in
    # "podman.socket",
]

# Services to explicitly DISABLE (override distro defaults)
DISABLE_SERVICES = [
    "lvm2-monitor.service",        # not needed on BTRFS installs
    "mdmonitor.service",           # no software RAID by default
    "abrtd.service",               # replaced by synthex crash reporter
    "abrt-journal-core.service",
    "geoclue.service",             # privacy — opt-in via settings
    "remote-fs.target",
    "nfs-client.target",
]

# User-level services to enable (run as the first user)
USER_ENABLE_SERVICES = [
    "pipewire.service",
    "pipewire-pulse.service",
    "wireplumber.service",
    "synthex-tray.service",
    "synthex-agent.service",
]


def _chroot_run(root: str, cmd: list[str], check=False) -> int:
    """Run a command in the target chroot."""
    full_cmd = ["chroot", root] + cmd
    r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        libcalamares.utils.debug(
            f"[synthexservices] {' '.join(cmd)} → rc={r.returncode}: {r.stderr.strip()}"
        )
    return r.returncode


def run():
    gs = libcalamares.globalStorage
    root = gs.value("rootMountPoint") or "/mnt/synthex"

    if not os.path.isdir(root):
        return (f"Target root {root!r} does not exist", "synthexservices: root not found")

    libcalamares.utils.debug(f"[synthexservices] Configuring services in {root}")

    # ── Check systemd in chroot ───────────────────────────────────────────────
    systemctl = os.path.join(root, "usr/bin/systemctl")
    if not os.path.exists(systemctl):
        libcalamares.utils.warning("[synthexservices] systemctl not found in chroot — skipping")
        return None

    errors = []

    # ── Enable services ───────────────────────────────────────────────────────
    libcalamares.utils.debug("[synthexservices] Enabling system services…")
    # Filter to only enable services that are actually installed
    available = []
    for svc in ENABLE_SERVICES:
        svc_path = os.path.join(root, "usr/lib/systemd/system", svc)
        if os.path.exists(svc_path):
            available.append(svc)
        else:
            libcalamares.utils.debug(f"[synthexservices] Skip (not installed): {svc}")

    if available:
        rc = _chroot_run(root, ["systemctl","enable"] + available)
        if rc != 0:
            errors.append(f"systemctl enable failed (rc={rc})")
        else:
            libcalamares.utils.debug(f"[synthexservices] Enabled: {len(available)} services")

    # ── Disable services ──────────────────────────────────────────────────────
    libcalamares.utils.debug("[synthexservices] Disabling unneeded services…")
    to_disable = []
    for svc in DISABLE_SERVICES:
        svc_path = os.path.join(root, "usr/lib/systemd/system", svc)
        if os.path.exists(svc_path):
            to_disable.append(svc)

    if to_disable:
        _chroot_run(root, ["systemctl","disable"] + to_disable)

    # ── Profile-specific overrides ────────────────────────────────────────────
    profile = gs.value("synthexProfile") or "classic"
    libcalamares.utils.debug(f"[synthexservices] Profile: {profile}")

    if profile in ("gaming", "pro-gaming"):
        # GameMode service for gaming profiles
        gm_svc = os.path.join(root, "usr/lib/systemd/system/synthex-gaming-mode.service")
        if os.path.exists(gm_svc):
            _chroot_run(root, ["systemctl","enable","synthex-gaming-mode.service"])
            libcalamares.utils.debug("[synthexservices] Enabled gaming mode service")

    if profile in ("studio", "pro"):
        # JACK audio for studio profiles
        for svc in ["jack.service","jackd.service"]:
            svc_path = os.path.join(root, "usr/lib/systemd/system", svc)
            if os.path.exists(svc_path):
                _chroot_run(root, ["systemctl","enable", svc])

    # ── First user lingering (for user services) ──────────────────────────────
    users = gs.value("users") or []
    if users:
        first_user = users[0].get("username","")
        if first_user:
            # Enable lingering so user services start at boot without login
            _chroot_run(root, ["loginctl","enable-linger", first_user])
            libcalamares.utils.debug(f"[synthexservices] Linger enabled for {first_user}")

            # Write user service preset
            user_systemd = os.path.join(root, f"home/{first_user}/.config/systemd/user")
            os.makedirs(user_systemd, exist_ok=True)

            # Write a wants-symlink list for user services
            wants_dir = os.path.join(user_systemd, "default.target.wants")
            os.makedirs(wants_dir, exist_ok=True)
            for svc in USER_ENABLE_SERVICES:
                svc_src = os.path.join(root, "usr/lib/systemd/user", svc)
                svc_dst = os.path.join(wants_dir, svc)
                if os.path.exists(svc_src) and not os.path.exists(svc_dst):
                    os.symlink(f"/usr/lib/systemd/user/{svc}", svc_dst)
                    libcalamares.utils.debug(f"[synthexservices] User service: {svc}")

    # ── Preset all installed services (respects vendor presets) ──────────────
    _chroot_run(root, ["systemctl","preset-all","--preset-mode=enable-only"])

    # ── Re-enable synthex services that may have been un-preset ──────────────
    if available:
        _chroot_run(root, ["systemctl","enable"] + available)

    if errors:
        libcalamares.utils.warning(f"[synthexservices] Completed with warnings: {errors}")
    else:
        libcalamares.utils.debug("[synthexservices] Service configuration complete.")

    return None
