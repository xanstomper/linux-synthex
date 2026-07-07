#!/usr/bin/env python3
"""Synthex CLI — Unified command center. Delegates to dedicated Synthex tools."""
import sys, os, subprocess, shutil

BIN_PREFIX = "/usr/bin"
DEV_BIN = os.path.expanduser("~/.local/bin")

def tool(name):
    """Resolve a Synthex tool binary — try dev path first, then system."""
    for base in (DEV_BIN, BIN_PREFIX):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return name

def run(*args, **kw):
    kw.setdefault("check", False)
    return subprocess.run(args, **kw)

CMDS = {
    "update":   lambda _: run(tool("synthex-update-manager")),
    "rollback": lambda _: run(tool("synthex-update-manager"), "rollback"),
    "snapshot": lambda a: run(tool("synthex-update-manager"), "snapshot", *(a.args or [])),
    "mode":     lambda a: run(tool("synthex-workspace"), a.mode),
    "status":   lambda _: run(tool("synthex.py") if "synthex.py" in tool("synthex.py") else "synthex", "status"),

    "layout":   lambda a: run(tool("synthex-layout"), "set", a.layout) if a.layout
                else run(tool("synthex-layout"), "list"),
    "theme":    lambda a: run(tool("synthex-layout"), "theme", a.name),

    "install":  lambda a: run("flatpak", "install", "-y", a.pkg) if run("flatpak", "search", a.pkg, capture_output=True).stdout.strip()
                else run("sudo", "dnf", "install", "-y", a.pkg),
    "remove":   lambda a: run("sudo", "dnf", "remove", "-y", a.pkg),
    "search":   lambda a: _search(a.query),
    "drivers":  lambda a: run(tool("synthex-driver-manager"), *(a.args or ["list"])),
    "hw-info":  lambda _: run(tool("synthex-hwdaemon"), "status"),
    "ai":       lambda _: run(tool("synthex-ai-hub")),
    "firewall": lambda a: run(tool("synthex-firewall"), a.profile) if a.profile
                else run(tool("synthex-firewall"), "status"),
    "proton":   lambda a: run(tool("synthex-proton-manager"), *a.args),
    "gpu":      lambda a: run(tool("synthex-gpu-switch"), a.mode),

    "blueprint": lambda a: run(tool("synthex-blueprint"), a.action, *(a.args or [])),
    "backup":    lambda _: run(tool("synthex-blueprint"), "export",
                               f"synthex-{os.uname().nodename}-{__import__('datetime').date.today()}.zbp"),
    "tray":      lambda _: run(tool("synthex-tray"), "status"),
    "welcome":   lambda _: run(tool("synthex-welcome")),
    "recovery":  lambda _: run(tool("synthex-recovery"), "--check-boot"),
    "gaming":    lambda _: run(tool("synthex-gaming-mode"), "enable"),
    "codecs":    lambda _: run("sudo", tool("synthex-codec-installer")),
    "nvidia":    lambda _: run("sudo", tool("synthex-nvidia-installer")),
    "kernel":    lambda a: run(tool("synthex-kernel-manager"), *a.args),
    "service":   lambda a: run(tool("synthex-service-manager"), a.action, *(a.args or [])),
    "logs":      lambda a: run(tool("synthex-log-viewer"), *(a.args or [])),
    "locale":    lambda a: run(tool("synthex-locale-setup"), a.action, *(a.args or [])),
    "ananicy":   lambda a: run(tool("synthex-ananicy"), a.action if a else "status"),
    "aur":       lambda a: run(tool("synthex-aur"), a.action or "list", *(a.args or [])),
    "usb":       lambda a: run(tool("synthex-usb-writer"), a.action or "list", *(a.args or [])),
    "input":     lambda _: run(tool("synthex-input-remapper")),
    "power-profiles": lambda a: run(tool("synthex-power-profiles"), *(a.args or ["status"])),
    "upgrade":   lambda a: run(tool("synthex-upgrade"), *(a.args or ["check"])),
    "disk":      lambda _: run(tool("synthex-disk-health")),
    "report":    lambda _: run(tool("synthex-system-report")),
    "timeshift": lambda a: run(tool("synthex-timeshift"), *(a.args or ["list"])),
    "handheld":  lambda a: run(tool("synthex-handheld"), *(a.args or ["status"])),
    "tour":      lambda _: run(tool("synthex-tour")),
    "appimage":  lambda a: run(tool("synthex-appimage"), *(a.args or ["list"])),
    "hermes":    lambda a: run(tool("synthex-agent"), *(a.args or [])),
    "agent":     lambda a: run(tool("synthex-agent"), *(a.args or [])),
    "codex":     lambda _: run(tool("synthex-agent"), "--codex"),
    "kb":        lambda a: run(tool("synthex-agent"), "--kb", *(a.args or [])),
}

def _search(query):
    print(f"🔍 {query}\n── Flatpak ──"); run("flatpak", "search", query)
    print("── RPM ──"); run("dnf", "search", query)

def main():
    if len(sys.argv) < 2:
        print("Synthex CLI — Usage: synthex <command> [args]")
        print(f"Commands: {', '.join(sorted(CMDS))}")
        return 1
    cmd = sys.argv[1]
    if cmd not in CMDS:
        print(f"Unknown: {cmd}. Try: {', '.join(sorted(CMDS))}")
        return 1
    CMDS[cmd](sys.argv[2:])
    return 0

if __name__ == "__main__":
    sys.exit(main())
