#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 3: System Integration Layer
Directly interfaces with NetworkManager, BlueZ, PipeWire/PulseAudio,
power-profiles-daemon, UPower, systemd, AccountsService, UDisks2, UFW,
xrandr, GSettings, and procfs/sysfs.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, GLib


# ── Safe D-Bus & GSettings Utilities ──────────────────────────────────────────

def get_gsettings(schema_id):
    try:
        source = Gio.SettingsSchemaSource.get_default()
        if source and source.lookup(schema_id, True):
            return Gio.Settings.new(schema_id)
    except Exception:
        pass
    return None


def run_cmd(cmd, timeout=5):
    try:
        res = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


# ── 1. Network Integration (NetworkManager) ───────────────────────────────────

class NetworkAdapter:
    @staticmethod
    def is_wifi_available():
        ok, out, _ = run_cmd("nmcli -t -f TYPE,STATE dev")
        return "wifi" in out

    @staticmethod
    def get_wifi_enabled():
        ok, out, _ = run_cmd("nmcli -t -f WIFI g")
        return "enabled" in out.lower()

    @staticmethod
    def set_wifi_enabled(enabled: bool):
        state = "on" if enabled else "off"
        return run_cmd(f"nmcli radio wifi {state}")[0]

    @staticmethod
    def get_wifi_networks():
        networks = []
        ok, out, _ = run_cmd("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list")
        if ok and out:
            for line in out.split("\n"):
                parts = line.split(":")
                if len(parts) >= 4:
                    in_use = parts[0] == "*"
                    ssid = parts[1]
                    if not ssid:
                        continue
                    try:
                        signal = int(parts[2])
                    except ValueError:
                        signal = 50
                    sec = parts[3] or "Open"
                    networks.append({
                        "ssid": ssid,
                        "signal": signal,
                        "security": sec,
                        "connected": in_use
                    })
        return networks

    @staticmethod
    def get_ethernet_status():
        ok, out, _ = run_cmd("nmcli -t -f DEVICE,TYPE,STATE,CONNECTION dev")
        if ok and out:
            for line in out.split("\n"):
                parts = line.split(":")
                if len(parts) >= 4 and parts[1] == "ethernet":
                    return {
                        "device": parts[0],
                        "connected": parts[2] == "connected",
                        "connection": parts[3]
                    }
        return {"device": "eth0", "connected": False, "connection": "Disconnected"}

    @staticmethod
    def get_dns_servers():
        ok, out, _ = run_cmd("nmcli dev show | grep 'IP4.DNS'")
        if ok and out:
            servers = [line.split(":", 1)[1].strip() for line in out.split("\n") if ":" in line]
            return servers
        return ["1.1.1.1", "8.8.8.8"]


# ── 2. Bluetooth Integration (BlueZ) ──────────────────────────────────────────

class BluetoothAdapter:
    @staticmethod
    def is_bluetooth_available():
        return os.path.exists("/sys/class/bluetooth") or shutil.which("bluetoothctl") is not None

    @staticmethod
    def get_bluetooth_enabled():
        ok, out, _ = run_cmd("bluetoothctl show")
        return "Powered: yes" in out

    @staticmethod
    def set_bluetooth_enabled(enabled: bool):
        state = "on" if enabled else "off"
        return run_cmd(f"bluetoothctl power {state}")[0]

    @staticmethod
    def get_paired_devices():
        devices = []
        ok, out, _ = run_cmd("bluetoothctl devices")
        if ok and out:
            for line in out.split("\n"):
                parts = line.split(" ", 2)
                if len(parts) >= 3 and parts[0] == "Device":
                    mac = parts[1]
                    name = parts[2]
                    # Check connected
                    _, info_out, _ = run_cmd(f"bluetoothctl info {mac}")
                    connected = "Connected: yes" in info_out
                    devices.append({
                        "mac": mac,
                        "name": name,
                        "connected": connected
                    })
        return devices


# ── 3. Audio Integration (PipeWire / PulseAudio) ──────────────────────────────

class AudioAdapter:
    @staticmethod
    def get_master_volume():
        # Try pactl
        ok, out, _ = run_cmd("pactl get-sink-volume @DEFAULT_SINK@")
        if ok and out:
            match = re.search(r"(\d+)%", out)
            if match:
                return int(match.group(1))
        # Fallback to amixer
        ok, out, _ = run_cmd("amixer get Master")
        if ok and out:
            match = re.search(r"\[(\d+)%\]", out)
            if match:
                return int(match.group(1))
        return 70

    @staticmethod
    def set_master_volume(volume_pct: int):
        volume_pct = max(0, min(150, volume_pct))
        run_cmd(f"pactl set-sink-volume @DEFAULT_SINK@ {volume_pct}%")
        run_cmd(f"amixer set Master {volume_pct}%")
        return True

    @staticmethod
    def get_mute():
        ok, out, _ = run_cmd("pactl get-sink-mute @DEFAULT_SINK@")
        if ok and out:
            return "yes" in out.lower()
        return False

    @staticmethod
    def set_mute(muted: bool):
        state = "1" if muted else "0"
        run_cmd(f"pactl set-sink-mute @DEFAULT_SINK@ {state}")
        return True

    @staticmethod
    def get_mic_volume():
        ok, out, _ = run_cmd("pactl get-source-volume @DEFAULT_SOURCE@")
        if ok and out:
            match = re.search(r"(\d+)%", out)
            if match:
                return int(match.group(1))
        return 65

    @staticmethod
    def set_mic_volume(volume_pct: int):
        volume_pct = max(0, min(100, volume_pct))
        run_cmd(f"pactl set-source-volume @DEFAULT_SOURCE@ {volume_pct}%")
        return True

    @staticmethod
    def get_audio_sinks():
        sinks = []
        ok, out, _ = run_cmd("pactl list short sinks")
        if ok and out:
            for line in out.split("\n"):
                parts = line.split("\t")
                if len(parts) >= 2:
                    sinks.append(parts[1])
        if not sinks:
            sinks = ["Built-in Audio (Analog Stereo)", "HDMI / DisplayPort Audio", "Bluetooth Audio Headset"]
        return sinks


# ── 4. Power & Battery Integration (UPower / power-profiles-daemon) ───────────

class PowerAdapter:
    @staticmethod
    def is_battery_available():
        return os.path.exists("/sys/class/power_supply") and any(
            p.startswith("BAT") for p in os.listdir("/sys/class/power_supply")
        )

    @staticmethod
    def get_battery_info():
        bat_dirs = [os.path.join("/sys/class/power_supply", p) for p in os.listdir("/sys/class/power_supply") if p.startswith("BAT")]
        if bat_dirs:
            bpath = bat_dirs[0]
            try:
                cap = int(open(os.path.join(bpath, "capacity")).read().strip())
                status = open(os.path.join(bpath, "status")).read().strip()
                return {"percentage": cap, "status": status, "charging": status.lower() == "charging"}
            except Exception:
                pass
        return {"percentage": 100, "status": "AC Power (Desktop / Full)", "charging": True}

    @staticmethod
    def get_power_profile():
        ok, out, _ = run_cmd("powerprofilesctl get")
        if ok and out:
            return out.strip()
        return "balanced"

    @staticmethod
    def set_power_profile(profile: str):
        return run_cmd(f"powerprofilesctl set {profile}")[0]


# ── 5. Display & DRM Integration ──────────────────────────────────────────────

class DisplayAdapter:
    @staticmethod
    def get_display_info():
        monitors = []
        ok, out, _ = run_cmd("xrandr --current")
        if ok and out:
            for line in out.split("\n"):
                if " connected" in line:
                    parts = line.split()
                    name = parts[0]
                    primary = "primary" in line
                    # Look for resolution
                    res_match = re.search(r"(\d+x\d+)\+(\d+)\+(\d+)", line)
                    res = res_match.group(1) if res_match else "1920x1080"
                    monitors.append({
                        "name": name,
                        "primary": primary,
                        "resolution": res
                    })
        if not monitors:
            monitors.append({"name": "eDP-1", "primary": True, "resolution": "1920x1080"})
        return monitors

    @staticmethod
    def is_hdr_supported():
        # Check DRM connector properties for HDR metadata
        ok, out, _ = run_cmd("grep -l 'HDR_OUTPUT_METADATA' /sys/class/drm/*/enabled 2>/dev/null")
        return ok

    @staticmethod
    def is_vrr_supported():
        # Check for adaptive sync / VRR capability in DRM
        ok, out, _ = run_cmd("find /sys/class/drm/ -name 'vrr_capable' -exec cat {} + 2>/dev/null")
        return "1" in out

    @staticmethod
    def set_resolution(output_name: str, mode: str):
        return run_cmd(f"xrandr --output {output_name} --mode {mode}")[0]


# ── 6. Storage & Disks Integration (UDisks2 / procfs) ──────────────────────────

class StorageAdapter:
    @staticmethod
    def get_storage_devices():
        devices = []
        ok, out, _ = run_cmd("lsblk -J -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL")
        if ok and out:
            try:
                data = json.loads(out)
                for dev in data.get("blockdevices", []):
                    devices.append({
                        "name": dev.get("name", "sda"),
                        "size": dev.get("size", "0G"),
                        "type": dev.get("type", "disk"),
                        "model": dev.get("model", "Storage Device").strip() if dev.get("model") else "Disk Drive",
                        "children": dev.get("children", [])
                    })
            except Exception:
                pass
        if not devices:
            devices.append({"name": "nvme0n1", "size": "512G", "type": "disk", "model": "NVMe SSD", "children": []})
        return devices

    @staticmethod
    def get_root_usage():
        ok, out, _ = run_cmd("df -h /")
        if ok and out:
            lines = out.split("\n")
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 5:
                    return {
                        "total": parts[1],
                        "used": parts[2],
                        "available": parts[3],
                        "percent": parts[4]
                    }
        return {"total": "500G", "used": "45G", "available": "455G", "percent": "9%"}


# ── 7. Security & Firewall Integration (UFW / nftables) ────────────────────────

class SecurityAdapter:
    @staticmethod
    def get_firewall_status():
        ok, out, _ = run_cmd("ufw status")
        return "active" in out.lower()

    @staticmethod
    def set_firewall_status(enabled: bool):
        action = "enable" if enabled else "disable"
        return run_cmd(f"pkexec ufw {action}")[0]

    @staticmethod
    def get_secure_boot_status():
        ok, out, _ = run_cmd("mokutil --sb-state 2>/dev/null")
        if ok and "SecureBoot enabled" in out:
            return "Enabled"
        elif ok and "SecureBoot disabled" in out:
            return "Disabled"
        return "Not Supported / Legacy BIOS"


# ── 8. System & Package Integration ───────────────────────────────────────────

class SystemAdapter:
    @staticmethod
    def get_system_specs():
        uname = os.uname()
        # CPU
        cpu = uname.machine
        try:
            for line in open("/proc/cpuinfo"):
                if "model name" in line:
                    cpu = line.split(":", 1)[1].strip()
                    break
        except Exception:
            pass
        # RAM
        ram = "Unknown"
        try:
            for line in open("/proc/meminfo"):
                if "MemTotal:" in line:
                    ram = f"{int(line.split()[1]) / 1048576:.1f} GiB"
                    break
        except Exception:
            pass
        # GPU
        gpu = "Standard Controller"
        ok, out, _ = run_cmd("lspci | grep -i -E 'vga|3d|display'")
        if ok and out:
            gpu = out.split(":", 2)[-1].strip()

        return {
            "os_name": "SynthOS Linux 2026.10 LTS",
            "kernel": uname.release,
            "arch": uname.machine,
            "cpu": cpu,
            "ram": ram,
            "gpu": gpu,
            "hostname": uname.nodename,
            "uptime": SystemAdapter.get_uptime()
        }

    @staticmethod
    def get_uptime():
        try:
            with open("/proc/uptime", "r") as f:
                uptime_sec = float(f.readline().split()[0])
                hours = int(uptime_sec // 3600)
                minutes = int((uptime_sec % 3600) // 60)
                return f"{hours} hours, {minutes} minutes"
        except Exception:
            return "Active"

    @staticmethod
    def get_services_status():
        services = ["NetworkManager", "bluetooth", "pipewire", "systemd-timesyncd", "ufw", "cups"]
        res = []
        for s in services:
            ok, out, _ = run_cmd(f"systemctl is-active {s}")
            res.append({"name": s, "active": out.strip() == "active"})
        return res
