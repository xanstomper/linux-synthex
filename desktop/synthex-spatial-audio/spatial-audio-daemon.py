#!/usr/bin/env python3
"""
SynthOS Brain OS — Spatial Audio Daemon
/home/jewboy420/linux-synthex/desktop/synthex-spatial-audio/spatial-audio-daemon.py

Polls Brain OS context endpoint, maps detected activity to an audio profile,
drives EasyEffects + PipeWire, and exposes org.synthex.SpatialAudio over D-Bus.

D-Bus API
─────────
  Interface : org.synthex.SpatialAudio
  Object    : /org/synthex/SpatialAudio
  Methods   : SetProfile(profile: String) -> ()
              GetProfile() -> String
  Signals   : ProfileChanged(old_profile: String, new_profile: String)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
import threading
from pathlib import Path
from typing import Optional

import dbus
import dbus.service
import dbus.mainloop.glib
import requests
from gi.repository import GLib

# ── Constants ─────────────────────────────────────────────────────────────────

DBUS_BUS_NAME   = "org.synthex.SpatialAudio"
DBUS_OBJECT_PATH = "/org/synthex/SpatialAudio"
DBUS_INTERFACE  = "org.synthex.SpatialAudio"

CONTEXT_URL     = "http://localhost:7700/context"
POLL_INTERVAL   = 5          # seconds between context polls
REQUEST_TIMEOUT = 3          # seconds for HTTP request

DATA_DIR   = Path.home() / ".local" / "share" / "synthex"
LOG_FILE   = DATA_DIR / "spatial-audio.log"
STATE_FILE = DATA_DIR / "spatial-audio-state.json"

EASYEFFECTS_BUS = "com.github.wwmm.easyeffects"
EASYEFFECTS_OBJ = "/com/github/wwmm/easyeffects"
EASYEFFECTS_IFACE = "com.github.wwmm.easyeffects"

# Activity keyword → profile mapping (first match wins)
ACTIVITY_MAP: list[tuple[list[str], str]] = [
    (["gaming", "game", "steam", "lutris", "proton"],           "gaming"),
    (["focus", "coding", "code", "terminal", "ide", "work"],    "focus"),
    (["video", "streaming", "youtube", "netflix", "cinema",
      "mpv", "vlc", "movie"],                                   "cinema"),
    (["music", "spotify", "tidal", "rhythmbox", "strawberry"],  "music"),
]

DEFAULT_PROFILE = "music"

# PipeWire sink node name inserted by setup.sh filter-chain
SYNTHEX_SINK = "synthex_spatial_capture"

# ── Logging ───────────────────────────────────────────────────────────────────

DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("synthex.spatial-audio")


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess, logging errors but never crashing the daemon."""
    log.debug("run: %s", " ".join(cmd))
    try:
        return subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=10, check=check,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        log.warning("Command failed: %s — %s", " ".join(cmd), exc)
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(exc))


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"profile": DEFAULT_PROFILE}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Profile drivers ───────────────────────────────────────────────────────────

class PipeWireDriver:
    """Thin wrapper around pw-cli for runtime node manipulation."""

    def set_volume(self, node_name: str, volume: float) -> None:
        """Set linear volume [0.0–1.0] on a named node."""
        run(["pw-cli", "set-param", node_name, "Props",
             f'{{ volume: {volume:.3f} }}'], check=False)

    def set_mute(self, node_name: str, mute: bool) -> None:
        run(["pw-cli", "set-param", node_name, "Props",
             f'{{ mute: {"true" if mute else "false"} }}'], check=False)

    def route_default_sink(self, sink_name: str) -> None:
        """Ask WirePlumber to make a sink the default."""
        run(["wpctl", "set-default", sink_name], check=False)

    def apply_eq_band(self, node_name: str, band: int, gain_db: float) -> None:
        """Apply a single EQ band via pw-cli (requires filter-chain EQ node)."""
        run(["pw-cli", "set-param", node_name, "Props",
             f'{{ params: [ "eq_band_{band}_gain" {gain_db:.1f} ] }}'], check=False)


class EasyEffectsDriver:
    """Controls EasyEffects via its D-Bus interface."""

    def __init__(self, session_bus: dbus.SessionBus) -> None:
        self._bus = session_bus
        self._proxy: Optional[dbus.proxies.Interface] = None

    def _get_proxy(self) -> Optional[dbus.proxies.Interface]:
        try:
            obj = self._bus.get_object(EASYEFFECTS_BUS, EASYEFFECTS_OBJ)
            return dbus.Interface(obj, EASYEFFECTS_IFACE)
        except dbus.DBusException as exc:
            log.debug("EasyEffects D-Bus unavailable: %s", exc)
            return None

    def load_preset(self, preset_name: str) -> bool:
        """
        Ask EasyEffects to load a named output preset.
        Falls back to writing to the EasyEffects IPC socket if D-Bus fails.
        """
        proxy = self._get_proxy()
        if proxy:
            try:
                proxy.loadPreset(preset_name)   # type: ignore[attr-defined]
                log.info("EasyEffects preset loaded via D-Bus: %s", preset_name)
                return True
            except dbus.DBusException as exc:
                log.warning("EasyEffects D-Bus loadPreset failed: %s", exc)

        # Fallback: easyeffects CLI (v7+)
        result = run(["easyeffects", "--load-preset", preset_name], check=False)
        if result.returncode == 0:
            log.info("EasyEffects preset loaded via CLI: %s", preset_name)
            return True

        log.warning("Could not load EasyEffects preset '%s'.", preset_name)
        return False

    def set_enabled(self, enabled: bool) -> None:
        proxy = self._get_proxy()
        if proxy:
            try:
                proxy.setEnabled(enabled)   # type: ignore[attr-defined]
            except dbus.DBusException:
                pass


class ProfileEngine:
    """Translates profile names into concrete audio system changes."""

    # preset name → (easyeffects_preset, pw_extra_steps_fn)
    PROFILES: dict[str, dict] = {
        "gaming": {
            "ee_preset":   "synthex-gaming",
            "description": "7.1 surround simulation, boosted lows",
            "pw_volume":   1.0,
        },
        "focus": {
            "ee_preset":   "synthex-focus",
            "description": "Brown noise, gentle compression, subtle reverb",
            "pw_volume":   0.75,
        },
        "cinema": {
            "ee_preset":   "synthex-cinema",
            "description": "Wide-stage cinema mode",
            "pw_volume":   0.95,
        },
        "music": {
            "ee_preset":   "synthex-music",
            "description": "Flat, accurate HRTF reproduction",
            "pw_volume":   0.90,
        },
    }

    def __init__(self, pw: PipeWireDriver, ee: EasyEffectsDriver) -> None:
        self._pw = pw
        self._ee = ee

    def apply(self, profile: str) -> None:
        cfg = self.PROFILES.get(profile)
        if not cfg:
            log.warning("Unknown profile '%s', falling back to music.", profile)
            profile = DEFAULT_PROFILE
            cfg = self.PROFILES[profile]

        log.info("Applying profile '%s': %s", profile, cfg["description"])

        # 1. Load EasyEffects preset
        self._ee.load_preset(cfg["ee_preset"])

        # 2. PipeWire volume
        self._pw.set_volume(SYNTHEX_SINK, cfg["pw_volume"])

        # 3. Profile-specific PipeWire tweaks
        if profile == "gaming":
            self._apply_gaming()
        elif profile == "focus":
            self._apply_focus()
        elif profile == "cinema":
            self._apply_cinema()
        elif profile == "music":
            self._apply_music()

    def _apply_gaming(self) -> None:
        # Boost sub-bass (+3 dB on band 0 ≈ 60 Hz) and low-mid (+1 dB)
        self._pw.apply_eq_band(SYNTHEX_SINK, 0,  3.0)
        self._pw.apply_eq_band(SYNTHEX_SINK, 1,  1.0)
        self._pw.apply_eq_band(SYNTHEX_SINK, 5, -0.5)

    def _apply_focus(self) -> None:
        # Cut highs slightly, mild mid scoop for fatigue reduction
        self._pw.apply_eq_band(SYNTHEX_SINK, 7, -2.0)
        self._pw.apply_eq_band(SYNTHEX_SINK, 8, -1.5)
        self._pw.apply_eq_band(SYNTHEX_SINK, 3, -1.0)

    def _apply_cinema(self) -> None:
        # Very slight bass shelf (+1.5) and air (+2 dB at 12 kHz)
        self._pw.apply_eq_band(SYNTHEX_SINK, 1,  1.5)
        self._pw.apply_eq_band(SYNTHEX_SINK, 9,  2.0)

    def _apply_music(self) -> None:
        # Flat — reset all bands to 0
        for band in range(10):
            self._pw.apply_eq_band(SYNTHEX_SINK, band, 0.0)


# ── Context poller ────────────────────────────────────────────────────────────

class ContextPoller:
    """Polls the Brain OS context endpoint and emits profile-change callbacks."""

    def __init__(self, on_profile_change) -> None:
        self._callback = on_profile_change
        self._session  = requests.Session()
        self._session.headers["User-Agent"] = "SynthOS-SpatialAudio/1.0"
        self._last_profile: Optional[str] = None
        self._running = False
        self._thread:  Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="ctx-poller")
        self._thread.start()
        log.info("Context poller started (interval=%ds, url=%s)", POLL_INTERVAL, CONTEXT_URL)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=POLL_INTERVAL + 1)

    def _loop(self) -> None:
        while self._running:
            try:
                self._poll()
            except Exception as exc:        # broad catch — never crash poller
                log.debug("Poll error: %s", exc)
            time.sleep(POLL_INTERVAL)

    def _poll(self) -> None:
        try:
            resp = self._session.get(CONTEXT_URL, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            ctx = resp.json()
        except requests.RequestException as exc:
            log.debug("Context endpoint unreachable: %s", exc)
            return

        activity: str = ctx.get("activity", "").lower()
        tags: list[str] = [t.lower() for t in ctx.get("tags", [])]
        combined = activity + " " + " ".join(tags)

        profile = self._activity_to_profile(combined)
        if profile != self._last_profile:
            log.info("Context changed → profile: %s (activity=%r)", profile, activity)
            self._last_profile = profile
            self._callback(profile)

    @staticmethod
    def _activity_to_profile(text: str) -> str:
        for keywords, profile in ACTIVITY_MAP:
            if any(kw in text for kw in keywords):
                return profile
        return DEFAULT_PROFILE


# ── D-Bus service ─────────────────────────────────────────────────────────────

class SpatialAudioService(dbus.service.Object):
    """
    org.synthex.SpatialAudio D-Bus service.

    Methods
    -------
    SetProfile(profile)  → change the active audio profile
    GetProfile()         → return the current profile name

    Signals
    -------
    ProfileChanged(old, new)
    """

    def __init__(self, bus: dbus.SessionBus, engine: ProfileEngine) -> None:
        bus_name = dbus.service.BusName(DBUS_BUS_NAME, bus=bus)
        super().__init__(bus_name, DBUS_OBJECT_PATH)
        self._engine  = engine
        self._profile = load_state().get("profile", DEFAULT_PROFILE)
        log.info("D-Bus service registered: %s at %s", DBUS_BUS_NAME, DBUS_OBJECT_PATH)

    # ── Public methods ────────────────────────────────────────────────────────

    @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="")
    def SetProfile(self, profile: str) -> None:                      # noqa: N802
        profile = str(profile).strip().lower()
        if profile not in ProfileEngine.PROFILES:
            raise dbus.DBusException(
                f"Unknown profile '{profile}'. "
                f"Valid: {', '.join(ProfileEngine.PROFILES)}"
            )
        old = self._profile
        if old == profile:
            log.debug("SetProfile: already on '%s', no-op.", profile)
            return
        self._apply_profile(profile)
        self.ProfileChanged(old, profile)

    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
    def GetProfile(self) -> str:                                      # noqa: N802
        return self._profile

    # ── Signal ────────────────────────────────────────────────────────────────

    @dbus.service.signal(DBUS_INTERFACE, signature="ss")
    def ProfileChanged(self, old_profile: str, new_profile: str) -> None:  # noqa: N802
        # Signal body — GLib emits this automatically
        log.info("Signal ProfileChanged('%s', '%s')", old_profile, new_profile)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _apply_profile(self, profile: str) -> None:
        self._engine.apply(profile)
        self._profile = profile
        save_state({"profile": profile})

    def apply_from_context(self, profile: str) -> None:
        """Called by the context poller from its background thread."""
        old = self._profile
        if old == profile:
            return
        # Schedule back onto the GLib main loop (thread-safe)
        GLib.idle_add(self._apply_and_signal, old, profile)

    def _apply_and_signal(self, old: str, new: str) -> bool:
        self._apply_profile(new)
        self.ProfileChanged(old, new)
        return GLib.SOURCE_REMOVE


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SynthOS Spatial Audio Daemon")
    parser.add_argument("--no-context-poll", action="store_true",
                        help="Disable automatic Brain OS context polling.")
    parser.add_argument("--profile", default=None,
                        help="Force an initial profile, then exit.")
    args = parser.parse_args()

    # D-Bus requires the GLib main loop for signal delivery
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    try:
        session_bus = dbus.SessionBus()
    except dbus.DBusException as exc:
        log.critical("Cannot connect to D-Bus session bus: %s", exc)
        sys.exit(1)

    pw_driver = PipeWireDriver()
    ee_driver = EasyEffectsDriver(session_bus)
    engine    = ProfileEngine(pw_driver, ee_driver)
    service   = SpatialAudioService(session_bus, engine)

    # Apply persisted/initial profile on startup
    initial = args.profile or load_state().get("profile", DEFAULT_PROFILE)
    log.info("Startup profile: %s", initial)
    engine.apply(initial)

    if args.profile:
        # One-shot mode: apply and quit
        save_state({"profile": initial})
        log.info("One-shot profile applied. Exiting.")
        return

    # Start context poller (background thread → GLib idle callbacks)
    poller: Optional[ContextPoller] = None
    if not args.no_context_poll:
        poller = ContextPoller(on_profile_change=service.apply_from_context)
        poller.start()

    loop = GLib.MainLoop()

    def _shutdown(signum, _frame):
        log.info("Received signal %d — shutting down.", signum)
        if poller:
            poller.stop()
        loop.quit()

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT,  _shutdown)

    log.info("SynthOS Spatial Audio daemon running. PID=%d", os.getpid())
    try:
        loop.run()
    finally:
        log.info("Daemon stopped.")


if __name__ == "__main__":
    main()
