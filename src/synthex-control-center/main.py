#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — native GTK3 control center.
Uses standard GTK widgets with the system theme (no custom CSS).
Delegates to native tools (pavucontrol, nm-connection-editor, etc.) when available.
"""

import glob
import os
import sys
import subprocess
import shutil
from pathlib import Path

# Ensure system PyGObject is accessible inside virtualenvs
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

MODULES = [
    # Appearance
    ("backgrounds",  "Backgrounds",           "preferences-desktop-wallpaper",          "Desktop wallpaper",              "Appearance", ["cinnamon-settings backgrounds"]),
    ("effects",      "Effects",               "preferences-desktop-effects",             "Animations and transitions",     "Appearance", ["cinnamon-settings effects"]),
    ("fonts",        "Font Selection",         "preferences-desktop-font",               "System fonts",                   "Appearance", ["cinnamon-settings fonts"]),
    ("themes",       "Themes",                "preferences-desktop-theme",              "Window borders, icons, controls","Appearance", ["cinnamon-settings themes"]),

    # Preferences
    ("accessibility","Accessibility",          "preferences-desktop-accessibility",       "Visual and input aids",          "Preferences", ["cinnamon-settings accessibility"]),
    ("account",      "Account Details",        "system-users",                           "User profile and password",      "Preferences", ["cinnamon-settings user"]),
    ("applets",      "Applets",               "cs-applets",                             "Panel applets",                  "Preferences", ["cinnamon-settings applets"]),
    ("datetime",     "Date & Time",            "preferences-system-time",                "Clock, timezone, NTP",           "Preferences", ["cinnamon-settings calendar"]),
    ("desklets",     "Desklets",              "cs-desklets",                            "Desktop widgets",                "Preferences", ["cinnamon-settings desklets"]),
    ("desktop",      "Desktop",               "cs-desktop",                             "Desktop icons",                  "Preferences", ["cinnamon-settings desktop"]),
    ("extensions",   "Extensions",            "cs-extensions",                          "Cinnamon extensions",            "Preferences", ["cinnamon-settings extensions"]),
    ("general",      "General",               "cs-general",                             "General settings",               "Preferences", ["cinnamon-settings general"]),
    ("hotcorners",   "Hot Corners",           "cs-hotcorners",                          "Screen corner actions",          "Preferences", ["cinnamon-settings hotcorner"]),
    ("inputmethod",  "Input Method",          "cs-input-method",                        "Language input methods",         "Preferences", ["mintlocale-im"]),
    ("languages",    "Languages",             "cs-language",                            "System language",                "Preferences", ["mintlocale"]),
    ("notifications","Notifications",          "preferences-desktop-notification",        "Popup settings",                 "Preferences", ["cinnamon-settings notifications"]),
    ("onlineacc",    "Online Accounts",       "gnome-online-accounts-gtk",              "Google, Nextcloud, etc.",        "Preferences", ["gnome-online-accounts-gtk"]),
    ("panel",        "Panel",                 "cs-panel",                               "Taskbar settings",               "Preferences", ["cinnamon-settings panel"]),
    ("preferred",    "Preferred Apps",        "preferences-desktop-default-applications","Default browser, terminal",      "Preferences", ["cinnamon-settings default"]),
    ("privacy",      "Privacy",               "preferences-system-privacy",              "Permissions and history",        "Preferences", ["cinnamon-settings privacy"]),
    ("screensaver",  "Screensaver",           "cs-screensaver",                         "Lock screen settings",           "Preferences", ["cinnamon-settings screensaver"]),
    ("startup",      "Startup Apps",          "session-properties",                      "Autostart programs",             "Preferences", ["cinnamon-settings startup"]),
    ("windows",      "Windows",               "preferences-system-windows",              "Focus, titlebar, alt-tab",       "Preferences", ["cinnamon-settings windows"]),
    ("workspaces",   "Workspaces",            "preferences-desktop-workspaces",           "Virtual desktops",               "Preferences", ["cinnamon-settings workspaces"]),

    # Hardware
    ("bluetooth",    "Bluetooth",             "bluetooth",                                "Paired devices",                 "Hardware", ["blueman-manager", "blueberry"]),
    ("color",        "Color",                 "cs-color",                               "Color profiles",                 "Hardware", ["cinnamon-settings color"]),
    ("disks",        "Disks",                 "org.gnome.DiskUtility",                  "Drive management",               "Hardware", ["gnome-disks"]),
    ("display",      "Display",               "preferences-desktop-display",              "Resolution, scaling, layout",    "Hardware", ["cinnamon-settings display"]),
    ("keyboard",     "Keyboard",              "preferences-desktop-keyboard",              "Layouts and shortcuts",          "Hardware", ["cinnamon-settings keyboard"]),
    ("mouse",        "Mouse and Touchpad",    "input-mouse",                              "Speed, scrolling, gestures",     "Hardware", ["cinnamon-settings mouse"]),
    ("network",      "Network",               "preferences-system-network",               "Wi-Fi, Ethernet, VPN",           "Hardware", ["cinnamon-settings network"]),
    ("power",        "Power Management",      "preferences-system-power",                 "Battery, sleep, profiles",       "Hardware", ["cinnamon-settings power"]),
    ("printers",     "Printers",              "cs-printer",                             "Printers and queues",            "Hardware", ["system-config-printer"]),
    ("sound",        "Sound",                 "multimedia-volume-control",                 "Volume, output, microphone",     "Hardware", ["cinnamon-settings sound"]),
    ("sysinfo",      "System Info",           "dialog-information",                       "Hardware and OS details",        "Hardware", ["mintreport"]),
    ("tablet",       "Graphics Tablet",       "cs-tablet",                              "Stylus and tablet mapping",      "Hardware", ["cinnamon-settings wacom"]),

    # Administration
    ("driver",       "Driver Manager",        "cs-drivers",                               "Hardware drivers",               "Administration", ["pkexec driver-manager", "driver-manager"]),
    ("firewall",     "Firewall",              "cs-firewall",                              "Network security rules",         "Administration", ["gufw", "firewall-config"]),
    ("login",        "Login Window",          "cs-login",                               "Login screen settings",          "Administration", ["pkexec lightdm-settings"]),
    ("sources",      "Software Sources",      "cs-sources",                             "PPA and repositories",           "Administration", ["pkexec mintsources", "mintsources"]),
    ("backup",       "Timeshift",             "timeshift",                              "Snapshots and restore",          "Administration", ["timeshift-launcher", "timeshift-gtk"]),
    ("update",       "Update Manager",        "mintupdate",                             "Package updates",                "Administration", ["mintupdate"]),
    ("users",        "Users and Groups",      "cs-user-accounts",                         "System accounts",                "Administration", ["cinnamon-settings-users", "users-admin"]),
]


class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="System Settings")
        self.set_default_size(880, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        self.all_buttons = []

        # Header bar — no custom styling, just standard GTK
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.set_title("System Settings")
        self.set_titlebar(hb)

        self.back_btn = Gtk.Button()
        self.back_btn.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU))
        self.back_btn.set_tooltip_text("All Settings")
        self.back_btn.connect("clicked", self._go_home)
        self.back_btn.set_no_show_all(True)
        hb.pack_start(self.back_btn)

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Search")
        self.search.connect("search-changed", self._filter)
        hb.pack_end(self.search)

        self.hb = hb

        # Stack: home grid vs module page
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(150)
        self.add(self.stack)

        self.stack.add_named(self._build_home(), "home")

        self.mod_scroll = Gtk.ScrolledWindow()
        self.mod_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(self.mod_scroll, "module")

    def _build_home(self):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(16)

        categories_seen = []
        for mod_id, label, icon, desc, cat, ext in MODULES:
            if cat not in categories_seen:
                categories_seen.append(cat)

        for cat in categories_seen:
            cat_label = Gtk.Label(xalign=0)
            cat_label.set_markup(f"<b>{cat}</b>")
            cat_label.set_margin_top(12)
            cat_label.set_margin_bottom(4)
            box.pack_start(cat_label, False, False, 0)

            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            box.pack_start(sep, False, False, 0)

            flow = Gtk.FlowBox()
            flow.set_valign(Gtk.Align.START)
            flow.set_max_children_per_line(6)
            flow.set_min_children_per_line(3)
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_row_spacing(6)
            flow.set_column_spacing(6)
            flow.set_margin_top(6)
            flow.set_margin_bottom(6)

            for mod_id, label, icon, desc, mcat, ext in MODULES:
                if mcat != cat:
                    continue

                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                btn.set_size_request(120, 88)
                btn.set_tooltip_text(desc)

                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                vb.set_valign(Gtk.Align.CENTER)
                vb.set_halign(Gtk.Align.CENTER)

                img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DND)
                vb.pack_start(img, False, False, 0)

                lbl = Gtk.Label(label=label)
                lbl.set_line_wrap(True)
                lbl.set_max_width_chars(14)
                lbl.set_justify(Gtk.Justification.CENTER)
                vb.pack_start(lbl, False, False, 0)

                btn.add(vb)
                btn.connect("clicked", self._on_click, mod_id, label, ext)

                flow.add(btn)
                self.all_buttons.append((label.lower(), desc.lower(), btn))

            box.pack_start(flow, False, False, 0)

        sw.add(box)
        return sw

    def _on_click(self, btn, mod_id, label, ext):
        # Try launching a real native tool first
        if ext:
            import shlex
            for cmd_str in ext:
                cmd_parts = shlex.split(cmd_str)
                if cmd_parts and shutil.which(cmd_parts[0]):
                    try:
                        subprocess.Popen(cmd_parts)
                        return
                    except Exception:
                        pass

        # Show built-in panel as fallback
        self.hb.set_title(label)
        self.back_btn.show()
        self.search.hide()

        child = self.mod_scroll.get_child()
        if child:
            self.mod_scroll.remove(child)

        self.mod_scroll.add(self._make_panel(mod_id, label))
        self.mod_scroll.show_all()
        self.stack.set_visible_child_name("module")

    def _make_panel(self, mod_id, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(20)

        if mod_id == "sysinfo":
            frame = Gtk.Frame()
            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(8)
            grid.set_border_width(16)

            uname = os.uname()
            rows = [
                ("Operating System", "SynthOS Linux 2026.10 LTS"),
                ("Linux Kernel",     uname.release),
                ("Processor",        self._read_cpu()),
                ("Memory",           self._read_mem()),
                ("Graphics",         self._read_gpu()),
                ("Disk",             self._read_disk()),
            ]
            for i, (k, v) in enumerate(rows):
                kl = Gtk.Label(xalign=0)
                kl.set_markup(f"<b>{k}</b>")
                vl = Gtk.Label(label=v, xalign=0)
                vl.set_selectable(True)
                grid.attach(kl, 0, i, 1, 1)
                grid.attach(vl, 1, i, 1, 1)

            frame.add(grid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "themes":
            for group_title, options, default in [
                ("Controls", ["Mint-Y-Dark", "Mint-Y-Dark-Teal", "Mint-Y-Dark-Aqua", "Mint-Y-Dark-Blue", "Adwaita-dark", "Breeze-Dark"], 0),
                ("Icons",    ["Mint-Y-Dark", "Papirus-Dark", "Breeze-dark", "Adwaita"], 0),
                ("Cursor",   ["Bibata-Modern-Classic", "DMZ-Black", "Adwaita"], 0),
            ]:
                frame = Gtk.Frame(label=group_title)
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                hb.set_border_width(12)
                combo = Gtk.ComboBoxText()
                for o in options:
                    combo.append_text(o)
                combo.set_active(default)
                hb.pack_start(Gtk.Label(label=f"{group_title}:", xalign=0), True, True, 0)
                hb.pack_end(combo, False, False, 0)
                frame.add(hb)
                box.pack_start(frame, False, False, 0)

        elif mod_id == "power":
            frame = Gtk.Frame(label="Power Profile")
            vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            vb.set_border_width(12)
            group = None
            for lbl in ["Balanced (recommended)", "Performance", "Power Saver"]:
                rb = Gtk.RadioButton.new_with_label_from_widget(group, lbl)
                if group is None:
                    group = rb
                vb.pack_start(rb, False, False, 0)
            frame.add(vb)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "preferred":
            frame = Gtk.Frame(label="Default Applications")
            grid = Gtk.Grid()
            grid.set_column_spacing(12)
            grid.set_row_spacing(8)
            grid.set_border_width(12)
            for i, (lbl, opts) in enumerate([
                ("Web Browser",   ["Firefox", "Chromium", "GNOME Web"]),
                ("File Manager",  ["Nemo", "Thunar", "Nautilus"]),
                ("Terminal",      ["Kitty", "Alacritty", "GNOME Terminal"]),
                ("Text Editor",   ["xed", "gedit", "Kate", "nano"]),
            ]):
                grid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                cb = Gtk.ComboBoxText()
                for o in opts:
                    cb.append_text(o)
                cb.set_active(0)
                grid.attach(cb, 1, i, 1, 1)
            frame.add(grid)
            box.pack_start(frame, False, False, 0)

        else:
            # Generic placeholder
            frame = Gtk.Frame(label=title)
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            inner.set_border_width(12)
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.pack_start(Gtk.Label(label=f"Enable {title}", xalign=0), True, True, 0)
            sw = Gtk.Switch()
            sw.set_active(True)
            row.pack_end(sw, False, False, 0)
            inner.pack_start(row, False, False, 0)
            frame.add(inner)
            box.pack_start(frame, False, False, 0)

        return box

    def _go_home(self, *a):
        self.hb.set_title("System Settings")
        self.back_btn.hide()
        self.search.show()
        self.stack.set_visible_child_name("home")

    def _filter(self, entry):
        q = entry.get_text().strip().lower()
        for name, desc, btn in self.all_buttons:
            parent = btn.get_parent()  # FlowBoxChild
            if parent:
                parent.set_visible((not q) or (q in name) or (q in desc))

    # ── System info helpers ─────────────────────────────────────────────
    def _read_cpu(self):
        try:
            for line in open("/proc/cpuinfo"):
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
        except Exception:
            pass
        return os.uname().machine

    def _read_mem(self):
        try:
            for line in open("/proc/meminfo"):
                if line.startswith("MemTotal:"):
                    return f"{int(line.split()[1]) / 1048576:.1f} GiB"
        except Exception:
            pass
        return "Unknown"

    def _read_gpu(self):
        try:
            out = subprocess.check_output(
                "lspci 2>/dev/null | grep -i -E 'vga|3d|display'",
                shell=True, text=True, timeout=3
            ).strip()
            if out:
                # Take the last colon-separated field
                return out.split(":")[-1].strip()
        except Exception:
            pass
        return "Unknown"

    def _read_disk(self):
        try:
            out = subprocess.check_output(
                ["df", "-h", "--output=size,used,avail,pcent,fstype", "/"],
                text=True, timeout=3
            ).strip().split("\n")
            if len(out) >= 2:
                return out[1].strip()
        except Exception:
            pass
        return "Unknown"


def main():
    win = SettingsWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()

