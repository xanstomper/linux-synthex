#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS App Manager — browse, install, and remove applications

import sys, os, subprocess, threading, json, shutil
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

APP_ID = "org.synthos.AppManager"

CATEGORIES = [
    ("All",           None,                   "applications-other"),
    ("Internet",      "Network;Internet",      "network-workgroup"),
    ("Productivity",  "Office",                "x-office-address-book"),
    ("Development",   "Development",           "applications-development"),
    ("Gaming",        "Game",                  "applications-games"),
    ("Media",         "AudioVideo;Graphics",   "applications-multimedia"),
    ("System",        "System;Utility",        "applications-system"),
    ("Education",     "Education;Science",     "applications-science"),
]

# Curated app catalogue (name, label, desc, icon, source, category)
APP_CATALOGUE = [
    # Browsers
    ("firefox",        "Firefox",          "Fast, private web browser",      "firefox",           "dnf",     "Internet"),
    ("chromium",       "Chromium",         "Open-source Chrome browser",     "chromium-browser",  "dnf",     "Internet"),
    ("brave-browser",  "Brave",            "Privacy-first browser",          "brave-browser",     "flatpak", "Internet"),
    ("vivaldi",        "Vivaldi",          "Highly customizable browser",    "vivaldi",           "flatpak", "Internet"),
    ("microsoft-edge-stable","Edge",       "Microsoft Edge browser",         "microsoft-edge",    "flatpak", "Internet"),
    # Messaging
    ("org.signal.Signal","Signal",         "Encrypted private messaging",    "signal-desktop",    "flatpak", "Internet"),
    ("com.discordapp.Discord","Discord",   "Voice, video & text chat",       "discord",           "flatpak", "Internet"),
    ("com.slack.Slack", "Slack",           "Team messaging & collaboration", "slack",             "flatpak", "Internet"),
    ("im.riot.Riot",    "Element",         "Matrix decentralized chat",      "element-desktop",   "flatpak", "Internet"),
    ("org.telegram.desktop","Telegram",    "Cloud messaging app",            "telegram-desktop",  "flatpak", "Internet"),
    # Productivity
    ("org.libreoffice.LibreOffice","LibreOffice","Full office suite",         "libreoffice-writer","flatpak","Productivity"),
    ("com.obsproject.Studio","OBS Studio", "Screen recording & streaming",   "obs",               "flatpak", "Media"),
    ("org.gimp.GIMP",   "GIMP",           "Image editing",                  "gimp",              "flatpak", "Media"),
    ("org.inkscape.Inkscape","Inkscape",   "Vector graphics editor",         "inkscape",          "flatpak", "Media"),
    ("org.kde.kdenlive","Kdenlive",        "Video editor",                   "kdenlive",          "flatpak", "Media"),
    ("org.blender.Blender","Blender",      "3D creation suite",              "blender",           "flatpak", "Media"),
    ("org.audacityteam.Audacity","Audacity","Audio editor",                  "audacity",          "flatpak", "Media"),
    ("org.spotify.Client","Spotify",       "Music streaming",                "spotify-client",    "flatpak", "Media"),
    # Development
    ("com.visualstudio.code","VS Code",    "Code editor by Microsoft",       "code",              "flatpak", "Development"),
    ("com.jetbrains.IntelliJ-IDEA-Community","IntelliJ IDEA","Java IDE",     "idea",              "flatpak", "Development"),
    ("io.github.shiftey.Desktop","GitHub Desktop","GitHub GUI client",        "github-desktop",    "flatpak", "Development"),
    ("dev.zed.Zed",     "Zed",            "Fast, AI code editor",           "zed",               "flatpak", "Development"),
    ("com.usebruno.Bruno","Bruno",         "API testing tool",               "bruno",             "flatpak", "Development"),
    ("io.podman.PodmanDesktop","Podman Desktop","Container management",       "podman-desktop",    "flatpak", "Development"),
    # Gaming
    ("com.valvesoftware.Steam","Steam",    "Valve game platform",            "steam",             "flatpak", "Gaming"),
    ("net.lutris.Lutris","Lutris",         "Open gaming platform",           "lutris",            "flatpak", "Gaming"),
    ("com.heroicgameslauncher.hgl","Heroic","Epic & GOG launcher",           "heroic",            "flatpak", "Gaming"),
    ("com.usebottles.bottles","Bottles",   "Run Windows games",              "bottles",           "flatpak", "Gaming"),
    ("io.github.Foldex.AdwSteamGtk","AdwSteam GTK","Steam skin manager",    "adwsteam",          "flatpak", "Gaming"),
    # System tools
    ("org.gnome.baobab","Baobab",          "Disk usage analyzer",            "baobab",            "flatpak", "System"),
    ("org.kde.filelight","Filelight",      "Disk usage visualizer",          "filelight",         "dnf",     "System"),
    ("com.mattjakeman.ExtensionManager","Extension Manager","GNOME extensions","extension-manager", "flatpak","System"),
    ("io.github.vikdevelop.SaveDesktop","SaveDesktop","Backup desktop config","savedesktop",       "flatpak", "System"),
]


def _is_flatpak_installed(app_id: str) -> bool:
    try:
        r = subprocess.run(["flatpak","info",app_id], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def _is_dnf_installed(pkg: str) -> bool:
    return shutil.which(pkg.split("-")[0]) is not None or \
           subprocess.run(["rpm","-q",pkg], capture_output=True).returncode == 0


class AppCard(Gtk.ListBoxRow):
    def __init__(self, app_data: tuple):
        super().__init__()
        self.app_data = app_data
        (pkg, label, desc, icon, source, category) = app_data

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8); box.set_margin_bottom(8)
        box.set_margin_start(12); box.set_margin_end(12)

        # Icon
        img = Gtk.Image.new_from_icon_name(icon)
        img.set_pixel_size(48)
        img.set_valign(Gtk.Align.CENTER)
        box.append(img)

        # Info
        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_hexpand(True)
        info.set_valign(Gtk.Align.CENTER)

        name_lbl = Gtk.Label(label=label)
        name_lbl.set_xalign(0)
        name_lbl.set_markup(f"<b>{GLib.markup_escape_text(label)}</b>")
        info.append(name_lbl)

        desc_lbl = Gtk.Label(label=desc)
        desc_lbl.set_xalign(0)
        desc_lbl.add_css_class("dim-label")
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        info.append(desc_lbl)

        # Source badge
        src_box = Gtk.Box(spacing=4)
        src_badge = Gtk.Label(label=source.upper())
        src_badge.add_css_class("badge")
        src_badge.add_css_class(f"badge-{source}")
        src_box.append(src_badge)
        info.append(src_box)

        box.append(info)

        # Install button
        self._btn = Gtk.Button()
        self._btn.set_valign(Gtk.Align.CENTER)
        self._btn.set_size_request(90, -1)
        self._btn.connect("clicked", self._on_btn_clicked)
        box.append(self._btn)

        self.set_child(box)
        self._label = label
        self._pkg   = pkg
        self._source = source

        # Check initial state async
        self._installed = False
        threading.Thread(target=self._check_installed, daemon=True).start()

    def _check_installed(self):
        if self._source == "flatpak":
            inst = _is_flatpak_installed(self._pkg)
        else:
            inst = _is_dnf_installed(self._pkg)
        self._installed = inst
        GLib.idle_add(self._update_btn)

    def _update_btn(self):
        if self._installed:
            self._btn.set_label("Remove")
            self._btn.add_css_class("destructive-action")
            self._btn.remove_css_class("suggested-action")
        else:
            self._btn.set_label("Install")
            self._btn.add_css_class("suggested-action")
            self._btn.remove_css_class("destructive-action")
        return False

    def _on_btn_clicked(self, _btn):
        if self._installed:
            self._run_action("remove")
        else:
            self._run_action("install")

    def _run_action(self, action: str):
        self._btn.set_sensitive(False)
        self._btn.set_label("…")
        threading.Thread(
            target=self._do_action, args=(action,), daemon=True
        ).start()

    def _do_action(self, action: str):
        if self._source == "flatpak":
            cmd = ["flatpak", action, "--noninteractive", "-y", self._pkg]
        else:
            cmd = ["pkexec", "dnf", action, "-y", "--", self._pkg]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            ok = r.returncode == 0
        except Exception:
            ok = False

        if ok:
            self._installed = (action == "install")
        GLib.idle_add(self._update_btn)
        GLib.idle_add(lambda: self._btn.set_sensitive(True))


class AppManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS App Manager")
        self.set_default_size(880, 700)
        self._current_category = None
        self._search_term = ""
        self._setup_css()
        self._build_ui()
        self._populate()

    def _setup_css(self):
        css = """
        .badge { font-size: 9px; font-weight: bold; border-radius: 4px; padding: 1px 5px; }
        .badge-flatpak { background: #0064C8; color: white; }
        .badge-dnf     { background: #5A2080; color: white; }
        .category-btn  { border-radius: 8px; }
        """
        p = Gtk.CssProvider(); p.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), p, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        # Header
        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="App Manager"))
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search apps…")
        self._search_entry.set_size_request(280, -1)
        self._search_entry.connect("search-changed", self._on_search)
        hb.set_title_widget(self._search_entry)
        outer.append(hb)

        # Content: sidebar + list
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content.set_vexpand(True)
        outer.append(content)

        # Sidebar: categories
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_size_request(160, -1)
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content.append(sidebar_scroll)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        sidebar.set_margin_top(8); sidebar.set_margin_bottom(8)
        sidebar.set_margin_start(8); sidebar.set_margin_end(8)
        sidebar_scroll.set_child(sidebar)

        self._cat_buttons = []
        for cat_label, cat_filter, cat_icon in CATEGORIES:
            btn = Gtk.Button()
            btn_inner = Gtk.Box(spacing=8)
            btn_inner.append(Gtk.Image.new_from_icon_name(cat_icon))
            btn_inner.append(Gtk.Label(label=cat_label))
            btn.set_child(btn_inner)
            btn.add_css_class("flat")
            btn.add_css_class("category-btn")
            btn.set_halign(Gtk.Align.FILL)
            btn.connect("clicked", self._on_category, cat_filter)
            sidebar.append(btn)
            self._cat_buttons.append(btn)

        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        content.append(sep)

        # App list
        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_hexpand(True)
        content.append(list_scroll)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._listbox.add_css_class("boxed-list")
        list_scroll.set_child(self._listbox)

        # Status bar
        self._statusbar = Gtk.Label(label="")
        self._statusbar.add_css_class("dim-label")
        self._statusbar.set_margin_start(12)
        self._statusbar.set_margin_top(4)
        self._statusbar.set_margin_bottom(4)
        self._statusbar.set_xalign(0)
        outer.append(self._statusbar)

    def _populate(self):
        for app in APP_CATALOGUE:
            card = AppCard(app)
            self._listbox.append(card)
        self._apply_filters()

    def _on_category(self, _btn, cat_filter):
        self._current_category = cat_filter
        self._apply_filters()

    def _on_search(self, entry):
        self._search_term = entry.get_text().lower()
        self._apply_filters()

    def _apply_filters(self):
        visible = 0
        row = self._listbox.get_row_at_index(0)
        while row is not None:
            card = row
            if isinstance(card, AppCard):
                pkg, label, desc, icon, source, category = card.app_data
                cat_match = (self._current_category is None or
                             self._current_category in category)
                srch_match = (not self._search_term or
                              self._search_term in label.lower() or
                              self._search_term in desc.lower())
                show = cat_match and srch_match
                card.set_visible(show)
                if show:
                    visible += 1
            row = self._listbox.get_row_at_index(card.get_index() + 1)
        self._statusbar.set_label(f"{visible} apps shown")


class AppManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: AppManagerWindow(a).present())


if __name__ == "__main__":
    app = AppManagerApp()
    sys.exit(app.run(sys.argv))
