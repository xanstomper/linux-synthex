#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Log Viewer — real-time journald browser with filters & search

import sys, subprocess, re, threading, time
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Pango

APP_ID = "org.synthos.LogViewer"

UNITS = [
    ("All",                   None),
    ("Boot",                  "synthex-firstboot.service"),
    ("Installer",             "calamares.service"),
    ("Control Center",        "synthex-control-center"),
    ("Update Manager",        "synthex-update-manager"),
    ("Gaming Mode",           "synthex-gaming-mode.service"),
    ("Network",               "NetworkManager.service"),
    ("Display Manager",       "sddm.service"),
    ("Security",              "synthex-security-scan.service"),
    ("GPU Setup",             "synthex-gpu-setup.service"),
    ("Kernel",                "kernel"),
    ("Hardware Detect",       "synthex-hardware-detect.service"),
]

PRIORITIES = [
    ("All Levels", None),
    ("Emergency+", "0"),
    ("Critical+",  "2"),
    ("Error+",     "3"),
    ("Warning+",   "4"),
    ("Info+",      "6"),
    ("Debug",      "7"),
]

LEVEL_COLORS = {
    "0": "#FF2222", "1": "#FF4444", "2": "#FF6600",
    "3": "#FF8800", "4": "#FFD700", "5": "#AADDFF",
    "6": "#CCCCCC", "7": "#888888",
}
LEVEL_LABELS = {
    "0":"EMERG","1":"ALERT","2":"CRIT","3":"ERR",
    "4":"WARN", "5":"NOTICE","6":"INFO","7":"DEBUG",
}


def run_journal(unit=None, priority=None, since=None, count=1000, search=None):
    cmd = ["journalctl", "--no-pager", "-o", "short-iso", f"-n{count}"]
    if unit:
        if unit == "kernel":
            cmd += ["-k"]
        else:
            cmd += ["-u", unit]
    if priority:
        cmd += [f"-p", priority]
    if since:
        cmd += ["--since", since]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = r.stdout.splitlines()
        if search:
            pat = re.compile(re.escape(search), re.IGNORECASE)
            lines = [l for l in lines if pat.search(l)]
        return lines
    except Exception as e:
        return [f"[Error reading journal: {e}]"]


class LogLine:
    """Parses a journalctl short-iso line into components."""
    PAT = re.compile(
        r'^(\d{4}-\d{2}-\d{2}T[\d:+.]+)\s+'   # timestamp
        r'(\S+)\s+'                              # hostname
        r'(\S+?)(?:\[(\d+)\])?:\s+'             # unit[pid]:
        r'(.*)$'                                 # message
    )

    def __init__(self, raw: str):
        self.raw = raw
        m = self.PAT.match(raw)
        if m:
            self.ts, self.host, self.unit, self.pid, self.msg = m.groups()
            self.pid = self.pid or ""
        else:
            self.ts = self.host = self.unit = self.pid = ""
            self.msg = raw
        # Guess priority from keywords
        msg_lower = self.msg.lower()
        if any(w in msg_lower for w in ("emerg","panic")):
            self.level = "0"
        elif "alert" in msg_lower:
            self.level = "1"
        elif any(w in msg_lower for w in ("crit","critical")):
            self.level = "2"
        elif any(w in msg_lower for w in ("err","error","failed","failure")):
            self.level = "3"
        elif any(w in msg_lower for w in ("warn","warning")):
            self.level = "4"
        elif "notice" in msg_lower:
            self.level = "5"
        elif any(w in msg_lower for w in ("debug","trace")):
            self.level = "7"
        else:
            self.level = "6"


class LogRow(Gtk.Box):
    def __init__(self, line: LogLine, search_term=""):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.add_css_class("log-row")

        # Level badge
        badge = Gtk.Label(label=LEVEL_LABELS.get(line.level, "INFO"))
        badge.set_size_request(58, -1)
        badge.add_css_class("log-level")
        badge.add_css_class(f"log-level-{line.level}")
        self.append(badge)

        # Timestamp
        ts_lbl = Gtk.Label(label=line.ts[11:19] if len(line.ts) > 10 else line.ts)
        ts_lbl.add_css_class("log-ts")
        ts_lbl.set_width_chars(8)
        self.append(ts_lbl)

        # Unit
        unit_lbl = Gtk.Label(label=line.unit[:28] if line.unit else "")
        unit_lbl.add_css_class("log-unit")
        unit_lbl.set_width_chars(28)
        unit_lbl.set_xalign(0)
        unit_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self.append(unit_lbl)

        # Message — highlight search term
        if search_term:
            msg_lbl = Gtk.Label()
            escaped = GLib.markup_escape_text(line.msg)
            esc_search = GLib.markup_escape_text(search_term)
            highlighted = re.sub(
                f"({re.escape(esc_search)})",
                r'<span background="#FFD700" foreground="#000000">\1</span>',
                escaped,
                flags=re.IGNORECASE
            )
            msg_lbl.set_markup(highlighted)
        else:
            msg_lbl = Gtk.Label(label=line.msg)
        msg_lbl.set_xalign(0)
        msg_lbl.set_hexpand(True)
        msg_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        msg_lbl.set_selectable(True)
        msg_lbl.add_css_class("log-msg")
        self.append(msg_lbl)


class LogViewerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Log Viewer")
        self.set_default_size(1280, 760)

        self._lines: list[LogLine] = []
        self._unit    = None
        self._prio    = None
        self._since   = "1 hour ago"
        self._search  = ""
        self._follow  = False
        self._follow_tid = None

        self._setup_css()
        self._build_ui()
        self._load()

    def _setup_css(self):
        css = """
        .log-row { padding: 2px 6px; font-family: "JetBrains Mono", "Noto Sans Mono", monospace; font-size: 12px; }
        .log-row:hover { background-color: alpha(white, 0.05); }
        .log-ts   { color: #8899AA; font-size: 11px; }
        .log-unit { color: #88BBDD; font-size: 11px; }
        .log-msg  { color: #CCCCCC; }
        .log-level { font-size: 10px; font-weight: bold; border-radius: 3px; padding: 1px 3px; }
        .log-level-0, .log-level-1, .log-level-2 { background: #AA0000; color: white; }
        .log-level-3 { background: #CC5500; color: white; }
        .log-level-4 { background: #996600; color: white; }
        .log-level-5 { background: #336699; color: white; }
        .log-level-6 { background: #333333; color: #AAAAAA; }
        .log-level-7 { background: #222222; color: #666666; }
        .sidebar-btn { border-radius: 6px; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        # Outer layout
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        # Header bar
        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="SynthOS Log Viewer"))
        outer.append(hb)

        # Toolbar row
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(8); toolbar.set_margin_end(8)
        toolbar.set_margin_top(4); toolbar.set_margin_bottom(4)
        outer.append(toolbar)

        # Unit dropdown
        unit_lbl = Gtk.Label(label="Service:")
        toolbar.append(unit_lbl)
        self._unit_combo = Gtk.DropDown.new_from_strings([u[0] for u in UNITS])
        self._unit_combo.set_selected(0)
        self._unit_combo.connect("notify::selected", self._on_filter_change)
        toolbar.append(self._unit_combo)

        # Priority dropdown
        prio_lbl = Gtk.Label(label="  Level:")
        toolbar.append(prio_lbl)
        self._prio_combo = Gtk.DropDown.new_from_strings([p[0] for p in PRIORITIES])
        self._prio_combo.set_selected(0)
        self._prio_combo.connect("notify::selected", self._on_filter_change)
        toolbar.append(self._prio_combo)

        # Time range
        time_lbl = Gtk.Label(label="  Since:")
        toolbar.append(time_lbl)
        self._time_combo = Gtk.DropDown.new_from_strings([
            "30 minutes","1 hour","6 hours","24 hours","3 days","7 days","All"
        ])
        self._time_combo.set_selected(1)
        self._time_combo.connect("notify::selected", self._on_filter_change)
        toolbar.append(self._time_combo)

        # Spacer
        spacer = Gtk.Box(); spacer.set_hexpand(True)
        toolbar.append(spacer)

        # Search entry
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("Search logs…")
        self._search_entry.set_size_request(240, -1)
        self._search_entry.connect("search-changed", self._on_search_change)
        toolbar.append(self._search_entry)

        # Follow toggle
        self._follow_btn = Gtk.ToggleButton(label="⏩ Follow")
        self._follow_btn.connect("toggled", self._on_follow_toggle)
        toolbar.append(self._follow_btn)

        # Clear / Refresh
        ref_btn = Gtk.Button(label="↺ Refresh")
        ref_btn.connect("clicked", lambda _: self._load())
        toolbar.append(ref_btn)

        # Export button
        exp_btn = Gtk.Button(label="⬇ Export")
        exp_btn.connect("clicked", self._on_export)
        toolbar.append(exp_btn)

        # Stats bar
        self._stats_bar = Gtk.Label(label="Loading…")
        self._stats_bar.set_margin_start(8); self._stats_bar.set_margin_bottom(2)
        self._stats_bar.set_xalign(0)
        self._stats_bar.add_css_class("dim-label")
        outer.append(self._stats_bar)

        # Main scroll area
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        outer.append(scroll)

        # ListBox for log lines
        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.set_activate_on_single_click(False)
        self._listbox.connect("row-activated", self._on_row_activated)
        scroll.set_child(self._listbox)
        self._scroll_adj = scroll.get_vadjustment()

        # Status bar
        self._statusbar = Gtk.Label(label="")
        self._statusbar.set_margin_start(8); self._statusbar.set_margin_top(2)
        self._statusbar.set_xalign(0)
        self._statusbar.add_css_class("dim-label")
        outer.append(self._statusbar)

    def _on_filter_change(self, *_):
        self._unit  = UNITS[self._unit_combo.get_selected()][1]
        self._prio  = PRIORITIES[self._prio_combo.get_selected()][1]
        times = ["30 minutes ago","1 hour ago","6 hours ago",
                 "24 hours ago","3 days ago","7 days ago",None]
        self._since = times[self._time_combo.get_selected()]
        self._load()

    def _on_search_change(self, entry):
        self._search = entry.get_text()
        self._render()

    def _on_follow_toggle(self, btn):
        self._follow = btn.get_active()
        if self._follow:
            self._follow_start()
        else:
            self._follow_stop()

    def _follow_start(self):
        self._follow_tid = threading.Thread(target=self._follow_worker, daemon=True)
        self._follow_tid.start()

    def _follow_stop(self):
        self._follow = False

    def _follow_worker(self):
        cmd = ["journalctl", "--no-pager", "-f", "-n0", "-o", "short-iso"]
        if self._unit and self._unit != "kernel":
            cmd += ["-u", self._unit]
        elif self._unit == "kernel":
            cmd += ["-k"]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
            while self._follow and proc.poll() is None:
                line = proc.stdout.readline()
                if line.strip():
                    parsed = LogLine(line.rstrip())
                    GLib.idle_add(self._append_line, parsed)
            proc.terminate()
        except Exception:
            pass

    def _append_line(self, line: LogLine):
        self._lines.append(line)
        row = Gtk.ListBoxRow()
        row.set_child(LogRow(line, self._search))
        self._listbox.append(row)
        # Auto-scroll to bottom
        GLib.idle_add(lambda: self._scroll_adj.set_value(self._scroll_adj.get_upper()))
        return False

    def _load(self):
        self._stats_bar.set_label("Loading…")
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        lines_raw = run_journal(
            unit=self._unit,
            priority=self._prio,
            since=self._since,
            search=self._search,
            count=2000
        )
        self._lines = [LogLine(l) for l in lines_raw]
        GLib.idle_add(self._render)

    def _render(self):
        # Clear
        while True:
            row = self._listbox.get_row_at_index(0)
            if row is None:
                break
            self._listbox.remove(row)

        search = self._search
        pat = re.compile(re.escape(search), re.IGNORECASE) if search else None

        counts = {"err": 0, "warn": 0, "total": 0}
        for ll in self._lines:
            if pat and not pat.search(ll.raw):
                continue
            row = Gtk.ListBoxRow()
            row.set_child(LogRow(ll, search))
            self._listbox.append(row)
            counts["total"] += 1
            if ll.level in ("0","1","2","3"):
                counts["err"] += 1
            elif ll.level == "4":
                counts["warn"] += 1

        self._stats_bar.set_markup(
            f'<span>Showing <b>{counts["total"]}</b> entries  •  '
            f'<span foreground="#FF8800">⚠ {counts["warn"]} warnings</span>  •  '
            f'<span foreground="#FF4444">✗ {counts["err"]} errors</span></span>'
        )
        return False

    def _on_row_activated(self, lb, row):
        idx = row.get_index()
        if 0 <= idx < len(self._lines):
            ll = self._lines[idx]
            dlg = Adw.MessageDialog(heading="Log Entry Detail", body=ll.raw)
            dlg.add_response("close", "Close")
            dlg.set_default_response("close")
            dlg.set_transient_for(self)
            dlg.present()

    def _on_export(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("Export Logs")
        dialog.set_initial_name("synthos-logs.txt")
        dialog.save(self, None, self._on_export_done)

    def _on_export_done(self, dialog, result):
        try:
            f = dialog.save_finish(result)
            path = f.get_path()
            with open(path, "w") as fh:
                for ll in self._lines:
                    fh.write(ll.raw + "\n")
            self._statusbar.set_label(f"Exported {len(self._lines)} lines to {path}")
        except Exception as e:
            self._statusbar.set_label(f"Export failed: {e}")


class LogViewerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", self._on_activate)

    def _on_activate(self, _):
        win = LogViewerWindow(self)
        win.present()


if __name__ == "__main__":
    app = LogViewerApp()
    sys.exit(app.run(sys.argv))
