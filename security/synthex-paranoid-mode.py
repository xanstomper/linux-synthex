#!/usr/bin/env python3
"""
synthex-paranoid-mode.py — SynthOS Paranoid Mode Security System
=================================================================
When activated:
  • Disables all USB ports except pre-approved serial numbers
  • Enables full network packet logging to encrypted rotating logs
  • Takes periodic encrypted screenshots for audit trail
  • Blocks all outbound connections except explicitly whitelisted IPs
  • Monitors /etc/passwd, /etc/sudoers, crontabs for tampering
  • Provides: synthex-paranoid [enable|disable|status]

Requirements:
  python3, cryptography, pillow (screenshot), usbguard, iptables/nftables,
  tcpdump, gnupg, systemd

GPL-3.0-or-later  |  SynthOS Project 2026.10
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
CONFIG_DIR   = Path("/etc/synthex/paranoid")
STATE_FILE   = CONFIG_DIR / "state.json"
LOG_DIR      = Path("/var/log/synthex/paranoid")
SCREENSHOT_DIR = LOG_DIR / "screenshots"
NETLOG_DIR   = LOG_DIR / "network"
WATCH_FILES  = [
    Path("/etc/passwd"),
    Path("/etc/shadow"),
    Path("/etc/sudoers"),
    Path("/etc/sudoers.d"),
    Path("/etc/crontab"),
    Path("/var/spool/cron"),
]
WATCH_INTERVAL   = 30        # seconds between file-integrity checks
SCREENSHOT_INTERVAL = 300    # seconds between screenshots (5 min)
NETLOG_ROTATE    = 50 * 1024 * 1024  # rotate after 50 MB
DAEMON_PID_FILE  = Path("/run/synthex-paranoid.pid")
ENCRYPTION_KEY_FILE = CONFIG_DIR / "paranoid.key"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("synthex-paranoid")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.handlers.RotatingFileHandler(
        LOG_DIR / "paranoid.log", maxBytes=10 * 1024 * 1024, backupCount=5
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)
    return log


# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------
def _generate_key() -> bytes:
    """Generate and persist a Fernet key for log encryption."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return b""
    ENCRYPTION_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if ENCRYPTION_KEY_FILE.exists():
        return ENCRYPTION_KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    ENCRYPTION_KEY_FILE.write_bytes(key)
    ENCRYPTION_KEY_FILE.chmod(0o600)
    return key


def _encrypt_file(path: Path, key: bytes) -> Optional[Path]:
    """Encrypt *path* in-place, returning the .enc output path."""
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        f = Fernet(key)
        enc = f.encrypt(path.read_bytes())
        out = path.with_suffix(path.suffix + ".enc")
        out.write_bytes(enc)
        path.unlink()
        return out
    except Exception as exc:
        logging.getLogger("synthex-paranoid").warning("Encryption failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# USB guard
# ---------------------------------------------------------------------------
def _load_approved_usb() -> list[str]:
    cfg = _load_state()
    return cfg.get("approved_usb_serials", [])


def _apply_usb_policy(approved_serials: list[str], log: logging.Logger) -> None:
    """Block all USB devices; re-allow approved serials via usbguard."""
    if not shutil.which("usbguard"):
        log.warning("usbguard not found — USB policy not enforced")
        return
    try:
        # Set default policy to block
        subprocess.run(
            ["usbguard", "set-parameter", "ImplicitPolicyTarget", "block"],
            check=True, capture_output=True
        )
        # Allow approved serials
        for serial in approved_serials:
            subprocess.run(
                ["usbguard", "allow-device", f"serial '{serial}'"],
                check=False, capture_output=True
            )
        log.info("USB policy applied: %d approved serials", len(approved_serials))
    except subprocess.CalledProcessError as exc:
        log.error("Failed to apply USB policy: %s", exc)


def _restore_usb_policy(log: logging.Logger) -> None:
    if not shutil.which("usbguard"):
        return
    try:
        subprocess.run(
            ["usbguard", "set-parameter", "ImplicitPolicyTarget", "allow"],
            check=True, capture_output=True
        )
        log.info("USB policy restored to allow-all")
    except subprocess.CalledProcessError as exc:
        log.error("Failed to restore USB policy: %s", exc)


# ---------------------------------------------------------------------------
# Network firewall (iptables)
# ---------------------------------------------------------------------------
def _load_whitelist() -> list[str]:
    return _load_state().get("outbound_whitelist", [])


def _apply_network_policy(whitelist: list[str], log: logging.Logger) -> None:
    """Block all outbound traffic except whitelisted IPs + DNS."""
    rules = [
        # Allow established/related
        ["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        # Allow loopback
        ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        # Allow DNS (port 53)
        ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "ACCEPT"],
        ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "ACCEPT"],
    ]
    for ip in whitelist:
        rules.append(["iptables", "-A", "OUTPUT", "-d", ip, "-j", "ACCEPT"])
    # Default deny outbound
    rules.append(["iptables", "-A", "OUTPUT", "-j", "DROP"])

    if os.geteuid() != 0:
        log.warning("Need root to apply iptables rules")
        return
    for rule in rules:
        try:
            subprocess.run(rule, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            log.error("iptables rule failed: %s  →  %s", " ".join(rule), exc)
    log.info("Network policy applied: %d whitelisted IPs, all others blocked", len(whitelist))


def _flush_network_policy(log: logging.Logger) -> None:
    if os.geteuid() != 0:
        return
    try:
        subprocess.run(["iptables", "-F", "OUTPUT"], check=True, capture_output=True)
        log.info("Network OUTPUT rules flushed")
    except subprocess.CalledProcessError as exc:
        log.error("Failed to flush iptables: %s", exc)


# ---------------------------------------------------------------------------
# Packet capture (tcpdump → encrypted rotating logs)
# ---------------------------------------------------------------------------
class PacketLogger:
    def __init__(self, key: bytes, log: logging.Logger):
        self._key = key
        self._log = log
        self._proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        NETLOG_DIR.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._log.info("Packet logger started")

    def _run(self) -> None:
        while not self._stop.is_set():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = NETLOG_DIR / f"capture_{ts}.pcap"
            try:
                self._proc = subprocess.Popen(
                    ["tcpdump", "-w", str(out_path), "-G",
                     str(NETLOG_ROTATE // 1024 // 1024), "-z",
                     "gzip", "-C", "50"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._proc.wait(timeout=3600)
            except FileNotFoundError:
                self._log.warning("tcpdump not found; using fallback netstat logger")
                self._fallback_log()
                break
            except subprocess.TimeoutExpired:
                if self._proc:
                    self._proc.kill()
            if out_path.exists() and self._key:
                _encrypt_file(out_path, self._key)

    def _fallback_log(self) -> None:
        """Log active connections via ss/netstat when tcpdump unavailable."""
        while not self._stop.is_set():
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                out = subprocess.check_output(
                    ["ss", "-tunp"], text=True, timeout=5
                )
                log_path = NETLOG_DIR / f"connections_{ts}.txt"
                log_path.write_text(out)
                if self._key:
                    _encrypt_file(log_path, self._key)
            except Exception as exc:
                self._log.debug("Fallback netlog error: %s", exc)
            self._stop.wait(60)

    def stop(self) -> None:
        self._stop.set()
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                pass
        self._log.info("Packet logger stopped")


# ---------------------------------------------------------------------------
# Screenshot auditor
# ---------------------------------------------------------------------------
class ScreenshotAuditor:
    def __init__(self, key: bytes, log: logging.Logger):
        self._key = key
        self._log = log
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._log.info("Screenshot auditor started (every %ds)", SCREENSHOT_INTERVAL)

    def _run(self) -> None:
        while not self._stop.is_set():
            self._take_screenshot()
            self._stop.wait(SCREENSHOT_INTERVAL)

    def _take_screenshot(self) -> None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out = SCREENSHOT_DIR / f"screen_{ts}.png"
        # Try multiple screenshot tools
        for cmd in (
            ["scrot", str(out)],
            ["gnome-screenshot", "-f", str(out)],
            ["import", "-window", "root", str(out)],
            ["grim", str(out)],
        ):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, check=True, capture_output=True, timeout=10)
                    self._log.debug("Screenshot: %s", out)
                    if self._key and out.exists():
                        _encrypt_file(out, self._key)
                    return
                except Exception:
                    continue
        # PIL fallback
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(str(out))
            if self._key and out.exists():
                _encrypt_file(out, self._key)
        except Exception as exc:
            self._log.warning("Screenshot failed: %s", exc)

    def stop(self) -> None:
        self._stop.set()
        self._log.info("Screenshot auditor stopped")


# ---------------------------------------------------------------------------
# File integrity monitor
# ---------------------------------------------------------------------------
def _hash_path(p: Path) -> str:
    h = hashlib.sha256()
    if p.is_dir():
        for child in sorted(p.rglob("*")):
            if child.is_file():
                try:
                    h.update(child.read_bytes())
                except PermissionError:
                    pass
    else:
        try:
            h.update(p.read_bytes())
        except (PermissionError, FileNotFoundError):
            pass
    return h.hexdigest()


class FileIntegrityMonitor:
    def __init__(self, log: logging.Logger):
        self._log = log
        self._baseline: dict[str, str] = {}
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _snapshot(self) -> dict[str, str]:
        return {str(p): _hash_path(p) for p in WATCH_FILES}

    def start(self) -> None:
        self._baseline = self._snapshot()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._log.info(
            "File integrity monitor started — watching %d paths", len(WATCH_FILES)
        )

    def _run(self) -> None:
        while not self._stop.is_set():
            self._stop.wait(WATCH_INTERVAL)
            current = self._snapshot()
            for path, digest in current.items():
                old = self._baseline.get(path)
                if old is None:
                    self._log.warning("[INTEGRITY] NEW path detected: %s", path)
                elif old != digest:
                    self._log.critical(
                        "[INTEGRITY] MODIFICATION DETECTED: %s  (was %s…, now %s…)",
                        path, old[:12], digest[:12],
                    )
                    _send_alert(f"⚠ PARANOID: {path} was modified!")
            removed = set(self._baseline) - set(current)
            for path in removed:
                self._log.critical("[INTEGRITY] PATH REMOVED: %s", path)
                _send_alert(f"⚠ PARANOID: {path} was removed!")
            self._baseline = current

    def stop(self) -> None:
        self._stop.set()
        self._log.info("File integrity monitor stopped")


# ---------------------------------------------------------------------------
# Alert helper
# ---------------------------------------------------------------------------
def _send_alert(msg: str) -> None:
    """Send a desktop notification and syslog entry."""
    try:
        subprocess.run(
            ["notify-send", "--urgency=critical", "SynthOS Paranoid Mode", msg],
            check=False, capture_output=True, timeout=3
        )
    except Exception:
        pass
    try:
        subprocess.run(
            ["logger", "-t", "synthex-paranoid", "-p", "auth.alert", msg],
            check=False, capture_output=True, timeout=3
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------
def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {
        "enabled": False,
        "approved_usb_serials": [],
        "outbound_whitelist": [],
        "enabled_at": None,
    }


def _save_state(state: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    STATE_FILE.chmod(0o600)


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------
class ParanoidDaemon:
    def __init__(self):
        import logging.handlers
        self._log = _setup_logging()
        self._key = _generate_key()
        self._pkt = PacketLogger(self._key, self._log)
        self._ss  = ScreenshotAuditor(self._key, self._log)
        self._fim = FileIntegrityMonitor(self._log)
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._log.warning("=" * 60)
        self._log.warning("PARANOID MODE ENABLED — system is now under strict monitoring")
        self._log.warning("=" * 60)
        state = _load_state()
        _apply_usb_policy(state.get("approved_usb_serials", []), self._log)
        _apply_network_policy(state.get("outbound_whitelist", []), self._log)
        self._pkt.start()
        self._ss.start()
        self._fim.start()
        self._running = True
        state["enabled"] = True
        state["enabled_at"] = datetime.datetime.now().isoformat()
        _save_state(state)
        DAEMON_PID_FILE.write_text(str(os.getpid()))
        _send_alert("🔒 Paranoid Mode ENABLED")

    def stop(self) -> None:
        if not self._running:
            return
        self._log.warning("PARANOID MODE DISABLED")
        _restore_usb_policy(self._log)
        _flush_network_policy(self._log)
        self._pkt.stop()
        self._ss.stop()
        self._fim.stop()
        self._running = False
        state = _load_state()
        state["enabled"] = False
        state["enabled_at"] = None
        _save_state(state)
        if DAEMON_PID_FILE.exists():
            DAEMON_PID_FILE.unlink()
        _send_alert("🔓 Paranoid Mode DISABLED")

    def run_forever(self) -> None:
        self.start()

        def _sigterm(sig, _frame):
            self._log.info("Received signal %d — shutting down", sig)
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, _sigterm)
        signal.signal(signal.SIGINT, _sigterm)
        while True:
            time.sleep(5)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _status() -> None:
    state = _load_state()
    enabled = state.get("enabled", False)
    enabled_at = state.get("enabled_at", "—")
    pid_alive = False
    if DAEMON_PID_FILE.exists():
        try:
            pid = int(DAEMON_PID_FILE.read_text())
            os.kill(pid, 0)
            pid_alive = True
        except (ValueError, ProcessLookupError, PermissionError):
            pass

    color = "\033[91m" if enabled else "\033[92m"
    reset = "\033[0m"
    print(f"\n{'='*55}")
    print(f"  SynthOS Paranoid Mode — Status")
    print(f"{'='*55}")
    print(f"  State       : {color}{'ENABLED' if enabled else 'DISABLED'}{reset}")
    print(f"  Daemon alive: {'yes' if pid_alive else 'no'}")
    print(f"  Enabled at  : {enabled_at}")
    usb = state.get("approved_usb_serials", [])
    wl  = state.get("outbound_whitelist", [])
    print(f"  USB approved: {len(usb)} serial(s)  {usb}")
    print(f"  Net whitelist: {len(wl)} IP(s)  {wl}")
    print(f"  Log dir     : {LOG_DIR}")
    print(f"{'='*55}\n")


def _cli_enable(daemon: bool) -> None:
    if os.geteuid() != 0:
        sys.exit("synthex-paranoid enable requires root (sudo)")
    if daemon:
        # Fork and run as background daemon
        pid = os.fork()
        if pid > 0:
            print(f"[paranoid] Daemon started (PID {pid})")
            return
        os.setsid()
        ParanoidDaemon().run_forever()
    else:
        ParanoidDaemon().run_forever()


def _cli_disable() -> None:
    if os.geteuid() != 0:
        sys.exit("synthex-paranoid disable requires root (sudo)")
    if not DAEMON_PID_FILE.exists():
        print("[paranoid] Daemon is not running")
        return
    try:
        pid = int(DAEMON_PID_FILE.read_text())
        os.kill(pid, signal.SIGTERM)
        print(f"[paranoid] Sent SIGTERM to PID {pid}")
    except (ValueError, ProcessLookupError) as exc:
        print(f"[paranoid] Could not signal daemon: {exc}")
    # Direct cleanup in case daemon is not running
    d = ParanoidDaemon()
    d.stop()


def _cli_add_usb(serial: str) -> None:
    state = _load_state()
    serials = state.setdefault("approved_usb_serials", [])
    if serial not in serials:
        serials.append(serial)
        _save_state(state)
        print(f"[paranoid] USB serial approved: {serial}")
    else:
        print(f"[paranoid] Already approved: {serial}")


def _cli_add_ip(ip: str) -> None:
    state = _load_state()
    wl = state.setdefault("outbound_whitelist", [])
    if ip not in wl:
        wl.append(ip)
        _save_state(state)
        print(f"[paranoid] IP whitelisted: {ip}")
    else:
        print(f"[paranoid] Already whitelisted: {ip}")


def main(argv: list[str] | None = None) -> int:
    import logging.handlers  # noqa: F401 (ensure available for _setup_logging)
    import shutil

    ap = argparse.ArgumentParser(
        prog="synthex-paranoid",
        description="SynthOS Paranoid Mode — extreme system lockdown & audit trail",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    en = sub.add_parser("enable", help="Enable paranoid mode")
    en.add_argument("--no-daemon", action="store_true",
                    help="Run in foreground instead of forking a daemon")

    sub.add_parser("disable", help="Disable paranoid mode and restore defaults")
    sub.add_parser("status",  help="Show current paranoid mode state")

    add_usb = sub.add_parser("add-usb", help="Approve a USB device by serial number")
    add_usb.add_argument("serial", help="USB device serial number")

    add_ip = sub.add_parser("add-ip", help="Whitelist an outbound IP address")
    add_ip.add_argument("ip", help="IP address to allow")

    args = ap.parse_args(argv)

    if args.cmd == "enable":
        _cli_enable(daemon=not args.no_daemon)
    elif args.cmd == "disable":
        _cli_disable()
    elif args.cmd == "status":
        _status()
    elif args.cmd == "add-usb":
        _cli_add_usb(args.serial)
    elif args.cmd == "add-ip":
        _cli_add_ip(args.ip)

    return 0


if __name__ == "__main__":
    sys.exit(main())
