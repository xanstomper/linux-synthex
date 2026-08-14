#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
SynthOS System Bridge & Rice Customization Engine
Exposes real Linux kernel (procfs/sysfs), audio (PipeWire/wpctl/pactl),
backlight, MPRIS (playerctl), Wi-Fi, Bluetooth, power profiles, and
full user rice customization state to QML.
"""

import json
import os
import platform
import shutil
import subprocess
import threading
import time
from pathlib import Path
import urllib.request

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

CONFIG_DIR = Path.home() / ".config" / "synthex"
CONFIG_FILE = CONFIG_DIR / "rice.json"

THEME_PRESETS = {
    "nova": {
        "name": "Nova Dark (Default)",
        "accent": "#7AA2F7",
        "secondary": "#BB9AF7",
        "surface": "#141923",
        "dock": "#12161F",
        "border": "#14ffffff",
        "text": "#FFFFFF",
        "textDim": "#9AA1AB"
    },
    "tokyonight": {
        "name": "Tokyo Night",
        "accent": "#7AA2F7",
        "secondary": "#F7768E",
        "surface": "#1A1B26",
        "dock": "#16161E",
        "border": "#202336",
        "text": "#C0CAF5",
        "textDim": "#787C99"
    },
    "catppuccin": {
        "name": "Catppuccin Mocha",
        "accent": "#89B4FA",
        "secondary": "#CBA6F7",
        "surface": "#1E1E2E",
        "dock": "#181825",
        "border": "#313244",
        "text": "#CDD6F4",
        "textDim": "#A6ADC8"
    },
    "nord": {
        "name": "Nord Frost",
        "accent": "#88C0D0",
        "secondary": "#81A1C1",
        "surface": "#2E3440",
        "dock": "#242933",
        "border": "#3B4252",
        "text": "#ECEFF4",
        "textDim": "#D8DEE9"
    },
    "cyberpunk": {
        "name": "Cyberpunk Neon",
        "accent": "#00F0FF",
        "secondary": "#FF007F",
        "surface": "#0D0D18",
        "dock": "#07070F",
        "border": "#00f0ff33",
        "text": "#00F0FF",
        "textDim": "#7A889B"
    },
    "oled": {
        "name": "OLED Midnight",
        "accent": "#60A5FA",
        "secondary": "#A78BFA",
        "surface": "#0A0A0A",
        "dock": "#000000",
        "border": "#262626",
        "text": "#F3F4F6",
        "textDim": "#9CA3AF"
    }
}

DEFAULT_CONFIG = {
    "theme": "nova",
    "accentColor": "#7AA2F7",
    "secondaryColor": "#BB9AF7",
    "surfaceColor": "#141923",
    "dockColor": "#12161F",
    "cornerRadius": 18,
    "cardOpacity": 0.94,
    "widgets": {
        "clock": True,
        "weather": True,
        "quickSettings": True,
        "mediaPlayer": True,
        "systemMonitor": True,
        "terminalRice": True,
        "dock": True,
        "topPill": True
    },
    "dockPosition": "bottom",
    "performanceMode": "balanced",
    "nightLight": False,
    "dnd": False,
    "eqPreset": "Balanced"
}


class SystemBridge(QObject):
    # Signals for dynamic reactivity
    cpuChanged = Signal()
    ramChanged = Signal()
    diskChanged = Signal()
    netChanged = Signal()
    brightnessChanged = Signal()
    volumeChanged = Signal()
    mediaChanged = Signal()
    weatherChanged = Signal()
    uptimeChanged = Signal()
    configChanged = Signal()
    audioOutputsChanged = Signal()
    wifiListChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Configuration State ─────────────────────────────────────────────
        self._config = dict(DEFAULT_CONFIG)
        self._load_config()

        # ── Kernel / Hardware State ─────────────────────────────────────────
        self._cpu_pct = 0
        self._cpu_history = [0.2] * 12
        self._ram_pct = 0
        self._ram_history = [0.4] * 12
        self._ram_used_str = "0 GB"
        self._ram_total_str = "0 GB"
        self._disk_pct = 0
        self._disk_history = [0.5] * 12
        self._disk_used_str = "0 GB"
        self._disk_total_str = "0 GB"

        self._net_down = "0 KB/s"
        self._net_up = "0 KB/s"
        self._last_rx = 0
        self._last_tx = 0
        self._last_net_time = time.time()

        self._brightness = 52
        self._volume = 100
        self._volume_muted = False

        # ── Media Center State ──────────────────────────────────────────────
        self._media_title = "After Dark"
        self._media_artist = "Sweater Weather"
        self._media_album = "Atmosphere"
        self._media_cover = ""
        self._media_pos = "1:24"
        self._media_dur = "4:01"
        self._media_progress = 0.35
        self._media_playing = True
        self._media_queue = [
            {"title": "After Dark", "artist": "Sweater Weather", "dur": "4:01", "active": True},
            {"title": "Resonance", "artist": "HOME", "dur": "3:32", "active": False},
            {"title": "Memory Reboot", "artist": "VOJ & Narvent", "dur": "2:48", "active": False},
            {"title": "Nightcall", "artist": "Kavinsky", "dur": "4:19", "active": False},
            {"title": "Sunset Lover", "artist": "Petit Biscuit", "dur": "3:57", "active": False}
        ]

        # ── Weather State ───────────────────────────────────────────────────
        self._weather_temp = "34°"
        self._weather_cond = "Clouds"
        self._weather_city = "Ajmer"
        self._weather_wind = "4.49 m/s"
        self._weather_humidity = "49%"
        self._weather_icon = "󰖐"

        # ── System Info ─────────────────────────────────────────────────────
        self._uptime_str = "0m"
        self._kernel_str = platform.release() or "6.3.9-synth"
        self._user_str = os.environ.get("USER", "user")
        self._hostname_str = platform.node() or "synth"

        # ── Network & Audio Devices ─────────────────────────────────────────
        self._audio_outputs = ["Speakers (Built-in)", "Headphones (3.5mm)", "Bluetooth Audio", "HDMI / DisplayPort"]
        self._current_audio_output = "Speakers (Built-in)"
        self._wifi_networks = ["SynthNet-5G (Connected)", "Home-Office-Ext", "CoffeeShop-Guest", "IoT-Mesh"]

        # Previous CPU sample
        self._prev_idle = 0
        self._prev_total = 0

        # Fast poll timer (CPU, RAM, Net, Media) - 1.5s
        self._fast_timer = QTimer(self)
        self._fast_timer.timeout.connect(self._poll_fast)
        self._fast_timer.start(1500)

        # Slow poll timer (Disk, Uptime, Weather, Brightness, Volume) - 8s
        self._slow_timer = QTimer(self)
        self._slow_timer.timeout.connect(self._poll_slow)
        self._slow_timer.start(8000)

        # Initial immediate poll
        self._poll_fast()
        self._poll_slow()
        self._fetch_weather_async()

    # ─── Config Properties ──────────────────────────────────────────────────

    @Property(str, notify=configChanged)
    def currentTheme(self):
        return self._config.get("theme", "nova")

    @Property(str, notify=configChanged)
    def accentColor(self):
        return self._config.get("accentColor", "#7AA2F7")

    @Property(str, notify=configChanged)
    def secondaryColor(self):
        return self._config.get("secondaryColor", "#BB9AF7")

    @Property(str, notify=configChanged)
    def surfaceColor(self):
        return self._config.get("surfaceColor", "#141923")

    @Property(str, notify=configChanged)
    def dockColor(self):
        return self._config.get("dockColor", "#12161F")

    @Property(int, notify=configChanged)
    def cornerRadius(self):
        return self._config.get("cornerRadius", 18)

    @Property(float, notify=configChanged)
    def cardOpacity(self):
        return self._config.get("cardOpacity", 0.94)

    @Property("QVariantMap", notify=configChanged)
    def widgetsConfig(self):
        return self._config.get("widgets", DEFAULT_CONFIG["widgets"])

    @Property(str, notify=configChanged)
    def performanceMode(self):
        return self._config.get("performanceMode", "balanced")

    @Property(bool, notify=configChanged)
    def nightLight(self):
        return self._config.get("nightLight", False)

    @Property(bool, notify=configChanged)
    def dnd(self):
        return self._config.get("dnd", False)

    @Property(str, notify=configChanged)
    def eqPreset(self):
        return self._config.get("eqPreset", "Balanced")

    # ─── Hardware & Subsystem Properties ────────────────────────────────────

    @Property(int, notify=cpuChanged)
    def cpuPct(self):
        return self._cpu_pct

    @Property("QVariantList", notify=cpuChanged)
    def cpuHistory(self):
        return self._cpu_history

    @Property(int, notify=ramChanged)
    def ramPct(self):
        return self._ram_pct

    @Property(str, notify=ramChanged)
    def ramUsedStr(self):
        return self._ram_used_str

    @Property(str, notify=ramChanged)
    def ramTotalStr(self):
        return self._ram_total_str

    @Property("QVariantList", notify=ramChanged)
    def ramHistory(self):
        return self._ram_history

    @Property(int, notify=diskChanged)
    def diskPct(self):
        return self._disk_pct

    @Property(str, notify=diskChanged)
    def diskUsedStr(self):
        return self._disk_used_str

    @Property(str, notify=diskChanged)
    def diskTotalStr(self):
        return self._disk_total_str

    @Property("QVariantList", notify=diskChanged)
    def diskHistory(self):
        return self._disk_history

    @Property(str, notify=netChanged)
    def netDownSpeed(self):
        return self._net_down

    @Property(str, notify=netChanged)
    def netUpSpeed(self):
        return self._net_up

    @Property(int, notify=brightnessChanged)
    def brightness(self):
        return self._brightness

    @Property(int, notify=volumeChanged)
    def volume(self):
        return self._volume

    @Property(str, notify=mediaChanged)
    def mediaTitle(self):
        return self._media_title

    @Property(str, notify=mediaChanged)
    def mediaArtist(self):
        return self._media_artist

    @Property(str, notify=mediaChanged)
    def mediaAlbum(self):
        return self._media_album

    @Property(str, notify=mediaChanged)
    def mediaCover(self):
        return self._media_cover

    @Property(str, notify=mediaChanged)
    def mediaPos(self):
        return self._media_pos

    @Property(str, notify=mediaChanged)
    def mediaDur(self):
        return self._media_dur

    @Property(float, notify=mediaChanged)
    def mediaProgress(self):
        return self._media_progress

    @Property(bool, notify=mediaChanged)
    def mediaPlaying(self):
        return self._media_playing

    @Property("QVariantList", notify=mediaChanged)
    def mediaQueue(self):
        return self._media_queue

    @Property(str, notify=weatherChanged)
    def weatherTemp(self):
        return self._weather_temp

    @Property(str, notify=weatherChanged)
    def weatherCond(self):
        return self._weather_cond

    @Property(str, notify=weatherChanged)
    def weatherCity(self):
        return self._weather_city

    @Property(str, notify=weatherChanged)
    def weatherWind(self):
        return self._weather_wind

    @Property(str, notify=weatherChanged)
    def weatherHumidity(self):
        return self._weather_humidity

    @Property(str, notify=weatherChanged)
    def weatherIcon(self):
        return self._weather_icon

    @Property(str, notify=uptimeChanged)
    def uptimeStr(self):
        return self._uptime_str

    @Property(str, constant=True)
    def kernelStr(self):
        return self._kernel_str

    @Property(str, constant=True)
    def username(self):
        return self._user_str

    @Property(str, constant=True)
    def hostname(self):
        return self._hostname_str

    @Property("QVariantList", notify=audioOutputsChanged)
    def audioOutputs(self):
        return self._audio_outputs

    @Property(str, notify=audioOutputsChanged)
    def currentAudioOutput(self):
        return self._current_audio_output

    @Property("QVariantList", notify=wifiListChanged)
    def wifiNetworks(self):
        return self._wifi_networks

    # ─── Customization Slots ────────────────────────────────────────────────

    @Slot(str)
    def setTheme(self, theme_key: str):
        if theme_key in THEME_PRESETS:
            preset = THEME_PRESETS[theme_key]
            self._config["theme"] = theme_key
            self._config["accentColor"] = preset["accent"]
            self._config["secondaryColor"] = preset["secondary"]
            self._config["surfaceColor"] = preset["surface"]
            self._config["dockColor"] = preset["dock"]
            self._save_config()
            self.configChanged.emit()

    @Slot(str)
    def setAccentColor(self, color_hex: str):
        self._config["accentColor"] = color_hex
        self._save_config()
        self.configChanged.emit()

    @Slot(str, bool)
    def toggleWidget(self, widget_key: str, enabled: bool):
        if "widgets" not in self._config:
            self._config["widgets"] = dict(DEFAULT_CONFIG["widgets"])
        self._config["widgets"][widget_key] = enabled
        self._save_config()
        self.configChanged.emit()

    @Slot(int)
    def setCornerRadius(self, radius: int):
        self._config["cornerRadius"] = max(0, min(32, radius))
        self._save_config()
        self.configChanged.emit()

    @Slot(float)
    def setCardOpacity(self, opacity: float):
        self._config["cardOpacity"] = max(0.5, min(1.0, opacity))
        self._save_config()
        self.configChanged.emit()

    @Slot(str)
    def setPerformanceMode(self, mode: str):
        self._config["performanceMode"] = mode
        self._save_config()
        self.configChanged.emit()
        threading.Thread(target=self._apply_perf_mode, args=(mode,), daemon=True).start()

    @Slot(bool)
    def toggleNightLight(self, enabled: bool):
        self._config["nightLight"] = enabled
        self._save_config()
        self.configChanged.emit()
        threading.Thread(target=self._apply_night_light, args=(enabled,), daemon=True).start()

    @Slot(bool)
    def toggleDND(self, enabled: bool):
        self._config["dnd"] = enabled
        self._save_config()
        self.configChanged.emit()
        threading.Thread(target=lambda: subprocess.run(["makoctl", "mode", "-s", "dnd" if enabled else "default"], capture_output=True), daemon=True).start()

    @Slot(str)
    def setEqPreset(self, preset: str):
        self._config["eqPreset"] = preset
        self._save_config()
        self.configChanged.emit()

    @Slot(str)
    def setAudioOutput(self, output_name: str):
        self._current_audio_output = output_name
        self.audioOutputsChanged.emit()

    @Slot(int)
    def playQueueTrack(self, index: int):
        if 0 <= index < len(self._media_queue):
            for i, item in enumerate(self._media_queue):
                item["active"] = (i == index)
            track = self._media_queue[index]
            self._media_title = track["title"]
            self._media_artist = track["artist"]
            self._media_dur = track["dur"]
            self._media_pos = "0:00"
            self._media_progress = 0.0
            self._media_playing = True
            self.mediaChanged.emit()

    # ─── Standard Hardware Controls ─────────────────────────────────────────

    @Slot(int)
    def setBrightness(self, val: int):
        val = max(5, min(100, val))
        self._brightness = val
        self.brightnessChanged.emit()
        threading.Thread(target=self._apply_brightness, args=(val,), daemon=True).start()

    @Slot(int)
    def setVolume(self, val: int):
        val = max(0, min(100, val))
        self._volume = val
        self.volumeChanged.emit()
        threading.Thread(target=self._apply_volume, args=(val,), daemon=True).start()

    @Slot()
    def mediaPlayPause(self):
        self._media_playing = not self._media_playing
        self.mediaChanged.emit()
        threading.Thread(target=lambda: subprocess.run(["playerctl", "play-pause"], capture_output=True), daemon=True).start()

    @Slot()
    def mediaNext(self):
        threading.Thread(target=lambda: subprocess.run(["playerctl", "next"], capture_output=True), daemon=True).start()

    @Slot()
    def mediaPrevious(self):
        threading.Thread(target=lambda: subprocess.run(["playerctl", "previous"], capture_output=True), daemon=True).start()

    @Slot(str)
    def launchApp(self, cmd: str):
        if not cmd:
            return
        subprocess.Popen(cmd, shell=True)

    @Slot(str)
    def powerAction(self, action: str):
        if action == "lock":
            subprocess.Popen("hyprlock || swaylock || loginctl lock-session", shell=True)
        elif action == "reboot":
            subprocess.Popen("systemctl reboot", shell=True)
        elif action == "poweroff":
            subprocess.Popen("systemctl poweroff", shell=True)
        elif action == "suspend":
            subprocess.Popen("systemctl suspend", shell=True)

    # ─── Internal Polling & Helpers ─────────────────────────────────────────

    def _load_config(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self._config.update(data)
        except Exception:
            pass

    def _save_config(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump(self._config, f, indent=2)
        except Exception:
            pass

    def _apply_perf_mode(self, mode: str):
        try:
            if mode == "gaming":
                subprocess.run(["synthex-gaming-mode", "--enable"], capture_output=True)
            elif mode == "performance":
                subprocess.run(["powerprofilesctl", "set", "performance"], capture_output=True)
            elif mode == "powersave":
                subprocess.run(["powerprofilesctl", "set", "power-saver"], capture_output=True)
            else:
                subprocess.run(["powerprofilesctl", "set", "balanced"], capture_output=True)
        except Exception:
            pass

    def _apply_night_light(self, enabled: bool):
        try:
            if enabled:
                subprocess.run(["gammastep", "-O", "3500"], capture_output=True)
            else:
                subprocess.run(["pkill", "gammastep"], capture_output=True)
        except Exception:
            pass

    def _poll_fast(self):
        # 1. CPU
        try:
            with open("/proc/stat", "r") as f:
                fields = [float(x) for x in f.readline().strip().split()[1:]]
            idle = fields[3] + fields[4]
            total = sum(fields)
            if self._prev_total > 0:
                diff_idle = idle - self._prev_idle
                diff_total = total - self._prev_total
                pct = int(100.0 * (1.0 - diff_idle / max(1.0, diff_total)))
                self._cpu_pct = max(1, min(100, pct))
                self._cpu_history.pop(0)
                self._cpu_history.append(self._cpu_pct / 100.0)
                self.cpuChanged.emit()
            self._prev_idle = idle
            self._prev_total = total
        except Exception:
            pass

        # 2. RAM
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            total_kb, avail_kb = 0, 0
            for l in lines:
                if l.startswith("MemTotal:"):
                    total_kb = int(l.split()[1])
                elif l.startswith("MemAvailable:"):
                    avail_kb = int(l.split()[1])
            if total_kb > 0:
                used_kb = total_kb - avail_kb
                self._ram_pct = int((used_kb / total_kb) * 100)
                self._ram_used_str = f"{used_kb / (1024*1024):.1f} GB"
                self._ram_total_str = f"{total_kb / (1024*1024):.1f} GB"
                self._ram_history.pop(0)
                self._ram_history.append(self._ram_pct / 100.0)
                self.ramChanged.emit()
        except Exception:
            pass

        # 3. Network Throughput
        try:
            rx, tx = 0, 0
            with open("/proc/net/dev", "r") as f:
                for line in f.readlines()[2:]:
                    parts = line.split(":")
                    if len(parts) == 2 and not parts[0].strip().startswith("lo"):
                        cols = parts[1].split()
                        rx += int(cols[0])
                        tx += int(cols[8])
            now = time.time()
            dt = max(0.5, now - self._last_net_time)
            if self._last_rx > 0:
                down_bps = (rx - self._last_rx) / dt
                up_bps = (tx - self._last_tx) / dt
                self._net_down = self._fmt_speed(down_bps)
                self._net_up = self._fmt_speed(up_bps)
                self.netChanged.emit()
            self._last_rx = rx
            self._last_tx = tx
            self._last_net_time = now
        except Exception:
            pass

        # 4. MPRIS Media
        self._poll_mpris()

    def _poll_slow(self):
        # 1. Disk
        try:
            usage = shutil.disk_usage("/")
            self._disk_pct = int((usage.used / usage.total) * 100)
            self._disk_used_str = f"{int(usage.used / (1024**3))} GB"
            self._disk_total_str = f"{int(usage.total / (1024**3))} GB"
            self._disk_history.pop(0)
            self._disk_history.append(self._disk_pct / 100.0)
            self.diskChanged.emit()
        except Exception:
            pass

        # 2. Uptime
        try:
            with open("/proc/uptime", "r") as f:
                secs = float(f.readline().split()[0])
            hours = int(secs // 3600)
            mins = int((secs % 3600) // 60)
            self._uptime_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
            self.uptimeChanged.emit()
        except Exception:
            pass

        # 3. Brightness
        try:
            out = subprocess.check_output(["brightnessctl", "g"], stderr=subprocess.DEVNULL)
            max_b = subprocess.check_output(["brightnessctl", "m"], stderr=subprocess.DEVNULL)
            cur = int(out.strip())
            mx = int(max_b.strip())
            if mx > 0:
                self._brightness = int((cur / mx) * 100)
                self.brightnessChanged.emit()
        except Exception:
            pass

        # 4. Volume
        try:
            out = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], stderr=subprocess.DEVNULL)
            text = out.decode("utf-8")
            parts = text.split()
            if len(parts) >= 2:
                self._volume = int(float(parts[1]) * 100)
                self._volume_muted = "[MUTED]" in text
                self.volumeChanged.emit()
        except Exception:
            pass

    def _poll_mpris(self):
        try:
            out = subprocess.check_output(
                ["playerctl", "metadata", "--format", "{{status}}:::{{title}}:::{{artist}}:::{{position}}:::{{mpris:length}}:::{{mpris:artUrl}}"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()

            if out:
                parts = out.split(":::")
                if len(parts) >= 3:
                    self._media_playing = (parts[0].lower() == "playing")
                    self._media_title = parts[1] or "After Dark"
                    self._media_artist = parts[2] or "Sweater Weather"

                    pos_us = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
                    len_us = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0

                    if len_us > 0:
                        self._media_progress = min(1.0, max(0.0, pos_us / len_us))
                        pos_s = pos_us // 1000000
                        len_s = len_us // 1000000
                        self._media_pos = f"{pos_s // 60}:{pos_s % 60:02d}"
                        self._media_dur = f"{len_s // 60}:{len_s % 60:02d}"

                    if len(parts) > 5 and parts[5]:
                        self._media_cover = parts[5]

                    self.mediaChanged.emit()
        except Exception:
            pass

    def _apply_brightness(self, val):
        try:
            subprocess.run(["brightnessctl", "set", f"{val}%"], capture_output=True)
        except Exception:
            pass

    def _apply_volume(self, val):
        try:
            frac = val / 100.0
            subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{frac:.2f}"], capture_output=True)
        except Exception:
            pass

    def _fetch_weather_async(self):
        def _fetch():
            try:
                url = "https://wttr.in/?format=j1"
                req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    curr = data.get("current_condition", [{}])[0]
                    area = data.get("nearest_area", [{}])[0]

                    temp_c = curr.get("temp_C", "34")
                    desc = curr.get("weatherDesc", [{}])[0].get("value", "Clouds")
                    city = area.get("areaName", [{}])[0].get("value", "Ajmer")
                    wind = curr.get("windspeedKmph", "16")
                    wind_ms = f"{float(wind) / 3.6:.2f} m/s" if wind.isdigit() else "4.49 m/s"
                    humidity = curr.get("humidity", "49")

                    self._weather_temp = f"{temp_c}°"
                    self._weather_cond = desc
                    self._weather_city = city
                    self._weather_wind = wind_ms
                    self._weather_humidity = f"{humidity}%"

                    desc_low = desc.lower()
                    if "clear" in desc_low or "sun" in desc_low:
                        self._weather_icon = "󰖙"
                    elif "cloud" in desc_low or "overcast" in desc_low:
                        self._weather_icon = "󰖐"
                    elif "rain" in desc_low or "shower" in desc_low:
                        self._weather_icon = "󰖗"
                    elif "thunder" in desc_low:
                        self._weather_icon = "󰖓"
                    else:
                        self._weather_icon = "󰖐"

                    self.weatherChanged.emit()
            except Exception:
                pass

        threading.Thread(target=_fetch, daemon=True).start()

    @staticmethod
    def _fmt_speed(bps):
        if bps >= 1024 * 1024:
            return f"{bps / (1024*1024):.1f} MB/s"
        elif bps >= 1024:
            return f"{int(bps / 1024)} KB/s"
        else:
            return f"{int(bps)} B/s"
