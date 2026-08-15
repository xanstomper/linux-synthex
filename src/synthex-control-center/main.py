#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
SynthOS System Settings — professional settings center.
Shell: grouped sidebar (Personal / Desktop / Hardware / System), deep search,
URI deep-linking (synthex-settings://category), toasts.
Pages: synthex_pages_a.py (Personal & Desktop), synthex_pages_b.py (Hardware & System).
Design system: synthex_design.py. Backends: synth_system_adapters.py + synth_platform_adapters.py.
"""

import os
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Gio

import synthex_design as design
from synthex_design import install_design, label, Toast, entity_card, badge, button, dot
import synthex_pages_a as pages_a
import synthex_pages_b as pages_b
import synthex_pages_c as pages_c
from synth_system_adapters import SystemAdapter

# ── Sidebar registry: (id, title, icon, page-builder, searchable keywords) ──
# Grouped like GNOME Settings / macOS System Settings.

SIDEBAR = [
    ("Personal", [
        ("appearance",   "Appearance",       "preferences-desktop-theme",     pages_a.build_appearance,
         "theme themes icons cursor dark light accent fonts effects ricing rice import"),
        ("backgrounds",  "Backgrounds",      "preferences-desktop-wallpaper", pages_a.build_backgrounds,
         "wallpaper wallpapers slideshow background picture desktop"),
        ("nightlight",   "Night Light",      "night-light",                   pages_a.build_nightlight,
         "redshift night light blue filter color temperature f.lux"),
        ("notifications","Notifications",    "preferences-desktop-notification", pages_a.build_notifications,
         "notifications do not disturb dnd popup banner sounds lock screen"),
        ("privacy",      "Privacy Center",   "preferences-system-privacy",    pages_c.build_privacy_center,
         "privacy location camera microphone permissions broker telemetry timeline kill switches zero telemetry AI audit clear recent files trash"),
        ("spoofgoof",    "SpoofGoof Shield", "network-vpn",                   pages_c.build_spoofgoof,
         "spoofgoof spoof privacy mac address randomize cloaking fingerprint traffic chaff decoy morphing dpi vpn identity network obfuscation stealth"),
        ("online",       "Online Accounts",  "applications-internet",         pages_a.build_online_accounts,
         "online accounts google nextcloud caldav mail calendar contacts files"),
        ("region",       "Language & Region","cs-language",                   pages_a.build_region,
         "language locale region input method ibus fcitx keyboard formats date time 24 hour"),
        ("account",      "Account Details",  "avatar-default",                pages_a.build_account,
         "account profile user full name shell groups login"),
        ("accessibility","Accessibility",    "preferences-desktop-accessibility", pages_a.build_accessibility,
         "accessibility a11y screen reader orca magnifier large text high contrast sticky keys slow keys bounce mouse keys hover click on-screen keyboard"),
        ("apps",         "Installed Apps",   "preferences-desktop-applications", pages_c.build_apps,
         "apps applications installed uninstall remove cache reset programs software"),
    ]),


    ("Desktop", [
        ("desktop",      "Desktop",          "cs-desktop",                    pages_a.build_desktop,
         "desktop icons hot corners trash volumes home"),
        ("windows",      "Windows",          "preferences-system-windows",    pages_a.build_windows,
         "windows titlebar focus placement double click raise maximize"),
        ("workspaces",   "Workspaces",       "view-grid",                     pages_a.build_workspaces,
         "workspaces virtual desktops dynamic osd pager"),
        ("panels",       "Panels",           "cs-panel",                      pages_a.build_panels,
         "panel panels taskbar bar autohide height applets"),
        ("applets",      "Applets",          "preferences-plugin",            pages_a.build_applets,
         "applets panel plugins spices systray"),
        ("desklets",     "Desklets",         "preferences-desktop-widgets",   pages_a.build_desklets,
         "desklets desktop widgets clock weather"),
        ("extensions",   "Extensions",       "application-x-extension",       pages_a.build_extensions,
         "extensions spices addons"),
        ("gestures",     "Gestures",         "input-touchpad",                pages_a.build_gestures,
         "gestures touchegg multitouch swipe pinch touchscreen"),
        ("preferred",    "Preferred Apps",   "preferences-desktop-default-applications", pages_a.build_preferred_apps,
         "default preferred applications browser mail editor video music pdf terminal"),
        ("startup",      "Startup Apps",     "preferences-session",           pages_a.build_startup,
         "startup autostart login launch boot applications"),
        ("screensaver",  "Screen Lock",      "system-lock-screen",            pages_b.build_screensaver,
         "screensaver lock screen idle blank away message"),
    ]),
    ("Hardware", [
        ("display",      "Display",          "preferences-desktop-display",   pages_b.build_display,
         "display resolution refresh rate scaling rotation monitor brightness night vrr hdr"),
        ("sound",        "Sound",            "multimedia-volume-control",     pages_b.build_sound,
         "sound audio volume output input microphone pipeWire speakers headphones per-app"),
        ("mouse",        "Mouse & Touchpad", "input-mouse",                   pages_b.build_mouse,
         "mouse touchpad pointer speed natural scrolling tap click acceleration xinput gestures"),
        ("keyboard",     "Keyboard",         "preferences-desktop-keyboard",  pages_b.build_keyboard,
         "keyboard layout shortcuts compose repeat delay typing layouts"),
        ("tablet",       "Graphics Tablet",  "input-tablet",                  pages_b.build_tablet,
         "wacom tablet stylus pen pressure buttons"),
        ("printers",     "Printers",         "cs-printer",                    pages_b.build_printers,
         "printers scanner cups printing queues test page"),
        ("bluetooth",    "Bluetooth",        "bluetooth",                     pages_b.build_bluetooth,
         "bluetooth devices pairing connect audio headset"),
        ("thunderbolt",  "Thunderbolt",      "thunderbolt",                   pages_b.build_thunderbolt,
         "thunderbolt bolt dock usb-c authorize"),
        ("color",        "Color",            "preferences-color",             pages_b.build_color,
         "color icc profile calibration colormgr display"),
        ("power",        "Power",            "preferences-system-power",      pages_b.build_power,
         "power battery suspend hibernate lid profile charging upower"),
        ("storage",      "Storage",          "drive-harddisk",                pages_b.build_storage,
         "storage disks partitions btrfs trim ssd lsblk mounts filesystems"),
        ("drivers",      "Drivers",          "applications-science",          pages_b.build_drivers,
         "drivers gpu nvidia amd intel mesa vulkan akmod firmware fwupd rpmfusion"),
        ("gaming",       "Gaming",           "applications-games",            pages_c.build_gaming,
         "gaming gamemode cpu governor zram ananicy mangohud gamescope performance fps latency"),
        ("devices",      "Cameras & Gamepads","camera-video",                 pages_c.build_devices,
         "devices cameras video v4l2 webcam gamepad joystick controller game controller calibration"),
    ]),
    ("System", [
        ("network",      "Network",          "preferences-system-network",    pages_b.build_network,
         "network wifi ethernet vpn proxy dns nmcli wireless"),
        ("aegis",        "Aegis Security",   "security-high",                 pages_c.build_aegis,
         "aegis antivirus malware endpoint protection behavioral reverse shell quarantine incidents scan shields eicar threat"),
        ("security",     "Security & Firewall","security-high",               pages_b.build_security,
         "security firewall firewalld ufw selinux encryption luks secure boot ssh tpm mitigations"),
        ("doctor",       "System Doctor",    "applications-engineering",      pages_c.build_doctor,
         "doctor repair diagnosis self-healing anti-brick bootloader fstab packages rollback snapshots auto-repair"),
        ("sources",      "Software Sources", "package-x-generic",             pages_b.build_sources,
         "sources repositories repos dnf copr rpmfusion flatpak flathub mirrors"),
        ("updates",      "Update Manager",   "system-software-update",        pages_b.build_updates,
         "updates upgrade packages dnf flatpak automatic history"),
        ("timeshift",    "Timeshift",        "timebench",                     pages_b.build_timeshift,
         "timeshift snapshots backup btrfs restore rollback recovery"),
        ("login",        "Login Window",     "cs-user",                       pages_b.build_login,
         "login sddm lightdm greeter autologin session theme display manager"),
        ("datetime",     "Date & Time",      "preferences-system-time",       pages_b.build_datetime,
         "date time timezone ntp clock 24 hour rtc sync"),
        ("sysinfo",      "System Info",      "dialog-information",            pages_b.build_system_info,
         "system info about hostname kernel cpu memory diagnostics journal specs hardware"),
        ("users",        "Users & Groups",   "system-users",                  pages_a.build_users,
         "users accounts groups administrator password wheel sudo create remove"),
    ]),
]

ALL_PAGES = {pid: (title, icon, builder, kw)
             for _group, items in SIDEBAR for (pid, title, icon, builder, kw) in items}


class SidebarRow(Gtk.ListBoxRow):
    def __init__(self, pid, title, icon):
        super().__init__(selectable=True, activatable=True)
        self.pid = pid
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_border_width(6)
        img = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU)
        img.get_style_context().add_class("sidebar-icon")
        box.pack_start(img, False, False, 0)
        box.pack_start(label(title, "sidebar-title"), False, False, 0)
        self.add(box)
        self.get_style_context().add_class("sidebar-item")


class SettingsWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_page="appearance"):
        super().__init__(application=app, title="System Settings")
        self.set_default_size(1220, 860)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.current_pid = None

        install_design(self)
        self.get_style_context().add_class("settings-window")

        # ── Header ─────────────────────────────────────────────────────
        hb = Gtk.HeaderBar(show_close_button=True)
        hb.set_show_close_button(True)
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.START)
        title_box.pack_start(label("System Settings", "app-title"), False, False, 0)
        hb.set_custom_title(title_box)
        self.set_titlebar(hb)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search settings…")
        self.search_entry.set_width_chars(32)
        self.search_entry.get_style_context().add_class("settings-search")
        self.search_entry.connect("search-changed", self._on_search)
        hb.pack_end(self.search_entry)

        btn_back = Gtk.Button.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        btn_back.set_tooltip_text("Back")
        btn_back.connect("clicked", lambda b: self.show_page(self.current_pid or "appearance"))
        hb.pack_start(btn_back)

        # ── Layout ─────────────────────────────────────────────────────
        self.main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(self.main)

        # Sidebar
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.get_style_context().add_class("sidebar")
        sidebar_box.set_size_request(246, -1)
        self.sidebar_scroll = Gtk.ScrolledWindow()
        self.sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar_scroll.get_style_context().add_class("sidebar-scroll")
        self.sidebar = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.sidebar.get_style_context().add_class("sidebar")
        self.sidebar.set_header_func(self._sidebar_headers)
        self.sidebar.connect("row-selected", lambda lb, row: row and self.show_page(row.pid))
        self.sidebar_rows = {}
        for group, items in SIDEBAR:
            for pid, title, icon, _b, _kw in items:
                row = SidebarRow(pid, title, icon)
                self.sidebar.add(row)
                self.sidebar_rows[pid] = row
        self.sidebar_scroll.add(self.sidebar)
        sidebar_box.pack_start(self.sidebar_scroll, True, True, 0)
        self.main.pack_start(sidebar_box, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.get_style_context().add_class("sidebar-sep")
        self.main.pack_start(sep, False, False, 0)

        # Content — Overlay hosts the scrolled content + toast
        self.content_scroll = Gtk.ScrolledWindow()
        self.content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content_scroll.get_style_context().add_class("content-scroll")

        self.toast = Toast()
        overlay = Gtk.Overlay()
        overlay.add(self.content_scroll)
        overlay.add_overlay(self.toast)
        self.main.pack_start(overlay, True, True, 0)

        self.show_all()
        self.show_page(initial_page)

    # ── Sidebar group headers (once per group, above its first row) ───
    @staticmethod
    def _group_of(pid):
        for gname, items in SIDEBAR:
            if any(i[0] == pid for i in items):
                return gname
        return None

    def _sidebar_headers(self, row, before, data=None):
        if before is None or self._group_of(before.pid) != self._group_of(row.pid):
            if not isinstance(row.get_header(), Gtk.Label):
                h = Gtk.Label(label=(self._group_of(row.pid) or "").upper(), xalign=0)
                h.get_style_context().add_class("sidebar-group")
                row.set_header(h)
        else:
            row.set_header(None)

    # ── Page switching ────────────────────────────────────────────────
    def show_page(self, pid):
        if pid not in ALL_PAGES:
            pid = "appearance"
        title, icon, builder, _kw = ALL_PAGES[pid]
        try:
            page = builder(self.toast)
        except Exception as exc:
            page = self._error_page(pid, title, exc)
        if self.content_scroll.get_child():
            self.content_scroll.remove(self.content_scroll.get_child())
        self.content_scroll.add(page)
        page.show_all()
        self.current_pid = pid
        if pid in self.sidebar_rows:
            self.sidebar.select_row(self.sidebar_rows[pid])
        # Pre-select while searching
        self.sidebar_rows[pid].show_all()

    def _error_page(self, pid, title, exc):
        from synthex_design import ContentColumn, PageHeader
        col = ContentColumn()
        col.add(PageHeader(title, "This page failed to load", badges=[("Error", "err")]))
        err = label(str(exc)[:300], "row-sub")
        err.set_selectable(True)
        col.add(err)
        return col

    # ── Deep search ───────────────────────────────────────────────────
    def _on_search(self, entry):
        q = entry.get_text().strip().lower()
        for pid, row in self.sidebar_rows.items():
            _t, _i, _b, kw = ALL_PAGES[pid]
            title = _t.lower()
            visible = (not q) or q in title or q in kw or any(w.startswith(q) for w in kw.split())
            row.set_visible(visible)


def _pick_initial_page():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("synthex-settings://"):
            arg = arg.split("://", 1)[1]
        return arg if arg in ALL_PAGES else "appearance"
    return "appearance"


def main():
    win = SettingsWindow(None, _pick_initial_page())
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
