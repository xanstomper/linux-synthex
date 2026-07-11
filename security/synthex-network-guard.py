#!/usr/bin/env python3
"""
synthex-network-guard.py — SynthOS Intelligent Network Guardian
================================================================
Features:
  • 7-day baseline learning phase — learns normal traffic patterns
  • Alerts on anomalous connections (new IPs, unusual ports, large uploads)
  • DNS-over-HTTPS enforced via a local DoH proxy (dnscrypt-proxy / stubby)
  • Automatic blocklist updates from multiple threat intel feeds
  • Real-time network map in a GTK4/Adwaita window (or terminal fallback)
  • CLI: synthex-network-guard [start|status|learn|block|unblock|show-map]

GPL-3.0-or-later  |  SynthOS Project 2026.10
"""

from __future__ import annotations

import argparse
import collections
import datetime
import json
import logging
import logging.handlers
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_DIR     = Path.home() / ".config" / "synthex-network-guard"
STATE_FILE     = CONFIG_DIR / "state.json"
BASELINE_FILE  = CONFIG_DIR / "baseline.json"
BLOCKLIST_FILE = CONFIG_DIR / "blocklist.txt"
LOG_DIR        = Path.home() / ".local" / "share" / "synthex" / "network-guard"
LOG_FILE       = LOG_DIR / "guard.log"

LEARN_DAYS     = 7
POLL_INTERVAL  = 10        # seconds between connection polls
ALERT_COOLDOWN = 300       # seconds before re-alerting same anomaly
LARGE_UPLOAD_THRESHOLD_MB = 50

BLOCKLIST_FEEDS = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
    "https://urlhaus.abuse.ch/downloads/hostfile/",
    "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/hosts/pro.txt",
]

DOH_PROXY_CONF = "/etc/dnscrypt-proxy/dnscrypt-proxy.toml"
STUBBY_CONF    = "/etc/stubby/stubby.yml"

APP_ID = "org.synthex.NetworkGuard"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("synthex-network-guard")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    if not log.handlers:
        log.addHandler(fh)
        log.addHandler(sh)
    return log


LOG = _setup_logging()


# ---------------------------------------------------------------------------
# State & baseline helpers
# ---------------------------------------------------------------------------
def _load_json(path: Path, default: dict | list) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return default


def _save_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def _load_state() -> dict:
    return _load_json(STATE_FILE, {
        "phase": "learning",
        "learn_start": datetime.datetime.now().isoformat(),
        "blocked_ips": [],
        "whitelisted_ips": [],
        "doh_enabled": False,
    })


def _save_state(s: dict) -> None:
    _save_json(STATE_FILE, s)


# ---------------------------------------------------------------------------
# Connection snapshot via `ss`
# ---------------------------------------------------------------------------
def _get_connections() -> list[dict]:
    """Return list of active TCP/UDP connections as dicts."""
    conns = []
    try:
        out = subprocess.check_output(
            ["ss", "-tunp", "--no-header"],
            text=True, timeout=10
        )
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue
            proto   = parts[0]
            state   = parts[1]
            local   = parts[4]
            remote  = parts[5]
            proc    = " ".join(parts[6:]) if len(parts) > 6 else ""
            remote_ip = remote.rsplit(":", 1)[0].strip("[]")
            remote_port_str = remote.rsplit(":", 1)[-1]
            try:
                remote_port = int(remote_port_str)
            except ValueError:
                remote_port = 0
            conns.append({
                "proto": proto,
                "state": state,
                "local": local,
                "remote": remote,
                "remote_ip": remote_ip,
                "remote_port": remote_port,
                "proc": proc,
                "ts": datetime.datetime.now().isoformat(),
            })
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        LOG.warning("ss failed: %s", exc)
    return conns


# ---------------------------------------------------------------------------
# Baseline (learning phase)
# ---------------------------------------------------------------------------
class Baseline:
    def __init__(self) -> None:
        raw = _load_json(BASELINE_FILE, {
            "ips": {}, "ports": {}, "samples": 0, "updated": None
        })
        # ip -> count, port -> count
        self.ips:   dict[str, int] = raw.get("ips", {})
        self.ports: dict[str, int] = raw.get("ports", {})
        self.samples: int          = raw.get("samples", 0)
        self.updated: Optional[str] = raw.get("updated")

    def record(self, conns: list[dict]) -> None:
        for c in conns:
            ip = c["remote_ip"]
            if ip and ip not in ("0.0.0.0", "[::]", "*", ""):
                self.ips[ip] = self.ips.get(ip, 0) + 1
            port = str(c["remote_port"])
            if port != "0":
                self.ports[port] = self.ports.get(port, 0) + 1
        self.samples += 1
        self.updated = datetime.datetime.now().isoformat()
        self._persist()

    def _persist(self) -> None:
        _save_json(BASELINE_FILE, {
            "ips": self.ips,
            "ports": self.ports,
            "samples": self.samples,
            "updated": self.updated,
        })

    def is_known_ip(self, ip: str) -> bool:
        return ip in self.ips

    def is_known_port(self, port: int) -> bool:
        return str(port) in self.ports

    def top_ips(self, n: int = 10) -> list[tuple[str, int]]:
        return sorted(self.ips.items(), key=lambda x: x[1], reverse=True)[:n]

    def top_ports(self, n: int = 10) -> list[tuple[str, int]]:
        return sorted(self.ports.items(), key=lambda x: x[1], reverse=True)[:n]


# ---------------------------------------------------------------------------
# Blocklist management
# ---------------------------------------------------------------------------
class Blocklist:
    def __init__(self) -> None:
        self._hosts: set[str] = set()
        self._custom_ips: set[str] = set()
        self._load()

    def _load(self) -> None:
        if BLOCKLIST_FILE.exists():
            for line in BLOCKLIST_FILE.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self._hosts.add(line.lower())
        state = _load_state()
        self._custom_ips = set(state.get("blocked_ips", []))

    def update_from_feeds(self) -> int:
        """Download blocklist feeds, parse, merge, persist. Returns new count."""
        new_hosts: set[str] = set()
        for url in BLOCKLIST_FEEDS:
            try:
                LOG.info("Fetching blocklist: %s", url)
                with urllib.request.urlopen(url, timeout=30) as resp:
                    for raw in resp:
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if line.startswith("#") or not line:
                            continue
                        # hosts-file format: "0.0.0.0 badhost.com"
                        parts = line.split()
                        if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1"):
                            new_hosts.add(parts[1].lower())
                        elif len(parts) == 1:
                            new_hosts.add(parts[0].lower())
            except Exception as exc:
                LOG.warning("Feed %s failed: %s", url, exc)
        self._hosts.update(new_hosts)
        BLOCKLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        BLOCKLIST_FILE.write_text(
            "# SynthOS Network Guard blocklist — updated "
            + datetime.datetime.now().isoformat() + "\n"
            + "\n".join(sorted(self._hosts))
        )
        LOG.info("Blocklist updated: %d entries", len(self._hosts))
        return len(new_hosts)

    def is_blocked_host(self, host: str) -> bool:
        return host.lower() in self._hosts

    def is_blocked_ip(self, ip: str) -> bool:
        return ip in self._custom_ips

    def block_ip(self, ip: str) -> None:
        self._custom_ips.add(ip)
        # Apply with iptables
        if os.geteuid() == 0:
            subprocess.run(
                ["iptables", "-I", "OUTPUT", "-d", ip, "-j", "DROP"],
                check=False, capture_output=True
            )
        state = _load_state()
        blocked = state.get("blocked_ips", [])
        if ip not in blocked:
            blocked.append(ip)
        state["blocked_ips"] = blocked
        _save_state(state)
        LOG.info("Blocked IP: %s", ip)

    def unblock_ip(self, ip: str) -> None:
        self._custom_ips.discard(ip)
        if os.geteuid() == 0:
            subprocess.run(
                ["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"],
                check=False, capture_output=True
            )
        state = _load_state()
        blocked = state.get("blocked_ips", [])
        state["blocked_ips"] = [b for b in blocked if b != ip]
        _save_state(state)
        LOG.info("Unblocked IP: %s", ip)


# ---------------------------------------------------------------------------
# DoH proxy setup
# ---------------------------------------------------------------------------
def _setup_doh_proxy(log: logging.Logger) -> bool:
    """Enable DNS-over-HTTPS via dnscrypt-proxy or stubby."""
    for svc in ("dnscrypt-proxy", "stubby"):
        if shutil.which(svc) or Path(f"/usr/sbin/{svc}").exists():
            try:
                subprocess.run(
                    ["systemctl", "enable", "--now", svc],
                    check=True, capture_output=True
                )
                log.info("DoH proxy enabled via %s", svc)
                # Point systemd-resolved at loopback
                resolved_conf = Path("/etc/systemd/resolved.conf.d/doh.conf")
                resolved_conf.parent.mkdir(parents=True, exist_ok=True)
                resolved_conf.write_text(
                    "[Resolve]\nDNS=127.0.0.1\nDNSOverTLS=opportunistic\n"
                )
                subprocess.run(
                    ["systemctl", "restart", "systemd-resolved"],
                    check=False, capture_output=True
                )
                state = _load_state()
                state["doh_enabled"] = True
                _save_state(state)
                return True
            except subprocess.CalledProcessError as exc:
                log.warning("%s failed: %s", svc, exc)
    log.warning("No DoH proxy found (install dnscrypt-proxy or stubby)")
    return False


# ---------------------------------------------------------------------------
# Anomaly detector
# ---------------------------------------------------------------------------
class AnomalyDetector:
    def __init__(self, baseline: Baseline, blocklist: Blocklist):
        self._bl  = baseline
        self._bk  = blocklist
        self._seen_alerts: dict[str, float] = {}  # key -> last alert time

    def _should_alert(self, key: str) -> bool:
        now = time.time()
        last = self._seen_alerts.get(key, 0)
        if now - last >= ALERT_COOLDOWN:
            self._seen_alerts[key] = now
            return True
        return False

    def check(self, conns: list[dict]) -> list[str]:
        alerts = []
        for c in conns:
            ip   = c["remote_ip"]
            port = c["remote_port"]
            if not ip or ip in ("0.0.0.0", "[::]", "*"):
                continue

            # Blocked IP
            if self._bk.is_blocked_ip(ip):
                key = f"blocked:{ip}"
                if self._should_alert(key):
                    msg = f"🚫 BLOCKED IP connection attempt: {ip}:{port}  proc={c['proc']}"
                    alerts.append(msg)
                continue

            # New / unknown IP
            if not self._bl.is_known_ip(ip):
                key = f"new_ip:{ip}"
                if self._should_alert(key):
                    alerts.append(
                        f"⚠ NEW IP: {ip}:{port}  proto={c['proto']}  proc={c['proc']}"
                    )

            # Unusual port (not in baseline)
            if port and not self._bl.is_known_port(port) and port not in (80, 443, 53, 22):
                key = f"new_port:{port}"
                if self._should_alert(key):
                    alerts.append(
                        f"⚠ UNUSUAL PORT: {ip}:{port}  proto={c['proto']}  proc={c['proc']}"
                    )

        return alerts


# ---------------------------------------------------------------------------
# Network traffic monitor (upload anomaly detection via /proc/net/dev)
# ---------------------------------------------------------------------------
def _get_bytes_sent() -> int:
    total = 0
    try:
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
            parts = line.split()
            if len(parts) >= 10:
                total += int(parts[9])  # bytes transmitted
    except Exception:
        pass
    return total


# ---------------------------------------------------------------------------
# GTK4 real-time network map
# ---------------------------------------------------------------------------
def _launch_gtk_map() -> None:
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Gtk, Adw, GLib
    except (ImportError, ValueError):
        LOG.warning("GTK4/libadwaita not available — using terminal map")
        _terminal_map()
        return

    class NetworkMapWindow(Adw.ApplicationWindow):
        def __init__(self, app):
            super().__init__(application=app)
            self.set_title("SynthOS Network Guard — Live Map")
            self.set_default_size(900, 600)
            self._baseline = Baseline()
            self._blocklist = Blocklist()

            hb = Adw.HeaderBar()
            refresh_btn = Gtk.Button(label="⟳ Refresh")
            refresh_btn.connect("clicked", lambda _: self._refresh())
            hb.pack_end(refresh_btn)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
            box.append(hb)

            self._store = Gtk.ListStore(str, str, str, str, str)
            tv = Gtk.TreeView(model=self._store)
            for i, col in enumerate(["Proto", "State", "Local", "Remote", "Process"]):
                renderer = Gtk.CellRendererText()
                tvc = Gtk.TreeViewColumn(col, renderer, text=i)
                tvc.set_resizable(True)
                tvc.set_min_width(120)
                tv.append_column(tvc)

            sw = Gtk.ScrolledWindow()
            sw.set_vexpand(True)
            sw.set_child(tv)

            self._status_bar = Gtk.Label(label="Loading…", xalign=0)
            self._status_bar.add_css_class("caption")

            box.append(sw)
            box.append(self._status_bar)
            self.set_content(box)

            GLib.timeout_add_seconds(5, self._refresh)
            self._refresh()

        def _refresh(self) -> bool:
            conns = _get_connections()
            self._store.clear()
            for c in conns:
                ip = c["remote_ip"]
                color_tag = "🔴" if self._blocklist.is_blocked_ip(ip) else (
                    "🟡" if not self._baseline.is_known_ip(ip) else "🟢"
                )
                self._store.append([
                    c["proto"],
                    c["state"],
                    c["local"],
                    f"{color_tag} {c['remote']}",
                    c["proc"][:60],
                ])
            self._status_bar.set_text(
                f"{len(conns)} connections — updated {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            return True  # keep running

    class NetworkGuardApp(Adw.Application):
        def __init__(self):
            super().__init__(application_id=APP_ID)
            self.connect("activate", self._on_activate)

        def _on_activate(self, app):
            win = NetworkMapWindow(app)
            win.present()

    NetworkGuardApp().run(sys.argv[:1])


def _terminal_map() -> None:
    """Fallback terminal network map (no GTK)."""
    baseline  = Baseline()
    blocklist = Blocklist()
    try:
        while True:
            conns = _get_connections()
            os.system("clear")
            print(f"{'='*70}")
            print("  SynthOS Network Guard — Live Map   "
                  f"[{datetime.datetime.now().strftime('%H:%M:%S')}]")
            print(f"{'='*70}")
            print(f"  {'PROTO':<6} {'STATE':<12} {'REMOTE':35} {'PROCESS'}")
            print(f"  {'-'*65}")
            for c in conns[:30]:
                ip = c["remote_ip"]
                tag = "🔴" if blocklist.is_blocked_ip(ip) else (
                    "🟡" if not baseline.is_known_ip(ip) else "🟢"
                )
                print(
                    f"  {c['proto']:<6} {c['state']:<12} "
                    f"{tag} {c['remote']:<33} {c['proc'][:30]}"
                )
            print(f"\n  Total: {len(conns)} connections    [Ctrl-C to exit]")
            time.sleep(3)
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------------------
# Main monitoring loop
# ---------------------------------------------------------------------------
class NetworkGuardDaemon:
    def __init__(self) -> None:
        self._baseline  = Baseline()
        self._blocklist = Blocklist()
        self._detector  = AnomalyDetector(self._baseline, self._blocklist)
        self._stop      = threading.Event()
        self._prev_bytes_sent = _get_bytes_sent()
        self._prev_ts         = time.time()

    def _check_large_upload(self) -> Optional[str]:
        now     = time.time()
        current = _get_bytes_sent()
        dt      = now - self._prev_ts
        if dt <= 0:
            return None
        rate_mbps = (current - self._prev_bytes_sent) / dt / 1024 / 1024
        self._prev_bytes_sent = current
        self._prev_ts         = now
        if rate_mbps > LARGE_UPLOAD_THRESHOLD_MB:
            return f"⚠ LARGE UPLOAD detected: {rate_mbps:.1f} MB/s"
        return None

    def _alert(self, msg: str) -> None:
        LOG.warning(msg)
        try:
            subprocess.run(
                ["notify-send", "--urgency=critical", "SynthOS Network Guard", msg],
                check=False, capture_output=True, timeout=3
            )
        except Exception:
            pass

    def run(self) -> None:
        state = _load_state()
        learn_start = datetime.datetime.fromisoformat(
            state.get("learn_start", datetime.datetime.now().isoformat())
        )
        LOG.info("Network Guard started — phase: %s", state.get("phase", "learning"))

        # Start blocklist update in background
        threading.Thread(
            target=self._blocklist.update_from_feeds, daemon=True
        ).start()

        while not self._stop.is_set():
            conns = _get_connections()
            state = _load_state()
            phase = state.get("phase", "learning")

            if phase == "learning":
                self._baseline.record(conns)
                elapsed_days = (
                    datetime.datetime.now() - learn_start
                ).total_seconds() / 86400
                if elapsed_days >= LEARN_DAYS:
                    state["phase"] = "monitoring"
                    _save_state(state)
                    LOG.info(
                        "Learning phase complete (%d samples) — switching to monitoring",
                        self._baseline.samples,
                    )
            else:
                # Monitoring: detect anomalies
                alerts = self._detector.check(conns)
                for msg in alerts:
                    self._alert(msg)
                upload_alert = self._check_large_upload()
                if upload_alert:
                    self._alert(upload_alert)

            self._stop.wait(POLL_INTERVAL)

        LOG.info("Network Guard stopped")

    def stop(self) -> None:
        self._stop.set()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="synthex-network-guard",
        description="SynthOS intelligent network guardian",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("start",      help="Start the guardian daemon")
    sub.add_parser("status",     help="Show current state and baseline summary")
    sub.add_parser("show-map",   help="Open live network map (GTK4 or terminal)")
    sub.add_parser("learn",      help="Force-reset to learning phase")
    sub.add_parser("update-blocklist", help="Update threat intel blocklists now")
    sub.add_parser("enable-doh", help="Enable DNS-over-HTTPS proxy")

    blk = sub.add_parser("block",   help="Block an IP address")
    blk.add_argument("ip")
    unb = sub.add_parser("unblock", help="Unblock an IP address")
    unb.add_argument("ip")

    args = ap.parse_args(argv)

    if args.cmd == "start":
        d = NetworkGuardDaemon()
        signal.signal(signal.SIGTERM, lambda *_: d.stop())
        signal.signal(signal.SIGINT,  lambda *_: d.stop())
        d.run()

    elif args.cmd == "status":
        state    = _load_state()
        baseline = Baseline()
        print(f"\n{'='*55}")
        print("  SynthOS Network Guard — Status")
        print(f"{'='*55}")
        print(f"  Phase           : {state.get('phase', 'learning')}")
        print(f"  Learn start     : {state.get('learn_start', '—')}")
        print(f"  Baseline samples: {baseline.samples}")
        print(f"  Known IPs       : {len(baseline.ips)}")
        print(f"  Known ports     : {len(baseline.ports)}")
        print(f"  Blocked IPs     : {state.get('blocked_ips', [])}")
        print(f"  DoH enabled     : {state.get('doh_enabled', False)}")
        print(f"\n  Top 5 IPs:")
        for ip, cnt in baseline.top_ips(5):
            print(f"    {ip:<40} {cnt:>6} hits")
        print(f"\n  Top 5 ports:")
        for port, cnt in baseline.top_ports(5):
            print(f"    {port:<10} {cnt:>6} hits")
        print(f"{'='*55}\n")

    elif args.cmd == "show-map":
        _launch_gtk_map()

    elif args.cmd == "learn":
        state = _load_state()
        state["phase"]       = "learning"
        state["learn_start"] = datetime.datetime.now().isoformat()
        _save_state(state)
        _save_json(BASELINE_FILE, {"ips": {}, "ports": {}, "samples": 0})
        print("[network-guard] Reset to learning phase")

    elif args.cmd == "update-blocklist":
        bl = Blocklist()
        n = bl.update_from_feeds()
        print(f"[network-guard] Blocklist updated: {n} new entries")

    elif args.cmd == "enable-doh":
        _setup_doh_proxy(LOG)

    elif args.cmd == "block":
        Blocklist().block_ip(args.ip)
        print(f"[network-guard] Blocked: {args.ip}")

    elif args.cmd == "unblock":
        Blocklist().unblock_ip(args.ip)
        print(f"[network-guard] Unblocked: {args.ip}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
