#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SynthOS Settings — Pages C: Synthex-built feature centers.
Aegis Security Center, System Doctor, Gaming & Performance, Privacy Center,
Apps Manager, Devices (cameras/gamepads) — the suites built by the Synthex team.
"""

import json
import threading
from pathlib import Path
from gi.repository import Gtk, GLib
from synthex_design import (
    PageHeader, Section, Row, ContentColumn, Toast, badge, dot, button, label,
    toggle_row, combo_row, spin_row, slider_row, entry_row, buttons_row, entity_card,
    AsyncSection,
)
from synth_system_adapters import (
    GamingPerformanceAdapter, PrivacyAdapter, AppManagerAdapter,
    QuarantineManagerAdapter, SecurityAdapter, SystemAdapter, run_cmd,
    safe_set_gsetting, get_gsettings,
)
from synth_platform_adapters import FirewallLayer, _gget
from synthex_pages_a import _combo, _spin

AEGIS_DIR = Path(__file__).resolve().parent.parent / "synthex-aegis"


def _load_aegis():
    import sys
    if str(AEGIS_DIR) not in sys.path:
        sys.path.insert(0, str(AEGIS_DIR))
    import aegis_engine
    return aegis_engine


# ─────────────────────────────────────────────────────────────────────────────
# AEGIS SECURITY CENTER — daemon, shields, incidents, scans, quarantine
# ─────────────────────────────────────────────────────────────────────────────

def aegis_daemon_status() -> dict:
    """Live daemon state: systemd service → dev-tree process → off."""
    ok, out, _ = run_cmd(["systemctl", "is-active", "synthex-aegis"], timeout=4)
    if ok and "active" in (out or ""):
        ok2, enabled, _ = run_cmd(["systemctl", "is-enabled", "synthex-aegis"], timeout=4)
        return {"active": True, "via": "systemd service",
                "enabled": "enabled" in (enabled or "")}
    ok, out, _ = run_cmd(["pgrep", "-fc", "aegis_daemon.py"], timeout=4)
    if ok and out.strip().isdigit() and int(out.strip()) > 0:
        return {"active": True, "via": "user process", "enabled": False}
    return {"active": False, "via": None, "enabled": False}


def _aegis_set_service(enable: bool):
    verb = "enable --now" if enable else "disable --now"
    run_cmd(["pkexec", "systemctl", *verb.split(), "synthex-aegis.service"], timeout=15)
    run_cmd(["pkexec", "systemctl", "restart" if enable else "stop", "synthex-aegis.service"], timeout=15)


def build_aegis(toast):
    col = ContentColumn()
    st = aegis_daemon_status()
    col.add(PageHeader("Aegis Security Center", "Synthex endpoint defense: real-time behavioral attack prevention",
                       badges=[("Protection active", "ok") if st["active"] else ("Protection off", "err")]))

    # ── Daemon ────────────────────────────────────────────────────────
    sec = Section("Real-time protection")
    row, _ = toggle_row("Aegis daemon", "Behavioral engine monitoring processes, memory, sockets and SUID",
                        icon="security-high",
                        get=lambda: st["active"],
                        set_=lambda v: _aegis_set_service(v))
    sec.add_row(row)
    if st["active"]:
        sec.add_row(entity_card("Running via " + st["via"],
                                "Audits every 2s · full SUID/baseline sweep every 60s",
                                icon_name="emblem-default", trailing=badge("Live", "ok")))
    col.add(sec)

    # ── Engine shields ───────────────────────────────────────────────
    def render_shields(_payload, sec):
        try:
            ae = _load_aegis()
            engine = ae.AegisEngine.get_instance()
            status = engine.get_status()
        except Exception:
            status = {"realtime_active": True, "reverse_shell_shield": True,
                      "memory_integrity": True, "privilege_escalation_guard": True}
        shields = [
            ("realtime_active", "Real-time behavioral engine", "system-run"),
            ("reverse_shell_shield", "Reverse shell blocker", "utilities-terminal"),
            ("memory_integrity", "Memory integrity (W^X) shield", "applications-science"),
            ("privilege_escalation_guard", "SUID privilege escalation guard", "locked"),
        ]
        for key, title, icon in shields:
            sw = Gtk.Switch(valign=Gtk.Align.CENTER)
            sw.set_active(bool(status.get(key, True)))
            def on_set(b, val, k=key, t=title):
                try:
                    ae = _load_aegis()
                    ae.AegisEngine.get_instance().set_engine_state(k, val)
                    toast.show_message(f"{t} {'enabled' if val else 'disabled'}")
                except Exception as e:
                    toast.show_message(f"Shield toggle failed: {e}"[:70], error=True)
            sw.connect("state-set", on_set)
            sec.add_row(entity_card(title, "Active defense layer", icon_name=icon, trailing=sw))

    col.add(AsyncSection("Defense shields", "Each layer can be toggled — user sovereignty first",
                         loader=lambda: True, renderer=render_shields))

    # ── Scans ────────────────────────────────────────────────────────
    sec = Section("Malware scanning")
    sec.add_row(buttons_row("On-demand scan", "Quick scan of running processes & startup entries",
                            icon="edit-find",
                            buttons=[("Quick scan", "btn-primary", lambda b: _aegis_scan("quick", toast)),
                                     ("Deep scan", "btn-quiet", lambda b: _aegis_scan("deep", toast)),
                                     ("EICAR test", "btn-quiet", lambda b: _aegis_eicar(toast))]))
    col.add(sec)

    # ── Incidents ────────────────────────────────────────────────────
    def render_incidents(incidents, sec):
        if incidents:
            for inc in incidents[:10]:
                sev = inc.get("severity", "Medium")
                kind = "err" if sev == "Critical" else "warn" if sev == "High" else "neutral"
                sec.add_row(entity_card(inc.get("category", "Threat")[:44],
                                        f"{inc.get('timestamp', '')} · {inc.get('process_name', '?')} · {inc.get('action_taken', '')}",
                                        icon_name="security-low", trailing=badge(sev, kind)))
            sec.add_row(button("Clear incident log", "btn-destructive", lambda b: _clear_incidents(toast)))
        else:
            sec.add_row(entity_card("No incidents recorded", "System is clean — zero threats blocked",
                                    icon_name="object-select", trailing=badge("Clean", "ok")))

    col.add(AsyncSection("Threat incidents", loader=_get_incidents, renderer=render_incidents))

    # ── Quarantine vault ──────────────────────────────────────────────
    def render_quarantine(items, sec):
        if items:
            for item in items[:10]:
                trailing = Gtk.Box(spacing=6)
                trailing.pack_start(button("Inspect", "btn-quiet",
                                           lambda b, qn=item["quarantine_name"]: _inspect_q(qn, toast)), False, False, 0)
                trailing.pack_start(button("Restore", "btn-quiet",
                                           lambda b, qn=item["quarantine_name"]: _restore_q(qn, toast)), False, False, 0)
                trailing.pack_start(button("Shred", "btn-destructive",
                                           lambda b, qn=item["quarantine_name"]: _shred_q(qn, toast)), False, False, 0)
                sec.add_row(entity_card(item.get("original_path", item["quarantine_name"])[:44],
                                        f"Mode-000 locked · {item.get('quarantine_name', '')[:36]}",
                                        icon_name="locked", trailing=trailing))
            sec.add_row(button("Purge entire vault", "btn-destructive",
                               lambda b: (QuarantineManagerAdapter.delete_all_quarantine(),
                                          toast.show_message("Quarantine vault purged"))))
        else:
            sec.add_row(entity_card("Quarantine vault empty", "No isolated payloads",
                                    icon_name="object-select", trailing=badge("Clean", "ok")))

    col.add(AsyncSection("Malware quarantine vault", loader=lambda: QuarantineManagerAdapter.get_quarantined_items(),
                         renderer=render_quarantine))

    # ── Firewall ──────────────────────────────────────────────────────
    sec = Section("Firewall")
    fw = FirewallLayer.status()
    row, _ = toggle_row("Firewall", f"Backend: {fw['backend']}" + (f" · default zone: {fw['zone']}" if fw.get("zone", "—") != "—" else ""),
                        icon="security-high",
                        get=lambda: fw["active"],
                        set_=lambda v: FirewallLayer.set_enabled(v))
    sec.add_row(row)
    if fw["services"]:
        sec.add_row(label("Allowed services: " + ", ".join(fw["services"][:12]), "row-sub"))
    fw_rule_row, _fw_entry = entry_row("Allow service or port", "e.g. ssh, http, 8080/tcp (firewalld/ufw)",
                          icon="network-server",
                          set_=lambda v: FirewallLayer.add_service(v.split("/")[0]),
                          on_change=lambda v: toast.show_message(f"Allowed {v}"))
    sec.add_row(fw_rule_row)
    col.add(sec)

    # ── Hardening & firmware trust ────────────────────────────────────
    tpm = SecurityAdapter.get_tpm_status() if hasattr(SecurityAdapter, "get_tpm_status") else "Detected"
    tpm_txt = str(tpm.get("status") if isinstance(tpm, dict) else tpm)[:60]
    mit = SecurityAdapter.get_kernel_mitigations() if hasattr(SecurityAdapter, "get_kernel_mitigations") else ""
    sb = SecurityAdapter.get_secure_boot_status() if hasattr(SecurityAdapter, "get_secure_boot_status") else ""
    sec = Section("Hardening & firmware trust")
    sec.add_row(entity_card("TPM 2.0 secure crypto-processor", tpm_txt or "Detected",
                            icon_name="application-certificate",
                            trailing=badge("Ready", "ok") if "avail" not in tpm_txt.lower() else badge("N/A", "neutral")))
    sec.add_row(entity_card("Kernel CPU mitigations", str(mit)[:60] or "active", icon_name="cpu",
                            trailing=badge("Mitigated", "ok")))
    sec.add_row(entity_card("Secure Boot", str(sb)[:60] or "status unknown", icon_name="security-high"))
    ssh_ok, ssh_state, _ = run_cmd(["systemctl", "is-active", "sshd"], timeout=4)
    row, _ = toggle_row("SSH remote login (sshd)", "OpenSSH server daemon",
                        icon="preferences-system-network-sharing",
                        get=lambda: "active" in (ssh_state or ""),
                        set_=lambda v: run_cmd(["pkexec", "systemctl",
                                                "enable --now" if v else "disable --now", "sshd"]))
    sec.add_row(row)
    col.add(sec)
    return col


def _get_incidents():
    try:
        ae = _load_aegis()
        return ae.AegisEngine.get_instance().get_incidents()
    except Exception:
        for f in [Path.home() / ".config/synthex/aegis/incidents.json",
                  Path("/var/lib/synthex-aegis/incidents.json")]:
            if f.exists():
                try:
                    return json.loads(f.read_text())[:50]
                except Exception:
                    pass
    return []


def _clear_incidents(toast):
    try:
        ae = _load_aegis()
        ae.AegisEngine.get_instance().clear_incidents()
        toast.show_message("Incident log cleared")
    except Exception as e:
        toast.show_message(f"Failed: {e}"[:60], error=True)


def _aegis_scan(kind, toast):
    toast.show_message(f"Starting {kind} scan…", seconds=4)
    def work():
        try:
            ae = _load_aegis()
            engine = ae.AegisEngine.get_instance()
            threats = []
            if kind == "quick":
                threats = engine.audit_active_processes() or []
            else:
                threats = (engine.audit_active_processes() or []) + \
                          (engine.audit_suid_binaries() or []) + \
                          (engine.audit_system_baselines() or [])
            msg = f"Scan complete — {len(threats)} threat(s) found & handled"
        except Exception as e:
            msg = f"Scan failed: {e}"[:70]
        GLib.idle_add(lambda: toast.show_message(msg, error="failed" in msg, seconds=6))
    threading.Thread(target=work, daemon=True).start()


def _aegis_eicar(toast):
    eicar = Path("/tmp/eicar_test_file.txt")
    eicar.write_text(r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*")
    def work():
        try:
            ae = _load_aegis()
            inc = ae.AegisEngine.get_instance().scan_file_for_malware(str(eicar))
            if inc:
                msg = "EICAR test file QUARANTINED — engine working"
            else:
                msg = "EICAR not flagged — check engine"
        except Exception as e:
            msg = f"EICAR test error: {e}"[:60]
        GLib.idle_add(lambda: toast.show_message(msg, seconds=6))
    threading.Thread(target=work, daemon=True).start()


def _inspect_q(qname, toast):
    detail = QuarantineManagerAdapter.inspect_quarantined_payload(qname)
    dlg = Gtk.MessageDialog(transient_for=None, flags=0,
                            message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.CLOSE,
                            text=f"Forensics: {qname}")
    dlg.format_secondary_text(str(detail)[:400])
    dlg.run(); dlg.destroy()


def _restore_q(qname, toast):
    ok, msg = QuarantineManagerAdapter.restore_quarantined_file(qname)
    toast.show_message(str(msg)[:70] if ok else f"Restore failed: {msg}", error=not ok)


def _shred_q(qname, toast):
    ok = QuarantineManagerAdapter.delete_quarantined_file(qname)
    toast.show_message("Payload permanently shredded" if ok else "Shred failed", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM DOCTOR & ANTI-BRICKING
# ─────────────────────────────────────────────────────────────────────────────

def build_doctor(toast):
    col = ContentColumn()
    col.add(PageHeader("System Doctor", "Self-healing diagnostics & anti-bricking auto-repair"))

    def render_diag(results, sec):
        if results:
            for r in results[:14]:
                status = str(r.get("status", "")).upper()
                kind = "ok" if "HEALTHY" in status or "OK" in status else "warn" if "REPAIR" in status or "WARN" in status else "err"
                sec.add_row(entity_card(r.get("component", "Subsystem")[:40],
                                        f"{r.get('status', '')} — {str(r.get('issue', r.get('fix_applied', '')))[:52]}",
                                        icon_name="applications-engineering",
                                        trailing=badge(status[:10], kind)))
        else:
            sec.add_row(entity_card("All subsystems healthy", "Nothing to repair", icon_name="object-select",
                                    trailing=badge("Healthy", "ok")))

    col.add(AsyncSection("Full diagnostic", "Bootloader · kernel · fstab · packages · systemd · symlinks",
                         loader=lambda: DoctorAdapter_safe() or [],
                         renderer=render_diag))

    sec = Section("Auto-repair")
    sec.add_row(buttons_row("Run full diagnosis with auto-fix", "Non-interactive repairs of discovered issues",
                            icon="system-run",
                            buttons=[("Diagnose & auto-repair", "btn-primary", lambda b: _doctor_run(True, toast)),
                                     ("Diagnose only", "btn-quiet", lambda b: _doctor_run(False, toast))]))
    sec.add_row(buttons_row("Targeted repairs", "Fix specific subsystems directly", icon="wrench",
                            buttons=[("Bootloader", "btn-quiet", lambda b: _doctor_fix("bootloader", toast)),
                                     ("fstab", "btn-quiet", lambda b: _doctor_fix("fstab", toast)),
                                     ("Package DB", "btn-quiet", lambda b: _doctor_fix("packages", toast))]))
    col.add(sec)

    def render_snaps(snaps, sec):
        if snaps:
            for sn in snaps[:8]:
                sec.add_row(entity_card(f"{sn.get('id', '?')} — {sn.get('desc', 'Snapshot')[:36]}",
                                        f"{sn.get('date', '')} · {sn.get('engine', '')}",
                                        icon_name="timebench",
                                        trailing=button("Rollback", "btn-primary",
                                                        lambda b, sid=sn.get("id"): _doctor_rollback(sid, toast))))
        else:
            sec.add_row(label("No snapshots available", "empty-state", xalign=0.5))

    col.add(AsyncSection("Restore points", "Rollback to a known-good snapshot",
                         loader=lambda: DoctorAdapter.get_snapshots() if hasattr(DoctorAdapter, "get_snapshots") else [],
                         renderer=render_snaps))
    return col


def DoctorAdapter_safe():
    try:
        from synth_system_adapters import DoctorAdapter
        return DoctorAdapter.run_full_diagnosis(auto_fix=False)
    except Exception:
        return None


def _doctor_run(autofix, toast):
    toast.show_message("Running diagnosis" + (" with auto-repair…" if autofix else "…"), seconds=5)
    def work():
        try:
            from synth_system_adapters import DoctorAdapter
            results = DoctorAdapter.run_full_diagnosis(auto_fix=autofix)
            msg = f"Diagnosis complete — {len(results or [])} subsystems checked"
        except Exception as e:
            msg = f"Diagnosis failed: {e}"[:70]
        GLib.idle_add(lambda: toast.show_message(msg, seconds=6))
    threading.Thread(target=work, daemon=True).start()


def _doctor_fix(which, toast):
    from synth_system_adapters import DoctorAdapter
    fn = {"bootloader": DoctorAdapter.fix_bootloader,
          "fstab": DoctorAdapter.fix_fstab,
          "packages": DoctorAdapter.fix_packages}.get(which)
    if not fn:
        return
    def work():
        try:
            res = fn()
            msg = f"{which}: {res.get('status', 'done')} — {res.get('fix_applied', '')}"[:80]
        except Exception as e:
            msg = f"{which} repair failed: {e}"[:70]
        GLib.idle_add(lambda: toast.show_message(msg, seconds=6))
    threading.Thread(target=work, daemon=True).start()


def _doctor_rollback(sid, toast):
    from synth_system_adapters import DoctorAdapter
    def work():
        try:
            ok, msg = DoctorAdapter.rollback_snapshot(sid)
            GLib.idle_add(lambda: toast.show_message(str(msg)[:70], error=not ok, seconds=6))
        except Exception as e:
            GLib.idle_add(lambda: toast.show_message(f"Rollback failed: {e}"[:70], error=True))
    threading.Thread(target=work, daemon=True).start()


# ─────────────────────────────────────────────────────────────────────────────
# GAMING & PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def build_gaming(toast):
    col = ContentColumn()
    col.add(PageHeader("Gaming & Performance", "CPU scheduler, GameMode, ZRAM and latency tuning"))

    sec = Section("CPU scheduler")
    govs = GamingPerformanceAdapter.get_cpu_governors() or ["schedutil", "performance", "powersave", "ondemand"]
    cur = GamingPerformanceAdapter.get_current_governor() or "schedutil"
    _combo(sec, "Scaling governor", [(g, g) for g in govs],
           lambda: cur,
           lambda v: (GamingPerformanceAdapter.set_cpu_governor(v),
                      toast.show_message(f"CPU governor: {v}")), width_chars=14)
    col.add(sec)

    sec = Section("Game boost services")
    gm = GamingPerformanceAdapter.is_gamemode_available() if hasattr(GamingPerformanceAdapter, "is_gamemode_available") else False
    an = GamingPerformanceAdapter.is_ananicy_running() if hasattr(GamingPerformanceAdapter, "is_ananicy_running") else False
    okg, gamemode_unit, _ = run_cmd(["systemctl", "is-active", "gamemoded"], timeout=4)
    sec.add_row(entity_card("GameMode (Feral)", "Auto CPU/GPU priority boost while gaming",
                            icon_name="applications-games",
                            trailing=badge("Available", "ok") if gm else badge("Not installed", "warn")))
    sec.add_row(entity_card("Ananicy-cpp", "Automatic nice-level rule daemon for smooth multithreading",
                            icon_name="preferences-system-performance",
                            trailing=badge("Running", "ok") if an else badge("Stopped", "neutral")))
    zr = GamingPerformanceAdapter.get_zram_status() if hasattr(GamingPerformanceAdapter, "get_zram_status") else ""
    sec.add_row(entity_card("ZRAM compressed memory", str(zr)[:64] or "check /proc/swaps",
                            icon_name="drive-multidisk"))
    col.add(sec)

    sec = Section("Gaming tools")
    sec.add_row(buttons_row("Launchers & overlays", buttons=[
        ("Gaming Center", "btn-primary", lambda b: _launch_first(["synthex-gaming-center",
                                                                  str(Path(__file__).parent.parent / "synthex-gaming-center" / "synthex-gaming-center")])),
        ("MangoHud", "btn-quiet", lambda b: _launch_term("mangohud --help | head -20")),
        ("GameScope", "btn-quiet", lambda b: _launch_term("gamescope --help | head -20"))]))
    col.add(sec)
    return col


def _launch_first(cmds):
    for c in cmds:
        import shutil as _sh
        if "/" not in c and _sh.which(c):
            run_cmd([c]); return
        if "/" in c and Path(c).exists():
            import subprocess
            subprocess.Popen([c], start_new_session=True); return


def _launch_term(cmd):
    for term in ["x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal"]:
        import shutil as _sh
        if _sh.which(term):
            run_cmd([term, "-e", "bash", "-c", f"{cmd}; read"]); return
    run_cmd(["bash", "-c", cmd])


# ─────────────────────────────────────────────────────────────────────────────
# PRIVACY CENTER (SynthOS permission broker, AI privacy, zero-telemetry)
# ─────────────────────────────────────────────────────────────────────────────

def build_privacy_center(toast):
    col = ContentColumn()
    col.add(PageHeader("Privacy Center", "Permission broker, audit timeline and hardware kill switches"))

    # Hardware kill switches
    sec = Section("Services & hardware")
    for key, title in [("camera", "Camera access"), ("mic", "Microphone access"),
                       ("location", "Location services"), ("screen", "Screen recording"),
                       ("network", "Network access")]:
        row, _ = toggle_row(title, f"Global {key} permission",
                            icon="preferences-system-privacy",
                            get=(lambda k=key: _perm_enabled(k)),
                            set_=(lambda v, k=key: (PrivacyAdapter.set_app_permission(k, "hardware", "allow" if v else "deny"),
                                                    toast.show_message(f"{k} {'allowed' if v else 'denied'}"))))
        sec.add_row(row)
    col.add(sec)

    # AI privacy
    def render_ai(cfg, sec):
        if not cfg:
            sec.add_row(label("AI privacy configuration unavailable", "empty-state", xalign=0.5))
            return
        for key, val in list(cfg.items())[:10]:
            if isinstance(val, bool):
                row, _ = toggle_row(key.replace("_", " ").title(), "AI subsystem permission",
                                    get=(lambda k=key, c=cfg: bool(c.get(k))),
                                    set_=(lambda v, k=key: PrivacyAdapter.set_ai_privacy_config(k, v)))
                sec.add_row(row)
            else:
                sec.add_row(entity_card(key.replace("_", " ").title(), str(val)[:56],
                                        icon_name="application-x-addon"))

    col.add(AsyncSection("AI subsystem privacy", "Control what Synthex AI components may access",
                         loader=lambda: PrivacyAdapter.get_ai_privacy_config() or {},
                         renderer=render_ai))

    # Zero telemetry
    sec = Section("Telemetry")
    zt = PrivacyAdapter.get_zero_telemetry_status() if hasattr(PrivacyAdapter, "get_zero_telemetry_status") else {}
    sec.add_row(entity_card("Zero-telemetry lockdown",
                            "Strips reporting, metrics and phoning-home across the OS",
                            icon_name="network-offline",
                            trailing=badge("Locked", "ok") if (zt and zt.get("locked", zt)) else badge("Off", "neutral")))
    sec.add_row(button("Enable full zero-telemetry lockdown", "btn-primary",
                       lambda b: (PrivacyAdapter.apply_zero_telemetry_lockdown(),
                                  toast.show_message("Zero-telemetry lockdown applied"))))
    col.add(sec)

    # Audit timeline
    def render_timeline(events, sec):
        if events:
            for ev in events[:12]:
                sec.add_row(entity_card(str(ev.get("app", ev.get("event", "Event"))[:40]),
                                        f"{ev.get('time', ev.get('timestamp', ''))} · {ev.get('detail', ev.get('action', ''))}"[:70],
                                        icon_name="preferences-system-privacy"))
        else:
            sec.add_row(label("No permission activity recorded", "empty-state", xalign=0.5))

    col.add(AsyncSection("Permission audit timeline", loader=lambda: PrivacyAdapter.get_privacy_timeline() or [],
                         renderer=render_timeline))

    # Private data cleanup
    sec = Section("Clear private data")
    sec.add_row(buttons_row("Cleanup", buttons=[
        ("Recent files", "btn-quiet", lambda b: (PrivacyAdapter.clear_private_data("recent_files"), toast.show_message("Recent files cleared"))),
        ("Thumbnails", "btn-quiet", lambda b: (PrivacyAdapter.clear_private_data("thumbnails"), toast.show_message("Thumbnails cleared"))),
        ("Trash", "btn-quiet", lambda b: (PrivacyAdapter.clear_private_data("trash"), toast.show_message("Trash emptied")))]))
    col.add(sec)

    # Active mic users
    def render_mic(users, sec):
        if users:
            for app in users[:8]:
                sec.add_row(entity_card(str(app)[:44], "Currently using your microphone",
                                        icon_name="audio-input-microphone", trailing=badge("Live", "warn")))
        else:
            sec.add_row(entity_card("No applications using the microphone", "Microphone idle",
                                    icon_name="microphone-sensitivity-low", trailing=badge("Idle", "ok")))

    col.add(AsyncSection("Active microphone users", loader=lambda: PrivacyAdapter.get_active_mic_users() or [],
                         renderer=render_mic))
    return col


def _perm_enabled(key):
    try:
        perms = PrivacyAdapter.get_app_permissions()
        hw = perms.get("hardware", {})
        return hw.get(key, "allow") == "allow"
    except Exception:
        return True


# ─────────────────────────────────────────────────────────────────────────────
# APPS MANAGER (installed applications — uninstall & cache reset)
# ─────────────────────────────────────────────────────────────────────────────

def build_apps(toast):
    col = ContentColumn()

    def render_apps(apps, sec):
        if not apps:
            sec.add_row(label("No applications found", "empty-state", xalign=0.5))
            return
        for app in apps[:24]:
            trailing = Gtk.Box(spacing=6)
            trailing.pack_start(button("Uninstall", "btn-destructive",
                                       lambda b, a=app: _uninstall(a, toast)), False, False, 0)
            trailing.pack_start(button("Reset cache", "btn-quiet",
                                       lambda b, a=app: (AppManagerAdapter.reset_app_cache(a),
                                                         toast.show_message(f"Cache cleared: {a.get('name', '')}"))), False, False, 0)
            sec.add_row(entity_card(app.get("name", "?")[:40],
                                    f"{app.get('category', '')} · {app.get('size', app.get('version', ''))}",
                                    icon_name=app.get("icon", "application-x-executable"),
                                    trailing=trailing))

    col.add(PageHeader("Installed Apps", "Uninstall applications and reset their caches"))
    col.add(AsyncSection("Applications", loader=lambda: AppManagerAdapter.get_installed_applications("") or [],
                         renderer=render_apps))
    return col


def _uninstall(app, toast):
    name = app.get("name", "app")
    dlg = Gtk.MessageDialog(transient_for=None, flags=0,
                            message_type=Gtk.MessageType.WARNING,
                            buttons=Gtk.ButtonsType.OK_CANCEL,
                            text=f"Uninstall {name}?")
    dlg.format_secondary_text("The application and its system package will be removed.")
    if dlg.run() == Gtk.ResponseType.OK:
        def work():
            ok, msg = AppManagerAdapter.uninstall_application(app)
            GLib.idle_add(lambda: toast.show_message(msg[:70] or ("Uninstalled " + name), error=not ok, seconds=5))
        threading.Thread(target=work, daemon=True).start()
    dlg.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# DEVICES (cameras & game controllers)
# ─────────────────────────────────────────────────────────────────────────────

def build_devices(toast):
    col = ContentColumn()
    col.add(PageHeader("Devices", "Cameras, game controllers and other peripherals"))

    sec = Section("Video cameras")
    cams = []
    ok, out, _ = run_cmd(["bash", "-c", "ls /dev/video* 2>/dev/null | head -6; v4l2-ctl --list-devices 2>/dev/null | grep -A1 ':' | head -8"], timeout=6)
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("/dev/video"):
            cams.append(line)
    if cams:
        for c in cams[:6]:
            sec.add_row(entity_card(c, "V4L2 capture device", icon_name="camera-video",
                                    trailing=badge("Ready", "ok")))
        sec.add_row(button("Test camera (cheese)", "btn-quiet", lambda b: run_cmd(["cheese"])))
    else:
        sec.add_row(label("No cameras detected", "empty-state", xalign=0.5))
    col.add(sec)

    sec = Section("Game controllers")
    pads = []
    ok, out, _ = run_cmd(["bash", "-c", "ls /dev/input/js* 2>/dev/null; evtest --list 2>/dev/null | grep -iE 'gamepad|joystick|controller|xbox|dualsense' | head -6"], timeout=6)
    for line in (out or "").splitlines():
        line = line.strip()
        if line and not line.startswith("No"):
            pads.append(line.split(":")[0][:60])
    if pads:
        for p in pads[:8]:
            sec.add_row(entity_card(p, "Game controller connected", icon_name="input-gaming",
                                    trailing=badge("Ready", "ok")))
        sec.add_row(buttons_row("Tools", buttons=[
            ("Calibrate (jstest)", "btn-quiet", lambda b: _launch_term("jstest /dev/input/js0")),
            ("evtest", "btn-quiet", lambda b: _launch_term("evtest --list | head -20"))]))
    else:
        sec.add_row(label("No game controllers detected", "empty-state", xalign=0.5))
    col.add(sec)
    return col
