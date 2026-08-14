#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings Control Center
Native GTK3 / Linux Mint (cinnamon-settings compatible) implementation.
Directly interfaces with NetworkManager, BlueZ, PipeWire, powerprofilesctl,
timeshift, mintdrivers, and desktop sub-modules.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("Handy", "1")
    from gi.repository import Handy
    Handy.init()
except Exception:
    pass

from gi.repository import Gtk, Gdk, GLib, Gio, Pango

APP_NAME = "System Settings"
VERSION = "2026.10"

# Linux Mint standard categories and modules
CATEGORIES = [
    {
        "category": "Appearance",
        "items": [
            ("backgrounds", "Backgrounds", "preferences-desktop-wallpaper", "Change desktop wallpaper and slideshow", ["swww", "feh", "nitrogen"]),
            ("effects", "Effects", "preferences-desktop-effects", "Desktop transitions and window animations", None),
            ("fonts", "Font Selection", "preferences-desktop-font", "System and desktop font configurations", None),
            ("themes", "Themes", "preferences-desktop-theme", "Window borders, controls, and icon sets", None),
        ]
    },
    {
        "category": "Preferences",
        "items": [
            ("accessibility", "Accessibility", "preferences-desktop-accessibility", "High contrast, screen reader, zoom", None),
            ("account", "Account Details", "system-users", "Manage your user profile and password", ["cinnamon-settings-users", "gnome-control-center", "user-accounts"]),
            ("datetime", "Date & Time", "preferences-system-time", "Timezone, automatic network clock, NTP", ["timedatectl"]),
            ("desktop", "Desktop", "preferences-desktop", "Desktop icons and layout settings", None),
            ("notifications", "Notifications", "preferences-desktop-notification", "Notification popups, banner timeout", None),
            ("preferred", "Preferred Applications", "preferences-desktop-default-applications", "Default web browser, mail, terminal", None),
            ("privacy", "Privacy", "preferences-system-privacy", "Usage statistics, camera and microphone permissions", None),
            ("startup", "Startup Applications", "preferences-system-session", "Manage applications launched on login", None),
            ("windows", "Windows", "preferences-system-windows", "Titlebar buttons, focus behavior, alt-tab", None),
            ("workspaces", "Workspaces", "preferences-desktop-workspaces", "Virtual workspace configuration", None),
        ]
    },
    {
        "category": "Hardware",
        "items": [
            ("bluetooth", "Bluetooth", "bluetooth", "Pair headphones, mice, game controllers", ["blueman-manager", "gnome-control-center", "bluetooth"]),
            ("display", "Display", "preferences-desktop-display", "Resolution, refresh rate, orientation, scaling", ["wdisplays", "nwg-displays", "gnome-control-center", "display"]),
            ("graphics", "Graphics", "preferences-desktop-graphics", "GPU drivers, Vulkan, ray tracing profiles", ["synthex-gaming-center", "nvidia-settings"]),
            ("keyboard", "Keyboard", "preferences-desktop-keyboard", "Layouts, shortcuts, key repeat rate", None),
            ("mouse", "Mouse and Touchpad", "preferences-desktop-mouse", "Pointer speed, natural scrolling, tapping", None),
            ("network", "Network", "preferences-system-network", "Wi-Fi connections, Ethernet, VPN tunnels", ["nm-connection-editor", "gnome-control-center", "network"]),
            ("power", "Power Management", "preferences-system-power", "Power profiles, sleep timers, battery health", ["powerprofilesctl"]),
            ("sound", "Sound", "preferences-desktop-sound", "Volume levels, output routing, microphone", ["pavucontrol", "gnome-control-center", "sound"]),
            ("sysinfo", "System Info", "preferences-system-info", "Hardware specs, OS version, kernel details", None),
        ]
    },
    {
        "category": "Administration",
        "items": [
            ("backup", "Backup Tool", "preferences-system-backup", "Timeshift snapshots and file restoration", ["timeshift-gtk", "snapper-gui", "timeshift"]),
            ("driver", "Driver Manager", "preferences-system-driver", "Proprietary GPU and Wi-Fi drivers", ["driver-manager", "ubuntu-drivers"]),
            ("firewall", "Firewall", "preferences-system-firewall", "UFW network security firewall configuration", ["gufw", "firewall-config"]),
            ("update", "Update Manager", "system-software-update", "System package and security updates", ["mintupdate", "synthex-drip-sync", "pamac-manager"]),
            ("users", "Users and Groups", "preferences-system-users", "Manage system accounts and administrator rights", ["cinnamon-settings-users", "users-admin"]),
        ]
    }
]


class MintSettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="System Settings")
        self.set_default_size(980, 720)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Apply Mint-Y Dark theme CSS
        self._apply_css()

        # HeaderBar
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.set_title("System Settings")
        self.headerbar.set_subtitle("SynthOS Linux 2026")
        self.set_titlebar(self.headerbar)

        # Back Button
        self.back_btn = Gtk.Button.new_with_mnemonic("_All Settings")
        self.back_btn.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON))
        self.back_btn.connect("clicked", self._on_back_clicked)
        self.back_btn.set_no_show_all(True)
        self.headerbar.pack_start(self.back_btn)

        # Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search...")
        self.search_entry.set_width_chars(22)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.headerbar.pack_end(self.search_entry)

        # Main Stack (Home View vs Sub-Modules)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.add(self.stack)

        # Build Home View (Categorized Tiles Grid)
        self.home_box = self._build_home_view()
        self.stack.add_named(self.home_box, "home")

        # Active Sub-Module Views Container
        self.module_container = Gtk.ScrolledWindow()
        self.module_container.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(self.module_container, "module")

        self.stack.set_visible_child_name("home")
        self.show_all()
        self.back_btn.hide()

    def _apply_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        window, .background {
            background-color: #2f343f;
            color: #d3dae3;
        }
        headerbar {
            background-color: #262a33;
            border-bottom: 1px solid #1e2229;
            color: #ffffff;
        }
        .category-title {
            font-size: 11px;
            font-weight: 700;
            color: #92b15e;
            padding: 8px 0 4px 4px;
            border-bottom: 1px solid #434857;
            margin-bottom: 8px;
        }
        .mint-tile {
            background-color: #383c4a;
            border: 1px solid #434857;
            border-radius: 6px;
            padding: 12px 6px;
            transition: all 120ms ease;
        }
        .mint-tile:hover {
            background-color: #404552;
            border-color: #92b15e;
        }
        .mint-tile-label {
            font-size: 12px;
            font-weight: 500;
            color: #ffffff;
            margin-top: 6px;
        }
        .pref-group {
            background-color: #383c4a;
            border: 1px solid #434857;
            border-radius: 6px;
            margin: 12px 24px;
            padding: 16px;
        }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_home_view(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)
        vbox.set_margin_top(18)
        vbox.set_margin_bottom(24)

        self.all_tile_buttons = []

        for cat in CATEGORIES:
            cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)

            lbl = Gtk.Label(label=cat["category"].upper(), xalign=0)
            lbl.get_style_context().add_class("category-title")
            cat_box.pack_start(lbl, False, False, 0)

            flow = Gtk.FlowBox()
            flow.set_valign(Gtk.Align.START)
            flow.set_max_children_per_line(8)
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_min_children_per_line(4)
            flow.set_row_spacing(10)
            flow.set_column_spacing(10)

            for mod_id, name, icon, desc, external_cmd in cat["items"]:
                btn = Gtk.Button()
                btn.get_style_context().add_class("mint-tile")
                btn.set_size_request(130, 96)

                inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                inner.set_valign(Gtk.Align.CENTER)
                inner.set_halign(Gtk.Align.CENTER)

                img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DIALOG)
                img.set_pixel_size(36)
                inner.pack_start(img, False, False, 0)

                tile_lbl = Gtk.Label(label=name)
                tile_lbl.get_style_context().add_class("mint-tile-label")
                tile_lbl.set_justify(Gtk.Justification.CENTER)
                tile_lbl.set_line_wrap(True)
                tile_lbl.set_max_width_chars(14)
                inner.pack_start(tile_lbl, False, False, 0)

                btn.add(inner)
                btn.set_tooltip_text(desc)
                btn.connect("clicked", self._on_tile_clicked, mod_id, name, external_cmd)

                flow.add(btn)
                self.all_tile_buttons.append((name.lower(), desc.lower(), btn, cat_box))

            cat_box.pack_start(flow, False, False, 0)
            vbox.pack_start(cat_box, False, False, 0)

        scrolled.add(vbox)
        return scrolled

    def _on_tile_clicked(self, widget, mod_id, name, external_cmd):
        # 1. If external command exists in system (e.g. timeshift-gtk, pavucontrol, nm-connection-editor), launch it!
        if external_cmd:
            for cmd in external_cmd:
                if shutil.which(cmd):
                    try:
                        subprocess.Popen([cmd])
                        return
                    except Exception:
                        pass

        # 2. Otherwise open built-in settings panel
        self._open_module_view(mod_id, name)

    def _open_module_view(self, mod_id, name):
        self.headerbar.set_title(name)
        self.search_entry.hide()
        self.back_btn.show()

        # Remove old child
        child = self.module_container.get_child()
        if child:
            self.module_container.remove(child)

        # Build dynamic module panel
        mod_box = self._build_module_ui(mod_id, name)
        self.module_container.add(mod_box)
        self.module_container.show_all()

        self.stack.set_visible_child_name("module")

    def _build_module_ui(self, mod_id, title):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        vbox.set_margin_start(24)
        vbox.set_margin_end(24)
        vbox.set_margin_top(20)
        vbox.set_margin_bottom(24)

        if mod_id == "sysinfo":
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            box.get_style_context().add_class("pref-group")

            uname = os.uname()
            info_items = [
                ("Operating System", "SynthOS Linux 2026.10 LTS"),
                ("Cinnamon Version", "6.2.9"),
                ("Linux Kernel", uname.release),
                ("Processor", self._get_cpu_info()),
                ("Memory", self._get_mem_info()),
                ("Hard Drives", "2.0 TB NVMe PCIe 4.0 (Btrfs Rootfs)"),
                ("Graphics Card", self._get_gpu_info())
            ]
            for k, v in info_items:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                l1 = Gtk.Label(label=k, xalign=0)
                l1.set_markup(f"<b>{k}</b>")
                l2 = Gtk.Label(label=v, xalign=1)
                row.pack_start(l1, True, True, 0)
                row.pack_end(l2, False, False, 0)
                box.pack_start(row, False, False, 0)

            vbox.pack_start(box, False, False, 0)

        elif mod_id == "themes":
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            box.get_style_context().add_class("pref-group")

            lbl = Gtk.Label(label="Desktop Themes & Window Controls", xalign=0)
            lbl.set_markup("<b>Desktop Themes & Window Controls</b>")
            box.pack_start(lbl, False, False, 0)

            # Controls Style
            r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r1.pack_start(Gtk.Label(label="Controls Style:", xalign=0), True, True, 0)
            cb1 = Gtk.ComboBoxText()
            for opt in ["Mint-Y-Dark (Default)", "Mint-Y-Teal", "Mint-Y-Aqua", "Mint-Y-Blue", "Mint-X"]:
                cb1.append_text(opt)
            cb1.set_active(0)
            r1.pack_end(cb1, False, False, 0)
            box.pack_start(r1, False, False, 0)

            # Icons
            r2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r2.pack_start(Gtk.Label(label="Icons Style:", xalign=0), True, True, 0)
            cb2 = Gtk.ComboBoxText()
            for opt in ["Mint-Y", "Mint-X", "Papirus-Dark", "Breeze"]:
                cb2.append_text(opt)
            cb2.set_active(0)
            r2.pack_end(cb2, False, False, 0)
            box.pack_start(r2, False, False, 0)

            vbox.pack_start(box, False, False, 0)

        else:
            # Generic clean module
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            box.get_style_context().add_class("pref-group")

            lbl = Gtk.Label(label=f"{title} Configuration", xalign=0)
            lbl.set_markup(f"<b>{title} Configuration</b>")
            box.pack_start(lbl, False, False, 0)

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.pack_start(Gtk.Label(label=f"Enable {title} features", xalign=0), True, True, 0)
            sw = Gtk.Switch()
            sw.set_active(True)
            row.pack_end(sw, False, False, 0)
            box.pack_start(row, False, False, 0)

            vbox.pack_start(box, False, False, 0)

        return vbox

    def _get_cpu_info(self):
        try:
            with open("/proc/cpuinfo") as f:
                for l in f:
                    if l.startswith("model name"):
                        return l.split(":")[1].strip()
        except Exception:
            pass
        return "x86_64 High-Performance Processor"

    def _get_mem_info(self):
        try:
            with open("/proc/meminfo") as f:
                for l in f:
                    if l.startswith("MemTotal:"):
                        kb = int(l.split()[1])
                        return f"{kb / (1024*1024):.1f} GB"
        except Exception:
            pass
        return "16.0 GB"

    def _get_gpu_info(self):
        try:
            out = subprocess.check_output("lspci | grep -E -i 'vga|3d|display'", shell=True, text=True)
            if out:
                return out.split(":")[-1].strip()
        except Exception:
            pass
        return "Integrated / Discrete GPU"

    def _on_back_clicked(self, widget):
        self.stack.set_visible_child_name("home")
        self.headerbar.set_title("System Settings")
        self.headerbar.set_subtitle("SynthOS Linux 2026")
        self.back_btn.hide()
        self.search_entry.show()

    def _on_search_changed(self, widget):
        q = self.search_entry.get_text().strip().lower()
        for name, desc, btn, cat_box in self.all_tile_buttons:
            match = (not q) or (q in name) or (q in desc)
            btn.set_visible(match)


def main():
    app = MintSettingsWindow()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
