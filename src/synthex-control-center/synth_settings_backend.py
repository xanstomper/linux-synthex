#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 2: Settings Backend & Setting Model
Manages the unified Setting schema, capability detection, state synchronization,
and transaction execution.
"""

from typing import Any, Callable, Dict, List, Optional
from synth_system_adapters import (
    NetworkAdapter,
    BluetoothAdapter,
    AudioAdapter,
    PowerAdapter,
    DisplayAdapter,
    StorageAdapter,
    SecurityAdapter,
    SystemAdapter,
    get_gsettings
)


class Setting:
    def __init__(
        self,
        id: str,
        category: str,
        subcategory: str,
        title: str,
        description: str,
        type: str,  # 'boolean', 'choice', 'range', 'action', 'info'
        current_value: Any,
        default_value: Any,
        capabilities: Optional[List[str]] = None,
        permissions: str = "user",  # 'user', 'polkit', 'root'
        backend: str = "internal",
        apply_fn: Optional[Callable[[Any], bool]] = None,
        reset_fn: Optional[Callable[[], bool]] = None,
        availability_fn: Optional[Callable[[], bool]] = None,
        options: Optional[List[str]] = None,
        min_val: float = 0.0,
        max_val: float = 100.0,
        step: float = 1.0,
    ):
        self.id = id
        self.category = category
        self.subcategory = subcategory
        self.title = title
        self.description = description
        self.type = type
        self._current_value = current_value
        self.default_value = default_value
        self.capabilities = capabilities or []
        self.permissions = permissions
        self.backend = backend
        self._apply_fn = apply_fn
        self._reset_fn = reset_fn
        self._availability_fn = availability_fn
        self.options = options or []
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

    @property
    def value(self) -> Any:
        return self._current_value

    @value.setter
    def value(self, new_val: Any):
        self._current_value = new_val

    def apply(self, new_value: Any) -> bool:
        self._current_value = new_value
        if self._apply_fn:
            try:
                return self._apply_fn(new_value)
            except Exception as e:
                print(f"[SettingsBackend] Error applying {self.id}: {e}")
                return False
        return True

    def reset(self) -> bool:
        if self._reset_fn:
            return self._reset_fn()
        return self.apply(self.default_value)

    def is_available(self) -> bool:
        if self._availability_fn:
            try:
                return self._availability_fn()
            except Exception:
                return False
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
        self._init_registry()

    def _init_registry(self):
        # ── 1. Network ──────────────────────────────────────────────────
        self.register(Setting(
            id="network.wifi.enabled",
            category="Network",
            subcategory="Wi-Fi",
            title="Wi-Fi Adapter",
            description="Enable or disable the wireless networking hardware",
            type="boolean",
            current_value=NetworkAdapter.get_wifi_enabled(),
            default_value=True,
            capabilities=["wifi"],
            backend="NetworkManager",
            apply_fn=lambda v: NetworkAdapter.set_wifi_enabled(v),
            availability_fn=lambda: self.detector.has_wifi
        ))

        # ── 2. Bluetooth ────────────────────────────────────────────────
        self.register(Setting(
            id="bluetooth.enabled",
            category="Bluetooth",
            subcategory="Devices",
            title="Bluetooth Radio",
            description="Enable or disable Bluetooth wireless communication",
            type="boolean",
            current_value=BluetoothAdapter.get_bluetooth_enabled(),
            default_value=True,
            capabilities=["bluetooth"],
            backend="BlueZ",
            apply_fn=lambda v: BluetoothAdapter.set_bluetooth_enabled(v),
            availability_fn=lambda: self.detector.has_bluetooth
        ))

        # ── 3. Sound ────────────────────────────────────────────────────
        self.register(Setting(
            id="sound.master_volume",
            category="Sound",
            subcategory="Volume",
            title="Master Output Volume",
            description="Adjust the global audio output volume level",
            type="range",
            current_value=AudioAdapter.get_master_volume(),
            default_value=75,
            min_val=0,
            max_val=100,
            step=1,
            backend="PipeWire",
            apply_fn=lambda v: AudioAdapter.set_master_volume(int(v))
        ))

        self.register(Setting(
            id="sound.mute",
            category="Sound",
            subcategory="Volume",
            title="Mute Audio",
            description="Silence all system audio playback",
            type="boolean",
            current_value=AudioAdapter.get_mute(),
            default_value=False,
            backend="PipeWire",
            apply_fn=lambda v: AudioAdapter.set_mute(v)
        ))

        # ── 4. Power ────────────────────────────────────────────────────
        self.register(Setting(
            id="power.profile",
            category="Power & Battery",
            subcategory="Power profiles",
            title="Active Power Profile",
            description="Select hardware performance and power scaling profile",
            type="choice",
            current_value=PowerAdapter.get_power_profile(),
            default_value="balanced",
            options=["power-saver", "balanced", "performance"],
            backend="power-profiles-daemon",
            apply_fn=lambda v: PowerAdapter.set_power_profile(v)
        ))

        # ── 5. Security ─────────────────────────────────────────────────
        self.register(Setting(
            id="security.firewall",
            category="Security",
            subcategory="Firewall",
            title="UFW Firewall Protection",
            description="Enforce packet inspection and port isolation rules",
            type="boolean",
            current_value=SecurityAdapter.get_firewall_status(),
            default_value=True,
            permissions="polkit",
            backend="UFW",
            apply_fn=lambda v: SecurityAdapter.set_firewall_status(v)
        ))

    def register(self, setting: Setting):
        self.settings[setting.id] = setting

    def get_setting(self, setting_id: str) -> Optional[Setting]:
        return self.settings.get(setting_id)

    def search_settings(self, query: str) -> List[Setting]:
        q = query.strip().lower()
        if not q:
            return list(self.settings.values())
        return [
            s for s in self.settings.values()
            if q in s.title.lower() or q in s.description.lower() or q in s.category.lower() or q in s.subcategory.lower()
        ]
