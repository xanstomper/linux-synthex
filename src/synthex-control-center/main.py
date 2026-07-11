#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Control Center — System settings hub
# Launches specialized pages or delegates to systemsettings5

import sys, os, subprocess, json
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

APP_ID   = "org.synthos.ControlCenter"
VERSION  = "2026.10"

PAGES = [
    # (id, label, icon, subtitle, cmd_or_page)
    ("display",    "Display",        "video-display",               "Resolution, refresh, multi-monitor",    ["systemsettings5", "kcm_kscreen"]),
    ("sound",      "Sound",          "audio-volume-medium",         "Volume, devices, microphone",           ["systemsettings5", "kcm_pulseaudio"]),
    ("network",    "Network",        "network-wired",               "Wi-Fi, Ethernet, VPN",                  ["nm-connection-editor"]),
    ("bluetooth",  "Bluetooth",      "bluetooth",                   "Pair and manage devices",               ["systemsettings5", "kcm_bluetooth"]),
    ("appearance", "Appearance",     "preferences-desktop-theme",   "Themes, colors, fonts, icons",          ["systemsettings5", "kcm_lookandfeel"]),
    ("wallpaper",  "Wallpaper",      "preferences-desktop-wallpaper","Desktop background",                   ["systemsettings5", "kcm_wallpaper"]),
    ("keyboard",   "Keyboard",       "input-keyboard",              "Shortcuts, layouts, input",             ["systemsettings5", "kcm_keyboard"]),
    ("mouse",      "Mouse & Touch",  "input-mouse",                 "Pointer speed, scrolling, gestures",    ["systemsettings5", "kcm_mouse"]),
    ("power",      "Power",          "battery",                     "Sleep, hibernate, energy saving",       ["systemsettings5", "kcm_powerprofilesdevice"]),
    ("gaming",     "Gaming",         "applications-games",          "GameMode, profiles, GPU tuning",        ["synthex-gaming-center"]),
    ("gpu",        "GPU",            "video-display",               "Driver, Vulkan, VRAM info",             ["/usr/lib/synthex/synthex-gpu-setup"]),
    ("security",   "Security",       "security-medium",             "Firewall, audit, updates",              ["/usr/lib/synthex/synthex-security-dashboard"]),
    ("updates",    "Updates",        "system-software-update",      "System and package updates",            ["/usr/lib/synthex/synthex-update-manager"]),
    ("apps",       "Applications",   "system-run",                  "Default apps, Flatpak, App Manager",   ["/usr/lib/synthex/synthex-app-manager"]),
    ("disk",       "Disk",           "drive-harddisk",              "Storage, health, partitions",           ["/usr/lib/synthex/synthex-disk-health"]),
    ("users",      "Users",          "system-users",                "Accounts, passwords, avatar",           ["systemsettings5", "kcm_users"]),
    ("datetime",   "Date & Time",    "preferences-system-time",     "Clock, timezone, NTP",                  ["systemsettings5", "kcm_clock"]),
    ("locale",     "Language",       "preferences-desktop-locale",  "Region, formats, input method",         ["systemsettings5", "kcm_translations"]),
    ("startup",    "Startup",        "system-run",                  "Autostart, sessions, SDDM",             ["systemsettings5", "kcm_autostart"]),
    ("about",      "About SynthOS",  "help-about",                  "Version, hardware info, licenses",      ["_about"]),
]

def run(cmd):
    try:
        subprocess.Popen(cmd)
    except FileNotFoundError:
        subprocess.Popen(cmd[1:])  # try without first arg


class PageTile(Gtk.Button):
    def __init__(self, page_id, label, icon_name, subtitle, action):
        super().__init__()
        self.page_id = page_id
        self.action  = action

        self.add_css_class("page-tile")
        self.set_hexpand(False)
        self.set_size_request(170, 110)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        box.set_margin_top(8); box.set_margin_bottom(8)

        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(40)
        icon.add_css_class("tile-icon")
        box.append(icon)

        lbl = Gtk.Label(label=label)
        lbl.add_css_class("tile-label")
        lbl.set_justify(Gtk.Justification.CENTER)
        box.append(lbl)

        sub = Gtk.Label(label=subtitle)
        sub.add_css_class("tile-subtitle")
        sub.set_justify(Gtk.Justification.CENTER)
        sub.set_wrap(True)
        sub.set_max_width_chars(20)
        sub.set_ellipsize(Pango.EllipsizeMode.END)
        box.append(sub)

        self.set_child(box)


class AboutDialog(Adw.MessageDialog):
    def __init__(self, parent):
        hw = self._get_hw()
        super().__init__(
            heading="About SynthOS",
            body=f"SynthOS Linux  {VERSION}\n\n"
                 f"CPU: {hw.get('cpu','Unknown')}\n"
                 f"RAM: {hw.get('ram','Unknown')}\n"
                 f"GPU: {hw.get('gpu','Unknown')}\n"
                 f"Kernel: {hw.get('kernel','Unknown')}\n\n"
                 f"Built with ♥ by the SynthOS community\n"
                 f"https://synthos-os.org",
        )
        self.add_response("ok", "Close")
        self.set_transient_for(parent)

    @staticmethod
    def _get_hw():
        info = {}
        try:
            info["kernel"] = subprocess.check_output(["uname","-r"], text=True).strip()
        except Exception:
            pass  # hardware detection is best-effort
        try:
            lines = open("/proc/cpuinfo").readlines()
            for l in lines:
                if "model name" in l:
                    info["cpu"] = l.split(":")[1].strip()
                    break
        except Exception:
            pass  # hardware detection is best-effort
        try:
            mem = int(open("/proc/meminfo").readline().split()[1])
            info["ram"] = f"{mem//1024//1024} GB"
        except Exception:
            pass  # hardware detection is best-effort
        try:
            gpu = subprocess.check_output(
                ["lspci","-mm"], text=True, stderr=subprocess.DEVNULL
            )
            for l in gpu.splitlines():
                if "VGA" in l or "3D" in l or "Display" in l:
                    info["gpu"] = l.split('"')[5] if '"' in l else l
                    break
        except Exception:
            pass  # hardware detection is best-effort
        return info


class ControlCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Control Center")
        self.set_default_size(900, 640)
        self._setup_css()
        self._build_ui()

    def _setup_css(self):
        css = """
        .page-tile {
            background: alpha(white, 0.04);
            border-radius: 12px;
            border: 1px solid alpha(white, 0.08);
            transition: background 120ms ease;
        }
        .page-tile:hover {
            background: alpha(white, 0.10);
            border-color: alpha(white, 0.18);
        }
        .tile-icon { color: #B0CCEE; }
        .tile-label { font-weight: bold; font-size: 13px; }
        .tile-subtitle { font-size: 10px; color: #888899; }
        .section-header { font-size: 11px; font-weight: bold; color: #6688AA;
                          letter-spacing: 1px; margin-top: 8px; margin-bottom: 2px; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        # Header bar
        hb = Adw.HeaderBar()
        hb.set_title_widget(Adw.WindowTitle(
            title="Control Center", subtitle=f"SynthOS {VERSION}"
        ))
        # Search button
        search_btn = Gtk.ToggleButton(icon_name="system-search-symbolic")
        search_btn.connect("toggled", self._on_search_toggle)
        hb.pack_end(search_btn)
        outer.append(hb)

        # Search bar (hidden by default)
        self._search_bar = Gtk.SearchBar()
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search settings…")
        self._search_entry.connect("search-changed", self._on_search)
        self._search_bar.set_child(self._search_entry)
        outer.append(self._search_bar)
        search_btn.bind_property("active", self._search_bar, "search-mode-enabled")

        # Scrollable grid
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        outer.append(scroll)

        self._main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._main_box.set_margin_start(20); self._main_box.set_margin_end(20)
        self._main_box.set_margin_top(12); self._main_box.set_margin_bottom(20)
        scroll.set_child(self._main_box)

        self._tiles: list[PageTile] = []
        self._build_tiles()

    def _build_tiles(self):
        # Group pages into sections
        sections = {
            "Hardware":      ["display","sound","network","bluetooth","gpu","disk","power"],
            "Personalization": ["appearance","wallpaper","keyboard","mouse"],
            "System":        ["apps","updates","startup","users","datetime","locale","security"],
            "SynthOS":       ["gaming","about"],
        }

        page_map = {p[0]: p for p in PAGES}

        for section_name, page_ids in sections.items():
            # Section header
            hdr = Gtk.Label(label=section_name.upper())
            hdr.set_xalign(0)
            hdr.add_css_class("section-header")
            self._main_box.append(hdr)

            # Flow box row
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_min_children_per_line(3)
            flow.set_max_children_per_line(8)
            flow.set_column_spacing(8)
            flow.set_row_spacing(8)
            flow.set_margin_bottom(8)
            self._main_box.append(flow)

            for pid in page_ids:
                if pid not in page_map:
                    continue
                _, label, icon, subtitle, action = page_map[pid]
                tile = PageTile(pid, label, icon, subtitle, action)
                tile.connect("clicked", self._on_tile_clicked)
                flow.append(tile)
                self._tiles.append(tile)

    def _on_tile_clicked(self, tile: PageTile):
        if tile.action == ["_about"]:
            dlg = AboutDialog(self)
            dlg.present()
        else:
            try:
                run(tile.action)
            except Exception as e:
                dlg = Adw.MessageDialog(
                    heading="Could not open",
                    body=str(e),
                )
                dlg.add_response("ok","OK")
                dlg.set_transient_for(self)
                dlg.present()

    def _on_search_toggle(self, btn):
        pass  # Handled by bind_property

    def _on_search(self, entry):
        query = entry.get_text().lower()
        for tile in self._tiles:
            visible = (not query
                       or query in tile.page_id
                       or query in tile.get_child().get_first_child().get_next_sibling().get_label().lower()
                       or query in tile.get_tooltip_text().lower() if tile.get_tooltip_text() else False)
            tile.set_visible(visible)


class ControlCenterApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: ControlCenterWindow(a).present())


if __name__ == "__main__":
    app = ControlCenterApp()
    sys.exit(app.run(sys.argv))
