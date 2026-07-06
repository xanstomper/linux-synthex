#!/usr/bin/env python3
"""Solus CLI — Unified command center. Delegates to dedicated Solus tools."""
import sys, os, subprocess, shutil

BIN_PREFIX = "/usr/bin"
DEV_BIN = os.path.expanduser("~/.local/bin")

def tool(name):
    """Resolve a Solus tool binary — try dev path first, then system."""
    for base in (DEV_BIN, BIN_PREFIX):
        path = os.path.join(base, name)
        if os.path.exists(path):
            return path
    return name

def run(*args, **kw):
    kw.setdefault("check", False)
    return subprocess.run(args, **kw)

CMDS = {
    "update":   lambda _: run(tool("solus-update-manager")),
    "rollback": lambda _: run(tool("solus-update-manager"), "rollback"),
    "snapshot": lambda a: run(tool("solus-update-manager"), "snapshot", *(a.args or [])),
    "mode":     lambda a: run(tool("solus-workspace"), a.mode),
    "status":   lambda _: run(tool("solus.py") if "solus.py" in tool("solus.py") else "solus", "status"),

    "layout":   lambda a: run(tool("solus-layout"), "set", a.layout) if a.layout
                else run(tool("solus-layout"), "list"),
    "theme":    lambda a: run(tool("solus-layout"), "theme", a.name),

    "install":  lambda a: run("flatpak", "install", "-y", a.pkg) if run("flatpak", "search", a.pkg, capture_output=True).stdout.strip()
                else run("sudo", "dnf", "install", "-y", a.pkg),
    "remove":   lambda a: run("sudo", "dnf", "remove", "-y", a.pkg),
    "search":   lambda a: _search(a.query),
    "drivers":  lambda a: run(tool("solus-driver-manager"), *(a.args or ["list"])),
    "hw-info":  lambda _: run(tool("solus-hwdaemon"), "status"),
    "ai":       lambda _: run(tool("solus-ai-hub")),
    "firewall": lambda a: run(tool("solus-firewall"), a.profile) if a.profile
                else run(tool("solus-firewall"), "status"),
    "proton":   lambda a: run(tool("solus-proton-manager"), *a.args),
    "gpu":      lambda a: run(tool("solus-gpu-switch"), a.mode),

    "blueprint": lambda a: run(tool("solus-blueprint"), a.action, *(a.args or [])),
    "backup":    lambda _: run(tool("solus-blueprint"), "export",
                               f"solus-{os.uname().nodename}-{__import__('datetime').date.today()}.zbp"),
    "tray":      lambda _: run(tool("solus-tray"), "status"),
    "welcome":   lambda _: run(tool("solus-welcome")),
    "recovery":  lambda _: run(tool("solus-recovery"), "--check-boot"),
    "gaming":    lambda _: run(tool("solus-gaming-mode"), "enable"),
    "codecs":    lambda _: run("sudo", tool("solus-codec-installer")),
    "nvidia":    lambda _: run("sudo", tool("solus-nvidia-installer")),
    "kernel":    lambda a: run(tool("solus-kernel-manager"), *a.args),
    "service":   lambda a: run(tool("solus-service-manager"), a.action, *(a.args or [])),
    "logs":      lambda a: run(tool("solus-log-viewer"), *(a.args or [])),
    "locale":    lambda a: run(tool("solus-locale-setup"), a.action, *(a.args or [])),
    "ananicy":   lambda a: run(tool("solus-ananicy"), a.action if a else "status"),
    "aur":       lambda a: run(tool("solus-aur"), a.action or "list", *(a.args or [])),
    "usb":       lambda a: run(tool("solus-usb-writer"), a.action or "list", *(a.args or [])),
    "input":     lambda _: run(tool("solus-input-remapper")),
    "power-profiles": lambda a: run(tool("solus-power-profiles"), *(a.args or ["status"])),
    "upgrade":   lambda a: run(tool("solus-upgrade"), *(a.args or ["check"])),
    "disk":      lambda _: run(tool("solus-disk-health")),
    "report":    lambda _: run(tool("solus-system-report")),
    "timeshift": lambda a: run(tool("solus-timeshift"), *(a.args or ["list"])),
    "handheld":  lambda a: run(tool("solus-handheld"), *(a.args or ["status"])),
    "tour":      lambda _: run(tool("solus-tour")),
    "appimage":  lambda a: run(tool("solus-appimage"), *(a.args or ["list"])),
    "hermes":    lambda a: run(tool("solus-agent"), *(a.args or [])),
    "agent":     lambda a: run(tool("solus-agent"), *(a.args or [])),
    "codex":     lambda _: run(tool("solus-agent"), "--codex"),
    "kb":        lambda a: run(tool("solus-agent"), "--kb", *(a.args or [])),
}

def _search(query):
    print(f"🔍 {query}\n── Flatpak ──"); run("flatpak", "search", query)
    print("── RPM ──"); run("dnf", "search", query)

def main():
    if len(sys.argv) < 2:
        print("Solus CLI — Usage: solus <command> [args]")
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
