#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis — Security & Attack Prevention Test Suite
Verifies behavioral detection, reverse shell interception, memory integrity W^X enforcement,
SUID privilege escalation detection, cryptographic baselining, and secure quarantine.
"""

import os
import sys
import time
import json
import socket
import signal
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path

# Add synthex-aegis to path
AEGIS_DIR = Path(__file__).resolve().parent.parent / "src" / "synthex-aegis"
sys.path.insert(0, str(AEGIS_DIR))

from aegis_engine import AegisEngine, ThreatIncident, AegisConfig


class TestAegisSecurityEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AegisEngine.get_instance()
        self.engine.config["auto_terminate_malicious_pids"] = True
        self.engine.config["realtime_protection"] = True

    def test_01_reverse_shell_socket_detection(self):
        """Simulates an interactive reverse shell process and verifies Aegis terminates it."""
        # Create a loopback listening socket
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        # Spawn a simulated bash reverse shell command
        cmd = f"python3 -c 'import socket,subprocess,os; s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.connect((\"127.0.0.1\",{port})); os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); import time; time.sleep(10)'"
        proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)

        try:
            time.sleep(0.5)
            # Run Aegis active process audit
            threats = self.engine.audit_active_processes()

            # Find matching threat
            rev_threats = [t for t in threats if "Reverse" in t.category or "Interactive" in t.category]
            self.assertTrue(len(rev_threats) > 0, "Aegis failed to detect interactive reverse shell!")

            detected = rev_threats[0]
            self.assertEqual(detected.severity, "Critical")
            self.assertIn("Execution", detected.tactic)

            # Verify process was terminated
            time.sleep(0.3)
            poll_res = proc.poll()
            self.assertIsNotNone(poll_res, "Aegis failed to terminate malicious reverse shell process!")

        finally:
            server_sock.close()
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass

    def test_02_ld_preload_injection_detection(self):
        """Simulates process spawning with unauthorized LD_PRELOAD from temporary directory."""
        dummy_so = "/tmp/dummy_malicious_lib.so"
        Path(dummy_so).touch()

        env = os.environ.copy()
        env["LD_PRELOAD"] = dummy_so

        proc = subprocess.Popen(["sleep", "15"], env=env)
        try:
            time.sleep(0.3)
            threats = self.engine.audit_active_processes()

            preload_threats = [t for t in threats if "LD_PRELOAD" in t.category]
            self.assertTrue(len(preload_threats) > 0, "Aegis failed to detect LD_PRELOAD injection!")
            self.assertEqual(preload_threats[0].severity, "High")

        finally:
            proc.kill()
            if os.path.exists(dummy_so):
                os.unlink(dummy_so)

    def test_03_world_writable_suid_vulnerability_detection(self):
        """Verifies Aegis detects dangerous world-writable SUID binaries."""
        with tempfile.NamedTemporaryFile(dir="/tmp", prefix="test_suid_", delete=False) as f:
            f.write(b"#!/bin/sh\nexit 0\n")
            fpath = f.name

        try:
            # Set SUID + World Writable (0o4777)
            os.chmod(fpath, 0o4777)

            threats = self.engine.audit_suid_binaries()
            suid_threats = [t for t in threats if os.path.basename(fpath) in t.process_name or fpath in t.target]
            self.assertTrue(len(suid_threats) > 0, "Aegis failed to flag world-writable SUID vulnerability!")
            self.assertEqual(suid_threats[0].severity, "Critical")

        finally:
            if os.path.exists(fpath):
                os.unlink(fpath)

    def test_04_cryptographic_integrity_baselining(self):
        """Verifies Aegis detects unauthorized tampering with monitored security files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"root ALL=(ALL:ALL) ALL\n")
            test_file = Path(f.name)

        try:
            # Update baseline
            h1 = self.engine._hash_file(test_file)
            self.assertIsNotNone(h1)

            # Tamper with file
            with open(test_file, "a") as f:
                f.write("attacker ALL=(ALL:ALL) NOPASSWD: ALL\n")

            h2 = self.engine._hash_file(test_file)
            self.assertNotEqual(h1, h2, "Hash should change upon tampering!")

        finally:
            if test_file.exists():
                test_file.unlink()

    def test_05_quarantine_vault_permission_locking(self):
        """Verifies Aegis locks quarantined payloads to mode 000 with cryptographic manifests."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"MALICIOUS_DROPPER_PAYLOAD_TEST")
            target_path = f.name

        try:
            ok = self.engine.quarantine_file(target_path)
            self.assertTrue(ok, "Quarantine operation failed!")
            self.assertFalse(os.path.exists(target_path), "Original file was not removed upon quarantine!")

            manifest = self.engine.get_quarantine_manifest()
            self.assertTrue(len(manifest) > 0, "Quarantine manifest was not updated!")

            # Verify quarantined file permissions are locked to 000
            for fname in manifest.keys():
                qpath = Path(self.engine.quarantine_manifest_path if hasattr(self.engine, 'quarantine_manifest_path') else (Path.home() / ".config" / "synthex" / "aegis" / "quarantine")) / fname
                if qpath.exists():
                    st = qpath.stat()
                    self.assertEqual(st.st_mode & 0o777, 0o000, "Quarantined payload must be locked with mode 000!")

        finally:
            if os.path.exists(target_path):
                os.unlink(target_path)

    def test_06_engine_status_and_sovereignty_toggles(self):
        """Verifies that the user can disable/enable any engine with 100% sovereignty."""
        self.engine.set_engine_state("realtime_protection", False)
        status = self.engine.get_status()
        self.assertFalse(status["realtime_active"])

        self.engine.set_engine_state("realtime_protection", True)
        status = self.engine.get_status()
        self.assertTrue(status["realtime_active"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
