#!/usr/bin/env python3
"""
Synthex Security Dashboard — System health monitor.

Usage:
    synthex-security-check          # Run security check, output to stdout
    synthex-security-dashboard      # Launch GTK GUI (if available)
"""

import sys
import os
import json
import subprocess
from datetime import datetime


def check_selinux():
    """Check SELinux status."""
    try:
        result = subprocess.run(["getenforce"], capture_output=True, text=True)
        status = result.stdout.strip()
        if status == "Enforcing":
            return {"status": "healthy", "message": "SELinux enforcing", "score": 10}
        elif status == "Permissive":
            return {"status": "warning", "message": "SELinux permissive", "score": 5}
        else:
            return {"status": "critical", "message": "SELinux disabled", "score": 0}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check SELinux", "score": 0}


def check_firewall():
    """Check firewall status."""
    try:
        result = subprocess.run(["firewall-cmd", "--state"], capture_output=True, text=True)
        if "running" in result.stdout:
            return {"status": "healthy", "message": "Firewall active", "score": 10}
        else:
            return {"status": "critical", "message": "Firewall not running", "score": 0}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check firewall", "score": 0}


def check_encryption():
    """Check disk encryption status."""
    try:
        result = subprocess.run(["dmsetup", "ls", "--target", "crypt"], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            devices = [l.split()[0] for l in result.stdout.splitlines() if l.strip()]
            return {"status": "healthy", "message": f"LUKS encrypted ({len(devices)} devices)", "score": 10}
        else:
            return {"status": "warning", "message": "No disk encryption detected", "score": 3}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check encryption", "score": 0}


def check_secureboot():
    """Check Secure Boot status."""
    try:
        result = subprocess.run(["mokutil", "--sb-state"], capture_output=True, text=True)
        if "enabled" in result.stdout:
            return {"status": "healthy", "message": "Secure Boot enabled", "score": 10}
        else:
            return {"status": "warning", "message": "Secure Boot disabled", "score": 5}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check Secure Boot", "score": 0}


def check_updates():
    """Check for available updates."""
    try:
        result = subprocess.run(["dnf", "check-update"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "healthy", "message": "System up to date", "score": 10}
        else:
            count = len([l for l in result.stdout.splitlines() 
                        if l.strip() and not l.startswith("Last") and not l.startswith("Upgrade")])
            return {"status": "warning", "message": f"{count} updates available", "score": max(0, 10 - count)}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check updates", "score": 0}


def check_kernel_lockdown():
    """Check kernel lockdown status."""
    try:
        with open("/sys/kernel/security/lockdown") as f:
            mode = f.read().strip()
        if mode in ("integrity", "confidentiality"):
            return {"status": "healthy", "message": f"Kernel lockdown: {mode}", "score": 10}
        else:
            return {"status": "warning", "message": f"Kernel lockdown: {mode}", "score": 5}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Kernel lockdown not supported", "score": 3}


def check_auditd():
    """Check audit daemon status."""
    try:
        result = subprocess.run(["systemctl", "is-active", "auditd"], 
                              capture_output=True, text=True)
        if "active" in result.stdout:
            return {"status": "healthy", "message": "Auditd running", "score": 10}
        else:
            return {"status": "warning", "message": "Auditd not running", "score": 0}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check auditd", "score": 0}


def check_ssh_hardening():
    """Check SSH configuration hardening."""
    try:
        with open("/etc/ssh/sshd_config") as f:
            config = f.read()
        issues = []
        if "PermitRootLogin yes" in config:
            issues.append("root login enabled")
        if "PasswordAuthentication yes" in config and "PubkeyAuthentication" not in config:
            issues.append("password auth without pubkey")
        if issues:
            return {"status": "warning", "message": f"SSH: {', '.join(issues)}", "score": 5}
        return {"status": "healthy", "message": "SSH hardened", "score": 10}
    except FileNotFoundError:
        return {"status": "healthy", "message": "SSH server not installed", "score": 10}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check SSH", "score": 0}


def check_automatic_updates():
    """Check if automatic security updates are configured."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "dnf-automatic.timer"],
            capture_output=True, text=True
        )
        if "active" in result.stdout:
            return {"status": "healthy", "message": "Auto-updates enabled", "score": 10}
        return {"status": "warning", "message": "Auto-updates not enabled", "score": 4}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check auto-updates", "score": 0}


def check_password_policy():
    """Check password quality settings."""
    try:
        with open("/etc/security/pwquality.conf") as f:
            config = f.read()
        minlen = 8
        for line in config.splitlines():
            if line.strip().startswith("minlen"):
                try:
                    minlen = int(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    pass
        if minlen >= 12:
            return {"status": "healthy", "message": f"Password minlen: {minlen}", "score": 10}
        return {"status": "warning", "message": f"Weak password policy (minlen={minlen})", "score": 5}
    except FileNotFoundError:
        return {"status": "warning", "message": "No password policy configured", "score": 3}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check password policy", "score": 0}


def check_btrfs_snapshots():
    """Check if Btrfs snapshots exist for rollback."""
    try:
        result = subprocess.run(
            ["snapper", "-c", "root", "list", "--columns", "number"],
            capture_output=True, text=True
        )
        lines = [l for l in result.stdout.splitlines() if l.strip() and not l.startswith("Number")]
        count = len(lines)
        if count >= 3:
            return {"status": "healthy", "message": f"{count} snapshots available", "score": 10}
        elif count > 0:
            return {"status": "warning", "message": f"Only {count} snapshots (recommend 5+)", "score": 5}
        return {"status": "warning", "message": "No snapshots found", "score": 2}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown", "message": "Cannot check snapshots", "score": 0}


def run_all_checks():
    """Run all security checks and return results."""
    checks = {
        "selinux": check_selinux(),
        "firewall": check_firewall(),
        "encryption": check_encryption(),
        "secure_boot": check_secureboot(),
        "updates": check_updates(),
        "kernel_lockdown": check_kernel_lockdown(),
        "auditd": check_auditd(),
        "ssh_hardening": check_ssh_hardening(),
        "automatic_updates": check_automatic_updates(),
        "password_policy": check_password_policy(),
        "btrfs_snapshots": check_btrfs_snapshots(),
    }
    
    total_score = sum(c["score"] for c in checks.values())
    max_score = len(checks) * 10
    health_percent = (total_score / max_score) * 100
    
    return {
        "timestamp": datetime.now().isoformat(),
        "health_percent": round(health_percent, 1),
        "total_score": total_score,
        "max_score": max_score,
        "checks": checks,
        "overall": "healthy" if health_percent >= 80 else "warning" if health_percent >= 50 else "critical"
    }


def print_report(report):
    """Print security report to stdout."""
    overall = report["overall"]
    icon = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(overall, "⚪")
    
    print(f"\n{icon} Synthex Security Report")
    print(f"{'='*50}")
    print(f"Health: {report['health_percent']}% ({overall})")
    print(f"Score: {report['total_score']}/{report['max_score']}")
    print(f"{'='*50}\n")
    
    for name, check in report["checks"].items():
        status_icon = {"healthy": "✅", "warning": "⚠️", "critical": "❌"}.get(check["status"], "❓")
        print(f"  {status_icon} {name.replace('_', ' ').title():20} {check['message']}")
    
    print(f"\n{'='*50}")
    if overall == "healthy":
        print("✅ System security is in good shape.")
    elif overall == "warning":
        print("⚠️ Some security improvements recommended.")
    else:
        print("🔴 Critical security issues detected!")
    print(f"{'='*50}\n")


def main():
    if "--json" in sys.argv:
        report = run_all_checks()
        print(json.dumps(report, indent=2))
    else:
        report = run_all_checks()
        print_report(report)


if __name__ == "__main__":
    main()
