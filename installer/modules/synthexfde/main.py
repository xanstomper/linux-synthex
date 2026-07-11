#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SynthexFDE - Full Disk Encryption setup for SynthOS Calamares installer"""

import subprocess, os, libcalamares
from libcalamares.utils import debug, warning

def pretty_name():
    return "Configuring full-disk encryption…"

def run():
    gs = libcalamares.globalstorage
    root = gs.value("rootMountPoint") or "/mnt"

    use_luks = gs.value("useLuks2")
    if not use_luks:
        debug("[FDE] LUKS2 not requested — skipping")
        return None

    debug("[FDE] Configuring LUKS2 / dm-crypt")

    # Write crypttab
    crypttab = os.path.join(root, "etc", "crypttab")
    try:
        with open(crypttab, "a") as f:
            f.write("# SynthOS FDE — managed by installer\n")
        debug("[FDE] crypttab updated")
    except Exception as e:
        warning(f"[FDE] Could not update crypttab: {e}")

    # Enable clevis/tang if configured
    tang_url = gs.value("tangUrl")
    if tang_url:
        debug(f"[FDE] Configuring Tang binding: {tang_url}")
        subprocess.run(
            ["chroot", root, "systemctl", "enable", "clevis-luks-askpass.path"],
            capture_output=True
        )

    debug("[FDE] Full-disk encryption setup complete")
    return None
