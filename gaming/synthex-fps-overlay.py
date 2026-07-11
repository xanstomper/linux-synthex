#!/usr/bin/env python3
"""
synthex-fps-overlay.py — SynthOS Brain OS GPU/Performance Overlay Daemon
Renders a transparent KDE Plasma overlay widget with live GPU, CPU, RAM,
FPS, temperature, and network metrics. Posts snapshots to the Brain daemon
and exposes a D-Bus service for external control.

Config: ~/.config/synthex/fps-overlay.toml
D-Bus:  org.synthex.FPSOverlay
Brain:  POST http://localhost:7700/gaming-metrics  (every 10 s)
"""

from __future__ import annotations

import asyncio
import ctypes
import glob
import json
import mmap
import os
import struct
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Optional GUI imports — fall back gracefully to stdout/MangoHud-DBUS mode
# ---------------------------------------------------------------------------
try:
    from PyQt6.QtWidgets import (
        QApplication, QLabel, QVBoxLayout, QWidget,
    )
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QColor, QPalette, QFont
    _QT_AVAILABLE = True
    _QT_VERSION = 6
except ImportError:
    try:
        from PyQt5.QtWidgets import (  # type: ignore[assignment]
            QApplication, QLabel, QVBoxLayout, QWidget,
        )
        from PyQt5.QtCore import Qt, QTimer, pyqtSignal  # type: ignore[assignment]
        from PyQt5.QtGui import QColor, QPalette, QFont  # type: ignore[assignment]
        _QT_AVAILABLE = True
        _QT_VERSION = 5
    except ImportError:
        _QT_AVAILABLE = False
        _QT_VERSION = 0

try:
    import dbus                          # type: ignore[import]
    import dbus.service                  # type: ignore[import]
    import dbus.mainloop.glib            # type: ignore[import]
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

try:
    import aiohttp                       # type: ignore[import]
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _AIOHTTP_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict = {
    "position": {"x": 16, "y": 16},
    "metrics": {
        "fps": True,
        "gpu": True,
        "cpu": True,
        "ram": True,
        "temp": True,
        "net": True,
        "vram": True,
    },
    "update_interval_ms": 500,
    "brain_post_interval_s": 10,
    "color_theme": {
        "background": "#cc000000",
        "text": "#e0e0e0",
        "highlight_warn": "#ffb347",
        "highlight_crit": "#ff4c4c",
        "highlight_ok": "#a8ff78",
    },
    "font_size": 12,
    "opacity": 0.82,
    "stdout_mode": False,   # force stdout/MangoHud-DBUS output even if Qt available
}

CONFIG_PATH = Path.home() / ".config" / "synthex" / "fps-overlay.toml"


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "rb") as fh:
            user = tomllib.load(fh)
        # Shallow-merge top-level sections
        for key, val in user.items():
            if isinstance(val, dict) and key in cfg:
                cfg[key] = {**cfg[key], **val}
            else:
                cfg[key] = val
    return cfg


# ---------------------------------------------------------------------------
# Hardware readers
# ---------------------------------------------------------------------------

@dataclass
class PerfSnapshot:
    ts: float = field(default_factory=time.time)
    fps: float = 0.0
    gpu_busy: float = 0.0       # 0-100 %
    gpu_mem_used_mb: float = 0.0
    gpu_mem_total_mb: float = 0.0
    cpu_pct: float = 0.0
    ram_used_mb: float = 0.0
    ram_total_mb: float = 0.0
    temp_gpu_c: float = 0.0
    temp_cpu_c: float = 0.0
    net_rx_kbps: float = 0.0
    net_tx_kbps: float = 0.0
    gpu_vendor: str = "unknown"  # "amd" | "nvidia" | "unknown"


class GPUReader:
    """Auto-detects AMD (sysfs) or NVIDIA (nvidia-smi) and reads stats."""

    def __init__(self) -> None:
        self.vendor = self._detect_vendor()
        self._nv_fields = "utilization.gpu,memory.used,memory.total"

    def _detect_vendor(self) -> str:
        # NVIDIA: nvidia-smi must be present
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL, timeout=2,
            )
            if out.strip():
                return "nvidia"
        except Exception:
            pass
        # AMD: drm sysfs path
        if glob.glob("/sys/class/drm/card*/device/gpu_busy_percent"):
            return "amd"
        return "unknown"

    def read(self) -> tuple[float, float, float]:
        """Returns (busy_pct, vram_used_mb, vram_total_mb)."""
        if self.vendor == "nvidia":
            return self._read_nvidia()
        if self.vendor == "amd":
            return self._read_amd()
        return 0.0, 0.0, 0.0

    def _read_nvidia(self) -> tuple[float, float, float]:
        try:
            out = subprocess.check_output(
                [
                    "nvidia-smi",
                    f"--query-gpu={self._nv_fields}",
                    "--format=csv,noheader,nounits",
                ],
                stderr=subprocess.DEVNULL, timeout=2,
            ).decode().strip()
            parts = [p.strip() for p in out.split(",")]
            busy = float(parts[0])
            used = float(parts[1])
            total = float(parts[2])
            return busy, used, total
        except Exception:
            return 0.0, 0.0, 0.0

    def _read_amd(self) -> tuple[float, float, float]:
        busy = 0.0
        used_mb = 0.0
        total_mb = 0.0
        paths = glob.glob("/sys/class/drm/card*/device/gpu_busy_percent")
        if paths:
            try:
                busy = float(Path(paths[0]).read_text().strip())
            except Exception:
                pass
        # VRAM via amdgpu sysfs
        vram_used_paths = glob.glob("/sys/class/drm/card*/device/mem_info_vram_used")
        vram_total_paths = glob.glob("/sys/class/drm/card*/device/mem_info_vram_total")
        if vram_used_paths:
            try:
                used_mb = int(Path(vram_used_paths[0]).read_text().strip()) / (1024 ** 2)
            except Exception:
                pass
        if vram_total_paths:
            try:
                total_mb = int(Path(vram_total_paths[0]).read_text().strip()) / (1024 ** 2)
            except Exception:
                pass
        return busy, used_mb, total_mb


class CPUReader:
    """Reads CPU utilisation from /proc/stat (delta between two calls)."""

    def __init__(self) -> None:
        self._prev: tuple[int, int] | None = None

    def read(self) -> float:
        try:
            line = Path("/proc/stat").read_text().splitlines()[0]
            vals = list(map(int, line.split()[1:]))
            idle = vals[3]
            total = sum(vals)
            if self._prev is None:
                self._prev = (idle, total)
                return 0.0
            p_idle, p_total = self._prev
            self._prev = (idle, total)
            delta_total = total - p_total
            delta_idle = idle - p_idle
            if delta_total == 0:
                return 0.0
            return 100.0 * (1.0 - delta_idle / delta_total)
        except Exception:
            return 0.0


class RAMReader:
    """Reads RAM usage from /proc/meminfo."""

    def read(self) -> tuple[float, float]:
        """Returns (used_mb, total_mb)."""
        try:
            info: dict[str, int] = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(":")] = int(parts[1])
            total_kb = info.get("MemTotal", 0)
            avail_kb = info.get("MemAvailable", info.get("MemFree", 0))
            used_kb = total_kb - avail_kb
            return used_kb / 1024, total_kb / 1024
        except Exception:
            return 0.0, 0.0


class TempReader:
    """Reads temperatures from hwmon sysfs entries."""

    def __init__(self) -> None:
        self._gpu_path: Optional[Path] = None
        self._cpu_path: Optional[Path] = None
        self._probe()

    def _probe(self) -> None:
        for hwmon in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
            name_file = Path(hwmon) / "name"
            if not name_file.exists():
                continue
            name = name_file.read_text().strip().lower()
            # GPU candidates: amdgpu, nouveau, nvidia (via hwmon)
            if any(k in name for k in ("amdgpu", "nouveau", "nvidia")):
                candidates = sorted(glob.glob(f"{hwmon}/temp*_input"))
                if candidates and self._gpu_path is None:
                    self._gpu_path = Path(candidates[0])
            # CPU candidates: coretemp, k10temp, zenpower
            if any(k in name for k in ("coretemp", "k10temp", "zenpower")):
                candidates = sorted(glob.glob(f"{hwmon}/temp*_input"))
                if candidates and self._cpu_path is None:
                    self._cpu_path = Path(candidates[0])

    def read(self) -> tuple[float, float]:
        """Returns (gpu_c, cpu_c)."""
        gpu_c = self._read_path(self._gpu_path)
        cpu_c = self._read_path(self._cpu_path)
        return gpu_c, cpu_c

    @staticmethod
    def _read_path(p: Optional[Path]) -> float:
        if p is None or not p.exists():
            return 0.0
        try:
            return int(p.read_text().strip()) / 1000.0
        except Exception:
            return 0.0


class NetReader:
    """Reads network throughput from /proc/net/dev."""

    def __init__(self, iface: Optional[str] = None) -> None:
        self._iface = iface
        self._prev: tuple[int, int, float] | None = None  # rx, tx, ts

    def _best_iface(self) -> Optional[str]:
        """Pick the first non-loopback interface with traffic."""
        try:
            lines = Path("/proc/net/dev").read_text().splitlines()[2:]
            for line in lines:
                parts = line.split()
                iface = parts[0].rstrip(":")
                if iface == "lo":
                    continue
                return iface
        except Exception:
            pass
        return None

    def read(self) -> tuple[float, float]:
        """Returns (rx_kbps, tx_kbps)."""
        iface = self._iface or self._best_iface()
        if not iface:
            return 0.0, 0.0
        try:
            lines = Path("/proc/net/dev").read_text().splitlines()[2:]
            for line in lines:
                parts = line.split()
                if parts[0].rstrip(":") != iface:
                    continue
                rx = int(parts[1])
                tx = int(parts[9])
                now = time.monotonic()
                if self._prev is None:
                    self._prev = (rx, tx, now)
                    return 0.0, 0.0
                p_rx, p_tx, p_ts = self._prev
                dt = now - p_ts or 1.0
                self._prev = (rx, tx, now)
                return (rx - p_rx) / dt / 1024, (tx - p_tx) / dt / 1024
        except Exception:
            pass
        return 0.0, 0.0


class FPSReader:
    """
    Reads FPS from MangoHud shared memory if available, otherwise
    estimates via frame-present timestamps supplied by the caller.
    """

    SHM_PATH = "/dev/shm/MangoHudExchangeInfo"
    # MangoHud exchange struct: first 8 bytes = version u64,
    # next 8 = frametime_ns u64.  Layout may vary; treat as best-effort.
    _STRUCT = struct.Struct("<QQ")

    def __init__(self) -> None:
        self._shm_fd: Optional[int] = None
        self._shm_mm: Optional[mmap.mmap] = None
        self._frame_ts: list[float] = []
        self._open_shm()

    def _open_shm(self) -> None:
        try:
            fd = os.open(self.SHM_PATH, os.O_RDONLY)
            self._shm_fd = fd
            self._shm_mm = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        except Exception:
            self._shm_fd = None
            self._shm_mm = None

    def push_frame(self) -> None:
        """Call once per rendered frame for fallback FPS estimation."""
        now = time.monotonic()
        self._frame_ts.append(now)
        cutoff = now - 1.0
        self._frame_ts = [t for t in self._frame_ts if t >= cutoff]

    def read(self) -> float:
        if self._shm_mm:
            try:
                self._shm_mm.seek(0)
                raw = self._shm_mm.read(self._STRUCT.size)
                _, frametime_ns = self._STRUCT.unpack_from(raw)
                if frametime_ns > 0:
                    return 1e9 / frametime_ns
            except Exception:
                pass
        # Fallback: count frames in last second
        return float(len(self._frame_ts))


# ---------------------------------------------------------------------------
# D-Bus service
# ---------------------------------------------------------------------------

if _DBUS_AVAILABLE:
    class FPSOverlayDBus(dbus.service.Object):
        IFACE = "org.synthex.FPSOverlay"

        def __init__(self, overlay: "OverlayDaemon") -> None:
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()
            bus_name = dbus.service.BusName("org.synthex.FPSOverlay", bus=bus)
            super().__init__(bus_name, "/org/synthex/FPSOverlay")
            self._overlay = overlay

        @dbus.service.method(IFACE)
        def Show(self) -> None:  # noqa: N802
            self._overlay.show_overlay()

        @dbus.service.method(IFACE)
        def Hide(self) -> None:  # noqa: N802
            self._overlay.hide_overlay()

        @dbus.service.method(IFACE, in_signature="ii")
        def SetPosition(self, x: int, y: int) -> None:  # noqa: N802
            self._overlay.set_position(x, y)

        @dbus.service.method(IFACE, out_signature="d")
        def CurrentFPS(self) -> float:  # noqa: N802
            return self._overlay.last_snapshot.fps


# ---------------------------------------------------------------------------
# Qt overlay widget
# ---------------------------------------------------------------------------

if _QT_AVAILABLE:
    class OverlayWidget(QWidget):
        def __init__(self, cfg: dict) -> None:
            super().__init__()
            theme = cfg["color_theme"]
            self._warn_color = theme["highlight_warn"]
            self._crit_color = theme["highlight_crit"]
            self._ok_color = theme["highlight_ok"]
            self._text_color = theme["text"]
            self._metrics_cfg = cfg["metrics"]

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            self.setWindowOpacity(cfg.get("opacity", 0.82))

            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 8, 10, 8)
            layout.setSpacing(2)

            self._label = QLabel("Initializing…")
            font = QFont("Monospace", cfg.get("font_size", 12))
            font.setStyleHint(QFont.StyleHint.Monospace)
            self._label.setFont(font)
            self._label.setStyleSheet(f"color: {self._text_color};")
            layout.addWidget(self._label)

            self.setStyleSheet(
                f"background-color: {theme['background']}; border-radius: 8px;"
            )
            self.adjustSize()

        def update_snapshot(self, snap: PerfSnapshot, metrics: dict) -> None:
            lines: list[str] = []

            def color(val: float, warn: float, crit: float) -> str:
                if val >= crit:
                    return self._crit_color
                if val >= warn:
                    return self._warn_color
                return self._ok_color

            def row(label: str, val: str, c: str) -> str:
                return (
                    f'<span style="color:{self._text_color}">{label} </span>'
                    f'<span style="color:{c}">{val}</span>'
                )

            if metrics.get("fps"):
                c = color(0, 0, 0)  # FPS: higher is better, colour by threshold
                c = self._crit_color if snap.fps < 30 else (
                    self._warn_color if snap.fps < 60 else self._ok_color
                )
                lines.append(row("FPS", f"{snap.fps:>6.1f}", c))

            if metrics.get("gpu"):
                c = color(snap.gpu_busy, 80, 95)
                lines.append(row("GPU", f"{snap.gpu_busy:>5.1f}%", c))

            if metrics.get("vram") and snap.gpu_mem_total_mb > 0:
                pct = 100 * snap.gpu_mem_used_mb / snap.gpu_mem_total_mb
                c = color(pct, 80, 95)
                lines.append(row(
                    "VRAM",
                    f"{snap.gpu_mem_used_mb:>6.0f}/{snap.gpu_mem_total_mb:.0f} MB",
                    c,
                ))

            if metrics.get("cpu"):
                c = color(snap.cpu_pct, 75, 92)
                lines.append(row("CPU", f"{snap.cpu_pct:>5.1f}%", c))

            if metrics.get("ram") and snap.ram_total_mb > 0:
                pct = 100 * snap.ram_used_mb / snap.ram_total_mb
                c = color(pct, 75, 90)
                lines.append(row(
                    "RAM",
                    f"{snap.ram_used_mb:>6.0f}/{snap.ram_total_mb:.0f} MB",
                    c,
                ))

            if metrics.get("temp"):
                if snap.temp_gpu_c > 0:
                    c = color(snap.temp_gpu_c, 80, 95)
                    lines.append(row("GPU°C", f"{snap.temp_gpu_c:>5.1f}", c))
                if snap.temp_cpu_c > 0:
                    c = color(snap.temp_cpu_c, 85, 100)
                    lines.append(row("CPU°C", f"{snap.temp_cpu_c:>5.1f}", c))

            if metrics.get("net"):
                lines.append(row(
                    "RX",
                    f"{snap.net_rx_kbps:>7.1f} KB/s",
                    self._text_color,
                ))
                lines.append(row(
                    "TX",
                    f"{snap.net_tx_kbps:>7.1f} KB/s",
                    self._text_color,
                ))

            self._label.setText(
                "<br>".join(lines) if lines else "No metrics enabled"
            )
            self.adjustSize()


# ---------------------------------------------------------------------------
# Main daemon
# ---------------------------------------------------------------------------

class OverlayDaemon:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.last_snapshot = PerfSnapshot()
        self._visible = True

        self._gpu = GPUReader()
        self._cpu = CPUReader()
        self._ram = RAMReader()
        self._temp = TempReader()
        self._net = NetReader()
        self._fps = FPSReader()

        self._widget: Optional["OverlayWidget"] = None
        self._qt_app: Optional["QApplication"] = None
        self._qt_timer: Optional["QTimer"] = None
        self._last_brain_post = 0.0
        self._stdout_mode: bool = (
            cfg.get("stdout_mode", False) or not _QT_AVAILABLE
        )

    # ------------------------------------------------------------------
    # D-Bus control interface
    # ------------------------------------------------------------------

    def show_overlay(self) -> None:
        self._visible = True
        if self._widget:
            self._widget.show()

    def hide_overlay(self) -> None:
        self._visible = False
        if self._widget:
            self._widget.hide()

    def set_position(self, x: int, y: int) -> None:
        self.cfg["position"] = {"x": x, "y": y}
        if self._widget:
            self._widget.move(x, y)

    # ------------------------------------------------------------------
    # Metrics collection
    # ------------------------------------------------------------------

    def _collect(self) -> PerfSnapshot:
        gpu_busy, vram_used, vram_total = self._gpu.read()
        cpu_pct = self._cpu.read()
        ram_used, ram_total = self._ram.read()
        temp_gpu, temp_cpu = self._temp.read()
        rx_kbps, tx_kbps = self._net.read()
        fps = self._fps.read()

        snap = PerfSnapshot(
            ts=time.time(),
            fps=fps,
            gpu_busy=gpu_busy,
            gpu_mem_used_mb=vram_used,
            gpu_mem_total_mb=vram_total,
            cpu_pct=cpu_pct,
            ram_used_mb=ram_used,
            ram_total_mb=ram_total,
            temp_gpu_c=temp_gpu,
            temp_cpu_c=temp_cpu,
            net_rx_kbps=rx_kbps,
            net_tx_kbps=tx_kbps,
            gpu_vendor=self._gpu.vendor,
        )
        self.last_snapshot = snap
        return snap

    # ------------------------------------------------------------------
    # Brain OS integration
    # ------------------------------------------------------------------

    async def _post_to_brain(self, snap: PerfSnapshot) -> None:
        if not _AIOHTTP_AVAILABLE:
            return
        payload = {
            "ts": snap.ts,
            "fps": snap.fps,
            "gpu_busy_pct": snap.gpu_busy,
            "vram_used_mb": snap.gpu_mem_used_mb,
            "vram_total_mb": snap.gpu_mem_total_mb,
            "cpu_pct": snap.cpu_pct,
            "ram_used_mb": snap.ram_used_mb,
            "ram_total_mb": snap.ram_total_mb,
            "temp_gpu_c": snap.temp_gpu_c,
            "temp_cpu_c": snap.temp_cpu_c,
            "net_rx_kbps": snap.net_rx_kbps,
            "net_tx_kbps": snap.net_tx_kbps,
            "gpu_vendor": snap.gpu_vendor,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:7700/gaming-metrics",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3),
                ) as resp:
                    if resp.status == 200:
                        body = await resp.json()
                        advice = body.get("advice")
                        if advice:
                            print(f"[Brain] {advice}", flush=True)
        except Exception:
            pass  # Brain daemon may not be running; fail silently

    # ------------------------------------------------------------------
    # Stdout / MangoHud-DBUS output mode
    # ------------------------------------------------------------------

    def _emit_stdout(self, snap: PerfSnapshot) -> None:
        metrics = self.cfg["metrics"]
        parts: list[str] = []
        if metrics.get("fps"):
            parts.append(f"fps={snap.fps:.1f}")
        if metrics.get("gpu"):
            parts.append(f"gpu={snap.gpu_busy:.1f}")
        if metrics.get("cpu"):
            parts.append(f"cpu={snap.cpu_pct:.1f}")
        if metrics.get("ram"):
            parts.append(f"ram_used={snap.ram_used_mb:.0f}")
        if metrics.get("temp"):
            parts.append(f"temp_gpu={snap.temp_gpu_c:.1f}")
            parts.append(f"temp_cpu={snap.temp_cpu_c:.1f}")
        if metrics.get("net"):
            parts.append(f"rx_kbps={snap.net_rx_kbps:.1f}")
            parts.append(f"tx_kbps={snap.net_tx_kbps:.1f}")
        print(" ".join(parts), flush=True)

    # ------------------------------------------------------------------
    # Qt event-loop tick
    # ------------------------------------------------------------------

    def _qt_tick(self) -> None:
        snap = self._collect()
        if self._widget and self._visible:
            self._widget.update_snapshot(snap, self.cfg["metrics"])
        if self._stdout_mode:
            self._emit_stdout(snap)
        now = time.monotonic()
        if now - self._last_brain_post >= self.cfg.get("brain_post_interval_s", 10):
            self._last_brain_post = now
            asyncio.ensure_future(self._post_to_brain(snap))

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    def run_qt(self) -> None:
        import sys
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setQuitOnLastWindowClosed(False)

        if not self._stdout_mode:
            self._widget = OverlayWidget(self.cfg)
            pos = self.cfg.get("position", {"x": 16, "y": 16})
            self._widget.move(pos.get("x", 16), pos.get("y", 16))
            self._widget.show()

        if _DBUS_AVAILABLE:
            try:
                FPSOverlayDBus(self)
            except Exception as exc:
                print(f"[synthex-fps-overlay] D-Bus registration failed: {exc}",
                      file=sys.stderr)

        interval_ms = self.cfg.get("update_interval_ms", 500)
        self._qt_timer = QTimer()
        self._qt_timer.timeout.connect(self._qt_tick)
        self._qt_timer.start(interval_ms)

        self._qt_app.exec()

    async def run_async(self) -> None:
        interval = self.cfg.get("update_interval_ms", 500) / 1000.0
        brain_interval = self.cfg.get("brain_post_interval_s", 10)
        last_brain = 0.0
        while True:
            snap = self._collect()
            self._emit_stdout(snap)
            now = time.monotonic()
            if now - last_brain >= brain_interval:
                last_brain = now
                await self._post_to_brain(snap)
            await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    cfg = load_config()

    # Ensure config dir exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    force_stdout = "--stdout" in sys.argv or cfg.get("stdout_mode", False)

    if _QT_AVAILABLE and not force_stdout:
        daemon = OverlayDaemon(cfg)
        daemon.run_qt()
    else:
        cfg["stdout_mode"] = True
        daemon = OverlayDaemon(cfg)
        asyncio.run(daemon.run_async())


if __name__ == "__main__":
    main()
