#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 1: Native GTK3 Settings Application
Full 3-layer architecture:
- Layer 1: Settings UI (Sidebar navigation, deep search, complete hardware panels)
- Layer 2: Settings Backend Daemon & Unified Setting Model (synth_settings_backend.py)
- Layer 3: System Integration Layer (synth_system_adapters.py: NetworkManager, BlueZ,
  PipeWire/WirePlumber, UPower, powerprofilesctl, UDisks2, UFW, xrandr, GSettings, systemd)
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
    ThemeAdapter,
    GamingPerformanceAdapter,
    StorageAdapter,
    SecurityAdapter,
    SystemAdapter,
    safe_set_gsetting,
    get_gsettings,
    run_cmd
)
from synth_settings_backend import SettingsDaemon, Setting


# ── Sidebar Navigation Categories Hierarchy ───────────────────────────────────

SIDEBAR_ITEMS = [
    ("overview",      "Overview",               "preferences-system",                      ["Quick Settings", "System Health", "Battery & Power"]),
    ("gaming",        "Gaming & Performance",   "applications-games",                      ["CPU Governor", "BORE Scheduler", "GameMode", "ZRAM Compression", "GPU Latency"]),
    ("network",       "Network",                "preferences-system-network",               ["Wi-Fi", "Ethernet", "VPN", "Proxy", "DNS", "Firewall", "Network sharing"]),
    ("bluetooth",     "Bluetooth",              "bluetooth",                                ["Devices", "Pairing", "Audio devices", "File transfer"]),
    ("display",       "Display",                "preferences-desktop-display",              ["Resolution", "Refresh rate", "Scaling", "HDR", "Night light", "Color profiles", "Multiple monitors", "VRR"]),
    ("appearance",    "Appearance",             "preferences-desktop-theme",                ["Theme", "Dark/Light", "Accent", "Wallpaper", "Icons", "Cursor", "Fonts", "Animations", "Effects"]),
    ("desktop",       "Desktop",                "cs-desktop",                             ["Panels", "Dock", "Workspaces", "Window behavior", "Virtual desktops", "Hot corners"]),
    ("sound",         "Sound",                  "multimedia-volume-control",                 ["Output", "Input", "Volume", "Per-app audio", "Microphone", "Audio effects", "Bluetooth audio"]),
    ("notifications", "Notifications",           "preferences-desktop-notification",        ["Global notifications", "Per-app permissions", "Do Not Disturb", "Notification sounds"]),
    ("keyboard",      "Keyboard",               "preferences-desktop-keyboard",              ["Layout", "Shortcuts", "Compose key", "Repeat rate", "Accessibility"]),
    ("mouse",         "Mouse & Touchpad",       "input-mouse",                              ["Pointer speed", "Acceleration", "Natural scrolling", "Gestures", "Tap-to-click", "Touchscreen / Pen"]),
    ("power",         "Power & Battery",        "preferences-system-power",                 ["Power profiles", "Sleep", "Hibernate", "Screen timeout", "Lid behavior", "Battery health", "Usage"]),
    ("users",         "Users & Accounts",       "system-users",                             ["Accounts", "Password", "Administrator privileges", "Login behavior", "Profile"]),
    ("security",      "Security",               "cs-firewall",                              ["Firewall", "Encryption", "Secure Boot status", "Permissions", "Authentication", "Screen lock"]),
    ("privacy",       "Privacy",                "preferences-system-privacy",              ["Location", "Camera", "Microphone", "Screen capture", "App permissions", "Telemetry", "Recent access"]),
    ("apps",          "Apps",                   "preferences-desktop-default-applications", ["Installed applications", "Default applications", "Startup applications", "File associations"]),
    ("packages",      "Packages & Software",    "system-software-install",                  ["Updates", "Installed packages", "Repositories", "Drivers", "Optional components"]),
    ("storage",       "Storage & Disks",        "drive-harddisk",                           ["Disks", "Partitions", "Mounts", "Filesystems", "External drives", "SMART health"]),
    ("printers",      "Printers & Scanners",    "cs-printer",                             ["Printers", "Scanners", "Print queues", "Test page"]),
    ("devices",       "Cameras & Gamepads",     "camera-video",                             ["Video devices", "Game controllers", "Calibration", "Force feedback"]),
    ("accessibility", "Accessibility",           "preferences-desktop-accessibility",       ["Screen reader", "Magnification", "High contrast", "Large text", "Sticky keys", "Slow keys"]),
    ("datetime",      "Date & Time",             "preferences-system-time",                 ["Timezone", "NTP network sync", "12/24 hour format", "Automatic time"]),
    ("region",        "Language & Region",      "cs-language",                            ["Language", "Locale", "Keyboard layouts", "Regional formats"]),
    ("system",        "System",                 "dialog-information",                       ["Hostname", "About", "Kernel", "Hardware", "Drivers", "System specs"]),
    ("developer",     "Developer",              "utilities-terminal",                       ["Developer mode", "Logs", "Services", "Debugging", "Experimental features"]),
]


class SettingsAppWindow(Gtk.Window):
    def __init__(self, initial_page="overview"):
        super().__init__(title="SynthOS System Settings")
        self.set_default_size(1180, 840)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        self.daemon = SettingsDaemon.get_instance()
        self.current_cat_id = initial_page

        # ── Header Bar ──────────────────────────────────────────────────
        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.set_title("System Settings")
        self.hb.set_subtitle("SynthOS Linux")
        self.set_titlebar(self.hb)

        # Global Deep Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search settings, Wi-Fi, CPU governor, displays, packages...")
        self.search_entry.set_width_chars(36)
        self.search_entry.connect("search-changed", self._on_global_search)
        self.hb.pack_end(self.search_entry)

        # ── Main Layout: Paned (Sidebar + Content Area) ──────────────────
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(self.main_box)

        # Left Sidebar
        self.sidebar_sw = Gtk.ScrolledWindow()
        self.sidebar_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar_sw.set_size_request(250, -1)

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

        # Select initial row
        target_row = self.sidebar_rows.get(initial_page) or self.sidebar_rows.get("overview")
        if target_row:
            self.sidebar_list.select_row(target_row)

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
        for child in self.content_box.get_children():
            child.destroy()

        # Page Header
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        h_title = Gtk.Label(xalign=0)
        safe_title = GLib.markup_escape_text(title)
        h_title.set_markup(f"<span size='xx-large' weight='bold'>{safe_title}</span>")
        header.pack_start(h_title, False, False, 0)

        h_sub = Gtk.Label(xalign=0)
        safe_subcats = GLib.markup_escape_text(' • '.join(subcats[:5]))
        h_sub.set_markup(f"<span color='#888888'>Configure {safe_subcats}</span>")
        header.pack_start(h_sub, False, False, 0)

        self.content_box.pack_start(header, False, False, 0)
        self.content_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        # ── 1. Overview ─────────────────────────────────────────────────
        if cat_id == "overview":
            card = Gtk.Frame(label="Quick System Controls")
            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(12)
            grid.set_border_width(16)

            grid.attach(Gtk.Label(label="Wi-Fi Wireless Networking:", xalign=0), 0, 0, 1, 1)
            sw_wifi = Gtk.Switch()
            sw_wifi.set_active(NetworkAdapter.get_wifi_enabled())
            sw_wifi.connect("state-set", lambda s, st: NetworkAdapter.set_wifi_enabled(st))
            grid.attach(sw_wifi, 1, 0, 1, 1)

            grid.attach(Gtk.Label(label="Bluetooth Radio:", xalign=0), 0, 1, 1, 1)
            sw_bt = Gtk.Switch()
            sw_bt.set_active(BluetoothAdapter.get_bluetooth_enabled())
            sw_bt.connect("state-set", lambda s, st: BluetoothAdapter.set_bluetooth_enabled(st))
            grid.attach(sw_bt, 1, 1, 1, 1)

            grid.attach(Gtk.Label(label="Dark Mode Color Scheme:", xalign=0), 0, 2, 1, 1)
            sw_dark = Gtk.Switch()
            sw_dark.set_active("dark" in ThemeAdapter.get_current_gtk_theme().lower())
            sw_dark.connect("state-set", lambda s, st: ThemeAdapter.set_gtk_theme("Orchis-Teal-Dark" if st else "Mint-Y"))
            grid.attach(sw_dark, 1, 2, 1, 1)

            grid.attach(Gtk.Label(label="Master Audio Output Volume:", xalign=0), 0, 3, 1, 1)
            vol = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            vol.set_value(AudioAdapter.get_master_volume())
            vol.set_hexpand(True)
            vol.connect("value-changed", lambda sc: AudioAdapter.set_master_volume(int(sc.get_value())))
            grid.attach(vol, 1, 3, 1, 1)

            card.add(grid)
            self.content_box.pack_start(card, False, False, 0)

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

        # ── 2. Gaming & Performance Tuning ──────────────────────────────
        elif cat_id == "gaming":
            frame = Gtk.Frame(label="CPU Frequency Governor & BORE Scheduler")
            ggrid = Gtk.Grid()
            ggrid.set_column_spacing(16)
            ggrid.set_row_spacing(12)
            ggrid.set_border_width(16)

            ggrid.attach(Gtk.Label(label="Active CPU Governor:", xalign=0), 0, 0, 1, 1)
            gov_cb = Gtk.ComboBoxText()
            govs = GamingPerformanceAdapter.get_cpu_governors()
            cur_gov = GamingPerformanceAdapter.get_current_governor()
            for g in govs:
                gov_cb.append_text(g)
            if cur_gov in govs:
                gov_cb.set_active(govs.index(cur_gov))
            else:
                gov_cb.set_active(0)
            gov_cb.connect("changed", lambda cb: GamingPerformanceAdapter.set_cpu_governor(cb.get_active_text()))
            ggrid.attach(gov_cb, 1, 0, 1, 1)

            ggrid.attach(Gtk.Label(label="BORE Latency Responsiveness:", xalign=0), 0, 1, 1, 1)
            bore_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
            bore_scale.set_value(8)
            bore_scale.set_hexpand(True)
            ggrid.attach(bore_scale, 1, 1, 1, 1)

            ggrid.attach(Gtk.Label(label="Feral GameMode Auto-Priority:", xalign=0), 0, 2, 1, 1)
            gm_sw = Gtk.Switch()
            gm_sw.set_active(GamingPerformanceAdapter.is_gamemode_available())
            ggrid.attach(gm_sw, 1, 2, 1, 1)

            ggrid.attach(Gtk.Label(label="Ananicy-Cpp Auto-Nice Rules:", xalign=0), 0, 3, 1, 1)
            an_sw = Gtk.Switch()
            an_sw.set_active(GamingPerformanceAdapter.is_ananicy_running())
            ggrid.attach(an_sw, 1, 3, 1, 1)

            frame.add(ggrid)
            self.content_box.pack_start(frame, False, False, 0)

            # ZRAM Status
            zframe = Gtk.Frame(label="ZRAM High-Speed RAM Swap Compression")
            zgrid = Gtk.Grid()
            zgrid.set_column_spacing(24)
            zgrid.set_row_spacing(8)
            zgrid.set_border_width(16)

            zdata = GamingPerformanceAdapter.get_zram_status()
            zgrid.attach(Gtk.Label(label="<b>ZRAM Device</b>", use_markup=True, xalign=0), 0, 0, 1, 1)
            zgrid.attach(Gtk.Label(label=zdata["name"], xalign=0), 1, 0, 1, 1)

            zgrid.attach(Gtk.Label(label="<b>Allocated Size</b>", use_markup=True, xalign=0), 0, 1, 1, 1)
            zgrid.attach(Gtk.Label(label=zdata["disksize"], xalign=0), 1, 1, 1, 1)

            zgrid.attach(Gtk.Label(label="<b>Compression Algorithm</b>", use_markup=True, xalign=0), 0, 2, 1, 1)
            zgrid.attach(Gtk.Label(label=f"{zdata['algorithm'].upper()} (Real-time Compressed)", xalign=0), 1, 2, 1, 1)

            zframe.add(zgrid)
            self.content_box.pack_start(zframe, False, False, 0)

        # ── 3. Network ──────────────────────────────────────────────────
        elif cat_id == "network":
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

            nlist = Gtk.ListBox()
            nlist.set_selection_mode(Gtk.SelectionMode.NONE)
            nets = NetworkAdapter.get_wifi_networks()
            for net in nets:
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=net["ssid"], xalign=0), True, True, 0)

                if net.get("connected"):
                    badge = Gtk.Label()
                    badge.set_markup("<span color='#2ecc71'><b>Connected</b></span>")
                    h.pack_end(badge, False, False, 0)
                else:
                    btn_conn = Gtk.Button.new_with_label("Connect")
                    btn_conn.connect("clicked", lambda b, ssid=net["ssid"]: self._show_wifi_connect_dialog(ssid))
                    h.pack_end(btn_conn, False, False, 0)

                h.pack_end(Gtk.Label(label=f"{net['signal']}% • {net['security']}"), False, False, 8)
                r.add(h)
                nlist.add(r)
            wvbox.pack_start(nlist, False, False, 4)
            wframe.add(wvbox)
            self.content_box.pack_start(wframe, False, False, 0)

            # VPN Frame
            vframe = Gtk.Frame(label="VPN & Secure Connections")
            vvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            vvbox.set_border_width(16)
            for vpn in NetworkAdapter.get_vpn_connections():
                vr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                vr.pack_start(Gtk.Label(label=f"<b>{vpn['name']}</b> ({vpn['type']})", use_markup=True, xalign=0), True, True, 0)
                vsw = Gtk.Switch()
                vsw.set_active(vpn.get("connected", False))
                vr.pack_end(vsw, False, False, 0)
                vvbox.pack_start(vr, False, False, 0)

            btn_add_vpn = Gtk.Button.new_with_label("Add New VPN Profile (WireGuard / OpenVPN)...")
            btn_add_vpn.connect("clicked", self._show_add_vpn_dialog)
            vvbox.pack_start(btn_add_vpn, False, False, 4)
            vframe.add(vvbox)
            self.content_box.pack_start(vframe, False, False, 0)

        # ── 4. Bluetooth ────────────────────────────────────────────────
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

            plist = Gtk.ListBox()
            plist.set_selection_mode(Gtk.SelectionMode.NONE)
            devs = BluetoothAdapter.get_paired_devices()
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

        # ── 5. Display ──────────────────────────────────────────────────
        elif cat_id == "display":
            monitors = DisplayAdapter.get_connected_monitors()

            frame = Gtk.Frame(label="Monitors, Resolution & Refresh Rate (xrandr / DRM)")
            dgrid = Gtk.Grid()
            dgrid.set_column_spacing(16)
            dgrid.set_row_spacing(12)
            dgrid.set_border_width(16)

            # Monitor Selector
            dgrid.attach(Gtk.Label(label="Select Display Monitor:", xalign=0), 0, 0, 1, 1)
            mon_cb = Gtk.ComboBoxText()
            for mname, mdata in monitors.items():
                label_txt = f"{mname} {'(Primary)' if mdata['primary'] else ''} — {mdata['current_res']} @ {mdata['current_hz']} Hz"
                mon_cb.append_text(label_txt)
            mon_cb.set_active(0)
            dgrid.attach(mon_cb, 1, 0, 1, 1)

            # Resolution
            dgrid.attach(Gtk.Label(label="Screen Resolution:", xalign=0), 0, 1, 1, 1)
            res_cb = Gtk.ComboBoxText()
            prim_name = list(monitors.keys())[0]
            unique_resolutions = sorted(list(set([m[0] for m in monitors[prim_name]["modes"]])), reverse=True)
            for r in unique_resolutions:
                res_cb.append_text(r)
            if not unique_resolutions:
                res_cb.append_text("1920x1080")
            res_cb.set_active(0)
            dgrid.attach(res_cb, 1, 1, 1, 1)

            # Refresh Rate
            dgrid.attach(Gtk.Label(label="Refresh Rate:", xalign=0), 0, 2, 1, 1)
            hz_cb = Gtk.ComboBoxText()
            rates = sorted(list(set([m[1] for m in monitors[prim_name]["modes"] if m[1]])), reverse=True)
            for h in rates:
                hz_cb.append_text(f"{h} Hz")
            if not rates:
                hz_cb.append_text("60.00 Hz")
            hz_cb.set_active(0)
            dgrid.attach(hz_cb, 1, 2, 1, 1)

            # Scaling
            dgrid.attach(Gtk.Label(label="UI Scaling:", xalign=0), 0, 3, 1, 1)
            sc_cb = Gtk.ComboBoxText()
            for s in ["100% (Standard)", "125% (Fractional)", "150%", "200% (HiDPI)"]:
                sc_cb.append_text(s)
            sc_cb.set_active(0)
            sc_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.interface", "text-scaling-factor", 1.25 if "125" in cb.get_active_text() else (1.5 if "150" in cb.get_active_text() else (2.0 if "200" in cb.get_active_text() else 1.0))))
            dgrid.attach(sc_cb, 1, 3, 1, 1)

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

        # ── 6. Appearance ───────────────────────────────────────────────
        elif cat_id == "appearance":
            installed_themes = ThemeAdapter.get_installed_themes()
            installed_icons = ThemeAdapter.get_installed_icons()
            cur_theme = ThemeAdapter.get_current_gtk_theme()

            frame = Gtk.Frame(label="Desktop Themes & Color Scheme")
            tgrid = Gtk.Grid()
            tgrid.set_column_spacing(16)
            tgrid.set_row_spacing(10)
            tgrid.set_border_width(16)

            # Controls Theme
            tgrid.attach(Gtk.Label(label="Window Controls (GTK):", xalign=0), 0, 0, 1, 1)
            theme_cb = Gtk.ComboBoxText()
            theme_idx = 0
            for i, t in enumerate(installed_themes):
                theme_cb.append_text(t)
                if t == cur_theme:
                    theme_idx = i
            theme_cb.set_active(theme_idx)
            theme_cb.connect("changed", lambda cb: ThemeAdapter.set_gtk_theme(cb.get_active_text()))
            tgrid.attach(theme_cb, 1, 0, 1, 1)

            # Icon Theme
            tgrid.attach(Gtk.Label(label="Icon Set:", xalign=0), 0, 1, 1, 1)
            icon_cb = Gtk.ComboBoxText()
            for i, ic in enumerate(installed_icons):
                icon_cb.append_text(ic)
            icon_cb.set_active(0)
            icon_cb.connect("changed", lambda cb: ThemeAdapter.set_icon_theme(cb.get_active_text()))
            tgrid.attach(icon_cb, 1, 1, 1, 1)

            # Mouse Cursor
            tgrid.attach(Gtk.Label(label="Mouse Cursor:", xalign=0), 0, 2, 1, 1)
            cur_cb = Gtk.ComboBoxText()
            for c in ["Bibata-Modern-Classic", "DMZ-Black", "Adwaita", "breeze_cursors"]:
                cur_cb.append_text(c)
            cur_cb.set_active(0)
            cur_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.interface", "cursor-theme", cb.get_active_text()))
            tgrid.attach(cur_cb, 1, 2, 1, 1)

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

        # ── 7. Desktop ──────────────────────────────────────────────────
        elif cat_id == "desktop":
            frame = Gtk.Frame(label="Panels & Taskbar Layout")
            pgrid = Gtk.Grid()
            pgrid.set_column_spacing(16)
            pgrid.set_row_spacing(10)
            pgrid.set_border_width(16)

            pgrid.attach(Gtk.Label(label="Window Titlebar Layout:", xalign=0), 0, 0, 1, 1)
            layout_cb = Gtk.ComboBoxText()
            layout_cb.append_text("Right Side (menu:minimize,maximize,close)")
            layout_cb.append_text("Left Side (close,minimize,maximize:menu)")
            layout_cb.set_active(0)
            layout_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.wm.preferences", "button-layout", "menu:minimize,maximize,close" if cb.get_active() == 0 else "close,minimize,maximize:menu"))
            pgrid.attach(layout_cb, 1, 0, 1, 1)

            pgrid.attach(Gtk.Label(label="Window Focus Mode:", xalign=0), 0, 1, 1, 1)
            focus_cb = Gtk.ComboBoxText()
            focus_cb.append_text("Click to Focus (Standard)")
            focus_cb.append_text("Focus Follows Mouse (Sloppy)")
            focus_cb.set_active(0)
            focus_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.wm.preferences", "focus-mode", "click" if cb.get_active() == 0 else "sloppy"))
            pgrid.attach(focus_cb, 1, 1, 1, 1)

            pgrid.attach(Gtk.Label(label="Number of Workspaces:", xalign=0), 0, 2, 1, 1)
            ws_spin = Gtk.SpinButton.new_with_range(1, 16, 1)
            ws_spin.set_value(4)
            ws_spin.connect("value-changed", lambda sp: safe_set_gsetting("org.cinnamon.desktop.wm.preferences", "num-workspaces", int(sp.get_value())))
            pgrid.attach(ws_spin, 1, 2, 1, 1)

            frame.add(pgrid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 8. Sound ────────────────────────────────────────────────────
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

            # Per-app audio mixer
            mix_frame = Gtk.Frame(label="Application Audio Mixer")
            mix_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            mix_box.set_border_width(16)
            for app in AudioAdapter.get_app_audio_streams():
                ar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                ar.pack_start(Gtk.Label(label=app["name"], xalign=0), False, False, 0)
                ascale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
                ascale.set_value(app["volume"])
                ascale.set_hexpand(True)
                ar.pack_start(ascale, True, True, 0)
                mix_box.pack_start(ar, False, False, 0)
            mix_frame.add(mix_box)
            self.content_box.pack_start(mix_frame, False, False, 0)

        # ── 9. Notifications ────────────────────────────────────────────
        elif cat_id == "notifications":
            frame = Gtk.Frame(label="Notification Preferences")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            n_sw1 = Gtk.Switch()
            n_sw1.set_active(True)
            n_sw1.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.notifications", "display-notifications", st))
            r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r1.pack_start(Gtk.Label(label="Enable popup alerts & notifications", xalign=0), True, True, 0)
            r1.pack_end(n_sw1, False, False, 0)
            vbox.pack_start(r1, False, False, 0)

            n_sw2 = Gtk.Switch()
            n_sw2.set_active(True)
            n_sw2.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.notifications", "fullscreen-notifications", not st))
            r2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r2.pack_start(Gtk.Label(label="Hide notification popups in full-screen games", xalign=0), True, True, 0)
            r2.pack_end(n_sw2, False, False, 0)
            vbox.pack_start(r2, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 10. Keyboard ────────────────────────────────────────────────
        elif cat_id == "keyboard":
            frame = Gtk.Frame(label="Key Repeat & Input Behavior")
            kgrid = Gtk.Grid()
            kgrid.set_column_spacing(16)
            kgrid.set_row_spacing(12)
            kgrid.set_border_width(16)

            kgrid.attach(Gtk.Label(label="Repeat Delay (ms):", xalign=0), 0, 0, 1, 1)
            del_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 100, 1000, 50)
            del_scale.set_value(400)
            del_scale.set_hexpand(True)
            del_scale.connect("value-changed", lambda sc: safe_set_gsetting("org.cinnamon.desktop.peripherals.keyboard", "delay", int(sc.get_value())))
            kgrid.attach(del_scale, 1, 0, 1, 1)

            kgrid.attach(Gtk.Label(label="Repeat Speed (chars/sec):", xalign=0), 0, 1, 1, 1)
            spd_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
            spd_scale.set_value(50)
            spd_scale.set_hexpand(True)
            spd_scale.connect("value-changed", lambda sc: safe_set_gsetting("org.cinnamon.desktop.peripherals.keyboard", "repeat-interval", int(sc.get_value())))
            kgrid.attach(spd_scale, 1, 1, 1, 1)

            kgrid.attach(Gtk.Label(label="Cursor Blinking in Text Fields:", xalign=0), 0, 2, 1, 1)
            blink_sw = Gtk.Switch()
            blink_sw.set_active(True)
            blink_sw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "cursor-blink", st))
            kgrid.attach(blink_sw, 1, 2, 1, 1)

            frame.add(kgrid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 11. Mouse & Touchpad ────────────────────────────────────────
        elif cat_id == "mouse":
            frame = Gtk.Frame(label="Pointer & Touchpad Behavior")
            mgrid = Gtk.Grid()
            mgrid.set_column_spacing(16)
            mgrid.set_row_spacing(10)
            mgrid.set_border_width(16)

            mgrid.attach(Gtk.Label(label="Pointer Speed:", xalign=0), 0, 0, 1, 1)
            ps_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1.0, 1.0, 0.1)
            ps_scale.set_value(0.0)
            ps_scale.set_hexpand(True)
            ps_scale.connect("value-changed", lambda sc: safe_set_gsetting("org.cinnamon.desktop.peripherals.mouse", "speed", float(sc.get_value())))
            mgrid.attach(ps_scale, 1, 0, 1, 1)

            mgrid.attach(Gtk.Label(label="Natural Scrolling (Reverse direction):", xalign=0), 0, 1, 1, 1)
            nsw = Gtk.Switch()
            nsw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.peripherals.mouse", "natural-scroll", st))
            mgrid.attach(nsw, 1, 1, 1, 1)

            mgrid.attach(Gtk.Label(label="Touchpad Tap to Click:", xalign=0), 0, 2, 1, 1)
            tsw = Gtk.Switch()
            tsw.set_active(True)
            tsw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.peripherals.touchpad", "tap-to-click", st))
            mgrid.attach(tsw, 1, 2, 1, 1)

            frame.add(mgrid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 12. Power & Battery ─────────────────────────────────────────
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
                rb.connect("toggled", lambda b, mode=p: PowerAdapter.set_power_profile("performance" if "Performance" in mode else ("power-saver" if "Power" in mode else "balanced")) if b.get_active() else None)
                pbox.pack_start(rb, False, False, 0)
            frame.add(pbox)
            self.content_box.pack_start(frame, False, False, 0)

            # Timeout frame
            to_frame = Gtk.Frame(label="Sleep & Inactivity Timeouts")
            to_grid = Gtk.Grid()
            to_grid.set_column_spacing(16)
            to_grid.set_row_spacing(10)
            to_grid.set_border_width(16)

            to_grid.attach(Gtk.Label(label="Turn off screen after inactivity:", xalign=0), 0, 0, 1, 1)
            to_cb = Gtk.ComboBoxText()
            for t in ["5 minutes", "10 minutes", "15 minutes", "30 minutes", "1 hour", "Never"]:
                to_cb.append_text(t)
            to_cb.set_active(1)
            to_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.session", "idle-delay", 300 if "5" in cb.get_active_text() else (600 if "10" in cb.get_active_text() else (900 if "15" in cb.get_active_text() else 0))))
            to_grid.attach(to_cb, 1, 0, 1, 1)

            to_frame.add(to_grid)
            self.content_box.pack_start(to_frame, False, False, 0)

        # ── 13. Users & Accounts ────────────────────────────────────────
        elif cat_id == "users":
            frame = Gtk.Frame(label="User Accounts & Permissions")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            ulist = Gtk.ListBox()
            ulist.set_selection_mode(Gtk.SelectionMode.NONE)
            row = Gtk.ListBoxRow()
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            h.set_border_width(8)
            h.pack_start(Gtk.Image.new_from_icon_name("system-users", Gtk.IconSize.BUTTON), False, False, 0)
            h.pack_start(Gtk.Label(label=f"User: <b>{os.environ.get('USER', 'jewboy420')}</b> (Administrator)", use_markup=True, xalign=0), True, True, 0)
            h.pack_end(Gtk.Label(label="Sudo Privileges: Yes"), False, False, 0)
            row.add(h)
            ulist.add(row)
            vbox.pack_start(ulist, False, False, 4)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_pwd = Gtk.Button.new_with_label("Change Password...")
            btn_add = Gtk.Button.new_with_label("Add New Account...")
            btn_add.connect("clicked", self._show_add_user_dialog)
            btn_box.pack_start(btn_pwd, False, False, 0)
            btn_box.pack_start(btn_add, False, False, 0)
            vbox.pack_start(btn_box, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 14. Security ────────────────────────────────────────────────
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

            btn_add_rule = Gtk.Button.new_with_label("Add Port Rule (Allow / Block)...")
            btn_add_rule.connect("clicked", self._show_add_firewall_rule_dialog)
            vbox.pack_start(btn_add_rule, False, False, 4)

            sb_r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            sb_r.pack_start(Gtk.Label(label="Secure Boot Status:", xalign=0), True, True, 0)
            sb_r.pack_end(Gtk.Label(label=SecurityAdapter.get_secure_boot_status()), False, False, 0)
            vbox.pack_start(sb_r, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 15. Privacy ─────────────────────────────────────────────────
        elif cat_id == "privacy":
            frame = Gtk.Frame(label="Privacy & Telemetry Controls")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            r_sw = Gtk.Switch()
            r_sw.set_active(True)
            r_sw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.privacy", "remember-recent-files", st))
            r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r.pack_start(Gtk.Label(label="Remember recently opened documents", xalign=0), True, True, 0)
            r.pack_end(r_sw, False, False, 0)
            vbox.pack_start(r, False, False, 0)

            btn_clr = Gtk.Button.new_with_label("Clear Activity History Now")
            btn_clr.connect("clicked", lambda b: run_cmd("rm -f ~/.local/share/recently-used.xbel"))
            vbox.pack_start(btn_clr, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 16. Apps ────────────────────────────────────────────────────
        elif cat_id == "apps":
            frame = Gtk.Frame(label="Default System Applications")
            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(10)
            grid.set_border_width(16)

            for i, (lbl, opts) in enumerate([
                ("Web Browser",   ["Firefox", "Chromium", "GNOME Web", "Brave", "Google Chrome"]),
                ("File Manager",  ["Nemo", "Thunar", "Nautilus", "Dolphin"]),
                ("Terminal",      ["Kitty", "Alacritty", "GNOME Terminal", "Tilix"]),
                ("Text Editor",   ["xed", "gedit", "Kate", "VSCode", "nano"]),
                ("Music Player",  ["Rhythmbox", "VLC media player", "Audacious", "Spotify"]),
                ("Video Player",  ["Celluloid", "VLC media player", "MPV"]),
            ]):
                grid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                cb = Gtk.ComboBoxText()
                for o in opts:
                    cb.append_text(o)
                cb.set_active(0)
                grid.attach(cb, 1, i, 1, 1)

            frame.add(grid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 17. Packages & Software ─────────────────────────────────────
        elif cat_id == "packages":
            frame = Gtk.Frame(label="Package Manager & Repositories (dpkg / apt)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            u_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            u_row.pack_start(Gtk.Label(label="System Packages Status: 100% Up to Date", xalign=0), True, True, 0)
            btn_chk = Gtk.Button.new_with_label("Check for Updates")
            btn_chk.connect("clicked", lambda b: subprocess.Popen(["pkexec", "apt", "update"]))
            u_row.pack_end(btn_chk, False, False, 0)
            vbox.pack_start(u_row, False, False, 0)

            # Core Packages Table
            plist = Gtk.ListBox()
            plist.set_selection_mode(Gtk.SelectionMode.NONE)
            for pkg in SystemAdapter.get_installed_packages_sample(limit=12):
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(6)
                h.pack_start(Gtk.Label(label=f"<b>{pkg['name']}</b>", use_markup=True, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"v{pkg['version']} • [{pkg['section']}]"), False, False, 0)
                r.add(h)
                plist.add(r)
            vbox.pack_start(plist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 18. Storage & Disks ─────────────────────────────────────────
        elif cat_id == "storage":
            frame = Gtk.Frame(label="Disks & Storage Partitions (UDisks2)")
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

            usage = StorageAdapter.get_root_usage()
            u_lbl = Gtk.Label(label=f"Root Partition (/): {usage['used']} used of {usage['total']} ({usage['percent']} full)", xalign=0)
            vbox.pack_start(u_lbl, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 19. Printers & Scanners ─────────────────────────────────────
        elif cat_id == "printers":
            frame = Gtk.Frame(label="Printers & Scanners (CUPS)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            plist = Gtk.ListBox()
            plist.set_selection_mode(Gtk.SelectionMode.NONE)
            for p in SystemAdapter.get_printers():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("printer-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=f"<b>{p['name']}</b>", use_markup=True, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=p["status"]), False, False, 0)
                r.add(h)
                plist.add(r)
            vbox.pack_start(plist, False, False, 4)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_add = Gtk.Button.new_with_label("Add New Printer...")
            btn_test = Gtk.Button.new_with_label("Print Test Page")
            btn_box.pack_start(btn_add, False, False, 0)
            btn_box.pack_start(btn_test, False, False, 0)
            vbox.pack_start(btn_box, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 20. Cameras & Gamepads ──────────────────────────────────────
        elif cat_id == "devices":
            frame = Gtk.Frame(label="Input Peripherals & Gamepad Interfaces")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            glist = Gtk.ListBox()
            glist.set_selection_mode(Gtk.SelectionMode.NONE)
            for dev_str in SystemAdapter.get_input_devices():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Image.new_from_icon_name("input-gaming-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=dev_str, xalign=0), True, True, 0)
                r.add(h)
                glist.add(r)
            vbox.pack_start(glist, False, False, 4)

            btn_cal = Gtk.Button.new_with_label("Calibrate Controller & Test Vibration")
            vbox.pack_start(btn_cal, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 21. Accessibility ───────────────────────────────────────────
        elif cat_id == "accessibility":
            frame = Gtk.Frame(label="Visual & Input Assistance")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            hc_sw = Gtk.Switch()
            hc_sw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "high-contrast", st))
            r_hc = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_hc.pack_start(Gtk.Label(label="High Contrast Display Mode", xalign=0), True, True, 0)
            r_hc.pack_end(hc_sw, False, False, 0)
            vbox.pack_start(r_hc, False, False, 0)

            lt_sw = Gtk.Switch()
            lt_sw.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "text-scaling-factor", 1.25 if st else 1.0))
            r_lt = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_lt.pack_start(Gtk.Label(label="Large Text Display", xalign=0), True, True, 0)
            r_lt.pack_end(lt_sw, False, False, 0)
            vbox.pack_start(r_lt, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 22. Date & Time ─────────────────────────────────────────────
        elif cat_id == "datetime":
            frame = Gtk.Frame(label="Clock & Network Time (systemd-timesyncd)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            sw_24h = Gtk.Switch()
            sw_24h.set_active(True)
            sw_24h.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-use-24h", st))
            r_24h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_24h.pack_start(Gtk.Label(label="Use 24-hour clock format", xalign=0), True, True, 0)
            r_24h.pack_end(sw_24h, False, False, 0)
            vbox.pack_start(r_24h, False, False, 0)

            sw_sec = Gtk.Switch()
            sw_sec.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-show-seconds", st))
            r_sec = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_sec.pack_start(Gtk.Label(label="Show seconds in clock", xalign=0), True, True, 0)
            r_sec.pack_end(sw_sec, False, False, 0)
            vbox.pack_start(r_sec, False, False, 0)

            sw_date = Gtk.Switch()
            sw_date.set_active(True)
            sw_date.connect("state-set", lambda s, st: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-show-date", st))
            r_date = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_date.pack_start(Gtk.Label(label="Show date in taskbar", xalign=0), True, True, 0)
            r_date.pack_end(sw_date, False, False, 0)
            vbox.pack_start(r_date, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 23. Language & Region ───────────────────────────────────────
        elif cat_id == "region":
            frame = Gtk.Frame(label="System Locale & Regional Formats")
            rgrid = Gtk.Grid()
            rgrid.set_column_spacing(16)
            rgrid.set_row_spacing(10)
            rgrid.set_border_width(16)

            rgrid.attach(Gtk.Label(label="Display Language:", xalign=0), 0, 0, 1, 1)
            lang_cb = Gtk.ComboBoxText()
            for l in ["English (United States)", "English (United Kingdom)", "German (Deutsch)", "French (Français)", "Spanish (Español)"]:
                lang_cb.append_text(l)
            lang_cb.set_active(0)
            rgrid.attach(lang_cb, 1, 0, 1, 1)

            rgrid.attach(Gtk.Label(label="Number & Currency Formats:", xalign=0), 0, 1, 1, 1)
            fmt_cb = Gtk.ComboBoxText()
            for f in ["United States ($ USD, MM/DD/YYYY)", "United Kingdom (£ GBP, DD/MM/YYYY)", "European (€ EUR, DD.MM.YYYY)"]:
                fmt_cb.append_text(f)
            fmt_cb.set_active(0)
            rgrid.attach(fmt_cb, 1, 1, 1, 1)

            frame.add(rgrid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 24. System ──────────────────────────────────────────────────
        elif cat_id == "system":
            frame = Gtk.Frame(label="System Specifications")
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

            btn_copy = Gtk.Button.new_with_label("Copy System Specs to Clipboard")
            btn_copy.connect("clicked", lambda b: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text("\n".join([f"{k}: {v}" for k, v in rows]), -1))
            grid.attach(btn_copy, 0, len(rows), 2, 1)

            frame.add(grid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 25. Developer ───────────────────────────────────────────────
        elif cat_id == "developer":
            frame = Gtk.Frame(label="Systemd Services & Diagnostic Tools")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            slist = Gtk.ListBox()
            slist.set_selection_mode(Gtk.SelectionMode.NONE)
            for s in SystemAdapter.get_services_status():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Label(label=f"service: <b>{s['name']}.service</b>", use_markup=True, xalign=0), True, True, 0)
                st = "Active (Running)" if s["active"] else "Inactive / Stopped"
                h.pack_end(Gtk.Label(label=st), False, False, 0)

                btn_restart = Gtk.Button.new_with_label("Restart")
                btn_restart.connect("clicked", lambda b, sname=s["name"]: SystemAdapter.service_action(sname, "restart"))
                h.pack_end(btn_restart, False, False, 4)

                r.add(h)
                slist.add(r)
            vbox.pack_start(slist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        self.content_box.show_all()

    # ── Interactive Modals & Dialogs ─────────────────────────────────────────

    def _show_wifi_connect_dialog(self, ssid):
        dialog = Gtk.Dialog(title=f"Connect to {ssid}", parent=self, flags=0)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button("Connect", Gtk.ResponseType.OK)
        dialog.set_default_size(360, 160)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(16)

        box.pack_start(Gtk.Label(label=f"Enter WPA/WPA2/WPA3 password for '{ssid}':", xalign=0), False, False, 0)
        pwd_entry = Gtk.Entry()
        pwd_entry.set_visibility(False)
        box.pack_start(pwd_entry, False, False, 0)

        show_cb = Gtk.CheckButton(label="Show Password")
        show_cb.connect("toggled", lambda cb: pwd_entry.set_visibility(cb.get_active()))
        box.pack_start(show_cb, False, False, 0)

        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            password = pwd_entry.get_text()
            NetworkAdapter.connect_wifi(ssid, password)
            self._render_category_page("network", "Network", ["Wi-Fi", "Ethernet", "VPN"])
        dialog.destroy()

    def _show_add_vpn_dialog(self, btn):
        dialog = Gtk.FileChooserDialog(
            title="Import VPN Profile (.conf / .ovpn)",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT)

        filt = Gtk.FileFilter()
        filt.set_name("VPN Configs (*.conf, *.ovpn)")
        filt.add_pattern("*.conf")
        filt.add_pattern("*.ovpn")
        dialog.add_filter(filt)

        if dialog.run() == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            subprocess.run(f"nmcli connection import type wireguard file {shlex.quote(filename)} || nmcli connection import type openvpn file {shlex.quote(filename)}", shell=True)
            self._render_category_page("network", "Network", ["Wi-Fi", "Ethernet", "VPN"])
        dialog.destroy()

    def _show_add_firewall_rule_dialog(self, btn):
        dialog = Gtk.Dialog(title="Add Firewall Rule", parent=self, flags=0)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button("Apply Rule", Gtk.ResponseType.OK)
        dialog.set_default_size(360, 200)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(16)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)

        grid.attach(Gtk.Label(label="Port Number / Service:", xalign=0), 0, 0, 1, 1)
        port_entry = Gtk.Entry()
        port_entry.set_text("22")
        grid.attach(port_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Protocol:", xalign=0), 0, 1, 1, 1)
        proto_cb = Gtk.ComboBoxText()
        proto_cb.append_text("tcp")
        proto_cb.append_text("udp")
        proto_cb.set_active(0)
        grid.attach(proto_cb, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Action:", xalign=0), 0, 2, 1, 1)
        act_cb = Gtk.ComboBoxText()
        act_cb.append_text("allow")
        act_cb.append_text("deny")
        act_cb.set_active(0)
        grid.attach(act_cb, 1, 2, 1, 1)

        box.pack_start(grid, False, False, 0)
        dialog.show_all()

        if dialog.run() == Gtk.ResponseType.OK:
            SecurityAdapter.add_firewall_rule(port_entry.get_text().strip(), proto_cb.get_active_text(), act_cb.get_active_text())
            self._render_category_page("security", "Security", ["Firewall", "Encryption"])
        dialog.destroy()

    def _show_add_user_dialog(self, btn):
        dialog = Gtk.Dialog(title="Add New User Account", parent=self, flags=0)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button("Create User", Gtk.ResponseType.OK)
        dialog.set_default_size(380, 220)

        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_border_width(16)

        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(10)

        grid.attach(Gtk.Label(label="Username:", xalign=0), 0, 0, 1, 1)
        u_entry = Gtk.Entry()
        grid.attach(u_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Full Name:", xalign=0), 0, 1, 1, 1)
        f_entry = Gtk.Entry()
        grid.attach(f_entry, 1, 1, 1, 1)

        grid.attach(Gtk.Label(label="Administrator:", xalign=0), 0, 2, 1, 1)
        admin_cb = Gtk.CheckButton(label="Grant sudo root privileges")
        grid.attach(admin_cb, 1, 2, 1, 1)

        box.pack_start(grid, False, False, 0)
        dialog.show_all()

        if dialog.run() == Gtk.ResponseType.OK:
            un = u_entry.get_text().strip()
            fn = f_entry.get_text().strip()
            if un:
                SecurityAdapter.add_system_user(un, fn, admin_cb.get_active())
                self._render_category_page("users", "Users & Accounts", ["Accounts", "Password"])
        dialog.destroy()

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
    initial_page = "overview"
    for arg in sys.argv[1:]:
        if arg.startswith("--page="):
            initial_page = arg.split("=", 1)[1]
        elif arg.startswith("synth-settings://"):
            initial_page = arg.replace("synth-settings://", "")

    win = SettingsAppWindow(initial_page=initial_page)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
