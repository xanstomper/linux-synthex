#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
SynthOS Desktop Rice Widgets Suite
Loads and manages interactive floating desktop widgets matching the reference rice.
Automatically detects PySide6 / PyQt5 in virtual environments if not in system Python.
"""

import os
import sys
from pathlib import Path


def try_reexec_in_venv():
    """Attempt to find and re-exec under a python environment with PySide6/PyQt5."""
    possible_pythons = [
        Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "python",
        Path.home() / ".venv" / "bin" / "python",
        Path.home() / "linux-synthex" / ".venv" / "bin" / "python",
        Path.home() / ".local" / "share" / "synthex" / "venv" / "bin" / "python",
    ]

    for py in possible_pythons:
        if py.exists() and str(py) != sys.executable:
            # Check if this python has PySide6 or PyQt5
            try:
                import subprocess
                res = subprocess.run([str(py), "-c", "import PySide6"], capture_output=True)
                if res.returncode == 0:
                    os.execv(str(py), [str(py)] + sys.argv)
            except Exception:
                pass


# Try auto-detecting venv first if PySide6 is missing
try:
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError:
    try_reexec_in_venv()
    try:
        from PyQt5.QtCore import QUrl, Qt
        from PyQt5.QtGui import QGuiApplication
        from PyQt5.QtQml import QQmlApplicationEngine
    except ImportError:
        print("=" * 60)
        print("SynthOS Desktop Rice Widgets")
        print("=" * 60)
        print("PySide6 is required to launch the interactive desktop widgets.")
        print("\nTo set up PySide6 in 1 step, run:")
        print("  python3 -m venv ~/linux-synthex/.venv && ~/linux-synthex/.venv/bin/pip install PySide6")
        print("\nThen launch with:")
        print("  ~/linux-synthex/.venv/bin/python ~/linux-synthex/desktop/synthex-widgets/main.py")
        print("=" * 60)
        sys.exit(1)


def main():
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SynthOS Desktop Rice")
    app.setOrganizationName("SynthOS")

    engine = QQmlApplicationEngine()

    script_dir = Path(__file__).resolve().parent
    engine.addImportPath(str(script_dir))

    qml_file = script_dir / "DesktopRice.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print(f"Error: Failed to load QML file from {qml_file}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
