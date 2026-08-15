#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Platform Adapters (Fedora-first)
Every adapter targets Synthex's Fedora base (dnf5/rpm, firewalld, grubby,
akmods, SDDM, btrfs/timeshift, PackageKit) and degrades gracefully on other
environments (pkcon → apt/dpkg dev boxes) so the UI is always functional.

Modules: PackageManager, FirewallLayer, ReposAdapter, UpdatesAdapter,
DriversAdapter, TimeshiftAdapter, LoginScreenAdapter, ThunderboltAdapter,
ColorAdapter, GraphicsTabletAdapter, ScreensaverAdapter, AutostartAdapter,
PreferredAppsAdapter, WindowsAdapter, WorkspacesAdapter, HotCornersAdapter,
EffectsAdapter, ExtensionsAdapter, GesturesAdapter, InputMethodAdapter,
FontsAdapter, BackgroundsAdapter, PanelAdapter, AppletAdapter, DeskletAdapter,
ActionsAdapter, AccountDetailsAdapter, NightLightAdapter, AdminAdapter,
OnlineAccountsAdapter, AdvancedPointerAdapter.
"""

import os
import re
import glob
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from gi.repository import Gio
from synth_system_adapters import run_cmd, get_gsettings, safe_set_gsetting

def _gget(schema_id: str, key: str, default=None):
    """Abort-proof GSettings read: verifies schema AND key existence first."""
    try:
        source = Gio.SettingsSchemaSource.get_default()
        if not source:
            return default
        schema_obj = source.lookup(schema_id, True)
        if not schema_obj or not schema_obj.has_key(key):
            return default
        s = Gio.Settings.new(schema_id)
        return s.get_value(key).unpack()
    except Exception:
        return default


HOME = Path.home()


def _which(*names):
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


# ══════════════════════════════════════════════════════════════════════════════
# 1. PACKAGE MANAGER ABSTRACTION (dnf5 → dnf4 → pkcon → apt)
# ══════════════════════════════════════════════════════════════════════════════

class PackageManager:
    """Detects the native backend once; Fedora/Synthex uses dnf5 or dnf4."""

    _backend = None

    @classmethod
    def backend(cls) -> str:
        if cls._backend:
            return cls._backend
        if _which("dnf5", "dnf"):
            cls._backend = "dnf"
        elif _which("pkcon"):
            cls._backend = "pkcon"
        elif _which("apt"):
            cls._backend = "apt"
        elif _which("rpm") and shutil.which("rpm"):
            cls._backend = "rpm"
        else:
            cls._backend = "none"
        return cls._backend

    @classmethod
    def list_installed(cls, query: str = "", limit: int = 25) -> List[Dict]:
        q = query.lower()
        pkgs = []
        be = cls.backend()
        if be in ("dnf", "rpm"):
            ok, out, _ = run_cmd(["rpm", "-qa", "--qf",
                                  "%{NAME}\\t%{VERSION}-%{RELEASE}\\t%{GROUP}\\n"], timeout=25)
            if ok and out:
                for line in out.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        pkgs.append({"name": parts[0], "version": parts[1],
                                     "section": parts[2] if len(parts) > 2 else "system"})
        elif be == "apt":
            ok, out, _ = run_cmd(["dpkg-query", "-W", "-f=${binary:Package}\\t${Version}\\t${Section}\\n"], timeout=25)
            if ok and out:
                for line in out.splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        pkgs.append({"name": parts[0], "version": parts[1],
                                     "section": parts[2] if len(parts) > 2 else "system"})
        else:
            ok, out, _ = run_cmd(["pkcon", "get-packages", "--filter", "installed"], timeout=30)
            if ok and out:
                for line in out.splitlines():
                    m = re.match(r"Installed\s+(\S+)\s+(\S+)\s+(.+)", line)
                    if m:
                        pkgs.append({"name": m.group(1), "version": m.group(2), "section": m.group(3)[:40]})
        if q:
            pkgs = [p for p in pkgs if q in p["name"].lower() or q in p["section"].lower()]
        return pkgs[:limit]

    @classmethod
    def install(cls, pkgs: List[str]) -> Dict:
        be = cls.backend()
        if be == "dnf":
            ok, out, err = run_cmd(["pkexec", "dnf", "install", "-y", *pkgs], timeout=900)
        elif be == "apt":
            ok, out, err = run_cmd(["pkexec", "apt-get", "install", "-y", *pkgs], timeout=900)
        else:
            ok, out, err = run_cmd(["pkcon", "install", "-y", *pkgs], timeout=900)
        return {"ok": ok, "message": (out or err).splitlines()[-1][:160] if (out or err) else "", "backend": be}

    @classmethod
    def remove(cls, pkgs: List[str]) -> Dict:
        be = cls.backend()
        if be == "dnf":
            ok, out, err = run_cmd(["pkexec", "dnf", "remove", "-y", *pkgs], timeout=600)
        elif be == "apt":
            ok, out, err = run_cmd(["pkexec", "apt-get", "purge", "-y", *pkgs], timeout=600)
        else:
            ok, out, err = run_cmd(["pkcon", "remove", "-y", *pkgs], timeout=600)
        return {"ok": ok, "message": (out or err).splitlines()[-1][:160] if (out or err) else "", "backend": be}

    @classmethod
    def refresh_cache(cls) -> Dict:
        be = cls.backend()
        if be == "dnf":
            ok, out, err = run_cmd(["pkexec", "dnf", "makecache", "--refresh"], timeout=600)
        elif be == "apt":
            ok, out, err = run_cmd(["pkexec", "apt-get", "update"], timeout=600)
        else:
            ok, out, err = run_cmd(["pkcon", "refresh", "force", "-y"], timeout=600)
        return {"ok": ok, "message": "Metadata refreshed" if ok else (err or "failed")[:160], "backend": be}

    @classmethod
    def clean_caches(cls) -> Dict:
        be = cls.backend()
        cmds = {"dnf": ["pkexec", "dnf", "clean", "all"],
                "apt": ["pkexec", "apt-get", "clean"]}
        if be in cmds:
            run_cmd(cmds[be], timeout=300)
        run_cmd(["flatpak", "uninstall", "--unused", "-y"], timeout=120)
        run_cmd(["pkexec", "dnf", "clean", "all"], timeout=300)
        run_cmd(["pkexec", "apt-get", "clean"], timeout=300)
        return {"ok": True, "message": "Package caches cleaned"}


# ══════════════════════════════════════════════════════════════════════════════
# 2. FIREWALL LAYER (firewalld → ufw)
# ══════════════════════════════════════════════════════════════════════════════

class FirewallLayer:
    @staticmethod
    def backend() -> str:
        ok, out, _ = run_cmd(["firewall-cmd", "--state"], timeout=4)
        if ok and "running" in out:
            return "firewalld"
        ok, _, _ = run_cmd(["ufw", "status"], timeout=4)
        if ok:
            return "ufw"
        return "none"

    @staticmethod
    def status() -> Dict:
        be = FirewallLayer.backend()
        if be == "firewalld":
            ok, out, _ = run_cmd(["firewall-cmd", "--list-all"], timeout=5)
            zone = "public"
            okz, outz, _ = run_cmd(["firewall-cmd", "--get-default-zone"], timeout=4)
            if okz:
                zone = outz
            services, ports = [], []
            if ok and out:
                for line in out.splitlines():
                    l = line.strip()
                    if l.startswith("services:"):
                        services = [s for s in l.split(":", 1)[1].split() if s]
                    if l.startswith("ports:"):
                        ports = [p for p in l.split(":", 1)[1].split() if p]
            return {"backend": "firewalld", "active": True, "zone": zone,
                    "services": services, "ports": ports}
        if be == "ufw":
            ok, out, _ = run_cmd(["ufw", "status", "verbose"], timeout=5)
            return {"backend": "ufw", "active": bool(ok and "Status: active" in out),
                    "zone": "—", "services": [], "ports": []}
        return {"backend": "none", "active": False, "zone": "—", "services": [], "ports": []}

    @staticmethod
    def set_enabled(enabled: bool) -> bool:
        if FirewallLayer.backend() == "firewalld":
            cmd = ["pkexec", "firewall-cmd", "--add-service=ssh", "--permanent"] if enabled else \
                  ["pkexec", "firewall-cmd", "--shutdown"]
            if enabled:
                run_cmd(cmd, timeout=10)
                ok, _, _ = run_cmd(["pkexec", "systemctl", "enable", "--now", "firewalld"], timeout=20)
                run_cmd(["pkexec", "firewall-cmd", "--reload"], timeout=10)
                return ok
            ok, _, _ = run_cmd(cmd, timeout=10)
            return ok
        ok, _, _ = run_cmd(["pkexec", "ufw", "enable" if enabled else "disable"], timeout=10)
        return ok

    @staticmethod
    def add_service(service: str) -> bool:
        if FirewallLayer.backend() == "firewalld":
            ok, _, _ = run_cmd(["pkexec", "firewall-cmd", f"--add-service={service}",
                                "--permanent"], timeout=10)
            run_cmd(["pkexec", "firewall-cmd", "--reload"], timeout=10)
            return ok
        ok, _, _ = run_cmd(["pkexec", "ufw", "allow", service], timeout=10)
        return ok

    @staticmethod
    def remove_service(service: str) -> bool:
        if FirewallLayer.backend() == "firewalld":
            ok, _, _ = run_cmd(["pkexec", "firewall-cmd", f"--remove-service={service}",
                                "--permanent"], timeout=10)
            run_cmd(["pkexec", "firewall-cmd", "--reload"], timeout=10)
            return ok
        ok, _, _ = run_cmd(["pkexec", "ufw", "delete", "allow", service], timeout=10)
        return ok

    @staticmethod
    def list_known_services() -> List[str]:
        ok, out, _ = run_cmd(["firewall-cmd", "--get-services"], timeout=5)
        if ok and out:
            return sorted(out.split())
        return ["ssh", "http", "https", "ftp", "samba", "ipp", "mdns", "vnc-server",
                "libvirt", "syncthing", "torrent", "steam-streaming"]


# ══════════════════════════════════════════════════════════════════════════════
# 3. SOFTWARE SOURCES / REPOSITORIES (dnf repolist, copr, rpmfusion)
# ══════════════════════════════════════════════════════════════════════════════

class ReposAdapter:
    @staticmethod
    def list_repos() -> List[Dict]:
        repos = []
        ok, out, _ = run_cmd(["dnf", "repolist", "--all", "-v"], timeout=20) if _which("dnf") else (False, "", "")
        if ok and out:
            cur = {}
            for line in out.splitlines():
                if line.startswith("Repo-id"):
                    if cur:
                        repos.append(cur)
                    cur = {"id": line.split(":", 1)[1].strip(), "enabled": False}
                elif line.startswith("Repo-name") and cur:
                    cur["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("Repo-enabled") and cur:
                    cur["enabled"] = "enabled" in line
                elif line.startswith("Repo-mirrors") and cur and "baseurl" not in cur:
                    cur["url"] = line.split(":", 1)[1].strip()[:70]
                elif line.startswith("Repo-baseurl") and cur:
                    cur["url"] = line.split(":", 1)[1].strip()[:70]
            if cur:
                repos.append(cur)
        if not repos and _which("apt"):
            ok, out, _ = run_cmd(["bash", "-c", "grep -rhsE '^(deb|Types:)' /etc/apt/sources.list /etc/apt/sources.list.d/ 2>/dev/null | head -30"], timeout=10)
            if ok and out:
                for i, line in enumerate(out.splitlines()):
                    repos.append({"id": f"apt-{i}", "name": line[:60], "enabled": True, "url": line[:70]})
        if not repos:
            for remote in _flatpak_remotes():
                repos.append({"id": f"flatpak:{remote['name']}", "name": f"Flatpak remote: {remote['name']}",
                              "enabled": not remote.get("disabled", False), "url": remote.get("url", "")})
        return repos[:40]

    @staticmethod
    def set_repo_enabled(repo_id: str, enabled: bool) -> bool:
        if _which("dnf") and not repo_id.startswith(("apt-", "flatpak:")):
            verb = "enable" if enabled else "disable"
            ok, _, _ = run_cmd(["pkexec", "dnf", "config-manager", "--set-enabled" if enabled else "--set-disabled", repo_id], timeout=15)
            if ok:
                return True
            ok, _, _ = run_cmd(["pkexec", "dnf5", "config-manager", verb, repo_id], timeout=15)
            return ok
        if repo_id.startswith("flatpak:"):
            name = repo_id.split(":", 1)[1]
            arg = "--enable" if enabled else "--disable"
            ok, _, _ = run_cmd(["flatpak", "remote-modify", arg, name], timeout=15)
            return ok
        return False

    @staticmethod
    def get_rpmfusion_status() -> Dict:
        pkgs = PackageManager.list_installed("rpmfusion", 10)
        return {"installed": [p["name"] for p in pkgs],
                "free": any("free" in p["name"] for p in pkgs),
                "nonfree": any("nonfree" in p["name"] for p in pkgs)}

    @staticmethod
    def enable_rpmfusion(which: str = "free") -> Dict:
        be = PackageManager.backend()
        if be == "dnf":
            return PackageManager.install([f"rpmfusion-{which}-release"])
        return {"ok": False, "message": "dnf backend required"}


def _flatpak_remotes() -> List[Dict]:
    remotes = []
    ok, out, _ = run_cmd(["flatpak", "remotes", "--columns=name,url,options"], timeout=8)
    if ok and out:
        for line in out.splitlines()[1:]:
            parts = line.split("\t")
            if parts:
                remotes.append({"name": parts[0],
                                "url": parts[1] if len(parts) > 1 else "",
                                "disabled": len(parts) > 2 and "disabled" in parts[2]})
    return remotes


# ══════════════════════════════════════════════════════════════════════════════
# 4. UPDATES (dnf check-update / PackageKit / flatpak)
# ══════════════════════════════════════════════════════════════════════════════

class UpdatesAdapter:
    @staticmethod
    def check_updates() -> Dict:
        updates = []
        be = PackageManager.backend()
        if be == "dnf":
            ok, out, _ = run_cmd(["dnf", "check-update", "--quiet"], timeout=120)
            for line in (out or "").splitlines():
                m = re.match(r"^(\S+)\s+(\S+)\s+(\S+)$", line)
                if m and not line.startswith(("Last metadata", "Obsoleting", "Security:")):
                    updates.append({"name": m.group(1), "version": m.group(2), "repo": m.group(3)})
        elif _which("pkcon"):
            ok, out, _ = run_cmd(["pkcon", "get-updates"], timeout=60)
            for line in (out or "").splitlines():
                m = re.match(r"(\S+)\s+(\S+)\s+(\S+)\s+(.+)", line)
                if m:
                    updates.append({"name": m.group(1), "version": m.group(2), "repo": m.group(4)[:24]})
        # Flatpak updates
        ok, out, _ = run_cmd(["flatpak", "update", "--noninteractive", "--just-update" if False else ""], timeout=5)
        okf, outf, _ = run_cmd(["bash", "-c", "flatpak remote-ls --updates flathub --columns=application 2>/dev/null | head -20"], timeout=20)
        flatpak_updates = [l for l in (outf or "").splitlines() if l.strip()]
        return {"rpm": updates, "flatpak": flatpak_updates,
                "total": len(updates) + len(flatpak_updates),
                "backend": be}

    @staticmethod
    def apply_updates() -> Dict:
        be = PackageManager.backend()
        if be == "dnf":
            ok, out, err = run_cmd(["pkexec", "dnf", "upgrade", "--refresh", "-y"], timeout=1800)
            msg = [l for l in (out or "").splitlines() if "Upgraded" in l or "Installed" in l]
            return {"ok": ok, "message": msg[-1][:160] if msg else ("System up to date" if ok else (err or "")[:160])}
        if _which("pkcon"):
            ok, out, err = run_cmd(["pkcon", "update", "-y"], timeout=1800)
            return {"ok": ok, "message": "Update finished" if ok else (err or "")[:160]}
        return {"ok": False, "message": "No package backend"}

    @staticmethod
    def get_history(limit: int = 12) -> List[Dict]:
        hist = []
        ok, out, _ = run_cmd(["dnf", "history", "list", "--reverse"], timeout=20) if _which("dnf") else (False, "", "")
        if ok and out:
            for line in out.splitlines():
                m = re.match(r"\s*(\d+)\s+\|(.+?)\s+\|\s*(.+?)\s+\|", line)
                if m:
                    hist.append({"id": m.group(1), "date": m.group(2).strip()[:26], "action": m.group(3).strip()[:40]})
        if not hist and _which("apt"):
            ok, out, _ = run_cmd(["bash", "-c", "grep -E '^(Start-Date|Commandline)' /var/log/dpkg.log /var/log/dpkg.log.1 2>/dev/null | tail -40"], timeout=8)
            if ok and out:
                for line in out.splitlines():
                    if line.startswith("Start-Date"):
                        hist.append({"id": "—", "date": line.split()[1], "action": "apt transaction"})
        return hist[:limit]

    # dnf-automatic (unattended upgrades, Fedora-native)
    @staticmethod
    def get_auto_update_status() -> Dict:
        ok, out, _ = run_cmd(["systemctl", "is-enabled", "dnf-automatic.timer"], timeout=5)
        active_ok, _, _ = run_cmd(["systemctl", "is-active", "dnf-automatic.timer"], timeout=5)
        return {"supported": _which("dnf") is not None,
                "enabled": ok and "enabled" in (out or ""),
                "active": active_ok}

    @staticmethod
    def set_auto_update(enabled: bool) -> bool:
        verb = "enable --now" if enabled else "disable --now"
        ok, _, _ = run_cmd(["pkexec", "systemctl", *verb.split(), "dnf-automatic.timer"], timeout=15)
        return ok


# ══════════════════════════════════════════════════════════════════════════════
# 5. DRIVERS (GPU/kernel modules: akmod-nvidia, mesa, xorg-x11-drv-*)
# ══════════════════════════════════════════════════════════════════════════════

class DriversAdapter:
    @staticmethod
    def get_gpus() -> List[Dict]:
        gpus = []
        ok, out, _ = run_cmd(["lspci", "-nnk", "-d", "::0300"], timeout=8)
        ok2, out2, _2 = run_cmd(["lspci", "-nnk", "-d", "::0380"], timeout=8)
        raw = "\n".join(x for x in (out or "") + "\n" + (out2 or "") if x)
        blocks = re.split(r"\n(?=\S)", raw)
        for b in blocks:
            if "VGA" in b or "3D" in b or "Display" in b:
                name = next((l.split(":", 1)[1].strip() for l in b.splitlines() if "VGA" in l or "3D" in l or "Display" in l), "GPU")
                drv = re.search(r"Kernel driver in use:\s*(\S+)", b)
                mods = re.search(r"Kernel modules:\s*(.+)", b)
                gpus.append({"name": name[:70],
                             "driver": drv.group(1) if drv else "none",
                             "modules": mods.group(1).split() if mods else []})
        if not gpus:
            gpus = [{"name": "Integrated graphics (fallback)", "driver": "modesetting", "modules": []}]
        return gpus

    @staticmethod
    def get_driver_packages() -> List[Dict]:
        """Installed driver packages relevant on Fedora/Synthex."""
        wanted = ["xorg-x11-drv", "akmod-nvidia", "kmod-nvidia", "mesa", "vulkan",
                  "nvidia", "broadcom", "realtek", "iwl", "amd-gpu", "xf86-input"]
        found = {}
        for p in PackageManager.list_installed("", limit=4000):
            n = p["name"]
            if any(w in n for w in wanted):
                found[n] = p
        return list(found.values())[:30]

    @staticmethod
    def get_available_gpu_drivers() -> List[Dict]:
        gpus = DriversAdapter.get_gpus()
        amd = any("amd" in g["name"].lower() or "ati" in g["name"].lower() for g in gpus)
        nvidia = any("nvidia" in g["name"].lower() for g in gpus)
        intel = any("intel" in g["name"].lower() for g in gpus)
        options = []
        if nvidia:
            options += [
                {"pkg": "akmod-nvidia", "name": "NVIDIA proprietary (akmod)", "desc": "DKMS-style auto-built kernel module — recommended", "installed": any(p["name"] == "akmod-nvidia" for p in DriversAdapter.get_driver_packages())},
                {"pkg": "xorg-x11-drv-nouveau", "name": "Nouveau (open source)", "desc": "Community NVIDIA driver", "installed": True},
            ]
        if amd:
            options += [
                {"pkg": "mesa-vulkan-drivers", "name": "RADV Vulkan (Mesa)", "desc": "AMD open Vulkan — gaming recommended", "installed": any("mesa-vulkan" in p["name"] for p in DriversAdapter.get_driver_packages())},
                {"pkg": "xorg-x11-drv-amdgpu", "name": "AMDGPU (kernel)", "desc": "Default AMD graphics stack", "installed": True},
            ]
        if intel:
            options += [
                {"pkg": "intel-media-driver", "name": "Intel media (VA-API)", "desc": "Hardware video acceleration", "installed": any("intel-media" in p["name"] for p in DriversAdapter.get_driver_packages())},
                {"pkg": "mesa-vulkan-drivers", "name": "ANV Vulkan (Mesa)", "desc": "Intel Vulkan support", "installed": any("mesa-vulkan" in p["name"] for p in DriversAdapter.get_driver_packages())},
            ]
        return options

    @staticmethod
    def install_driver(pkg: str) -> Dict:
        return PackageManager.install([pkg])

    @staticmethod
    def get_firmware_status() -> Dict:
        ok, out, _ = run_cmd(["fwupdmgr", "get-updates"], timeout=20)
        if ok and out:
            n = len(re.findall(r"^│", out, re.M))
            return {"tool": "fwupd", "updates": n, "detail": out.splitlines()[0][:80] if out else ""}
        return {"tool": "fwupd" if _which("fwupdmgr") else "none", "updates": 0, "detail": ""}


# ══════════════════════════════════════════════════════════════════════════════
# 6. TIMESHIFT SNAPSHOTS (btrfs — Synthex default)
# ══════════════════════════════════════════════════════════════════════════════

class TimeshiftAdapter:
    @staticmethod
    def is_available() -> bool:
        return shutil.which("timeshift") is not None

    @staticmethod
    def list_snapshots() -> List[Dict]:
        if not TimeshiftAdapter.is_available():
            return []
        ok, out, _ = run_cmd(["timeshift", "--list", "--scripted"], timeout=20)
        snaps = []
        for line in (out or "").splitlines():
            m = re.match(r"\s*\d+\s+:\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(.*)", line)
            if m:
                snaps.append({"num": m.group(1), "type": m.group(2), "date": f"{m.group(3)} {m.group(4)}", "tag": m.group(5).strip() or "—", "desc": ""})
        if not snaps:
            for line in (out or "").splitlines():
                if ">" in line and "/" in line:
                    parts = [p.strip() for p in line.split(">") if p.strip()]
                    if len(parts) >= 4:
                        snaps.append({"num": parts[0], "type": parts[1], "date": parts[2][:22], "tag": parts[3] if len(parts) > 3 else "—", "desc": parts[4] if len(parts) > 4 else ""})
        # btrfs raw fallback
        if not snaps:
            ok2, out2, _ = run_cmd(["bash", "-c", "sudo -n btrfs subvolume list / 2>/dev/null | grep -i timeshift | head -20"], timeout=8)
            for line in (out2 or "").splitlines():
                m = re.search(r"path\s+(\S+)", line)
                if m:
                    snaps.append({"num": m.group(1).split("/")[-1], "type": "btrfs", "date": "—", "tag": "subvolume", "desc": m.group(1)})
        return snaps

    @staticmethod
    def create_snapshot(tag: str = "", desc: str = "") -> Dict:
        if not TimeshiftAdapter.is_available():
            return {"ok": False, "message": "timeshift not installed"}
        args = ["pkexec", "timeshift", "--create", "--scripted"]
        if tag:
            args += ["--tags", tag]
        if desc:
            args += ["--comments", desc[:80]]
        ok, out, err = run_cmd(args, timeout=300)
        return {"ok": ok, "message": "Snapshot created" if ok else (err or out or "failed")[:160]}

    @staticmethod
    def restore_snapshot(num: str) -> Dict:
        if not TimeshiftAdapter.is_available():
            return {"ok": False, "message": "timeshift not installed"}
        ok, out, err = run_cmd(["pkexec", "timeshift", "--restore", "--snapshot", num, "--scripted", "--yes"], timeout=600)
        return {"ok": ok, "message": "Restoration complete" if ok else (err or out or "failed")[:160]}

    @staticmethod
    def delete_snapshot(num: str) -> Dict:
        if not TimeshiftAdapter.is_available():
            return {"ok": False, "message": "timeshift not installed"}
        ok, out, err = run_cmd(["pkexec", "timeshift", "--delete", "--snapshot", num, "--scripted"], timeout=120)
        return {"ok": ok, "message": "Snapshot deleted" if ok else (err or "failed")[:160]}


# ══════════════════════════════════════════════════════════════════════════════
# 7. LOGIN SCREEN (SDDM-first, LightDM fallback)
# ══════════════════════════════════════════════════════════════════════════════

class LoginScreenAdapter:
    @staticmethod
    def detect_dm() -> str:
        ok, out, _ = run_cmd(["bash", "-c", "cat /etc/systemd/system/display-manager.service 2>/dev/null | sed 's/.*=//'"], timeout=5)
        dm = (out or "").strip()
        if "sddm" in dm:
            return "sddm"
        if "lightdm" in dm:
            return "lightdm"
        if "gdm" in dm:
            return "gdm"
        return dm or "unknown"

    @staticmethod
    def _conf() -> Path:
        Path("/etc/sddm.conf.d").mkdir(parents=True, exist_ok=True)
        return Path("/etc/sddm.conf.d/10-synthex.conf")

    @staticmethod
    def get_settings() -> Dict:
        dm = LoginScreenAdapter.detect_dm()
        conf = Path("/etc/sddm.conf") 
        confd = list(Path("/etc/sddm.conf.d").glob("*.conf")) if Path("/etc/sddm.conf.d").exists() else []
        text = ""
        for f in [conf, *confd]:
            if f.exists():
                text += f.read_text() + "\n"
        def get(section, key, default=""):
            m = re.search(rf"\[{section}\][^\[]*?{key}\s*=\s*(\S+)", text)
            return m.group(1) if m else default
        themes = LoginScreenAdapter.list_themes()
        return {
            "dm": dm,
            "theme": get("Theme", "Current", "breeze"),
            "themes": themes,
            "autologin_user": get("Autologin", "User", ""),
            "autologin_enabled": bool(get("Autologin", "User", "")),
            "cursor_theme": get("Theme", "CursorTheme", "default"),
        }

    @staticmethod
    def list_themes() -> List[str]:
        themes = []
        for d in ["/usr/share/sddm/themes", "/usr/share/lightdm-webkit/themes", "/usr/share/xgreeters"]:
            p = Path(d)
            if p.is_dir():
                themes += [t.name for t in p.iterdir() if t.is_dir()][:20]
        return sorted(set(themes)) or ["default"]

    @staticmethod
    def set_setting(section: str, key: str, value: str) -> bool:
        path = LoginScreenAdapter._conf()
        text = path.read_text() if path.exists() else ""
        block_m = re.search(rf"(\[{section}\])", text)
        if block_m and re.search(rf"\[{section}\][^\[]*?{key}\s*=", text):
            text = re.sub(rf"(\[{section}\][^\[]*?{key}\s*=).*", rf"\1{value}", text)
        elif block_m:
            text = text.replace(block_m.group(1), f"[{section}]\n{key}={value}", 1)
        else:
            text += f"\n[{section}]\n{key}={value}\n"
        tmp = Path("/tmp/synthex-sddm.conf")
        tmp.write_text(text)
        ok, _, _ = run_cmd(["pkexec", "cp", str(tmp), str(path)], timeout=10)
        return ok

    @staticmethod
    def set_autologin(user: str, enabled: bool) -> bool:
        if enabled and user:
            LoginScreenAdapter.set_setting("Autologin", "User", user)
            return LoginScreenAdapter.set_setting("Autologin", "Session", "cinnamon.desktop")
        LoginScreenAdapter.set_setting("Autologin", "User", "")
        return True


# ══════════════════════════════════════════════════════════════════════════════
# 8. THUNDERBOLT (bolt)
# ══════════════════════════════════════════════════════════════════════════════

class ThunderboltAdapter:
    @staticmethod
    def available() -> bool:
        return _which("boltctl") is not None or Path("/sys/bus/thunderbolt").is_dir()

    @staticmethod
    def devices() -> List[Dict]:
        devs = []
        if Path("/sys/bus/thunderbolt/devices").is_dir():
            for d in Path("/sys/bus/thunderbolt/devices").iterdir():
                name_f = d / "device_name"
                auth_f = d / "authorized"
                if name_f.exists():
                    try:
                        name = name_f.read_text().strip() or d.name
                        auth = auth_f.read_text().strip() == "1" if auth_f.exists() else False
                        devs.append({"name": name, "id": d.name, "authorized": auth})
                    except Exception:
                        pass
        if _which("boltctl"):
            ok, out, _ = run_cmd(["boltctl", "list"], timeout=6)
            for block in (out or "").split("\n\n"):
                m = re.search(r"●\s+(.+)", block)
                if m:
                    devs.append({"name": m.group(1).strip(), "id": m.group(1).split()[0], "authorized": "authorized" in block})
        return devs

    @staticmethod
    def authorize(uuid: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "boltctl", "authorize", uuid], timeout=10)
        return ok

    @staticmethod
    def security_level() -> str:
        if _which("boltctl"):
            ok, out, _ = run_cmd(["boltctl", "power"], timeout=5)
            if ok and out:
                m = re.search(r"security level:\s*(\S+)", out)
                if m:
                    return m.group(1)
        return "unknown"


# ══════════════════════════════════════════════════════════════════════════════
# 9. COLOR MANAGEMENT (colord)
# ══════════════════════════════════════════════════════════════════════════════

class ColorAdapter:
    @staticmethod
    def devices() -> List[Dict]:
        devs = []
        ok, out, _ = run_cmd(["colormgr", "get-devices"], timeout=8)
        for block in (out or "").split("\n\n"):
            if not block.strip():
                continue
            m_id = re.search(r"([0-9a-f-]{36})", block)
            m_model = re.search(r"model:\s*(.+)", block)
            m_kind = re.search(r"type:\s*(.+)", block)
            m_prof = re.search(r"default profile:\s*(.+)", block)
            if m_id:
                devs.append({"id": m_id.group(1), "model": (m_model.group(1).strip() if m_model else "Display")[:48],
                             "kind": m_kind.group(1).strip() if m_kind else "display",
                             "profile": m_prof.group(1).strip()[:48] if m_prof else "—"})
        return devs

    @staticmethod
    def profiles() -> List[Dict]:
        profs = []
        ok, out, _ = run_cmd(["colormgr", "get-profiles"], timeout=8)
        for block in (out or "").split("\n\n"):
            m_id = re.search(r"([0-9a-f-]{36})", block)
            m_t = re.search(r"title:\s*(.+)", block)
            if m_id:
                profs.append({"id": m_id.group(1), "title": (m_t.group(1).strip() if m_t else "Profile")[:48]})
        return profs

    @staticmethod
    def assign_profile(device_id: str, profile_id: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "colormgr", "device-add-profile", device_id, profile_id], timeout=10)
        ok2, _, _ = run_cmd(["pkexec", "colormgr", "device-make-profile-default", device_id, profile_id], timeout=10)
        return ok or ok2


# ══════════════════════════════════════════════════════════════════════════════
# 10. GRAPHICS TABLET (Wacom / libinput)
# ══════════════════════════════════════════════════════════════════════════════

class GraphicsTabletAdapter:
    @staticmethod
    def tablets() -> List[Dict]:
        tabs = []
        ok, out, _ = run_cmd(["xinput", "list", "--name-only"], timeout=6)
        for name in (out or "").splitlines():
            if any(k in name for k in ("Wacom", "Tablet", "Pen", "Stylus", "HID_TABLET")):
                tabs.append({"name": name.strip()[:60], "connected": True})
        return tabs

    @staticmethod
    def stylus_settings(name: str) -> Dict:
        return {"pressure_curve": get_tablet_gsetting("pressure-curve"),
                "pressure_feel": get_tablet_gsetting("pressure-feel"),
                "button_mapping": get_tablet_gsetting("button-mapping")}

    @staticmethod
    def set_stylus(key: str, value) -> bool:
        return safe_set_gsetting("org.cinnamon.settings-daemon.plugins.csdwacom", f"stylus-{key}", value)


def get_tablet_gsetting(key: str):
    return _gget("org.cinnamon.settings-daemon.plugins.csdwacom", f"stylus-{key}", None)


# ══════════════════════════════════════════════════════════════════════════════
# 11. SCREENSAVER & LOCK
# ══════════════════════════════════════════════════════════════════════════════

class ScreensaverAdapter:
    SCHEMA = "org.cinnamon.desktop.screensaver"

    @staticmethod
    def get(key, default=None):
        return _gget(ScreensaverAdapter.SCHEMA, key, default)

    @staticmethod
    def set(key, value) -> bool:
        return safe_set_gsetting(ScreensaverAdapter.SCHEMA, key, value)

    @staticmethod
    def lock_enabled() -> bool:
        s = get_gsettings("org.cinnamon.desktop.lockdown")
        if s:
            return not s.get_boolean("disable-lock-screen")
        return True

    @staticmethod
    def idle_settings() -> Dict:
        return {"idle_activation": ScreensaverAdapter.get("idle-activation-enabled", True),
                "lock_delay": ScreensaverAdapter.get("lock-delay", 0),
                "lock_enabled": ScreensaverAdapter.get("lock-enabled", False),
                "ubuntu_lock_on_suspend": ScreensaverAdapter.get("ubuntu-lock-on-suspend", True),
                "allow_shortcuts": ScreensaverAdapter.get("allow-shortcuts", False),
                "show_clock": ScreensaverAdapter.get("show-clock", True),
                "use_custom_format": ScreensaverAdapter.get("use-custom-date-format", False),
                "date_format": ScreensaverAdapter.get("date-format", "%A %b %e"),
                "idle_delay": ScreensaverAdapter._session_idle()}

    @staticmethod
    def _session_idle() -> int:
        v = _gget("org.cinnamon.desktop.session", "idle-delay", None)
        return int(v) if v is not None else 0

    @staticmethod
    def set_idle_delay(seconds: int) -> bool:
        return safe_set_gsetting("org.cinnamon.desktop.session", "idle-delay", int(seconds))

    @staticmethod
    def lock_now() -> bool:
        ok, _, _ = run_cmd(["cinnamon-screensaver-command", "-l"], timeout=5)
        if not ok:
            run_cmd(["loginctl", "lock-session"], timeout=5)
        return True


# ══════════════════════════════════════════════════════════════════════════════
# 12. STARTUP APPLICATIONS (XDG autostart)
# ══════════════════════════════════════════════════════════════════════════════

class AutostartAdapter:
    USER_DIR = HOME / ".config" / "autostart"

    @staticmethod
    def list_autostarts() -> List[Dict]:
        apps = []
        seen = set()
        for d in ["/etc/xdg/autostart", str(AutostartAdapter.USER_DIR)]:
            for f in sorted(glob.glob(os.path.join(d, "*.desktop"))):
                try:
                    content = Path(f).read_text()
                    name = (re.search(r"^Name=(.+)", content, re.M) or [None, Path(f).stem])[1].strip()
                    icon = (re.search(r"^Icon=(.+)", content, re.M) or [None, "application-x-executable"])[1].strip()
                    hidden = re.search(r"^Hidden=true", content, re.M) is not None
                    nogen = re.search(r"^X-GNOME-Autostart-enabled=false", content, re.M) is not None
                    key = Path(f).stem
                    if key in seen:
                        continue
                    seen.add(key)
                    apps.append({"key": key, "name": name[:44], "icon": icon[:40],
                                 "enabled": not (hidden or nogen),
                                 "user": d == str(AutostartAdapter.USER_DIR)})
                except Exception:
                    continue
        return apps

    @staticmethod
    def set_enabled(key: str, enabled: bool) -> bool:
        # User override file controls both system and user autostarts
        AutostartAdapter.USER_DIR.mkdir(parents=True, exist_ok=True)
        src = None
        for d in ["/etc/xdg/autostart", str(AutostartAdapter.USER_DIR)]:
            p = Path(d) / f"{key}.desktop"
            if p.exists():
                src = p
                break
        target = AutostartAdapter.USER_DIR / f"{key}.desktop"
        text = src.read_text() if src else f"[Desktop Entry]\nType=Application\nName={key}\n"
        if enabled:
            text = re.sub(r"^Hidden=true", "Hidden=false", text, flags=re.M)
            if "Hidden=" not in text:
                text += "\nHidden=false\n"
            if "X-GNOME-Autostart-enabled=false" in text:
                text = re.sub(r"^X-GNOME-Autostart-enabled=false", "X-GNOME-Autostart-enabled=true", text, flags=re.M)
        else:
            text = re.sub(r"^Hidden=(true|false)", "Hidden=true", text, flags=re.M)
            if "Hidden=" not in text:
                text += "\nHidden=true\n"
        target.write_text(text)
        return True

    @staticmethod
    def add_custom(name: str, command: str, comment: str = "") -> bool:
        AutostartAdapter.USER_DIR.mkdir(parents=True, exist_ok=True)
        key = re.sub(r"\W+", "-", name.lower()).strip("-")
        f = AutostartAdapter.USER_DIR / f"synthex-custom-{key}.desktop"
        f.write_text(f"[Desktop Entry]\nType=Application\nName={name}\nExec={command}\n"
                     f"Comment={comment}\nX-GNOME-Autostart-enabled=true\n")
        return True

    @staticmethod
    def remove(key: str) -> bool:
        p = AutostartAdapter.USER_DIR / f"{key}.desktop"
        if p.exists() and p.name.startswith("synthex-custom-"):
            p.unlink()
            return True
        # For system entries: disable instead of delete
        return AutostartAdapter.set_enabled(key, False)


# ══════════════════════════════════════════════════════════════════════════════
# 13. PREFERRED APPLICATIONS (xdg-mime / xdg-settings)
# ══════════════════════════════════════════════════════════════════════════════

class PreferredAppsAdapter:
    ROLES = [
        ("web-browser", "Web Browser", "x-scheme-handler/http"),
        ("mail-reader", "Email Client", "x-scheme-handler/mailto"),
        ("text-editor", "Text Editor", "text/plain"),
        ("image-viewer", "Image Viewer", "image/png"),
        ("video-player", "Video Player", "video/mp4"),
        ("audio-player", "Music Player", "audio/mpeg"),
        ("calendar", "Calendar", "text/calendar"),
        ("pdf-viewer", "Document Viewer", "application/pdf"),
        ("file-manager", "File Manager", "inode/directory"),
        ("terminal", "Terminal", None),
    ]

    @staticmethod
    def get_default(role: str, mime: Optional[str]) -> str:
        if role == "terminal":
            s = get_gsettings("org.cinnamon.desktop.default-applications.terminal")
            if s:
                try:
                    return s.get_string("exec") or ""
                except Exception:
                    pass
            return ""
        if mime:
            ok, out, _ = run_cmd(["xdg-mime", "query", "default", mime], timeout=5)
            if ok and out:
                return out.replace(".desktop", "")
        return ""

    @staticmethod
    def set_default(role: str, mime: Optional[str], value: str) -> bool:
        if role == "terminal":
            return safe_set_gsetting("org.cinnamon.desktop.default-applications.terminal", "exec", value)
        if mime:
            ok, _, _ = run_cmd(["xdg-mime", "default", f"{value}.desktop", mime], timeout=5)
            for extra in _related_mimes(mime):
                run_cmd(["xdg-mime", "default", f"{value}.desktop", extra], timeout=5)
            return ok
        return False

    @staticmethod
    def candidates(role: str, mime: Optional[str]) -> List[Dict]:
        apps = []
        dirs = [HOME / ".local/share/applications", Path("/usr/share/applications")]
        for d in dirs:
            if not d.is_dir():
                continue
            for f in d.glob("*.desktop"):
                try:
                    text = f.read_text()
                except Exception:
                    continue
                if role == "terminal" and ("Terminal=true" in text or not any(k in text for k in ("TerminalEmulator", "terminal"))):
                    continue
                nm = re.search(r"^Name=(.+)", text, re.M)
                cats = re.search(r"^Categories=(.+)", text, re.M)
                if role == "web-browser" and cats and not any(c in cats.group(1) for c in ("WebBrowser", "Network")):
                    continue
                apps.append({"id": f.stem, "name": (nm.group(1).strip() if nm else f.stem)[:40]})
        # de-dup
        seen, out = set(), []
        for a in apps:
            if a["id"] not in seen:
                seen.add(a["id"])
                out.append(a)
        return out[:24]


def _related_mimes(mime: str) -> List[str]:
    fam = {
        "x-scheme-handler/http": ["x-scheme-handler/https", "text/html"],
        "image/png": ["image/jpeg", "image/gif", "image/webp", "image/bmp", "image/svg+xml", "image/tiff"],
        "video/mp4": ["video/x-matroska", "video/webm", "video/x-msvideo", "video/quicktime"],
        "audio/mpeg": ["audio/flac", "audio/x-wav", "audio/ogg", "audio/x-vorbis+ogg"],
        "application/pdf": ["application/epub+zip", "application/x-pdf"],
        "text/plain": ["text/x-python", "text/x-csrc", "text/markdown", "text/x-log"],
        "inode/directory": ["x-scheme-handler/trash"],
    }
    return fam.get(mime, [])


# ══════════════════════════════════════════════════════════════════════════════
# 14. WINDOWS / WORKSPACES / HOT CORNERS / EFFECTS (Muffin + Cinnamon)
# ══════════════════════════════════════════════════════════════════════════════

class WindowsAdapter:
    SCHEMA = "org.cinnamon.desktop.wm.preferences"

    @staticmethod
    def get(key, default=None):
        s = get_gsettings(WindowsAdapter.SCHEMA)
        if s:
            try:
                return s.get_value(key).unpack()
            except Exception:
                pass
        return default

    @staticmethod
    def set(key, value) -> bool:
        return safe_set_gsetting(WindowsAdapter.SCHEMA, key, value)

    @staticmethod
    def all() -> Dict:
        return {k: WindowsAdapter.get(k, d) for k, d in [
            ("action-double-click-titlebar", "toggle-shade"),
            ("action-middle-click-titlebar", "lower"),
            ("action-right-click-titlebar", "menu"),
            ("focus-mode", "click"),
            ("auto-raise", False),
            ("raise-on-click", True),
            ("titlebar-font", "Sans Bold 10"),
            ("num-workspaces", 4),
            ("workspace-cycle", True),
            ("placement-mode", "automatic"),
        ]}


class WorkspacesAdapter:
    SCHEMA = "org.cinnamon"
    WS_SCHEMA = "org.cinnamon.desktop.wm.preferences"

    @staticmethod
    def get_osd() -> bool:
        return bool(_gget("org.cinnamon", "workspace-osd-visible", True))

    @staticmethod
    def set_osd(v: bool) -> bool:
        return safe_set_gsetting("org.cinnamon", "workspace-osd-visible", v)

    @staticmethod
    def set_count(n: int) -> bool:
        return safe_set_gsetting(WorkspacesAdapter.WS_SCHEMA, "num-workspaces", int(n))

    @staticmethod
    def get_count() -> int:
        v = _gget(WorkspacesAdapter.WS_SCHEMA, "num-workspaces", None)
        return int(v) if v is not None else 4

    @staticmethod
    def dynamic() -> bool:
        return bool(_gget("org.cinnamon.muffin", "dynamic-workspaces", False))

    @staticmethod
    def set_dynamic(v: bool) -> bool:
        return safe_set_gsetting("org.cinnamon.muffin", "dynamic-workspaces", v)


class HotCornersAdapter:
    SCHEMA = "org.cinnamon"

    @staticmethod
    def _get(key, default=None):
        if key.endswith("list"):
            v = _gget(HotCornersAdapter.SCHEMA, key, None)
            return v if v is not None else default
        return _gget(HotCornersAdapter.SCHEMA, key, default)

    @staticmethod
    def settings() -> Dict:
        return {
            "enabled": HotCornersAdapter._get("hotcorners-enabled", True),
            "tl": HotCornersAdapter._get("overview-corner", ""),  # top-left overview
            "tr": HotCornersAdapter._get("workspace-osd-visible", True),
            "visible": not HotCornersAdapter._get("panel-autohide", False),
        }

    @staticmethod
    def set_enabled(v: bool) -> bool:
        return safe_set_gsetting(HotCornersAdapter.SCHEMA, "hotcorners-enabled", v)

    @staticmethod
    def corner_actions() -> List[str]:
        return ["expo", "scale", "desktop", "workspace-down", "workspace-up", "none"]


class EffectsAdapter:
    SCHEMA = "org.cinnamon.muffin"

    @staticmethod
    def _get(key, default):
        return _gget(EffectsAdapter.SCHEMA, key, default)

    @staticmethod
    def all() -> Dict:
        return {k: EffectsAdapter._get(k, d) for k, d in [
            ("compositing-enabled", True),
            ("compositing-fast-alt-tab", True),
            ("unredirect-fullscreen-windows", True),
            ("desktop-effects-on-dialogs", False),
            ("desktop-effects", True),
            ("desktop-effects-workspace", "scale"),
            ("desktop-effects-mapping", "fade"),
            ("close-window-effect", "scale"),
            ("minimize-window-effect", "traditional"),
            ("unminimize-window-effect", "none"),
            ("tile-hud-threshold", 25),
            ("shadow-radius", 6),
            ("shadow-opacity", 0.45),
        ]}

    @staticmethod
    def set(key, value) -> bool:
        return safe_set_gsetting(EffectsAdapter.SCHEMA, key, value)


# ══════════════════════════════════════════════════════════════════════════════
# 15. EXTENSIONS / APPLETS / DESKLETS (Cinnamon xlets)
# ══════════════════════════════════════════════════════════════════════════════

class ExtensionsAdapter:
    KINDS = {"extensions": "extensions", "applets": "applets", "desklets": "desklets", "themes": "themes"}

    @staticmethod
    def _dirs(kind: str) -> List[Path]:
        return [HOME / ".local/share/cinnamon" / kind, Path(f"/usr/share/cinnamon/{kind}")]

    @staticmethod
    def list_installed(kind: str = "applets") -> List[Dict]:
        items = []
        for d in ExtensionsAdapter._dirs(kind):
            if not d.is_dir():
                continue
            for xdir in sorted(d.iterdir()):
                if xdir.is_dir():
                    name, desc, icon = xdir.name, "", "application-x-addon"
                    meta = xdir / "metadata.json"
                    if meta.exists():
                        try:
                            import json
                            m = json.loads(meta.read_text())
                            name = m.get("name", name)
                            desc = m.get("description", "")[:60]
                            icon = m.get("icon", icon)
                        except Exception:
                            pass
                    items.append({"uuid": xdir.name, "name": name[:40], "desc": desc, "icon": icon[:36]})
        return items

    @staticmethod
    def enabled_keys(kind: str = "applets") -> List[str]:
        s = get_gsettings("org.cinnamon")
        if s:
            try:
                return list(s.get_strv(f"enabled-{kind}"))
            except Exception:
                pass
        return []

    @staticmethod
    def is_enabled(kind: str, uuid: str) -> bool:
        return uuid in ExtensionsAdapter.enabled_keys(kind) or \
            any(e.endswith(f":{uuid}") for e in ExtensionsAdapter.enabled_keys(kind))

    @staticmethod
    def set_enabled(kind: str, uuid: str, enabled: bool) -> bool:
        s = get_gsettings("org.cinnamon")
        if not s:
            return False
        cur = list(s.get_strv(f"enabled-{kind}"))
        if enabled:
            if uuid not in cur:
                cur.append(uuid)
        else:
            cur = [c for c in cur if not c.endswith(f":{uuid}") and c != uuid]
        s.set_strv(f"enabled-{kind}", cur)
        return True


# ══════════════════════════════════════════════════════════════════════════════
# 16. GESTURES (touchegg + cinnamon gestures schema)
# ══════════════════════════════════════════════════════════════════════════════

class GesturesAdapter:
    SCHEMA = "org.cinnamon.gestures"

    @staticmethod
    def available() -> bool:
        return _which("touchegg") is not None

    @staticmethod
    def _get(key, default):
        return _gget(GesturesAdapter.SCHEMA, key, default)

    @staticmethod
    def settings() -> Dict:
        return {
            "enabled": GesturesAdapter._get("enabled", True),
            "swipe_down_fullscreen": GesturesAdapter._get("swipe-down-fullscreen", False),
            "pinch_in": GesturesAdapter._get("pinch-in", "zoom"),
            "pinch_out": GesturesAdapter._get("pinch-out", "zoom"),
            "swipe_up_workspace": True,
            "touchegg_running": GesturesAdapter.available(),
        }

    @staticmethod
    def set(key, value) -> bool:
        return safe_set_gsetting(GesturesAdapter.SCHEMA, key, value)


# ══════════════════════════════════════════════════════════════════════════════
# 17. INPUT METHOD (IBus / fcitx)
# ══════════════════════════════════════════════════════════════════════════════

class InputMethodAdapter:
    @staticmethod
    def available_engines() -> List[Dict]:
        engines = []
        if _which("ibus"):
            ok, out, _ = run_cmd(["ibus", "list-engine"], timeout=6)
            cur_lang = ""
            for line in (out or "").splitlines():
                m = re.match(r"(\S+)\s+-\s+(.+)", line.strip())
                if m:
                    engines.append({"name": m.group(1), "lang": cur_lang, "desc": m.group(2)[:40]})
                elif line.startswith("Language:"):
                    cur_lang = line.split(":", 1)[1].strip()[:20]
        if _which("fcitx5"):
            engines.append({"name": "fcitx5", "lang": "multi", "desc": "Fcitx5 input method framework"})
        return engines or [{"name": "ibus", "lang": "simple", "desc": "IBus (installed)"}]

    @staticmethod
    def current() -> str:
        s = get_gsettings("org.cinnamon.desktop.interface")
        if s:
            try:
                v = s.get_string("gtk-im-module")
                if v and v != "gtk-im-context-simple":
                    return v
            except Exception:
                pass
        return os.environ.get("GTK_IM_MODULE", "simple")

    @staticmethod
    def set_current(engine: str) -> bool:
        ok = safe_set_gsetting("org.cinnamon.desktop.interface", "gtk-im-module", engine)
        safe_set_gsetting("org.cinnamon.settings-daemon.peripherals.input-devices", "input-method", engine)
        return ok

    @staticmethod
    def sources() -> List[str]:
        s = get_gsettings("org.cinnamon.desktop.input-sources")
        if s:
            try:
                return list(s.get_strv("sources"))
            except Exception:
                pass
        return []

    @staticmethod
    def set_sources(srcs: List[str]) -> bool:
        return safe_set_gsetting("org.cinnamon.desktop.input-sources", "sources", srcs)


# ══════════════════════════════════════════════════════════════════════════════
# 18. FONTS (fontconfig)
# ══════════════════════════════════════════════════════════════════════════════

class FontsAdapter:
    @staticmethod
    def families() -> List[str]:
        fams = set()
        ok, out, _ = run_cmd(["fc-list", ":", "family"], timeout=8)
        for line in (out or "").splitlines():
            for f in line.split(","):
                f = f.strip()
                if f:
                    fams.add(f)
        return sorted(fams)

    @staticmethod
    def current_fonts() -> Dict:
        s = get_gsettings("org.cinnamon.desktop.interface")
        out = {}
        if s:
            for key, label in [("font-name", "interface"), ("document-font-name", "document")]:
                try:
                    out[label] = s.get_string(key)
                except Exception:
                    pass
        wm = get_gsettings("org.cinnamon.desktop.wm.preferences")
        if wm:
            try:
                out["window_title"] = wm.get_string("titlebar-font")
            except Exception:
                pass
        mon = get_gsettings("org.cinnamon.desktop.interface")
        if mon:
            try:
                out["monospace"] = mon.get_string("monospace-font-name")
            except Exception:
                pass
        return out

    @staticmethod
    def set_font(which: str, font: str) -> bool:
        mapping = {
            "interface": ("org.cinnamon.desktop.interface", "font-name"),
            "document": ("org.cinnamon.desktop.interface", "document-font-name"),
            "window_title": ("org.cinnamon.desktop.wm.preferences", "titlebar-font"),
            "monospace": ("org.cinnamon.desktop.interface", "monospace-font-name"),
        }
        if which in mapping:
            schema, key = mapping[which]
            return safe_set_gsetting(schema, key, font)
        return False

    @staticmethod
    def install_font_file(path: str) -> Dict:
        dest = HOME / ".local/share/fonts"
        dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy(path, str(dest / Path(path).name))
            run_cmd(["fc-cache", "-f", str(dest)], timeout=15)
            return {"ok": True, "message": f"{Path(path).name} installed"}
        except Exception as e:
            return {"ok": False, "message": str(e)[:120]}

    @staticmethod
    def antialias_settings() -> Dict:
        keys = ["antialiasing", "hinting", "dpi"]
        out = {}
        s = get_gsettings("org.cinnamon.settings-daemon.plugins.xsettings")
        if s:
            for k in keys:
                try:
                    out[k] = s.get_value(k).unpack()
                except Exception:
                    pass
        return out or {"antialiasing": "rgba", "hinting": "slight", "dpi": 0}

    @staticmethod
    def set_antialias(key: str, value) -> bool:
        return safe_set_gsetting("org.cinnamon.settings-daemon.plugins.xsettings", key, value)


# ══════════════════════════════════════════════════════════════════════════════
# 19. BACKGROUNDS / WALLPAPER + SLIDESHOW
# ══════════════════════════════════════════════════════════════════════════════

class BackgroundsAdapter:
    SCHEMA = "org.cinnamon.desktop.background"

    @staticmethod
    def current() -> Dict:
        s = get_gsettings(BackgroundsAdapter.SCHEMA)
        out = {"picture_uri": "", "mode": "wallpaper"}
        if s:
            try:
                out["picture_uri"] = s.get_string("picture-uri")
            except Exception:
                pass
        slide = get_gsettings("org.cinnamon.desktop.background.slideshow")
        if slide:
            try:
                out["slideshow_enabled"] = slide.get_boolean("slideshow-enabled")
                out["delay"] = slide.get_int("delay")
            except Exception:
                pass
        return out

    @staticmethod
    def list_wallpapers() -> List[Dict]:
        walls = []
        pats = ["/usr/share/backgrounds/**/*.{jpg,jpeg,png,webp}", "svg",
                "/usr/share/wallpapers/**/*.{jpg,jpeg,png}",
                str(HOME / ".local/share/backgrounds/**/*.{jpg,jpeg,png,webp}"),
                str(HOME / "linux-synthex/branding/wallpaper/*.svg")]
        seen = set()
        import itertools
        for d in ["/usr/share/backgrounds", "/usr/share/wallpapers",
                  str(HOME / ".local/share/backgrounds"), str(HOME / "linux-synthex/branding/wallpaper")]:
            p = Path(d)
            if p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".svg") and f.name not in seen:
                        seen.add(f.name)
                        walls.append({"name": f.stem.replace("_", " ").title()[:36], "path": str(f)})
        return walls[:60]

    @staticmethod
    def set_wallpaper(path: str) -> bool:
        uri = f"file://{path}"
        ok = safe_set_gsetting(BackgroundsAdapter.SCHEMA, "picture-uri", uri)
        return ok

    @staticmethod
    def set_slideshow(enabled: bool, delay: int = 300, folder: str = "") -> bool:
        schema = "org.cinnamon.desktop.background.slideshow"
        ok = safe_set_gsetting(schema, "slideshow-enabled", enabled)
        if enabled:
            safe_set_gsetting(schema, "delay", int(delay))
            if folder:
                safe_set_gsetting(schema, "image-source", f"directory://{folder}")
        return ok


# ══════════════════════════════════════════════════════════════════════════════
# 20. PANEL SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

class PanelAdapter:
    SCHEMA = "org.cinnamon"

    @staticmethod
    def _get(key, default=None, type_=None):
        v = _gget(PanelAdapter.SCHEMA, key, None)
        if v is None:
            return default
        if type_ == "b":
            return bool(v)
        if type_ == "i":
            return int(v)
        return v

    @staticmethod
    def settings() -> Dict:
        return {
            "autohide": PanelAdapter._get("panel-autohide", "false"),
            "showdelay": PanelAdapter._get("panel-show-delay", 0),
            "hidedelay": PanelAdapter._get("panel-hide-delay", 0),
            "height": PanelAdapter._get("panel-resizable", True, "b"),
            "intelligent_hide": False,
            "zones": PanelAdapter._get("panel-edit-mode", False, "b"),
        }

    @staticmethod
    def panel_heights() -> List[int]:
        return [24, 28, 32, 36, 40, 44, 48]

    @staticmethod
    def set_autohide(mode: str) -> bool:
        return safe_set_gsetting(PanelAdapter.SCHEMA, "panel-autohide", mode)

    @staticmethod
    def set_desktop_names(names: List[str]) -> bool:
        return safe_set_gsetting(PanelAdapter.SCHEMA, "panels-autohide", names)


# ══════════════════════════════════════════════════════════════════════════════
# 21. POWER/BUTTON ACTIONS (logind + cinnamon settings daemon)
# ══════════════════════════════════════════════════════════════════════════════

class ActionsAdapter:
    @staticmethod
    def lid_action() -> str:
        ok, out, _ = run_cmd(["bash", "-c", "grep -E '^HandleLidSwitch(=.*)?$' /etc/systemd/logind.conf | tail -1"], timeout=5)
        if ok and "=" in (out or ""):
            return out.split("=")[1].strip()
        return "suspend"

    @staticmethod
    def power_button_action() -> str:
        ok, out, _ = run_cmd(["bash", "-c", "grep -E '^HandlePowerKey' /etc/systemd/logind.conf | tail -1"], timeout=5)
        if ok and "=" in (out or ""):
            return out.split("=")[1].strip()
        return "poweroff"

    @staticmethod
    def set_lid_action(action: str) -> bool:
        return _set_logind("HandleLidSwitch", action)

    @staticmethod
    def set_power_button_action(action: str) -> bool:
        return _set_logind("HandlePowerKey", action)


def _set_logind(key: str, value: str) -> bool:
    """Writes a drop-in override (never edits the vendor file)."""
    dropin_dir = Path("/etc/systemd/logind.conf.d")
    dropin = dropin_dir / "10-synthex-settings.conf"
    dropin_dir.mkdir(parents=True, exist_ok=True)
    text = dropin.read_text() if dropin.exists() else "[Login]\n"
    if re.search(rf"^{key}=", text, re.M):
        text = re.sub(rf"^{key}=.*", f"{key}={value}", text, flags=re.M)
    else:
        text += f"{key}={value}\n"
    tmp = Path("/tmp/synthex-logind.conf")
    tmp.write_text(text)
    ok, _, _ = run_cmd(["pkexec", "cp", str(tmp), str(dropin)], timeout=10)
    run_cmd(["pkexec", "systemctl", "kill", "-s", "HUP", "systemd-logind"], timeout=10)
    return ok


# ══════════════════════════════════════════════════════════════════════════════
# 22. ACCOUNT DETAILS (chfn fields, groups, avatar)
# ══════════════════════════════════════════════════════════════════════════════

class AccountDetailsAdapter:
    @staticmethod
    def current() -> Dict:
        import pwd
        u = pwd.getpwuid(os.getuid())
        groups = []
        ok, out, _ = run_cmd(["id", "-nG"], timeout=4)
        if ok and out:
            groups = out.split()
        return {
            "username": u.pw_name,
            "full_name": u.pw_gecos.split(",")[0],
            "home": u.pw_dir,
            "shell": u.pw_shell,
            "uid": u.pw_uid,
            "groups": groups,
            "is_admin": "wheel" in groups or "sudo" in groups,
        }

    @staticmethod
    def set_full_name(name: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "usermod", "-c", f"{name}", os.environ.get("USER", "")], timeout=8)
        return ok

    @staticmethod
    def set_shell(shell: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "usermod", "-s", shell, os.environ.get("USER", "")], timeout=8)
        return ok

    @staticmethod
    def available_shells() -> List[str]:
        try:
            return [l.strip() for l in Path("/etc/shells").read_text().splitlines() if l.strip() and not l.startswith("#")]
        except Exception:
            return ["/bin/bash", "/usr/bin/fish", "/usr/bin/zsh"]

    @staticmethod
    def avatars() -> List[str]:
        p = Path("/var/lib/AccountsService/icons")
        if p.is_dir():
            return [str(f) for f in p.iterdir()][:20]
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 23. NIGHT LIGHT (redshift/color temperature)
# ══════════════════════════════════════════════════════════════════════════════

class NightLightAdapter:
    SCHEMA = "org.cinnamon.settings-daemon.plugins.color"

    @staticmethod
    def _get(key, default):
        return _gget(NightLightAdapter.SCHEMA, key, default)

    @staticmethod
    def settings() -> Dict:
        return {
            "enabled": NightLightAdapter._get("night-light-enabled", False),
            "temperature": NightLightAdapter._get("night-light-temperature", 4500),
            "auto_schedule": NightLightAdapter._get("night-light-schedule-automatic", True),
            "schedule_from": NightLightAdapter._get("night-light-schedule-from", 20.0),
            "schedule_to": NightLightAdapter._get("night-light-schedule-to", 6.0),
        }

    @staticmethod
    def set(key, value) -> bool:
        return safe_set_gsetting(NightLightAdapter.SCHEMA, f"night-light-{key}", value)


# ══════════════════════════════════════════════════════════════════════════════
# 24. SYSTEM ADMINISTRATION (hostname, SELinux, journald, sysctl)
# ══════════════════════════════════════════════════════════════════════════════

class AdminAdapter:
    @staticmethod
    def hostname() -> str:
        ok, out, _ = run_cmd(["hostnamectl", "--no-legend", "hostname"], timeout=4)
        return out.strip() if ok and out else os.uname().nodename

    @staticmethod
    def set_hostname(name: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "hostnamectl", "set-hostname", name], timeout=8)
        return ok

    @staticmethod
    def selinux() -> Dict:
        ok, out, _ = run_cmd(["getenforce"], timeout=4)
        mode = out.strip().lower() if ok and out else "unavailable"
        cfg = "enforcing"
        try:
            m = re.search(r"^SELINUX=(\w+)", Path("/etc/selinux/config").read_text(), re.M)
            if m:
                cfg = m.group(1).lower()
        except Exception:
            pass
        return {"mode": mode, "boot_mode": cfg, "available": mode != "unavailable"}

    @staticmethod
    def set_selinux(mode: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "setenforce", mode], timeout=6)
        return ok

    @staticmethod
    def journal_health() -> Dict:
        ok, out, _ = run_cmd(["bash", "-c", "journalctl --disk-usage 2>/dev/null | head -1"], timeout=8)
        size = (out or "").strip()[:60]
        failed_units = []
        okf, outf, _ = run_cmd(["systemctl", "--failed", "--no-legend"], timeout=8)
        for line in (outf or "").splitlines():
            if line.strip():
                failed_units.append(line.split()[0][:40])
        return {"disk_usage": size or "unknown", "failed_units": failed_units}

    @staticmethod
    def restart_unit(unit: str) -> bool:
        ok, _, _ = run_cmd(["pkexec", "systemctl", "restart", unit], timeout=30)
        return ok


# ══════════════════════════════════════════════════════════════════════════════
# 25. ONLINE ACCOUNTS (GNOME Online Accounts / Nextcloud / CalDAV)
# ══════════════════════════════════════════════════════════════════════════════

class OnlineAccountsAdapter:
    @staticmethod
    def provider_supported() -> Dict[str, bool]:
        return {
            "GOA (GNOME Online Accounts)": _which("goa-daemon", "gnome-online-accounts") is not None,
            "KAccounts (KDE)": _which("kaccounts-dell", "kaccountsctl") is not None,
            "Nextcloud client": _which("nextcloudcmd", "nextcloud") is not None,
            "CalDAV sync (vdirsyncer)": _which("vdirsyncer") is not None,
        }

    @staticmethod
    def configured() -> List[Dict]:
        accounts = []
        ok, out, _ = run_cmd(["goa-daemon", "--version"], timeout=4)
        if _which("goa-daemon"):
            # Real GOA enumeration is via D-Bus; offer launcher instead
            accounts.append({"name": "GNOME Online Accounts", "type": "hub", "action": "goa-panel" if _which("goa-panel") else "gnome-control-center online-accounts"})
        if _which("nextcloudcmd") or _which("nextcloud"):
            accounts.append({"name": "Nextcloud sync client", "type": "files", "action": "nextcloud"})
        return accounts

    @staticmethod
    def launch_configurator(action: str) -> bool:
        if not shutil.which(action.split()[0]):
            return False
        subprocess.Popen([action], start_new_session=True)
        return True


# ══════════════════════════════════════════════════════════════════════════════
# 26. ADVANCED POINTER (xinput per-device tuning)
# ══════════════════════════════════════════════════════════════════════════════

class AdvancedPointerAdapter:
    @staticmethod
    def pointer_devices() -> List[Dict]:
        devs = []
        ok, out, _ = run_cmd(["xinput", "list", "--name-only"], timeout=6)
        for name in (out or "").splitlines():
            n = name.strip()
            if any(k in n.lower() for k in ("mouse", "touchpad", "trackball", "trackpoint", "tablet", "pointer")):
                devs.append({"name": n[:52]})
        return devs

    @staticmethod
    def device_props(device_name: str) -> List[Dict]:
        props = []
        ok, out, _ = run_cmd(["xinput", "list-props", shlex.quote(device_name)], timeout=6)
        cur = {}
        for line in (out or "").splitlines():
            m = re.match(r"\s*(.+?)\s+\((\d+)\):\s*(.*)", line)
            if m:
                if cur:
                    props.append(cur)
                cur = {"prop": m.group(1)[:44], "id": m.group(2), "value": m.group(3)[:40]}
        if cur:
            props.append(cur)
        return [p for p in props if "libinput" in p["prop"].lower() or "Accel" in p["prop"] or "Scroll" in p["prop"] or "Button" in p["prop"]][:18]

    @staticmethod
    def set_prop(device_name: str, prop: str, value: str) -> bool:
        ok, _, _ = run_cmd(["xinput", "set-prop", shlex.quote(device_name), shlex.quote(prop), value], timeout=6)
        return ok
