#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS First Boot — runs once on first system startup to finalize setup

import sys, os, subprocess, json, logging, time
logging.basicConfig(level=logging.INFO, format="[synthex-boot] %(levelname)s %(message)s")
log = logging.getLogger("synthex-boot")

STATE_FILE = "/var/lib/synthex/firstboot-complete"

def run(cmd, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("timeout", 60)
    try:
        return subprocess.run(cmd, **kw)
    except Exception as e:
        log.warning(f"Command failed: {cmd}: {e}")
        return None

def init_flatpak():
    log.info("Initializing Flatpak repositories")
    run(["flatpak","remote-add","--if-not-exists","flathub",
         "https://dl.flathub.org/repo/flathub.flatpakrepo"])
    run(["flatpak","remote-add","--if-not-exists","flathub-beta",
         "https://dl.flathub.org/beta-repo/flathub-beta.flatpakrepo"])
    log.info("Flatpak repos configured")

def init_dnf():
    log.info("Updating DNF metadata")
    run(["dnf","makecache","--timer"], timeout=120)

def generate_machine_id():
    mid = "/etc/machine-id"
    if not os.path.exists(mid) or os.path.getsize(mid) == 0:
        log.info("Generating machine-id")
        run(["systemd-machine-id-setup"])

def init_ssh_keys():
    log.info("Generating SSH host keys")
    for key_type in ["rsa","ecdsa","ed25519"]:
        key_file = f"/etc/ssh/ssh_host_{key_type}_key"
        if not os.path.exists(key_file):
            run(["ssh-keygen","-t",key_type,"-f",key_file,"-N",""])

def init_entropy():
    log.info("Seeding random number generator")
    run(["rngd","-r","/dev/random"], timeout=5)

def rebuild_font_cache():
    log.info("Rebuilding font cache")
    run(["fc-cache","-f"], timeout=60)

def setup_synthex_dirs():
    dirs = [
        "/var/lib/synthex",
        "/var/cache/synthex",
        "/var/log/synthex",
        "/etc/synthex",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    log.info("SynthOS directories created")

def mark_complete():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({
            "completed_at": time.time(),
            "version": "2026.10",
        }, f)
    log.info(f"First boot complete. State: {STATE_FILE}")

def main():
    if os.path.exists(STATE_FILE):
        log.info("First boot already completed — exiting")
        sys.exit(0)

    log.info("=== SynthOS First Boot Initialization ===")

    steps = [
        ("Creating SynthOS directories",    setup_synthex_dirs),
        ("Generating machine ID",           generate_machine_id),
        ("Initializing SSH host keys",      init_ssh_keys),
        ("Seeding entropy",                 init_entropy),
        ("Configuring Flatpak",             init_flatpak),
        ("Updating DNF metadata",           init_dnf),
        ("Rebuilding font cache",           rebuild_font_cache),
    ]

    for desc, fn in steps:
        log.info(f"Step: {desc}")
        try:
            fn()
        except Exception as e:
            log.error(f"Step failed ({desc}): {e}")
            # Continue with remaining steps

    mark_complete()
    log.info("=== First boot complete ===")

if __name__ == "__main__":
    main()
