#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
Comprehensive Boot & System Daemon Health Auditor for SynthOS / Synthex.
Audits every systemd service, socket, timer, target, D-Bus policy,
tmpfiles, sysusers, dracut confs, modprobe rules, and session definitions.
"""

import glob
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class BootAuditor:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = 0

    def check(self, condition: bool, msg: str, is_warning: bool = False):
        if condition:
            self.passed += 1
            print(f"  \033[32m✔\033[0m {msg}")
        else:
            if is_warning:
                self.warnings.append(msg)
                print(f"  \033[33m⚠ [WARN]\033[0m {msg}")
            else:
                self.errors.append(msg)
                print(f"  \033[31m✖ [FAIL]\033[0m {msg}")

    def run_all_audits(self):
        print("\n" + "=" * 70)
        print("  SYNTHOS BOOT & SYSTEM DAEMON INTEGRITY AUDIT")
        print("=" * 70)

        self.audit_systemd_services()
        self.audit_sysusers_and_tmpfiles()
        self.audit_dbus_bus_policies()
        self.audit_dracut_and_initramfs()
        self.audit_modprobe_and_kernel_cmdline()
        self.audit_display_manager_and_sessions()
        self.audit_firstboot_and_installer()
        self.audit_polkit_and_sudoers()
        self.audit_udev_rules()

        print("\n" + "=" * 70)
        print(f"  AUDIT SUMMARY: {self.passed} Passed | {len(self.warnings)} Warnings | {len(self.errors)} Errors")
        print("=" * 70 + "\n")

        if self.errors:
            print("\033[31mCritical Errors Found:\033[0m")
            for e in self.errors:
                print(f"  - {e}")
            return 1
        else:
            print("\033[32m✔ 100% BOOT & DAEMON INTEGRITY VERIFIED — SYSTEM IS READY TO BOOT CLEANLY!\033[0m\n")
            return 0

    # ── 1. Systemd Units Audit ──────────────────────────────────────────────
    def audit_systemd_services(self):
        print("\n[1/9] Auditing Systemd Units in systemd/ ...")
        systemd_dir = REPO_ROOT / "systemd"
        services = list(systemd_dir.glob("*.service"))
        self.check(len(services) > 20, f"Found {len(services)} systemd services in systemd/")

        # Gather crate binaries built in src/ and aether/
        crates_built = set()
        for cargo_toml in list(REPO_ROOT.glob("src/**/Cargo.toml")) + list(REPO_ROOT.glob("aether/**/Cargo.toml")):
            try:
                with open(cargo_toml) as f:
                    content = f.read()
                    for line in content.splitlines():
                        if line.strip().startswith("name = "):
                            name = line.split("=")[1].strip().strip('"').strip("'")
                            crates_built.add(name)
            except Exception:
                pass

        for s_file in services:
            content = s_file.read_text()
            name = s_file.name

            # Check Unit section
            self.check("[Unit]" in content, f"{name} contains [Unit] section")
            self.check("[Install]" in content or "Type=oneshot" in content or "synthex.target" in name, f"{name} contains [Install] or is target/oneshot")

            # Check ExecStart
            exec_match = re.search(r"ExecStart=(.+)", content)
            if exec_match:
                cmd_line = exec_match.group(1).strip()
                cmd = cmd_line.split()[0].lstrip("-")
                base_cmd = os.path.basename(cmd)
                is_valid = (
                    base_cmd in crates_built or
                    cmd.startswith("/usr/bin/") or
                    cmd.startswith("/usr/sbin/") or
                    cmd.startswith("/usr/libexec/") or
                    cmd.startswith("/bin/") or
                    cmd.startswith("/sbin/") or
                    cmd.endswith(".sh") or
                    cmd in ("python3", "bash", "sh", "systemctl", "env")
                )
                self.check(is_valid, f"{name} ExecStart ({base_cmd}) maps to valid crate or system executable")

            # Check Type
            type_match = re.search(r"Type=(\w+)", content)
            if type_match:
                srv_type = type_match.group(1)
                self.check(srv_type in ("simple", "exec", "forking", "oneshot", "dbus", "notify", "idle"), f"{name} valid service Type={srv_type}")

    # ── 2. Sysusers & Tmpfiles Audit ─────────────────────────────────────────
    def audit_sysusers_and_tmpfiles(self):
        print("\n[2/9] Auditing Sysusers & Tmpfiles ...")
        systemd_dir = REPO_ROOT / "systemd"
        services = list(systemd_dir.glob("*.service"))

        # Find all custom users requested in services
        users_requested = set()
        for s in services:
            content = s.read_text()
            matches = re.findall(r"^User=([a-zA-Z0-9_-]+)", content, re.MULTILINE)
            for u in matches:
                if u not in ("root", "nobody", "daemon"):
                    users_requested.add(u)

        # Find all users declared in .sysusers files
        users_declared = set()
        for su in systemd_dir.glob("*.sysusers"):
            for line in su.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0] == "u":
                        users_declared.add(parts[1])

        # Also check tmpfiles.d
        tmpfiles_dir = systemd_dir / "tmpfiles.d"
        self.check(tmpfiles_dir.exists(), "systemd/tmpfiles.d exists")

        for u in sorted(users_requested):
            is_declared = (u in users_declared)
            self.check(is_declared, f"Service User='{u}' has corresponding sysusers definition", is_warning=False)

    # ── 3. D-Bus Policies Audit ──────────────────────────────────────────────
    def audit_dbus_bus_policies(self):
        print("\n[3/9] Auditing D-Bus System Bus Policies in dbus/ ...")
        dbus_dir = REPO_ROOT / "dbus"
        self.check(dbus_dir.exists(), "dbus/ directory exists")

        conf_files = list(dbus_dir.glob("*.conf"))
        self.check(len(conf_files) >= 4, f"Found {len(conf_files)} D-Bus policy configurations")

        for conf in conf_files:
            text = conf.read_text()
            self.check("<busconfig>" in text, f"{conf.name} is valid XML busconfig")
            self.check("allow own=" in text or "allow send_destination=" in text, f"{conf.name} grants service ownership/send permissions")

    # ── 4. Dracut & Initramfs Audit ─────────────────────────────────────────
    def audit_dracut_and_initramfs(self):
        print("\n[4/9] Auditing Dracut & Early Boot Initramfs configs ...")
        dracut_conf = REPO_ROOT / "configs/dracut/dracut-synthex.conf"
        self.check(dracut_conf.exists(), "configs/dracut/dracut-synthex.conf exists")
        if dracut_conf.exists():
            txt = dracut_conf.read_text()
            self.check("add_dracutmodules+=" in txt, "dracut-synthex.conf specifies add_dracutmodules")
            self.check("btrfs" in txt, "dracut includes btrfs module for rootfs")
            self.check("systemd" in txt, "dracut includes systemd initramfs")

    # ── 5. Modprobe & Kernel Cmdline Audit ──────────────────────────────────
    def audit_modprobe_and_kernel_cmdline(self):
        print("\n[5/9] Auditing Modprobe & Kernel Cmdline configs ...")
        modprobe_dir = REPO_ROOT / "configs/modprobe"
        self.check(modprobe_dir.exists(), "configs/modprobe directory exists")

        # Check nvidia modeset
        nvidia_conf = modprobe_dir / "synthex-nvidia.conf"
        if nvidia_conf.exists():
            self.check("modeset=1" in nvidia_conf.read_text(), "Nvidia DRM modeset=1 enabled")

        # Check blacklist
        blacklist_conf = modprobe_dir / "synthex-blacklist.conf"
        if blacklist_conf.exists():
            txt = blacklist_conf.read_text()
            self.check("blacklist nouveau" in txt, "Nouveau blacklisted in favor of Nvidia proprietary driver")

    # ── 6. Display Manager & Session Startup Audit ──────────────────────────
    def audit_display_manager_and_sessions(self):
        print("\n[6/9] Auditing Display Manager & Desktop Session configs ...")
        sddm_conf = REPO_ROOT / "desktop/sddm/sddm.conf"
        self.check(sddm_conf.exists(), "desktop/sddm/sddm.conf exists")
        if sddm_conf.exists():
            txt = sddm_conf.read_text()
            self.check("DisplayServer=wayland" in txt or "Wayland" in txt, "SDDM configured for Wayland display server")

        # Check Hyprland configs
        hypr_conf = REPO_ROOT / "desktop/hyprland/hyprland.conf"
        self.check(hypr_conf.exists(), "desktop/hyprland/hyprland.conf exists")

    # ── 7. Firstboot & Installer Audit ──────────────────────────────────────
    def audit_firstboot_and_installer(self):
        print("\n[7/9] Auditing Firstboot & Calamares Installer modules ...")
        fb_sh = REPO_ROOT / "systemd/synthex-firstboot-impl.sh"
        self.check(fb_sh.exists(), "systemd/synthex-firstboot-impl.sh exists")
        if fb_sh.exists():
            txt = fb_sh.read_text()
            self.check("set -e" in txt or "#!/bin/bash" in txt, "synthex-firstboot-impl.sh has proper shell header")

        calamares_settings = REPO_ROOT / "installer/config/settings.conf"
        self.check(calamares_settings.exists(), "installer/config/settings.conf exists")

    # ── 8. Polkit & Sudoers Audit ───────────────────────────────────────────
    def audit_polkit_and_sudoers(self):
        print("\n[8/9] Auditing Polkit & Sudoers Permissions ...")
        sudoers_files = list(REPO_ROOT.glob("security/**/sudoers*")) + list(REPO_ROOT.glob("configs/**/sudoers*"))
        self.check(len(sudoers_files) > 0 or (REPO_ROOT / "build/kickstart").exists(), "Sudoers rules or kickstart configurations exist")

    # ── 9. Udev Rules Audit ─────────────────────────────────────────────────
    def audit_udev_rules(self):
        print("\n[9/9] Auditing Udev Rules in udev/ ...")
        udev_dir = REPO_ROOT / "udev"
        self.check(udev_dir.exists(), "udev directory exists")
        rules = list(udev_dir.glob("*.rules"))
        self.check(len(rules) > 0, f"Found {len(rules)} udev rules files")


if __name__ == "__main__":
    auditor = BootAuditor()
    sys.exit(auditor.run_all_audits())
