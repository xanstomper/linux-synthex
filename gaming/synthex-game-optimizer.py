#!/usr/bin/env python3
"""SynthOS Game Optimizer - Per-game automatic performance tuning"""

import os
import sys
import signal
import time
import json
import logging
import threading
import subprocess
import argparse
import pathlib
import typing
import hashlib

from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POLL_INTERVAL: float = 2.0  # seconds between process scans

PID_FILE: pathlib.Path = pathlib.Path("/run/synthex-game-optimizer.pid")

LOG_DIR: pathlib.Path = pathlib.Path("/var/log/synthex")
LOG_FILE: pathlib.Path = LOG_DIR / "game-optimizer.log"
LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT: int = 3

PRIMARY_PROFILES_PATH: pathlib.Path = pathlib.Path(
    "/home/jewboy420/linux-synthex/gaming/game-profiles.json"
)
FALLBACK_PROFILES_PATH: pathlib.Path = pathlib.Path(
    "~/.config/synthex/game-profiles.json"
).expanduser()

CPU_GOVERNOR_PERF: str = "performance"
CPU_GOVERNOR_DEFAULT: str = "schedutil"

BACKGROUND_SERVICES: List[str] = [
    "synthex-update-manager",
    "baloo_file",
    "tracker-miner-fs-3",
    "tracker-miner-fs",
    "kdeconnectd",
]


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _build_logger() -> logging.Logger:
    """Create and return the application logger."""
    logger = logging.getLogger("synthex-game-optimizer")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Console handler (always present)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Rotating file handler (best-effort — may lack permissions as non-root)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except PermissionError:
        logger.warning(
            "Cannot write to %s — file logging disabled (run as root or adjust permissions).",
            LOG_FILE,
        )

    return logger


log: logging.Logger = _build_logger()


# ---------------------------------------------------------------------------
# Profile loader
# ---------------------------------------------------------------------------

def load_profiles() -> Dict[str, Any]:
    """
    Load game profiles from JSON.

    Tries PRIMARY_PROFILES_PATH first; falls back to FALLBACK_PROFILES_PATH.
    Returns an empty dict if neither exists.

    Expected schema (example)::

        {
          "steam": {
            "exe": "steam",
            "display_name": "Steam Client",
            "network_qos_priority": true,
            "env": {"DXVK_ASYNC": "1"}
          },
          "cs2": {
            "exe": "cs2",
            "display_name": "Counter-Strike 2",
            "network_qos_priority": true,
            "env": {"__GL_THREADED_OPTIMIZATIONS": "1"}
          }
        }
    """
    for path in (PRIMARY_PROFILES_PATH, FALLBACK_PROFILES_PATH):
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    data: Dict[str, Any] = json.load(fh)
                log.info("Loaded %d profile(s) from %s", len(data), path)
                return data
            except (json.JSONDecodeError, OSError) as exc:
                log.warning("Failed to read profiles from %s: %s", path, exc)

    log.warning(
        "No game-profiles.json found at %s or %s — using empty profile set.",
        PRIMARY_PROFILES_PATH,
        FALLBACK_PROFILES_PATH,
    )
    return {}


def save_profiles(profiles: Dict[str, Any]) -> None:
    """Persist profiles to PRIMARY_PROFILES_PATH."""
    PRIMARY_PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PRIMARY_PROFILES_PATH.open("w", encoding="utf-8") as fh:
        json.dump(profiles, fh, indent=2)
    log.info("Saved profiles to %s", PRIMARY_PROFILES_PATH)


# ---------------------------------------------------------------------------
# System helpers
# ---------------------------------------------------------------------------

def _run(
    cmd: List[str],
    *,
    check: bool = False,
    capture: bool = False,
    timeout: int = 10,
) -> Optional[subprocess.CompletedProcess]:  # type: ignore[type-arg]
    """Thin wrapper around subprocess.run with consistent error handling."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            timeout=timeout,
        )
        return result
    except FileNotFoundError:
        log.debug("Command not found: %s", cmd[0])
    except subprocess.CalledProcessError as exc:
        log.debug("Command %s returned %d: %s", cmd, exc.returncode, exc.stderr)
    except subprocess.TimeoutExpired:
        log.warning("Command timed out: %s", cmd)
    return None


def set_cpu_governor(governor: str) -> None:
    """Write *governor* to every online CPU's scaling_governor sysfs node."""
    cpu_root = pathlib.Path("/sys/devices/system/cpu")
    nodes = sorted(cpu_root.glob("cpu*/cpufreq/scaling_governor"))
    if not nodes:
        log.warning("No cpufreq scaling_governor nodes found — skipping CPU governor change.")
        return

    success = 0
    for node in nodes:
        try:
            node.write_text(governor, encoding="ascii")
            success += 1
        except OSError as exc:
            log.debug("Could not write %s to %s: %s", governor, node, exc)

    log.info("Set CPU governor to '%s' on %d/%d CPUs.", governor, success, len(nodes))


def enable_gamemode() -> None:
    """Activate gamemode via `gamemoded -r` if the binary is available."""
    try:
        result = _run(["gamemoded", "-r"], capture=True)
        if result is not None:
            log.info("gamemoded -r: %s", (result.stdout or result.stderr).strip())
        else:
            log.debug("gamemoded not available.")
    except Exception as exc:  # noqa: BLE001
        log.debug("gamemode activation skipped: %s", exc)


def suspend_background_services() -> None:
    """Send SIGSTOP to known background services to free resources for gaming."""
    for svc in BACKGROUND_SERVICES:
        result = _run(["pkill", "-STOP", svc], capture=True)
        if result is not None and result.returncode == 0:
            log.info("Suspended service: %s", svc)
        else:
            log.debug("Service not running or pkill failed: %s", svc)


def resume_background_services() -> None:
    """Send SIGCONT to previously suspended background services."""
    for svc in BACKGROUND_SERVICES:
        result = _run(["pkill", "-CONT", svc], capture=True)
        if result is not None and result.returncode == 0:
            log.info("Resumed service: %s", svc)
        else:
            log.debug("Service not found for SIGCONT: %s", svc)


def _detect_default_interface() -> Optional[str]:
    """Return the name of the default network interface, or None."""
    result = _run(
        ["ip", "route", "show", "default"],
        capture=True,
    )
    if result and result.stdout:
        # e.g. "default via 192.168.1.1 dev enp3s0 proto dhcp ..."
        parts = result.stdout.split()
        try:
            idx = parts.index("dev")
            return parts[idx + 1]
        except (ValueError, IndexError):
            pass
    return None


def apply_network_qos(pid: int, profile: Dict[str, Any]) -> None:
    """
    Prioritise traffic for *pid* using Linux `tc` (traffic control).

    Sets up a prio qdisc on the default interface and uses a u32 filter
    keyed on the socket owner UID (best available approximation — cgroup-
    based filtering requires kernel BPF, which is beyond scope here).
    """
    if not profile.get("network_qos_priority", False):
        log.debug("Network QoS not requested for this profile.")
        return

    iface = _detect_default_interface()
    if not iface:
        log.warning("Cannot determine default network interface — skipping QoS.")
        return

    log.info("Applying network QoS for PID %d on interface %s", pid, iface)

    # Determine UID of the game process
    uid: Optional[str] = None
    try:
        status = pathlib.Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
        for line in status.splitlines():
            if line.startswith("Uid:"):
                uid = line.split()[1]  # effective uid
                break
    except OSError:
        log.warning("Could not read /proc/%d/status for UID — skipping QoS.", pid)
        return

    # Remove any pre-existing root qdisc, then install prio
    _run(["tc", "qdisc", "del", "dev", iface, "root"], capture=True)
    res = _run(
        ["tc", "qdisc", "add", "dev", iface, "root", "handle", "1:", "prio", "bands", "3"],
        capture=True,
    )
    if res is None or res.returncode != 0:
        log.warning("tc qdisc add failed — QoS not applied.")
        return

    if uid:
        # Direct traffic from this user's sockets to the highest-priority band
        _run(
            [
                "tc", "filter", "add", "dev", iface,
                "parent", "1:",
                "protocol", "ip",
                "handle", uid,
                "fw",
                "flowid", "1:1",
            ],
            capture=True,
        )
        log.info("tc filter installed for UID %s → band 1:1 (highest priority).", uid)


def remove_network_qos() -> None:
    """Remove the tc prio qdisc from the default network interface."""
    iface = _detect_default_interface()
    if not iface:
        return
    result = _run(
        ["tc", "qdisc", "del", "dev", iface, "root"],
        capture=True,
    )
    if result and result.returncode == 0:
        log.info("Removed tc qdisc from %s.", iface)
    else:
        log.debug("tc qdisc removal returned non-zero (may already be clean).")


def set_gpu_performance() -> None:
    """
    Enable GPU performance mode.

    Tries NVIDIA via nvidia-settings first; falls back to AMD sysfs.
    """
    # --- NVIDIA ---
    try:
        res = _run(
            ["nvidia-settings", "-a", "GPUPowerMizerMode=1"],
            capture=True,
        )
        if res is not None and res.returncode == 0:
            log.info("NVIDIA GPU: set GPUPowerMizerMode=1 (prefer maximum performance).")
            return
    except Exception as exc:  # noqa: BLE001
        log.debug("nvidia-settings not available: %s", exc)

    # --- AMD ---
    try:
        amd_nodes = sorted(
            pathlib.Path("/sys/class/drm").glob("card*/device/power_dyn_sw_status")
        )
        if amd_nodes:
            for node in amd_nodes:
                try:
                    node.write_text("performance\n", encoding="ascii")
                    log.info("AMD GPU: wrote 'performance' to %s", node)
                except OSError as exc:
                    log.debug("Could not write to AMD power node %s: %s", node, exc)
        else:
            log.debug("No AMD power_dyn_sw_status nodes found.")
    except Exception as exc:  # noqa: BLE001
        log.debug("AMD GPU performance mode skipped: %s", exc)


def restore_gpu_auto() -> None:
    """Restore GPU to automatic / power-saving mode."""
    # --- NVIDIA ---
    try:
        res = _run(
            ["nvidia-settings", "-a", "GPUPowerMizerMode=0"],
            capture=True,
        )
        if res is not None and res.returncode == 0:
            log.info("NVIDIA GPU: restored GPUPowerMizerMode=0 (auto).")
            return
    except Exception as exc:  # noqa: BLE001
        log.debug("nvidia-settings restore skipped: %s", exc)

    # --- AMD ---
    try:
        amd_nodes = sorted(
            pathlib.Path("/sys/class/drm").glob("card*/device/power_dyn_sw_status")
        )
        for node in amd_nodes:
            try:
                node.write_text("auto\n", encoding="ascii")
                log.info("AMD GPU: restored 'auto' on %s", node)
            except OSError as exc:
                log.debug("Could not restore AMD node %s: %s", node, exc)
    except Exception as exc:  # noqa: BLE001
        log.debug("AMD GPU restore skipped: %s", exc)


def log_env_vars(pid: int, profile: Dict[str, Any]) -> None:
    """
    Document the environment variables that the profile requests for the game.

    NOTE: It is not possible to inject environment variables into a running
    process on Linux without ptrace trickery that can cause instability.
    This function logs what *would* be applied so the user knows what to
    set in the launch wrapper / .desktop file / Steam launch options.
    """
    env_vars: Dict[str, str] = profile.get("env", {})
    if not env_vars:
        return

    log.info(
        "PID %d — profile requests the following env vars (cannot inject into running "
        "process; set these in your launcher / Steam launch options):",
        pid,
    )
    for key, value in env_vars.items():
        log.info("  %s=%s", key, value)


def notify(title: str, body: str) -> None:
    """Send a desktop notification via notify-send (best-effort)."""
    try:
        # notify-send needs DBUS_SESSION_BUS_ADDRESS; try to pass it through.
        env = os.environ.copy()
        _run(["notify-send", "--urgency=normal", title, body], capture=True)
        log.debug("Desktop notification sent: %s — %s", title, body)
    except Exception as exc:  # noqa: BLE001
        log.debug("notify-send unavailable: %s", exc)


# ---------------------------------------------------------------------------
# Process scanner
# ---------------------------------------------------------------------------

def scan_running_executables() -> Dict[str, int]:
    """
    Return a mapping of {executable_basename: pid} for all running processes.

    Reads /proc/<pid>/comm for each numeric /proc entry — no external tools
    required and avoids privilege escalation.
    """
    running: Dict[str, int] = {}
    proc_root = pathlib.Path("/proc")
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        comm_file = entry / "comm"
        try:
            comm = comm_file.read_text(encoding="utf-8").strip()
            running[comm] = int(entry.name)
        except OSError:
            pass
        # Also check the full exe symlink basename for cases where comm is truncated (15 chars)
        exe_link = entry / "exe"
        try:
            exe_path = exe_link.resolve()
            exe_name = exe_path.name
            if exe_name and exe_name not in running:
                running[exe_name] = int(entry.name)
        except OSError:
            pass
    return running


# ---------------------------------------------------------------------------
# Core optimizer logic
# ---------------------------------------------------------------------------

class GameOptimizer:
    """
    Continuously monitors running processes and applies/reverts performance
    tuning when known game executables start or stop.

    Thread-safe via ``_lock``.
    """

    def __init__(self) -> None:
        self._profiles: Dict[str, Any] = load_profiles()
        # Maps profile_key → pid of currently active game instance
        self._active_games: Dict[str, int] = {}
        self._lock: threading.Lock = threading.Lock()
        self._stop_event: threading.Event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reload_profiles(self) -> None:
        with self._lock:
            self._profiles = load_profiles()

    def start(self) -> None:
        """Write PID file and enter the main polling loop (blocking)."""
        self._write_pid()
        log.info("SynthOS Game Optimizer started (PID %d). Polling every %.1fs.", os.getpid(), POLL_INTERVAL)
        try:
            self._main_loop()
        finally:
            self._cleanup()
            self._remove_pid()

    def stop(self) -> None:
        """Signal the main loop to terminate cleanly."""
        self._stop_event.set()

    def active_games(self) -> Dict[str, int]:
        """Return a snapshot of currently active game sessions {key: pid}."""
        with self._lock:
            return dict(self._active_games)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _main_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                running = scan_running_executables()
                self._reconcile(running)
            except Exception as exc:  # noqa: BLE001
                log.exception("Unexpected error in main loop: %s", exc)
            self._stop_event.wait(timeout=POLL_INTERVAL)

    def _reconcile(self, running: Dict[str, int]) -> None:
        """
        Compare currently running executables against known profiles.

        - Newly detected game → call ``_on_game_launch``.
        - Previously tracked game that is no longer running → call ``_on_game_exit``.
        """
        with self._lock:
            profiles_snapshot = dict(self._profiles)
            active_snapshot = dict(self._active_games)

        # Detect launches
        for key, profile in profiles_snapshot.items():
            exe: str = profile.get("exe", "")
            if not exe:
                continue
            if key not in active_snapshot and exe in running:
                pid = running[exe]
                with self._lock:
                    self._active_games[key] = pid
                self._on_game_launch(key, pid, profile)

        # Detect exits
        for key, pid in list(active_snapshot.items()):
            profile = profiles_snapshot.get(key, {})
            exe: str = profile.get("exe", "")
            if exe not in running:
                with self._lock:
                    self._active_games.pop(key, None)
                self._on_game_exit(key, pid, profile)

    # ------------------------------------------------------------------
    # Launch / exit handlers
    # ------------------------------------------------------------------

    def _on_game_launch(self, key: str, pid: int, profile: Dict[str, Any]) -> None:
        display_name: str = profile.get("display_name", key)
        log.info("=== Game LAUNCH detected: %s (PID %d) ===", display_name, pid)

        set_cpu_governor(CPU_GOVERNOR_PERF)
        enable_gamemode()
        suspend_background_services()
        apply_network_qos(pid, profile)
        set_gpu_performance()
        log_env_vars(pid, profile)
        notify("🎮 Game Mode ON", f"Optimizing for {display_name}")

        log.info("All optimizations applied for %s.", display_name)

    def _on_game_exit(self, key: str, pid: int, profile: Dict[str, Any]) -> None:
        display_name: str = profile.get("display_name", key)
        log.info("=== Game EXIT detected: %s (was PID %d) ===", display_name, pid)

        set_cpu_governor(CPU_GOVERNOR_DEFAULT)
        resume_background_services()
        remove_network_qos()
        restore_gpu_auto()
        notify("🎮 Game Mode OFF", "Restored normal performance")

        log.info("System restored to normal performance after %s.", display_name)

    # ------------------------------------------------------------------
    # Cleanup (called when stop_event fires or signal received)
    # ------------------------------------------------------------------

    def _cleanup(self) -> None:
        """Restore system state for any games that were active at shutdown."""
        with self._lock:
            active_snapshot = dict(self._active_games)
            profiles_snapshot = dict(self._profiles)

        if active_snapshot:
            log.info("Shutting down with %d active game(s) — restoring system.", len(active_snapshot))
            for key, pid in active_snapshot.items():
                profile = profiles_snapshot.get(key, {})
                self._on_game_exit(key, pid, profile)
        else:
            # Restore unconditionally to be safe
            set_cpu_governor(CPU_GOVERNOR_DEFAULT)
            resume_background_services()
            remove_network_qos()
            restore_gpu_auto()

    # ------------------------------------------------------------------
    # PID file management
    # ------------------------------------------------------------------

    @staticmethod
    def _write_pid() -> None:
        try:
            PID_FILE.parent.mkdir(parents=True, exist_ok=True)
            PID_FILE.write_text(str(os.getpid()), encoding="ascii")
            log.debug("PID file written: %s", PID_FILE)
        except OSError as exc:
            log.warning("Could not write PID file %s: %s", PID_FILE, exc)

    @staticmethod
    def _remove_pid() -> None:
        try:
            PID_FILE.unlink(missing_ok=True)
        except OSError as exc:
            log.debug("Could not remove PID file: %s", exc)


# ---------------------------------------------------------------------------
# Signal handling
# ---------------------------------------------------------------------------

_optimizer_instance: Optional[GameOptimizer] = None


def _handle_sigterm(signum: int, frame: object) -> None:  # noqa: ARG001
    log.info("Received SIGTERM — shutting down.")
    if _optimizer_instance is not None:
        _optimizer_instance.stop()


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _read_pid() -> Optional[int]:
    """Read and return the PID from the PID file, or None if absent/stale."""
    try:
        raw = PID_FILE.read_text(encoding="ascii").strip()
        pid = int(raw)
        # Verify the process actually exists
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def cmd_start(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Start the optimizer daemon in the foreground (systemd runs it this way)."""
    global _optimizer_instance  # noqa: PLW0603

    existing_pid = _read_pid()
    if existing_pid is not None:
        log.error("Optimizer is already running (PID %d).", existing_pid)
        return 1

    optimizer = GameOptimizer()
    _optimizer_instance = optimizer

    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        optimizer.start()
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received — shutting down.")
        optimizer.stop()

    return 0


def cmd_stop(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Send SIGTERM to the running optimizer daemon."""
    pid = _read_pid()
    if pid is None:
        print("SynthOS Game Optimizer is not running.")
        return 1
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to PID {pid}.")
        return 0
    except OSError as exc:
        print(f"Failed to send SIGTERM to PID {pid}: {exc}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Print whether the optimizer daemon is running."""
    pid = _read_pid()
    if pid is not None:
        print(f"SynthOS Game Optimizer is RUNNING (PID {pid}).")
        return 0
    else:
        print("SynthOS Game Optimizer is STOPPED.")
        return 1


def cmd_list_games(args: argparse.Namespace) -> int:  # noqa: ARG001
    """List all games in the profile database."""
    profiles = load_profiles()
    if not profiles:
        print("No games in profile database.")
        return 0

    print(f"{'KEY':<24} {'DISPLAY NAME':<36} {'EXE':<28} QOS  ENV VARS")
    print("-" * 100)
    for key, profile in sorted(profiles.items()):
        display_name = profile.get("display_name", key)
        exe = profile.get("exe", "(none)")
        qos = "yes" if profile.get("network_qos_priority") else "no "
        env_count = len(profile.get("env", {}))
        print(f"{key:<24} {display_name:<36} {exe:<28} {qos}  {env_count}")

    print(f"\nTotal: {len(profiles)} game(s).")
    return 0


def cmd_add_game(args: argparse.Namespace) -> int:
    """Add a new game profile to the database."""
    profiles = load_profiles()
    # Derive a stable key from the name
    key: str = hashlib.md5(args.name.encode()).hexdigest()[:8] + "_" + args.name.lower().replace(" ", "_")
    if key in profiles:
        print(f"A profile with key '{key}' already exists. Edit game-profiles.json directly to modify it.")
        return 1

    profiles[key] = {
        "exe": args.exe,
        "display_name": args.name,
        "network_qos_priority": True,
        "env": {},
    }
    save_profiles(profiles)
    print(f"Added game '{args.name}' (exe: {args.exe}) with key '{key}'.")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="synthex-game-optimizer",
        description="SynthOS Game Optimizer — per-game automatic performance tuning daemon.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  synthex-game-optimizer start\n"
            "  synthex-game-optimizer stop\n"
            "  synthex-game-optimizer status\n"
            "  synthex-game-optimizer list-games\n"
            "  synthex-game-optimizer add-game 'Counter-Strike 2' cs2\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    sub.add_parser("start", help="Start the optimizer daemon (foreground; managed by systemd).")
    sub.add_parser("stop", help="Stop the running optimizer daemon.")
    sub.add_parser("status", help="Show whether the optimizer daemon is running.")
    sub.add_parser("list-games", help="List all games in the profile database.")

    add_game = sub.add_parser("add-game", help="Add a new game to the profile database.")
    add_game.add_argument("name", metavar="NAME", help="Human-readable game name.")
    add_game.add_argument("exe", metavar="EXE", help="Executable basename (e.g. cs2).")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    dispatch: Dict[str, typing.Callable[[argparse.Namespace], int]] = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "list-games": cmd_list_games,
        "add-game": cmd_add_game,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
