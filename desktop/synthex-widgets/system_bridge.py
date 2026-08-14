#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""
SynthOS System Bridge
Exposes real Linux kernel (procfs/sysfs), audio (PipeWire/wpctl/pactl),
backlight (brightnessctl), MPRIS (playerctl), and desktop apps to QML.
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


class SystemBridge(QObject):
    # Signals for property updates
    cpuChanged = Signal()
    ramChanged = Signal()
    diskChanged = Signal()
    netChanged = Signal()
    brightnessChanged = Signal()
    volumeChanged = Signal()
    mediaChanged = Signal()
    weatherChanged = Signal()
    uptimeChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Internal state
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

        self._media_title = "No Track Playing"
        self._media_artist = "SynthOS Audio"
        self._media_cover = ""
        self._media_pos = "0:00"
        self._media_dur = "0:00"
        self._media_progress = 0.0
        self._media_playing = False

        self._weather_temp = "34°"
        self._weather_cond = "Clouds"
        self._weather_city = "Ajmer"
        self._weather_wind = "4.49 m/s"
        self._weather_humidity = "49%"
        self._weather_icon = "󰖐"

        self._uptime_str = "0m"
        self._kernel_str = platform.release() or "6.3.9-synth"
        self._user_str = os.environ.get("USER", "user")
        self._hostname_str = platform.node() or "synth"

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

    # ─── Properties ─────────────────────────────────────────────────────────

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

    # ─── Slots (Callable from QML) ──────────────────────────────────────────

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

    # ─── Polling Workers ───────────────────────────────────────────────────

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
            # format: Volume: 0.65 [MUTED]
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
                    return
        except Exception:
            pass

        # Fallback to reference track if playerctl is idle
        if not self._media_title or self._media_title == "No Track Playing":
            self._media_title = "After Dark"
            self._media_artist = "Sweater Weather"
            self._media_pos = "1:24"
            self._media_dur = "4:01"
            self._media_progress = 0.35
            self._media_playing = True
            self.mediaChanged.emit()

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

                    # Icon selection
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
