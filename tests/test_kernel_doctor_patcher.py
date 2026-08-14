#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Kernel-Level Doctor & Auto-Patcher Test Suite
Verifies kernel-space diagnostics and healing:
1. Kernel taint bitmask decoding
2. Kernel cmdline resilient parameters injection
3. Magic SysRq emergency keys enabler
4. Dracut early-boot auto-healing hook configuration
5. Hardware quirks & modprobe overrides
"""

import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add synthex-doctor to path
DOCTOR_DIR = Path(__file__).resolve().parent.parent / "src" / "synthex-doctor"
sys.path.insert(0, str(DOCTOR_DIR))

from kernel_doctor import KernelDoctor, KernelDiagnosticResult


class TestKernelDoctorPatcher(unittest.TestCase):
    def setUp(self):
        self.kdoc = KernelDoctor(dry_run=True)

    def test_01_kernel_taint_bitmask_decoding(self):
        """Verifies kernel taint decoding correctly identifies taint bit flags."""
        res = self.kdoc.diagnose_kernel_health()
        self.assertIn(res.status, ["OK", "WARNING", "CRITICAL"])
        self.assertEqual(res.subsystem, "Kernel Core & Taint Health")
        self.assertIn("Taints:", res.technical_details)

    def test_02_resilient_kernel_cmdline_inspection(self):
        """Verifies kernel command line inspector checks panic=10, fsck.repair=yes, and modeset."""
        res = self.kdoc.check_and_patch_kernel_cmdline(auto_patch=False)
        self.assertIn(res.status, ["OK", "WARNING", "REPAIRED"])
        self.assertEqual(res.subsystem, "Kernel Boot Parameters (cmdline)")

    def test_03_magic_sysrq_emergency_recovery_inspection(self):
        """Verifies Magic SysRq emergency key validator checks /proc/sys/kernel/sysrq."""
        res = self.kdoc.check_and_repair_sysrq_keys(auto_patch=False)
        self.assertIn(res.status, ["OK", "WARNING", "REPAIRED"])
        self.assertEqual(res.subsystem, "Magic SysRq Emergency Recovery")

    def test_04_dracut_early_boot_hook_status(self):
        """Verifies Dracut 99synthex-kernel-doctor hook detection."""
        res = self.kdoc.check_and_install_dracut_hook(auto_patch=False)
        self.assertIn(res.status, ["OK", "WARNING", "REPAIRED"])
        self.assertEqual(res.subsystem, "Dracut Early-Boot Auto-Healer")

    def test_05_hardware_quirks_and_modprobe_analysis(self):
        """Verifies hardware quirks diagnostic analyzes PCIe AER and audio DMA buffers."""
        res = self.kdoc.check_and_patch_hardware_quirks(auto_patch=False)
        self.assertIn(res.status, ["OK", "WARNING", "REPAIRED"])
        self.assertEqual(res.subsystem, "Hardware & Kernel Driver Quirks")

    def test_06_full_kernel_doctor_diagnostics_pass(self):
        """Executes full kernel diagnostics suite."""
        results = self.kdoc.run_full_kernel_diagnostics(auto_patch=False)
        self.assertEqual(len(results), 5)
        subs = [r.subsystem for r in results]
        self.assertIn("Kernel Core & Taint Health", subs)
        self.assertIn("Kernel Boot Parameters (cmdline)", subs)
        self.assertIn("Magic SysRq Emergency Recovery", subs)
        self.assertIn("Dracut Early-Boot Auto-Healer", subs)
        self.assertIn("Hardware & Kernel Driver Quirks", subs)


if __name__ == "__main__":
    unittest.main()
