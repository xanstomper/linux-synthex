"""User preference store for Synthex Agent."""
import json, os
from pathlib import Path

_CFG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "synthex-agent" / "settings.json"

DEFAULTS = {
    "provider":        "local",       # "local" | "claude" | "openai"
    "model":           "llama3.2",
    "hotkey":          "Meta+Space",
    "enable_hermes":   True,
    "enable_codex":    True,
    "enable_terminal": True,
    "context_window":  8192,
    "theme":           "dark",
    "telemetry":       False,
}

def load() -> dict:
    if _CFG.exists():
        try:
            return {**DEFAULTS, **json.loads(_CFG.read_text())}
        except Exception:
            pass
    return dict(DEFAULTS)

def save(cfg: dict) -> None:
    _CFG.parent.mkdir(parents=True, exist_ok=True)
    _CFG.write_text(json.dumps(cfg, indent=2))

def get(key: str, default=None):
    return load().get(key, default)

def set(key: str, value) -> None:
    cfg = load()
    cfg[key] = value
    save(cfg)
