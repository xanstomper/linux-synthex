#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Software Center — unified DNF + Flatpak store with featured apps

import sys, subprocess, threading, json, os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

APP_ID = "org.synthos.SoftwareCenter"

FEATURED = [
    {"name":"Firefox",         "icon":"firefox",           "desc":"Fast, private browser",            "id":"firefox",                          "src":"dnf"},
    {"name":"VS Code",         "icon":"code",              "desc":"Powerful code editor",             "id":"com.visualstudio.code",            "src":"flatpak"},
    {"name":"Steam",           "icon":"steam",             "desc":"The ultimate game store",          "id":"com.valvesoftware.Steam",          "src":"flatpak"},
    {"name":"OBS Studio",      "icon":"obs",               "desc":"Stream and record",                "id":"com.obsproject.Studio",            "src":"flatpak"},
    {"name":"GIMP",            "icon":"gimp",              "desc":"Powerful image editor",            "id":"org.gimp.GIMP",                    "src":"flatpak"},
    {"name":"LibreOffice",     "icon":"libreoffice-writer","desc":"Complete office suite",            "id":"org.libreoffice.LibreOffice",      "src":"flatpak"},
    {"name":"Discord",         "icon":"discord",           "desc":"Voice, video & text chat",         "id":"com.discordapp.Discord",           "src":"flatpak"},
    {"name":"Blender",         "icon":"blender",           "desc":"3D creation suite",                "id":"org.blender.Blender",              "src":"flatpak"},
]


def run_cmd(cmd, timeout=300):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        class R:
            returncode = 1
            stdout = ""
            stderr = str(e)
        return R()


class FeaturedCard(Gtk.Box):
    def __init__(self, app_info, on_install):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_size_request(180, 200)
        self.add_css_class("featured-card")
        self.set_halign(Gtk.Align.FILL)

        icon = Gtk.Image.new_from_icon_name(app_info["icon"])
        icon.set_pixel_size(64)
        icon.set_margin_top(12)
        self.append(icon)

        name_lbl = Gtk.Label(label=app_info["name"])
        name_lbl.set_markup(f"<b>{GLib.markup_escape_text(app_info['name'])}</b>")
        self.append(name_lbl)

        desc_lbl = Gtk.Label(label=app_info["desc"])
        desc_lbl.add_css_class("dim-label")
        desc_lbl.set_font_desc(Pango.FontDescription.from_string("10"))
        desc_lbl.set_justify(Gtk.Justification.CENTER)
        desc_lbl.set_wrap(True)
        self.append(desc_lbl)

        spacer = Gtk.Box(); spacer.set_vexpand(True)
        self.append(spacer)

        btn = Gtk.Button(label="Install")
        btn.add_css_class("suggested-action")
        btn.set_margin_start(12); btn.set_margin_end(12); btn.set_margin_bottom(12)
        btn.connect("clicked", lambda _: on_install(app_info))
        self.append(btn)


class SoftwareCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Software Center")
        self.set_default_size(960, 720)
        self._search_results = []
        self._installing = {}
        self._setup_css()
        self._build_ui()

    def _setup_css(self):
        css = """
        .featured-card {
            background: alpha(white, 0.04);
            border: 1px solid alpha(white, 0.10);
            border-radius: 14px;
            transition: background 100ms;
        }
        .featured-card:hover { background: alpha(white, 0.09); }
        .search-result-row { padding: 8px 12px; }
        .install-btn { min-width: 80px; }
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
        hb.set_title_widget(Gtk.Label(label="SynthOS Software Center"))
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_size_request(320, -1)
        self._search_entry.set_placeholder_text("Search packages and apps…")
        self._search_entry.connect("activate", self._on_search)
        hb.pack_start(self._search_entry)
        outer.append(hb)

        # Stack: home / search results
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_vexpand(True)
        outer.append(self._stack)

        self._stack.add_named(self._build_home(), "home")
        self._stack.add_named(self._build_results(), "results")

        # Progress bar (visible during installs)
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        self._progress.set_pulse_step(0.05)
        outer.append(self._progress)

        # Status bar
        self._status = Gtk.Label(label="")
        self._status.set_xalign(0)
        self._status.set_margin_start(12)
        self._status.set_margin_top(2)
        self._status.set_margin_bottom(4)
        self._status.add_css_class("dim-label")
        outer.append(self._status)

    def _build_home(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        box.set_margin_top(24); box.set_margin_bottom(24)
        box.set_margin_start(24); box.set_margin_end(24)
        scroll.set_child(box)

        # Featured header
        feat_hdr = Gtk.Label()
        feat_hdr.set_markup('<span size="large" weight="bold">Featured Apps</span>')
        feat_hdr.set_xalign(0)
        box.append(feat_hdr)

        # Featured grid
        feat_flow = Gtk.FlowBox()
        feat_flow.set_selection_mode(Gtk.SelectionMode.NONE)
        feat_flow.set_min_children_per_line(3)
        feat_flow.set_max_children_per_line(6)
        feat_flow.set_column_spacing(12)
        feat_flow.set_row_spacing(12)
        for app_info in FEATURED:
            card = FeaturedCard(app_info, self._on_quick_install)
            feat_flow.append(card)
        box.append(feat_flow)

        # Categories quick links
        cat_hdr = Gtk.Label()
        cat_hdr.set_markup('<span size="large" weight="bold">Browse by Category</span>')
        cat_hdr.set_xalign(0)
        box.append(cat_hdr)

        cats = [
            ("Internet",     "network-workgroup"),
            ("Development",  "applications-development"),
            ("Gaming",       "applications-games"),
            ("Media",        "applications-multimedia"),
            ("Office",       "x-office-presentation"),
            ("Utilities",    "applications-system"),
        ]
        cat_box = Gtk.Box(spacing=10)
        for cat_label, cat_icon in cats:
            btn = Gtk.Button()
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            inner.set_margin_top(8); inner.set_margin_bottom(8)
            inner.set_margin_start(12); inner.set_margin_end(12)
            icon = Gtk.Image.new_from_icon_name(cat_icon)
            icon.set_pixel_size(32)
            inner.append(icon)
            inner.append(Gtk.Label(label=cat_label))
            btn.set_child(inner)
            btn.add_css_class("flat")
            btn.connect("clicked", lambda _b, c=cat_label: self._search_category(c))
            cat_box.append(btn)
        box.append(cat_box)

        return scroll

    def _build_results(self):
        scroll = Gtk.ScrolledWindow()
        self._results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self._results_box.set_margin_top(12)
        self._results_box.set_margin_start(16)
        self._results_box.set_margin_end(16)
        scroll.set_child(self._results_box)
        return scroll

    def _on_search(self, entry):
        query = entry.get_text().strip()
        if not query:
            self._stack.set_visible_child_name("home")
            return
        self._do_search(query)

    def _search_category(self, cat):
        self._search_entry.set_text(cat)
        self._do_search(cat)

    def _do_search(self, query):
        self._status.set_label(f"Searching for '{query}'…")
        self._stack.set_visible_child_name("results")
        # Clear results
        while True:
            child = self._results_box.get_first_child()
            if child is None:
                break
            self._results_box.remove(child)
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query):
        results = []
        # Search Flatpak
        r = run_cmd(["flatpak", "search", "--columns=application,name,description", query], timeout=15)
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines()[:20]:
                parts = line.split("\t")
                if len(parts) >= 3:
                    results.append({"id": parts[0], "name": parts[1], "desc": parts[2], "src": "flatpak"})

        # Search DNF
        r2 = run_cmd(["dnf", "search", "--quiet", query], timeout=15)
        if r2.returncode == 0:
            for line in r2.stdout.strip().splitlines()[:20]:
                if ":" in line and not line.startswith("="):
                    pkg, desc = line.split(":", 1)
                    results.append({"id": pkg.strip().split(".")[0], "name": pkg.strip(),
                                    "desc": desc.strip(), "src": "dnf"})

        GLib.idle_add(self._show_results, results, query)

    def _show_results(self, results, query):
        self._status.set_label(f"Found {len(results)} results for '{query}'")
        for r in results:
            row = self._make_result_row(r)
            self._results_box.append(row)
        return False

    def _make_result_row(self, app_info):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8); box.set_margin_bottom(8)
        box.set_margin_start(8); box.set_margin_end(8)
        box.add_css_class("search-result-row")

        icon = Gtk.Image.new_from_icon_name("application-x-executable")
        icon.set_pixel_size(40)
        box.append(icon)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_hexpand(True)
        name_lbl = Gtk.Label()
        name_lbl.set_markup(f"<b>{GLib.markup_escape_text(app_info['name'])}</b>")
        name_lbl.set_xalign(0)
        info.append(name_lbl)
        desc_lbl = Gtk.Label(label=app_info["desc"][:100])
        desc_lbl.set_xalign(0)
        desc_lbl.add_css_class("dim-label")
        desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        info.append(desc_lbl)
        src_badge = Gtk.Label(label=app_info["src"].upper())
        src_badge.set_xalign(0)
        info.append(src_badge)
        box.append(info)

        btn = Gtk.Button(label="Install")
        btn.add_css_class("suggested-action")
        btn.add_css_class("install-btn")
        btn.set_valign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda _: self._on_install(app_info, btn))
        box.append(btn)

        frame = Gtk.Frame(); frame.set_child(box)
        return frame

    def _on_install(self, app_info, btn):
        btn.set_sensitive(False)
        btn.set_label("Installing…")
        self._progress.set_visible(True)
        self._progress_tid = GLib.timeout_add(100, lambda: self._progress.pulse() or True)
        threading.Thread(target=self._install_worker, args=(app_info, btn), daemon=True).start()

    def _on_quick_install(self, app_info):
        self._status.set_label(f"Installing {app_info['name']}…")
        self._progress.set_visible(True)
        self._progress_tid = GLib.timeout_add(100, lambda: self._progress.pulse() or True)
        threading.Thread(target=self._install_worker, args=(app_info, None), daemon=True).start()

    def _install_worker(self, app_info, btn):
        if app_info["src"] == "flatpak":
            cmd = ["flatpak", "install", "--noninteractive", "-y", app_info["id"]]
        else:
            cmd = ["pkexec", "dnf", "install", "-y", "--", app_info["id"]]
        r = run_cmd(cmd, timeout=300)
        ok = r.returncode == 0
        GLib.idle_add(self._install_done, app_info, btn, ok, r.stderr)

    def _install_done(self, app_info, btn, ok, stderr):
        GLib.source_remove(self._progress_tid)
        self._progress.set_visible(False)
        if ok:
            self._status.set_label(f"✓ {app_info['name']} installed successfully!")
            if btn:
                btn.set_label("Installed")
                btn.remove_css_class("suggested-action")
                btn.set_sensitive(False)
        else:
            self._status.set_label(f"✗ Failed to install {app_info['name']}: {stderr[:80]}")
            if btn:
                btn.set_label("Retry")
                btn.set_sensitive(True)
        return False


class SoftwareCenterApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: SoftwareCenterWindow(a).present())


if __name__ == "__main__":
    app = SoftwareCenterApp()
    sys.exit(app.run(sys.argv))
