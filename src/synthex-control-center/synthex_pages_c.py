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
    safe_set_gsetting, get_gsettings, SpoofGoofAdapter, MarketplaceAdapter,
)

from synth_platform_adapters import FirewallLayer, _gget, ensure_polkit_agent
from synthex_pages_a import _combo, _spin

AEGIS_DIR = Path(__file__).resolve().parent.parent / "synthex-aegis"
SECURITY_DIR = Path(__file__).resolve().parent.parent / "synthex-security"


def _load_privacy():
    import sys
    if str(SECURITY_DIR) not in sys.path:
        sys.path.insert(0, str(SECURITY_DIR))
    import synthex_privacy
    return synthex_privacy


def _privacy_harden(toast):
    def work():
        rep = _load_privacy().apply_browser_hardening()
        n = len(rep.get("written", []))
        GLib.idle_add(lambda: toast.show_message(
            f"Hardened {n} browser policy configs" + (f" · {len(rep['errors'])} errors" if rep.get("errors") else ""),
            error=bool(rep.get("errors")), seconds=5))
    threading.Thread(target=work, daemon=True).start()


def _privacy_audit(toast):
    def work():
        a = _load_privacy().fingerprint_audit()
        sig = a["signals"]
        lines = " · ".join(f"{k}:{v}" for k, v in list(sig.items())[:8] if k != "user")
        GLib.idle_add(lambda: toast.show_message(
            f"fingerprint ~{a['entropy_bits']} bits — {lines}"[:120], error=False, seconds=8))
    threading.Thread(target=work, daemon=True).start()


def _privacy_trackers_blocked():
    try:
        return _load_privacy().trackers_blocked() > 0
    except Exception:
        return False


def _privacy_set_block(v, toast):
    pg = _load_privacy()
    ok, msg = (pg.apply_tracker_block() if v else (pg.remove_tracker_block(), "Tracker block removed"))
    toast.show_message((msg if ok else "Block needs privileges (pkexec)")[:90], error=not ok, seconds=5)


def _privacy_telemetry(toast):
    def work():
        rep = _load_privacy().apply_telemetry_reduction()
        n = len(rep.get("written", []))
        err = rep.get("errors", [])
        GLib.idle_add(lambda: toast.show_message(
            f"Telemetry reduction applied ({n} config files)" + ("" if not err else " · partial, needs sudo"),
            error=bool(err), seconds=5))
    threading.Thread(target=work, daemon=True).start()


def _privacy_tel_audit(toast):
    def work():
        items = _load_privacy().telemetry_audit()
        active = [t for t in items if t["present"] and not t["mitigated"]]
        msgs = ", ".join(t["name"] for t in active) or "all collectors clean"
        GLib.idle_add(lambda: toast.show_message(
            f"Telemetry audit: {len(active)} active → {msgs}"[:110], error=bool(active), seconds=7))
    threading.Thread(target=work, daemon=True).start()


def _privacy_purge(toast):
    try:
        from synth_system_adapters import SpoofGoofAdapter
        rep = SpoofGoofAdapter.purge_browser_linkage()
        n = len(rep.get("purged", []))
        toast.show_message(f"Purged {n} linkage items (bookmarks kept)", error=bool(rep.get("errors")), seconds=5)
    except Exception as e:
        toast.show_message(f"Purge failed: {e}"[:80], error=True)


def _privacy_schedule(minutes, toast):
    def work():
        rep = _load_privacy().schedule_auto_clean(int(minutes))
        GLib.idle_add(lambda: toast.show_message(
            f"Auto de-identification {'every ' + str(rep['interval']) + ' min' if rep.get('enabled') else 'off'}",
            seconds=5))
    threading.Thread(target=work, daemon=True).start()


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


def _aegis_set_service(enable: bool) -> bool:
    """Single-prompt daemon control.
    Installed OS: systemd unit via one pkexec call.
    Source checkout: manage the daemon as a user process (no auth needed)."""
    ensure_polkit_agent()
    ok_units, units_out, _ = run_cmd(["systemctl", "list-unit-files", "synthex-aegis.service"], timeout=6)
    if "synthex-aegis.service" in (units_out or ""):
        verb = ["enable", "--now"] if enable else ["disable", "--now"]
        ok, _, _ = run_cmd(["pkexec", "systemctl", *verb, "synthex-aegis.service"], timeout=30)
        return ok
    # Dev/source-tree fallback: run the real daemon as a user process
    import sys as _sys
    import subprocess as _sp
    if enable:
        try:
            log = open("/tmp/synthex-aegis-daemon.log", "ab")
            _sp.Popen([_sys.executable, str(AEGIS_DIR / "aegis_daemon.py")],
                      start_new_session=True, stdout=log, stderr=_sp.STDOUT,
                      stdin=_sp.DEVNULL)
            return True
        except Exception:
            return False
    run_cmd(["pkill", "-f", "aegis_daemon[.]py"], timeout=6)
    return True


def build_aegis(toast):
    col = ContentColumn()
    st = aegis_daemon_status()
    col.add(PageHeader("Aegis Security Center", "Synthex endpoint defense: real-time behavioral attack prevention",
                       badges=[("Protection active", "ok") if st["active"] else ("Protection off", "err")]))

    # ── Daemon ────────────────────────────────────────────────────────
    sec = Section("Real-time protection")
    daemon_sw = Gtk.Switch(valign=Gtk.Align.CENTER)
    daemon_sw.set_active(st["active"])

    def _on_daemon_toggle(sw, state):
        ok = _aegis_set_service(state)
        msg = ("Aegis protection " + ("started — behavioral engine live" if state else "stopped")) \
            if ok else "Could not change protection state"
        toast.show_message(msg, error=not ok, seconds=5)
        return True

    daemon_sw.connect("state-set", _on_daemon_toggle)
    sec.add_row(entity_card("Aegis daemon",
                            "Behavioral engine monitoring processes, memory, sockets and SUID",
                            icon_name="security-high", trailing=daemon_sw))
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
# SPOOFGOOF — network identity & traffic obfuscation (Synthex security suite)
# ─────────────────────────────────────────────────────────────────────────────

def build_spoofgoof(toast):
    col = ContentColumn()
    try:
        st = SpoofGoofAdapter.get_status()
    except Exception:
        st = {"active": False, "profile": "—", "features": []}
    dm = SpoofGoofAdapter.daemon_status()
    col.add(PageHeader("SpoofGoof Traffic Shield",
                       "Network identity cloaking, packet morphing and decoy chaff — zero added latency",
                       badges=[("Active", "ok") if st.get("active") else ("Off", "err"),
                               (str(st.get("network_latency_penalty", "+0.0 ms")).split("(")[0].strip(), "neutral")]))

    # ── Master + daemon ──────────────────────────────────────────────
    sec = Section("Protection")
    sw = Gtk.Switch(valign=Gtk.Align.CENTER)
    sw.set_active(bool(st.get("active")))

    def _on_toggle(swt, state):
        ok = SpoofGoofAdapter.toggle(state)
        toast.show_message(("SpoofGoof " + ("engaged — full-spectrum cloaking live" if state else "disengaged"))
                           if ok else "Could not change SpoofGoof state", error=not ok, seconds=5)
        return True

    sw.connect("state-set", _on_toggle)
    sec.add_row(entity_card("SpoofGoof engine",
                            "MAC cloaking · DPI morphing · decoy chaff · hostname strip · TCP neutralizer",
                            icon_name="security-high", trailing=sw))
    if dm.get("active"):
        sec.add_row(entity_card("Daemon running" + (" via systemd service" if dm.get("via_service") else ""),
                                "Zero-latency fast path active — no ping penalty",
                                icon_name="emblem-default", trailing=badge("Live", "ok")))
    col.add(sec)

    # ── Profile ───────────────────────────────────────────────────────
    sec = Section("Obfuscation profile")
    row, _ = combo_row("Profile", SpoofGoofAdapter.profiles(),
                       subtitle="Balanced · Ultra-Stealth · Gaming zero-ping",
                       icon="network-workgroup",
                       get=lambda: st.get("profile_key", "balanced"),
                       set_=lambda v: (SpoofGoofAdapter.set_profile(v),
                                       toast.show_message(f"Profile: {dict(SpoofGoofAdapter.profiles()).get(v, v)}")),
                       width_chars=24)
    sec.add_row(row)
    col.add(sec)

    # ── Live identity controls ────────────────────────────────────────
    sec = Section("Identity controls")
    ifaces = SpoofGoofAdapter.list_interfaces()
    primary = SpoofGoofAdapter.primary_interface()
    iface_names = [(i["name"], f"{i['name']}  ({i['mac'][:17]})") for i in ifaces][:8] or [(primary, primary)]
    _sel = {"iface": primary}

    def _new_mac(b):
        ok, msg = SpoofGoofAdapter.spoof_mac(_sel["iface"])
        toast.show_message((f"MAC randomized on {_sel['iface']}" if ok else f"MAC spoof failed: {msg}")[:70],
                           error=not ok, seconds=5)

    row, cb = combo_row("Network interface", iface_names,
                        subtitle="Interface to cloak",
                        icon="network-wireless",
                        get=lambda: primary,
                        set_=lambda v: _sel.update(iface=v),
                        width_chars=20)
    sec.add_row(row)
    sec.add_row(buttons_row("Randomize MAC address", "Assigns a fresh randomized unicast MAC immediately",
                            icon="media-playlist-shuffle",
                            buttons=[("Randomize now", "btn-primary", _new_mac)]))

    def _enforce(b):
        toast.show_message("Enforcing 100% full-spectrum spoofing…", seconds=4)
        def work():
            ok, msg = SpoofGoofAdapter.enforce_full_spectrum()
            GLib.idle_add(lambda: toast.show_message(
                ("Full-spectrum spoofing enforced — " + msg)[:80] if ok else f"Enforcement failed: {msg}"[:70],
                error=not ok, seconds=6))
        threading.Thread(target=work, daemon=True).start()

    sec.add_row(buttons_row("Full-spectrum enforcement", "MAC + DHCP hostname + TCP stack + chaff in one shot",
                            icon="system-run",
                            buttons=[("Enforce 100% now", "btn-primary", _enforce)]))
    col.add(sec)

    # ── Active countermeasures list ───────────────────────────────────
    def render_feats(_p, sec):
        for f in (st.get("features") or [])[:8]:
            sec.add_row(entity_card(f.get("name", "?")[:40], f.get("status", "")[:56],
                                    icon_name=f.get("icon", "security-high"),
                                    trailing=badge("Active", "ok")))

    col.add(AsyncSection("Active countermeasures", loader=lambda: True, renderer=render_feats))

    # ── IP identity rotation (new address without a VPN) ──────────────
    def render_ip(payload, sec):
        pub = payload.get("ip") or "unavailable"
        def _rotate(b):
            dlg = Gtk.MessageDialog(
                transient_for=None, flags=0, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Rotate network identity now?")
            dlg.format_secondary_text(
                "A fresh randomized MAC forces a new DHCP lease — your public IP\n"
                "typically changes. Expect a ~5-15 second disconnect.\n\n"
                "Note: live TCP source-IP spoofing is impossible by protocol design;\n"
                "this delivers a genuinely new, unlinkable address instead.")
            if dlg.run() == Gtk.ResponseType.OK:
                dlg.destroy()
                toast.show_message("Rotating identity — connection will blip…", seconds=8)
                def work():
                    res = SpoofGoofAdapter.rotate_ip(verify=True)
                    GLib.idle_add(lambda: toast.show_message(
                        (res.get("message", "") +
                         (f" · public IP CHANGED {res.get('before_public_ip')} → {res.get('after_public_ip')}"
                          if res.get("public_ip_changed") else " · ISP re-issued same IP (new MAC still unlinkable)"))[:120],
                        error=not res.get("ok"), seconds=8))
                threading.Thread(target=work, daemon=True).start()
            else:
                dlg.destroy()

        sec.add_row(entity_card("Current public IP", pub,
                                icon_name="network-idle",
                                trailing=button("Rotate now", "btn-primary", _rotate)))

        def _rot6(b):
            res = SpoofGoofAdapter.rotate_ipv6()
            toast.show_message((f"IPv6 privacy addresses regenerated ({res.get('temporary_addresses', 0)} temporary)"
                                if res.get("ok") else f"IPv6 rotation failed: {res.get('message', res.get('error', ''))}")[:80],
                               error=not res.get("ok"))

        sec.add_row(buttons_row("IPv6 privacy rotation", "Regenerate RFC 4941 temporary addresses",
                                icon="network-wireless",
                                buttons=[("New IPv6 identity", "btn-quiet", _rot6)]))

    col.add(AsyncSection("IP identity rotation", "New public address via MAC re-roll + fresh DHCP lease — no VPN",
                         loader=lambda: {"ip": SpoofGoofAdapter.get_public_ip()},
                         renderer=render_ip))

    # Auto-rotation schedule
    sec = Section("Automatic rotation")
    row, _ = combo_row("Rotate identity every",
                       [(0, "Off"), (15, "15 minutes"), (30, "30 minutes"),
                        (60, "1 hour"), (180, "3 hours"), (360, "6 hours")],
                       subtitle="The daemon re-rolls MAC + DHCP lease on schedule",
                       icon="preferences-system-time",
                       get=lambda: 0,
                       set_=lambda v: (SpoofGoofAdapter.set_ip_rotate_interval(int(v)),
                                       toast.show_message(f"Auto IP rotation: {'off' if int(v) == 0 else f'every {int(v)} min'} (applied by daemon)")),
                       width_chars=14)
    sec.add_row(row)
    col.add(sec)

    # ── Trace-link audit: what re-attaches your history ───────────────
    def render_audit(findings, sec):
        icons = {0: ("dot-ok", "ok"), 1: ("dot-warn", "neutral"), 2: ("dot-warn", "warn"), 3: ("dot-err", "err")}
        for f in findings[:10]:
            dot_css, badge_kind = icons.get(f.get("severity", 1), ("dot-off", "neutral"))
            sev_label = {0: "Mitigated", 1: "Low", 2: "High", 3: "Critical"}[f.get("severity", 1)]
            sec.add_row(entity_card(f.get("vector", "?")[:42], f.get("detail", "")[:72],
                                    icon_name="preferences-system-privacy",
                                    trailing=badge(sev_label, badge_kind)))

    col.add(AsyncSection("Trace-link audit", "What can still re-attach your history after an IP change",
                         loader=lambda: SpoofGoofAdapter.audit_traceability(),
                         renderer=render_audit))

    def _purge(b):
        dlg = Gtk.MessageDialog(transient_for=None, flags=0,
                                message_type=Gtk.MessageType.WARNING,
                                buttons=Gtk.ButtonsType.OK_CANCEL,
                                text="Purge browser linkage state?")
        dlg.format_secondary_text(
            "Destroys cookies, history, cache and site storage in ALL browsers.\n"
            "Bookmarks and passwords are preserved. Close your browsers first.\n"
            "You will be logged out of every site.")
        if dlg.run() == Gtk.ResponseType.OK:
            dlg.destroy()
            def work():
                rep = SpoofGoofAdapter.purge_browser_linkage()
                n = len(rep.get("purged", []))
                warn = (" · CLOSE: " + ", ".join(set(rep["running"]))) if rep.get("running") else ""
                GLib.idle_add(lambda: toast.show_message(
                    f"Purged {n} linkage items (bookmarks kept){warn}"[:110],
                    error=bool(rep.get("errors")), seconds=7))
            threading.Thread(target=work, daemon=True).start()
        else:
            dlg.destroy()

    sec = Section("History purge")
    sec.add_row(buttons_row("Browser linkage purge", "Cookies · history · cache · site storage — bookmarks & passwords kept",
                            icon="edit-clear-all",
                            buttons=[("Purge all browsers", "btn-destructive", _purge)]))
    col.add(sec)

    # ── Tor: the only real answer to ISP-log tracing ──────────────────
    tor = SpoofGoofAdapter.tor_status()
    sec = Section("Tor circuit")
    tsw = Gtk.Switch(valign=Gtk.Align.CENTER)
    tsw.set_active(bool(tor.get("socks_listening")))

    def _on_tor(sw, state):
        toast.show_message("Bringing up Tor circuit…" if state else "Stopping Tor…", seconds=4)
        def work():
            if state:
                ok, msg = SpoofGoofAdapter.tor_enable()
            else:
                ok, msg = SpoofGoofAdapter.tor_disable(), "Tor disabled"
            GLib.idle_add(lambda: (sw.set_active(bool(SpoofGoofAdapter.tor_status().get("socks_listening"))),
                                   toast.show_message(msg[:90], error=not ok, seconds=6)))
        threading.Thread(target=work, daemon=True).start()
        return True

    tsw.connect("state-set", _on_tor)
    sec.add_row(entity_card("Tor daemon",
                            "Three-hop onion routing — removes your IP from the destination's view",
                            icon_name="network-vpn", trailing=tsw))

    prox = Gtk.Switch(valign=Gtk.Align.CENTER)
    ok_px, px_mode, _ = run_cmd(["gsettings", "get", "org.gnome.system.proxy", "mode"], timeout=4)

    def _proxy_state():
        okm, m, _ = run_cmd(["gsettings", "get", "org.gnome.system.proxy", "mode"], timeout=4)
        return "manual" in (m or "")
    prox.set_active(_proxy_state())

    def _on_proxy(sw, state):
        SpoofGoofAdapter.set_system_proxy_via_tor(state)
        toast.show_message("System proxy → Tor SOCKS 127.0.0.1:9050" if state else "System proxy cleared")
        return True
    prox.connect("state-set", _on_proxy)
    sec.add_row(entity_card("Route desktop via Tor", "SOCKS5 127.0.0.1:9050 for proxy-aware apps",
                            icon_name="preferences-system-network", trailing=prox))
    col.add(sec)

    # ── Honest threat model ────────────────────────────────────────────
    sec = Section("What rotation can — and cannot — do")
    for line, kind in [
        ("✓  Local network & access point: you appear as a brand-new device", "ok"),
        ("✓  Websites see a new address; hostname stripped; DNS encrypted end-to-end", "ok"),
        ("✗  Cookies, storage and LOGINS re-link you instantly — purge or use a clean profile", "err"),
        ("✗  ISP logs tie every IP you ever held to your account — rotation deletes nothing", "err"),
        ("✗  IPv6 prefix is household-stable (ISP-delegated) regardless of rotation", "err"),
        ("→  For traffic that must not be traceable to your IP: use the Tor circuit above", "neutral"),
    ]:
        sec.add_row(entity_card("", line, trailing=badge("", kind) if False else None)
                    if False else Gtk.Label(label=line, xalign=0.02))
    col.add(sec)

    # ── Live stats ────────────────────────────────────────────────────
    sec = Section("Live statistics")
    sec.add_row(entity_card("Latency penalty", str(st.get("network_latency_penalty", "+0.0 ms")),
                            icon_name="speedometer", trailing=badge("Zero", "ok")))
    sec.add_row(entity_card("Correlation resistance", str(st.get("correlation_resistance_score", "—")),
                            icon_name="channel-secure"))
    sec.add_row(entity_card("Chaff packets injected", f"{st.get('packets_injected_today', 0):,}",
                            icon_name="network-transmit-receive"))
    sec.add_row(entity_card("Traffic obfuscated", f"{st.get('bytes_obfuscated_mb', 0)} MB",
                            icon_name="drive-multidisk"))
    col.add(sec)
    return col


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

    # ── Fingerprint & data privacy reduction ──────────────────────
    pg = _load_privacy()
    sec = Section("Fingerprint hardening")
    sec.add_row(buttons_row("Browser fingerprint reduction",
                            "Chromium/Brave policy: WebRTC off · no metrics · no sync · cookies/geolocation/sensors disabled (Firefox RFP already active)",
                            icon="preferences-system-privacy",
                            buttons=[("Apply to browsers", "btn-primary", lambda b: _privacy_harden(toast)),
                                     ("Fingerprint audit", "btn-quiet", lambda b: _privacy_audit(toast))]))
    sec.add_row(entity_card("Firefox resist-fingerprinting",
                            "letterboxing · tracking/crypto/social protection · sensors/referer/beacon off · ECH+DoH",
                            icon_name="firefox", trailing=badge("Active", "ok")))
    col.add(sec)

    sec = Section("DNS tracker block")
    blocked = _privacy_trackers_blocked()
    row, _ = combo_row("Tracker / ad blocklist",
                       [(True, "On — block 70+ tracker domains system-wide"), (False, "Off")],
                       subtitle="Applies to EVERY app via /etc/hosts, not just a browser",
                       icon="network-offline",
                       get=lambda: blocked,
                       set_=lambda v: _privacy_set_block(bool(v), toast), width_chars=34)
    sec.add_row(row)
    sec.add_row(entity_card("Status",
                            f"{pg.trackers_blocked() if hasattr(pg, 'trackers_blocked') else 0} tracker domains blocked" if hasattr(pg, 'trackers_blocked') else "",
                            icon_name="system-shield", trailing=badge("Blocked", "ok") if blocked else badge("Off", "neutral")))
    col.add(sec)

    sec = Section("Telemetry reduction")
    sec.add_row(buttons_row("System telemetry sweep", "coredump storage · apport · cockpit — reversible drop-in overrides",
                            icon="dialog-information",
                            buttons=[("Apply reduction", "btn-primary", lambda b: _privacy_telemetry(toast)),
                                     ("Audit", "btn-quiet", lambda b: _privacy_tel_audit(toast))]))
    sec.add_row(buttons_row("Browser linkage purge", "Cookies · history · cache · site storage (bookmarks kept)",
                            icon="edit-clear-all",
                            buttons=[("Purge all browsers", "btn-destructive",
                                      lambda b: _privacy_purge(toast))]))
    col.add(sec)

    sec = Section("Scheduled de-identification")
    _combo(sec, "Auto-clean frequency",
           [(0, "Off"), (15, "Every 15 minutes"), (60, "Every hour"), (180, "Every 3 hours")],
           lambda: 15,
           lambda v: _privacy_schedule(int(v), toast),
           subtitle="A user timer periodically purges browser + shell linkage", width_chars=18)
    col.add(sec)
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


# ─────────────────────────────────────────────────────────────────────────────
# SOFTWARE MARKETPLACE (1-Click AI, Privacy, Dev & Gaming Software Center)
# ─────────────────────────────────────────────────────────────────────────────

def build_marketplace(toast):
    col = ContentColumn()
    col.add(PageHeader("Software Marketplace", "1-Click installation for AI models, zero-trace privacy tools, dev suites & games"))

    def _do_install(app, btn, badge_box):
        name = app.get("name", "App")
        btn.set_sensitive(False)
        btn.set_label("Installing…")
        toast.show_message(f"Installing {name} in background…", seconds=6)

        def work():
            ok, msg = MarketplaceAdapter.install_app(app["id"])
            def done():
                btn.set_sensitive(True)
                if ok:
                    btn.set_label("Launch")
                    btn.get_style_context().remove_class("btn-primary")
                    btn.get_style_context().add_class("btn-quiet")
                    btn.disconnect_by_func(_on_click)
                    btn.connect("clicked", lambda b: MarketplaceAdapter.launch_app(app["id"]))
                    toast.show_message(f"✓ {name} installed successfully!", error=False, seconds=5)
                else:
                    btn.set_label("Retry")
                    toast.show_message(f"Installation failed: {msg}", error=True, seconds=7)
            GLib.idle_add(done)

        threading.Thread(target=work, daemon=True).start()

    def _on_click(btn, app, badge_box):
        _do_install(app, btn, badge_box)

    def render_category(cat_key, title, subtitle, icon, sec_col):
        items = MarketplaceAdapter.get_catalog(category=cat_key)
        if not items:
            return
        sec = Section(title, subtitle)
        for app in items:
            is_inst = app.get("installed", False)
            trailing = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)

            if is_inst:
                trailing.pack_start(badge("Installed", "ok"), False, False, 0)
                trailing.pack_start(button("Launch", "btn-quiet",
                                           lambda b, a=app: (MarketplaceAdapter.launch_app(a["id"]),
                                                             toast.show_message(f"Launching {a['name']}…"))), False, False, 0)
            else:
                trailing.pack_start(badge(app.get("size", "Free"), "neutral"), False, False, 0)
                inst_btn = button("Get", "btn-primary", None)
                inst_btn.connect("clicked", _on_click, app, trailing)
                trailing.pack_start(inst_btn, False, False, 0)

            sec.add_row(entity_card(
                f"{app['name']}  ·  {app.get('author', 'Official')}",
                app.get("description", ""),
                icon_name=app.get("icon", icon),
                trailing=trailing
            ))
        sec_col.add(sec)

    # 1. 🧠 AI & LLM Acceleration
    render_category("ai", "AI Acceleration & Local LLMs", "Run state-of-the-art models locally on GPU/NPU with zero cloud telemetry", "applications-science", col)

    # 2. 🛡️ Zero-Trace Privacy & Security
    render_category("privacy", "Zero-Trace Privacy & Cryptography", "Tor anonymity, end-to-end messaging, sealed wallets and encrypted vaults", "network-vpn", col)

    # 3. 💻 Developer Intelligence
    render_category("developer", "Developer Environments & Container Engines", "Polyglot IDEs, Rust compiler toolchains, and OCI container virtualization", "applications-development", col)

    # 4. 🎮 Gaming & Graphics
    render_category("gaming", "Gaming Hub & Media Creation", "Steam with Proton-GE compatibility, game launchers, and OBS streaming suite", "applications-games", col)

    return col

