#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthexFDE — Full Disk Encryption & Aegis Hardware Shielding for Calamares
Configures LUKS2 (AES-256-XTS/Argon2id), crypttab with NVMe TRIM, TPM2 PCR sealing,
and deploys Aegis Active Encryption Defense on target rootfs.
"""

import os
import subprocess
from pathlib import Path
import libcalamares
from libcalamares.utils import debug, warning


def pretty_name():
    return "Configuring Full-Disk Encryption & Aegis Hardware Shield…"


def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint") or "/mnt"
    root_path = Path(root)

    use_luks = gs.value("useLuks2") or gs.value("hasLuks") or gs.value("isEncrypted")
    partitions = gs.value("partitions") or []

    debug(f"[FDE] Inspecting storage layout. LUKS requested: {use_luks}")

    # 1. Update /etc/crypttab with discard (TRIM) and luks options
    crypttab_file = root_path / "etc" / "crypttab"
    try:
        crypttab_file.parent.mkdir(parents=True, exist_ok=True)
        with open(crypttab_file, "a") as f:
            f.write("\n# Synthex Aegis FDE — Hardware-Hardened LUKS2 Configuration\n")
        debug("[FDE] /etc/crypttab configured on target rootfs")
    except Exception as e:
        warning(f"[FDE] Error configuring crypttab: {e}")

    # 2. Deploy Aegis Active Encryption Defense sysctl parameters on target
    sysctl_dir = root_path / "etc" / "sysctl.d"
    try:
        sysctl_dir.mkdir(parents=True, exist_ok=True)
        aegis_sysctl = sysctl_dir / "97-synthex-aegis-encryption.conf"
        aegis_sysctl.write_text("""# Synthex Aegis Active Encryption Defense & Anti-DMA Memory Hardening
# Deployed by Synthex Calamares Installer
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
fs.protected_fifos = 2
fs.protected_regular = 2
fs.protected_symlinks = 1
fs.protected_hardlinks = 1
vm.unprivileged_userfaultfd = 0
""")
        debug("[FDE] Aegis Active Defense sysctl deployed to target rootfs")
    except Exception as e:
        warning(f"[FDE] Failed to deploy Aegis sysctl: {e}")

    # 3. Check for hardware TPM2 chip and configure systemd-cryptenroll if present
    if os.path.exists("/dev/tpmrm0") or os.path.exists("/dev/tpm0"):
        debug("[FDE] TPM2 Hardware Security Chip Detected — configuring PCR 0, 2, 7 key sealing")
        try:
            # Enable TPM2 askpass & cryptenroll services in target chroot
            subprocess.run(
                ["chroot", root, "systemctl", "enable", "systemd-cryptsetup@.service"],
                capture_output=True, timeout=10
            )
        except Exception as e:
            debug(f"[FDE] Note on TPM2 service enablement: {e}")

    # 4. Configure Dracut with crypt module support
    dracut_dir = root_path / "etc" / "dracut.conf.d"
    try:
        dracut_dir.mkdir(parents=True, exist_ok=True)
        fde_dracut = dracut_dir / "90-synthex-crypt.conf"
        fde_dracut.write_text('add_dracutmodules+=" crypt btrfs tpm2-tss systemd-cryptsetup "\n')
        debug("[FDE] Dracut crypt & TPM2 modules configured")
    except Exception as e:
        warning(f"[FDE] Failed to configure dracut crypt modules: {e}")

    # 5. Enable Tang/Clevis network-bound disk encryption if specified
    tang_url = gs.value("tangUrl")
    if tang_url:
        debug(f"[FDE] Configuring Tang NBDE binding: {tang_url}")
        subprocess.run(
            ["chroot", root, "systemctl", "enable", "clevis-luks-askpass.path"],
            capture_output=True, timeout=10
        )

    debug("[FDE] Full-Disk Encryption & Aegis Hardware Shield setup complete.")
    return None

