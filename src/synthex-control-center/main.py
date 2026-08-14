#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Layer 1: Native GTK3 Settings Application
Full 3-layer architecture:
- Layer 1: Settings UI (Visual multi-monitor canvas, confirmation countdown with rollback,
  tier filters, deep search, hardware control surfaces)
- Layer 2: Settings Backend Daemon & Unified Setting Model (synth_settings_backend.py)
- Layer 3: System Integration Layer (synth_system_adapters.py: DRM/KMS, xrandr, NetworkManager,
  BlueZ, PipeWire/WirePlumber, UPower, powerprofilesctl, UDisks2, UFW, GSettings, systemd)
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
    PrivacyAdapter,
    safe_set_gsetting,
    get_gsettings,
    run_cmd
)
from synth_settings_backend import SettingsDaemon, Setting


# ── Sidebar Navigation Categories Hierarchy ───────────────────────────────────

SIDEBAR_ITEMS = [
    ("overview",      "Overview",               "preferences-system",                      ["Quick Settings", "System Health", "Battery & Power"]),
    ("display",       "Display",                "preferences-desktop-display",              ["Resolution", "Refresh rate", "Arrangement", "Scaling", "HDR", "Night light", "VRR", "Rotation"]),
    ("gaming",        "Gaming & Performance",   "applications-games",                      ["CPU Governor", "BORE Scheduler", "GameMode", "ZRAM Compression", "GPU Latency"]),
    ("network",       "Network",                "preferences-system-network",               ["Wi-Fi", "Ethernet", "VPN", "Proxy", "DNS", "Firewall", "Saved Networks"]),
    ("bluetooth",     "Bluetooth",              "bluetooth",                                ["Devices", "Pairing", "Audio devices", "Codecs", "File transfer"]),
    ("sound",         "Sound",                  "multimedia-volume-control",                 ["Output", "Input", "Volume", "Per-app audio", "Microphone", "Audio test", "PipeWire"]),
    ("appearance",    "Appearance",             "preferences-desktop-theme",                ["Theme", "Dark/Light", "Accent", "Wallpaper", "Icons", "Cursor", "Fonts", "Animations"]),
    ("desktop",       "Desktop",                "cs-desktop",                             ["Panels", "Dock", "Workspaces", "Window behavior", "Virtual desktops", "Hot corners"]),
    ("notifications", "Notifications",           "preferences-desktop-notification",        ["Global notifications", "Per-app permissions", "Do Not Disturb", "Notification sounds"]),
    ("keyboard",      "Keyboard",               "preferences-desktop-keyboard",              ["Layout", "Shortcuts", "Compose key", "Repeat rate", "Accessibility"]),
    ("mouse",         "Mouse & Touchpad",       "input-mouse",                              ["Pointer speed", "Acceleration", "Natural scrolling", "Gestures", "Tap-to-click"]),
    ("power",         "Power & Battery",        "preferences-system-power",                 ["Power profiles", "Sleep", "Hibernate", "Screen timeout", "Lid behavior", "Battery health"]),
    ("storage",       "Storage & Disks",        "drive-harddisk",                           ["Disks", "Partitions", "Mounts", "Filesystems", "External drives", "TRIM"]),
    ("users",         "Users & Accounts",       "system-users",                             ["Accounts", "Password", "Administrator privileges", "Login behavior", "Profile"]),
    ("security",      "Security",               "cs-firewall",                              ["Firewall", "Encryption", "Secure Boot status", "Permissions", "Authentication", "Screen lock"]),
    ("privacy",       "Privacy",                "preferences-system-privacy",              ["Location", "Camera", "Microphone", "Screen capture", "App permissions", "Telemetry"]),
    ("apps",          "Apps & Defaults",        "preferences-desktop-default-applications", ["Installed applications", "Default applications", "Startup applications", "File associations"]),
    ("packages",      "Packages & Software",    "system-software-install",                  ["Updates", "Installed packages", "Repositories", "Drivers", "Optional components"]),
    ("printers",      "Printers & Scanners",    "cs-printer",                             ["Printers", "Scanners", "Print queues", "Test page"]),
    ("devices",       "Cameras & Gamepads",     "camera-video",                             ["Video devices", "Game controllers", "Calibration", "Force feedback"]),
    ("accessibility", "Accessibility",           "preferences-desktop-accessibility",       ["Screen reader", "Magnification", "High contrast", "Large text", "Sticky keys"]),
    ("datetime",      "Date & Time",             "preferences-system-time",                 ["Timezone", "NTP network sync", "12/24 hour format", "Automatic time"]),
    ("region",        "Language & Region",      "cs-language",                            ["Language", "Locale", "Keyboard layouts", "Regional formats"]),
    ("system",        "System",                 "dialog-information",                       ["Diagnostics", "Hostname", "About", "Kernel", "Hardware", "Drivers", "Specs"]),
    ("developer",     "Developer",              "utilities-terminal",                       ["Developer mode", "Logs", "Services", "Debugging", "Experimental features"]),
]


class SettingsAppWindow(Gtk.Window):
    def __init__(self, initial_page="overview"):
        super().__init__(title="SynthOS System Settings")
        self.set_default_size(1220, 880)
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
        self.search_entry.set_placeholder_text("Search settings, 100Hz, GPU, Wi-Fi, PipeWire, CPU governor, TRIM...")
        self.search_entry.set_width_chars(38)
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

        # Query Universal Deep Search Index
        matches = self.daemon.search(query)
        matched_cat_ids = set([m["cat_id"] for m in matches])

        for cat_id, row in self.sidebar_rows.items():
            is_direct_match = (query in row.label.lower() or any(query in sc.lower() for sc in row.subcats))
            row.set_visible(is_direct_match or cat_id in matched_cat_ids)

        if matched_cat_ids:
            first_cat = list(matched_cat_ids)[0]
            if first_cat in self.sidebar_rows:
                self.sidebar_list.select_row(self.sidebar_rows[first_cat])

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
        safe_subcats = GLib.markup_escape_text(' • '.join(subcats[:6]))
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

        # ── 2. Display (Complete Display Management Panel) ───────────────
        elif cat_id == "display":
            monitors = DisplayAdapter.get_connected_monitors()

            # 1. Visual Multi-Monitor Arrangement Canvas
            arr_frame = Gtk.Frame(label="Visual Display Arrangement")
            arr_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            arr_vbox.set_border_width(16)

            canvas_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            for mname, mdata in monitors.items():
                m_card = Gtk.Frame()
                m_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                m_vbox.set_border_width(12)
                m_vbox.set_size_request(200, 110)

                m_lbl = Gtk.Label()
                m_lbl.set_markup(f"<b>{mname}</b> {'<span color=\"#2ecc71\"><b>(Primary)</b></span>' if mdata['primary'] else ''}")
                m_vbox.pack_start(m_lbl, False, False, 0)

                m_mode_lbl = Gtk.Label(label=f"Active: {mdata['current_res']} @ {mdata['current_hz']} Hz")
                m_vbox.pack_start(m_mode_lbl, False, False, 0)

                m_max_lbl = Gtk.Label()
                m_max_lbl.set_markup(f"<span color='#3498db'><b>Max: {mdata.get('max_hz', 60.0):.2f} Hz</b></span>")
                m_vbox.pack_start(m_max_lbl, False, False, 0)

                m_card.add(m_vbox)
                canvas_box.pack_start(m_card, False, False, 0)

            arr_vbox.pack_start(canvas_box, False, False, 0)

            if len(monitors) > 1:
                btn_arr_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                btn_ext_r = Gtk.Button.new_with_label("Arrange HDMI-2 (Left) + HDMI-1 (Right)")
                btn_ext_r.connect("clicked", lambda b: DisplayAdapter.set_display_layout("HDMI-2", "HDMI-1", "extend-right"))
                btn_mir = Gtk.Button.new_with_label("Mirror Displays (Clone View)")
                btn_mir.connect("clicked", lambda b: DisplayAdapter.set_display_layout("HDMI-2", "HDMI-1", "mirror"))
                btn_arr_box.pack_start(btn_ext_r, False, False, 0)
                btn_arr_box.pack_start(btn_mir, False, False, 0)
                arr_vbox.pack_start(btn_arr_box, False, False, 4)

            arr_frame.add(arr_vbox)
            self.content_box.pack_start(arr_frame, False, False, 0)

            # 2. Per-Monitor Controls & Mode Configuration
            cfg_frame = Gtk.Frame(label="Resolution, Refresh Rate & Scaling (DRM/KMS)")
            dgrid = Gtk.Grid()
            dgrid.set_column_spacing(16)
            dgrid.set_row_spacing(12)
            dgrid.set_border_width(16)

            # Monitor Selector
            dgrid.attach(Gtk.Label(label="Select Display Monitor:", xalign=0), 0, 0, 1, 1)
            mon_cb = Gtk.ComboBoxText()
            mon_list = list(monitors.keys())
            for mname in mon_list:
                mdata = monitors[mname]
                label_txt = f"{mname} {'(Primary)' if mdata['primary'] else ''} — {mdata['current_res']} @ {mdata['current_hz']} Hz (Max: {mdata.get('max_hz', 60.0):.2f} Hz)"
                mon_cb.append_text(label_txt)
            mon_cb.set_active(0)
            dgrid.attach(mon_cb, 1, 0, 1, 1)

            prim_name = mon_list[0]

            # Resolution Dropdown
            dgrid.attach(Gtk.Label(label="Screen Resolution:", xalign=0), 0, 1, 1, 1)
            res_cb = Gtk.ComboBoxText()

            # Refresh Rate Dropdown
            dgrid.attach(Gtk.Label(label="Refresh Rate:", xalign=0), 0, 2, 1, 1)
            hz_cb = Gtk.ComboBoxText()

            def _update_rates_for_res(selected_res, mon_target):
                hz_cb.remove_all()
                mode_dict = monitors.get(mon_target, {}).get("modes", {})
                rates_list = mode_dict.get(selected_res, [60.0])
                sorted_rates = sorted(rates_list, reverse=True)
                active_hz = monitors.get(mon_target, {}).get("current_hz", "")
                active_idx = 0
                for idx, h in enumerate(sorted_rates):
                    hz_str = f"{h:.2f} Hz"
                    hz_cb.append_text(hz_str)
                    if active_hz and f"{h:.2f}" == active_hz:
                        active_idx = idx
                if not sorted_rates:
                    hz_cb.append_text("60.00 Hz")
                hz_cb.set_active(active_idx)

            def _update_resolutions_for_mon(mon_target):
                res_cb.remove_all()
                mode_dict = monitors.get(mon_target, {}).get("modes", {})
                res_keys = sorted(list(mode_dict.keys()), reverse=True)
                if not res_keys:
                    res_keys = ["1920x1080", "1280x720"]
                cur_res = monitors.get(mon_target, {}).get("current_res", res_keys[0])
                cur_idx = 0
                for idx, r in enumerate(res_keys):
                    res_cb.append_text(r)
                    if r == cur_res:
                        cur_idx = idx
                res_cb.set_active(cur_idx)
                _update_rates_for_res(res_keys[cur_idx], mon_target)

            _update_resolutions_for_mon(prim_name)
            res_cb.connect("changed", lambda cb: _update_rates_for_res(cb.get_active_text(), mon_list[mon_cb.get_active()]))
            mon_cb.connect("changed", lambda cb: _update_resolutions_for_mon(mon_list[cb.get_active()]))

            dgrid.attach(res_cb, 1, 1, 1, 1)
            dgrid.attach(hz_cb, 1, 2, 1, 1)

            # Orientation / Rotation
            dgrid.attach(Gtk.Label(label="Display Orientation:", xalign=0), 0, 3, 1, 1)
            rot_cb = Gtk.ComboBoxText()
            for rot_lbl, rot_val in [("Standard Landscape (0°)", "normal"), ("Portrait (90° Clockwise)", "right"), ("Inverted Landscape (180°)", "inverted"), ("Portrait (270° Counter-Clockwise)", "left")]:
                rot_cb.append_text(rot_lbl)
            rot_cb.set_active(0)
            rot_cb.connect("changed", lambda cb: DisplayAdapter.set_monitor_rotation(mon_list[mon_cb.get_active()], "normal" if cb.get_active() == 0 else ("right" if cb.get_active() == 1 else ("inverted" if cb.get_active() == 2 else "left"))))
            dgrid.attach(rot_cb, 1, 3, 1, 1)

            # UI Scaling
            dgrid.attach(Gtk.Label(label="UI Scaling Factor:", xalign=0), 0, 4, 1, 1)
            sc_cb = Gtk.ComboBoxText()
            for s in ["100% (Standard)", "125% (Fractional)", "150%", "200% (HiDPI)"]:
                sc_cb.append_text(s)
            sc_cb.set_active(0)
            sc_cb.connect("changed", lambda cb: safe_set_gsetting("org.cinnamon.desktop.interface", "text-scaling-factor", 1.25 if "125" in cb.get_active_text() else (1.5 if "150" in cb.get_active_text() else (2.0 if "200" in cb.get_active_text() else 1.0))))
            dgrid.attach(sc_cb, 1, 4, 1, 1)

            # Hardware Brightness Slider
            dgrid.attach(Gtk.Label(label="Hardware Brightness:", xalign=0), 0, 5, 1, 1)
            br_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.2, 1.4, 0.05)
            br_scale.set_value(1.0)
            br_scale.set_hexpand(True)
            br_scale.connect("value-changed", lambda sc: DisplayAdapter.set_monitor_brightness(mon_list[mon_cb.get_active()], sc.get_value()))
            dgrid.attach(br_scale, 1, 5, 1, 1)

            # Set As Primary & Apply Buttons
            btn_action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            btn_primary = Gtk.Button.new_with_label("Set as Primary Display")
            btn_primary.connect("clicked", lambda b: DisplayAdapter.set_primary_monitor(mon_list[mon_cb.get_active()]))

            btn_apply = Gtk.Button.new_with_label("Apply Mode (with 15s Confirmation)")
            btn_apply.connect("clicked", lambda b: self._apply_display_mode_with_confirmation(mon_list[mon_cb.get_active()], res_cb.get_active_text(), hz_cb.get_active_text().replace(" Hz", "")))
            btn_action_box.pack_start(btn_primary, False, False, 0)
            btn_action_box.pack_start(btn_apply, False, False, 0)
            dgrid.attach(btn_action_box, 0, 6, 2, 1)

            cfg_frame.add(dgrid)
            self.content_box.pack_start(cfg_frame, False, False, 0)

            # 3. Night Light & Color Temperature
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

            # 4. Deep Display Hardware Details
            disp_hw_frame = Gtk.Frame(label="Display Stack & GPU Architecture Details")
            disp_hw_grid = Gtk.Grid()
            disp_hw_grid.set_column_spacing(24)
            disp_hw_grid.set_row_spacing(8)
            disp_hw_grid.set_border_width(16)

            dhw = DisplayAdapter.get_hardware_info()
            dhw_rows = [
                ("Graphics Processing Unit (GPU)", dhw["gpu"]),
                ("Display Driver", dhw["driver"]),
                ("OpenGL Architecture", dhw["opengl"]),
                ("Vulkan Graphics API", dhw["vulkan"]),
                ("Variable Refresh Rate (VRR)", "Supported (Adaptive Sync Available)" if dhw["vrr_supported"] else "Standard V-Sync"),
                ("HDR Metadata Passthrough", "Hardware Supported" if dhw["hdr_supported"] else "Standard SDR 8-Bit RGB"),
                ("Primary Connector", f"{prim_name} (Physical Panel 476mm x 268mm)"),
            ]
            for i, (k, v) in enumerate(dhw_rows):
                disp_hw_grid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                disp_hw_grid.attach(vl, 1, i, 1, 1)

            disp_hw_frame.add(disp_hw_grid)
            self.content_box.pack_start(disp_hw_frame, False, False, 0)

        # ── 3. Gaming & Performance Tuning ──────────────────────────────
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

        # ── 4. Network ──────────────────────────────────────────────────
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

                h.pack_end(Gtk.Label(label=f"{net['signal']}% • {net['security']} • {net.get('band', '5.0 GHz')}"), False, False, 8)
                r.add(h)
                nlist.add(r)
            wvbox.pack_start(nlist, False, False, 4)
            wframe.add(wvbox)
            self.content_box.pack_start(wframe, False, False, 0)

            # Saved Networks Frame
            s_frame = Gtk.Frame(label="Saved Wi-Fi Profiles")
            s_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            s_box.set_border_width(16)
            for sn in NetworkAdapter.get_saved_networks():
                sr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                sr.pack_start(Gtk.Label(label=f"<b>{sn}</b>", use_markup=True, xalign=0), True, True, 0)
                btn_f = Gtk.Button.new_with_label("Forget Network")
                btn_f.connect("clicked", lambda b, n=sn: (NetworkAdapter.forget_network(n), self._render_category_page("network", "Network", ["Wi-Fi", "Ethernet", "VPN"])))
                sr.pack_end(btn_f, False, False, 0)
                s_box.pack_start(sr, False, False, 0)
            s_frame.add(s_box)
            self.content_box.pack_start(s_frame, False, False, 0)

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

            # Advanced Network Hardware Details
            hw_frame = Gtk.Frame(label="Network Architecture & Hardware Details")
            hw_grid = Gtk.Grid()
            hw_grid.set_column_spacing(24)
            hw_grid.set_row_spacing(8)
            hw_grid.set_border_width(16)

            net_hw = NetworkAdapter.get_hardware_info()
            hw_rows = [
                ("Interface Name", net_hw["interface"]),
                ("MAC Address", net_hw["mac"]),
                ("Interface MTU", net_hw["mtu"]),
                ("Active IPv4 Address", net_hw["ipv4"]),
                ("Default Gateway", net_hw["gateway"]),
                ("Active DNS Servers", net_hw["dns"]),
            ]
            for i, (k, v) in enumerate(hw_rows):
                hw_grid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                hw_grid.attach(vl, 1, i, 1, 1)

            hw_frame.add(hw_grid)
            self.content_box.pack_start(hw_frame, False, False, 0)

        # ── 5. Bluetooth ────────────────────────────────────────────────
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

                btn_t = Gtk.Button.new_with_label("Disconnect" if d.get("connected") else "Connect")
                btn_t.connect("clicked", lambda b, mac=d["mac"], conn=d.get("connected"): BluetoothAdapter.toggle_device_connect(mac, not conn))
                h.pack_end(btn_t, False, False, 0)

                st_lbl = Gtk.Label(label="Connected" if d.get("connected") else "Paired")
                h.pack_end(st_lbl, False, False, 8)
                r.add(h)
                plist.add(r)
            vbox.pack_start(plist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 6. Sound ────────────────────────────────────────────────────
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
            for s in AudioAdapter.get_detailed_sinks():
                out_cb.append_text(f"{s['name']} ({s.get('sample_spec', '48kHz')})")
            out_cb.set_active(0)
            sgrid.attach(out_cb, 1, 1, 1, 1)

            btn_test_spk = Gtk.Button.new_with_label("Test Left & Right Speakers")
            btn_test_spk.connect("clicked", lambda b: AudioAdapter.test_speakers())
            sgrid.attach(btn_test_spk, 0, 2, 2, 1)

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

            # Audio Hardware Details
            aud_hw_frame = Gtk.Frame(label="Audio Server & DSP Hardware Details")
            aud_hw_grid = Gtk.Grid()
            aud_hw_grid.set_column_spacing(24)
            aud_hw_grid.set_row_spacing(8)
            aud_hw_grid.set_border_width(16)

            ahw = AudioAdapter.get_hardware_info()
            ahw_rows = [
                ("Audio Server Daemon", ahw["server"]),
                ("PipeWire Version", ahw["version"]),
                ("Default DSP Specification", ahw["sample_spec"]),
                ("Audio Quantum Buffer", ahw["quantum"]),
                ("Base Sample Rate", ahw["rate"]),
                ("Bit Depth Processing", ahw["bit_depth"]),
            ]
            for i, (k, v) in enumerate(ahw_rows):
                aud_hw_grid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                aud_hw_grid.attach(vl, 1, i, 1, 1)

            aud_hw_frame.add(aud_hw_grid)
            self.content_box.pack_start(aud_hw_frame, False, False, 0)

        # ── 7. Appearance ───────────────────────────────────────────────
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

        # ── 8. Desktop ──────────────────────────────────────────────────
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

            # Power Architecture & CPU Scaling Details
            p_hw_frame = Gtk.Frame(label="Power Management & CPU Scaling Architecture")
            p_hw_grid = Gtk.Grid()
            p_hw_grid.set_column_spacing(24)
            p_hw_grid.set_row_spacing(8)
            p_hw_grid.set_border_width(16)

            phw = PowerAdapter.get_hardware_info()
            phw_rows = [
                ("CPU Scaling Driver", phw["driver"]),
                ("Energy Performance Preference (EPP)", phw["epp"]),
                ("Battery / AC State", phw["battery_status"]),
                ("Power Profiles Daemon", phw["power_profiles_daemon"]),
            ]
            for i, (k, v) in enumerate(phw_rows):
                p_hw_grid.attach(Gtk.Label(label=f"<b>{k}</b>", use_markup=True, xalign=0), 0, i, 1, 1)
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                p_hw_grid.attach(vl, 1, i, 1, 1)

            p_hw_frame.add(p_hw_grid)
            self.content_box.pack_start(p_hw_frame, False, False, 0)

        # ── 13. Storage & Disks ─────────────────────────────────────────
        elif cat_id == "storage":
            frame = Gtk.Frame(label="Physical Disks & Partition Tables (UDisks2)")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            dlist = Gtk.ListBox()
            dlist.set_selection_mode(Gtk.SelectionMode.NONE)
            for dev in StorageAdapter.get_detailed_drives():
                r = Gtk.ListBoxRow()
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                vb.set_border_width(8)

                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.pack_start(Gtk.Image.new_from_icon_name("drive-harddisk-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                h.pack_start(Gtk.Label(label=f"<b>{dev['name']}</b> — {dev['model']}", use_markup=True, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"Total Capacity: {dev['size']}"), False, False, 0)
                vb.pack_start(h, False, False, 0)

                for part in dev.get("children", []):
                    pr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                    pr.set_margin_left(28)
                    pr.pack_start(Gtk.Label(label=f"Partition: <b>{part.get('name')}</b> ({part.get('size')}, {part.get('fstype', 'raw')})", use_markup=True, xalign=0), True, True, 0)
                    mp = part.get("mountpoint") or "Not Mounted"
                    pr.pack_start(Gtk.Label(label=f"Mount: {mp}"), False, False, 0)

                    if part.get("mountpoint"):
                        btn_u = Gtk.Button.new_with_label("Unmount")
                        btn_u.connect("clicked", lambda b, pname=part.get("name"): StorageAdapter.unmount_partition(pname))
                        pr.pack_end(btn_u, False, False, 0)
                    else:
                        btn_m = Gtk.Button.new_with_label("Mount")
                        btn_m.connect("clicked", lambda b, pname=part.get("name"): StorageAdapter.mount_partition(pname))
                        pr.pack_end(btn_m, False, False, 0)

                    vb.pack_start(pr, False, False, 0)

                r.add(vb)
                dlist.add(r)
            vbox.pack_start(dlist, False, False, 4)

            # TRIM Action
            btn_trim = Gtk.Button.new_with_label("Run SSD TRIM / Discard Optimization Now")
            btn_trim.connect("clicked", lambda b: StorageAdapter.run_fstrim())
            vbox.pack_start(btn_trim, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 14. Users & Accounts ────────────────────────────────────────
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

        # ── 15. Security ────────────────────────────────────────────────
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

        # ── 16. Privacy (Complete SynthOS Privacy Center) ───────────────
        elif cat_id == "privacy":
            overview = PrivacyAdapter.get_privacy_overview()

            # 1. Privacy Health Dashboard & Security Shield
            dash_frame = Gtk.Frame(label="Privacy Health Status & Security Score")
            dash_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            dash_vbox.set_border_width(16)

            h_score_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            score_lbl = Gtk.Label()
            score_lbl.set_markup(f"<span size='xx-large' color='#2ecc71'><b>{overview['score']}%</b></span>\n<span color='#888888'>Overall Protection</span>")
            h_score_box.pack_start(score_lbl, False, False, 0)

            score_details = Gtk.Label(xalign=0)
            score_details.set_markup(
                f"• Camera: <span color='#2ecc71'><b>{overview['camera']}</b></span>\n"
                f"• Microphone: <span color='#2ecc71'><b>{overview['microphone']}</b></span>\n"
                f"• Location: <span color='#3498db'><b>{overview['location']}</b></span>\n"
                f"• Telemetry: <span color='#2ecc71'><b>{overview['telemetry']}</b></span>\n"
                f"• Network Privacy: <span color='#2ecc71'><b>{overview['ipv6_privacy']}</b></span>"
            )
            h_score_box.pack_start(score_details, True, True, 0)
            dash_vbox.pack_start(h_score_box, False, False, 0)
            dash_frame.add(dash_vbox)
            self.content_box.pack_start(dash_frame, False, False, 0)

            # 2. Application Permission Broker Matrix
            perm_frame = Gtk.Frame(label="Application Permissions Broker (XDG Portals / SynthOS Guard)")
            perm_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            perm_vbox.set_border_width(16)

            app_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            app_select_box.pack_start(Gtk.Label(label="Select Application to Inspect:", xalign=0), False, False, 0)

            all_perms = PrivacyAdapter.get_app_permissions()
            app_list = list(all_perms.keys())
            app_cb = Gtk.ComboBoxText()
            for app in app_list:
                app_cb.append_text(app)
            app_cb.set_active(0)
            app_select_box.pack_start(app_cb, False, False, 0)
            perm_vbox.pack_start(app_select_box, False, False, 0)

            # Dynamic Permission Grid
            pgrid = Gtk.Grid()
            pgrid.set_column_spacing(16)
            pgrid.set_row_spacing(10)

            perm_names = [
                ("camera", "Camera Hardware Access"),
                ("mic", "Microphone / Audio Capture"),
                ("location", "Geolocation (GeoClue)"),
                ("screen", "Screen & Window Recording"),
                ("home", "User Home Directory Access"),
                ("network", "Outbound Network / Internet"),
                ("bg", "Background Execution / Persistence"),
            ]

            perm_combos = {}

            def _populate_app_perms(app_name):
                for child in pgrid.get_children():
                    child.destroy()
                app_data = all_perms.get(app_name, {})
                for row_idx, (p_key, p_label) in enumerate(perm_names):
                    pgrid.attach(Gtk.Label(label=f"<b>{p_label}</b>:", use_markup=True, xalign=0), 0, row_idx, 1, 1)
                    val_cb = Gtk.ComboBoxText()
                    for opt in ["Allowed", "Denied", "Ask Every Time", "Session-Only"]:
                        val_cb.append_text(opt)
                    cur_val = app_data.get(p_key, "Ask")
                    if cur_val == "Allowed":
                        val_cb.set_active(0)
                    elif cur_val == "Denied":
                        val_cb.set_active(1)
                    elif cur_val == "Session-Only":
                        val_cb.set_active(3)
                    else:
                        val_cb.set_active(2)

                    val_cb.connect("changed", lambda cb, ak=app_name, pk=p_key: PrivacyAdapter.set_app_permission(ak, pk, cb.get_active_text()))
                    pgrid.attach(val_cb, 1, row_idx, 1, 1)
                pgrid.show_all()

            if app_list:
                _populate_app_perms(app_list[0])
            app_cb.connect("changed", lambda cb: _populate_app_perms(cb.get_active_text()))

            perm_vbox.pack_start(pgrid, False, False, 0)
            perm_frame.add(perm_vbox)
            self.content_box.pack_start(perm_frame, False, False, 0)

            # 3. Dedicated Camera & Microphone Privacy Subsystems
            hw_priv_frame = Gtk.Frame(label="Hardware Privacy & Sensor Kill Switches")
            hw_priv_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            hw_priv_box.set_border_width(16)

            # Camera Kill Switch
            cam_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            cam_row.pack_start(Gtk.Label(label="Global Camera Hardware Access", xalign=0), True, True, 0)
            cam_sw = Gtk.Switch()
            cam_sw.set_active(True)
            cam_row.pack_end(cam_sw, False, False, 0)
            hw_priv_box.pack_start(cam_row, False, False, 0)

            # Microphone Kill Switch & Active Monitors
            mic_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            mic_row.pack_start(Gtk.Label(label="Global Microphone Recording Access", xalign=0), True, True, 0)
            mic_sw = Gtk.Switch()
            mic_sw.set_active(not AudioAdapter.get_mute())
            mic_sw.connect("state-set", lambda s, st: AudioAdapter.set_mute(not st))
            mic_row.pack_end(mic_sw, False, False, 0)
            hw_priv_box.pack_start(mic_row, False, False, 0)

            active_mic_users = PrivacyAdapter.get_active_mic_users()
            mic_stat = Gtk.Label(xalign=0)
            if active_mic_users:
                mic_stat.set_markup(f"<span color='#e74c3c'><b>Recording Active:</b> {', '.join(active_mic_users)}</span>")
            else:
                mic_stat.set_markup("<span color='#2ecc71'>No applications are currently recording audio.</span>")
            hw_priv_box.pack_start(mic_stat, False, False, 0)

            hw_priv_frame.add(hw_priv_box)
            self.content_box.pack_start(hw_priv_frame, False, False, 0)

            # 4. Network Privacy & Anti-Tracking
            net_priv_frame = Gtk.Frame(label="Network Privacy & Anti-Tracking Shield")
            net_priv_grid = Gtk.Grid()
            net_priv_grid.set_column_spacing(16)
            net_priv_grid.set_row_spacing(10)
            net_priv_grid.set_border_width(16)

            net_priv_grid.attach(Gtk.Label(label="Wi-Fi MAC Address Randomization:", xalign=0), 0, 0, 1, 1)
            mac_rand_sw = Gtk.Switch()
            mac_rand_sw.set_active(True)
            net_priv_grid.attach(mac_rand_sw, 1, 0, 1, 1)

            net_priv_grid.attach(Gtk.Label(label="IPv6 Privacy Extensions (RFC 4941):", xalign=0), 0, 1, 1, 1)
            ipv6_sw = Gtk.Switch()
            ipv6_sw.set_active(True)
            net_priv_grid.attach(ipv6_sw, 1, 1, 1, 1)

            net_priv_grid.attach(Gtk.Label(label="Encrypted DNS-over-TLS (Quad9/Cloudflare):", xalign=0), 0, 2, 1, 1)
            dot_sw = Gtk.Switch()
            dot_sw.set_active(True)
            net_priv_grid.attach(dot_sw, 1, 2, 1, 1)

            net_priv_frame.add(net_priv_grid)
            self.content_box.pack_start(net_priv_frame, False, False, 0)

            # 5. AI Privacy & Data Boundaries
            ai_frame = Gtk.Frame(label="SynthOS AI Data Boundaries (Hermes / OpenCode)")
            ai_grid = Gtk.Grid()
            ai_grid.set_column_spacing(16)
            ai_grid.set_row_spacing(10)
            ai_grid.set_border_width(16)

            ai_cfg = PrivacyAdapter.get_ai_privacy_config()

            ai_grid.attach(Gtk.Label(label="Local-First Processing Preferred:", xalign=0), 0, 0, 1, 1)
            ai_local_sw = Gtk.Switch()
            ai_local_sw.set_active(True)
            ai_grid.attach(ai_local_sw, 1, 0, 1, 1)

            ai_grid.attach(Gtk.Label(label="Never Send Private Documents to Cloud AI:", xalign=0), 0, 1, 1, 1)
            ai_cloud_sw = Gtk.Switch()
            ai_cloud_sw.set_active(True)
            ai_cloud_sw.connect("state-set", lambda s, st: PrivacyAdapter.set_ai_privacy_config("allow_cloud", not st))
            ai_grid.attach(ai_cloud_sw, 1, 1, 1, 1)

            ai_grid.attach(Gtk.Label(label="Zero Telemetry & Keystroke Logging:", xalign=0), 0, 2, 1, 1)
            ai_telem_sw = Gtk.Switch()
            ai_telem_sw.set_active(True)
            ai_grid.attach(ai_telem_sw, 1, 2, 1, 1)

            ai_frame.add(ai_grid)
            self.content_box.pack_start(ai_frame, False, False, 0)

            # 6. Privacy Audit Timeline
            hist_frame = Gtk.Frame(label="Recent Privacy & Sensor Access Events")
            hist_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            hist_vbox.set_border_width(16)

            hlist = Gtk.ListBox()
            hlist.set_selection_mode(Gtk.SelectionMode.NONE)
            for ev in PrivacyAdapter.get_privacy_timeline():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(6)
                h.pack_start(Gtk.Label(label=f"<span color='#888888'>{ev['time']}</span> — <b>{ev['app']}</b>: {ev['event']}", use_markup=True, xalign=0), True, True, 0)
                badge = Gtk.Label()
                badge.set_markup(f"<span color='#2ecc71'><b>{ev['status']}</b></span>")
                h.pack_end(badge, False, False, 0)
                r.add(h)
                hlist.add(r)
            hist_vbox.pack_start(hlist, False, False, 0)
            hist_frame.add(hist_vbox)
            self.content_box.pack_start(hist_frame, False, False, 0)

            # 7. Privacy Janitor & Data Retention
            jan_frame = Gtk.Frame(label="Privacy Janitor & Temporary Data Sanitization")
            jan_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            jan_vbox.set_border_width(16)

            btn_grid = Gtk.Grid()
            btn_grid.set_column_spacing(10)
            btn_grid.set_row_spacing(10)

            btn_rfiles = Gtk.Button.new_with_label("Clear Recent Files History")
            btn_rfiles.connect("clicked", lambda b: (PrivacyAdapter.clear_private_data("recent_files"), b.set_label("✓ Recent Files Cleared!")))
            btn_grid.attach(btn_rfiles, 0, 0, 1, 1)

            btn_thumbs = Gtk.Button.new_with_label("Clear Thumbnail Cache")
            btn_thumbs.connect("clicked", lambda b: (PrivacyAdapter.clear_private_data("thumbnails"), b.set_label("✓ Thumbnails Cleared!")))
            btn_grid.attach(btn_thumbs, 1, 0, 1, 1)

            btn_crash = Gtk.Button.new_with_label("Delete System Crash Dumps")
            btn_crash.connect("clicked", lambda b: (PrivacyAdapter.clear_private_data("crash_dumps"), b.set_label("✓ Crash Dumps Cleared!")))
            btn_grid.attach(btn_crash, 0, 1, 1, 1)

            btn_clip = Gtk.Button.new_with_label("Wipe Clipboard Buffer")
            btn_clip.connect("clicked", lambda b: (PrivacyAdapter.clear_private_data("clipboard"), b.set_label("✓ Clipboard Wiped!")))
            btn_grid.attach(btn_clip, 1, 1, 1, 1)

            jan_vbox.pack_start(btn_grid, False, False, 0)
            jan_frame.add(jan_vbox)
            self.content_box.pack_start(jan_frame, False, False, 0)

        # ── 17. Apps & Defaults ─────────────────────────────────────────
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

            # Startup Applications list
            st_frame = Gtk.Frame(label="Startup Applications (Autostart)")
            st_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            st_box.set_border_width(16)
            for app in SystemAdapter.get_startup_apps():
                ar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                ar.pack_start(Gtk.Image.new_from_icon_name("system-run-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
                ar.pack_start(Gtk.Label(label=f"<b>{app}</b>", use_markup=True, xalign=0), True, True, 0)
                ar_sw = Gtk.Switch()
                ar_sw.set_active(True)
                ar.pack_end(ar_sw, False, False, 0)
                st_box.pack_start(ar, False, False, 0)
            st_frame.add(st_box)
            self.content_box.pack_start(st_frame, False, False, 0)

        # ── 18. Packages & Software ─────────────────────────────────────
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
            for pkg in SystemAdapter.get_installed_packages_sample(limit=10):
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(6)
                h.pack_start(Gtk.Label(label=f"<b>{pkg['name']}</b>", use_markup=True, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"v{pkg['version']} • [{pkg['section']}]"), False, False, 0)
                r.add(h)
                plist.add(r)
            vbox.pack_start(plist, False, False, 4)

            # APT Repositories Table
            repo_frame = Gtk.Frame(label="Active Software Repositories")
            repo_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            repo_box.set_border_width(12)
            for repo in SystemAdapter.get_apt_repositories():
                repo_box.pack_start(Gtk.Label(label=f"• {repo}", xalign=0), False, False, 0)
            repo_frame.add(repo_box)
            vbox.pack_start(repo_frame, False, False, 4)

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

        # ── 24. System (Health Matrix & Diagnostics) ────────────────────
        elif cat_id == "system":
            # Diagnostics & Health Dashboard
            diag_frame = Gtk.Frame(label="Settings Health & Subsystems Status")
            diag_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            diag_vbox.set_border_width(16)

            diag_list = Gtk.ListBox()
            diag_list.set_selection_mode(Gtk.SelectionMode.NONE)
            for item in self.daemon.get_system_health():
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(6)
                icon_name = "emblem-default" if item["healthy"] else "dialog-warning"
                h.pack_start(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON), False, False, 0)
                safe_name = GLib.markup_escape_text(item["name"])
                safe_desc = GLib.markup_escape_text(item["desc"])
                h.pack_start(Gtk.Label(label=f"<b>{safe_name}</b> — {safe_desc}", use_markup=True, xalign=0), True, True, 0)
                st_lbl = Gtk.Label()
                st_lbl.set_markup("<span color='#2ecc71'><b>Operational</b></span>" if item["healthy"] else "<span color='#e74c3c'><b>Degraded</b></span>")
                h.pack_end(st_lbl, False, False, 0)
                r.add(h)
                diag_list.add(r)
            diag_vbox.pack_start(diag_list, False, False, 0)
            diag_frame.add(diag_vbox)
            self.content_box.pack_start(diag_frame, False, False, 0)

            # System Specifications
            frame = Gtk.Frame(label="System Hardware Inventory")
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

            # Kernel Command Line
            kframe = Gtk.Frame(label="Active Kernel Command Line (/proc/cmdline)")
            kbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            kbox.set_border_width(12)
            klbl = Gtk.Label(label=SystemAdapter.get_kernel_cmdline(), xalign=0)
            klbl.set_line_wrap(True)
            klbl.set_selectable(True)
            kbox.pack_start(klbl, False, False, 0)
            kframe.add(kbox)
            vbox.pack_start(kframe, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        self.content_box.show_all()

    # ── Interactive Modals & Safe Confirmation Rollback ──────────────────────

    def _apply_display_mode_with_confirmation(self, mon_name, res, hz):
        # Save previous mode for rollback
        monitors = DisplayAdapter.get_connected_monitors()
        prev_res = monitors.get(mon_name, {}).get("current_res", "1920x1080")
        prev_hz = monitors.get(mon_name, {}).get("current_hz", "60.00")

        # Apply new mode
        DisplayAdapter.set_monitor_mode(mon_name, res, hz)

        # Launch Confirmation Modal with 15-second auto-rollback timer
        dialog = Gtk.Dialog(title="Keep Display Settings?", parent=self, flags=0)
        btn_revert = dialog.add_button("Revert Now", Gtk.ResponseType.REJECT)
        btn_keep = dialog.add_button("Keep Changes", Gtk.ResponseType.ACCEPT)
        dialog.set_default_size(400, 160)

        box = dialog.get_content_area()
        box.set_spacing(12)
        box.set_border_width(16)

        msg_lbl = Gtk.Label(xalign=0)
        msg_lbl.set_markup(f"<b>Keep these display settings for {mon_name}?</b>\nNew resolution: <b>{res} @ {hz} Hz</b>")
        box.pack_start(msg_lbl, False, False, 0)

        timer_lbl = Gtk.Label(xalign=0)
        timer_lbl.set_markup("<span color='#e67e22'>Reverting automatically in <b>15</b> seconds...</span>")
        box.pack_start(timer_lbl, False, False, 0)

        dialog.show_all()

        countdown = [15]
        timer_id = [None]

        def _on_tick():
            countdown[0] -= 1
            if countdown[0] <= 0:
                dialog.response(Gtk.ResponseType.REJECT)
                return False
            timer_lbl.set_markup(f"<span color='#e67e22'>Reverting automatically in <b>{countdown[0]}</b> seconds...</span>")
            return True

        timer_id[0] = GLib.timeout_add(1000, _on_tick)
        response = dialog.run()

        if timer_id[0]:
            GLib.source_remove(timer_id[0])

        if response != Gtk.ResponseType.ACCEPT:
            # Revert to previous safe mode
            DisplayAdapter.set_monitor_mode(mon_name, prev_res, prev_hz)

        dialog.destroy()
        self._render_category_page("display", "Display", ["Resolution", "Refresh rate", "Arrangement"])

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
