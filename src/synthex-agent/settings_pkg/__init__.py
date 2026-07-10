"""settings_pkg — persistent user preference store for Synthex Agent.

Key/value JSON document stored at ~/.local/share/synthex/agent/settings.json.
Accessed by Codex IDE, Hermes AI panel, and tray icon.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

_SETTINGS_FILE = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) \
    / "synthex" / "agent" / "settings.json"

_DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "accent_color": "#FFB300",
    "font_size": 13,
    "show_tray_icon": True,
    "enable_inline_completions": True,
    "llm_backend": "local",          # local | cloud | hybrid
    "local_model": "ollama/mistral",
    "max_context_tokens": 8192,
    "auto_save_interval": 30,
    "telemetry_opt_in": False,
    "first_run_done": False,
    "panel_width": 400,
    "sidebar_section": "chat",
}

_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    try:
        _cache = json.loads(_SETTINGS_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        _cache = dict(_DEFAULTS)
    return _cache


def get(key: str, default: Any = None) -> Any:
    """Return setting *key*, falling back to *default* (or built-in default)."""
    return _load().get(key, _DEFAULTS.get(key, default))


def set(key: str, value: Any) -> None:  # noqa: A001
    """Persist *key = value* immediately."""
    data = _load()
    data[key] = value
    _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def reset(key: str) -> None:
    """Reset *key* to its built-in default value."""
    set(key, _DEFAULTS.get(key))


def all_settings() -> dict[str, Any]:
    """Return a shallow copy of all current settings."""
    return dict(_load())
