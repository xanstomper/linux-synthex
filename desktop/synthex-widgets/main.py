#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
SynthOS Desktop Rice Widgets Suite
Loads and manages interactive floating desktop widgets matching the reference rice.
"""

import sys
import os
from pathlib import Path

try:
    from PySide6.QtCore import QUrl, Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except ImportError:
    try:
        from PyQt5.QtCore import QUrl, Qt
        from PyQt5.QtGui import QGuiApplication
        from PyQt5.QtQml import QQmlApplicationEngine
    except ImportError:
        print("Error: PySide6 or PyQt5 is required to launch synthex desktop widgets.")
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
