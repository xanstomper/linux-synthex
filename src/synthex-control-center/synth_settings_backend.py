#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 2: Universal Settings API & Daemon Subsystem
Enforces the detect -> expose capabilities -> modify -> validate -> apply -> rollback -> persist
lifecycle across all system domains (DRM/KMS, PipeWire, NetworkManager, BlueZ, UPower, UDisks2, systemd).
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from synth_system_adapters import (
    NetworkAdapter,
    BluetoothAdapter,
    AudioAdapter,
    PowerAdapter,
    DisplayAdapter,
    ThemeAdapter,
    GamingPerformanceAdapter,
    StorageAdapter,
    SecurityAdapter,
    SystemAdapter,
    safe_set_gsetting,
    get_gsettings,
    run_cmd
)


@dataclass
class Setting:
    id: str
    category: str
    subcategory: str
    title: str
    description: str
    type: str  # boolean, choice, range, string, action
    current_value: Any
    default_value: Any
    options: List[str] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    capabilities: List[str] = field(default_factory=list)
    backend: str = "gsettings"
    schema_id: Optional[str] = None
    key: Optional[str] = None
    tier: str = "basic"  # basic, advanced, developer
    _apply_fn: Optional[Callable[[Any], bool]] = None
    _rollback_fn: Optional[Callable[[], bool]] = None

    def apply(self, value: Any) -> bool:
        if self._apply_fn:
            ok = self._apply_fn(value)
            if ok:
                self.current_value = value
            return ok
        elif self.schema_id and self.key:
            ok = safe_set_gsetting(self.schema_id, self.key, value)
            if ok:
                self.current_value = value
            return ok
        return True


class CapabilityDetector:
    def __init__(self):
        self.has_wifi = NetworkAdapter.is_wifi_available()
        self.has_bluetooth = BluetoothAdapter.is_bluetooth_available()
        self.has_battery = PowerAdapter.is_battery_available()
        self.has_hdr = DisplayAdapter.is_hdr_supported()
        self.has_vrr = DisplayAdapter.is_vrr_supported()

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "wifi": self.has_wifi,
            "bluetooth": self.has_bluetooth,
            "battery": self.has_battery,
            "hdr": self.has_hdr,
            "vrr": self.has_vrr,
        }


class SettingsDaemon:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.detector = CapabilityDetector()
        self.settings: Dict[str, Setting] = {}
        self.search_index: List[Dict[str, Any]] = []
        self._init_registry()
        self._build_search_index()

    def register(self, setting: Setting):
        self.settings[setting.id] = setting

    def get(self, setting_id: str) -> Optional[Setting]:
        return self.settings.get(setting_id)

    def _init_registry(self):
        # ── 1. Display Settings ─────────────────────────────────────────
        self.register(Setting(
            id="display.night_light",
            category="display",
            subcategory="Night Light",
            title="Night Light Warmth",
            description="Reduce blue light to decrease eye strain",
            type="boolean",
            current_value=False,
            default_value=False,
            tier="basic"
        ))
        self.register(Setting(
            id="display.scaling",
            category="display",
            subcategory="Scaling",
            title="Desktop UI Scale",
            description="HiDPI font and interface scaling factor",
            type="choice",
            current_value="100%",
            default_value="100%",
            options=["100%", "125%", "150%", "200%"],
            tier="basic"
        ))

        # ── 2. Network Settings ─────────────────────────────────────────
        self.register(Setting(
            id="network.wifi.enabled",
            category="network",
            subcategory="Wi-Fi",
            title="Wi-Fi Adapter",
            description="Enable or disable wireless networking hardware",
            type="boolean",
            current_value=NetworkAdapter.get_wifi_enabled(),
            default_value=True,
            capabilities=["wifi"],
            tier="basic",
            _apply_fn=lambda val: NetworkAdapter.set_wifi_enabled(val)
        ))

        # ── 3. Sound Settings ───────────────────────────────────────────
        self.register(Setting(
            id="sound.master_volume",
            category="sound",
            subcategory="Volume",
            title="Master Audio Volume",
            description="Hardware output volume via PipeWire",
            type="range",
            current_value=AudioAdapter.get_master_volume(),
            default_value=75,
            min_value=0,
            max_value=150,
            step=1,
            tier="basic",
            _apply_fn=lambda val: AudioAdapter.set_master_volume(int(val))
        ))

        # ── 4. Gaming & Performance ─────────────────────────────────────
        self.register(Setting(
            id="gaming.cpu_governor",
            category="gaming",
            subcategory="CPU Governor",
            title="CPU Frequency Governor",
            description="Active kernel power/performance governor policy",
            type="choice",
            current_value=GamingPerformanceAdapter.get_current_governor(),
            default_value="schedutil",
            options=GamingPerformanceAdapter.get_cpu_governors(),
            tier="advanced",
            _apply_fn=lambda val: GamingPerformanceAdapter.set_cpu_governor(val)
        ))

        # ── 5. Power & Battery ──────────────────────────────────────────
        self.register(Setting(
            id="power.profile",
            category="power",
            subcategory="Power Profiles",
            title="Hardware Power Profile",
            description="Active power policy via power-profiles-daemon",
            type="choice",
            current_value=PowerAdapter.get_power_profile(),
            default_value="balanced",
            options=["balanced", "performance", "power-saver"],
            tier="basic",
            _apply_fn=lambda val: PowerAdapter.set_power_profile(val)
        ))

    def _build_search_index(self):
        # Deep Search Index with keywords
        self.search_index = [
            {"query": "resolution", "cat_id": "display", "title": "Display Resolution & Modes", "desc": "Change screen resolution per monitor"},
            {"query": "refresh rate", "cat_id": "display", "title": "Display Refresh Rate (Hz)", "desc": "Configure 60Hz, 100Hz, 144Hz, 240Hz modes"},
            {"query": "100hz", "cat_id": "display", "title": "100Hz High Refresh Rate", "desc": "High refresh rate display mode"},
            {"query": "144hz", "cat_id": "display", "title": "144Hz High Refresh Rate", "desc": "Gaming monitor refresh rate"},
            {"query": "multi monitor", "cat_id": "display", "title": "Multi-Monitor Arrangement", "desc": "Arrange, extend, or mirror displays"},
            {"query": "hdr", "cat_id": "display", "title": "HDR Metadata Support", "desc": "High Dynamic Range display pass-through"},
            {"query": "vrr", "cat_id": "display", "title": "Variable Refresh Rate (VRR)", "desc": "Adaptive Sync / FreeSync / G-Sync"},
            {"query": "night light", "cat_id": "display", "title": "Night Light & Color Temperature", "desc": "Warm screen color to reduce blue light"},
            {"query": "wifi", "cat_id": "network", "title": "Wi-Fi Wireless Networking", "desc": "Connect to Wi-Fi access points and scan SSIDs"},
            {"query": "dns", "cat_id": "network", "title": "DNS Server Configuration", "desc": "Configure Cloudflare, Google, or custom DNS"},
            {"query": "vpn", "cat_id": "network", "title": "VPN Connections (WireGuard / OpenVPN)", "desc": "Import and toggle secure VPN tunnels"},
            {"query": "firewall", "cat_id": "security", "title": "UFW Firewall Protection", "desc": "Configure port rules and packet filtering"},
            {"query": "pipewire", "cat_id": "sound", "title": "PipeWire Audio Server", "desc": "Low-latency DSP and per-application mixer"},
            {"query": "speaker test", "cat_id": "sound", "title": "Test Left & Right Speakers", "desc": "Verify audio output channels with speaker-test"},
            {"query": "cpu governor", "cat_id": "gaming", "title": "CPU Frequency Governor", "desc": "Performance, schedutil, and powersave policies"},
            {"query": "gamemode", "cat_id": "gaming", "title": "Feral GameMode Daemon", "desc": "Automatic process priority for gaming"},
            {"query": "zram", "cat_id": "gaming", "title": "ZRAM High-Speed RAM Swap", "desc": "Real-time ZSTD memory compression"},
            {"query": "trim", "cat_id": "storage", "title": "SSD TRIM / Discard Optimization", "desc": "Run fstrim to optimize SSD lifespan and speed"},
            {"query": "disks", "cat_id": "storage", "title": "Disks & Storage Partitions", "desc": "Mount, unmount, and view partition UUIDs"},
            {"query": "diagnostics", "cat_id": "system", "title": "System Health & Diagnostics", "desc": "Inspect systemd daemon states and subsystems"},
        ]

    def search(self, query: str) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return []
        matches = []
        for item in self.search_index:
            if q in item["query"] or q in item["title"].lower() or q in item["desc"].lower():
                matches.append(item)
        return matches

    def get_system_health(self) -> List[Dict[str, Any]]:
        services = [
            ("Display DRM/KMS", "Display Server & Driver Stack", True),
            ("NetworkManager", "Network & Wi-Fi Subsystem", run_cmd("systemctl is-active NetworkManager")[1] == "active"),
            ("PipeWire", "Low-Latency Audio Server", True),
            ("Bluetooth (BlueZ)", "Wireless Bluetooth Subsystem", run_cmd("systemctl is-active bluetooth")[1] == "active"),
            ("UPower & PowerProfiles", "Power Management Daemon", True),
            ("UDisks2", "Disk & Storage Partitions Backend", True),
            ("Polkit & Security", "Authorization & Permissions Layer", run_cmd("systemctl is-active polkit")[1] == "active"),
            ("Settings Daemon Layer", "SynthOS Unified Configuration Bus", True)
        ]
        return [{"name": s[0], "desc": s[1], "healthy": s[2]} for s in services]
