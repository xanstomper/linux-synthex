#!/usr/bin/env python3
"""SynthOS Predictive Launcher — ML-based app pre-launching via Markov chains"""

import os
import sys
import signal
import time
import json
import math
import logging
import threading
import argparse
import pathlib
import datetime
import subprocess
import collections
import typing
import hashlib
import itertools

from logging.handlers import RotatingFileHandler
from typing import Dict, List, Tuple, Optional, FrozenSet, Any

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

UID = os.getuid()

DIR_DATA   = pathlib.Path.home() / ".local" / "share" / "synthex"
DIR_CONFIG = pathlib.Path.home() / ".config" / "synthex"
PID_FILE   = pathlib.Path(f"/run/user/{UID}/synthex-predictive.pid")
HISTORY_FILE = DIR_DATA / "launch-history.json"
MODEL_FILE   = DIR_DATA / "launch-model.json"
LOG_FILE     = DIR_DATA / "predictive-launch.log"
CONFIG_FILE  = DIR_CONFIG / "predictive-launch.json"

DESKTOP_DIRS = [
    pathlib.Path.home() / ".local" / "share" / "applications",
    pathlib.Path("/usr/share/applications"),
]

POLL_INTERVAL_S      = 30
DBUS_BUS_NAME        = "org.synthex.Predictive"
DBUS_OBJECT_PATH     = "/org/synthex/Predictive"
DBUS_INTERFACE       = "org.synthex.Predictive"

HOUR_BUCKETS = {
    "morning":   range(6,  12),
    "afternoon": range(12, 18),
    "evening":   range(18, 22),
    "night":     list(range(22, 24)) + list(range(0, 6)),
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "threshold": 0.6,
    "max_prefork": 3,
    "prefork_timeout_minutes": 30,
    "excluded_apps": ["bash", "sh", "python3"],
}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    DIR_DATA.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("synthex.predictive")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        ))
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger

log = setup_logging()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = dict(DEFAULT_CONFIG)
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open() as f:
                    on_disk = json.load(f)
                with self._lock:
                    self._data.update(on_disk)
                log.debug("Config loaded from %s", CONFIG_FILE)
            except Exception as exc:
                log.warning("Failed to load config (%s); using defaults.", exc)

    def save(self) -> None:
        DIR_CONFIG.mkdir(parents=True, exist_ok=True)
        with self._lock:
            snapshot = dict(self._data)
        with CONFIG_FILE.open("w") as f:
            json.dump(snapshot, f, indent=2)
        log.debug("Config saved to %s", CONFIG_FILE)

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
        self.save()

    @property
    def threshold(self) -> float:
        return float(self.get("threshold", 0.6))

    @threshold.setter
    def threshold(self, value: float) -> None:
        self.set("threshold", float(value))

    @property
    def max_prefork(self) -> int:
        return int(self.get("max_prefork", 3))

    @property
    def prefork_timeout_minutes(self) -> int:
        return int(self.get("prefork_timeout_minutes", 30))

    @property
    def excluded_apps(self) -> List[str]:
        return list(self.get("excluded_apps", []))


config = Config()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def hour_bucket(hour: int) -> str:
    for name, rng in HOUR_BUCKETS.items():
        if hour in rng:
            return name
    return "night"


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def open_apps_snapshot() -> List[str]:
    """Return a sorted list of unique executable names currently running."""
    try:
        result = subprocess.run(
            ["ps", "-eo", "comm", "--no-headers"],
            capture_output=True, text=True, timeout=5
        )
        names = sorted(set(
            line.strip() for line in result.stdout.splitlines()
            if line.strip() and line.strip() not in config.excluded_apps
        ))
        return names
    except Exception as exc:
        log.debug("open_apps_snapshot failed: %s", exc)
        return []


def build_state(
    day_of_week: int,
    hour: int,
    open_apps: List[str],
) -> Tuple[int, str, FrozenSet[str]]:
    return (day_of_week, hour_bucket(hour), frozenset(open_apps))


def state_to_key(state: Tuple) -> str:
    dow, bucket, apps = state
    apps_hash = hashlib.sha256(
        json.dumps(sorted(apps), separators=(",", ":")).encode()
    ).hexdigest()[:16]
    return f"{dow}:{bucket}:{apps_hash}"


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class HistoryStore:
    def __init__(self) -> None:
        DIR_DATA.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(self, launched_app: str, open_apps: Optional[List[str]] = None) -> None:
        if open_apps is None:
            open_apps = open_apps_snapshot()
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = {
            "timestamp":   now.isoformat(),
            "day_of_week": now.weekday(),
            "hour":        now.hour,
            "open_apps":   open_apps,
            "launched_app": launched_app,
        }
        with self._lock:
            history = self._load_raw()
            history.append(entry)
            self._save_raw(history)
        log.debug("History: recorded launch of '%s'", launched_app)

    def load(self) -> List[Dict]:
        with self._lock:
            return self._load_raw()

    def clear(self) -> None:
        with self._lock:
            self._save_raw([])
        log.info("Launch history cleared.")

    def _load_raw(self) -> List[Dict]:
        if not HISTORY_FILE.exists():
            return []
        try:
            with HISTORY_FILE.open() as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception as exc:
            log.warning("History load error: %s", exc)
        return []

    def _save_raw(self, history: List[Dict]) -> None:
        tmp = HISTORY_FILE.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(history, f, indent=2)
        tmp.replace(HISTORY_FILE)


history_store = HistoryStore()

# ---------------------------------------------------------------------------
# Markov chain model
# ---------------------------------------------------------------------------

class MarkovModel:
    """
    State = (day_of_week, hour_bucket, frozenset_of_open_apps)
    Transitions: state_key -> {app_name: count}
    """

    def __init__(self) -> None:
        # state_key -> collections.Counter
        self._transitions: Dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        self._lock = threading.RLock()
        self._trained_on: int = 0  # number of history entries used

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, history: List[Dict]) -> None:
        """Rebuild the chain from scratch using the provided history."""
        new_transitions: Dict[str, collections.Counter] = collections.defaultdict(
            collections.Counter
        )
        excluded = set(config.excluded_apps)
        for entry in history:
            app = entry.get("launched_app", "")
            if not app or app in excluded:
                continue
            try:
                dow    = int(entry["day_of_week"])
                hour   = int(entry["hour"])
                o_apps = list(entry.get("open_apps", []))
            except (KeyError, ValueError, TypeError):
                continue
            state = build_state(dow, hour, o_apps)
            key   = state_to_key(state)
            new_transitions[key][app] += 1

        with self._lock:
            self._transitions = new_transitions
            self._trained_on  = len(history)
        log.info("Model trained on %d history entries, %d unique states.",
                 len(history), len(new_transitions))

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        current_state: Tuple,
        top_n: int = 3,
    ) -> List[Tuple[str, float]]:
        """Return [(app_name, probability), ...] sorted by probability desc."""
        key = state_to_key(current_state)
        with self._lock:
            counter = self._transitions.get(key, collections.Counter())

        if not counter:
            # Fall back to global popularity across all states
            counter = self._global_popularity()

        total = sum(counter.values())
        if total == 0:
            return []

        ranked = counter.most_common(top_n)
        return [(app, count / total) for app, count in ranked]

    def _global_popularity(self) -> collections.Counter:
        combined: collections.Counter = collections.Counter()
        with self._lock:
            for c in self._transitions.values():
                combined.update(c)
        return combined

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        DIR_DATA.mkdir(parents=True, exist_ok=True)
        with self._lock:
            serialisable = {
                k: dict(v) for k, v in self._transitions.items()
            }
            trained_on = self._trained_on
        payload = {
            "version":    1,
            "trained_on": trained_on,
            "saved_at":   now_iso(),
            "transitions": serialisable,
        }
        tmp = MODEL_FILE.with_suffix(".tmp")
        with tmp.open("w") as f:
            json.dump(payload, f)
        tmp.replace(MODEL_FILE)
        log.debug("Model saved to %s (%d states).", MODEL_FILE, len(serialisable))

    def load(self) -> bool:
        if not MODEL_FILE.exists():
            log.info("No saved model found at %s.", MODEL_FILE)
            return False
        try:
            with MODEL_FILE.open() as f:
                payload = json.load(f)
            raw = payload.get("transitions", {})
            transitions: Dict[str, collections.Counter] = collections.defaultdict(
                collections.Counter
            )
            for k, v in raw.items():
                transitions[k] = collections.Counter(v)
            with self._lock:
                self._transitions = transitions
                self._trained_on  = payload.get("trained_on", 0)
            log.info("Model loaded from %s (%d states, trained on %d entries).",
                     MODEL_FILE, len(transitions), self._trained_on)
            return True
        except Exception as exc:
            log.warning("Model load failed: %s", exc)
            return False


model = MarkovModel()

# ---------------------------------------------------------------------------
# Accuracy tracker
# ---------------------------------------------------------------------------

class AccuracyTracker:
    """Thread-safe tracker for prediction accuracy."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total_launches   = 0
        self._correct_at_top_n = 0
        self._pre_launches_used = 0

    def record_launch(self, app: str, predictions: List[Tuple[str, float]]) -> None:
        predicted_apps = [a for a, _ in predictions]
        with self._lock:
            self._total_launches += 1
            if app in predicted_apps:
                self._correct_at_top_n += 1
        log.debug(
            "Accuracy: launched=%s  predicted=%s  hit=%s",
            app, predicted_apps, app in predicted_apps
        )

    def record_prefork_used(self) -> None:
        with self._lock:
            self._pre_launches_used += 1

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._total_launches
            correct = self._correct_at_top_n
            used = self._pre_launches_used
        rate = (correct / total) if total > 0 else 0.0
        return {
            "total_launches":    total,
            "accuracy_rate":     round(rate, 4),
            "pre_launches_used": used,
        }


accuracy = AccuracyTracker()

# ---------------------------------------------------------------------------
# Pre-forking manager
# ---------------------------------------------------------------------------

class PreForkEntry(typing.NamedTuple):
    proc:       subprocess.Popen
    app_name:   str
    started_at: float          # time.monotonic()


class PreForkManager:
    """
    Manages pre-forked (SIGSTOP-ed) processes.
    When the user launches the app we resume it with SIGCONT.
    Stale entries are reaped after prefork_timeout_minutes.
    """

    def __init__(self) -> None:
        self._lock   = threading.Lock()
        self._procs: Dict[str, PreForkEntry] = {}
        self._reaper = threading.Thread(
            target=self._reap_loop, name="prefork-reaper", daemon=True
        )

    def start(self) -> None:
        self._reaper.start()

    def prefork(self, app_name: str) -> bool:
        """Spawn app_name, immediately SIGSTOP it, and record it."""
        with self._lock:
            if app_name in self._procs:
                log.debug("Pre-fork: '%s' already pre-forked.", app_name)
                return False
            if len(self._procs) >= config.max_prefork:
                log.debug("Pre-fork: at capacity (%d).", config.max_prefork)
                return False

        excluded = set(config.excluded_apps)
        if app_name in excluded:
            return False

        try:
            proc = subprocess.Popen(
                [app_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            # Give the process a moment to initialise before we stop it
            time.sleep(0.05)
            os.kill(proc.pid, signal.SIGSTOP)
            entry = PreForkEntry(proc=proc, app_name=app_name, started_at=time.monotonic())
            with self._lock:
                self._procs[app_name] = entry
            log.info("Pre-forked '%s' (pid=%d) and SIGSTOP-ed.", app_name, proc.pid)
            return True
        except FileNotFoundError:
            log.warning("Pre-fork: executable '%s' not found.", app_name)
        except PermissionError as exc:
            log.warning("Pre-fork: permission error for '%s': %s", app_name, exc)
        except Exception as exc:
            log.error("Pre-fork: unexpected error for '%s': %s", app_name, exc)
        return False

    def activate(self, app_name: str) -> bool:
        """Resume a pre-forked process when the user actually launches the app."""
        with self._lock:
            entry = self._procs.pop(app_name, None)
        if entry is None:
            return False
        try:
            os.kill(entry.proc.pid, signal.SIGCONT)
            latency = time.monotonic() - entry.started_at
            log.info(
                "Activated pre-forked '%s' (pid=%d) after %.1fs warm-up.",
                app_name, entry.proc.pid, latency
            )
            accuracy.record_prefork_used()
            return True
        except ProcessLookupError:
            log.warning("Activate: process '%s' (pid=%d) already gone.",
                        app_name, entry.proc.pid)
        except Exception as exc:
            log.error("Activate '%s': %s", app_name, exc)
        return False

    def kill_prefork(self, app_name: str) -> None:
        with self._lock:
            entry = self._procs.pop(app_name, None)
        if entry is None:
            return
        self._terminate_entry(entry)
        log.info("Killed stale pre-fork for '%s' (pid=%d).", app_name, entry.proc.pid)

    def kill_all(self) -> None:
        with self._lock:
            entries = list(self._procs.values())
            self._procs.clear()
        for entry in entries:
            self._terminate_entry(entry)
        log.info("Killed all (%d) pre-forked processes.", len(entries))

    def list_preforked(self) -> List[str]:
        with self._lock:
            return list(self._procs.keys())

    def _terminate_entry(self, entry: PreForkEntry) -> None:
        try:
            os.kill(entry.proc.pid, signal.SIGCONT)   # un-stop so SIGTERM is delivered
            entry.proc.terminate()
            entry.proc.wait(timeout=3)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            try:
                entry.proc.kill()
            except ProcessLookupError:
                pass
        except Exception as exc:
            log.debug("_terminate_entry error: %s", exc)

    def _reap_loop(self) -> None:
        while True:
            time.sleep(60)
            timeout_s = config.prefork_timeout_minutes * 60
            now = time.monotonic()
            with self._lock:
                stale = [
                    name for name, entry in self._procs.items()
                    if (now - entry.started_at) > timeout_s
                ]
            for name in stale:
                log.info("Reaping timed-out pre-fork for '%s'.", name)
                self.kill_prefork(name)


prefork_manager = PreForkManager()

# ---------------------------------------------------------------------------
# Process monitor — detects new app launches
# ---------------------------------------------------------------------------

class ProcessMonitor:
    """
    Polls running processes every POLL_INTERVAL_S seconds.
    When a new process appears it is treated as a launch event.
    """

    def __init__(self, on_launch: typing.Callable[[str], None]) -> None:
        self._on_launch   = on_launch
        self._known: set  = set()
        self._thread      = threading.Thread(
            target=self._poll_loop, name="process-monitor", daemon=True
        )
        self._stop_event  = threading.Event()

    def start(self) -> None:
        self._known = self._current_procs()
        self._thread.start()
        log.debug("ProcessMonitor started (interval=%ds).", POLL_INTERVAL_S)

    def stop(self) -> None:
        self._stop_event.set()

    def _poll_loop(self) -> None:
        while not self._stop_event.wait(POLL_INTERVAL_S):
            try:
                current = self._current_procs()
                new_procs = current - self._known
                for name in new_procs:
                    if name not in config.excluded_apps:
                        log.debug("ProcessMonitor: detected new process '%s'.", name)
                        self._on_launch(name)
                self._known = current
            except Exception as exc:
                log.warning("ProcessMonitor poll error: %s", exc)

    @staticmethod
    def _current_procs() -> set:
        try:
            result = subprocess.run(
                ["ps", "-eo", "comm", "--no-headers"],
                capture_output=True, text=True, timeout=5
            )
            return {
                line.strip() for line in result.stdout.splitlines()
                if line.strip()
            }
        except Exception:
            return set()


# ---------------------------------------------------------------------------
# Desktop file watcher (inotify via inotifywait)
# ---------------------------------------------------------------------------

class DesktopWatcher:
    """
    Watches .desktop file directories with inotifywait.
    A CLOSE_WRITE or CREATE event on a .desktop file is treated as a launch.
    Requires inotifywait to be installed (inotify-tools).
    """

    def __init__(self, on_desktop_launch: typing.Callable[[str], None]) -> None:
        self._callback = on_desktop_launch
        self._proc: Optional[subprocess.Popen] = None
        self._thread   = threading.Thread(
            target=self._watch_loop, name="desktop-watcher", daemon=True
        )

    def start(self) -> None:
        dirs = [str(d) for d in DESKTOP_DIRS if d.exists()]
        if not dirs:
            log.info("DesktopWatcher: no existing desktop dirs to watch.")
            return
        try:
            self._proc = subprocess.Popen(
                [
                    "inotifywait",
                    "-m", "-r",
                    "-e", "close_write",
                    "-e", "create",
                    "--format", "%f",
                ] + dirs,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            self._thread.start()
            log.info("DesktopWatcher started on %s.", dirs)
        except FileNotFoundError:
            log.info(
                "inotifywait not found — desktop-file watching disabled. "
                "Install inotify-tools to enable."
            )
        except Exception as exc:
            log.warning("DesktopWatcher start error: %s", exc)

    def stop(self) -> None:
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass

    def _watch_loop(self) -> None:
        if self._proc is None or self._proc.stdout is None:
            return
        try:
            for line in self._proc.stdout:
                fname = line.strip()
                if fname.endswith(".desktop"):
                    app_name = fname[:-8]  # strip .desktop suffix
                    if app_name and app_name not in config.excluded_apps:
                        log.debug("DesktopWatcher: event for '%s'.", app_name)
                        self._callback(app_name)
        except Exception as exc:
            log.debug("DesktopWatcher loop ended: %s", exc)


# ---------------------------------------------------------------------------
# Core daemon / orchestrator
# ---------------------------------------------------------------------------

class PredictiveLauncher:
    """Central orchestrator — wires model, monitor, pre-forker and DBus."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._current_predictions: List[Tuple[str, float]] = []
        self._pred_lock = threading.Lock()

        self._process_monitor = ProcessMonitor(on_launch=self._on_app_launched)
        self._desktop_watcher = DesktopWatcher(
            on_desktop_launch=self._on_app_launched
        )
        self._retrain_thread  = threading.Thread(
            target=self._periodic_retrain,
            name="model-retrain",
            daemon=True,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        log.info("SynthOS Predictive Launcher starting (uid=%d).", UID)
        self._write_pid()

        # Load or train model
        if not model.load():
            history = history_store.load()
            if history:
                model.train(history)
                model.save()

        prefork_manager.start()
        self._process_monitor.start()
        self._desktop_watcher.start()
        self._retrain_thread.start()

        # Initial prediction pass
        self._run_predictions()

        log.info("Predictive Launcher ready.")

    def run_until_stopped(self) -> None:
        self.start()
        try:
            while not self._stop_event.is_set():
                self._stop_event.wait(timeout=60)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        log.info("Shutting down Predictive Launcher.")
        self._stop_event.set()
        self._process_monitor.stop()
        self._desktop_watcher.stop()
        prefork_manager.kill_all()
        model.save()
        self._remove_pid()
        log.info("Shutdown complete.")

    # ------------------------------------------------------------------
    # Launch event handler
    # ------------------------------------------------------------------

    def _on_app_launched(self, app_name: str) -> None:
        if app_name in config.excluded_apps:
            return

        log.info("Launch detected: '%s'.", app_name)

        # 1. Activate pre-fork if available
        prefork_manager.activate(app_name)

        # 2. Record to history
        history_store.append(app_name)

        # 3. Update accuracy
        with self._pred_lock:
            preds = list(self._current_predictions)
        accuracy.record_launch(app_name, preds)

        # 4. Re-run predictions based on updated state
        self._run_predictions()

    def record_launch_explicit(self, app_name: str) -> None:
        """Called from DBus RecordLaunch."""
        self._on_app_launched(app_name)

    # ------------------------------------------------------------------
    # Prediction + pre-fork pipeline
    # ------------------------------------------------------------------

    def _run_predictions(self) -> None:
        now   = datetime.datetime.now()
        state = build_state(now.weekday(), now.hour, open_apps_snapshot())
        preds = model.predict(state, top_n=config.max_prefork * 2)

        with self._pred_lock:
            self._current_predictions = preds

        threshold = config.threshold
        preforked = set(prefork_manager.list_preforked())
        candidates = [
            (app, prob) for app, prob in preds
            if prob >= threshold and app not in preforked
        ]
        # Pre-fork up to max_prefork
        prefork_count = len(preforked)
        for app, prob in candidates:
            if prefork_count >= config.max_prefork:
                break
            if prefork_manager.prefork(app):
                prefork_count += 1
                log.info("Pre-forked candidate '%s' (prob=%.2f).", app, prob)

    def get_predictions(self) -> List[Dict[str, Any]]:
        with self._pred_lock:
            preds = list(self._current_predictions)
        preforked = set(prefork_manager.list_preforked())
        return [
            {
                "app":          app,
                "probability":  round(prob, 4),
                "pre_launched": app in preforked,
            }
            for app, prob in preds
        ]

    # ------------------------------------------------------------------
    # Periodic model retraining (every hour)
    # ------------------------------------------------------------------

    def _periodic_retrain(self) -> None:
        while not self._stop_event.wait(3600):
            try:
                log.info("Periodic model retrain starting.")
                history = history_store.load()
                model.train(history)
                model.save()
                self._run_predictions()
            except Exception as exc:
                log.error("Periodic retrain error: %s", exc)

    # ------------------------------------------------------------------
    # PID management
    # ------------------------------------------------------------------

    def _write_pid(self) -> None:
        try:
            PID_FILE.parent.mkdir(parents=True, exist_ok=True)
            PID_FILE.write_text(str(os.getpid()))
            log.debug("PID %d written to %s.", os.getpid(), PID_FILE)
        except Exception as exc:
            log.warning("Could not write PID file: %s", exc)

    def _remove_pid(self) -> None:
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception as exc:
            log.debug("PID file removal error: %s", exc)


# ---------------------------------------------------------------------------
# DBus service
# ---------------------------------------------------------------------------

def _start_dbus_service(launcher: PredictiveLauncher) -> None:
    """
    Attempt to register a DBus service.
    Gracefully skips if dbus-python is not installed.
    """
    try:
        import dbus                          # type: ignore
        import dbus.service                  # type: ignore
        import dbus.mainloop.glib            # type: ignore
        from gi.repository import GLib      # type: ignore
    except ImportError:
        log.info(
            "dbus-python / GLib not available — DBus service disabled. "
            "Install python3-dbus to enable."
        )
        return

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    class PredictiveService(dbus.service.Object):
        def __init__(self, _launcher: PredictiveLauncher) -> None:
            self._launcher = _launcher
            bus  = dbus.SessionBus()
            name = dbus.service.BusName(DBUS_BUS_NAME, bus)
            super().__init__(name, DBUS_OBJECT_PATH)

        @dbus.service.method(DBUS_INTERFACE, out_signature="s")
        def GetPredictions(self) -> str:  # noqa: N802
            return json.dumps(self._launcher.get_predictions())

        @dbus.service.method(DBUS_INTERFACE, in_signature="s")
        def RecordLaunch(self, app_name: str) -> None:  # noqa: N802
            self._launcher.record_launch_explicit(str(app_name))

        @dbus.service.method(DBUS_INTERFACE, in_signature="d")
        def SetThreshold(self, threshold: float) -> None:  # noqa: N802
            config.threshold = float(threshold)
            log.info("Threshold set to %.2f via DBus.", threshold)

        @dbus.service.method(DBUS_INTERFACE, out_signature="s")
        def GetStats(self) -> str:  # noqa: N802
            return json.dumps(accuracy.stats())

    def _run_loop() -> None:
        try:
            service = PredictiveService(launcher)  # noqa: F841
            loop    = GLib.MainLoop()
            log.info("DBus service %s registered.", DBUS_BUS_NAME)
            loop.run()
        except Exception as exc:
            log.error("DBus service error: %s", exc)

    t = threading.Thread(target=_run_loop, name="dbus-service", daemon=True)
    t.start()


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

_LAUNCHER_SINGLETON: Optional[PredictiveLauncher] = None


def _handle_sigterm(signum: int, frame: Any) -> None:
    log.info("SIGTERM received — initiating shutdown.")
    if _LAUNCHER_SINGLETON is not None:
        _LAUNCHER_SINGLETON.shutdown()
    sys.exit(0)


def _handle_sighup(signum: int, frame: Any) -> None:
    log.info("SIGHUP received — reloading config.")
    config._load()


def register_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGHUP,  _handle_sighup)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _read_pid() -> Optional[int]:
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except ValueError:
            pass
    return None


def _daemon_running() -> bool:
    pid = _read_pid()
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but we can't signal it


def cmd_start(_args: argparse.Namespace) -> int:
    if _daemon_running():
        print("Predictive Launcher is already running (pid=%s)." % _read_pid())
        return 1

    global _LAUNCHER_SINGLETON
    register_signal_handlers()
    launcher = PredictiveLauncher()
    _LAUNCHER_SINGLETON = launcher
    _start_dbus_service(launcher)
    launcher.run_until_stopped()
    return 0


def cmd_stop(_args: argparse.Namespace) -> int:
    pid = _read_pid()
    if pid is None or not _daemon_running():
        print("Predictive Launcher is not running.")
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
        print("Sent SIGTERM to pid %d." % pid)
        return 0
    except ProcessLookupError:
        print("Process %d not found." % pid)
        return 1
    except PermissionError:
        print("Permission denied sending signal to pid %d." % pid)
        return 1


def cmd_status(_args: argparse.Namespace) -> int:
    running = _daemon_running()
    pid     = _read_pid()
    if running:
        print("Status: RUNNING  (pid=%d)" % pid)
    else:
        print("Status: STOPPED")
    stats = accuracy.stats()
    print("  Total launches recorded : %(total_launches)d" % stats)
    print("  Prediction accuracy     : %(accuracy_rate).2%%" % {
        "accuracy_rate": stats["accuracy_rate"]
    })
    print("  Pre-launches activated  : %(pre_launches_used)d" % stats)
    return 0


def cmd_predict(_args: argparse.Namespace) -> int:
    if not model.load():
        history = history_store.load()
        if not history:
            print("No history available — cannot predict.")
            return 1
        model.train(history)

    now   = datetime.datetime.now()
    state = build_state(now.weekday(), now.hour, open_apps_snapshot())
    preds = model.predict(state, top_n=5)

    if not preds:
        print("No predictions available (insufficient history).")
        return 0

    print("Top predictions for current context:")
    print("  %-30s  %s" % ("App", "Probability"))
    print("  " + "-" * 42)
    for app, prob in preds:
        bar = "█" * int(prob * 20)
        print("  %-30s  %.1f%%  %s" % (app, prob * 100, bar))
    return 0


def cmd_stats(_args: argparse.Namespace) -> int:
    stats = accuracy.stats()
    print(json.dumps(stats, indent=2))
    return 0


def cmd_clear_history(_args: argparse.Namespace) -> int:
    history_store.clear()
    print("Launch history cleared.")
    return 0


# ---------------------------------------------------------------------------
# Argument parser & entry-point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthex-predict",
        description="SynthOS Predictive Launcher — ML-based app pre-launching.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    sub.add_parser("start",         help="Start the predictive launcher daemon")
    sub.add_parser("stop",          help="Stop the running daemon")
    sub.add_parser("status",        help="Show daemon status and accuracy stats")
    sub.add_parser("predict",       help="Print current top predictions and exit")
    sub.add_parser("stats",         help="Print accuracy stats as JSON and exit")
    sub.add_parser("clear-history", help="Erase all recorded launch history")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args   = parser.parse_args(argv)

    dispatch: Dict[str, typing.Callable[[argparse.Namespace], int]] = {
        "start":         cmd_start,
        "stop":          cmd_stop,
        "status":        cmd_status,
        "predict":       cmd_predict,
        "stats":         cmd_stats,
        "clear-history": cmd_clear_history,
    }

    cmd = args.command
    if cmd is None:
        parser.print_help()
        return 0

    handler = dispatch.get(cmd)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
