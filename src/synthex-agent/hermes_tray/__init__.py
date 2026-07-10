"""hermes_tray — System-tray icon & quick-actions panel for Synthex Agent.

Provides:
  • Animated Synthex logo tray icon (status-aware colour)
  • Left-click → toggle Hermes AI side panel
  • Right-click → context menu (New Chat / Settings / Quit)
  • Middle-click → paste clipboard into active AI session
  • Notification badge for pending AI responses

Built on AppIndicator3 (fallback: Qt.SystemTrayIcon for non-GNOME DEs).
"""
from __future__ import annotations

__version__ = "2026.10.0"
__all__ = ["TrayApp", "TrayMenu", "StatusIcon"]


ICON_IDLE     = "/usr/share/icons/synthex/scalable/apps/synthex-agent.svg"
ICON_THINKING = "/usr/share/icons/synthex/scalable/status/synthex-agent-busy.svg"
ICON_ERROR    = "/usr/share/icons/synthex/scalable/status/synthex-agent-error.svg"
ICON_OFFLINE  = "/usr/share/icons/synthex/scalable/status/synthex-agent-offline.svg"


class StatusIcon:
    """Manages the tray icon image based on agent state."""

    STATES = ("idle", "thinking", "error", "offline")

    def __init__(self, indicator) -> None:
        self._indicator = indicator
        self._state = "idle"

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str) -> None:
        assert state in self.STATES, f"Unknown tray state: {state}"
        self._state = state
        icon = {
            "idle":     ICON_IDLE,
            "thinking": ICON_THINKING,
            "error":    ICON_ERROR,
            "offline":  ICON_OFFLINE,
        }[state]
        try:
            self._indicator.set_icon_full(icon, f"Synthex Agent — {state}")
        except AttributeError:
            pass  # Qt fallback path
