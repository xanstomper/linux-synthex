#!/usr/bin/env python3
"""solus AI Troubleshooter — detect broken services, missing deps, conflicts.

Scans systemctl --failed, journalctl errors, dnf check, and missing firmware
to produce concrete fix suggestions.

Usage:
    solus-ai-assistant troubleshoot
    solus-ai-assistant troubleshoot --json
"""
import json
import os
import subprocess
import sys


def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 1, "", str(e)


def failed_units():
    rc, out, _ = run(["systemctl", "--failed", "--no-legend", "--plain",
                      "list-units"])
    units = []
    for line in out.splitlines():
        if line.strip():
            units.append(line.split()[0])
    return units


def journal_errors():
    rc, out, _ = run(["journalctl", "-p", "err", "-b", "--no-pager", "-o",
                      "short", "-n", "40"])
    return [l for l in out.splitlines() if l.strip()]


def dnf_check():
    rc, out, err = run(["dnf", "-q", "check"])
    if rc == 0:
        return {"status": "ok", "problems": []}
    return {"status": "broken", "problems": (out + err).splitlines()}


def missing_firmware():
    rc, out, _ = run(["journalctl", "-b", "--no-pager", "-g",
                      "firmware.*not found", "-n", "20"])
    return [l for l in out.splitlines() if l.strip()]


def broken_unit_fix(unit):
    # Common restart hints
    return [f"systemctl restart {unit}",
            f"journalctl -u {unit} -b --no-pager | tail -30"]


def analyze():
    failed = failed_units()
    errs = journal_errors()
    deps = dnf_check()
    fw = missing_firmware()

    fixes = []
    for u in failed:
        fixes.extend(broken_unit_fix(u))
    if deps["status"] == "broken":
        fixes.append("sudo dnf distro-sync --refresh")
        fixes.append("sudo dnf reinstall $(dnf -q check | head)")
    if fw:
        fixes.append("sudo dnf install linux-firmware linux-firmware-amd "
                     "linux-firmware-intel linux-firmware-network")
    if not failed and deps["status"] == "ok" and not fw:
        status = "healthy"
    else:
        status = "issues found"

    return {
        "status": status,
        "failed_units": failed,
        "dependency_check": deps,
        "missing_firmware": fw,
        "journal_errors": errs[:10],
        "suggested_fixes": fixes,
    }


def main(argv):
    as_json = "--json" in argv
    result = analyze()
    if as_json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"System status: {result['status']}\n")
    if result["failed_units"]:
        print("Failed services:")
        for u in result["failed_units"]:
            print(f"  ✗ {u}")
        print()
    if result["dependency_check"]["status"] == "broken":
        print("Package dependency problems detected:")
        for p in result["dependency_check"]["problems"][:5]:
            print(f"  • {p}")
        print()
    if result["missing_firmware"]:
        print("Missing firmware (recent):")
        for f in result["missing_firmware"][:5]:
            print(f"  • {f}")
        print()
    if result["suggested_fixes"]:
        print("Suggested fixes:")
        for f in result["suggested_fixes"]:
            print(f"  → {f}")
    else:
        print("No issues found — system is healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
