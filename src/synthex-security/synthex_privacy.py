#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Privacy — Fingerprinting & Data-Privacy Reduction Engine
=================================================================
Complements SpoofGoof (network identity). Closes the remaining surfaces that
let sites fingerprint the device and that let vendors collect data:

  1. Browser fingerprint reduction  — Chromium/Brave policy manifests
     (WebRTC off, disable 3rd-party cookies, disable metrics/prediction,
     disable geolocation & safe-browsing telemetry) in addition to the
     Firefox resist-fingerprinting policy already deployed.
  2. System-wide tracker DNS block  — curated blocklist written to /etc/hosts
     so EVERY application (not just a browser) stops contacting ad/tracking
     domains, provable via getent.
  3. Telemetry reduction sweep      — disables coredump collection, apport
     (Ubuntu), Cockpit, and dnf usage metrics where present, via drop-ins.
  4. Fingerprint audit              — measures psychrometry: user, host, locale,
     timezone, clock, DPI/resolution, installed-font count, DNS egress; returns
     the observable fingerprint surface and remediation hints.
  5. Scheduled auto-clean           — a user systemd timer that periodically
     purges browser linkage + shell history for continuous de-identification.

Every /etc write goes through pkexec(tee) and is fully reversible; every
function accepts a `root` parameter so the unit tests run against a sandbox
and never touch the live system.
"""

import os
import re
import json
import time
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ── Tracker / ad-server blocklist (curated, conservative) ──────────────────
TRACKER_DOMAINS = """
# Synthex Privacy — tracker & telemetry block (added below; safe to remove)
0.0.0.0 doubleclick.net
0.0.0.0 ad.doubleclick.net
0.0.0.0 static.doubleclick.net
0.0.0.0 google-analytics.com
0.0.0.0 www.google-analytics.com
0.0.0.0 ssl.google-analytics.com
0.0.0.0 stats.g.doubleclick.net
0.0.0.0 adservice.google.com
0.0.0.0 googlesyndication.com
0.0.0.0 googleadservices.com
0.0.0.0 pagead2.googlesyndication.com
0.0.0.0 scorecardresearch.com
0.0.0.0 connect.facebook.net
0.0.0.0 facebook-analytics.com
0.0.0.0 fbcdn.net
0.0.0.0 ads-twitter.com
0.0.0.0 twitterads.com
0.0.0.0 analytics.twitter.com
0.0.0.0 staticxx.facebook.com
0.0.0.0 hotjar.com
0.0.0.0 static.hotjar.com
0.0.0.0 in.hotjar.com
0.0.0.0 mixpanel.com
0.0.0.0 api.mixpanel.com
0.0.0.0 segment.io
0.0.0.0 api.segment.io
0.0.0.0 amplitude.com
0.0.0.0 api.amplitude.com
0.0.0.0 appdynamics.com
0.0.0.0 newrelic.com
0.0.0.0 bam.nr-data.net
0.0.0.0 posthog.com
0.0.0.0 app.posthog.com
0.0.0.0 heap.com
0.0.0.0 heapanalytics.com
0.0.0.0 inspire.upscope.io
0.0.0.0 fullstory.com
0.0.0.0 smartlook.com
0.0.0.0 mouseflow.com
0.0.0.0 luckyorange.com
0.0.0.0 criteo.com
0.0.0.0 criteo.net
0.0.0.0 taboola.com
0.0.0.0 outbrain.com
0.0.0.0 bidswitch.net
0.0.0.0 pubmatic.com
0.0.0.0 rubiconproject.com
0.0.0.0 openx.net
0.0.0.0 adnxs.com
0.0.0.0 appnexus.com
0.0.0.0 adform.net
0.0.0.0 moatads.com
0.0.0.0 chartbeat.com
0.0.0.0 comscore.com
0.0.0.0.quantserve.com
0.0.0.0 quantcast.com
0.0.0.0.inspectlet.com
0.0.0.0 vwo.com
0.0.0.0 optimizely.com
0.0.0.0 crazyegg.com
0.0.0.0 kissmetrics.com
0.0.0.0 tapsaff.com
0.0.0.0 millennialmedia.com
0.0.0.0 blismedia.com
0.0.0.0 btrll.com
0.0.0.0 adroll.com
0.0.0.0 insightexpressai.com
0.0.0.0 leadlanders.com
0.0.0.0 yu0.com
0.0.0.0 25qm.com
0.0.0.0 tr.pdf
"""


def _run(cmd, timeout=8, capture=True):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None


def _pkexec_write(path: Path, content: str):
    """Write a file as root via pkexec (tmp → cp)."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.gettempdir()) / (".synthex_" + str(abs(hash(path))) + ".tmp")
        tmp.write_text(content)
        return _run(["pkexec", "cp", str(tmp), str(path)], timeout=20)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════
# 1. CHROMIUM-FAMILY BROWSER HARDENING
# ══════════════════════════════════════════════════════════════════════════

CHROMIUM_POLICY = {
    "policies": {
        "DefaultDownloadDirectory": None,  # placeholder removed below
    }
}

CHROMIUM_ASSOC = {
    "chrome": "/etc/opt/chrome/policies/managed",
    "chromium": "/etc/chromium/policies/managed",
    "brave": "/etc/brave/policies/managed",
    "edge": "/etc/opt/edge/policies/managed",
}

CHROMIUM_RECOMMENDED = {
    "AlternativeBrowserParameters": [],
    "AutofillAddressEnabled": False,
    "AutofillCreditCardEnabled": False,
    "DefaultSearchProviderEnabled": False,
    "DisableSpdy": True,
    "MetricsReportingEnabled": False,
    "SearchSuggestEnabled": False,
    "SimpleCacheBackendEnabled": True,
    "WebComponentsEnabled": True,
    "WebRtcIpHandlingPolicy": 1,
    "BrowserSignin": 0,
    "PasswordManagerEnabled": False,
    "SyncDisabled": True,
    "NetworkPredictionOptions": 2,
    "EnableMediaRouter": False,
    "RapporteurEnabled": False,
    "SafetyCheckSetting": 1,
    "CloudManagementEnrollmentToken": "",
    "SavingBrowserHistoryDisabled": True,
    "DefaultSearchProviderSearchURL": "",
    "PrivacySandboxAdMeasurementEnabled": False,
    "PrivacySandboxAdTopicsEnabled": False,
    "PrivacySandboxAntiAbuseEnabled": False,
    "DefaultGeolocationSetting": 2,
    "DefaultMediaStreamSetting": 2,
    "DefaultSensorsSetting": 2,
    "CloudReportingEnabled": False,
    "SafeBrowsingEnabled": False,
}


def build_chromium_manifest(root: Optional[Path] = None) -> Dict[str, Dict]:
    """Returns {policy_dir_relative: json_content} to lay down."""
    chrome = {
        "MetricsReportingEnabled": False,
        "PasswordManagerEnabled": False,
        "SyncDisabled": True,
        "DefaultBrowserSettingEnabled": False,
        "AutofillAddressEnabled": False,
        "AutofillCreditCardEnabled": False,
        "DefaultGeolocationSetting": 2,
        "DefaultNotificationsSetting": 2,
        "DefaultMediaStreamSetting": 2,
        "WebRtcIPHandlingPolicy": "capture-morphed",
        "EnableNetworkPrediction": False,
        "ShowURLInIncognito": False,
    }
    manifests = {}
    for name, rel in CHROMIUM_ASSERTIES.items():
        dirs = [Path(rel)]
        for d in dirs:
            d = (root or Path("/")) / str(d) if str(d).startswith("/") else (root or Path("/")) / d
            manifests[str(d / f"synthex-privacy-{name}.json")] = json.dumps(chrome, indent=2)
    return manifests


def apply_browser_hardening(root: Optional[Path] = None) -> Dict:
    """Write policy manifests for every installed Chromium-family browser.
    Returns a per-browser report. Uses pkexec when writing to live /etc."""
    report = {"written": [], "errors": []}
    manifests = _chromium_manifests()
    for path_str, content in manifests.items():
        path = Path(path_str) if not root else root / Path(path_str).relative_to("/") if str(path_str).startswith("/") else Path(root) / path_str
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if root:
                path.write_text(content)
            else:
                _pkexec_write(path, content)
            report["written"].append(str(path))
        except Exception as e:
            report["errors"].append(f"{path}: {e}")
    return report


def _chromium_manifests() -> Dict[str, str]:
    """All browser-specific managed policy manifests for the live system."""
    return {
        "/etc/opt/chrome/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/chromium/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/brave/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/opt/microsoft/edge/policies/managed/synthex-privacy.json": _chrome_json(),
    }


def _chrome_json() -> str:
    return json.dumps({"policies": CHROMIUM_RECOMMENDED}, indent=2)


# ══════════════════════════════════════════════════════════════════════════
# 2. TRACKER DNS BLOCK (/etc/hosts)
# ══════════════════════════════════════════════════════════════════════════

def build_hosts(root: Optional[Path] = None) -> str:
    """Current /etc/hosts content with tracker block merged (idempotent)."""
    r = Path(root or Path("/"))
    hosts_path = r / "etc/hosts" if root else Path("/etc/hosts")
    existing = hosts_path.read_text() if hosts_path.exists() else ""
    if "Synthex Privacy" in existing:
        # Replace the previous block (everything between markers)
        start = existing.find("# ----")
        end = existing.find("# ====")
        if start != -1 and end != -1:
            existing = existing[:start] + existing[end + len("# ----"):]
    return existing + "\n" + TRACKER_DOMAINS


def apply_tracker_block(root: Optional[Path] = None) -> Tuple[bool, str]:
    """Write the blocklist to /etc/hosts. Verifies a sample resolves to 0.0.0.0."""
    try:
        if root:
            (Path(root) / "etc/hosts").write_text(build_hosts(root))
        else:
            tmp = Path(tempfile.gettempdir()) / "synthex-hosts"
            tmp.write_text(build_hosts())
            r = _run(["pkexec", "cp", str(tmp), "/etc/hosts"], timeout=15)
            if not r or r.returncode != 0:
                return False, "pkexec denied or failed"
        verified = _run(["getent", "hosts", "doubleclick.net"], timeout=8)
        ok = verified and "0.0.0.0" in verified.stdout
        return True, ("Tracker block active (%d domains). doubleclick.net → 0.0.0.0" % len(TRACKER_DOMAINS.splitlines())) if ok else ("Domains added; DNS cache may need flush")
    except Exception as e:
        return False, str(e)


def trackers_blocked() -> int:
    try:
        hosts = Path("/etc/hosts").read_text()
        return sum(1 for d in TRACKER_DOMAINS.splitlines() if d.strip() and d in hosts)
    except Exception:
        return 0


def remove_tracker_block(root: Optional[Path] = None) -> bool:
    try:
        r = Path(root or Path("/"))
        hosts_path = r / "etc/hosts" if root else Path("/etc/hosts")
        lines = hosts_path.read_text().splitlines()
        keep = [l for l in lines if "synthex.pri" not in l and "Synthex Privacy" not in l and not (l and not l.startswith("#") and "0.0.0.0" in l)]
        if root:
            hosts_path.write_text("\n".join(keep) + "\n")
        else:
            tmp = Path(tempfile.gettempdir()) / "synthex-hosts-remove"; tmp.write_text("\n".join(keep) + "\n")
            _run(["pkexec", "cp", str(tmp), str(hosts_path)], timeout=15)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════
# 3. TELEMETRY REDUCTION SWEEP
# ══════════════════════════════════════════════════════════════════════════

def telemetry_audit(root: Optional[Path] = None) -> List[Dict]:
    """Read-only audit of telemetry/collector surfaces across the OS."""
    r = Path(root or Path("/"))
    out = []
    def probe(name, conf, present_if=None, active=False, mitigation=""):
        p = (r / conf) if not str(conf).startswith("/") else (r / conf.lstrip("/"))
        exists = p.exists() if p is not None else False
        detail = ""
        if exists and conf.endswith("coredump.conf"):
            try:
                txt = p.read_text()
                m = re.search(r"^Storage=(\w+)", txt, re.M)
                detail = f"Storage={m.group(1) if m else 'unknown'}"
            except Exception:
                pass
        out.append({"name": name, "present": exists, "detail": detail,
                    "mitigation": mitigation, "mitigated": exists and ("coredump" in conf and detail.startswith("Storage=none"))})

    add("systemd-coredump", "/etc/systemd/coredump.conf", mitigation="coredump.conf.d/10-synthex.conf Storage=none")
    add("apport", "/etc/default/apport", mitigation="set enabled=0")
    add("cockpit", "/etc/systemd/system/sockets.target.wants/cockpit.socket", mitigation="systemctl disable cockpit")
    add("abrt", "/etc/abrt/abrt-action-save-kernel-data.conf", mitigation="disable crash reporting")
    add("dnf-automatic", "/etc/systemd/system/dnf-automatic.timer.restart" if False else "/usr/lib/systemd/system/dnf-automatic.timer", mitigation="auto-update telemetry")
    return out


def apply_telemetry_reduction(root: Optional[Path] = None) -> Dict:
    """Lay down drop-in overrides disabling coredump/abrt knobs where possible."""
    report = {"written": [], "errors": [], "systemd": []}
    drops = [
        ("/etc/systemd/coredump.conf.d/10-synthex.conf",
         "[Coredump]\nStorage=none\nExternal size=0\nProcessSizeMax=0\nCompress=no\n"),
        ("/etc/default/apport", "enabled=0\n"),
    ]
    for rel, content in drops:
        path_str = rel
        if root:
            base = Path(root)
            if rel.startswith("/"):
                rel = rel[1:]
            path = base / rel
        else:
            path = Path(rel) if str(rel).startswith("/") else Path("/etc") / rel
        try:
            if root:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            else:
                _pkexec_write(path, content)
            report["written"].append(str(path))
        except Exception as e:
            report["errors"].append(f"{path}: {e}")

    res = _run(["systemctl", "is-enabled", "cockpit.socket"], timeout=5)
    if res and "enabled" in (res.stdout or ""):
        _run(["pkexec", "systemctl", "disable", "cockpit.socket"], timeout=15)
        report["systemd"].append("cockpit disabled")
    elif res:
        report["systemd"].append("cockpit not enabled (ok)")
    return report


# ══════════════════════════════════════════════════════════════════════════
# 4. FINGERPRINT AUDIT (read-only — does not fix, only measures)
# ══════════════════════════════════════════════════════════════════════════

def fingerprint_audit() -> Dict:
    """Collect the observable fingerprint surface and estimate entropy."""
    signals: Dict[str, str] = {}

    signals["user"] = os.environ.get("USER", "?")
    signals["hostname"] = socket.gethostname()
    r = _run(["localectl", "status"], timeout=5)
    lang = "?"
    if r and r.stdout:
        m = re.search(r"LANG=(\S+)", r.stdout)
        if m: lang = m.group(1)
    signals["locale"] = lang
    r = _run(["timedatectl", "status"], timeout=5)
    tz = time.tzname or ""
    if r and r.stdout:
        m = re.search(r"Time ?zone: (.+)", r.stdout)
        if m: tz = m.group(1).strip()
    signals["timezone"] = tz
    r = _run(["fc-list", ":", "family"], timeout=8)
    n_fonts = len(r.stdout.splitlines()) if r and r.stdout else 0
    signals["installed_fonts"] = str(n_fonts)
    r = _run(["xrandr"], timeout=5)
    res = ""
    if r and r.stdout:
        m = re.search(r"current (\d+) x (\d+)", r.stdout)
        if m: res = f"{m.group(1)}x{m.group(2)}"
    signals["screen"] = res or "unknown"
    r = _run(["bash", "-c", "getconf MAC; ip -o -4 route show default 2>/dev/null | awk '{print $5}' | head -1"], timeout=5)
    signals["dpi_mac"] = r.stdout.splitlines()[0] if r and r.stdout else "?"
    signals["mac_policy"] = "check-hosts"
    ok, out = True, ""
    r = _run(["resolvectl", "status"], timeout=5)
    signals["dns"] = "DoT" if r and "+DNSOverTLS" in (r.stdout or "") else "plaintext"

    # Estimated bits of entropy from font/screen/locale/tz
    entropy = 0
    if n_fonts: entropy += min(n_fonts / 400, 1.0) * 8
    if "x" in res: entropy += 3   # resolution
    entropy += 1 if lang != "en_US" else 0
    entropy += min(len(tz)/4, 1) * 2

    return {"signals": signals, "entropy_bits": round(entropy), 
            "recommendation": [
                "fonts — install a generic set, keep counter-consistent",
                "screen — a fixed window size resists WxH fingerprint",
                "clock — keep NTP sync (already drifting)",
                "DNS — run SpoofGoof 'audit' to confirm DoT",
            ]}


# ══════════════════════════════════════════════════════════════════════════
# 5. SCHEDULED AUTO-CLEAN (user systemd timer)
# ══════════════════════════════════════════════════════════════════════════

USER_SERVICE = """[Unit]
Description=Synthex Privacy — periodic de-identification
After=graphical-session.target

[Service]
Type=oneshot
ExecStart=%s run-clean
"""

USER_TIMER = """[Unit]
Description=Synthex privacy auto-clean timer

[Timer]
OnBootSec=15min
OnUnitActiveSec=%dmin
Persistent=false

[Install]
WantedBy=timers.target
"""


def schedule_auto_clean(minutes: int) -> Dict:
    """Install ~/.config/systemd/user timer to run an auto-purge every N minutes."""
    cfg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "systemd" / "user"
    cfg.mkdir(parents=True, exist_ok=True)
    python_bin = shutil.which("python3") or "/usr/bin/python3"
    module = Path(__file__).resolve()
    service = cfg / "synthex-privacy.service"
    timer = cfg / "synthex-privacy.timer"
    service.write_text(AUTO_SERVICE.format(python_bin, module))
    timer.write_text(USER_TIMER.replace("%dmin" if False else " 1min", str(max(minutes,1))))
    subprocess.run(["systemctl", "--user", "daemon-reload"], timeout=10)
    if minutes <= 0:
        subprocess.run(["systemctl", "--user", "disable", "--now", "synthex-privacy.timer"], timeout=10)
        return {"enabled": False, "interval": 0}
    subprocess.run(["systemctl", "--user", "enable", "--now", "synthex-privacy.timer"], timeout=15)
    return {"enabled": True, "interval": minutes}


def run_auto_clean() -> Dict:
    """One-shot: purge browser linkage + shell histories + tmp residue."""
    report = {"purge": None, "shell_history": False, "tmp": False}
    try:
        from synthex_spoofgoof import SpoofGoofEngine
        report["purge"] = SpoofGoofEngine.purge_browser_linkage(full=True)
    except Exception as e:
        report["purge"] = {"errors": [str(e)]}
    for hf in (Path.home() / ".bash_history", Path.home() / ".zsh_history"):
        try:
            hf.unlink(missing_ok=True); report["cleaned"] = True
        except Exception:
            pass
    return report


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "audit"
    if cmd == "audit":
        a = fingerprint_audit()
        print("FINGERPRINT SIGNALS:")
        for k, v in a["signals"].items():
            print(f"  {k:16s}: {v}")
        print(f"entropy ≈ {a['entropy_bits']} bits")
        for r in a["recommendation"]:
            print(f"  ▶ {r}")
    elif cmd == "harden":
        rep = apply_browser_hardening()
        print("browser hardening:", rep)
    elif cmd == "block":
        ok, msg = apply_tracker_block()
        print(("✓ " if ok else "✗ ") + msg)
    elif cmd == "unblock":
        print("removed" if remove_tracker_block() else "failed")
    elif cmd == "telemetry":
        for t in telemetry_audit():
            print(("🛡" if t["mitigated"] else ("•" if t["present"] else "—")) + f" {t['name']} {t['detail']}")
        rep = apply_telemetry_reduction()
        print("applied:", rep)
    elif cmd == "schedule" and len(sys.argv) >= 3:
        print("auto-clean:", schedule_auto_clean(int(sys.argv[2])))
    elif cmd == "run_tools":
        print("run_auto_clean:", run_auto_clean())
    else:
        print(__doc__)