#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis Background Daemon
Production real-time protection service.

Continuously audits process execution trees, memory permissions, SUID binaries
and cryptographic integrity baselines, intercepting behavioral attacks in real
time. Designed to run as a systemd service (`synthex-aegis.service`) or in the
foreground for development.

Exit codes:
    0  clean shutdown / single audit pass completed
    3  another Aegis daemon instance is already running
"""

import os
import sys
import argparse
import logging
import signal
import fcntl
import time
import tempfile
from pathlib import Path

# Resolve aegis modules whether run from source tree or /usr/lib/synthex/aegis
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aegis_engine
from aegis_engine import AegisEngine, AegisConfig

PROG = "synthex-aegis-daemon"

log = logging.getLogger(PROG)

DEFAULT_INTERVAL = 2          # seconds between behavioral process audits
DEFAULT_FULL_AUDIT_EVERY = 30 # behavioral cycles between SUID/baseline audits

_running = True


def _lock_path() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return Path(runtime_dir) / f"synthex-aegis-{os.getuid()}.lock"


def _acquire_singleton_lock() -> "int | None":
    """Returns the lock fd, or None if another instance holds the lock."""
    lock_file = _lock_path()
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_file), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    os.ftruncate(fd, 0)
    os.write(fd, f"{os.getpid()}\n".encode())
    return fd


def _apply_data_dir(data_dir: str):
    """Redirect the engine's config/incident/quarantine storage root."""
    import aegis_engine as ae
    root = Path(data_dir)
    ae.CONFIG_DIR = root
    ae.CONFIG_FILE = root / "config.json"
    ae.INCIDENTS_FILE = root / "incidents.json"
    ae.BASELINES_FILE = root / "baselines.json"
    ae.QUARANTINE_DIR = root / "quarantine"
    ae.QUARANTINE_MANIFEST = ae.QUARANTINE_DIR / "manifest.json"


def _handle_stop(signum, frame):
    global _running
    _running = False


def _handle_reload(signum, frame):
    try:
        engine = AegisEngine.get_instance()
        engine.config = AegisConfig.load()
        log.info("Configuration reloaded (realtime_protection=%s)",
                 engine.config.get("realtime_protection", True))
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("Config reload failed: %s", exc)


def run_daemon(interval: float, full_audit_every: int, once: bool) -> int:
    engine = AegisEngine.get_instance()
    engine.config = AegisConfig.load()

    log.info("Synthex Aegis Real-Time Protection active "
             "(interval=%ss, full audit every %d cycles)", interval, full_audit_every)
    log.info("Engine layers: reverse_shell=%s memory_integrity=%s suid_guard=%s baselining=%s "
             "auto_terminate=%s",
             engine.config.get("reverse_shell_blocker", True),
             engine.config.get("memory_integrity_shield", True),
             engine.config.get("privilege_escalation_guard", True),
             engine.config.get("integrity_baselining", True),
             engine.config.get("auto_terminate_malicious_pids", True))

    cycle = 0
    idle_logged = False
    global _running
    _running = True

    while _running:
        try:
            if not engine.config.get("realtime_protection", True):
                if not idle_logged:
                    log.info("Real-time protection disabled by user sovereignty toggle — daemon idling")
                    idle_logged = True
            else:
                idle_logged = False
                threats = engine.audit_active_processes() or []

                # Periodic deep audits: SUID misconfiguration + integrity baselines
                if cycle % max(1, full_audit_every) == 0:
                    threats += engine.audit_suid_binaries() or []
                    threats += engine.audit_system_baselines() or []

                if threats:
                    for t in threats:
                        log.log(logging.CRITICAL if t.severity == "Critical" else logging.WARNING,
                                "THREAT BLOCKED [%s] %s (PID %s): %s — action: %s",
                                t.severity, t.category, t.pid, t.details[:120], t.action_taken)
                cycle += 1
                log.debug("audit cycle %d complete (%d threats)", cycle, len(threats))

        except KeyboardInterrupt:
            break
        except Exception as exc:
            log.error("Audit cycle error: %s", exc, exc_info=log.isEnabledFor(logging.DEBUG))
            if once:
                return 1
            time.sleep(min(interval * 2, 10))

        if once:
            log.info("Single audit pass complete")
            return 0

        # Interruptible sleep
        slept = 0.0
        while _running and slept < interval:
            time.sleep(min(0.25, interval - slept))
            slept += 0.25

    log.info("Aegis daemon shutting down cleanly")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Synthex Aegis real-time behavioral attack prevention daemon")
    parser.add_argument("--once", action="store_true",
                        help="run a single full audit pass and exit (for CI/testing)")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                        help=f"seconds between behavioral audits (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--full-audit-every", type=int, default=DEFAULT_FULL_AUDIT_EVERY,
                        help=f"audits between SUID/baseline sweeps (default: {DEFAULT_FULL_AUDIT_EVERY})")
    parser.add_argument("--data-dir", metavar="PATH",
                        help="override engine config/incident/quarantine storage root (default: ~/.config/synthex/aegis)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="enable debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format=f"%(asctime)s {PROG}[%(process)d] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    if args.data_dir:
        _apply_data_dir(args.data_dir)

    if args.once:
        # One-shot mode: no singleton lock required (parallel audits are safe)
        return run_daemon(args.interval, args.full_audit_every, once=True)

    lock_fd = _acquire_singleton_lock()
    if lock_fd is None:
        existing_pid = ""
        try:
            existing_pid = _lock_path().read_text().strip()
        except Exception:
            pass
        log.error("Another Aegis daemon is already running (PID %s) — refusing to start",
                  existing_pid or "unknown")
        return 3

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGHUP, _handle_reload)

    try:
        return run_daemon(args.interval, args.full_audit_every, once=False)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
