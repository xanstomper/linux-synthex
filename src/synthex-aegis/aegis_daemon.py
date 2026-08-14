#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis Background Daemon
Continuously audits process execution trees, monitors memory permissions, and intercepts
behavioral attacks in real-time.
"""

import time
import os
import sys

from aegis_engine import AegisEngine


def main():
    print("[Aegis Daemon] Initializing Synthex Aegis Real-Time Protection...")
    engine = AegisEngine.get_instance()
    print("[Aegis Daemon] Aegis Behavioral Attack Prevention active.")

    while True:
        try:
            # Audit active processes every 2 seconds
            engine.audit_active_processes()
            time.sleep(2)
        except KeyboardInterrupt:
            print("[Aegis Daemon] Terminating Aegis daemon.")
            break
        except Exception as e:
            print(f"[Aegis Daemon] Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
