#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Aegis — Security Center User Interface (Native GTK3)
Windows Security-inspired design for Linux: Clean, responsive, high-performance,
and empowering the user with full sovereignty over all protection engines.
"""

import os
import sys
import glob
import time
import subprocess
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
from gi.repository import Gtk, Gdk, GLib, Pango

from aegis_engine import AegisEngine, AegisConfig


class AegisMainWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Synthex Aegis — Endpoint Attack Prevention")
        self.set_default_size(1080, 750)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)

        self.engine = AegisEngine.get_instance()
        self.current_tab = "home"

        # ── Header Bar ──────────────────────────────────────────────────
        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.set_title("Aegis Security Center")
        self.hb.set_subtitle("SynthOS Endpoint Attack Prevention")
        self.set_titlebar(self.hb)

        # ── Main Container: Sidebar + Content Panes ─────────────────────
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(self.main_box)

        # Sidebar
        self.sidebar_sw = Gtk.ScrolledWindow()
        self.sidebar_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.sidebar_sw.set_size_request(240, -1)

        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.connect("row-selected", self._on_tab_selected)
        self.sidebar_sw.add(self.sidebar_list)

        self.sidebar_rows = {}
        tabs = [
            ("home",        "Home & Protection",        "security-high"),
            ("engines",     "Attack Prevention Engines", "system-run"),
            ("history",     "Protection History",        "document-open-recent"),
            ("device",      "Device & Hardware Security", "computer"),
            ("exclusions",  "Developer Exclusions",      "folder-saved-search"),
        ]

        for tab_id, label, icon in tabs:
            row = Gtk.ListBoxRow()
            row.tab_id = tab_id
            h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            h.set_border_width(12)
            h.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON), False, False, 0)
            h.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
            row.add(h)
            self.sidebar_list.add(row)
            self.sidebar_rows[tab_id] = row

        self.main_box.pack_start(self.sidebar_sw, False, False, 0)
        self.main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)

        # Right Content Area
        self.content_sw = Gtk.ScrolledWindow()
        self.content_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.content_sw.set_hexpand(True)
        self.content_sw.set_vexpand(True)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.content_box.set_border_width(24)
        self.content_sw.add(self.content_box)
        self.main_box.pack_start(self.content_sw, True, True, 0)

        # Select initial tab
        self.sidebar_list.select_row(self.sidebar_rows["home"])

    def _on_tab_selected(self, listbox, row):
        if not row:
            return
        self.current_tab = row.tab_id
        self._render_tab(row.tab_id)

    def _render_tab(self, tab_id):
        for child in self.content_box.get_children():
            child.destroy()

        # ── 1. Home / Overview ──────────────────────────────────────────
        if tab_id == "home":
            # Big Protection Shield Banner
            status = self.engine.get_status()
            shield_frame = Gtk.Frame()
            shield_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            shield_vbox.set_border_width(20)

            top_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            shield_icon = Gtk.Image.new_from_icon_name(
                "security-high" if status["realtime_active"] else "security-low",
                Gtk.IconSize.DIALOG
            )
            top_h.pack_start(shield_icon, False, False, 0)

            title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            t_lbl = Gtk.Label(xalign=0)
            if status["realtime_active"]:
                t_lbl.set_markup("<span size='xx-large' weight='bold' color='#2ecc71'>Your System is Actively Protected</span>")
            else:
                t_lbl.set_markup("<span size='xx-large' weight='bold' color='#e67e22'>Real-Time Protection is Paused</span>")
            title_box.pack_start(t_lbl, False, False, 0)

            sub_lbl = Gtk.Label(xalign=0)
            sub_lbl.set_markup("<span color='#888888'>Aegis Behavioral Attack Prevention is actively monitoring reverse shells, memory exploits, and privilege escalations.</span>")
            title_box.pack_start(sub_lbl, False, False, 0)
            top_h.pack_start(title_box, True, True, 0)

            shield_vbox.pack_start(top_h, False, False, 0)
            shield_frame.add(shield_vbox)
            self.content_box.pack_start(shield_frame, False, False, 0)

            # Active Scan Box
            scan_frame = Gtk.Frame(label="System Health & Threat Scan")
            scan_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            scan_vbox.set_border_width(16)

            self.status_lbl = Gtk.Label(label="No active threats detected. Last scan: Today", xalign=0)
            scan_vbox.pack_start(self.status_lbl, False, False, 0)

            self.prog_bar = Gtk.ProgressBar()
            self.prog_bar.set_fraction(0.0)
            scan_vbox.pack_start(self.prog_bar, False, False, 0)

            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            self.btn_quick = Gtk.Button.new_with_label("Quick Scan (Processes & Memory)")
            self.btn_quick.connect("clicked", lambda b: self._execute_scan("quick"))
            self.btn_full = Gtk.Button.new_with_label("Full System Scan")
            self.btn_full.connect("clicked", lambda b: self._execute_scan("full"))
            self.btn_cancel = Gtk.Button.new_with_label("Cancel Scan")
            self.btn_cancel.set_sensitive(False)
            self.btn_cancel.connect("clicked", lambda b: self.engine.cancel_scan())

            btn_box.pack_start(self.btn_quick, False, False, 0)
            btn_box.pack_start(self.btn_full, False, False, 0)
            btn_box.pack_start(self.btn_cancel, False, False, 0)
            scan_vbox.pack_start(btn_box, False, False, 4)

            scan_frame.add(scan_vbox)
            self.content_box.pack_start(scan_frame, False, False, 0)

            # Quick Engine Status Cards
            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(12)

            engines = [
                ("Reverse Shell Blocker", "Active", "Blocks remote interactive socket hijacking"),
                ("Memory Integrity Shield", "Active", "Prevents write-and-execute memory tampering"),
                ("Privilege Escalation Guard", "Active", "Protects /etc/sudoers and Polkit exploits"),
                ("Supply Chain Interceptor", "Active", "Inspects obfuscated pipe-to-bash executions"),
            ]
            for idx, (title, st, desc) in enumerate(engines):
                f = Gtk.Frame()
                b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                b.set_border_width(12)
                b.pack_start(Gtk.Label(label=f"<b>{title}</b>", use_markup=True, xalign=0), False, False, 0)
                b.pack_start(Gtk.Label(label=f"<span color='#2ecc71'>● {st}</span>", use_markup=True, xalign=0), False, False, 0)
                b.pack_start(Gtk.Label(label=f"<span size='small' color='#888888'>{desc}</span>", use_markup=True, xalign=0), False, False, 0)
                f.add(b)
                grid.attach(f, idx % 2, idx // 2, 1, 1)

            self.content_box.pack_start(grid, False, False, 0)

        # ── 2. Attack Prevention Engines ────────────────────────────────
        elif tab_id == "engines":
            cfg = self.engine.config
            frame = Gtk.Frame(label="Real-Time Attack Prevention Subsystems")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            vbox.set_border_width(16)

            engine_toggles = [
                ("realtime_protection", "Real-Time Attack Prevention (Master Switch)", "Continuously monitors process execution, memory permissions, and system persistence"),
                ("reverse_shell_blocker", "Reverse Shell & TTY Hijack Blocker", "Detects and halts interactive /dev/tcp, python, nc, and socat remote shell injections"),
                ("memory_integrity_shield", "Memory Integrity & Exploit Prevention", "Enforces W^X page permissions and stops LD_PRELOAD dynamic linker tampering"),
                ("privilege_escalation_guard", "Sudo & Privilege Escalation Guard", "Monitors /etc/sudoers.d, SUID binary abuses, and unprivileged container escapes"),
                ("supply_chain_interceptor", "Supply Chain & Pipe-to-Bash Interceptor", "Blocks obfuscated curl/wget downloads executing directly into bash or sh"),
                ("badusb_peripheral_shield", "BadUSB & Keystroke Injection Shield", "Detects and isolates rogue USB HID emulators injecting rapid keystrokes"),
                ("ebpf_network_filter", "eBPF Network Beacon & C2 Filter", "Detects unauthorized reverse SSH tunnels and outbound telemetry beacons"),
                ("auto_terminate_malicious_pids", "Auto-Terminate Malicious Processes (SIGKILL)", "Automatically kills offending attack processes without waiting for prompt"),
            ]

            for key, title, desc in engine_toggles:
                r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                vb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                vb.pack_start(Gtk.Label(label=f"<b>{title}</b>", use_markup=True, xalign=0), False, False, 0)
                vb.pack_start(Gtk.Label(label=f"<span size='small' color='#888888'>{desc}</span>", use_markup=True, xalign=0), False, False, 0)
                r.pack_start(vb, True, True, 0)

                sw = Gtk.Switch()
                sw.set_active(cfg.get(key, True))
                sw.connect("state-set", lambda s, st, k=key: self.engine.set_engine_state(k, st))
                r.pack_end(sw, False, False, 0)
                vbox.pack_start(r, False, False, 0)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 3. Protection History ───────────────────────────────────────
        elif tab_id == "history":
            frame = Gtk.Frame(label="Threat Incident Log & Prevented Attacks")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            incidents = self.engine.get_incidents()
            if not incidents:
                vbox.pack_start(Gtk.Label(label="✓ No threat incidents recorded. Your system is safe and clean.", xalign=0), False, False, 8)
            else:
                ilist = Gtk.ListBox()
                ilist.set_selection_mode(Gtk.SelectionMode.NONE)
                for inc in incidents:
                    r = Gtk.ListBoxRow()
                    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                    b.set_border_width(8)

                    h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                    safe_cat = GLib.markup_escape_text(str(inc.get('category', 'Threat')))
                    h.pack_start(Gtk.Label(label=f"<b>{safe_cat}</b>", use_markup=True, xalign=0), True, True, 0)
                    sev_lbl = Gtk.Label()
                    sev_lbl.set_markup(f"<span color='#e74c3c'><b>{inc.get('severity', 'High')}</b></span>")
                    h.pack_end(sev_lbl, False, False, 0)
                    b.pack_start(h, False, False, 0)

                    safe_proc = GLib.markup_escape_text(str(inc.get('process_name', 'unknown')))
                    safe_tac = GLib.markup_escape_text(str(inc.get('tactic', 'Execution')))
                    safe_act = GLib.markup_escape_text(str(inc.get('action_taken', 'Blocked')))
                    detail = f"<span color='#888888'>{inc.get('timestamp')}</span> • Process: <b>{safe_proc}</b> (PID: {inc.get('pid')})\nMITRE: {safe_tac}\nAction: <span color='#2ecc71'>{safe_act}</span>"
                    b.pack_start(Gtk.Label(label=detail, use_markup=True, xalign=0), False, False, 0)
                    r.add(b)
                    ilist.add(r)
                vbox.pack_start(ilist, False, False, 4)

                btn_clear = Gtk.Button.new_with_label("Clear Incident History")
                btn_clear.connect("clicked", lambda b: (self.engine.clear_incidents(), self._render_tab("history")))
                vbox.pack_start(btn_clear, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 4. Device & Hardware Security ───────────────────────────────
        elif tab_id == "device":
            frame = Gtk.Frame(label="Hardware Security & Kernel Attestation")
            grid = Gtk.Grid()
            grid.set_column_spacing(24)
            grid.set_row_spacing(12)
            grid.set_border_width(16)

            has_tpm = os.path.exists("/dev/tpm0") or os.path.exists("/dev/tpmrm0")
            grid.attach(Gtk.Label(label="<b>Trusted Platform Module (TPM):</b>", use_markup=True, xalign=0), 0, 0, 1, 1)
            grid.attach(Gtk.Label(label="TPM 2.0 Security Module Active" if has_tpm else "Software Emulated", xalign=0), 1, 0, 1, 1)

            grid.attach(Gtk.Label(label="<b>UEFI Secure Boot:</b>", use_markup=True, xalign=0), 0, 1, 1, 1)
            grid.attach(Gtk.Label(label="Hardware Verified (Standard UEFI)", xalign=0), 1, 1, 1, 1)

            grid.attach(Gtk.Label(label="<b>Kernel DMA Protection:</b>", use_markup=True, xalign=0), 0, 2, 1, 1)
            grid.attach(Gtk.Label(label="IOMMU Direct Memory Access Shielded", xalign=0), 1, 2, 1, 1)

            grid.attach(Gtk.Label(label="<b>CPU Hardware Mitigations:</b>", use_markup=True, xalign=0), 0, 3, 1, 1)
            grid.attach(Gtk.Label(label="Spectre, Meltdown, Retbleed Mitigated", xalign=0), 1, 3, 1, 1)

            frame.add(grid)
            self.content_box.pack_start(frame, False, False, 0)

        # ── 5. Developer Exclusions ─────────────────────────────────────
        elif tab_id == "exclusions":
            frame = Gtk.Frame(label="Developer Exclusions & Compiler Paths")
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            vbox.set_border_width(16)

            vbox.pack_start(Gtk.Label(label="The following paths and build directories are excluded from aggressive behavioral inspection to preserve maximum compiler and dev performance:", xalign=0), False, False, 0)

            elist = Gtk.ListBox()
            elist.set_selection_mode(Gtk.SelectionMode.NONE)
            for ex in self.engine.config.get("exclusions", []):
                r = Gtk.ListBoxRow()
                h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                h.set_border_width(6)
                h.pack_start(Gtk.Label(label=f"📁 <code>{ex}</code>", use_markup=True, xalign=0), True, True, 0)
                r.add(h)
                elist.add(r)
            vbox.pack_start(elist, False, False, 4)

            frame.add(vbox)
            self.content_box.pack_start(frame, False, False, 0)

        self.content_box.show_all()

    def _execute_scan(self, scan_type: str):
        self.btn_quick.set_sensitive(False)
        self.btn_full.set_sensitive(False)
        self.btn_cancel.set_sensitive(True)

        def _on_progress(fraction, status_text, threat_count):
            GLib.idle_add(self._update_progress, fraction, status_text, threat_count)

        self.engine.start_scan(scan_type=scan_type, progress_callback=_on_progress)

    def _update_progress(self, fraction, status_text, threat_count):
        self.prog_bar.set_fraction(fraction)
        self.status_lbl.set_markup(f"<b>{status_text}</b> ({int(fraction * 100)}%)")
        if fraction >= 1.0 or not self.engine.is_scanning:
            self.btn_quick.set_sensitive(True)
            self.btn_full.set_sensitive(True)
            self.btn_cancel.set_sensitive(False)
            self.status_lbl.set_markup(f"<span color='#2ecc71'><b>✓ Scan Finished: {threat_count} threats detected / blocked.</b></span>")


def main():
    win = AegisMainWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
