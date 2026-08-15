#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis — Daemon & Service Integration Test Suite
Verifies the production background daemon: one-shot audits, single-instance
locking, configuration reload signals, systemd unit integrity, and portable
desktop/packaging metadata.
"""

import os
import sys
import time
import json
import signal
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AEGIS_DIR = ROOT / "src" / "synthex-aegis"
DAEMON = AEGIS_DIR / "aegis_daemon.py"
sys.path.insert(0, str(AEGIS_DIR))


def _run_daemon(*args, timeout=60):
    return subprocess.run(
        [sys.executable, str(DAEMON), *args],
        capture_output=True, text=True, timeout=timeout)


class TestAegisDaemonService(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aegis-daemon-test-"))
        # Sovereignty-safe config: real audits still run (proving the engine
        # works) but spawned test processes are never auto-terminated.
        cfg = {
            "realtime_protection": True,
            "reverse_shell_blocker": True,
            "memory_integrity_shield": True,
            "privilege_escalation_guard": False,
            "auto_terminate_malicious_pids": False,
            "desktop_notifications": False,
            "exclusions": [],
        }
        (self.tmp / "config.json").write_text(json.dumps(cfg))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_01_once_mode_completes_cleanly(self):
        """`--once` performs a full audit pass and exits 0 with structured logs."""
        res = _run_daemon("--once", "--data-dir", str(self.tmp), timeout=90)
        self.assertEqual(res.returncode, 0,
                         f"daemon --once failed: {res.stderr[-500:]}")
        self.assertIn("Single audit pass complete", res.stdout)
        self.assertIn("Real-Time Protection active", res.stdout)
        # Data-dir redirection worked: engine artifacts under temp root
        self.assertTrue((self.tmp / "baselines.json").exists() or
                        (self.tmp / "quarantine").exists(),
                        "engine did not honor --data-dir redirection")

    def test_02_single_instance_lock(self):
        """A second daemon instance refuses to start (exit 3) while one runs."""
        env = dict(os.environ, XDG_RUNTIME_DIR=str(self.tmp))
        first = subprocess.Popen(
            [sys.executable, str(DAEMON), "--data-dir", str(self.tmp),
             "--interval", "30"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        try:
            deadline = time.time() + 15
            lock = self.tmp / f"synthex-aegis-{os.getuid()}.lock"
            while time.time() < deadline:
                if lock.exists() and first.poll() is None:
                    break
                time.sleep(0.2)
            self.assertIsNone(first.poll(), "first daemon failed to stay running")

            second = subprocess.run(
                [sys.executable, str(DAEMON), "--data-dir", str(self.tmp)],
                capture_output=True, text=True, env=env, timeout=30)
            self.assertEqual(second.returncode, 3,
                             f"second instance should exit 3, got {second.returncode}")
            self.assertIn("already running", second.stderr + second.stdout)
        finally:
            first.send_signal(signal.SIGTERM)
            try:
                first.wait(timeout=10)
            except subprocess.TimeoutExpired:
                first.kill()
                first.wait()

    def test_03_sigterm_graceful_shutdown(self):
        """SIGTERM triggers a clean loop exit with shutdown log line."""
        env = dict(os.environ, XDG_RUNTIME_DIR=str(self.tmp))
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--data-dir", str(self.tmp),
             "--interval", "5"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            text=True)
        time.sleep(1.5)
        proc.send_signal(signal.SIGTERM)
        out, _ = proc.communicate(timeout=15)
        self.assertEqual(proc.returncode, 0, f"unclean exit: {out[-400:]}")
        self.assertIn("shutting down cleanly", out)

    def test_04_systemd_unit_integrity(self):
        """The synthex-aegis.service unit is complete, hardened and installable."""
        unit = ROOT / "systemd" / "synthex-aegis.service"
        self.assertTrue(unit.exists(), "systemd unit missing")
        text = unit.read_text()
        for required in ["[Unit]", "[Service]", "[Install]",
                         "ExecStart=/usr/bin/synthex-aegis-daemon",
                         "Restart=on-failure", "ExecReload=",
                         "ProtectSystem=strict", "NoNewPrivileges=yes",
                         "WantedBy=multi-user.target"]:
            self.assertIn(required, text, f"unit missing: {required}")
        # Behavioral defense needs these capabilities; SUID/SGID creation is
        # forbidden via RestrictSUIDSGID.
        self.assertIn("CAP_KILL", text)
        self.assertIn("RestrictSUIDSGID=yes", text)
        # Verify with systemd itself when available (ignore missing-binary
        # warnings — the wrapper is only at /usr/bin after packaging/install)
        if shutil.which("systemd-analyze"):
            res = subprocess.run(["systemd-analyze", "verify", str(unit)],
                                 capture_output=True, text=True, timeout=60)
            fatal = [l for l in (res.stderr or "").splitlines()
                     if "is not executable" not in l
                     and "command not found" not in l
                     and l.strip()]
            self.assertEqual(fatal, [], f"systemd-analyze verify errors: {fatal}")

    def test_05_target_wiring(self):
        """synthex.target pulls in the Aegis protection service."""
        target = (ROOT / "systemd" / "synthex.target").read_text()
        self.assertIn("synthex-aegis.service", target)

    def test_06_desktop_and_wrapper_portability(self):
        """No hardcoded home paths; launchers resolve from source tree or /usr."""
        desktop = (AEGIS_DIR / "synthex-aegis.desktop").read_text()
        self.assertNotIn("/home/", desktop, "desktop file hardcodes a home path")
        self.assertIn("Exec=synthex-aegis", desktop)

        for wrapper in ["synthex-aegis", "synthex-aegis-daemon"]:
            w = AEGIS_DIR / wrapper
            self.assertTrue(w.exists(), f"{wrapper} missing")
            self.assertTrue(os.access(w, os.X_OK), f"{wrapper} not executable")
            self.assertNotIn("/home/", w.read_text(), f"{wrapper} hardcodes a home path")

        # Daemon wrapper launches the one-shot audit successfully end-to-end
        res = subprocess.run([str(AEGIS_DIR / "synthex-aegis-daemon"),
                              "--once", "--data-dir", str(self.tmp)],
                             capture_output=True, text=True, timeout=90)
        self.assertEqual(res.returncode, 0, f"wrapper run failed: {res.stderr[-400:]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
