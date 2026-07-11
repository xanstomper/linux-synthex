#!/usr/bin/env python3
"""SynthOS Focus Mode — Distraction-free environment with binaural beats"""

import os
import sys
import signal
import time
import json
import math
import wave
import struct
import subprocess
import threading
import logging
import argparse
import pathlib
import datetime
from typing import Optional, List, Dict, Any, Tuple

# ─────────────────────────────────────────────
# Constants & Paths
# ─────────────────────────────────────────────

VERSION = "1.0.0"
APP_NAME = "synthex-focus-mode"

STATE_DIR = pathlib.Path.home() / ".local" / "share" / "synthex"
STATE_FILE = STATE_DIR / "focus-mode-state.json"
HISTORY_FILE = STATE_DIR / "focus-history.json"
BINAURAL_WAV = pathlib.Path("/tmp/synthex-binaural.wav")
BELL_WAV = pathlib.Path("/tmp/synthex-bell.wav")
LOG_FILE = STATE_DIR / "focus-mode.log"

DBUS_SERVICE = "org.synthex.FocusMode"
DBUS_PATH = "/org/synthex/FocusMode"
DBUS_IFACE = "org.synthex.FocusMode"

DEFAULT_FOCUS_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
SAMPLE_RATE = 44100
BINAURAL_DURATION_SEC = 60 * 60  # 1 hour loop (trimmed on playback)

DISTRACTING_APPS: List[str] = [
    "discord",
    "telegram-desktop",
    "slack",
    "spotify",
    "firefox",
    "thunderbird",
]

# Binaural beat presets: (beat_hz, base_left_hz, base_right_hz, label)
BINAURAL_PRESETS: Dict[str, Tuple[int, int, int, str]] = {
    "focus": (40, 200, 240, "Gamma — Deep Focus"),
    "relax": (10, 200, 210, "Alpha — Relaxed Awareness"),
    "sleep": (4,  200, 204, "Theta — Drowsy / Sleep"),
}

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────

STATE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(APP_NAME)

# ─────────────────────────────────────────────
# Audio generation
# ─────────────────────────────────────────────

def _sine_samples(freq_hz: float, duration_sec: float, sample_rate: int = SAMPLE_RATE,
                  amplitude: float = 0.6) -> List[float]:
    """Return a list of normalised float samples for a pure sine wave."""
    n = int(sample_rate * duration_sec)
    return [amplitude * math.sin(2.0 * math.pi * freq_hz * i / sample_rate) for i in range(n)]


def _fade(samples: List[float], sample_rate: int = SAMPLE_RATE,
          fade_ms: int = 20) -> List[float]:
    """Apply a linear fade-in and fade-out to avoid clicking."""
    fade_n = int(sample_rate * fade_ms / 1000)
    result = samples[:]
    for i in range(min(fade_n, len(result))):
        t = i / fade_n
        result[i] *= t
        result[-(i + 1)] *= t
    return result


def generate_binaural_wav(output_path: pathlib.Path, mode: str = "focus",
                           duration_sec: float = 30.0) -> bool:
    """
    Generate a stereo binaural-beat WAV file at *output_path*.

    The left channel plays at *base_left_hz* and the right channel plays at
    *base_right_hz*.  The difference is the binaural beat frequency that the
    brain perceives when listening through headphones.

    Returns True on success, False on error.
    """
    preset = BINAURAL_PRESETS.get(mode, BINAURAL_PRESETS["focus"])
    beat_hz, left_hz, right_hz, label = preset

    log.info("Generating binaural WAV: mode=%s (%s) beat=%d Hz left=%d Hz right=%d Hz duration=%.0fs",
             mode, label, beat_hz, left_hz, right_hz, duration_sec)

    try:
        left_samples  = _fade(_sine_samples(left_hz,  duration_sec))
        right_samples = _fade(_sine_samples(right_hz, duration_sec))

        n_frames = len(left_samples)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)          # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.setnframes(n_frames)

            for l, r in zip(left_samples, right_samples):
                l_int = int(max(-32768, min(32767, l * 32767)))
                r_int = int(max(-32768, min(32767, r * 32767)))
                wf.writeframes(struct.pack("<hh", l_int, r_int))

        log.info("Binaural WAV written to %s (%.1f MB)",
                 output_path, output_path.stat().st_size / 1_048_576)
        return True

    except Exception as exc:
        log.error("Failed to generate binaural WAV: %s", exc)
        return False


def generate_bell_wav(output_path: pathlib.Path, freq_hz: float = 440.0,
                      duration_sec: float = 1.5, amplitude: float = 0.5) -> bool:
    """
    Generate a short mono bell tone (exponentially decaying sine) at *output_path*.
    Returns True on success.
    """
    log.info("Generating bell WAV: %s @ %.0f Hz", output_path, freq_hz)
    try:
        n = int(SAMPLE_RATE * duration_sec)
        decay = math.exp(-4.0 / (SAMPLE_RATE * duration_sec))
        env = amplitude

        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.setnframes(n)
            for i in range(n):
                sample = env * math.sin(2.0 * math.pi * freq_hz * i / SAMPLE_RATE)
                env *= decay
                wf.writeframes(struct.pack("<h", int(max(-32768, min(32767, sample * 32767)))))

        return True
    except Exception as exc:
        log.error("Failed to generate bell WAV: %s", exc)
        return False


def play_wav(path: pathlib.Path, loop: bool = False) -> Optional[subprocess.Popen]:
    """
    Attempt to play *path* with paplay → aplay → ffplay.
    If *loop* is True, wrap in a shell loop (best-effort).
    Returns the Popen object so the caller can terminate it, or None.
    """
    if not path.exists():
        log.warning("WAV file not found: %s", path)
        return None

    players = [
        (["paplay", "--volume=49152", str(path)], "paplay"),
        (["aplay", "-q", str(path)], "aplay"),
        (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)], "ffplay"),
    ]

    if loop:
        shell_players = [
            (f"while true; do paplay --volume=49152 {path}; done", "paplay-loop"),
            (f"while true; do aplay -q {path}; done", "aplay-loop"),
            (f"ffplay -nodisp -loop 0 -loglevel quiet {path}", "ffplay-loop"),
        ]

    for (cmd, name) in (shell_players if loop else players):
        try:
            if loop and isinstance(cmd, str):
                proc = subprocess.Popen(["bash", "-c", cmd],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            else:
                proc = subprocess.Popen(cmd,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)
            log.info("Playing audio via %s (pid=%d)", name, proc.pid)
            return proc
        except FileNotFoundError:
            continue
        except Exception as exc:
            log.debug("Audio player %s failed: %s", name, exc)

    log.warning("No audio player found (tried paplay, aplay, ffplay)")
    return None


def stop_audio(proc: Optional[subprocess.Popen]) -> None:
    """Terminate an audio playback process."""
    if proc and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


# ─────────────────────────────────────────────
# Do Not Disturb
# ─────────────────────────────────────────────

class DndManager:
    """Manages Do-Not-Disturb state across KDE, GNOME, and dunst/mako fallbacks."""

    def __init__(self) -> None:
        self._kde_cookie: Optional[str] = None
        self._gnome_prev: Optional[str] = None
        self._stopped_notifiers: List[str] = []

    # ── KDE ──────────────────────────────────

    def _kde_inhibit(self) -> bool:
        try:
            result = subprocess.run(
                [
                    "qdbus", "org.kde.plasmashell",
                    "/org/freedesktop/Notifications",
                    "org.freedesktop.Notifications.Inhibit",
                    APP_NAME, "Focus Mode active", "{}",
                ],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self._kde_cookie = result.stdout.strip()
                log.info("KDE DND enabled (cookie=%s)", self._kde_cookie)
                return True
        except Exception as exc:
            log.debug("KDE DND inhibit failed: %s", exc)
        return False

    def _kde_uninhibit(self) -> bool:
        if not self._kde_cookie:
            return False
        try:
            subprocess.run(
                [
                    "qdbus", "org.kde.plasmashell",
                    "/org/freedesktop/Notifications",
                    "org.freedesktop.Notifications.UnInhibit",
                    self._kde_cookie,
                ],
                capture_output=True, timeout=5,
            )
            log.info("KDE DND released (cookie=%s)", self._kde_cookie)
            self._kde_cookie = None
            return True
        except Exception as exc:
            log.debug("KDE DND uninhibit failed: %s", exc)
        return False

    # ── GNOME ────────────────────────────────

    def _gnome_inhibit(self) -> bool:
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.notifications", "show-banners"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                self._gnome_prev = result.stdout.strip()
                subprocess.run(
                    ["gsettings", "set", "org.gnome.desktop.notifications",
                     "show-banners", "false"],
                    timeout=5,
                )
                log.info("GNOME DND enabled (prev show-banners=%s)", self._gnome_prev)
                return True
        except Exception as exc:
            log.debug("GNOME DND inhibit failed: %s", exc)
        return False

    def _gnome_uninhibit(self) -> bool:
        if self._gnome_prev is None:
            return False
        try:
            subprocess.run(
                ["gsettings", "set", "org.gnome.desktop.notifications",
                 "show-banners", self._gnome_prev],
                timeout=5,
            )
            log.info("GNOME DND released (restored show-banners=%s)", self._gnome_prev)
            self._gnome_prev = None
            return True
        except Exception as exc:
            log.debug("GNOME DND uninhibit failed: %s", exc)
        return False

    # ── Fallback: stop dunst / mako ──────────

    def _notifier_stop(self) -> bool:
        stopped: List[str] = []
        for notifier in ("dunst", "mako"):
            try:
                result = subprocess.run(["pgrep", "-x", notifier],
                                        capture_output=True, timeout=3)
                if result.returncode == 0:
                    subprocess.run(["pkill", "-STOP", notifier], timeout=3)
                    stopped.append(notifier)
                    log.info("Sent SIGSTOP to %s", notifier)
            except Exception as exc:
                log.debug("Failed to stop %s: %s", notifier, exc)
        self._stopped_notifiers = stopped
        return bool(stopped)

    def _notifier_cont(self) -> None:
        for notifier in self._stopped_notifiers:
            try:
                subprocess.run(["pkill", "-CONT", notifier], timeout=3)
                log.info("Sent SIGCONT to %s", notifier)
            except Exception as exc:
                log.debug("Failed to resume %s: %s", notifier, exc)
        self._stopped_notifiers.clear()

    # ── Public ───────────────────────────────

    def enable(self) -> None:
        if not self._kde_inhibit():
            if not self._gnome_inhibit():
                self._notifier_stop()

    def disable(self) -> None:
        self._kde_uninhibit()
        self._gnome_uninhibit()
        self._notifier_cont()


# ─────────────────────────────────────────────
# App suspension
# ─────────────────────────────────────────────

class AppSuspender:
    """Sends SIGSTOP to distracting processes and SIGCONT to restore them."""

    def __init__(self, app_names: Optional[List[str]] = None) -> None:
        self._targets: List[str] = app_names if app_names is not None else DISTRACTING_APPS
        self._suspended_pids: Dict[str, List[int]] = {}  # name → [pid, ...]

    def _find_pids(self, name: str) -> List[int]:
        """Return a list of PIDs whose process name matches *name* (partial)."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", name],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return [int(p) for p in result.stdout.split() if p.strip().isdigit()]
        except Exception as exc:
            log.debug("pgrep failed for %s: %s", name, exc)
        return []

    def suspend_all(self) -> None:
        self._suspended_pids.clear()
        for app in self._targets:
            pids = self._find_pids(app)
            if pids:
                sent: List[int] = []
                for pid in pids:
                    try:
                        os.kill(pid, signal.SIGSTOP)
                        sent.append(pid)
                        log.info("SIGSTOP → %s (pid=%d)", app, pid)
                    except ProcessLookupError:
                        pass
                    except PermissionError:
                        log.warning("No permission to SIGSTOP pid=%d (%s)", pid, app)
                if sent:
                    self._suspended_pids[app] = sent

    def resume_all(self) -> None:
        for app, pids in self._suspended_pids.items():
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGCONT)
                    log.info("SIGCONT → %s (pid=%d)", app, pid)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    log.warning("No permission to SIGCONT pid=%d (%s)", pid, app)
        self._suspended_pids.clear()

    @property
    def suspended(self) -> Dict[str, List[int]]:
        return dict(self._suspended_pids)


# ─────────────────────────────────────────────
# Desktop notifications
# ─────────────────────────────────────────────

def notify(title: str, body: str, urgency: str = "normal",
           icon: str = "preferences-system-time") -> None:
    """Send a desktop notification via notify-send (best-effort)."""
    try:
        subprocess.run(
            ["notify-send", f"--urgency={urgency}", f"--icon={icon}",
             "--app-name=SynthOS Focus", title, body],
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        log.warning("notify-send not found; skipping notification: %s — %s", title, body)
    except Exception as exc:
        log.debug("notify-send failed: %s", exc)


# ─────────────────────────────────────────────
# KWin rule writer (KDE)
# ─────────────────────────────────────────────

def write_kwin_rule(window_class: str) -> bool:
    """
    Write a temporary KWin rule to force *window_class* always-on-top.
    Uses kwriteconfig5 to append to kwinrulesrc.
    Returns True if kwriteconfig5 is available.
    """
    try:
        subprocess.run(["which", "kwriteconfig5"], capture_output=True, check=True, timeout=5)
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.debug("kwriteconfig5 not available; skipping KWin rule")
        return False

    group = f"SynthexFocus_{window_class}"
    rules = {
        "Description":          f"SynthOS Focus: {window_class} always on top",
        "wmclass":              window_class,
        "wmclasscomplete":      "false",
        "wmclassmatch":         "1",
        "above":                "true",
        "aboverule":            "2",  # Force
    }

    try:
        for key, value in rules.items():
            subprocess.run(
                ["kwriteconfig5", "--file", "kwinrulesrc",
                 "--group", group, "--key", key, value],
                timeout=5, check=True,
            )
        subprocess.run(
            ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"],
            timeout=5, check=False,
        )
        log.info("KWin always-on-top rule written for '%s'", window_class)
        return True
    except Exception as exc:
        log.warning("KWin rule write failed: %s", exc)
        return False


def remove_kwin_rule(window_class: str) -> None:
    """Remove the KWin rule written by write_kwin_rule."""
    group = f"SynthexFocus_{window_class}"
    try:
        subprocess.run(
            ["kwriteconfig5", "--file", "kwinrulesrc",
             "--group", group, "--key", "Description", "--delete"],
            timeout=5, check=False,
        )
        subprocess.run(
            ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"],
            timeout=5, check=False,
        )
        log.info("KWin rule removed for '%s'", window_class)
    except Exception as exc:
        log.debug("KWin rule removal failed: %s", exc)


# ─────────────────────────────────────────────
# State file helpers
# ─────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()


def write_state(data: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(STATE_FILE)
    except Exception as exc:
        log.error("Failed to write state file: %s", exc)


def read_state() -> Optional[Dict[str, Any]]:
    try:
        return json.loads(STATE_FILE.read_text())
    except FileNotFoundError:
        return None
    except Exception as exc:
        log.error("Failed to read state file: %s", exc)
        return None


def clear_state() -> None:
    try:
        STATE_FILE.unlink(missing_ok=True)
    except Exception as exc:
        log.debug("Failed to clear state file: %s", exc)


# ─────────────────────────────────────────────
# Session history
# ─────────────────────────────────────────────

def append_history(entry: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    history: List[Dict[str, Any]] = []
    try:
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())
            if not isinstance(history, list):
                history = []
    except Exception:
        history = []

    history.append(entry)

    try:
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception as exc:
        log.error("Failed to write history: %s", exc)


# ─────────────────────────────────────────────
# DBus service (org.synthex.FocusMode)
# ─────────────────────────────────────────────

_DBUS_AVAILABLE = False
try:
    import dbus                          # type: ignore
    import dbus.service                  # type: ignore
    import dbus.mainloop.glib            # type: ignore
    from gi.repository import GLib       # type: ignore
    _DBUS_AVAILABLE = True
except ImportError:
    pass


if _DBUS_AVAILABLE:
    class FocusModeDBusService(dbus.service.Object):
        """
        DBus service exposing org.synthex.FocusMode.

        Methods
        -------
        Start(minutes: uint32, mode: str) → void
        Stop() → void
        GetStatus() → dict{sv}
        TakeBreak() → void

        Properties (via introspection)
        --------------------------------
        IsActive  : bool
        TimeRemaining : uint32 (seconds)
        Mode : str
        """

        def __init__(self, session: "FocusSession",
                     bus: "dbus.SessionBus",
                     object_path: str = DBUS_PATH) -> None:
            bus_name = dbus.service.BusName(DBUS_SERVICE, bus=bus)
            super().__init__(bus_name, object_path)
            self._session = session
            log.info("DBus service registered as %s at %s", DBUS_SERVICE, object_path)

        # ── Methods ──────────────────────────

        @dbus.service.method(DBUS_IFACE,
                             in_signature="us", out_signature="")
        def Start(self, minutes: int, mode: str) -> None:
            """Start a focus session."""
            log.info("DBus Start called: minutes=%d mode=%s", minutes, mode)
            if self._session.is_active:
                log.warning("DBus Start: session already active")
                return
            threading.Thread(
                target=self._session.start,
                kwargs={"minutes": int(minutes), "mode": str(mode)},
                daemon=True,
            ).start()

        @dbus.service.method(DBUS_IFACE,
                             in_signature="", out_signature="")
        def Stop(self) -> None:
            """Stop the current focus session."""
            log.info("DBus Stop called")
            self._session.stop(reason="dbus")

        @dbus.service.method(DBUS_IFACE,
                             in_signature="", out_signature="a{sv}")
        def GetStatus(self) -> Dict[str, Any]:
            """Return current session status as a variant dict."""
            return {
                "is_active":       dbus.Boolean(self._session.is_active),
                "time_remaining":  dbus.UInt32(max(0, int(self._session.time_remaining))),
                "mode":            dbus.String(self._session.mode or ""),
                "breaks_taken":    dbus.UInt32(self._session.breaks_taken),
                "elapsed_seconds": dbus.UInt32(int(self._session.elapsed)),
            }

        @dbus.service.method(DBUS_IFACE,
                             in_signature="", out_signature="")
        def TakeBreak(self) -> None:
            """Trigger a break in the current session."""
            log.info("DBus TakeBreak called")
            self._session.take_break()

        # ── Signals ──────────────────────────

        @dbus.service.signal(DBUS_IFACE, signature="s")
        def StatusChanged(self, status: str) -> None:
            """Emitted when session status changes."""

        @dbus.service.signal(DBUS_IFACE, signature="u")
        def TimerTick(self, seconds_remaining: int) -> None:
            """Emitted every minute with remaining seconds."""


# ─────────────────────────────────────────────
# Pomodoro Timer
# ─────────────────────────────────────────────

class PomodoroTimer:
    """
    Runs a Pomodoro-style countdown in a background thread.

    Fires callbacks at:
      - halfway point
      - 5 minutes remaining
      - session end
    """

    def __init__(self, duration_minutes: int,
                 on_halfway: Optional[callable] = None,
                 on_five_minutes: Optional[callable] = None,
                 on_end: Optional[callable] = None,
                 tick_interval_sec: float = 1.0) -> None:
        self.duration_sec = duration_minutes * 60
        self.on_halfway = on_halfway
        self.on_five_minutes = on_five_minutes
        self.on_end = on_end
        self.tick_interval = tick_interval_sec

        self._remaining: float = float(self.duration_sec)
        self._started_at: Optional[float] = None
        self._paused_at: Optional[float] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._fired_halfway = False
        self._fired_five_min = False

    @property
    def remaining(self) -> float:
        if self._started_at is None:
            return self._remaining
        if self._paused_at is not None:
            return self._remaining
        elapsed = time.monotonic() - self._started_at
        return max(0.0, self._remaining - elapsed)

    @property
    def elapsed(self) -> float:
        return self.duration_sec - self.remaining

    def start(self) -> None:
        self._stop_event.clear()
        self._pause_event.clear()
        self._started_at = time.monotonic()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        if self._paused_at is None and self._started_at is not None:
            now = time.monotonic()
            self._remaining = max(0.0, self._remaining - (now - self._started_at))
            self._paused_at = now
            log.info("Timer paused (%.0f s remaining)", self._remaining)

    def resume(self) -> None:
        if self._paused_at is not None:
            self._started_at = time.monotonic()
            self._paused_at = None
            log.info("Timer resumed (%.0f s remaining)", self._remaining)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        log.info("Timer started: %.0f s", self.duration_sec)
        while not self._stop_event.is_set():
            rem = self.remaining
            if rem <= 0:
                if self.on_end:
                    try:
                        self.on_end()
                    except Exception as exc:
                        log.error("on_end callback error: %s", exc)
                break

            half = self.duration_sec / 2
            if not self._fired_halfway and (self.duration_sec - rem) >= half:
                self._fired_halfway = True
                if self.on_halfway:
                    try:
                        self.on_halfway(int(rem))
                    except Exception as exc:
                        log.error("on_halfway callback error: %s", exc)

            if not self._fired_five_min and rem <= 300:
                self._fired_five_min = True
                if self.on_five_minutes:
                    try:
                        self.on_five_minutes(int(rem))
                    except Exception as exc:
                        log.error("on_five_minutes callback error: %s", exc)

            time.sleep(self.tick_interval)

        log.info("Timer thread exiting")


# ─────────────────────────────────────────────
# Core Focus Session
# ─────────────────────────────────────────────

class FocusSession:
    """
    Orchestrates all focus-mode subsystems:
      binaural audio · DND · app suspension · timer · KWin rule · state/history
    """

    def __init__(self,
                 enable_binaural: bool = True,
                 enable_dnd: bool = True,
                 app_list: Optional[List[str]] = None,
                 kwin_window_class: Optional[str] = None) -> None:
        self.enable_binaural = enable_binaural
        self.enable_dnd = enable_dnd
        self.kwin_window_class = kwin_window_class

        self._dnd = DndManager()
        self._suspender = AppSuspender(app_names=app_list)
        self._audio_proc: Optional[subprocess.Popen] = None
        self._timer: Optional[PomodoroTimer] = None
        self._dbus_service: Optional[Any] = None

        self._is_active = False
        self._mode: Optional[str] = None
        self._breaks_taken = 0
        self._session_start: Optional[datetime.datetime] = None
        self._duration_minutes: int = DEFAULT_FOCUS_MINUTES
        self._stop_reason: Optional[str] = None
        self._break_thread: Optional[threading.Thread] = None

        self._lock = threading.Lock()

        # Register SIGTERM / SIGINT for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT,  self._handle_signal)

    # ── Properties ───────────────────────────

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def mode(self) -> Optional[str]:
        return self._mode

    @property
    def time_remaining(self) -> float:
        if self._timer is None:
            return 0.0
        return self._timer.remaining

    @property
    def elapsed(self) -> float:
        if self._timer is None:
            return 0.0
        return self._timer.elapsed

    @property
    def breaks_taken(self) -> int:
        return self._breaks_taken

    # ── Signal handler ───────────────────────

    def _handle_signal(self, signum: int, frame: Any) -> None:
        log.info("Received signal %d — initiating graceful shutdown", signum)
        self.stop(reason="signal")
        sys.exit(0)

    # ── Timer callbacks ──────────────────────

    def _on_halfway(self, remaining_sec: int) -> None:
        mins = remaining_sec // 60
        log.info("Halfway point — %d min remaining", mins)
        notify("⏱ SynthOS Focus — Halfway There!",
               f"{mins} minutes remaining in your focus session.",
               urgency="low")

    def _on_five_minutes(self, remaining_sec: int) -> None:
        log.info("5 minutes remaining")
        notify("⚠ SynthOS Focus — Almost Done!",
               "5 minutes remaining. Start wrapping up.",
               urgency="normal")

    def _on_end(self) -> None:
        log.info("Focus session ended — playing bell and notifying")
        generate_bell_wav(BELL_WAV)
        bell_proc = play_wav(BELL_WAV, loop=False)
        if bell_proc:
            bell_proc.wait(timeout=5)

        notify("✅ SynthOS Focus — Session Complete!",
               f"Great work! Your {self._duration_minutes}-minute focus session is done.\n"
               f"Take a {DEFAULT_BREAK_MINUTES}-minute break.",
               urgency="critical",
               icon="dialog-ok-apply")
        self.stop(reason="completed")

    # ── Start / Stop ─────────────────────────

    def start(self, minutes: int = DEFAULT_FOCUS_MINUTES, mode: str = "focus") -> None:
        with self._lock:
            if self._is_active:
                log.warning("Session already active — ignoring start()")
                return

            if mode not in BINAURAL_PRESETS:
                log.warning("Unknown mode '%s', defaulting to 'focus'", mode)
                mode = "focus"

            self._mode = mode
            self._duration_minutes = minutes
            self._is_active = True
            self._session_start = datetime.datetime.now(tz=datetime.timezone.utc)
            self._breaks_taken = 0
            self._stop_reason = None

        log.info("=== SynthOS Focus Mode START (mode=%s, %d min) ===", mode, minutes)
        notify("🧠 SynthOS Focus Mode",
               f"Starting {minutes}-minute {mode} session.\nDistractions blocked.",
               urgency="normal",
               icon="preferences-system-time")

        # 1. Write state
        write_state({
            "active": True,
            "mode": mode,
            "minutes": minutes,
            "started_at": _now_iso(),
            "pid": os.getpid(),
        })

        # 2. Enable DND
        if self.enable_dnd:
            self._dnd.enable()

        # 3. Suspend distracting apps
        self._suspender.suspend_all()

        # 4. KWin rule
        if self.kwin_window_class:
            write_kwin_rule(self.kwin_window_class)

        # 5. Generate & play binaural audio
        if self.enable_binaural:
            # Use a shorter generation for quick start then loop
            duration = min(float(minutes * 60 + 10), 3600.0)
            if generate_binaural_wav(BINAURAL_WAV, mode=mode, duration_sec=duration):
                self._audio_proc = play_wav(BINAURAL_WAV, loop=True)

        # 6. Start timer
        self._timer = PomodoroTimer(
            duration_minutes=minutes,
            on_halfway=self._on_halfway,
            on_five_minutes=self._on_five_minutes,
            on_end=self._on_end,
        )
        self._timer.start()

        log.info("Focus session running. Timer thread started.")

    def stop(self, reason: str = "user") -> None:
        with self._lock:
            if not self._is_active:
                return
            self._is_active = False
            self._stop_reason = reason

        log.info("=== SynthOS Focus Mode STOP (reason=%s) ===", reason)

        # 1. Stop timer
        if self._timer:
            self._timer.stop()
            self._timer = None

        # 2. Stop audio
        stop_audio(self._audio_proc)
        self._audio_proc = None

        # 3. Resume suspended apps
        self._suspender.resume_all()

        # 4. Disable DND
        if self.enable_dnd:
            self._dnd.disable()

        # 5. Remove KWin rule
        if self.kwin_window_class:
            remove_kwin_rule(self.kwin_window_class)

        # 6. Write history
        elapsed_sec = 0
        if self._session_start:
            elapsed_sec = int(
                (datetime.datetime.now(tz=datetime.timezone.utc) - self._session_start)
                .total_seconds()
            )

        append_history({
            "started_at":      self._session_start.isoformat() if self._session_start else None,
            "ended_at":        _now_iso(),
            "mode":            self._mode,
            "planned_minutes": self._duration_minutes,
            "elapsed_seconds": elapsed_sec,
            "breaks_taken":    self._breaks_taken,
            "completed":       reason == "completed",
            "stop_reason":     reason,
        })

        # 7. Clear state
        clear_state()

        if reason != "completed":
            notify("🛑 SynthOS Focus Mode",
                   "Session ended. All apps resumed.",
                   urgency="low")

        log.info("Focus session stopped. Elapsed: %d s", elapsed_sec)

    # ── Break ────────────────────────────────

    def take_break(self) -> None:
        """Pause the timer for DEFAULT_BREAK_MINUTES, notify, then resume."""
        if not self._is_active:
            log.warning("take_break called but no active session")
            return
        if self._break_thread and self._break_thread.is_alive():
            log.warning("Break already in progress")
            return

        self._break_thread = threading.Thread(target=self._break_worker, daemon=True)
        self._break_thread.start()

    def _break_worker(self) -> None:
        self._breaks_taken += 1
        log.info("Break #%d starting (%d min)", self._breaks_taken, DEFAULT_BREAK_MINUTES)
        notify("☕ SynthOS Break Time",
               f"Take a {DEFAULT_BREAK_MINUTES}-minute break!\nTimer paused.",
               urgency="normal",
               icon="coffee")

        if self._timer:
            self._timer.pause()

        # Temporarily resume distracting apps during break
        self._suspender.resume_all()
        if self.enable_dnd:
            self._dnd.disable()

        time.sleep(DEFAULT_BREAK_MINUTES * 60)

        if not self._is_active:
            return  # session was stopped during break

        # Restore
        self._suspender.suspend_all()
        if self.enable_dnd:
            self._dnd.enable()

        if self._timer:
            self._timer.resume()

        notify("🔁 SynthOS Focus",
               "Break over — back to focus mode!",
               urgency="normal")
        log.info("Break #%d ended — resuming timer", self._breaks_taken)

    # ── DBus integration ─────────────────────

    def run_dbus_service(self) -> None:
        """Register the DBus service and run the GLib main loop."""
        if not _DBUS_AVAILABLE:
            log.warning("python-dbus / GLib not available; DBus service disabled")
            return

        try:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()
            self._dbus_service = FocusModeDBusService(session=self, bus=bus)
            loop = GLib.MainLoop()
            log.info("DBus main loop running")
            loop.run()
        except Exception as exc:
            log.warning("DBus service failed to start: %s", exc)

    # ── Blocking wait (CLI usage) ─────────────

    def wait_until_done(self) -> None:
        """Block the calling thread until the session ends."""
        while self._is_active:
            time.sleep(1)


# ─────────────────────────────────────────────
# Status display helpers
# ─────────────────────────────────────────────

def _fmt_duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"


def print_status(state: Optional[Dict[str, Any]]) -> None:
    if state is None or not state.get("active"):
        print("SynthOS Focus Mode: ● INACTIVE")
        return

    started = state.get("started_at", "?")
    mode    = state.get("mode", "?")
    minutes = state.get("minutes", "?")
    pid     = state.get("pid", "?")

    print(f"SynthOS Focus Mode: ● ACTIVE")
    print(f"  Mode    : {mode}")
    print(f"  Duration: {minutes} min")
    print(f"  Started : {started}")
    print(f"  PID     : {pid}")

    # Try to compute elapsed from started_at
    try:
        started_dt = datetime.datetime.fromisoformat(started)
        elapsed = (datetime.datetime.now(tz=datetime.timezone.utc) - started_dt).total_seconds()
        remaining = float(minutes) * 60 - elapsed
        print(f"  Elapsed : {_fmt_duration(elapsed)}")
        print(f"  Remaining: {_fmt_duration(remaining)}")
    except Exception:
        pass


def print_history(limit: int = 10) -> None:
    try:
        history: List[Dict[str, Any]] = json.loads(HISTORY_FILE.read_text())
    except FileNotFoundError:
        print("No session history found.")
        return
    except Exception as exc:
        print(f"Error reading history: {exc}")
        return

    entries = history[-limit:]
    print(f"Last {len(entries)} focus sessions:")
    print("-" * 60)
    for i, entry in enumerate(reversed(entries), start=1):
        completed = "✅" if entry.get("completed") else "⛔"
        started   = entry.get("started_at", "?")[:19].replace("T", " ")
        elapsed   = _fmt_duration(entry.get("elapsed_seconds", 0))
        mode      = entry.get("mode", "?")
        breaks    = entry.get("breaks_taken", 0)
        planned   = entry.get("planned_minutes", "?")
        print(f"{i:2}. {completed} {started}  {mode:6}  {elapsed} / {planned}min  breaks={breaks}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthex-focus",
        description="SynthOS Focus Mode — Distraction-free environment with binaural beats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  synthex-focus start 25
  synthex-focus start 50 --mode relax --no-dnd
  synthex-focus start 90 --apps discord,slack
  synthex-focus stop
  synthex-focus status
  synthex-focus break
  synthex-focus history
""",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable debug logging")

    sub = parser.add_subparsers(dest="command", title="commands")

    # start
    p_start = sub.add_parser("start", help="Start a focus session")
    p_start.add_argument("minutes", nargs="?", type=int, default=DEFAULT_FOCUS_MINUTES,
                         help=f"Duration in minutes (default: {DEFAULT_FOCUS_MINUTES})")
    p_start.add_argument("--mode", choices=list(BINAURAL_PRESETS.keys()), default="focus",
                         help="Binaural beat mode (default: focus)")
    p_start.add_argument("--no-binaural", action="store_true",
                         help="Disable binaural beat audio")
    p_start.add_argument("--no-dnd", action="store_true",
                         help="Disable Do Not Disturb")
    p_start.add_argument("--apps", type=str, default=None,
                         metavar="LIST",
                         help="Comma-separated list of app names to suspend "
                              f"(default: {','.join(DISTRACTING_APPS)})")
    p_start.add_argument("--kwin-class", type=str, default=None,
                         metavar="CLASS",
                         help="KWin window class to pin always-on-top (KDE only)")
    p_start.add_argument("--dbus-service", action="store_true",
                         help="Also expose a DBus service (org.synthex.FocusMode)")

    # stop
    sub.add_parser("stop", help="Stop the current focus session")

    # status
    sub.add_parser("status", help="Show current session status")

    # break
    sub.add_parser("break", help="Trigger a break in the active session")

    # history
    p_hist = sub.add_parser("history", help="Show focus session history")
    p_hist.add_argument("--limit", type=int, default=10,
                        help="Number of recent sessions to show (default: 10)")

    return parser


def cmd_start(args: argparse.Namespace) -> int:
    state = read_state()
    if state and state.get("active"):
        existing_pid = state.get("pid")
        if existing_pid:
            try:
                os.kill(existing_pid, 0)   # check if process is alive
                print(f"Error: A focus session is already active (pid={existing_pid}).")
                print("Run 'synthex-focus stop' first.")
                return 1
            except ProcessLookupError:
                log.warning("Stale state file found (pid=%d dead) — clearing", existing_pid)
                clear_state()

    app_list: Optional[List[str]] = None
    if args.apps:
        app_list = [a.strip() for a in args.apps.split(",") if a.strip()]

    session = FocusSession(
        enable_binaural=not args.no_binaural,
        enable_dnd=not args.no_dnd,
        app_list=app_list,
        kwin_window_class=args.kwin_class,
    )

    if args.dbus_service:
        dbus_thread = threading.Thread(
            target=session.run_dbus_service, daemon=True
        )
        dbus_thread.start()
        # Give the DBus thread a moment to register
        time.sleep(0.5)

    session.start(minutes=args.minutes, mode=args.mode)
    print(f"Focus session started: {args.minutes} min [{args.mode}] (PID {os.getpid()})")
    print("Press Ctrl+C to stop early.")
    session.wait_until_done()
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    state = read_state()
    if not state or not state.get("active"):
        print("No active focus session.")
        return 0

    pid = state.get("pid")
    if not pid:
        print("State file has no PID — clearing stale state.")
        clear_state()
        return 0

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to focus session (pid={pid}).")
    except ProcessLookupError:
        print(f"Process {pid} not found — clearing stale state.")
        clear_state()
    except PermissionError:
        print(f"Permission denied to signal pid={pid}.")
        return 1
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = read_state()
    print_status(state)
    return 0


def cmd_break(args: argparse.Namespace) -> int:
    state = read_state()
    if not state or not state.get("active"):
        print("No active focus session.")
        return 1

    if not _DBUS_AVAILABLE:
        print("python-dbus not available; cannot signal break over DBus.")
        print("Tip: run 'kill -USR1 <pid>' instead (not implemented in this session).")
        return 1

    try:
        import dbus  # type: ignore
        bus = dbus.SessionBus()
        obj = bus.get_object(DBUS_SERVICE, DBUS_PATH)
        iface = dbus.Interface(obj, dbus_interface=DBUS_IFACE)
        iface.TakeBreak()
        print("Break triggered.")
    except Exception as exc:
        print(f"DBus call failed: {exc}")
        return 1
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    print_history(limit=args.limit)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "start":   cmd_start,
        "stop":    cmd_stop,
        "status":  cmd_status,
        "break":   cmd_break,
        "history": cmd_history,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
