#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Service Manager — systemd service browser and controller

import sys, subprocess, threading, json
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib, Pango

APP_ID = "org.synthos.ServiceManager"

def systemctl(*args, timeout=10):
    try:
        r = subprocess.run(["systemctl"] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode
    except Exception as e:
        return str(e), 1

def list_units(service_type="service", state=None):
    cmd = ["systemctl","list-units",f"--type={service_type}","--no-pager","--no-legend","-o","json"]
    if state:
        cmd += [f"--state={state}"]
    try:
        out, _ = systemctl(*cmd[1:], timeout=15)
        return json.loads(out)
    except Exception:
        out, _ = systemctl("list-units",f"--type={service_type}","--no-pager","--no-legend", timeout=15)
        units = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                units.append({"unit":parts[0],"load":parts[1],"active":parts[2],"sub":parts[3],
                               "description":" ".join(parts[4:])})
        return units


class ServiceManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Service Manager")
        self.set_default_size(960, 660)
        self._units = []
        self._filter = ""
        self._show_user = False
        self._build()
        self._load()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="Service Manager"))

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text("Filter services…")
        search_entry.set_size_request(280,-1)
        search_entry.connect("search-changed", self._on_filter)
        hb.set_title_widget(search_entry)

        user_btn = Gtk.ToggleButton(label="User Services")
        user_btn.connect("toggled", self._on_user_toggle)
        hb.pack_end(user_btn)

        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.connect("clicked", lambda _: self._load())
        hb.pack_end(refresh_btn)
        outer.append(hb)

        # Stats bar
        self._stats = Gtk.Label(label="Loading…")
        self._stats.set_xalign(0)
        self._stats.set_margin_start(12)
        self._stats.set_margin_top(4)
        self._stats.set_margin_bottom(4)
        self._stats.add_css_class("dim-label")
        outer.append(self._stats)

        # Unit list
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        outer.append(scroll)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.add_css_class("boxed-list")
        self._listbox.connect("row-activated", self._on_row_activated)
        scroll.set_child(self._listbox)

        # Action bar
        action_bar = Gtk.ActionBar()
        self._start_btn = Gtk.Button(label="Start")
        self._start_btn.connect("clicked", lambda _: self._service_action("start"))
        self._stop_btn  = Gtk.Button(label="Stop")
        self._stop_btn.connect("clicked", lambda _: self._service_action("stop"))
        self._restart_btn = Gtk.Button(label="Restart")
        self._restart_btn.connect("clicked", lambda _: self._service_action("restart"))
        self._enable_btn  = Gtk.Button(label="Enable at Boot")
        self._enable_btn.connect("clicked", lambda _: self._service_action("enable"))
        self._disable_btn = Gtk.Button(label="Disable at Boot")
        self._disable_btn.add_css_class("destructive-action")
        self._disable_btn.connect("clicked", lambda _: self._service_action("disable"))
        self._logs_btn    = Gtk.Button(label="View Logs")
        self._logs_btn.connect("clicked", self._view_logs)

        for btn in [self._start_btn, self._stop_btn, self._restart_btn]:
            action_bar.pack_start(btn)
        for btn in [self._enable_btn, self._disable_btn, self._logs_btn]:
            action_bar.pack_end(btn)
        outer.append(action_bar)

        self._selected_unit = None

    def _load(self):
        self._stats.set_label("Loading services…")
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        extra = ["--user"] if self._show_user else []
        cmd = ["list-units","--type=service","--no-pager","--no-legend"] + extra
        out, _ = systemctl(*cmd, timeout=15)
        units = []
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                units.append({
                    "unit": parts[0],
                    "load": parts[1],
                    "active": parts[2],
                    "sub": parts[3],
                    "description": " ".join(parts[4:])
                })
        self._units = units
        GLib.idle_add(self._render)

    def _render(self):
        while True:
            row = self._listbox.get_row_at_index(0)
            if row is None: break
            self._listbox.remove(row)

        filt = self._filter.lower()
        shown = active = inactive = 0
        for unit in self._units:
            if filt and filt not in unit["unit"].lower() and filt not in unit["description"].lower():
                continue

            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(6); box.set_margin_bottom(6)
            box.set_margin_start(10); box.set_margin_end(10)

            # Status dot
            status = unit.get("active","unknown")
            dot = Gtk.Label(label="●")
            if status == "active":
                dot.set_markup('<span foreground="#44CC88">●</span>')
                active += 1
            elif status == "failed":
                dot.set_markup('<span foreground="#FF4444">●</span>')
            else:
                dot.set_markup('<span foreground="#666666">●</span>')
                inactive += 1
            box.append(dot)

            # Info
            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            info.set_hexpand(True)

            name_lbl = Gtk.Label(label=unit["unit"])
            name_lbl.set_xalign(0)
            name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            name_lbl.set_markup(f"<b>{GLib.markup_escape_text(unit['unit'])}</b>")
            info.append(name_lbl)

            desc_lbl = Gtk.Label(label=unit.get("description",""))
            desc_lbl.set_xalign(0)
            desc_lbl.add_css_class("dim-label")
            desc_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            info.append(desc_lbl)
            box.append(info)

            # Sub-state badge
            sub = Gtk.Label(label=unit.get("sub",""))
            sub.add_css_class("dim-label")
            box.append(sub)

            row.set_child(box)
            row._unit_name = unit["unit"]
            self._listbox.append(row)
            shown += 1

        self._stats.set_markup(
            f'<span>{shown} services  •  '
            f'<span foreground="#44CC88">{active} active</span>  •  '
            f'<span foreground="#888888">{inactive} inactive</span></span>'
        )
        return False

    def _on_filter(self, entry):
        self._filter = entry.get_text()
        self._render()

    def _on_user_toggle(self, btn):
        self._show_user = btn.get_active()
        self._load()

    def _on_row_activated(self, lb, row):
        self._selected_unit = getattr(row, "_unit_name", None)

    def _service_action(self, action):
        if not self._selected_unit:
            return
        extra = ["--user"] if self._show_user else []
        if action in ("enable", "disable", "start", "stop", "restart") and not self._show_user:
            cmd = ["pkexec","systemctl", action] + extra + [self._selected_unit]
        else:
            cmd = ["systemctl", action] + extra + [self._selected_unit]
        threading.Thread(
            target=lambda: subprocess.run(cmd, timeout=30),
            daemon=True
        ).start()
        GLib.timeout_add(1500, self._load)

    def _view_logs(self, _btn):
        if self._selected_unit:
            subprocess.Popen([
                "konsole","--","journalctl","-u",self._selected_unit,"-f","--no-pager"
            ])


class ServiceManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: ServiceManagerWindow(a).present())

if __name__ == "__main__":
    ServiceManagerApp().run(sys.argv)
