#!/usr/bin/env python3
"""
Solus Security Dashboard — System Health Monitor
==================================================
Daemon that collects and reports system security status.

Features:
  - Checks SELinux status (enforcing/permissive/disabled)
  - Checks firewalld status (active/inactive)
  - Checks disk encryption status (LUKS)
  - Checks Secure Boot status
  - Checks available system updates
  - Checks auditd status
  - Reports as JSON via stdout or D-Bus
  - Configurable check interval

Usage:
  solus-securityd [--daemon] [--interval <seconds>]
  solus-securityd --check     Run a single check and exit
  solus-securityd --json      Output results as JSON
  solus-securityd --dbus      Export results via D-Bus

Configuration:
  ~/.config/solus/security/config.json
"""

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG = logging.getLogger("solus-securityd")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_DIR = Path.home() / ".config" / "solus" / "security"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_INTERVAL = 300  # 5 minutes

DEFAULT_CONFIG = {
    "interval": DEFAULT_INTERVAL,
    "checks": {
        "selinux": True,
        "firewalld": True,
        "encryption": True,
        "secure_boot": True,
        "updates": True,
        "auditd": True,
        "apparmor": True,
    },
    "alert_on_failure": True,
    "dbus_export": False,
}


# ---------------------------------------------------------------------------
# System Check Functions
# ---------------------------------------------------------------------------

def _run_cmd(cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        return subprocess.CompletedProcess(cmd, -1, "", str(exc))


def check_selinux() -> Dict[str, Any]:
    """Check SELinux status."""
    result: Dict[str, Any] = {
        "name": "SELinux",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": True,
    }
    # Try getenforce first
    proc = _run_cmd(["getenforce"])
    if proc.returncode == 0:
        mode = proc.stdout.strip()
        result["status"] = "enforcing" if mode == "Enforcing" else mode.lower()
        result["details"]["mode"] = mode
        result["healthy"] = mode == "Enforcing"

        # Get policy type
        proc2 = _run_cmd(["sestatus"])
        if proc2.returncode == 0:
            for line in proc2.stdout.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    result["details"][key.strip().lower().replace(" ", "_")] = val.strip()
    else:
        # Check if SELinux is available at all
        if os.path.exists("/sys/fs/selinux"):
            result["status"] = "disabled"
            result["details"]["note"] = "SELinux disabled but filesystem present"
        else:
            result["status"] = "not_present"
            result["details"]["note"] = "SELinux not installed"
        result["healthy"] = False

    return result


def check_apparmor() -> Dict[str, Any]:
    """Check AppArmor status."""
    result: Dict[str, Any] = {
        "name": "AppArmor",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": True,
    }
    proc = _run_cmd(["aa-status"])
    if proc.returncode == 0:
        result["status"] = "active"
        result["healthy"] = True
        # Parse profile count
        for line in proc.stdout.splitlines():
            if "profiles are loaded" in line:
                match = re.search(r"(\d+)\s+profiles", line)
                if match:
                    result["details"]["loaded_profiles"] = int(match.group(1))
            elif "processes are unconfined" in line:
                match = re.search(r"(\d+)\s+processes", line)
                if match:
                    result["details"]["unconfined_processes"] = int(match.group(1))
    elif proc.returncode == 4:
        # AppArmor not enabled
        result["status"] = "disabled"
        result["details"]["note"] = "AppArmor not enabled in kernel"
    else:
        result["status"] = "not_installed"
        result["details"]["note"] = "aa-status not found"

    return result


def check_firewalld() -> Dict[str, Any]:
    """Check firewalld status."""
    result: Dict[str, Any] = {
        "name": "FirewallD",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": True,
    }
    proc = _run_cmd(["firewall-cmd", "--state"])
    if proc.returncode == 0:
        result["status"] = "active"
        result["healthy"] = True
        # Get default zone
        zone_proc = _run_cmd(["firewall-cmd", "--get-default-zone"])
        if zone_proc.returncode == 0:
            result["details"]["default_zone"] = zone_proc.stdout.strip()
        # Get active zones
        active_proc = _run_cmd(["firewall-cmd", "--get-active-zones"])
        if active_proc.returncode == 0:
            result["details"]["active_zones"] = [
                z.strip() for z in active_proc.stdout.splitlines() if z.strip() and not z.startswith(" ")
            ]
    elif proc.returncode == 252:
        result["status"] = "not_running"
        result["details"]["note"] = "firewalld is not running"
    else:
        # Check if firewalld is installed
        if shutil.which("firewall-cmd"):
            result["status"] = "inactive"
        else:
            result["status"] = "not_installed"
        result["details"]["note"] = "firewalld unavailable"

    return result


def check_encryption() -> Dict[str, Any]:
    """Check disk encryption status (LUKS)."""
    result: Dict[str, Any] = {
        "name": "Disk Encryption",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": True,
    }
    # Check for LUKS on mounted root
    proc = _run_cmd(["lsblk", "-o", "NAME,TYPE,FSTYPE,MOUNTPOINT", "-J"], timeout=10)
    if proc.returncode == 0:
        try:
            data = json.loads(proc.stdout)
            encrypted_count = 0
            total_fs = 0
            root_encrypted = False

            def _walk(devices: List[dict]) -> None:
                nonlocal encrypted_count, total_fs, root_encrypted
                for dev in devices:
                    fstype = dev.get("fstype", "") or ""
                    mount = dev.get("mountpoint", "") or ""
                    name = dev.get("name", "")

                    if fstype == "crypto_LUKS":
                        encrypted_count += 1
                        result["details"][f"luks_device_{encrypted_count}"] = name
                    if fstype and fstype != "crypto_LUKS":
                        total_fs += 1
                    if mount == "/" and encrypted_count > 0:
                        root_encrypted = True

                    if "children" in dev:
                        _walk(dev["children"])

            _walk(data.get("blockdevices", []))
            result["details"]["luks_devices"] = encrypted_count
            result["details"]["root_encrypted"] = root_encrypted
            result["healthy"] = root_encrypted or encrypted_count > 0
            result["status"] = "encrypted" if encrypted_count > 0 else "not_encrypted"
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            result["details"]["error"] = str(exc)
            result["status"] = "check_failed"
    else:
        result["status"] = "check_failed"
        result["details"]["error"] = proc.stderr.strip()

    # Also check for /crypto_keyfile.bin (common in Fedora/Solus)
    if os.path.exists("/crypto_keyfile.bin") or os.path.exists("/boot/crypto_keyfile.bin"):
        result["details"]["keyfile_present"] = True

    return result


def check_secure_boot() -> Dict[str, Any]:
    """Check Secure Boot status."""
    result: Dict[str, Any] = {
        "name": "Secure Boot",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": True,
    }
    # Check via mokutil
    proc = _run_cmd(["mokutil", "--sb-state"])
    if proc.returncode == 0:
        state = proc.stdout.strip()
        result["status"] = "enabled" if "enabled" in state.lower() else "disabled"
        result["healthy"] = "enabled" in state.lower()
        result["details"]["state"] = state
        return result

    # Check via efibootmgr (fallback)
    proc = _run_cmd(["efibootmgr", "-v"])
    if proc.returncode == 0:
        # SecureBoot bit in efivar
        sb_var = "/sys/firmware/efi/efivars/SecureBoot-*"
        sb_files = list(Path("/sys/firmware/efi/efivars").glob("SecureBoot*"))
        if sb_files:
            try:
                with open(sb_files[0], "rb") as fh:
                    data = fh.read()
                    # Byte 4 (index 4) has the value: 1 = enabled
                    result["details"]["raw_value"] = data[-1] if len(data) > 4 else 0
                    result["healthy"] = data[-1] == 1 if len(data) > 4 else False
                    result["status"] = "enabled" if result["healthy"] else "disabled"
            except (OSError, IndexError):
                pass
        else:
            # Either not UEFI or Secure Boot not available
            if os.path.isdir("/sys/firmware/efi"):
                result["status"] = "not_supported"
                result["details"]["note"] = "UEFI detected but Secure Boot variables not found"
            else:
                result["status"] = "legacy_bios"
                result["details"]["note"] = "Legacy BIOS boot (not UEFI)"
            result["healthy"] = False
    else:
        result["status"] = "check_failed"
        result["details"]["error"] = "efibootmgr not available or system not UEFI"

    return result


def check_updates() -> Dict[str, Any]:
    """Check available system updates."""
    result: Dict[str, Any] = {
        "name": "System Updates",
        "status": "unknown",
        "details": {},
        "healthy": True,
        "critical": False,
    }
    # Check with dnf check-update (non-root shows available)
    proc = _run_cmd(["dnf", "check-update", "--quiet"], timeout=60)
    if proc.returncode == 0:
        result["status"] = "up_to_date"
        result["details"]["updates_available"] = 0
        result["healthy"] = True
    elif proc.returncode == 100:
        # Updates available
        lines = [l for l in proc.stdout.splitlines() if l.strip() and not l.startswith("Last metadata")]
        result["details"]["updates_available"] = len(lines)
        result["details"]["updates"] = lines[:20]  # Limit to 20 entries
        result["status"] = f"{len(lines)} updates available"
        result["healthy"] = False  # Not critical but unhealthy
    else:
        # Could be offline or error
        result["status"] = "check_failed"
        result["details"]["error"] = proc.stderr.strip() or "Check failed (system may be offline)"
        result["healthy"] = False

    # Check security updates specifically
    sec_proc = _run_cmd(["dnf", "updateinfo", "--list", "--security", "--quiet"], timeout=30)
    if sec_proc.returncode == 0:
        sec_lines = [l for l in sec_proc.stdout.splitlines() if l.strip()]
        if sec_lines:
            result["details"]["security_updates"] = len(sec_lines)

    return result


def check_auditd() -> Dict[str, Any]:
    """Check auditd status."""
    result: Dict[str, Any] = {
        "name": "AuditD",
        "status": "unknown",
        "details": {},
        "healthy": False,
        "critical": False,
    }
    # Check via systemctl
    proc = _run_cmd(["systemctl", "is-active", "auditd"])
    if proc.returncode == 0:
        result["status"] = proc.stdout.strip()  # "active"
        result["healthy"] = True
    else:
        result["details"]["state"] = proc.stdout.strip() if proc.stdout else "inactive"

    # Check if auditd is enabled
    enabled_proc = _run_cmd(["systemctl", "is-enabled", "auditd"])
    if enabled_proc.returncode == 0:
        result["details"]["enabled"] = enabled_proc.stdout.strip()
    else:
        result["details"]["enabled"] = "disabled"

    # Get audit rules count
    rules_proc = _run_cmd(["auditctl", "-l"])
    if rules_proc.returncode == 0:
        rules = [l for l in rules_proc.stdout.splitlines() if l.strip()]
        result["details"]["rules_count"] = len(rules)

    # If not active/healthy, fill in
    if not result["healthy"]:
        if shutil.which("auditd"):
            result["status"] = "inactive"
        else:
            result["status"] = "not_installed"

    return result


# ---------------------------------------------------------------------------
# Security Check Runner
# ---------------------------------------------------------------------------

class SecurityChecker:
    """Runs all configured security checks and aggregates results."""

    def __init__(self, config: Optional[dict] = None) -> None:
        self.config = config or dict(DEFAULT_CONFIG)
        self.enabled_checks = self.config.get("checks", {})
        self._lock = threading.Lock()
        self._last_results: Dict[str, Any] = {}

    def run_all(self) -> Dict[str, Any]:
        """Execute all enabled checks and return results."""
        results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "hostname": os.uname().nodename,
            "checks": {},
            "summary": {
                "total": 0,
                "healthy": 0,
                "unhealthy": 0,
                "failed": 0,
                "overall_healthy": False,
            },
        }

        check_map = {
            "selinux": check_selinux,
            "apparmor": check_apparmor,
            "firewalld": check_firewalld,
            "encryption": check_encryption,
            "secure_boot": check_secure_boot,
            "updates": check_updates,
            "auditd": check_auditd,
        }

        for name, func in check_map.items():
            if self.enabled_checks.get(name, True):
                try:
                    result = func()
                    results["checks"][name] = result
                    results["summary"]["total"] += 1
                    if result.get("healthy", False):
                        results["summary"]["healthy"] += 1
                    else:
                        results["summary"]["unhealthy"] += 1
                        LOG.warning("Unhealthy: %s — %s", name, result.get("status", "unknown"))
                except Exception as exc:
                    LOG.error("Check '%s' failed: %s", name, exc)
                    results["checks"][name] = {
                        "name": name,
                        "status": "error",
                        "healthy": False,
                        "error": str(exc),
                    }
                    results["summary"]["failed"] += 1
                    results["summary"]["unhealthy"] += 1

        # Overall status
        total = results["summary"]["total"]
        healthy = results["summary"]["healthy"]
        results["summary"]["overall_healthy"] = (healthy == total) if total > 0 else False
        results["overall_health"] = "healthy" if results["summary"]["overall_healthy"] else "issues_detected"

        with self._lock:
            self._last_results = results

        return results

    def get_last_results(self) -> Dict[str, Any]:
        """Return the last check results."""
        with self._lock:
            return dict(self._last_results)


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------

class SecurityDaemon:
    """Background daemon that periodically runs security checks."""

    def __init__(self, config: Optional[dict] = None) -> None:
        self.config = config or dict(DEFAULT_CONFIG)
        self.checker = SecurityChecker(self.config)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the background check loop."""
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        LOG.info("Security daemon started (interval: %ds)", self.config.get("interval", DEFAULT_INTERVAL))

    def stop(self) -> None:
        """Stop the daemon."""
        self._running = False
        LOG.info("Security daemon stopped")

    def _loop(self) -> None:
        """Main check loop."""
        while self._running:
            try:
                results = self.checker.run_all()
                self._report_results(results)
            except Exception as exc:
                LOG.error("Check loop error: %s", exc)

            # Sleep with interrupt support
            for _ in range(self.config.get("interval", DEFAULT_INTERVAL)):
                if not self._running:
                    return
                time.sleep(1)

    def _report_results(self, results: Dict[str, Any]) -> None:
        """Log or export check results."""
        summary = results.get("summary", {})
        LOG.info(
            "Security check: %d/%d healthy, overall: %s",
            summary.get("healthy", 0),
            summary.get("total", 0),
            results.get("overall_health", "unknown"),
        )

        # Show critical issues
        for name, check in results.get("checks", {}).items():
            if not check.get("healthy", True) and check.get("critical", False):
                LOG.warning("CRITICAL: %s — %s", check.get("name", name), check.get("status", "unhealthy"))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load daemon configuration."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as fh:
                cfg = json.load(fh)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """Persist configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as fh:
        json.dump(cfg, fh, indent=2)


def print_report(results: Dict[str, Any], json_output: bool = False) -> None:
    """Print security report to stdout."""
    if json_output:
        print(json.dumps(results, indent=2, default=str))
        return

    # Human-readable report
    print(f"\n{'='*60}")
    print(f"  Solus Security Report — {results.get('hostname', '?')}")
    print(f"  {results.get('timestamp', '?')}")
    print(f"{'='*60}\n")

    summary = results.get("summary", {})
    overall = results.get("overall_health", "unknown")
    status_color = "\033[32m" if overall == "healthy" else "\033[31m"
    print(f"  Overall: {status_color}{overall}\033[0m")
    print(f"  Checks:  {summary.get('healthy', 0)}/{summary.get('total', 0)} healthy\n")

    for name, check in results.get("checks", {}).items():
        healthy = check.get("healthy", False)
        critical = check.get("critical", False)
        icon = "\033[32m✓\033[0m" if healthy else ("\033[31m✗\033[0m" if critical else "\033[33m!\033[0m")
        print(f"  {icon} {check.get('name', name):20s}  {check.get('status', '?')}")
        details = check.get("details", {})
        if details and not healthy:
            for k, v in list(details.items())[:3]:
                if not k.startswith("_"):
                    print(f"      {k}: {v}")

    print("")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solus Security Dashboard — System Health Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--daemon", action="store_true",
                        help="Run as a background daemon")
    parser.add_argument("--check", action="store_true",
                        help="Run a single security check and exit")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--interval", "-i", type=int, default=None,
                        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--config", default=str(CONFIG_FILE),
                        help=f"Configuration file (default: {CONFIG_FILE})")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    config = load_config()
    if args.interval:
        config["interval"] = args.interval

    if args.daemon:
        daemon = SecurityDaemon(config)
        try:
            daemon.start()
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            daemon.stop()
        return 0

    if args.check or args.json:
        checker = SecurityChecker(config)
        results = checker.run_all()
        print_report(results, json_output=args.json)
        if args.check:
            # Exit non-zero if issues found
            if not results.get("summary", {}).get("overall_healthy", False):
                return 1
        return 0

    # Default: run single check with human-readable output
    checker = SecurityChecker(config)
    results = checker.run_all()
    print_report(results, json_output=False)

    return 0 if results.get("summary", {}).get("overall_healthy", False) else 1


if __name__ == "__main__":
    sys.exit(main())
