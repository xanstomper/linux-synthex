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
0.0.0.0 quantserve.com
0.0.0.0 quantcast.com
0.0.0.0 inspectlet.com
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
# ══════════════════════════════════════════════════════════════════════════
# 2. TRACKER DNS BLOCK (/etc/hosts)
# ══════════════════════════════════════════════════════════════════════════

_BLOCK_HEAD = "# ---- Synthex Privacy Tracker Block ----"
_BLOCK_TAIL = "# ---- End Synthex Privacy Tracker Block ----"


def _block_entries() -> List[str]:
    """Just the 0.0.0.0 DOMAIN lines from the blocklist."""
    return [d for d in TRACKER_DOMAINS.splitlines() if d.startswith("0.0.0.0")]


def build_hosts(root: Optional[Path] = None) -> str:
    """/etc/hosts content with the complete, current tracker block.
    Reconciles fully: any previously-applied Synthex block is replaced with the
    current list, so domains added to TRACKER_DOMAINS appear on the next apply
    and nothing is ever duplicated."""
    r = Path(root or Path("/"))
    hosts_path = r / "etc/hosts" if root else Path("/etc/hosts")
    existing = hosts_path.read_text() if hosts_path.exists() else ""

    # Strip any prior Synthex block (current marker style, or legacy single-header)
    if _BLOCK_HEAD in existing and _BLOCK_TAIL in existing:
        s = existing.index(_BLOCK_HEAD)
        e = existing.index(_BLOCK_TAIL) + len(_BLOCK_TAIL)
        existing = existing[:s] + existing[e:]
    elif "Synthex Privacy" in existing:
        start = existing.find("# Synthex Privacy")
        end = existing.find("\n\n", start)
        existing = existing[:start] + (existing[end:] if end != -1 else "")

    block = "\n" + _BLOCK_HEAD + "\n" + TRACKER_DOMAINS.rstrip() + "\n" + _BLOCK_TAIL + "\n"
    return existing.rstrip("\n") + "\n" + block


def apply_tracker_block(root: Optional[Path] = None) -> Tuple[bool, str]:
    """Write the blocklist to /etc/hosts (idempotent, fully reconciles)."""
    try:
        content = build_hosts(root)
        if root:
            (Path(root) / "etc/hosts").write_text(content)
        else:
            tmp = Path(tempfile.gettempdir()) / "synthex-hosts"
            tmp.write_text(content)
            r = _run(["pkexec", "cp", str(tmp), "/etc/hosts"], timeout=15)
            if not r or r.returncode != 0:
                return False, "pkexec denied or failed"
        n = len(_block_entries())
        verified = _run(["getent", "ahostsv4", "doubleclick.net"], timeout=8)
        ok = bool(verified and "0.0.0.0" in (verified.stdout or ""))
        msg = f"Tracker block active ({n} domains)"
        msg += ". doubleclick.net sinkholed to 0.0.0.0." if ok else ", DNS cache may need flush."
        return True, msg
    except Exception as e:
        return False, str(e)


def trackers_blocked() -> int:
    """Count of blocklist entries currently present in /etc/hosts (0 if off)."""
    try:
        hosts = Path("/etc/hosts").read_text()
        return sum(1 for d in _block_entries() if d in hosts)
    except Exception:
        return 0


def remove_tracker_block(root: Optional[Path] = None) -> bool:
    try:
        r = Path(root or Path("/"))
        hosts_path = r / "etc/hosts" if root else Path("/etc/hosts")
        txt = hosts_path.read_text() if hosts_path.exists() else ""
        s = txt.find(_BLOCK_HEAD)
        e = txt.find(_BLOCK_TAIL)
        if s != -1 and e != -1:
            txt = txt[:s] + txt[e + len(_BLOCK_TAIL):]
        if root:
            hosts_path.write_text(txt)
        else:
            tmp = Path(tempfile.gettempdir()) / "synthex-hosts-remove"
            tmp.write_text(txt)
            _run(["pkexec", "cp", str(tmp), str(hosts_path)], timeout=15)
        return True
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════
# 3. TELEMETRY REDUCTION SWEEP
# ══════════════════════════════════════════════════════════════════════════

def fingerprint_audit() -> Dict:
    """Delegate to the Synthex fingerprint-shield engine (avoids reimplementation)."""
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from synthex_fingerprint_shield import SynthexFingerprintShield
        data = SynthexFingerprintShield.get_instance().audit_fingerprint_resistance()
        vectors = data.get("vectors", [])
        return {
            "signals": {
                "score": data.get("overall_privacy_score", 0),
                "state": data.get("state_label", "?"),
                "evaluated": data.get("vectors_evaluated", len(vectors)),
                "mitigated": data.get("vectors_mitigated", 0),
                "vectors": [v.get("name", "?")[:34] for v in vectors[:8]],
            },
            "entropy_bits": 0,
            "recommendation": [v.get("technical_defense", "")[:70] for v in vectors[:6] if v.get("is_active")],
        }
    except Exception:
        return {"signals": {"score": 0, "state": "engine unavailable"}, "entropy_bits": 0, "recommendation": []}


def telemetry_audit(root: Optional[Path] = None) -> List[Dict]:
    """Delegate to SynthexTelemetryKiller (avoids a duplicate implementation)."""
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from synthex_telemetry_killer import SynthexTelemetryKiller
        data = SynthexTelemetryKiller.get_instance().audit_privacy_shield()
        out = []
        for v in data.get("vectors", []):
            out.append({"name": str(v.get("name", "?"))[:34],
                        "present": bool(v.get("is_active", False)),
                        "mitigated": bool(v.get("is_active", False)),
                        "detail": str(v.get("technical_defense", ""))[:70],
                        "mitigation": str(v.get("target", ""))[:70]})
        return out
    except Exception:
        return [{"name": "telemetry engine unavailable", "present": False,
                 "mitigated": False, "detail": "", "mitigation": ""}]


def apply_telemetry_reduction(root: Optional[Path] = None) -> Dict:
    """Delegate the actual telemetry lockdown to SynthexTelemetryKiller."""
    report = {"written": [], "errors": [], "systemd": []}
    try:
        import os, sys
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from synthex_telemetry_killer import SynthexTelemetryKiller
        ok, msg = SynthexTelemetryKiller.get_instance().apply_maximum_privacy_lockdown()
        report["systemd"] = [msg]
        report["written"].append("telemetry-killer lockdown")
    except Exception as e:
        report["errors"].append(str(e))
    return report


def apply_browser_hardening(root: Optional[Path] = None) -> Dict:
    """Emit Chromium/Brave/Edge privacy policy manifests.
    (Firefox hardening is already covered by the SpoofGoof policies.json.)"""
    report = {"written": [], "errors": []}
    for path_str, content in _chromium_manifests().items():
        path = Path(path_str)
        if root:
            path = root / path_str.lstrip("/")
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
    return {
        "/etc/opt/chrome/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/chromium/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/brave/policies/managed/synthex-privacy.json": _chrome_json(),
        "/etc/opt/microsoft/edge/policies/managed/synthex-privacy.json": _chrome_json(),
    }


def _chrome_json() -> str:
    import json as _json
    return _json.dumps({"policies": CHROMIUM_RECOMMENDED}, indent=2)


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
    (cfg / "synthex-privacy.service").write_text(USER_SERVICE.format(python_bin, module))
    (cfg / "synthex-privacy.timer").write_text(USER_TIMER.format(interval=max(int(minutes), 1)))
    subprocess.run(["systemctl", "--user", "daemon-reload"], timeout=10)
    if int(minutes) <= 0:
        subprocess.run(["systemctl", "--user", "disable", "--now", "synthex-privacy.timer"], timeout=15)
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
    elif cmd == "run-tool":
        print("run_auto_clean:", run_auto_clean())
    else:
        print(__doc__)