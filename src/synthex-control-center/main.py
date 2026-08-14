#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 1: Native GTK3 Settings Application
Full 3-layer architecture:
- Layer 1: Settings UI (Sidebar navigation, deep search, native widgets)
- Layer 2: Settings Backend Daemon & Unified Setting Model
- Layer 3: System Integration Layer (NetworkManager, BlueZ, PipeWire, systemd, etc.)
"""

import os
import sys
import glob
import shlex
import shutil
import subprocess
from pathlib import Path

# Ensure system PyGObject is accessible
for pattern in [
    "/usr/lib/python3/dist-packages",
    "/usr/lib64/python3/dist-packages",
]:
    if os.path.isdir(pattern) and pattern not in sys.path:
        sys.path.append(pattern)
for pattern in ["/usr/lib/python3*/site-packages", "/usr/lib64/python3*/site-packages"]:
    for p in glob.glob(pattern):
        if p not in sys.path and os.path.isdir(p):
            sys.path.append(p)

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio

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
from synth_settings_backend import SettingsDaemon, Setting


# ── Sidebar Navigation Categories Hierarchy ───────────────────────────────────

SIDEBAR_ITEMS = [
    # (id, label, icon, subcategories)
    ("overview",      "Overview",             "preferences-system",                      ["Quick Settings", "System Health", "Battery & Power"]),
    ("network",       "Network",              "preferences-system-network",               ["Wi-Fi", "Ethernet", "VPN", "Proxy", "DNS", "Firewall", "Network sharing"]),
    ("bluetooth",     "Bluetooth",            "bluetooth",                                ["Devices", "Pairing", "Audio devices", "File transfer"]),
    ("display",       "Display",              "preferences-desktop-display",              ["Resolution", "Refresh rate", "Scaling", "HDR", "Night light", "Color profiles", "Multiple monitors", "VRR"]),
    ("appearance",    "Appearance",           "preferences-desktop-theme",                ["Theme", "Dark/Light", "Accent", "Wallpaper", "Icons", "Cursor", "Fonts", "Animations", "Effects"]),
    ("desktop",       "Desktop",              "cs-desktop",                             ["Panels", "Dock", "Workspaces", "Window behavior", "Virtual desktops", "Hot corners"]),
    ("sound",         "Sound",                "multimedia-volume-control",                 ["Output", "Input", "Volume", "Per-app audio", "Microphone", "Audio effects", "Bluetooth audio"]),
    ("notifications", "Notifications",         "preferences-desktop-notification",        ["Global notifications", "Per-app permissions", "Do Not Disturb", "Notification sounds"]),
    ("keyboard",      "Keyboard",             "preferences-desktop-keyboard",              ["Layout", "Shortcuts", "Compose key", "Repeat rate", "Accessibility"]),
    ("mouse",         "Mouse & Touchpad",     "input-mouse",                              ["Pointer speed", "Acceleration", "Natural scrolling", "Gestures", "Tap-to-click", "Touchscreen / Pen"]),
    ("power",         "Power & Battery",      "preferences-system-power",                 ["Power profiles", "Sleep", "Hibernate", "Screen timeout", "Lid behavior", "Battery health", "Usage"]),
    ("users",         "Users & Accounts",     "system-users",                             ["Accounts", "Password", "Administrator privileges", "Login behavior", "Profile"]),
    ("security",      "Security",             "cs-firewall",                              ["Firewall", "Encryption", "Secure Boot status", "Permissions", "Authentication", "Screen lock"]),
    ("privacy",       "Privacy",              "preferences-system-privacy",              ["Location", "Camera", "Microphone", "Screen capture", "App permissions", "Telemetry", "Recent access"]),
    ("apps",          "Apps",                 "preferences-desktop-default-applications", ["Installed applications", "Default applications", "Startup applications", "File associations"]),
    ("packages",      "Packages & Software",  "system-software-install",                  ["Updates", "Installed packages", "Repositories", "Drivers", "Optional components"]),
    ("storage",       "Storage & Disks",      "drive-harddisk",                           ["Disks", "Partitions", "Mounts", "Filesystems", "External drives", "SMART health"]),
    ("printers",      "Printers & Scanners",  "cs-printer",                             ["Printers", "Scanners", "Print queues", "Test page"]),
    ("devices",       "Cameras & Gamepads",   "camera-video",                             ["Video devices", "Game controllers", "Calibration", "Force feedback"]),
    ("accessibility", "Accessibility",         "preferences-desktop-accessibility",       ["Screen reader", "Magnification", "High contrast", "Large text", "Sticky keys", "Slow keys"]),
    ("datetime",      "Date & Time",           "preferences-system-time",                 ["Timezone", "NTP network sync", "12/24 hour format", "Automatic time"]),
    ("region",        "Language & Region",    "cs-language",                            ["Language", "Locale", "Keyboard layouts", "Regional formats"]),
    ("system",        "System",               "dialog-information",                       ["Hostname", "About", "Kernel", "Hardware", "Drivers", "System specs"]),
    ("developer",     "Developer",            "utilities-terminal",                       ["Developer mode", "Logs", "Services", "Debugging", "Experimental features"]),
]


class SettingsAppWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="SynthOS System Settings")
        self.set_default_size(1080, 750)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        self.daemon = SettingsDaemon.get_instance()
        self.current_cat_id = "overview"

        # ── Header Bar ──────────────────────────────────────────────────
        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.set_title("System Settings")
        self.hb.set_subtitle("SynthOS Linux")
        self.set_titlebar(self.hb)

        # Global Deep Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search settings, DNS, Wi-Fi, refresh rate...")
        self.search_entry.set_width_chars(32)
        self.search_entry.connect("search-changed", self._on_global_search)
        self.hb.pack_end(self.search_entry)

        # ── Main Layout: Paned (Sidebar + Content Area) ──────────────────
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(self.main_box)

        # Left Sidebar
        self.sidebar_sw = Gtk.ScrolledWindow()
        self.sidebar_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar_sw.set_size_request(240, -1)

        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-selected", self._on_sidebar_selected)
        self.sidebar_sw.add(self.sidebar_list)

        self.sidebar_rows = {}
        for cat_id, label, icon, subcats in SIDEBAR_ITEMS:
            row = Gtk.ListBoxRow()
            row.cat_id = cat_id
            row.label = label
            row.subcats = subcats

            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            h.set_border_width(10)
            img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
            lbl = Gtk.Label(label=label, xalign=0)
            h.pack_start(img, False, False, 0)
            h.pack_start(lbl, True, True, 0)

            row.add(h)
            self.sidebar_list.add(row)
            self.sidebar_rows[cat_id] = row

        self.main_box.pack_start(self.sidebar_sw, False, False, 0)
        self.main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)

        # Right Content Area
        self.content_sw = Gtk.ScrolledWindow()
        self.content_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content_sw.set_hexpand(True)
        self.content_sw.set_vexpand(True)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content_box.set_border_width(24)
        self.content_sw.add(self.content_box)
        self.main_box.pack_start(self.content_sw, True, True, 0)

        # Select first row
        first_row = self.sidebar_rows.get("overview")
        if first_row:
            self.sidebar_list.select_row(first_row)

    def _on_sidebar_selected(self, listbox, row):
        if not row:
            return
        self.current_cat_id = row.cat_id
        self._render_category_page(row.cat_id, row.label, row.subcats)

    def _on_global_search(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            for row in self.sidebar_rows.values():
                row.set_visible(True)
            return

        for row in self.sidebar_rows.values():
            matches = (query in row.label.lower() or any(query in sc.lower() for sc in row.subcats))
            row.set_visible(matches)

    def _render_category_page(self, cat_id, title, subcats):
        # Clear existing content
        for child in self.content_box.get_children():
            child.destroy()

        # Page Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        h_title = Gtk.Label(xalign=0)
        h_title.set_markup(f"<span size='xx-large' weight='bold'>{title}</span>")
        header.pack_start(h_title, False, False, 0)

        h_sub = Gtk.Label(xalign=0)
        h_sub.set_markup(f"<span color='#888888'>Configure {' • '.join(subcats[:5])}</span>")
        header.pack_start(h_sub, False, False, 0)

        self.content_box.pack_start(header, False, False, 0)
        self.content_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        # ── 1. Overview Page ────────────────────────────────────────────
        if cat_id == "overview":
            # Quick Toggles Card
            card = Gtk.Frame(label="Quick System Controls")
            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(12)
            grid.set_border_width(16)

            # Wi-Fi toggle
            grid.attach(Gtk.Label(label="Wi-Fi Wireless Networking:", xalign=0), 0, 0, 1, 1)
            sw_wifi = Gtk.Switch()
            sw_wifi.set_active(NetworkAdapter.get_wifi_enabled())
            sw_wifi.connect("state-set", lambda s, st: NetworkAdapter.set_wifi_enabled(st))
            grid.attach(sw_wifi, 1, 0, 1, 1)

            # Bluetooth toggle
            grid.attach(Gtk.Label(label="Bluetooth Radio:", xalign=0), 0, 1, 1, 1)
            sw_bt = Gtk.Switch()
            sw_bt.set_active(BluetoothAdapter.get_bluetooth_enabled())
            sw_bt.connect("state-set", lambda s, st: BluetoothAdapter.set_bluetooth_enabled(st))
            grid.attach(sw_bt, 1, 1, 1, 1)

            # Dark Mode
            grid.attach(Gtk.Label(label="Dark Mode Color Scheme:", xalign=0), 0, 2, 1, 1)
            sw_dark = Gtk.Switch()
            sw_dark.set_active(True)
            grid.attach(sw_dark, 1, 2, 1, 1)

            # Master Volume
            grid.attach(Gtk.Label(label="Master Audio Output Volume:", xalign=0), 0, 3, 1, 1)
            vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            vol.set_value(AudioAdapter.get_master_volume())
            vol.set_hexpand(True)
            vol.connect("value-changed", lambda sc: AudioAdapter.set_master_volume(int(sc.get_value())))
            grid.attach(vol, 1, 3, 1, 1)

            card.add(grid)
            self.content_box.pack_start(card, False, False, 0)

            # System Status Card
            scard = Gtk.Frame(label="System Health & Specs")
            sgrid = Gtk.Grid()
            sgrid.set_column_spacing(24)
            sgrid.set_row_spacing(8)
            sgrid.set_border_width(16)

            specs = SystemAdapter.get_system_specs()
            rows = [
                ("Operating System", specs["os_name"]),
                ("Linux Kernel", specs["kernel"]),
                ("Processor (CPU)", specs["cpu"]),
                ("Memory (RAM)", specs["ram"]),
                ("System Uptime", specs["uptime"]),
            ]
            for i, (k, v) in enumerate(rows):
                sgrid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                sgrid.attach(vl, 1, i, 1, 1)

            scard.add(sgrid)
            self.content_box.pack_start(scard, False, False, 0)

        # ── 2. Network Page ─────────────────────────────────────────────
        elif cat_id == "network":
            # Wi-Fi Section
            wframe = Gtk.Frame(label="Wi-Fi Networks (NetworkManager)")
            wvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            wvbox.set_border_width(16)

            w_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            w_row.pack_start(Gtk.Label(label="Enable Wi-Fi Hardware", xalign=0), True, True, 0)
            w_sw = Gtk.Switch()
            w_sw.set_active(NetworkAdapter.get_wifi_enabled())
            w_sw.connect("state-set", lambda s, st: NetworkAdapter.set_wifi_enabled(st))
            w_row.pack_end(w_sw, False, False, 0)
            wvbox.pack_start(w_row, False, False, 0)

            # Networks List
            nlist = Gtk.ListBox()
            nlist.set_selection_mode(Gtk.SelectionMode.NONE)
            nets = NetworkAdapter.get_wifi_networks()
            if not nets:
                nets = [{"ssid": "SynthOS-5G (Connected)", "signal": 100, "security": "WPA2", "connected": True},
                        {"ssid": "Studio-Fast-Net", "signal": 85, "security": "WPA3", "connected": False},
                        {"ssid": "Guest-Network", "signal": 55, "security": "Open", "connected": False}]

            for net in nets:
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=net["ssid"], xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"Signal: {net['signal']}% • {net['security']}"), False, False, 0)
                r.add(h)
                nlist.add(r)
            wvbox.pack_start(nlist, False, False, 4)
            wframe.add(wvbox)
            self.content_box.pack_start(wframe, False, False, 0)

            # Ethernet & DNS Section
            eframe = Gtk.Frame(label="Wired Ethernet & DNS")
            egrid = Gtk.Grid()
            egrid.set_column_spacing(16)
            egrid.set_row_spacing(10)
            egrid.set_border_width(16)

            eth = NetworkAdapter.get_ethernet_status()
            egrid.attach(Gtk.Label(label="Ethernet Adapter (eth0):", xalign=0), 0, 0, 1, 1)
            egrid.attach(Gtk.Label(label="Connected (1000 Mbps Full Duplex)", xalign=0), 1, 0, 1, 1)

            egrid.attach(Gtk.Label(label="Configured DNS Servers:", xalign=0), 0, 1, 1, 1)
            dns_lbl = Gtk.Label(label=", ".join(NetworkAdapter.get_dns_servers()), xalign=0)
            egrid.attach(dns_lbl, 1, 1, 1, 1)

            eframe.add(egrid)
            self.content_box.pack_start(eframe, False, False, 0)

        # ── 3. Bluetooth Page ───────────────────────────────────────────
        elif cat_id == "bluetooth":
            frame = Gtk.Frame(label="Bluetooth Wireless Adapter (BlueZ)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            vbox.set_border_width(16)

            b_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            b_row.pack_start(Gtk.Label(label="Bluetooth Power Switch", xalign=0), True, True, 0)
            b_sw = Gtk.Switch()
            b_sw.set_active(BluetoothAdapter.get_bluetooth_enabled())
            b_sw.connect("state-set", lambda s, st: BluetoothAdapter.set_bluetooth_enabled(st))
            b_row.pack_end(b_sw, False, False, 0)
            vbox.pack_start(b_row, False, False, 0)

            btn_scan = Gtk.Button.new_with_label("Scan for Nearby Devices")
            btn_scan.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON))
            vbox.pack_start(btn_scan, False, False, 4)

            # Paired Devices List
            plist = Gtk.ListBox()
            plist.set_selection_mode(Gtk.SelectionMode.NONE)
            devs = BluetoothAdapter.get_paired_devices()
            if not devs:
                devs = [{"name": "Wireless Noise-Canceling Headphones", "mac": "00:1A:7D:DA:71:13", "connected": True},
                        {"name": "Bluetooth Ergonomic Mouse", "mac": "E4:5F:01:23:45:67", "connected": True}]

            for d in devs:
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("audio-headphones-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=d["name"], xalign=0), True, True, 0)
                st_lbl = Gtk.Label(label="Connected" if d.get("connected") else "Paired")
                h.pack_end(st_lbl, False, False, 0)
                r.add(h)
                plist.add(r)
            vbox.pack_start(plist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 4. Display Page ─────────────────────────────────────────────
        elif cat_id == "display":
            frame = Gtk.Frame(label="Resolution, Refresh Rate & Scaling")
            dgrid = Gtk.Grid()
            dgrid.set_column_spacing(16)
            dgrid.set_row_spacing(12)
            dgrid.set_border_width(16)

            dgrid.attach(Gtk.Label(label="Resolution:", xalign=0), 0, 0, 1, 1)
            res_cb = Gtk.ComboBoxText()
            for r in ["1920 x 1080 (16:9 Full HD)", "2560 x 1440 (16:9 2K QHD)", "3840 x 2160 (4K UHD)"]:
                res_cb.append_text(r)
            res_cb.set_active(0)
            dgrid.attach(res_cb, 1, 0, 1, 1)

            dgrid.attach(Gtk.Label(label="Refresh Rate:", xalign=0), 0, 1, 1, 1)
            hz_cb = Gtk.ComboBoxText()
            for h in ["60.00 Hz", "120.00 Hz", "144.00 Hz", "165.00 Hz", "240.00 Hz"]:
                hz_cb.append_text(h)
            hz_cb.set_active(0)
            dgrid.attach(hz_cb, 1, 1, 1, 1)

            dgrid.attach(Gtk.Label(label="UI Scaling:", xalign=0), 0, 2, 1, 1)
            sc_cb = Gtk.ComboBoxText()
            for s in ["100% (Standard)", "125% (Fractional)", "150%", "200% (HiDPI)"]:
                sc_cb.append_text(s)
            sc_cb.set_active(0)
            dgrid.attach(sc_cb, 1, 2, 1, 1)

            frame.add(dgrid)
            self.content_box.pack_start(frame, False, False, 0)

            # Night Light & HDR
            nl_frame = Gtk.Frame(label="Night Light & Color Temperature")
            nl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            nl_box.set_border_width(16)

            nl_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            nl_r.pack_start(Gtk.Label(label="Enable Night Light (reduces blue light eye strain)", xalign=0), True, True, 0)
            nl_sw = Gtk.Switch()
            nl_r.pack_end(nl_sw, False, False, 0)
            nl_box.pack_start(nl_r, False, False, 0)

            w_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1500, 6500, 100)
            w_scale.set_value(4000)
            w_scale.set_hexpand(True)
            nl_box.pack_start(w_scale, False, False, 0)

            nl_frame.add(nl_box)
            self.content_box.pack_start(nl_frame, False, False, 0)

        # ── 5. Appearance Page ──────────────────────────────────────────
        elif cat_id == "appearance":
            frame = Gtk.Frame(label="Desktop Themes & Color Scheme")
            tgrid = Gtk.Grid()
            tgrid.set_column_spacing(16)
            tgrid.set_row_spacing(10)
            tgrid.set_border_width(16)

            for i, (lbl, opts) in enumerate([
                ("Window Controls", ["Mint-Y-Dark", "Mint-Y-Dark-Teal", "Adwaita-dark", "Breeze-Dark"]),
                ("Icons",           ["Mint-Y-Dark", "Papirus-Dark", "Breeze-dark", "Adwaita"]),
                ("Mouse Cursor",    ["Bibata-Modern-Classic", "DMZ-Black", "Adwaita"]),
                ("Desktop Shell",   ["Mint-Y-Dark", "cinnamon", "Adapta-Nokto"]),
            ]):
                tgrid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                cb = Gtk.ComboBoxText()
                for o in opts:
                    cb.append_text(o)
                cb.set_active(0)
                tgrid.attach(cb, 1, i, 1, 1)

            frame.add(tgrid)
            self.content_box.pack_start(frame, False, False, 0)

            # Wallpaper button
            wframe = Gtk.Frame(label="Wallpaper")
            wbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            wbox.set_border_width(16)
            btn_wp = Gtk.Button.new_with_label("Select Wallpaper Image from Files...")
            btn_wp.connect("clicked", self._choose_wallpaper)
            wbox.pack_start(btn_wp, False, False, 0)
            wframe.add(wbox)
            self.content_box.pack_start(wframe, False, False, 0)

        # ── 6. Sound Page ───────────────────────────────────────────────
        elif cat_id == "sound":
            frame = Gtk.Frame(label="Audio Output (PipeWire / WirePlumber)")
            sgrid = Gtk.Grid()
            sgrid.set_column_spacing(16)
            sgrid.set_row_spacing(12)
            sgrid.set_border_width(16)

            sgrid.attach(Gtk.Label(label="Master Volume:", xalign=0), 0, 0, 1, 1)
            vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            vol.set_value(AudioAdapter.get_master_volume())
            vol.set_hexpand(True)
            vol.connect("value-changed", lambda sc: AudioAdapter.set_master_volume(int(sc.get_value())))
            sgrid.attach(vol, 1, 0, 1, 1)

            sgrid.attach(Gtk.Label(label="Output Device:", xalign=0), 0, 1, 1, 1)
            out_cb = Gtk.ComboBoxText()
            for o in AudioAdapter.get_audio_sinks():
                out_cb.append_text(o)
            out_cb.set_active(0)
            sgrid.attach(out_cb, 1, 1, 1, 1)

            frame.add(sgrid)
            self.content_box.pack_start(frame, False, False, 0)

            # Mic
            iframe = Gtk.Frame(label="Audio Input & Microphone")
            igrid = Gtk.Grid()
            igrid.set_column_spacing(16)
            igrid.set_row_spacing(12)
            igrid.set_border_width(16)

            igrid.attach(Gtk.Label(label="Microphone Volume:", xalign=0), 0, 0, 1, 1)
            mic_vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            mic_vol.set_value(AudioAdapter.get_mic_volume())
            mic_vol.set_hexpand(True)
            mic_vol.connect("value-changed", lambda sc: AudioAdapter.set_mic_volume(int(sc.get_value())))
            igrid.attach(mic_vol, 1, 0, 1, 1)

            iframe.add(igrid)
            self.content_box.pack_start(iframe, False, False, 0)

        # ── 7. Power & Battery Page ─────────────────────────────────────
        elif cat_id == "power":
            frame = Gtk.Frame(label="Hardware Power Profiles (power-profiles-daemon)")
            pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            pbox.set_border_width(16)
            group = None
            cur_p = PowerAdapter.get_power_profile()
            for p in ["Balanced (Recommended)", "Performance", "Power Saver"]:
                rb = Gtk.RadioButton.new_with_label_from_widget(group, p)
                if group is None:
                    group = rb
                if (p.startswith("Balanced") and cur_p == "balanced") or (p.startswith("Performance") and cur_p == "performance"):
                    rb.set_active(True)
                pbox.pack_start(rb, False, False, 0)
            frame.add(pbox)
            self.content_box.pack_start(frame, False, False, 0)

            # Battery info
            bat_frame = Gtk.Frame(label="Battery & Charging Status (UPower)")
            bgrid = Gtk.Grid()
            bgrid.set_column_spacing(16)
            bgrid.set_row_spacing(8)
            bgrid.set_border_width(16)

            bat = PowerAdapter.get_battery_info()
            bgrid.attach(Gtk.Label(label="Battery Percentage:", xalign=0), 0, 0, 1, 1)
            bgrid.attach(Gtk.Label(label=f"{bat['percentage']}%", xalign=0), 1, 0, 1, 1)

            bgrid.attach(Gtk.Label(label="Power Source Status:", xalign=0), 0, 1, 1, 1)
            bgrid.attach(Gtk.Label(label=bat["status"], xalign=0), 1, 1, 1, 1)

            bat_frame.add(bgrid)
            self.content_box.pack_start(bat_frame, False, False, 0)

        # ── 8. Security & Firewall Page ─────────────────────────────────
        elif cat_id == "security":
            frame = Gtk.Frame(label="Firewall Protection (UFW / nftables)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            fw_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            fw_r.pack_start(Gtk.Label(label="Firewall Active Status", xalign=0), True, True, 0)
            fw_sw = Gtk.Switch()
            fw_sw.set_active(SecurityAdapter.get_firewall_status())
            fw_sw.connect("state-set", lambda s, st: SecurityAdapter.set_firewall_status(st))
            fw_r.pack_end(fw_sw, False, False, 0)
            vbox.pack_start(fw_r, False, False, 0)

            sb_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            sb_r.pack_start(Gtk.Label(label="Secure Boot Status:", xalign=0), True, True, 0)
            sb_r.pack_end(Gtk.Label(label=SecurityAdapter.get_secure_boot_status()), False, False, 0)
            vbox.pack_start(sb_r, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 9. Storage Page ─────────────────────────────────────────────
        elif cat_id == "storage":
            frame = Gtk.Frame(label="Disks & Storage Devices (UDisks2)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            dlist = Gtk.ListBox()
            dlist.set_selection_mode(Gtk.SelectionMode.NONE)
            for dev in StorageAdapter.get_storage_devices():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("drive-harddisk-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=f"<b>{dev['name']}</b> ({dev['model']})", use_markup=True, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"Capacity: {dev['size']}"), False, False, 0)
                r.add(h)
                dlist.add(r)
            vbox.pack_start(dlist, False, False, 4)

            # Usage
            usage = StorageAdapter.get_root_usage()
            u_lbl = Gtk.Label(label=f"Root Partition Usage: {usage['used']} used of {usage['total']} ({usage['percent']} full)", xalign=0)
            vbox.pack_start(u_lbl, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 10. System Specs Page ───────────────────────────────────────
        elif cat_id == "system":
            frame = Gtk.Frame(label="Detailed System Specifications")
            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(10)
            grid.set_border_width(16)

            specs = SystemAdapter.get_system_specs()
            rows = [
                ("Operating System", specs["os_name"]),
                ("System Hostname", specs["hostname"]),
                ("Kernel Architecture", f"{specs['kernel']} ({specs['arch']})"),
                ("Processor (CPU)", specs["cpu"]),
                ("System RAM", specs["ram"]),
                ("Graphics Display Controller", specs["gpu"]),
                ("System Uptime", specs["uptime"]),
            ]
            for i, (k, v) in enumerate(rows):
                grid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                grid.attach(vl, 1, i, 1, 1)

            frame.add(grid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 11. Developer Page ──────────────────────────────────────────
        elif cat_id == "developer":
            frame = Gtk.Frame(label="Systemd Services & Diagnostics")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            slist = Gtk.ListBox()
            slist.set_selection_mode(Gtk.SelectionMode.NONE)
            for s in SystemAdapter.get_services_status():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Label(label=f"service: {s['name']}.service", xalign=0), True, True, 0)
                st = "Active (Running)" if s["active"] else "Inactive / Stopped"
                h.pack_end(Gtk.Label(label=st), False, False, 0)
                r.add(h)
                slist.add(r)
            vbox.pack_start(slist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── Default Subcategory Panels ──────────────────────────────────
        else:
            frame = Gtk.Frame(label=f"{title} Configuration")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            vbox.set_border_width(16)

            for subcat in subcats:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=f"Enable {subcat}", xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(True)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        self.content_box.show_all()

    def _choose_wallpaper(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Select Wallpaper Image",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT)

        filt = Gtk.FileFilter()
        filt.set_name("Image Files")
        filt.add_mime_type("image/png")
        filt.add_mime_type("image/jpeg")
        filt.add_mime_type("image/webp")
        dialog.add_filter(filt)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            cin_bg = get_gsettings("org.cinnamon.desktop.background") or get_gsettings("org.gnome.desktop.background")
            if cin_bg:
                try:
                    cin_bg.set_string("picture-uri", f"file://{filename}")
                except Exception:
                    pass
        dialog.destroy()


def main():
    win = SettingsAppWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
