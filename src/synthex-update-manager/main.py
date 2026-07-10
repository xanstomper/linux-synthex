#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Update Manager — GTK4/libadwaita
import sys, os, subprocess, threading, json, datetime
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1"); gi.require_version("GLib","2.0")
from gi.repository import Gtk, Adw, GLib, Gio

APP_ID = "org.synthos.UpdateManager"

def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout+r.stderr).strip()
    except Exception as e:
        return 1, str(e)

def run_stream(cmd, on_line, timeout=600):
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, bufsize=1)
        for line in proc.stdout:
            GLib.idle_add(on_line, line.rstrip())
        proc.wait(timeout=timeout)
        return proc.returncode
    except Exception as e:
        GLib.idle_add(on_line, f"Error: {e}")
        return 1

def check_dnf_updates():
    rc, out = run(["dnf","check-update","--quiet","--refresh"], timeout=60)
    if rc not in (0,100): return []
    pkgs = []
    for line in out.split("\n"):
        parts = line.split()
        if len(parts) >= 3 and not line.startswith(("Obsoleting","Security","Last")):
            pkgs.append({"name":parts[0],"version":parts[1],"repo":parts[2],"type":"dnf","security":False})
    return pkgs

def check_flatpak_updates():
    rc, out = run(["flatpak","remote-ls","--updates","--columns=application,version"], timeout=30)
    if rc != 0: return []
    pkgs = []
    for line in out.split("\n"):
        parts = line.split()
        if parts:
            pkgs.append({"name":parts[0],"version":parts[1] if len(parts)>1 else "?",
                         "repo":"flathub","type":"flatpak","security":False})
    return pkgs

class UpdateManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Update Manager",
                         default_width=950, default_height=700)
        self._all_updates = []; self._selected = set()
        self._build_ui(); self._check_updates()

    def _build_ui(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="Update Manager"))
        self._check_btn = Gtk.Button(label="Check", icon_name="view-refresh-symbolic")
        self._check_btn.connect("clicked", lambda b: self._check_updates())
        self._update_all_btn = Gtk.Button(label="Update All", css_classes=["suggested-action"])
        self._update_all_btn.connect("clicked", self._on_update_all)
        self._update_all_btn.set_sensitive(False)
        hb.pack_end(self._check_btn); hb.pack_end(self._update_all_btn)
        root.append(hb)

        self._banner = Adw.Banner()
        self._banner.set_title("Checking for updates…"); self._banner.set_revealed(True)
        root.append(self._banner)

        # Tab
        self._tab = Adw.TabView(); bar = Adw.TabBar(); bar.set_view(self._tab)
        root.append(bar); root.append(self._tab)

        # Updates page
        upd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        self._updates_list = Gtk.ListBox()
        self._updates_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self._updates_list.add_css_class("boxed-list")
        self._updates_list.set_margin_start(16); self._updates_list.set_margin_end(16)
        self._updates_list.set_margin_top(8); self._updates_list.set_margin_bottom(16)
        scroll.set_child(self._updates_list)
        upd_box.append(scroll)
        # Bottom bar
        bot = Gtk.Box(spacing=8, margin_start=16, margin_end=16, margin_top=4, margin_bottom=12)
        self._update_sel_btn = Gtk.Button(label="Update Selected (0)", css_classes=["suggested-action"])
        self._update_sel_btn.set_sensitive(False)
        self._update_sel_btn.connect("clicked", self._on_update_selected)
        sp = Gtk.Box(); sp.set_hexpand(True)
        bot.append(sp); bot.append(self._update_sel_btn)
        upd_box.append(bot)
        self._tab.append(upd_box).set_title("Available Updates")

        # Log page
        log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        log_scroll = Gtk.ScrolledWindow(); log_scroll.set_vexpand(True)
        self._log_tv = Gtk.TextView(editable=False, monospace=True, left_margin=12, top_margin=8)
        log_scroll.set_child(self._log_tv)
        log_box.append(log_scroll)
        self._progress = Gtk.ProgressBar(show_text=True, text="Idle",
                                          margin_start=16, margin_end=16,
                                          margin_top=4, margin_bottom=8)
        log_box.append(self._progress)
        self._tab.append(log_box).set_title("Install Log")

        # Settings page
        prefs = Adw.PreferencesPage()
        grp = Adw.PreferencesGroup(title="Automatic Updates")
        for title, unit in [("Security auto-updates","dnf-automatic-install.timer"),
                             ("Firmware updates (LVFS)","fwupd.service")]:
            row = Adw.ActionRow(title=title)
            rc,_ = run(["systemctl","is-enabled",unit])
            sw = Gtk.Switch(valign=Gtk.Align.CENTER, active=(rc==0))
            sw.connect("state-set", lambda s,state,u=unit: (
                run(["pkexec","systemctl","enable" if state else "disable","--now",u]), False)[-1])
            row.add_suffix(sw)
            grp.add(row)
        prefs.add(grp)

        snap_grp = Adw.PreferencesGroup(title="Safety")
        snap_row = Adw.ActionRow(title="Snapshot before upgrade",
                                   subtitle="Create Timeshift snapshot before applying updates")
        self._snap_sw = Gtk.Switch(valign=Gtk.Align.CENTER, active=True)
        snap_row.add_suffix(self._snap_sw)
        snap_grp.add(snap_row)
        prefs.add(snap_grp)
        self._tab.append(prefs).set_title("Settings")

    def _check_updates(self):
        self._check_btn.set_sensitive(False)
        self._banner.set_title("Checking for updates…"); self._banner.set_revealed(True)
        def worker():
            pkgs = check_dnf_updates() + check_flatpak_updates()
            GLib.idle_add(self._on_fetched, pkgs)
        threading.Thread(target=worker, daemon=True).start()

    def _on_fetched(self, pkgs):
        self._all_updates = pkgs
        self._check_btn.set_sensitive(True)
        if pkgs:
            self._banner.set_title(f"{len(pkgs)} update{'s' if len(pkgs)!=1 else ''} available")
            self._update_all_btn.set_sensitive(True)
        else:
            self._banner.set_title("✓  System is up to date")
            self._update_all_btn.set_sensitive(False)
        self._repopulate()
        return False

    def _repopulate(self):
        while self._updates_list.get_row_at_index(0):
            self._updates_list.remove(self._updates_list.get_row_at_index(0))
        for pkg in self._all_updates:
            row = Adw.ActionRow(title=pkg["name"], subtitle=f"{pkg['version']}  [{pkg['repo']}]")
            badge = Gtk.Label(label=pkg["type"].upper())
            badge.add_css_class("dim-label"); badge.add_css_class("caption")
            badge.set_valign(Gtk.Align.CENTER)
            row.add_suffix(badge)
            chk = Gtk.CheckButton(); chk.set_valign(Gtk.Align.CENTER)
            chk._pkg = pkg
            chk.connect("toggled", self._on_pkg_toggled)
            row.add_prefix(chk)
            self._updates_list.append(row)

    def _on_pkg_toggled(self, chk):
        name = chk._pkg["name"]
        if chk.get_active(): self._selected.add(name)
        else: self._selected.discard(name)
        n = len(self._selected)
        self._update_sel_btn.set_label(f"Update Selected ({n})")
        self._update_sel_btn.set_sensitive(n > 0)

    def _on_update_all(self, _btn): self._run_update(None)
    def _on_update_selected(self, _btn): self._run_update(list(self._selected))

    def _run_update(self, pkg_names):
        self._update_all_btn.set_sensitive(False)
        self._update_sel_btn.set_sensitive(False)
        # Switch to log tab (index 1)
        self._tab.set_selected_page(self._tab.get_nth_page(1))

        def append_log(line):
            buf = self._log_tv.get_buffer()
            buf.insert(buf.get_end_iter(), line+"\n")
            return False

        def worker():
            if self._snap_sw.get_active():
                GLib.idle_add(append_log, "📸 Creating pre-update snapshot…")
                run(["pkexec","timeshift","--create","--comments",
                     f"Pre-update {datetime.datetime.now():%Y-%m-%d %H:%M}"], timeout=120)
            GLib.idle_add(append_log, "\n🔄 Installing DNF updates…")
            cmd = ["pkexec","dnf","upgrade","-y"]
            if pkg_names:
                dnf = [p["name"] for p in self._all_updates if p["name"] in pkg_names and p["type"]=="dnf"]
                if dnf: cmd = ["pkexec","dnf","upgrade","-y"]+dnf
            rc = run_stream(cmd, append_log)
            GLib.idle_add(append_log, f"\n{'✓' if rc==0 else '✗'} DNF complete")
            GLib.idle_add(append_log, "\n🔄 Updating Flatpaks…")
            run_stream(["flatpak","update","-y"], append_log)
            GLib.idle_add(self._on_update_done)
        threading.Thread(target=worker, daemon=True).start()

    def _on_update_done(self):
        self._progress.set_fraction(1.0); self._progress.set_text("Update complete!")
        self._check_updates()
        return False

class UpdateManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", lambda a: UpdateManagerWindow(self).present())

if __name__ == "__main__":
    sys.exit(UpdateManagerApp().run(sys.argv))
