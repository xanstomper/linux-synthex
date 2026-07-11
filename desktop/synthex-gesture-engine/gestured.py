#!/usr/bin/env python3
"""
gestured.py — SynthOS Brain OS Gesture Recognition Engine
Part of the linux-synthex desktop stack.

Listens for touchpad and mouse gestures via libinput, routes them through
the Hermes AI command bus, exposes a D-Bus service, and logs everything.

Author: SynthOS Brain OS
License: MIT
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import signal
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

# ── optional deps (graceful fallback) ────────────────────────────────────────
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # pip install tomli
    except ImportError:
        tomllib = None  # type: ignore

try:
    from dbus_next.aio import MessageBus
    from dbus_next import BusType, Message, Variant
    from dbus_next.service import ServiceInterface, method, dbus_property, signal as dbus_signal
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    ServiceInterface = object  # type: ignore

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# ── constants ─────────────────────────────────────────────────────────────────
VERSION = "1.0.0"
DAEMON_NAME = "synthex-gesture-engine"
HERMES_URL = "http://localhost:7700/gesture"
DBUS_SERVICE_NAME = "org.synthex.GestureEngine"
DBUS_OBJECT_PATH = "/org/synthex/GestureEngine"

CONFIG_DIR = Path.home() / ".config" / "synthex"
CONFIG_FILE = CONFIG_DIR / "gestures.toml"
LOG_DIR = Path.home() / ".local" / "share" / "synthex"
GESTURE_LOG = LOG_DIR / "gesture-log.jsonl"

LONG_PRESS_SECONDS = 1.5
SWIPE_MIN_DELTA = 40.0        # pixels of accumulated travel to confirm
PINCH_RATIO_THRESHOLD = 0.15  # 15 % change in scale to confirm
MOUSE_DRAG_MIN_PX = 30        # pixels right-button must travel

log = logging.getLogger(DAEMON_NAME)


# ── enums & data classes ──────────────────────────────────────────────────────

class GestureKind(str, Enum):
    SWIPE_3_LEFT       = "swipe_3_left"
    SWIPE_3_RIGHT      = "swipe_3_right"
    SWIPE_3_UP         = "swipe_3_up"
    SWIPE_3_DOWN       = "swipe_3_down"
    SWIPE_4_UP         = "swipe_4_up"
    PINCH_IN           = "pinch_in"
    PINCH_OUT          = "pinch_out"
    LONGPRESS_2        = "longpress_2"
    MOUSE_DRAG_UP      = "mouse_drag_up"
    MOUSE_DRAG_DOWN    = "mouse_drag_down"
    MOUSE_DRAG_LEFT    = "mouse_drag_left"
    MOUSE_DRAG_RIGHT   = "mouse_drag_right"


@dataclass
class GestureEvent:
    kind: GestureKind
    confidence: float          # 0.0–1.0
    fingers: int
    dx: float = 0.0
    dy: float = 0.0
    scale: float = 1.0
    timestamp: float = field(default_factory=time.time)
    source: str = "touchpad"   # "touchpad" | "mouse"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gesture": self.kind.value,
            "confidence": round(self.confidence, 3),
            "fingers": self.fingers,
            "dx": round(self.dx, 2),
            "dy": round(self.dy, 2),
            "scale": round(self.scale, 4),
            "timestamp": self.timestamp,
            "source": self.source,
            "iso_time": datetime.fromtimestamp(
                self.timestamp, tz=timezone.utc
            ).isoformat(),
        }


@dataclass
class SwipeState:
    fingers: int = 0
    dx: float = 0.0
    dy: float = 0.0
    active: bool = False


@dataclass
class PinchState:
    scale: float = 1.0
    active: bool = False


@dataclass
class MouseDragState:
    active: bool = False
    start_x: float = 0.0
    start_y: float = 0.0
    cur_x: float = 0.0
    cur_y: float = 0.0


@dataclass
class LongPressState:
    fingers: int = 0
    start_time: float = 0.0
    active: bool = False
    fired: bool = False


# ── default configuration ─────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "sensitivity": {
        "swipe_min_delta": SWIPE_MIN_DELTA,
        "pinch_ratio_threshold": PINCH_RATIO_THRESHOLD,
        "mouse_drag_min_px": MOUSE_DRAG_MIN_PX,
        "long_press_seconds": LONG_PRESS_SECONDS,
    },
    "bindings": {
        GestureKind.SWIPE_3_LEFT.value:  "kwin:desktop_prev",
        GestureKind.SWIPE_3_RIGHT.value: "kwin:desktop_next",
        GestureKind.SWIPE_3_UP.value:    "hermes:open_krunner",
        GestureKind.SWIPE_3_DOWN.value:  "kwin:show_desktop",
        GestureKind.SWIPE_4_UP.value:    "synthex:focus_mode_toggle",
        GestureKind.PINCH_IN.value:      "kwin:zoom_in",
        GestureKind.PINCH_OUT.value:     "kwin:zoom_out",
        GestureKind.LONGPRESS_2.value:   "hermes:context_assistant",
        GestureKind.MOUSE_DRAG_UP.value:    "kwin:maximize",
        GestureKind.MOUSE_DRAG_DOWN.value:  "kwin:minimize",
        GestureKind.MOUSE_DRAG_LEFT.value:  "app:prev",
        GestureKind.MOUSE_DRAG_RIGHT.value: "app:next",
    },
    "hermes": {
        "url": HERMES_URL,
        "timeout_seconds": 2.0,
        "enabled": True,
    },
    "logging": {
        "level": "INFO",
        "gesture_log": str(GESTURE_LOG),
    },
    "daemon": {
        "enabled": True,
        "libinput_debug_events": True,
    },
}


def load_config() -> Dict[str, Any]:
    """Load config from TOML, falling back to defaults for missing keys."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy

    if not CONFIG_FILE.exists():
        log.info("No config at %s — using defaults", CONFIG_FILE)
        return cfg

    if tomllib is None:
        log.warning("tomllib/tomli not available — cannot parse config, using defaults")
        return cfg

    try:
        with open(CONFIG_FILE, "rb") as fh:
            user = tomllib.load(fh)
        # shallow-merge each section
        for section, values in user.items():
            if section in cfg and isinstance(cfg[section], dict):
                cfg[section].update(values)
            else:
                cfg[section] = values
        log.info("Loaded config from %s", CONFIG_FILE)
    except Exception as exc:
        log.error("Failed to parse %s: %s — using defaults", CONFIG_FILE, exc)

    return cfg


# ── action dispatcher ─────────────────────────────────────────────────────────

class ActionDispatcher:
    """Translates binding strings into real side effects."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._cfg = config

    async def dispatch(self, action: str, event: GestureEvent) -> None:
        ns, _, cmd = action.partition(":")
        try:
            if ns == "kwin":
                await self._kwin(cmd, event)
            elif ns == "hermes":
                await self._hermes(cmd, event)
            elif ns == "synthex":
                await self._synthex(cmd, event)
            elif ns == "app":
                await self._app(cmd, event)
            elif ns == "exec":
                await self._exec(cmd, event)
            else:
                log.warning("Unknown action namespace %r in %r", ns, action)
        except Exception as exc:
            log.error("Action dispatch error for %r: %s", action, exc)

    # ── kwin ──────────────────────────────────────────────────────────────────
    async def _kwin(self, cmd: str, event: GestureEvent) -> None:
        kwin_scripts: Dict[str, str] = {
            "desktop_prev":  "qdbus org.kde.KWin /KWin switchToPreviousDesktop",
            "desktop_next":  "qdbus org.kde.KWin /KWin switchToNextDesktop",
            "show_desktop":  "qdbus org.kde.KWin /KWin showDesktop",
            "maximize":      "qdbus org.kde.KWin /KWin slotWindowMaximize",
            "minimize":      "qdbus org.kde.KWin /KWin slotWindowMinimize",
            "zoom_in":       "qdbus org.kde.KWin /KWin slotIncreaseWindowOpacity",
            "zoom_out":      "qdbus org.kde.KWin /KWin slotDecreaseWindowOpacity",
        }
        shell_cmd = kwin_scripts.get(cmd)
        if shell_cmd is None:
            log.warning("Unknown kwin command: %r", cmd)
            return
        await _run_shell(shell_cmd)

    # ── hermes ────────────────────────────────────────────────────────────────
    async def _hermes(self, cmd: str, event: GestureEvent) -> None:
        hermes_cmds: Dict[str, str] = {
            "open_krunner":      "krunner",
            "context_assistant": "qdbus org.kde.krunner /App display",
        }
        # First notify Hermes REST endpoint
        await post_to_hermes(event, self._cfg)
        # Then fire the local KDE action
        shell_cmd = hermes_cmds.get(cmd)
        if shell_cmd:
            await _run_shell(shell_cmd)

    # ── synthex ───────────────────────────────────────────────────────────────
    async def _synthex(self, cmd: str, event: GestureEvent) -> None:
        if cmd == "focus_mode_toggle":
            await _run_shell(
                "qdbus org.synthex.FocusMode /FocusMode Toggle 2>/dev/null "
                "|| notify-send 'SynthOS' 'Focus mode toggled' --icon=focus-windows"
            )
        else:
            log.warning("Unknown synthex command: %r", cmd)

    # ── app ───────────────────────────────────────────────────────────────────
    async def _app(self, cmd: str, event: GestureEvent) -> None:
        app_cmds: Dict[str, str] = {
            "prev": "qdbus org.kde.KWin /KWin slotSwitchToPrevWindow",
            "next": "qdbus org.kde.KWin /KWin slotSwitchToNextWindow",
        }
        shell_cmd = app_cmds.get(cmd)
        if shell_cmd:
            await _run_shell(shell_cmd)

    # ── exec ──────────────────────────────────────────────────────────────────
    async def _exec(self, cmd: str, event: GestureEvent) -> None:
        """User-defined shell command in binding value after 'exec:'."""
        await _run_shell(cmd)


async def _run_shell(cmd: str) -> None:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0 and stderr:
        log.debug("Shell cmd stderr: %s", stderr.decode(errors="replace").strip())


# ── Hermes REST poster ────────────────────────────────────────────────────────

async def post_to_hermes(event: GestureEvent, config: Dict[str, Any]) -> None:
    hermes_cfg = config.get("hermes", {})
    if not hermes_cfg.get("enabled", True):
        return
    url = hermes_cfg.get("url", HERMES_URL)
    timeout = hermes_cfg.get("timeout_seconds", 2.0)

    payload = {
        "gesture": event.kind.value,
        "context": {
            "confidence": event.confidence,
            "fingers": event.fingers,
            "dx": event.dx,
            "dy": event.dy,
            "scale": event.scale,
            "source": event.source,
            "timestamp": event.timestamp,
        },
    }

    if AIOHTTP_AVAILABLE:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as resp:
                    log.debug("Hermes responded %s for %s", resp.status, event.kind.value)
        except Exception as exc:
            log.debug("Hermes POST failed (non-fatal): %s", exc)
    else:
        # Fallback: fire-and-forget curl
        body = json.dumps(payload)
        await _run_shell(
            f"curl -sf -X POST {url} "
            f"-H 'Content-Type: application/json' "
            f"-d '{body}' "
            f"--max-time {int(timeout)} > /dev/null 2>&1"
        )


# ── gesture logger ────────────────────────────────────────────────────────────

class GestureLogger:
    def __init__(self, log_path: Path) -> None:
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, event: GestureEvent, action: str) -> None:
        record = event.to_dict()
        record["action"] = action
        try:
            with open(self._path, "a") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            log.error("Could not write gesture log: %s", exc)


# ── D-Bus service ─────────────────────────────────────────────────────────────

if DBUS_AVAILABLE:
    class GestureEngineInterface(ServiceInterface):
        def __init__(self, engine: "GestureEngine") -> None:
            super().__init__(DBUS_SERVICE_NAME)
            self._engine = engine
            self._enabled = True

        @dbus_property(access="readwrite")  # type: ignore[misc]
        def Enabled(self) -> "b":  # type: ignore[name-defined]
            return self._enabled

        @Enabled.setter  # type: ignore[misc]
        def Enabled(self, value: "b") -> None:  # type: ignore[name-defined]
            self._enabled = bool(value)
            self._engine.enabled = bool(value)
            log.info("GestureEngine.Enabled set to %s via D-Bus", self._enabled)

        @method()  # type: ignore[misc]
        def BindGesture(self, gesture_id: "s", action: "s") -> None:  # type: ignore[name-defined]
            """Override a gesture binding at runtime."""
            self._engine.config["bindings"][gesture_id] = action
            log.info("D-Bus BindGesture: %s → %s", gesture_id, action)

        @dbus_signal()  # type: ignore[misc]
        def GestureDetected(self, gesture_id: "s", confidence: "d") -> None:  # type: ignore[name-defined]
            pass


async def setup_dbus(engine: "GestureEngine") -> Optional[Any]:
    if not DBUS_AVAILABLE:
        log.info("dbus-next not installed — D-Bus service disabled")
        return None
    try:
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        iface = GestureEngineInterface(engine)
        bus.export(DBUS_OBJECT_PATH, iface)
        await bus.request_name(DBUS_SERVICE_NAME)
        log.info("D-Bus service %s registered at %s", DBUS_SERVICE_NAME, DBUS_OBJECT_PATH)
        return (bus, iface)
    except Exception as exc:
        log.warning("D-Bus setup failed (non-fatal): %s", exc)
        return None


# ── libinput parser ───────────────────────────────────────────────────────────

# Regex patterns for libinput debug-events output
_RE_SWIPE_BEGIN  = re.compile(
    r"GESTURE_SWIPE_BEGIN\s+[+\d.]+\s+(?P<dev>\S+)\s+(?P<fingers>\d+)\s+fingers?"
)
_RE_SWIPE_UPDATE = re.compile(
    r"GESTURE_SWIPE_UPDATE\s+[+\d.]+\s+\S+\s+\d+\s+fingers?"
    r".*?(?P<dx>[+-]?\d+\.\d+)/(?P<dy>[+-]?\d+\.\d+)"
)
_RE_SWIPE_END    = re.compile(
    r"GESTURE_SWIPE_END\s+[+\d.]+\s+\S+\s+(?P<fingers>\d+)\s+fingers?"
    r"(?:.*?(?P<cancelled>cancelled))?"
)
_RE_PINCH_BEGIN  = re.compile(r"GESTURE_PINCH_BEGIN")
_RE_PINCH_UPDATE = re.compile(
    r"GESTURE_PINCH_UPDATE\s+[+\d.]+\s+\S+\s+\d+\s+fingers?"
    r".*?scale\s+(?P<scale>[+-]?\d+\.\d+)"
)
_RE_PINCH_END    = re.compile(
    r"GESTURE_PINCH_END\s+[+\d.]+\s+\S+\s+\d+\s+fingers?"
    r"(?:.*?(?P<cancelled>cancelled))?"
)
_RE_TOUCH_BEGIN  = re.compile(
    r"TOUCH_DOWN\s+[+\d.]+\s+\S+\s+(?P<slot>\d+)\s+\("
)
_RE_TOUCH_END    = re.compile(
    r"TOUCH_UP\s+[+\d.]+\s+\S+\s+(?P<slot>\d+)"
)


class LibinputParser:
    """
    Spawns `libinput debug-events --quiet` and parses its line-buffered
    stdout to emit GestureEvents.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        on_gesture: Callable[[GestureEvent], Coroutine[Any, Any, None]],
    ) -> None:
        self._cfg = config
        self._on_gesture = on_gesture
        self._swipe = SwipeState()
        self._pinch = PinchState()
        self._longpress = LongPressState()
        self._touch_slots: set[int] = set()
        self._lp_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
        sens = config.get("sensitivity", {})
        self._swipe_min   = float(sens.get("swipe_min_delta",       SWIPE_MIN_DELTA))
        self._pinch_ratio = float(sens.get("pinch_ratio_threshold", PINCH_RATIO_THRESHOLD))
        self._lp_secs     = float(sens.get("long_press_seconds",    LONG_PRESS_SECONDS))

    async def run(self) -> None:
        cmd = ["libinput", "debug-events", "--quiet"]
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                env={**os.environ, "LIBINPUT_DEBUG_EVENTS_QUIET": "1"},
            )
        except FileNotFoundError:
            log.warning("libinput not found — touchpad gestures disabled")
            return

        log.info("libinput debug-events started (pid=%s)", proc.pid)
        assert proc.stdout is not None

        try:
            while True:
                line_bytes = await proc.stdout.readline()
                if not line_bytes:
                    break
                line = line_bytes.decode(errors="replace").rstrip()
                await self._parse_line(line)
        except asyncio.CancelledError:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                proc.kill()
            raise
        finally:
            log.info("libinput reader stopped")

    async def _parse_line(self, line: str) -> None:
        # ── swipe begin ───────────────────────────────────────────────────────
        m = _RE_SWIPE_BEGIN.search(line)
        if m:
            self._swipe = SwipeState(
                fingers=int(m.group("fingers")),
                active=True,
            )
            # check if this might start a long-press (2-finger)
            if self._swipe.fingers == 2:
                self._start_longpress_timer()
            return

        # ── swipe update ──────────────────────────────────────────────────────
        m = _RE_SWIPE_UPDATE.search(line)
        if m and self._swipe.active:
            self._swipe.dx += float(m.group("dx"))
            self._swipe.dy += float(m.group("dy"))
            # movement cancels long-press
            if abs(self._swipe.dx) > 5 or abs(self._swipe.dy) > 5:
                self._cancel_longpress_timer()
            return

        # ── swipe end ─────────────────────────────────────────────────────────
        m = _RE_SWIPE_END.search(line)
        if m and self._swipe.active:
            cancelled = bool(m.group("cancelled"))
            self._cancel_longpress_timer()
            if not cancelled:
                await self._resolve_swipe()
            self._swipe = SwipeState()
            return

        # ── pinch begin ───────────────────────────────────────────────────────
        if _RE_PINCH_BEGIN.search(line):
            self._pinch = PinchState(scale=1.0, active=True)
            return

        # ── pinch update ──────────────────────────────────────────────────────
        m = _RE_PINCH_UPDATE.search(line)
        if m and self._pinch.active:
            self._pinch.scale = float(m.group("scale"))
            return

        # ── pinch end ─────────────────────────────────────────────────────────
        m = _RE_PINCH_END.search(line)
        if m and self._pinch.active:
            cancelled = bool(m.group("cancelled"))
            if not cancelled:
                await self._resolve_pinch()
            self._pinch = PinchState()
            return

    async def _resolve_swipe(self) -> None:
        dx, dy = self._swipe.dx, self._swipe.dy
        fingers = self._swipe.fingers
        total = math.hypot(dx, dy)
        if total < self._swipe_min:
            return

        # Determine primary axis
        if abs(dx) >= abs(dy):
            direction = "left" if dx < 0 else "right"
            axis = "h"
        else:
            direction = "up" if dy < 0 else "down"
            axis = "v"

        confidence = min(1.0, total / (self._swipe_min * 3))

        kind: Optional[GestureKind] = None
        if fingers == 3:
            kind = {
                "left":  GestureKind.SWIPE_3_LEFT,
                "right": GestureKind.SWIPE_3_RIGHT,
                "up":    GestureKind.SWIPE_3_UP,
                "down":  GestureKind.SWIPE_3_DOWN,
            }.get(direction)
        elif fingers == 4 and direction == "up":
            kind = GestureKind.SWIPE_4_UP

        if kind is not None:
            await self._on_gesture(GestureEvent(
                kind=kind,
                confidence=confidence,
                fingers=fingers,
                dx=dx,
                dy=dy,
                source="touchpad",
            ))

    async def _resolve_pinch(self) -> None:
        scale = self._pinch.scale
        ratio = abs(scale - 1.0)
        if ratio < self._pinch_ratio:
            return
        kind = GestureKind.PINCH_IN if scale < 1.0 else GestureKind.PINCH_OUT
        confidence = min(1.0, ratio / (self._pinch_ratio * 4))
        await self._on_gesture(GestureEvent(
            kind=kind,
            confidence=confidence,
            fingers=2,
            scale=scale,
            source="touchpad",
        ))

    def _start_longpress_timer(self) -> None:
        self._cancel_longpress_timer()
        self._lp_task = asyncio.ensure_future(self._longpress_timeout())

    def _cancel_longpress_timer(self) -> None:
        if self._lp_task and not self._lp_task.done():
            self._lp_task.cancel()
        self._lp_task = None

    async def _longpress_timeout(self) -> None:
        await asyncio.sleep(self._lp_secs)
        await self._on_gesture(GestureEvent(
            kind=GestureKind.LONGPRESS_2,
            confidence=1.0,
            fingers=2,
            source="touchpad",
        ))


# ── mouse gesture tracker ─────────────────────────────────────────────────────

class MouseGestureTracker:
    """
    Reads /dev/input/event* via evdev (if available) for right-button drag
    gestures.  Falls back to a libinput-based relative motion parser.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        on_gesture: Callable[[GestureEvent], Coroutine[Any, Any, None]],
    ) -> None:
        self._cfg = config
        self._on_gesture = on_gesture
        sens = config.get("sensitivity", {})
        self._min_px = float(sens.get("mouse_drag_min_px", MOUSE_DRAG_MIN_PX))
        self._state = MouseDragState()

    async def run(self) -> None:
        try:
            import evdev  # type: ignore
            await self._run_evdev(evdev)
        except ImportError:
            log.info("python-evdev not installed — mouse gesture detection disabled")

    async def _run_evdev(self, evdev: Any) -> None:
        """Find the first mouse device and monitor it."""
        devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
        mice = [
            d for d in devices
            if evdev.ecodes.EV_REL in d.capabilities()
            and evdev.ecodes.BTN_RIGHT in d.capabilities().get(evdev.ecodes.EV_KEY, [])
        ]
        if not mice:
            log.info("No mouse evdev device found")
            return

        mouse = mice[0]
        log.info("Tracking mouse gestures on %s (%s)", mouse.path, mouse.name)

        try:
            async for ev in mouse.async_read_loop():
                await self._handle_evdev_event(ev, evdev)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("Mouse evdev error: %s", exc)

    async def _handle_evdev_event(self, ev: Any, evdev: Any) -> None:
        EV_KEY = evdev.ecodes.EV_KEY
        EV_REL = evdev.ecodes.EV_REL
        BTN_RIGHT = evdev.ecodes.BTN_RIGHT
        REL_X = evdev.ecodes.REL_X
        REL_Y = evdev.ecodes.REL_Y

        if ev.type == EV_KEY and ev.code == BTN_RIGHT:
            if ev.value == 1:  # press
                self._state = MouseDragState(
                    active=True,
                    start_x=0, start_y=0,
                    cur_x=0, cur_y=0,
                )
            elif ev.value == 0:  # release
                if self._state.active:
                    await self._resolve_drag()
                self._state = MouseDragState()

        elif ev.type == EV_REL and self._state.active:
            if ev.code == REL_X:
                self._state.cur_x += ev.value
            elif ev.code == REL_Y:
                self._state.cur_y += ev.value

    async def _resolve_drag(self) -> None:
        dx = self._state.cur_x
        dy = self._state.cur_y
        total = math.hypot(dx, dy)
        if total < self._min_px:
            return

        confidence = min(1.0, total / (self._min_px * 3))

        if abs(dx) >= abs(dy):
            kind = GestureKind.MOUSE_DRAG_LEFT if dx < 0 else GestureKind.MOUSE_DRAG_RIGHT
        else:
            kind = GestureKind.MOUSE_DRAG_UP if dy < 0 else GestureKind.MOUSE_DRAG_DOWN

        await self._on_gesture(GestureEvent(
            kind=kind,
            confidence=confidence,
            fingers=0,
            dx=dx,
            dy=dy,
            source="mouse",
        ))


# ── core engine ───────────────────────────────────────────────────────────────

class GestureEngine:
    """
    Orchestrates all input sources, D-Bus, HTTP posting, and logging.
    """

    def __init__(self) -> None:
        self.config: Dict[str, Any] = load_config()
        self.enabled: bool = self.config.get("daemon", {}).get("enabled", True)
        self._logger = GestureLogger(
            Path(self.config.get("logging", {}).get("gesture_log", str(GESTURE_LOG)))
        )
        self._dispatcher = ActionDispatcher(self.config)
        self._dbus_handle: Optional[Any] = None
        self._tasks: List[asyncio.Task] = []  # type: ignore[type-arg]

        # Cooldown: prevent gesture floods (minimum ms between same gesture)
        self._last_gesture: Dict[str, float] = defaultdict(float)
        self._cooldown_secs = 0.4

    async def on_gesture(self, event: GestureEvent) -> None:
        if not self.enabled:
            return

        # Cooldown guard
        now = time.time()
        last = self._last_gesture[event.kind.value]
        if now - last < self._cooldown_secs:
            log.debug("Gesture %s suppressed by cooldown", event.kind.value)
            return
        self._last_gesture[event.kind.value] = now

        # Look up binding
        bindings = self.config.get("bindings", {})
        action = bindings.get(event.kind.value)
        if action is None:
            log.debug("No binding for gesture %s", event.kind.value)
            return

        log.info(
            "Gesture: %-22s  conf=%.2f  fingers=%d  action=%s",
            event.kind.value, event.confidence, event.fingers, action
        )

        # Fire D-Bus signal
        if self._dbus_handle is not None:
            try:
                _, iface = self._dbus_handle
                iface.GestureDetected(event.kind.value, event.confidence)
            except Exception as exc:
                log.debug("D-Bus signal failed: %s", exc)

        # Log to JSONL
        self._logger.write(event, action)

        # Dispatch action
        await self._dispatcher.dispatch(action, event)

        # Always POST to Hermes for gestures not already handled there
        if not action.startswith("hermes:"):
            await post_to_hermes(event, self.config)

    async def run(self) -> None:
        log.info("SynthOS Gesture Engine v%s starting", VERSION)

        # D-Bus
        self._dbus_handle = await setup_dbus(self)

        # Input sources
        libinput_parser = LibinputParser(self.config, self.on_gesture)
        mouse_tracker   = MouseGestureTracker(self.config, self.on_gesture)

        self._tasks = [
            asyncio.ensure_future(libinput_parser.run()),
            asyncio.ensure_future(mouse_tracker.run()),
        ]

        # If D-Bus is available, keep its event loop running too
        if self._dbus_handle is not None:
            bus, _ = self._dbus_handle
            self._tasks.append(asyncio.ensure_future(bus.wait_for_disconnect()))

        log.info("Gesture engine running — PID %d", os.getpid())

        try:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

    async def shutdown(self) -> None:
        log.info("Shutting down gesture engine…")
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        log.info("Gesture engine stopped cleanly")


# ── entry point ───────────────────────────────────────────────────────────────

def setup_logging(level_name: str = "INFO") -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    fmt = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    # Suppress noisy sub-loggers
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def write_default_config() -> None:
    """Write a commented default config if none exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        return

    content = """\
# SynthOS Gesture Engine Configuration
# ~/.config/synthex/gestures.toml

[sensitivity]
swipe_min_delta       = 40.0   # px accumulated travel to trigger swipe
pinch_ratio_threshold = 0.15   # scale-change ratio to trigger pinch
mouse_drag_min_px     = 30     # px right-drag travel to trigger
long_press_seconds    = 1.5    # 2-finger hold duration

[hermes]
url             = "http://localhost:7700/gesture"
timeout_seconds = 2.0
enabled         = true

[logging]
level       = "INFO"
gesture_log = "~/.local/share/synthex/gesture-log.jsonl"

[daemon]
enabled               = true
libinput_debug_events = true

[bindings]
swipe_3_left    = "kwin:desktop_prev"
swipe_3_right   = "kwin:desktop_next"
swipe_3_up      = "hermes:open_krunner"
swipe_3_down    = "kwin:show_desktop"
swipe_4_up      = "synthex:focus_mode_toggle"
pinch_in        = "kwin:zoom_in"
pinch_out       = "kwin:zoom_out"
longpress_2     = "hermes:context_assistant"
mouse_drag_up   = "kwin:maximize"
mouse_drag_down = "kwin:minimize"
mouse_drag_left = "app:prev"
mouse_drag_right= "app:next"
"""
    CONFIG_FILE.write_text(content)
    log.info("Wrote default config to %s", CONFIG_FILE)


async def async_main() -> None:
    engine = GestureEngine()

    loop = asyncio.get_running_loop()

    def _handle_signal(sig: signal.Signals) -> None:
        log.info("Received %s", sig.name)
        asyncio.ensure_future(engine.shutdown())
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _handle_signal, sig)

    try:
        await engine.run()
    except asyncio.CancelledError:
        pass
    finally:
        await engine.shutdown()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="SynthOS Brain OS Gesture Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level from config",
    )
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Write default gestures.toml and exit",
    )
    args = parser.parse_args()

    # Peek at config for log level before full init
    cfg_log_level = "INFO"
    if tomllib is not None and CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "rb") as fh:
                _pre_cfg = tomllib.load(fh)
            cfg_log_level = _pre_cfg.get("logging", {}).get("level", "INFO")
        except Exception:
            pass

    setup_logging(args.log_level or cfg_log_level)

    if args.write_config:
        write_default_config()
        print(f"Config written to {CONFIG_FILE}")
        sys.exit(0)

    write_default_config()

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
