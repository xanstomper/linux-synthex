"""Tray state helpers for the Hermes AI assistant systray icon."""
import subprocess
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class TrayState:
    agent_running:  bool = False
    hermes_running: bool = False
    current_task:   Optional[str] = None
    unread_count:   int = 0
    errors:         list[str] = field(default_factory=list)

def get_state() -> TrayState:
    def svc_active(name: str) -> bool:
        r = subprocess.run(["systemctl","--user","is-active","--quiet", name])
        return r.returncode == 0

    return TrayState(
        agent_running  = svc_active("synthex-agent.service"),
        hermes_running = svc_active("hermesd.service"),
    )

def notify(title: str, body: str, icon: str = "synthex") -> None:
    subprocess.Popen(["notify-send", "--app-name=Hermes",
                      f"--icon={icon}", title, body])
