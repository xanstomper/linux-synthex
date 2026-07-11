#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Security Dashboard — GTK4/libadwaita
# Live firewall status, audit log viewer, AppArmor/SELinux, fail2ban, ClamAV

import sys, os, subprocess, threading, re, time
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, Adw, GLib, Gio

APP_ID  = "org.synthos.SecurityDashboard"
VERSION = "2026.10"


def run(cmd: list[str], timeout: int = 10) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"error: {e}"


def run_root(cmd: list[str], timeout: int = 30) -> tuple[int, str]:
    try:
        r = subprocess.run(["pkexec"] + cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except Exception as e:
        return 1, str(e)


def svc_active(unit: str) -> bool:
    return run(["systemctl", "is-active", "--quiet", unit]) == ""


def svc_enabled(unit: str) -> bool:
    r = subprocess.run(["systemctl", "is-enabled", unit], capture_output=True)
    return r.returncode == 0


# ── Score calculation ─────────────────────────────────────────────────────────
def compute_security_score() -> tuple[int, list[dict]]:
    checks = [
        {"name": "Firewall (firewalld)",    "ok": svc_active("firewalld.service"),          "weight": 20},
        {"name": "SELinux enforcing",       "ok": run(["getenforce"]) == "Enforcing",        "weight": 15},
        {"name": "Fail2ban active",         "ok": svc_active("fail2ban.service"),            "weight": 10},
        {"name": "Root login disabled",     "ok": _check_root_login_disabled(),              "weight": 15},
        {"name": "SSH password auth off",   "ok": _check_ssh_nopasswd(),                     "weight": 10},
        {"name": "Automatic updates on",    "ok": svc_enabled("dnf-automatic-install.timer"),"weight": 10},
        {"name": "auditd running",          "ok": svc_active("auditd.service"),              "weight": 5 },
        {"name": "AIDE installed",          "ok": bool(run(["which","aide"])),               "weight": 5 },
        {"name": "ClamAV installed",        "ok": bool(run(["which","clamscan"])),           "weight": 5 },
        {"name": "No world-writable /etc",  "ok": _check_no_world_writable(),               "weight": 5 },
    ]
    score = sum(c["weight"] for c in checks if c["ok"])
    return score, checks


def _check_root_login_disabled() -> bool:
    try:
        out = open("/etc/passwd").read()
        m = re.search(r"^root:[^:]*:0:0:[^:]*:.*:(.+)$", out, re.M)
        if m:
            shell = m.group(1).strip()
            return shell in ("/sbin/nologin", "/usr/sbin/nologin", "/bin/false")
    except Exception:
        pass  # service-check best-effort; UI continues
    return False


def _check_ssh_nopasswd() -> bool:
    try:
        sshd_cfg = open("/etc/ssh/sshd_config").read()
        m = re.search(r"^\s*PasswordAuthentication\s+(\w+)", sshd_cfg, re.M | re.I)
        return m and m.group(1).lower() == "no"
    except Exception:
        return True  # SSH might not be installed → not a risk


def _check_no_world_writable() -> bool:
    try:
        r = subprocess.run(
            ["find", "/etc", "-maxdepth", "2", "-perm", "-o+w", "-not", "-type", "l"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.strip() == ""
    except Exception:
        return True


# ── Main Window ───────────────────────────────────────────────────────────────
class SecurityDashboardWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Security Dashboard",
                         default_width=1000, default_height=720)
        self._build_ui()
        self._refresh_all()
        # Auto-refresh every 30s
        GLib.timeout_add_seconds(30, self._auto_refresh)

    def _build_ui(self):
        # ── Root layout ───────────────────────────────────────────────────────
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)

        # Header
        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="SynthOS Security Dashboard"))
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic",
                                 tooltip_text="Refresh all checks")
        refresh_btn.connect("clicked", lambda b: self._refresh_all())
        hb.pack_end(refresh_btn)
        root.append(hb)

        # Score banner
        self._score_row = Adw.ActionRow(title="Security Score", subtitle="Calculating…")
        self._score_badge = Gtk.Label(label="…/100")
        self._score_badge.add_css_class("title-1")
        self._score_row.add_suffix(self._score_badge)

        score_list = Gtk.ListBox()
        score_list.add_css_class("boxed-list")
        score_list.set_margin_start(16); score_list.set_margin_end(16)
        score_list.set_margin_top(16);  score_list.set_margin_bottom(8)
        score_list.append(self._score_row)
        root.append(score_list)

        # Tab view
        self._tab = Adw.TabView()
        bar = Adw.TabBar()
        bar.set_view(self._tab)
        root.append(bar)
        root.append(self._tab)

        self._tab.append(self._build_overview_page()).set_title("Overview")
        self._tab.append(self._build_firewall_page()).set_title("Firewall")
        self._tab.append(self._build_selinux_page()).set_title("SELinux")
        self._tab.append(self._build_fail2ban_page()).set_title("Fail2ban")
        self._tab.append(self._build_audit_page()).set_title("Audit Log")
        self._tab.append(self._build_clamav_page()).set_title("ClamAV")

    # ── Overview ──────────────────────────────────────────────────────────────
    def _build_overview_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=8)
        scroll.set_child(box)

        # Checks list
        self._checks_list = Gtk.ListBox()
        self._checks_list.add_css_class("boxed-list")
        box.append(self._checks_list)

        # Quick actions
        lbl = Gtk.Label(label="Quick Actions", xalign=0, margin_top=12)
        lbl.add_css_class("title-3")
        box.append(lbl)

        actions_box = Gtk.FlowBox(row_spacing=8, column_spacing=8,
                                  homogeneous=False, max_children_per_line=4)
        box.append(actions_box)

        quick_actions = [
            ("Enable Firewall",  lambda: run_root(["systemctl","enable","--now","firewalld"]), "network-firewall"),
            ("Run ClamAV Scan",  self._run_clamav_scan,                                       "edit-find"),
            ("View Audit Log",   lambda: None,                                                 "text-x-log"),
            ("Update System",    lambda: run_root(["dnf","upgrade","-y"]),                    "system-software-update"),
            ("Check SELinux",    lambda: None,                                                 "security-medium"),
            ("Fail2ban Status",  lambda: None,                                                 "network-vpn"),
        ]

        for label, action, icon in quick_actions:
            btn = Gtk.Button(label=label, icon_name=icon)
            btn.connect("clicked", lambda b, a=action: threading.Thread(target=a, daemon=True).start())
            actions_box.insert(btn, -1)

        return scroll

    # ── Firewall ──────────────────────────────────────────────────────────────
    def _build_firewall_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=12)
        scroll.set_child(box)

        # Status
        self._fw_status_row = Adw.ActionRow(
            title="Firewall Status",
            subtitle="Checking…"
        )
        self._fw_toggle = Gtk.Switch(valign=Gtk.Align.CENTER)
        self._fw_toggle.connect("state-set", self._on_fw_toggle)
        self._fw_status_row.add_suffix(self._fw_toggle)

        fw_list = Gtk.ListBox()
        fw_list.add_css_class("boxed-list")
        fw_list.append(self._fw_status_row)
        box.append(fw_list)

        # Zone info
        self._fw_zone_lbl = Gtk.Label(label="Active zone: —", xalign=0)
        self._fw_zone_lbl.add_css_class("caption")
        box.append(self._fw_zone_lbl)

        # Open ports
        lbl = Gtk.Label(label="Open Ports", xalign=0)
        lbl.add_css_class("title-3")
        box.append(lbl)

        self._fw_ports_text = Gtk.TextView(editable=False, monospace=True)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(200)
        sw.set_child(self._fw_ports_text)
        box.append(sw)

        # Quick port actions
        port_row = Gtk.Box(spacing=8)
        self._port_entry = Gtk.Entry(placeholder_text="Port (e.g. 22/tcp)")
        self._port_entry.set_hexpand(True)
        open_btn  = Gtk.Button(label="Open Port",  css_classes=["suggested-action"])
        close_btn = Gtk.Button(label="Close Port", css_classes=["destructive-action"])
        open_btn.connect("clicked",  self._on_open_port)
        close_btn.connect("clicked", self._on_close_port)
        port_row.append(self._port_entry)
        port_row.append(open_btn)
        port_row.append(close_btn)
        box.append(port_row)

        return scroll

    # ── SELinux ───────────────────────────────────────────────────────────────
    def _build_selinux_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=12)
        scroll.set_child(box)

        # Mode selector
        self._sel_mode_row = Adw.ComboRow(title="SELinux Mode")
        self._sel_mode_row.set_model(Gtk.StringList.new(["Enforcing", "Permissive", "Disabled"]))
        self._sel_mode_row.connect("notify::selected", self._on_selinux_mode_changed)

        sel_list = Gtk.ListBox()
        sel_list.add_css_class("boxed-list")
        sel_list.append(self._sel_mode_row)
        box.append(sel_list)

        # Policy violations
        lbl = Gtk.Label(label="Recent AVC Denials", xalign=0)
        lbl.add_css_class("title-3")
        box.append(lbl)

        self._sel_denials_text = Gtk.TextView(editable=False, monospace=True)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(300)
        sw.set_child(self._sel_denials_text)
        box.append(sw)

        btn = Gtk.Button(label="Refresh AVC Denials")
        btn.connect("clicked", lambda b: self._refresh_selinux_denials())
        box.append(btn)
        return scroll

    # ── Fail2ban ──────────────────────────────────────────────────────────────
    def _build_fail2ban_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=12)
        scroll.set_child(box)

        f2b_list = Gtk.ListBox()
        f2b_list.add_css_class("boxed-list")

        self._f2b_status_row = Adw.ActionRow(title="Fail2ban Service", subtitle="Checking…")
        f2b_sw = Gtk.Switch(valign=Gtk.Align.CENTER)
        f2b_sw.set_active(svc_active("fail2ban.service"))
        f2b_sw.connect("state-set", lambda sw, s: run_root(
            ["systemctl", "enable" if s else "disable", "--now", "fail2ban"]))
        self._f2b_status_row.add_suffix(f2b_sw)
        f2b_list.append(self._f2b_status_row)
        box.append(f2b_list)

        lbl = Gtk.Label(label="Banned IPs", xalign=0)
        lbl.add_css_class("title-3")
        box.append(lbl)

        self._f2b_bans_text = Gtk.TextView(editable=False, monospace=True)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(250)
        sw.set_child(self._f2b_bans_text)
        box.append(sw)

        row = Gtk.Box(spacing=8)
        self._unban_entry = Gtk.Entry(placeholder_text="IP to unban")
        self._unban_entry.set_hexpand(True)
        unban_btn = Gtk.Button(label="Unban IP", css_classes=["destructive-action"])
        unban_btn.connect("clicked", self._on_unban_ip)
        row.append(self._unban_entry)
        row.append(unban_btn)
        box.append(row)
        return scroll

    # ── Audit Log ─────────────────────────────────────────────────────────────
    def _build_audit_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=12)
        scroll.set_child(box)

        lbl = Gtk.Label(label="Recent Audit Events", xalign=0)
        lbl.add_css_class("title-3")
        box.append(lbl)

        self._audit_text = Gtk.TextView(editable=False, monospace=True)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(400)
        sw.set_child(self._audit_text)
        box.append(sw)

        filter_row = Gtk.Box(spacing=8)
        self._audit_filter = Gtk.Entry(placeholder_text="Filter events (e.g. USER_LOGIN, SYSCALL)…")
        self._audit_filter.set_hexpand(True)
        filter_btn = Gtk.Button(label="Filter")
        filter_btn.connect("clicked", lambda b: self._refresh_audit_log())
        filter_row.append(self._audit_filter)
        filter_row.append(filter_btn)
        box.append(filter_row)
        return scroll

    # ── ClamAV ────────────────────────────────────────────────────────────────
    def _build_clamav_page(self) -> Gtk.Widget:
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                      margin_start=16, margin_end=16, margin_top=8, margin_bottom=16,
                      spacing=12)
        scroll.set_child(box)

        clam_list = Gtk.ListBox()
        clam_list.add_css_class("boxed-list")

        self._clam_version_row = Adw.ActionRow(
            title="ClamAV",
            subtitle=run(["clamscan","--version"]) or "Not installed"
        )
        clam_list.append(self._clam_version_row)

        self._clam_db_row = Adw.ActionRow(
            title="Virus definitions",
            subtitle="Checking…"
        )
        update_btn = Gtk.Button(label="Update DB", valign=Gtk.Align.CENTER)
        update_btn.connect("clicked", lambda b: threading.Thread(
            target=lambda: run_root(["freshclam"]), daemon=True).start())
        self._clam_db_row.add_suffix(update_btn)
        clam_list.append(self._clam_db_row)
        box.append(clam_list)

        # Scan target
        lbl = Gtk.Label(label="On-Demand Scan", xalign=0)
        lbl.add_css_class("title-3")
        box.append(lbl)

        scan_row = Gtk.Box(spacing=8)
        self._scan_path = Gtk.Entry(text=str(os.path.expanduser("~")))
        self._scan_path.set_hexpand(True)
        scan_btn = Gtk.Button(label="Scan", css_classes=["suggested-action"])
        scan_btn.connect("clicked", lambda b: self._run_clamav_scan())
        scan_row.append(self._scan_path)
        scan_row.append(scan_btn)
        box.append(scan_row)

        self._clam_progress = Gtk.ProgressBar(show_text=True, text="Idle")
        box.append(self._clam_progress)

        self._clam_results = Gtk.TextView(editable=False, monospace=True)
        sw = Gtk.ScrolledWindow()
        sw.set_min_content_height(250)
        sw.set_child(self._clam_results)
        box.append(sw)
        return scroll

    # ── Refresh logic ─────────────────────────────────────────────────────────
    def _refresh_all(self):
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        score, checks = compute_security_score()
        fw_active   = svc_active("firewalld.service")
        fw_zone     = run(["firewall-cmd","--get-default-zone"])
        fw_ports    = run(["firewall-cmd","--list-ports"])
        f2b_active  = svc_active("fail2ban.service")
        f2b_bans    = run(["fail2ban-client","status","sshd"], timeout=5)
        sel_mode    = run(["getenforce"])
        audit_tail  = run(["ausearch","-ts","recent","-i"], timeout=8) or \
                      run(["tail","-n","50","/var/log/audit/audit.log"])

        GLib.idle_add(self._update_ui, score, checks, fw_active, fw_zone,
                      fw_ports, f2b_active, f2b_bans, sel_mode, audit_tail)

    def _update_ui(self, score, checks, fw_active, fw_zone,
                   fw_ports, f2b_active, f2b_bans, sel_mode, audit_tail):
        # Score badge
        color = "green" if score >= 80 else "orange" if score >= 60 else "red"
        self._score_badge.set_markup(f'<span foreground="{color}"><b>{score}/100</b></span>')
        self._score_row.set_subtitle(
            f"{'Excellent' if score>=80 else 'Good' if score>=60 else 'Needs attention'} — "
            f"{sum(1 for c in checks if c['ok'])}/{len(checks)} checks passed"
        )

        # Checks list
        while True:
            row = self._checks_list.get_row_at_index(0)
            if row is None: break
            self._checks_list.remove(row)

        for c in checks:
            row = Adw.ActionRow(title=c["name"])
            icon = Gtk.Image.new_from_icon_name(
                "emblem-ok-symbolic" if c["ok"] else "emblem-important-symbolic"
            )
            icon.set_pixel_size(16)
            if c["ok"]:
                icon.add_css_class("success")
            else:
                icon.add_css_class("error")
            row.add_suffix(icon)
            self._checks_list.append(row)

        # Firewall
        self._fw_status_row.set_subtitle("Running" if fw_active else "Stopped")
        self._fw_toggle.set_active(fw_active)
        self._fw_zone_lbl.set_label(f"Active zone: {fw_zone or '—'}  |  Open ports: {fw_ports or 'none'}")
        self._fw_ports_text.get_buffer().set_text(
            run(["firewall-cmd","--list-all"]) or "firewalld not running"
        )

        # Fail2ban
        self._f2b_status_row.set_subtitle("Active" if f2b_active else "Stopped")
        self._f2b_bans_text.get_buffer().set_text(f2b_bans or "Fail2ban not running")

        # SELinux mode
        idx = {"Enforcing": 0, "Permissive": 1, "Disabled": 2}.get(sel_mode, 0)
        self._sel_mode_row.set_selected(idx)

        # Audit
        self._audit_text.get_buffer().set_text(audit_tail or "No audit events (is auditd running?)")
        return False

    def _refresh_selinux_denials(self):
        def worker():
            out = run(["ausearch","-m","AVC","-ts","today","-i"]) or \
                  run(["grep","avc: denied","/var/log/audit/audit.log","| tail -50"]) or \
                  "No AVC denials found today"
            GLib.idle_add(lambda: self._sel_denials_text.get_buffer().set_text(out))
        threading.Thread(target=worker, daemon=True).start()

    def _refresh_audit_log(self):
        flt = self._audit_filter.get_text()
        def worker():
            if flt:
                out = run(["ausearch","-ts","recent","-i","-m",flt.upper()]) or f"No events matching '{flt}'"
            else:
                out = run(["ausearch","-ts","recent","-i"]) or "No recent audit events"
            GLib.idle_add(lambda: self._audit_text.get_buffer().set_text(out))
        threading.Thread(target=worker, daemon=True).start()

    def _auto_refresh(self) -> bool:
        self._refresh_all()
        return True  # keep repeating

    # ── Actions ───────────────────────────────────────────────────────────────
    def _on_fw_toggle(self, sw, state):
        action = "enable" if state else "disable"
        threading.Thread(
            target=lambda: run_root(["systemctl", action, "--now", "firewalld"]),
            daemon=True
        ).start()

    def _on_open_port(self, _btn):
        port = self._port_entry.get_text().strip()
        if not port: return
        threading.Thread(
            target=lambda: run_root(["firewall-cmd", "--permanent", f"--add-port={port}",
                                     "&&", "firewall-cmd", "--reload"]),
            daemon=True
        ).start()

    def _on_close_port(self, _btn):
        port = self._port_entry.get_text().strip()
        if not port: return
        threading.Thread(
            target=lambda: run_root(["firewall-cmd", "--permanent", f"--remove-port={port}",
                                     "&&", "firewall-cmd", "--reload"]),
            daemon=True
        ).start()

    def _on_selinux_mode_changed(self, row, _):
        modes = ["enforcing", "permissive", "permissive"]  # "disabled" needs reboot
        idx   = row.get_selected()
        if idx == 2:
            # Disabled needs /etc/selinux/config edit + reboot — just warn
            return
        threading.Thread(
            target=lambda: run_root(["setenforce", modes[idx]]),
            daemon=True
        ).start()

    def _on_unban_ip(self, _btn):
        ip = self._unban_entry.get_text().strip()
        if not ip: return
        threading.Thread(
            target=lambda: run_root(["fail2ban-client", "unban", ip]),
            daemon=True
        ).start()

    def _run_clamav_scan(self):
        path = getattr(self, "_scan_path", None)
        target = path.get_text() if path else str(os.path.expanduser("~"))
        self._clam_progress.set_fraction(0)
        self._clam_progress.set_text("Scanning…")

        def worker():
            out = run(["clamscan", "-r", "--infected", "--bell", target], timeout=600)
            GLib.idle_add(lambda: self._clam_results.get_buffer().set_text(out))
            GLib.idle_add(lambda: self._clam_progress.set_fraction(1.0))
            GLib.idle_add(lambda: self._clam_progress.set_text("Scan complete"))
        threading.Thread(target=worker, daemon=True).start()


# ── Application ───────────────────────────────────────────────────────────────
class SecurityDashboardApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self._on_activate)

    def _on_activate(self, _app):
        win = SecurityDashboardWindow(self)
        win.present()


if __name__ == "__main__":
    app = SecurityDashboardApp()
    sys.exit(app.run(sys.argv))
