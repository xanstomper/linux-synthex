"""D-Bus bridge from Hermes IDE to the Synthex Agent daemon."""
import subprocess, json
from typing import Optional

HERMES_BUS   = "org.synthex.Hermes"
HERMES_PATH  = "/org/synthex/Hermes"
HERMES_IFACE = "org.synthex.Hermes.Codex"

def _dbus_call(method: str, payload: str) -> Optional[str]:
    cmd = ["dbus-send", "--session", "--print-reply=literal",
           f"--dest={HERMES_BUS}", HERMES_PATH,
           f"{HERMES_IFACE}.{method}", f"string:{payload}"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None

def is_running() -> bool:
    r = subprocess.run(
        ["dbus-send","--session","--print-reply",
         "--dest=org.freedesktop.DBus","/org/freedesktop/DBus",
         "org.freedesktop.DBus.ListNames"],
        capture_output=True, text=True)
    return HERMES_BUS in r.stdout

def complete_code(code: str, language: str = "auto", cursor: int = -1) -> str:
    return _dbus_call("CompleteCode",
                      json.dumps({"code": code, "lang": language, "cursor": cursor})) or ""

def explain_code(code: str, language: str = "auto") -> str:
    return _dbus_call("ExplainCode",
                      json.dumps({"code": code, "lang": language})) or ""

def refactor(code: str, instruction: str) -> str:
    return _dbus_call("Refactor",
                      json.dumps({"code": code, "instruction": instruction})) or code

def generate_tests(code: str, framework: str = "auto") -> str:
    return _dbus_call("GenerateTests",
                      json.dumps({"code": code, "framework": framework})) or ""
