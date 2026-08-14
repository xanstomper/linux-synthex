#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
SynthOS System Settings — Main Entry Point
Instantiates Qt Quick Engine with live system bridge.
"""

import os
import sys
from pathlib import Path

# Self-exec in local .venv if PySide6 is not in current Python
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"

if VENV_PYTHON.exists() and sys.executable != str(VENV_PYTHON):
    try:
        import PySide6
    except ImportError:
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "desktop" / "synthex-widgets"))

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from control_bridge import SettingsBridge


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("SynthOS System Settings")
    app.setApplicationDisplayName("System Settings")
    app.setOrganizationName("SynthOS")
    app.setOrganizationDomain("synthos-os.org")

    bridge = SettingsBridge()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(HERE / "ui"))
    engine.addImportPath(str(HERE / "ui" / "pages"))
    engine.rootContext().setContextProperty("settingsBridge", bridge)
    engine.rootContext().setContextProperty("systemBridge", bridge)

    qml_file = HERE / "ui" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
