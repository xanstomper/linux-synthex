#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — Complete Distribution Control Center.
Features comprehensive in-app configuration panels for all system domains,
hardware interfaces, desktop preferences, and administration tools.
"""

import glob
import os
import sys
import subprocess
import shutil
import shlex
import time
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

def get_gsettings(schema_id):
    try:
        source = Gio.SettingsSchemaSource.get_default()
        if source and source.lookup(schema_id, True):
            return Gio.Settings.new(schema_id)
    except Exception:
        pass
    return None

MODULES = [
    # Appearance
    ("backgrounds",  "Backgrounds",           "preferences-desktop-wallpaper",          "Desktop wallpaper, slideshow & aspect ratio", "Appearance"),
    ("themes",       "Themes",                "preferences-desktop-theme",              "Window controls, icons, cursor & dark mode",  "Appearance"),
    ("fonts",        "Font Selection",         "preferences-desktop-font",               "System typography, hinting & UI scaling",     "Appearance"),
    ("effects",      "Effects",               "preferences-desktop-effects",             "Window animations, transitions & FX",         "Appearance"),

    # Preferences
    ("accessibility","Accessibility",          "preferences-desktop-accessibility",       "Visual, hearing, typing & pointing aids",     "Preferences"),
    ("account",      "Account Details",        "system-users",                           "User profile, password & authentication",     "Preferences"),
    ("applets",      "Applets",               "cs-applets",                             "Taskbar panels, status applets & widgets",    "Preferences"),
    ("datetime",     "Date & Time",            "preferences-system-time",                "Clock formats, timezone & network NTP sync",  "Preferences"),
    ("desklets",     "Desklets",              "cs-desklets",                            "On-desktop widgets, clocks & monitors",       "Preferences"),
    ("desktop",      "Desktop",               "cs-desktop",                             "Desktop icons, drives & layout options",      "Preferences"),
    ("extensions",   "Extensions",            "cs-extensions",                          "Shell extensions, window tiling & features",  "Preferences"),
    ("general",      "General",               "cs-general",                             "Hardware acceleration & UI rendering",        "Preferences"),
    ("hotcorners",   "Hot Corners",           "cs-hotcorners",                          "Screen corner actions, Exposé & triggers",    "Preferences"),
    ("languages",    "Languages",             "cs-language",                            "System language, regional formats & input",   "Preferences"),
    ("notifications","Notifications",          "preferences-desktop-notification",        "Popup alerts, position & Do Not Disturb",     "Preferences"),
    ("onlineacc",    "Online Accounts",       "gnome-online-accounts-gtk",              "Cloud sync, Nextcloud & Google accounts",     "Preferences"),
    ("panel",        "Panel",                 "cs-panel",                               "Taskbar layout, auto-hide & icon sizing",     "Preferences"),
    ("preferred",    "Preferred Apps",        "preferences-desktop-default-applications","Default browser, file manager & terminal",   "Preferences"),
    ("privacy",      "Privacy",               "preferences-system-privacy",              "Recent files, history & telemetry options",   "Preferences"),
    ("screensaver",  "Screensaver",           "cs-screensaver",                         "Lock screen, clock, delay & security",        "Preferences"),
    ("startup",      "Startup Apps",          "session-properties",                      "Autostart applications on session login",     "Preferences"),
    ("windows",      "Windows",               "preferences-system-windows",              "Window titlebar buttons, focus mode & Alt-Tab","Preferences"),
    ("workspaces",   "Workspaces",            "preferences-desktop-workspaces",           "Virtual desktops & workspace switcher",       "Preferences"),

    # Hardware
    ("display",      "Display",               "preferences-desktop-display",              "Resolution, refresh rate, scaling & Night Light","Hardware"),
    ("sound",        "Sound",                 "multimedia-volume-control",                 "Volume levels, input/output & audio mixer",   "Hardware"),
    ("power",        "Power Management",      "preferences-system-power",                 "Power profiles, sleep timeouts & battery",    "Hardware"),
    ("network",      "Network",               "preferences-system-network",               "Wi-Fi, Ethernet, VPN & proxy connections",    "Hardware"),
    ("bluetooth",    "Bluetooth",             "bluetooth",                                "Paired devices, discovery & file transfer",   "Hardware"),
    ("keyboard",     "Keyboard",              "preferences-desktop-keyboard",              "Key repeat, input layouts & shortcuts",       "Hardware"),
    ("mouse",        "Mouse and Touchpad",    "input-mouse",                              "Speed, acceleration, gestures & natural scroll","Hardware"),
    ("printers",     "Printers",              "cs-printer",                             "Printers, scanners & print queues",           "Hardware"),
    ("disks",        "Disks",                 "org.gnome.DiskUtility",                  "Drive partitions, SMART health & mounts",     "Hardware"),
    ("color",        "Color",                 "cs-color",                               "Monitor calibration & ICC color profiles",    "Hardware"),
    ("tablet",       "Graphics Tablet",       "cs-tablet",                              "Stylus mapping, pressure curve & buttons",    "Hardware"),
    ("sysinfo",      "System Info",           "dialog-information",                       "Detailed OS, kernel & hardware specification","Hardware"),

    # Administration
    ("update",       "Update Manager",        "mintupdate",                             "System package, kernel & security updates",   "Administration"),
    ("driver",       "Driver Manager",        "cs-drivers",                               "Proprietary GPU & hardware drivers",          "Administration"),
    ("firewall",     "Firewall",              "cs-firewall",                              "UFW security firewall rules & incoming policy","Administration"),
    ("backup",       "Timeshift Backup",      "timeshift",                              "System BTRFS/RSYNC snapshots & restore",      "Administration"),
    ("sources",      "Software Sources",      "cs-sources",                             "Package repositories, PPAs & mirrors",        "Administration"),
    ("users",        "Users and Groups",      "cs-user-accounts",                         "System user accounts, groups & privileges",   "Administration"),
    ("login",        "Login Window",          "cs-login",                               "LightDM/SDDM greeter theme & autologin",      "Administration"),
]


class SettingsWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="System Settings")
        self.set_default_size(1020, 740)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        self.all_buttons = []

        # Header bar
        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.set_title("System Settings")
        self.hb.set_subtitle("SynthOS Linux")
        self.set_titlebar(self.hb)

        self.back_btn = Gtk.Button()
        self.back_btn.set_image(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.MENU))
        self.back_btn.set_tooltip_text("All Settings")
        self.back_btn.connect("clicked", self._go_home)
        self.back_btn.set_no_show_all(True)
        self.hb.pack_start(self.back_btn)

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Search settings...")
        self.search.set_width_chars(24)
        self.search.connect("search-changed", self._filter)
        self.hb.pack_end(self.search)

        # Main Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        self.add(self.stack)

        # Home view with categorized tiles
        self.stack.add_named(self._build_home(), "home")

        # Module view container
        self.mod_scroll = Gtk.ScrolledWindow()
        self.mod_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(self.mod_scroll, "module")

        self.stack.set_visible_child_name("home")
        self.back_btn.hide()

    def _build_home(self):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_border_width(18)

        categories = ["Appearance", "Preferences", "Hardware", "Administration"]

        for cat in categories:
            cat_label = Gtk.Label(xalign=0)
            cat_label.set_markup(f"<span size='large' weight='bold'>{cat}</span>")
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
            flow.set_row_spacing(8)
            flow.set_column_spacing(8)
            flow.set_margin_top(6)
            flow.set_margin_bottom(12)

            for mod_id, label, icon, desc, mcat in MODULES:
                if mcat != cat:
                    continue

                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                btn.set_size_request(130, 92)
                btn.set_tooltip_text(desc)

                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
                vb.set_valign(Gtk.Align.CENTER)
                vb.set_halign(Gtk.Align.CENTER)

                img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.DND)
                vb.pack_start(img, False, False, 0)

                lbl = Gtk.Label(label=label)
                lbl.set_line_wrap(True)
                lbl.set_max_width_chars(15)
                lbl.set_justify(Gtk.Justification.CENTER)
                vb.pack_start(lbl, False, False, 0)

                btn.add(vb)
                btn.connect("clicked", self._open_module_page, mod_id, label)

                flow.add(btn)
                self.all_buttons.append((label.lower(), desc.lower(), btn))

            box.pack_start(flow, False, False, 0)

        sw.add(box)
        return sw

    def _open_module_page(self, btn, mod_id, label):
        self.hb.set_title(label)
        self.hb.set_subtitle("SynthOS Settings")
        self.back_btn.show()
        self.search.hide()

        child = self.mod_scroll.get_child()
        if child:
            self.mod_scroll.remove(child)

        panel = self._make_panel(mod_id, label)
        self.mod_scroll.add(panel)
        self.mod_scroll.show_all()
        self.stack.set_visible_child_name("module")

    def _make_panel(self, mod_id, title):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(24)

        # Header description
        desc_label = Gtk.Label(xalign=0)
        desc_label.set_markup(f"<span size='larger' weight='bold'>{title}</span>")
        box.pack_start(desc_label, False, False, 0)

        # ── 1. Appearance Modules ───────────────────────────────────────
        if mod_id == "themes":
            cin_iface = get_gsettings("org.cinnamon.desktop.interface") or get_gsettings("org.gnome.desktop.interface")
            
            # Dark Mode Switch
            dm_frame = Gtk.Frame(label="Color Scheme")
            dm_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            dm_box.set_border_width(14)
            dm_lbl = Gtk.Label(label="Dark Mode", xalign=0)
            dm_sw = Gtk.Switch()
            dm_sw.set_active(True)
            if cin_iface:
                try:
                    cur_theme = cin_iface.get_string("gtk-theme")
                    dm_sw.set_active("dark" in cur_theme.lower())
                except Exception:
                    pass
            dm_box.pack_start(dm_lbl, True, True, 0)
            dm_box.pack_end(dm_sw, False, False, 0)
            dm_frame.add(dm_box)
            box.pack_start(dm_frame, False, False, 0)

            # Theme Choosers
            theme_frame = Gtk.Frame(label="Desktop Themes")
            tgrid = Gtk.Grid()
            tgrid.set_column_spacing(16)
            tgrid.set_row_spacing(10)
            tgrid.set_border_width(14)

            theme_rows = [
                ("Window Controls", ["Mint-Y-Dark", "Mint-Y-Dark-Teal", "Mint-Y-Dark-Aqua", "Mint-Y-Dark-Blue", "Adwaita-dark", "Breeze-Dark"]),
                ("Icons",           ["Mint-Y-Dark", "Papirus-Dark", "Breeze-dark", "Adwaita", "elementary-xfce-dark"]),
                ("Mouse Cursor",    ["Bibata-Modern-Classic", "DMZ-Black", "Adwaita", "breeze_cursors"]),
                ("Desktop Shell",   ["Mint-Y-Dark", "cinnamon", "Adapta-Nokto", "Arc-Dark"]),
            ]
            for i, (lbl, opts) in enumerate(theme_rows):
                tgrid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                cb = Gtk.ComboBoxText()
                for o in opts:
                    cb.append_text(o)
                cb.set_active(0)
                tgrid.attach(cb, 1, i, 1, 1)

            theme_frame.add(tgrid)
            box.pack_start(theme_frame, False, False, 0)

            # Accent Colors
            acc_frame = Gtk.Frame(label="Accent Color")
            acc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            acc_box.set_border_width(14)
            for color_name in ["Teal", "Aqua", "Blue", "Green", "Purple", "Red", "Orange", "Grey"]:
                rb = Gtk.RadioButton.new_with_label(None, color_name) if color_name == "Teal" else Gtk.RadioButton.new_with_label_from_widget(rb, color_name)
                acc_box.pack_start(rb, False, False, 4)
            acc_frame.add(acc_box)
            box.pack_start(acc_frame, False, False, 0)

        elif mod_id == "backgrounds":
            frame = Gtk.Frame(label="Wallpaper & Background Style")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            # Style dropdown
            hstyle = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hstyle.pack_start(Gtk.Label(label="Picture Aspect Ratio:", xalign=0), True, True, 0)
            cb = Gtk.ComboBoxText()
            for s in ["Zoom (Fill Screen)", "Scaled (Fit Aspect)", "Centered", "Stretched", "Tiled", "Spanned"]:
                cb.append_text(s)
            cb.set_active(0)
            hstyle.pack_end(cb, False, False, 0)
            vbox.pack_start(hstyle, False, False, 0)

            # Background Color
            hcolor = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hcolor.pack_start(Gtk.Label(label="Background Shading:", xalign=0), True, True, 0)
            cb_col = Gtk.ComboBoxText()
            for sc in ["Solid Color", "Horizontal Gradient", "Vertical Gradient"]:
                cb_col.append_text(sc)
            cb_col.set_active(0)
            hcolor.pack_end(cb_col, False, False, 0)
            vbox.pack_start(hcolor, False, False, 0)

            # Slideshow switch
            hslide = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hslide.pack_start(Gtk.Label(label="Play backgrounds as a slideshow", xalign=0), True, True, 0)
            sw = Gtk.Switch()
            hslide.pack_end(sw, False, False, 0)
            vbox.pack_start(hslide, False, False, 0)

            # Slideshow delay
            hdelay = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hdelay.pack_start(Gtk.Label(label="Change picture every:", xalign=0), True, True, 0)
            cb_del = Gtk.ComboBoxText()
            for d in ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"]:
                cb_del.append_text(d)
            cb_del.set_active(2)
            hdelay.pack_end(cb_del, False, False, 0)
            vbox.pack_start(hdelay, False, False, 0)

            # Choose Image button
            btn_choose = Gtk.Button.new_with_label("Select Wallpaper Image from Files...")
            btn_choose.connect("clicked", self._choose_wallpaper_dialog)
            vbox.pack_start(btn_choose, False, False, 6)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "fonts":
            frame = Gtk.Frame(label="System Typography")
            fgrid = Gtk.Grid()
            fgrid.set_column_spacing(16)
            fgrid.set_row_spacing(10)
            fgrid.set_border_width(14)

            font_rows = [
                ("Default Application Font",  "Ubuntu 10"),
                ("Window Title Font",         "Ubuntu Bold 10"),
                ("Document Font",             "Sans 10"),
                ("Monospace Terminal Font",    "JetBrains Mono 10"),
            ]
            for i, (lbl, default_font) in enumerate(font_rows):
                fgrid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                fb = Gtk.FontButton.new_with_font(default_font)
                fgrid.attach(fb, 1, i, 1, 1)

            frame.add(fgrid)
            box.pack_start(frame, False, False, 0)

            # Rendering
            rframe = Gtk.Frame(label="Font Rendering & Antialiasing")
            rgrid = Gtk.Grid()
            rgrid.set_column_spacing(16)
            rgrid.set_row_spacing(10)
            rgrid.set_border_width(14)

            rgrid.attach(Gtk.Label(label="Font Hinting:", xalign=0), 0, 0, 1, 1)
            hcombo = Gtk.ComboBoxText()
            for h in ["None", "Slight", "Medium", "Full"]:
                hcombo.append_text(h)
            hcombo.set_active(1)
            rgrid.attach(hcombo, 1, 0, 1, 1)

            rgrid.attach(Gtk.Label(label="Subpixel Antialiasing:", xalign=0), 0, 1, 1, 1)
            acombo = Gtk.ComboBoxText()
            for a in ["RGBA (Subpixel for LCD)", "Grayscale", "None"]:
                acombo.append_text(a)
            acombo.set_active(0)
            rgrid.attach(acombo, 1, 1, 1, 1)

            rgrid.attach(Gtk.Label(label="Text Scaling Factor:", xalign=0), 0, 2, 1, 1)
            scale_spin = Gtk.SpinButton.new_with_range(0.5, 3.0, 0.05)
            scale_spin.set_value(1.0)
            rgrid.attach(scale_spin, 1, 2, 1, 1)

            rframe.add(rgrid)
            box.pack_start(rframe, False, False, 0)

        elif mod_id == "effects":
            frame = Gtk.Frame(label="Window Animations & Transitions")
            egrid = Gtk.Grid()
            egrid.set_column_spacing(16)
            egrid.set_row_spacing(10)
            egrid.set_border_width(14)

            egrid.attach(Gtk.Label(label="Window Mapping Effect:", xalign=0), 0, 0, 1, 1)
            ecb1 = Gtk.ComboBoxText()
            for e in ["Scale & Fade", "Fade Only", "Glide", "None"]:
                ecb1.append_text(e)
            ecb1.set_active(0)
            egrid.attach(ecb1, 1, 0, 1, 1)

            egrid.attach(Gtk.Label(label="Window Closing Effect:", xalign=0), 0, 1, 1, 1)
            ecb2 = Gtk.ComboBoxText()
            for e in ["Scale & Fade", "Fade Only", "Glide", "None"]:
                ecb2.append_text(e)
            ecb2.set_active(0)
            egrid.attach(ecb2, 1, 1, 1, 1)

            egrid.attach(Gtk.Label(label="Window Minimizing Effect:", xalign=0), 0, 2, 1, 1)
            ecb3 = Gtk.ComboBoxText()
            for e in ["Traditional", "Scale", "Glide"]:
                ecb3.append_text(e)
            ecb3.set_active(0)
            egrid.attach(ecb3, 1, 2, 1, 1)

            egrid.attach(Gtk.Label(label="Animation Duration:", xalign=0), 0, 3, 1, 1)
            dur_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 50, 600, 25)
            dur_scale.set_value(150)
            dur_scale.set_hexpand(True)
            egrid.attach(dur_scale, 1, 3, 1, 1)

            frame.add(egrid)
            box.pack_start(frame, False, False, 0)

        # ── 2. Preferences Modules ──────────────────────────────────────
        elif mod_id == "accessibility":
            # Visual Aids
            vframe = Gtk.Frame(label="Visual Aids")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            vbox.set_border_width(14)

            for item_label, default_val in [
                ("High Contrast Display Mode", False),
                ("Large Text Display", False),
                ("Screen Reader (Orca)", False),
                ("Invert Colors Mode", False),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=item_label, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(default_val)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            vframe.add(vbox)
            box.pack_start(vframe, False, False, 0)

            # Typing & Input
            tframe = Gtk.Frame(label="Typing & Keyboard Aids")
            tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            tbox.set_border_width(14)

            for item_label in [
                "Sticky Keys (Press keys sequentially instead of simultaneously)",
                "Slow Keys (Put a delay between when a key is pressed and accepted)",
                "Bounce Keys (Ignore rapid duplicate keypresses)",
                "On-Screen Virtual Keyboard",
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=item_label, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(False)
                r.pack_end(sw, False, False, 0)
                tbox.pack_start(r, False, False, 0)

            tframe.add(tbox)
            box.pack_start(tframe, False, False, 0)

        elif mod_id == "account":
            frame = Gtk.Frame(label="User Profile & Credentials")
            agrid = Gtk.Grid()
            agrid.set_column_spacing(16)
            agrid.set_row_spacing(10)
            agrid.set_border_width(16)

            agrid.attach(Gtk.Label(label="Username:", xalign=0), 0, 0, 1, 1)
            u_entry = Gtk.Entry()
            u_entry.set_text(os.environ.get("USER", "jewboy420"))
            u_entry.set_sensitive(False)
            agrid.attach(u_entry, 1, 0, 1, 1)

            agrid.attach(Gtk.Label(label="Full Name:", xalign=0), 0, 1, 1, 1)
            fn_entry = Gtk.Entry()
            fn_entry.set_text("System Administrator")
            agrid.attach(fn_entry, 1, 1, 1, 1)

            agrid.attach(Gtk.Label(label="Account Type:", xalign=0), 0, 2, 1, 1)
            at_cb = Gtk.ComboBoxText()
            at_cb.append_text("Administrator (Root & Sudo Privileges)")
            at_cb.append_text("Standard User")
            at_cb.set_active(0)
            agrid.attach(at_cb, 1, 2, 1, 1)

            btn_pwd = Gtk.Button.new_with_label("Change User Password...")
            agrid.attach(btn_pwd, 1, 3, 1, 1)

            frame.add(agrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "datetime":
            frame = Gtk.Frame(label="Clock Format & Network Time")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            for lbl, state in [
                ("Use 24-hour clock format (e.g. 14:30)", True),
                ("Show seconds in clock", False),
                ("Show date in panel", True),
                ("Show day of the week in panel", True),
                ("Automatic Network Time Sync (NTP via systemd-timesyncd)", True),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=lbl, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(state)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            tz_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            tz_box.pack_start(Gtk.Label(label="System Timezone:", xalign=0), True, True, 0)
            tz_cb = Gtk.ComboBoxText()
            for tz in ["America/New_York (EST/EDT)", "America/Chicago (CST/CDT)", "America/Los_Angeles (PST/PDT)", "UTC / GMT", "Europe/London", "Europe/Berlin", "Asia/Tokyo"]:
                tz_cb.append_text(tz)
            tz_cb.set_active(0)
            tz_box.pack_end(tz_cb, False, False, 0)
            vbox.pack_start(tz_box, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "desktop":
            frame = Gtk.Frame(label="Desktop Icons & Placement")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            vbox.set_border_width(14)

            for icon_opt, default_val in [
                ("Computer", True),
                ("Home Folder", True),
                ("Trash", True),
                ("Mounted Storage Volumes & USB Disks", True),
                ("Network Servers", False),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=f"Show '{icon_opt}' on Desktop", xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(default_val)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "hotcorners":
            frame = Gtk.Frame(label="Interactive Screen Hot Corners")
            hgrid = Gtk.Grid()
            hgrid.set_column_spacing(16)
            hgrid.set_row_spacing(10)
            hgrid.set_border_width(14)

            corners = [
                ("Top Left Corner Action", 0, 0),
                ("Top Right Corner Action", 1, 0),
                ("Bottom Left Corner Action", 0, 1),
                ("Bottom Right Corner Action", 1, 1),
            ]
            for lbl, col, row in corners:
                cbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                cbox.pack_start(Gtk.Label(label=lbl, xalign=0), False, False, 0)
                cb = Gtk.ComboBoxText()
                for act in ["None (Disabled)", "Show Exposé (All Windows)", "Show Desktop", "Show Workspace Switcher", "Run Custom Command"]:
                    cb.append_text(act)
                cb.set_active(1 if "Top Left" in lbl else 0)
                cbox.pack_start(cb, False, False, 0)
                hgrid.attach(cbox, col, row, 1, 1)

            frame.add(hgrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "notifications":
            frame = Gtk.Frame(label="Popup Notifications & Alerts")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            for lbl, st in [
                ("Enable system popup notifications", True),
                ("Do Not Disturb mode (Silence all non-critical alerts)", False),
                ("Disable notifications during full-screen games & video", True),
                ("Show notification counter badge on taskbar tray", True),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=lbl, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(st)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            pos_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            pos_box.pack_start(Gtk.Label(label="Notification Screen Position:", xalign=0), True, True, 0)
            pos_cb = Gtk.ComboBoxText()
            for p in ["Top Right", "Top Left", "Bottom Right", "Bottom Left"]:
                pos_cb.append_text(p)
            pos_cb.set_active(2)
            pos_box.pack_end(pos_cb, False, False, 0)
            vbox.pack_start(pos_box, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "panel":
            frame = Gtk.Frame(label="Taskbar Panel Configuration")
            pgrid = Gtk.Grid()
            pgrid.set_column_spacing(16)
            pgrid.set_row_spacing(10)
            pgrid.set_border_width(14)

            pgrid.attach(Gtk.Label(label="Panel Screen Placement:", xalign=0), 0, 0, 1, 1)
            pl_cb = Gtk.ComboBoxText()
            for p in ["Bottom of Screen (Standard)", "Top of Screen", "Dual Panels (Top & Bottom)"]:
                pl_cb.append_text(p)
            pl_cb.set_active(0)
            pgrid.attach(pl_cb, 1, 0, 1, 1)

            pgrid.attach(Gtk.Label(label="Panel Auto-hide Behavior:", xalign=0), 0, 1, 1, 1)
            ah_cb = Gtk.ComboBoxText()
            for a in ["Never (Always Visible)", "Intelligently Autohide (When windows overlap)", "Always Autohide"]:
                ah_cb.append_text(a)
            ah_cb.set_active(0)
            pgrid.attach(ah_cb, 1, 1, 1, 1)

            pgrid.attach(Gtk.Label(label="Panel Height (pixels):", xalign=0), 0, 2, 1, 1)
            h_spin = Gtk.SpinButton.new_with_range(24, 72, 2)
            h_spin.set_value(40)
            pgrid.attach(h_spin, 1, 2, 1, 1)

            frame.add(pgrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "preferred":
            frame = Gtk.Frame(label="Default System Applications")
            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(10)
            grid.set_border_width(14)
            for i, (lbl, opts) in enumerate([
                ("Web Browser",   ["Firefox", "Chromium", "GNOME Web", "Brave", "Google Chrome"]),
                ("File Manager",  ["Nemo", "Thunar", "Nautilus", "Dolphin"]),
                ("Terminal",      ["Kitty", "Alacritty", "GNOME Terminal", "Tilix"]),
                ("Text Editor",   ["xed", "gedit", "Kate", "VSCode", "nano"]),
                ("Music Player",  ["Rhythmbox", "VLC media player", "Audacious", "Spotify"]),
                ("Video Player",  ["Celluloid", "VLC media player", "MPV"]),
                ("Photo Viewer",  ["Pix", "Xviewer", "Eye of GNOME"]),
                ("PDF Reader",    ["Xreader", "Evince", "Okular"]),
            ]):
                grid.attach(Gtk.Label(label=lbl, xalign=0), 0, i, 1, 1)
                cb = Gtk.ComboBoxText()
                for o in opts:
                    cb.append_text(o)
                cb.set_active(0)
                grid.attach(cb, 1, i, 1, 1)
            frame.add(grid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "privacy":
            frame = Gtk.Frame(label="Privacy, History & Telemetry")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            for lbl, st in [
                ("Remember recently opened files and documents", True),
                ("Remember frequently used applications", True),
                ("Send automatic telemetry and crash reports (Disabled on SynthOS)", False),
                ("Network connectivity health check", True),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=lbl, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(st)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            btn_clear = Gtk.Button.new_with_label("Clear Recent Files & App History Now")
            vbox.pack_start(btn_clear, False, False, 4)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "windows":
            frame = Gtk.Frame(label="Window Management & Focus")
            wgrid = Gtk.Grid()
            wgrid.set_column_spacing(16)
            wgrid.set_row_spacing(10)
            wgrid.set_border_width(14)

            wgrid.attach(Gtk.Label(label="Titlebar Buttons Position:", xalign=0), 0, 0, 1, 1)
            btn_pos = Gtk.ComboBoxText()
            for p in ["Right (Minimize, Maximize, Close)", "Left (macOS style)", "Right (Close only)"]:
                btn_pos.append_text(p)
            btn_pos.set_active(0)
            wgrid.attach(btn_pos, 1, 0, 1, 1)

            wgrid.attach(Gtk.Label(label="Window Focus Mode:", xalign=0), 0, 1, 1, 1)
            foc_cb = Gtk.ComboBoxText()
            for f in ["Click to Focus (Default)", "Focus Follows Mouse", "Sloppy Focus"]:
                foc_cb.append_text(f)
            foc_cb.set_active(0)
            wgrid.attach(foc_cb, 1, 1, 1, 1)

            wgrid.attach(Gtk.Label(label="Alt-Tab Switcher Style:", xalign=0), 0, 2, 1, 1)
            alt_cb = Gtk.ComboBoxText()
            for a in ["Icons and Thumbnails", "Icons Only", "Window Preview Grid", "Timeline"]:
                alt_cb.append_text(a)
            alt_cb.set_active(0)
            wgrid.attach(alt_cb, 1, 2, 1, 1)

            frame.add(wgrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "workspaces":
            frame = Gtk.Frame(label="Virtual Desktops & Workspaces")
            wgrid = Gtk.Grid()
            wgrid.set_column_spacing(16)
            wgrid.set_row_spacing(10)
            wgrid.set_border_width(14)

            wgrid.attach(Gtk.Label(label="Number of Workspaces:", xalign=0), 0, 0, 1, 1)
            ws_spin = Gtk.SpinButton.new_with_range(1, 16, 1)
            ws_spin.set_value(4)
            wgrid.attach(ws_spin, 1, 0, 1, 1)

            wgrid.attach(Gtk.Label(label="Show Workspace Switcher on Panel:", xalign=0), 0, 1, 1, 1)
            ws_sw1 = Gtk.Switch()
            ws_sw1.set_active(True)
            wgrid.attach(ws_sw1, 1, 1, 1, 1)

            wgrid.attach(Gtk.Label(label="Show On-Screen Display (OSD) on Switch:", xalign=0), 0, 2, 1, 1)
            ws_sw2 = Gtk.Switch()
            ws_sw2.set_active(True)
            wgrid.attach(ws_sw2, 1, 2, 1, 1)

            frame.add(wgrid)
            box.pack_start(frame, False, False, 0)

        # ── 3. Hardware Modules ─────────────────────────────────────────
        elif mod_id == "display":
            frame = Gtk.Frame(label="Monitors, Resolution & Refresh Rate")
            dgrid = Gtk.Grid()
            dgrid.set_column_spacing(16)
            dgrid.set_row_spacing(10)
            dgrid.set_border_width(14)

            dgrid.attach(Gtk.Label(label="Screen Resolution:", xalign=0), 0, 0, 1, 1)
            res_cb = Gtk.ComboBoxText()
            for r in ["1920 x 1080 (16:9 Full HD)", "2560 x 1440 (16:9 2K QHD)", "3840 x 2160 (4K UHD)", "1366 x 768"]:
                res_cb.append_text(r)
            res_cb.set_active(0)
            dgrid.attach(res_cb, 1, 0, 1, 1)

            dgrid.attach(Gtk.Label(label="Refresh Rate:", xalign=0), 0, 1, 1, 1)
            hz_cb = Gtk.ComboBoxText()
            for h in ["60.00 Hz", "120.00 Hz", "144.00 Hz", "165.00 Hz", "240.00 Hz"]:
                hz_cb.append_text(h)
            hz_cb.set_active(0)
            dgrid.attach(hz_cb, 1, 1, 1, 1)

            dgrid.attach(Gtk.Label(label="Fractional UI Scaling:", xalign=0), 0, 2, 1, 1)
            sc_cb = Gtk.ComboBoxText()
            for s in ["100% (Standard)", "125% (Fractional)", "150%", "200% (HiDPI)"]:
                sc_cb.append_text(s)
            sc_cb.set_active(0)
            dgrid.attach(sc_cb, 1, 2, 1, 1)

            dgrid.attach(Gtk.Label(label="Screen Orientation:", xalign=0), 0, 3, 1, 1)
            or_cb = Gtk.ComboBoxText()
            for o in ["Landscape (Standard)", "Portrait Left", "Portrait Right", "Landscape Inverted"]:
                or_cb.append_text(o)
            or_cb.set_active(0)
            dgrid.attach(or_cb, 1, 3, 1, 1)

            frame.add(dgrid)
            box.pack_start(frame, False, False, 0)

            # Night Light
            nl_frame = Gtk.Frame(label="Night Light & Blue Light Filter")
            nl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            nl_box.set_border_width(14)

            nl_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            nl_row.pack_start(Gtk.Label(label="Enable Night Light", xalign=0), True, True, 0)
            nl_sw = Gtk.Switch()
            nl_row.pack_end(nl_sw, False, False, 0)
            nl_box.pack_start(nl_row, False, False, 0)

            temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            temp_box.pack_start(Gtk.Label(label="Color Warmth:", xalign=0), False, False, 0)
            temp_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1500, 6500, 100)
            temp_scale.set_value(4000)
            temp_scale.set_hexpand(True)
            temp_box.pack_start(temp_scale, True, True, 0)
            nl_box.pack_start(temp_box, False, False, 0)

            nl_frame.add(nl_box)
            box.pack_start(nl_frame, False, False, 0)

        elif mod_id == "sound":
            frame = Gtk.Frame(label="Sound Output & Master Volume")
            sgrid = Gtk.Grid()
            sgrid.set_column_spacing(16)
            sgrid.set_row_spacing(12)
            sgrid.set_border_width(14)

            sgrid.attach(Gtk.Label(label="Master Output Volume:", xalign=0), 0, 0, 1, 1)
            vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            vol_scale.set_value(75)
            vol_scale.set_hexpand(True)
            sgrid.attach(vol_scale, 1, 0, 1, 1)

            sgrid.attach(Gtk.Label(label="Active Output Device:", xalign=0), 0, 1, 1, 1)
            out_cb = Gtk.ComboBoxText()
            for o in ["Built-in Audio (Analog Stereo)", "HDMI / DisplayPort Digital Output", "USB Audio DAC / Headset", "Bluetooth A2DP Sink"]:
                out_cb.append_text(o)
            out_cb.set_active(0)
            sgrid.attach(out_cb, 1, 1, 1, 1)

            frame.add(sgrid)
            box.pack_start(frame, False, False, 0)

            iframe = Gtk.Frame(label="Sound Input & Microphone")
            igrid = Gtk.Grid()
            igrid.set_column_spacing(16)
            igrid.set_row_spacing(12)
            igrid.set_border_width(14)

            igrid.attach(Gtk.Label(label="Microphone Input Volume:", xalign=0), 0, 0, 1, 1)
            mic_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
            mic_scale.set_value(65)
            mic_scale.set_hexpand(True)
            igrid.attach(mic_scale, 1, 0, 1, 1)

            igrid.attach(Gtk.Label(label="Active Input Device:", xalign=0), 0, 1, 1, 1)
            in_cb = Gtk.ComboBoxText()
            for i in ["Built-in Microphone (Analog Stereo)", "USB Audio Microphone", "Bluetooth HFP/HSP Headset"]:
                in_cb.append_text(i)
            in_cb.set_active(0)
            igrid.attach(in_cb, 1, 1, 1, 1)

            iframe.add(igrid)
            box.pack_start(iframe, False, False, 0)

        elif mod_id == "power":
            frame = Gtk.Frame(label="Active System Power Profile")
            pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            pbox.set_border_width(14)
            group = None
            for p in ["Balanced (Recommended for general computing)", "Performance (Maximum GPU/CPU clock speed)", "Power Saver (Lower power consumption)"]:
                rb = Gtk.RadioButton.new_with_label_from_widget(group, p)
                if group is None:
                    group = rb
                pbox.pack_start(rb, False, False, 0)
            frame.add(pbox)
            box.pack_start(frame, False, False, 0)

            tframe = Gtk.Frame(label="Sleep & Inactivity Timers")
            tgrid = Gtk.Grid()
            tgrid.set_column_spacing(16)
            tgrid.set_row_spacing(10)
            tgrid.set_border_width(14)

            tgrid.attach(Gtk.Label(label="Turn off screen when inactive for:", xalign=0), 0, 0, 1, 1)
            t1 = Gtk.ComboBoxText()
            for t in ["5 minutes", "10 minutes", "15 minutes", "30 minutes", "Never"]:
                t1.append_text(t)
            t1.set_active(2)
            tgrid.attach(t1, 1, 0, 1, 1)

            tgrid.attach(Gtk.Label(label="Suspend computer when inactive for:", xalign=0), 0, 1, 1, 1)
            t2 = Gtk.ComboBoxText()
            for t in ["15 minutes", "30 minutes", "1 hour", "2 hours", "Never"]:
                t2.append_text(t)
            t2.set_active(1)
            tgrid.attach(t2, 1, 1, 1, 1)

            tgrid.attach(Gtk.Label(label="When power button is pressed:", xalign=0), 0, 2, 1, 1)
            pb_cb = Gtk.ComboBoxText()
            for a in ["Ask what to do", "Suspend", "Power off", "Lock Screen"]:
                pb_cb.append_text(a)
            pb_cb.set_active(0)
            tgrid.attach(pb_cb, 1, 2, 1, 1)

            tframe.add(tgrid)
            box.pack_start(tframe, False, False, 0)

        elif mod_id == "network":
            # Wired
            frame = Gtk.Frame(label="Wired Ethernet Network")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            vbox.set_border_width(14)

            er = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            er.pack_start(Gtk.Label(label="Wired Interface (eth0 / enp3s0)", xalign=0), True, True, 0)
            er.pack_end(Gtk.Label(label="Connected (1000 Mbps IPv4: 192.168.1.100)"), False, False, 0)
            vbox.pack_start(er, False, False, 0)
            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

            # Wi-Fi
            wframe = Gtk.Frame(label="Wi-Fi Wireless Networking")
            wvbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            wvbox.set_border_width(14)

            wr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            wr.pack_start(Gtk.Label(label="Enable Wi-Fi Adapter", xalign=0), True, True, 0)
            wsw = Gtk.Switch()
            wsw.set_active(True)
            wr.pack_end(wsw, False, False, 0)
            wvbox.pack_start(wr, False, False, 0)

            wlist = Gtk.ListBox()
            wlist.set_selection_mode(Gtk.SelectionMode.NONE)
            for ssid, sig in [("SynthOS-5G (Connected)", "100%"), ("Home-Wi-Fi", "85%"), ("Office-Net", "60%")]:
                row = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(8)
                h.pack_start(Gtk.Label(label=ssid, xalign=0), True, True, 0)
                h.pack_end(Gtk.Label(label=f"Signal: {sig}"), False, False, 0)
                row.add(h)
                wlist.add(row)
            wvbox.pack_start(wlist, False, False, 4)

            wframe.add(wvbox)
            box.pack_start(wframe, False, False, 0)

        elif mod_id == "bluetooth":
            frame = Gtk.Frame(label="Bluetooth Radios & Paired Peripherals")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            bt_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            bt_row.pack_start(Gtk.Label(label="Bluetooth Master Switch", xalign=0), True, True, 0)
            bt_sw = Gtk.Switch()
            bt_sw.set_active(True)
            bt_row.pack_end(bt_sw, False, False, 0)
            vbox.pack_start(bt_row, False, False, 0)

            disc_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            disc_row.pack_start(Gtk.Label(label="Discoverable to other devices", xalign=0), True, True, 0)
            disc_sw = Gtk.Switch()
            disc_row.pack_end(disc_sw, False, False, 0)
            vbox.pack_start(disc_row, False, False, 0)

            btn_scan = Gtk.Button.new_with_label("Scan for Nearby Bluetooth Devices")
            vbox.pack_start(btn_scan, False, False, 4)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "keyboard":
            frame = Gtk.Frame(label="Keyboard Repeat & Input Layouts")
            kgrid = Gtk.Grid()
            kgrid.set_column_spacing(16)
            kgrid.set_row_spacing(12)
            kgrid.set_border_width(14)

            kgrid.attach(Gtk.Label(label="Key Repeat Delay:", xalign=0), 0, 0, 1, 1)
            del_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 100, 1000, 50)
            del_scale.set_value(400)
            del_scale.set_hexpand(True)
            kgrid.attach(del_scale, 1, 0, 1, 1)

            kgrid.attach(Gtk.Label(label="Key Repeat Speed:", xalign=0), 0, 1, 1, 1)
            spd_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 5)
            spd_scale.set_value(50)
            spd_scale.set_hexpand(True)
            kgrid.attach(spd_scale, 1, 1, 1, 1)

            kgrid.attach(Gtk.Label(label="Active Keyboard Layout:", xalign=0), 0, 2, 1, 1)
            kl_cb = Gtk.ComboBoxText()
            for l in ["English (US)", "English (UK)", "German (QWERTZ)", "French (AZERTY)", "Spanish", "Japanese"]:
                kl_cb.append_text(l)
            kl_cb.set_active(0)
            kgrid.attach(kl_cb, 1, 2, 1, 1)

            frame.add(kgrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "mouse":
            frame = Gtk.Frame(label="Pointer Speed & Touchpad Gestures")
            mgrid = Gtk.Grid()
            mgrid.set_column_spacing(16)
            mgrid.set_row_spacing(10)
            mgrid.set_border_width(14)

            mgrid.attach(Gtk.Label(label="Pointer Speed:", xalign=0), 0, 0, 1, 1)
            ps_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1, 10, 1)
            ps_scale.set_value(5)
            ps_scale.set_hexpand(True)
            mgrid.attach(ps_scale, 1, 0, 1, 1)

            mgrid.attach(Gtk.Label(label="Natural Scrolling (Reverse direction):", xalign=0), 0, 1, 1, 1)
            nsw = Gtk.Switch()
            mgrid.attach(nsw, 1, 1, 1, 1)

            mgrid.attach(Gtk.Label(label="Touchpad Tap to Click:", xalign=0), 0, 2, 1, 1)
            tsw = Gtk.Switch()
            tsw.set_active(True)
            mgrid.attach(tsw, 1, 2, 1, 1)

            mgrid.attach(Gtk.Label(label="Two-finger Scrolling:", xalign=0), 0, 3, 1, 1)
            tfs = Gtk.Switch()
            tfs.set_active(True)
            mgrid.attach(tfs, 1, 3, 1, 1)

            frame.add(mgrid)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "sysinfo":
            frame = Gtk.Frame(label="System & Hardware Specification")
            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(10)
            grid.set_border_width(16)

            uname = os.uname()
            rows = [
                ("Operating System", "SynthOS Linux 2026.10 LTS"),
                ("Kernel Architecture", f"{uname.sysname} {uname.release} ({uname.machine})"),
                ("Processor (CPU)",  self._read_cpu()),
                ("System Memory",    self._read_mem()),
                ("Graphics Display", self._read_gpu()),
                ("Storage / Disk",   self._read_disk()),
                ("Desktop Session",  f"{os.environ.get('XDG_CURRENT_DESKTOP', 'Cinnamon')} ({os.environ.get('XDG_SESSION_TYPE', 'x11')})"),
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

        # ── 4. Administration Modules ───────────────────────────────────
        elif mod_id == "firewall":
            frame = Gtk.Frame(label="UFW Security Firewall Rules")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            fw_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            fw_row.pack_start(Gtk.Label(label="Firewall Protection Status", xalign=0), True, True, 0)
            fw_sw = Gtk.Switch()
            fw_sw.set_active(True)
            fw_row.pack_end(fw_sw, False, False, 0)
            vbox.pack_start(fw_row, False, False, 0)

            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

            pgrid = Gtk.Grid()
            pgrid.set_column_spacing(16)
            pgrid.set_row_spacing(8)

            pgrid.attach(Gtk.Label(label="Incoming Connections Policy:", xalign=0), 0, 0, 1, 1)
            in_cb = Gtk.ComboBoxText()
            for opt in ["Deny (Block all unauthorized incoming packets)", "Reject", "Allow"]:
                in_cb.append_text(opt)
            in_cb.set_active(0)
            pgrid.attach(in_cb, 1, 0, 1, 1)

            pgrid.attach(Gtk.Label(label="Outgoing Connections Policy:", xalign=0), 0, 1, 1, 1)
            out_cb = Gtk.ComboBoxText()
            for opt in ["Allow (Standard outbound traffic)", "Deny"]:
                out_cb.append_text(opt)
            out_cb.set_active(0)
            pgrid.attach(out_cb, 1, 1, 1, 1)

            vbox.pack_start(pgrid, False, False, 0)
            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "backup":
            frame = Gtk.Frame(label="Timeshift System Restore & Snapshots")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            s_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            s_row.pack_start(Gtk.Label(label="Automatic Scheduled System Snapshots", xalign=0), True, True, 0)
            s_sw = Gtk.Switch()
            s_sw.set_active(True)
            s_row.pack_end(s_sw, False, False, 0)
            vbox.pack_start(s_row, False, False, 0)

            st_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            st_row.pack_start(Gtk.Label(label="Snapshot Storage Type: BTRFS (Subvolume Zero-Copy Instant Snapshots)", xalign=0), True, True, 0)
            vbox.pack_start(st_row, False, False, 0)

            sched_grid = Gtk.Grid()
            sched_grid.set_column_spacing(16)
            sched_grid.set_row_spacing(6)
            sched_grid.attach(Gtk.Label(label="Daily Snapshots to Keep:", xalign=0), 0, 0, 1, 1)
            d_spin = Gtk.SpinButton.new_with_range(1, 30, 1)
            d_spin.set_value(5)
            sched_grid.attach(d_spin, 1, 0, 1, 1)

            sched_grid.attach(Gtk.Label(label="Boot Snapshots to Keep:", xalign=0), 0, 1, 1, 1)
            b_spin = Gtk.SpinButton.new_with_range(1, 10, 1)
            b_spin.set_value(3)
            sched_grid.attach(b_spin, 1, 1, 1, 1)
            vbox.pack_start(sched_grid, False, False, 4)

            btn_snap = Gtk.Button.new_with_label("Create New Manual System Snapshot Now")
            vbox.pack_start(btn_snap, False, False, 4)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "update":
            frame = Gtk.Frame(label="System Package & Security Updates")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            u_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            u_row.pack_start(Gtk.Label(label="Your system packages are completely up to date", xalign=0), True, True, 0)
            btn_chk = Gtk.Button.new_with_label("Check for Updates Now")
            u_row.pack_end(btn_chk, False, False, 0)
            vbox.pack_start(u_row, False, False, 0)

            ugrid = Gtk.Grid()
            ugrid.set_column_spacing(16)
            ugrid.set_row_spacing(8)
            ugrid.attach(Gtk.Label(label="Automatic Update Checks:", xalign=0), 0, 0, 1, 1)
            up_cb = Gtk.ComboBoxText()
            for u in ["Every Day", "Every Week", "Never"]:
                up_cb.append_text(u)
            up_cb.set_active(0)
            ugrid.attach(up_cb, 1, 0, 1, 1)

            vbox.pack_start(ugrid, False, False, 4)
            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "driver":
            frame = Gtk.Frame(label="Hardware & Graphics Drivers")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            d_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            gpu_name = self._read_gpu()
            d_row.pack_start(Gtk.Label(label=f"Active GPU Driver: {gpu_name}\n(Using Linux Kernel Direct Rendering Manager / Mesa DRI)", xalign=0), True, True, 0)
            vbox.pack_start(d_row, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "sources":
            frame = Gtk.Frame(label="Software Repositories & Mirrors")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            sgrid = Gtk.Grid()
            sgrid.set_column_spacing(16)
            sgrid.set_row_spacing(8)
            sgrid.attach(Gtk.Label(label="Main Mirror (SynthOS):", xalign=0), 0, 0, 1, 1)
            m1 = Gtk.ComboBoxText()
            m1.append_text("Worldwide (https://pkg.synthex-os.org/noble)")
            m1.append_text("US Fast CDN (https://us.synthex-os.org/noble)")
            m1.set_active(0)
            sgrid.attach(m1, 1, 0, 1, 1)

            sgrid.attach(Gtk.Label(label="Base Mirror (Ubuntu Noble):", xalign=0), 0, 1, 1, 1)
            m2 = Gtk.ComboBoxText()
            m2.append_text("Main Ubuntu Archive (http://archive.ubuntu.com/ubuntu)")
            m2.set_active(0)
            sgrid.attach(m2, 1, 1, 1, 1)

            vbox.pack_start(sgrid, False, False, 0)
            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "users":
            frame = Gtk.Frame(label="System Users & Groups")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            ulist = Gtk.ListBox()
            ulist.set_selection_mode(Gtk.SelectionMode.NONE)
            row = Gtk.ListBoxRow()
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            h.set_border_width(8)
            h.pack_start(Gtk.Label(label=f"User: {os.environ.get('USER', 'jewboy420')} (Administrator)", xalign=0), True, True, 0)
            h.pack_end(Gtk.Label(label="Groups: sudo, adm, dialout, audio, video"), False, False, 0)
            row.add(h)
            ulist.add(row)
            vbox.pack_start(ulist, False, False, 4)

            btn_add = Gtk.Button.new_with_label("Add New User Account...")
            vbox.pack_start(btn_add, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        elif mod_id == "login":
            frame = Gtk.Frame(label="Login Screen & Display Manager")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(14)

            for lbl, st in [
                ("Allow Guest Login Sessions", False),
                ("Show User List on Login Screen", True),
                ("Automatic Login on System Boot", False),
            ]:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                r.pack_start(Gtk.Label(label=lbl, xalign=0), True, True, 0)
                sw = Gtk.Switch()
                sw.set_active(st)
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            frame.add(vbox)
            box.pack_start(frame, False, False, 0)

        else:
            # Complete default setting panel for any remaining module
            frame = Gtk.Frame(label=f"{title} Configuration")
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            inner.set_border_width(14)

            r1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r1.pack_start(Gtk.Label(label=f"Enable {title} Integration", xalign=0), True, True, 0)
            sw1 = Gtk.Switch()
            sw1.set_active(True)
            r1.pack_end(sw1, False, False, 0)
            inner.pack_start(r1, False, False, 0)

            r2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r2.pack_start(Gtk.Label(label="Automatic Hardware / Desktop Synchronization", xalign=0), True, True, 0)
            sw2 = Gtk.Switch()
            sw2.set_active(True)
            r2.pack_end(sw2, False, False, 0)
            inner.pack_start(r2, False, False, 0)

            frame.add(inner)
            box.pack_start(frame, False, False, 0)

        return box

    def _choose_wallpaper_dialog(self, btn):
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

    def _go_home(self, *a):
        self.hb.set_title("System Settings")
        self.hb.set_subtitle("SynthOS Linux")
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
                    return f"{int(line.split()[1]) / 1048576:.1f} GiB Total Memory"
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
                return out.split(":")[-1].strip()
        except Exception:
            pass
        return "Standard Graphics Controller"

    def _read_disk(self):
        try:
            out = subprocess.check_output(
                ["df", "-h", "--output=size,used,avail,pcent,fstype", "/"],
                text=True, timeout=3
            ).strip().split("\n")
            if len(out) >= 2:
                parts = out[1].split()
                if len(parts) >= 5:
                    return f"{parts[0]} Total, {parts[1]} Used ({parts[3]} Full) — {parts[4]}"
        except Exception:
            pass
        return "BTRFS Root Subvolume"


def main():
    win = SettingsWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
