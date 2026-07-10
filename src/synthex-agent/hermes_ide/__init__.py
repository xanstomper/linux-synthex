"""hermes_ide — Codex IDE integration layer for Synthex Agent.

Bridges the Hermes AI daemon with the D-Bus IDE interface so that
in-editor AI completions, refactoring suggestions, and code reviews
are served by the local Synthex LLM engine instead of a cloud API.

Sub-packages:
    .bridge    — D-Bus ↔ Hermes message bridge
    .lsp       — Language Server Protocol hooks
    .snippets  — AI-generated snippet cache
    .refactor  — Refactor / explain / document actions
"""
from __future__ import annotations

__version__ = "2026.10.0"
__all__ = ["bridge", "lsp", "snippets", "refactor"]


def register_dbus_interface(bus) -> None:  # type: ignore[type-arg]
    """Register the Hermes IDE D-Bus object on *bus*.

    Called during Synthex Agent startup so the Codex IDE extension
    can call methods on ``org.synthex.HermesIDE``.
    """
    from .bridge import HermesIDEBridge  # noqa: PLC0415
    bridge = HermesIDEBridge(bus)
    bridge.export()
    return bridge
