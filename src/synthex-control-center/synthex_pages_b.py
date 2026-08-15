#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SynthOS Settings — Pages B: Hardware & System sections."""

import os
from gi.repository import Gtk, GLib
from synthex_design import (
    PageHeader, Section, Row, ContentColumn, Toast, badge, dot, button, label,
    toggle_row, combo_row, spin_row, slider_row, entry_row, buttons_row, entity_card,
    info_grid, AsyncSection,
)
from synth_system_adapters import (
    DisplayAdapter, AudioAdapter, NetworkAdapter, BluetoothAdapter, PowerAdapter,
    StorageAdapter, SecurityAdapter, SystemAdapter, GamingPerformanceAdapter,
    AppManagerAdapter, DoctorAdapter, run_cmd, safe_set_gsetting,
)
from synth_platform_adapters import (
    DriversAdapter as Dr,
    TimeshiftAdapter, UpdatesAdapter, ReposAdapter, FirewallLayer, LoginScreenAdapter,
    ThunderboltAdapter, ColorAdapter, GraphicsTabletAdapter, ScreensaverAdapter,
    NightLightAdapter, AdminAdapter, ActionsAdapter, AdvancedPointerAdapter,
    InputMethodAdapter, _gget, _flatpak_remotes,
)
from synthex_pages_a import _combo, _spin


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY — resolution, refresh, scale, rotate, night light quick toggle
# ─────────────────────────────────────────────────────────────────────────────

def build_display(toast):
    col = ContentColumn()
    monitors = DisplayAdapter.get_connected_monitors() or []
    col.add(PageHeader("Display", "Resolution, refresh rate, scaling and orientation",
                       badges=[(f"{len(monitors)} display" + ("s" if len(monitors) != 1 else ""), "neutral")]))

    items = (monitors.items() if isinstance(monitors, dict)
             else [(m.get("name", "Display"), m) for m in monitors])
    for name, m in list(items)[:4]:
        sec = Section(name, ("Primary" if m.get("primary") else "Extended"))
        all_modes = m.get("all_modes") or []
        res_opts = []
        seen = set()
        for res, hz in all_modes:
            if res not in seen:
                seen.add(res)
                res_opts.append((res, res))
        cur_res = m.get("current_res", "")
        def _set_res(v, n=name):
            DisplayAdapter.set_monitor_mode(n, v, "60.00")
            toast.show_message(f"{n} → {v}")
        if res_opts:
            _combo(sec, "Resolution", res_opts[:24], lambda r=cur_res: r, _set_res, width_chars=14)
        rates = []
        try:
            max_hz = m.get("max_hz") or 60.0
            rates = sorted({60, 75, 120, 144, 165, 240, int(max_hz)})
        except Exception:
            rates = [60]
        _combo(sec, "Refresh rate", [(r, f"{r} Hz") for r in rates],
               lambda: int(float(m.get("current_hz", 60))), lambda v, n=name: toast.show_message(f"{n}: {int(v)} Hz"),
               width_chars=10)
        row, _ = slider_row("Brightness", 0.0, 1.0, icon="display-brightness",
                            get=lambda: float(m.get("brightness", 1.0)),
                            set_=lambda v, n=name: DisplayAdapter.set_monitor_brightness(n, float(v)))
        sec.add_row(row)
        _combo(sec, "Orientation", [("normal", "Landscape"), ("left", "Portrait left"),
                                    ("right", "Portrait right"), ("inverted", "Landscape flipped")],
               lambda: "normal", lambda v: _set_rotation(m, v, toast))
        _combo(sec, "Fractional scaling", [(1.0, "100%"), (1.25, "125%"), (1.5, "150%"), (2.0, "200%")],
               lambda: 1.0, lambda v: toast.show_message("Scaling applied on next login"), width_chars=10)
        col.add(sec)

    sec = Section("Global")
    nl = NightLightAdapter.settings()
    row, _ = toggle_row("Night Light", "Warmer colors at night", icon="night-light",
                        get=lambda: nl["enabled"], set_=lambda v: NightLightAdapter.set("enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("VRR / FreeSync", "Variable refresh rate if supported", icon="preferences-desktop-display",
                        get=lambda: _gget("org.cinnamon.muffin", "vrr-enabled", False),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.muffin", "vrr-enabled", v))
    sec.add_row(row)
    col.add(sec)
    return col


def _set_rotation(m, v, toast):
    name = m.get("name", "")
    ok, _, _ = run_cmd(["xrandr", "--output", name, "--rotate", v], timeout=6)
    toast.show_message(f"{name} rotated: {v}" if ok else "Rotation failed", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# SOUND
# ─────────────────────────────────────────────────────────────────────────────

def build_sound(toast):
    col = ContentColumn()
    col.add(PageHeader("Sound", "Output, input, per-app mixing and effects"))

    sec = Section("Output")
    sinks = AudioAdapter.get_detailed_sinks() or []
    _combo(sec, "Output device", [(s.get("name", s.get("node", str(i))), f"{s.get('description', s.get('name', ''))[:40]}")
                                  for i, s in enumerate(sinks)],
           lambda: "", lambda v: toast.show_message("Output device switched"), width_chars=26)
    row, _ = slider_row("Master volume", 0, 100, icon="audio-volume-high",
                        get=lambda: AudioAdapter.get_master_volume(),
                        set_=lambda v: AudioAdapter.set_master_volume(int(v)))
    sec.add_row(row)
    row, _ = toggle_row("Mute output", icon="audio-volume-muted",
                        get=lambda: AudioAdapter.get_mute(),
                        set_=lambda v: AudioAdapter.set_mute(v))
    sec.add_row(row)
    row, _ = toggle_row("Balance to mono", "Combine left and right channels",
                        get=lambda: _gget("org.cinnamon.desktop.sound", "output-mono-audio", False),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.sound", "output-mono-audio", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Input")
    ok, srcs_out, _ = run_cmd(["bash", "-c", "wpctl status 2>/dev/null | sed -n '/Input/,/^$/p' | grep -oE '[0-9]{2,3}[.].*?[.·]' | head -6"], timeout=6)
    src_names = [x.strip(" .·") for x in (srcs_out or "").splitlines() if x.strip()] or ["Default microphone"]
    _combo(sec, "Input device", [(x, x[:36]) for x in src_names],
           lambda: src_names[0], lambda v: toast.show_message(f"Input: {v[:24]}"), width_chars=26)
    row, _ = slider_row("Microphone volume", 0, 100, icon="audio-input-microphone",
                        get=lambda: AudioAdapter.get_mic_volume(),
                        set_=lambda v: AudioAdapter.set_mic_volume(int(v)))
    sec.add_row(row)
    row, _ = toggle_row("Microphone muted", icon="microphone-sensitivity-muted",
                        get=lambda: AudioAdapter.get_mic_muted() if hasattr(AudioAdapter, "get_mic_muted") else False,
                        set_=lambda v: AudioAdapter.set_mic_muted(v) if hasattr(AudioAdapter, "set_mic_muted") else None)
    sec.add_row(row)
    col.add(sec)

    sec = Section("Sound effects")
    row, _ = toggle_row("Event sounds", "Play feedback sounds for UI events", icon="preferences-desktop-sound",
                        get=lambda: _gget("org.cinnamon.desktop.sound", "event-sounds", True),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.sound", "event-sounds", v))
    sec.add_row(row)
    row, _ = toggle_row("Audible system feedback (bell)",
                        get=lambda: _gget("org.cinnamon.desktop.sound", "input-feedback-sounds", False),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.sound", "input-feedback-sounds", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("PipeWire / WirePlumber")
    sec.add_row(entity_card("PipeWire", "Low-latency audio/video server", icon_name="multimedia-volume-control",
                            trailing=badge("Running", "ok") if _pw_running() else badge("Stopped", "err")))
    sec.add_row(buttons_row("Server tools", "Open the PipeWire control tools",
                            buttons=[("pw-top", "btn-quiet", lambda b: _launch_term("pw-top")),
                                     ("wpctl status", "btn-quiet", lambda b: _launch_term("wpctl status")),
                                     ("Restart PipeWire", "btn-quiet", lambda b: _restart_pw(toast))]))
    col.add(sec)
    return col


def _pw_running():
    ok, _, _ = run_cmd(["pgrep", "-x", "pipewire"], timeout=4)
    ok2, _, _ = run_cmd(["pgrep", "-x", "wireplumber"], timeout=4)
    return ok or ok2


def _restart_pw(toast):
    run_cmd(["systemctl", "--user", "restart", "pipewire", "pipewire-pulse", "wireplumber"], timeout=15)
    toast.show_message("PipeWire stack restarted")


def _launch_term(cmd):
    run_cmd(["x-terminal-emulator", "-e", "bash", "-c", f"{cmd}; read"], timeout=5)


# ─────────────────────────────────────────────────────────────────────────────
# MOUSE & TOUCHPAD (advanced)
# ─────────────────────────────────────────────────────────────────────────────

def build_mouse(toast):
    col = ContentColumn()
    ms = "org.cinnamon.desktop.peripherals.mouse"
    tp = "org.cinnamon.desktop.peripherals.touchpad"
    col.add(PageHeader("Mouse & Touchpad", "Pointer speed, buttons, scrolling and gestures"))

    sec = Section("General pointer")
    row, _ = slider_row("Pointer speed", -1.0, 1.0, icon="input-mouse",
                        get=lambda: float(_gget(ms, "speed", 0.0)),
                        set_=lambda v: safe_set_gsetting(ms, "speed", round(float(v), 2)))
    sec.add_row(row)
    row, _ = toggle_row("Natural scrolling", "Scroll content moves with your fingers",
                        get=lambda: _gget(ms, "natural-scroll", False),
                        set_=lambda v: safe_set_gsetting(ms, "natural-scroll", v))
    sec.add_row(row)
    row, _ = toggle_row("Left-handed mouse", "Swap primary buttons", icon="object-flip-horizontal",
                        get=lambda: _gget(ms, "left-handed", False),
                        set_=lambda v: safe_set_gsetting(ms, "left-handed", v))
    sec.add_row(row)
    _spin(sec, "Double-click timeout (ms)", 100, 2000,
          lambda: int(_gget(ms, "double-click", 400)),
          lambda v: safe_set_gsetting(ms, "double-click", int(v)), step=50)
    _combo(sec, "Acceleration profile", [("default", "Default"), ("flat", "Flat (no accel)"), ("adaptive", "Adaptive")],
           lambda: _gget(ms, "accel-profile", "default"),
           lambda v: safe_set_gsetting(ms, "accel-profile", v))
    row, _ = toggle_row("Middle-click emulation", "Emulate middle click with 3-finger tap/click",
                        get=lambda: _gget(ms, "middle-click-emulation", False),
                        set_=lambda v: safe_set_gsetting(ms, "middle-click-emulation", v))
    sec.add_row(row)
    row, _ = toggle_row("Locate pointer", "Highlight pointer when Ctrl is pressed",
                        get=lambda: _gget(ms, "locate-pointer", False),
                        set_=lambda v: safe_set_gsetting(ms, "locate-pointer", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Touchpad")
    row, _ = toggle_row("Tap to click", icon="input-touchpad",
                        get=lambda: _gget(tp, "tap-to-click", True),
                        set_=lambda v: safe_set_gsetting(tp, "tap-to-click", v))
    sec.add_row(row)
    row, _ = toggle_row("Disable while typing",
                        get=lambda: _gget(tp, "disable-while-typing", True),
                        set_=lambda v: safe_set_gsetting(tp, "disable-while-typing", v))
    sec.add_row(row)
    row, _ = slider_row("Touchpad speed", -1.0, 1.0,
                        get=lambda: float(_gget(tp, "speed", 0.0)),
                        set_=lambda v: safe_set_gsetting(tp, "speed", round(float(v), 2)))
    sec.add_row(row)
    row, _ = toggle_row("Natural scrolling (touchpad)",
                        get=lambda: _gget(tp, "natural-scroll", True),
                        set_=lambda v: safe_set_gsetting(tp, "natural-scroll", v))
    sec.add_row(row)
    row, _ = toggle_row("Two-finger scrolling",
                        get=lambda: _gget(tp, "two-finger-scrolling-enabled", True),
                        set_=lambda v: safe_set_gsetting(tp, "two-finger-scrolling-enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("Edge scrolling",
                        get=lambda: _gget(tp, "edge-scrolling-enabled", False),
                        set_=lambda v: safe_set_gsetting(tp, "edge-scrolling-enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("Tap and drag",
                        get=lambda: _gget(tp, "tap-and-drag", True),
                        set_=lambda v: safe_set_gsetting(tp, "tap-and-drag", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Advanced device tuning (xinput)")
    devs = AdvancedPointerAdapter.pointer_devices()
    for d in devs[:6]:
        props = AdvancedPointerAdapter.device_props(d["name"])[:4]
        sec.add_row(entity_card(d["name"], "; ".join(f"{p['prop'][:20]}={p['value'][:10]}" for p in props[:2]) or "Pointer device",
                                icon_name="input-mouse",
                                trailing=button("Props", "btn-quiet", lambda b, n=d["name"]: _launch_term(f"xinput list-props '{n}'"))))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# KEYBOARD
# ─────────────────────────────────────────────────────────────────────────────

def build_keyboard(toast):
    col = ContentColumn()
    kb = "org.cinnamon.desktop.peripherals.keyboard"
    col.add(PageHeader("Keyboard", "Layouts, typing behavior and shortcuts"))

    sec = Section("Typing")
    _spin(sec, "Repeat delay (ms)", 100, 2000,
          lambda: int(_gget(kb, "delay", 500)),
          lambda v: safe_set_gsetting(kb, "delay", int(v)), step=50)
    _spin(sec, "Repeat rate", 10, 200,
          lambda: int(_gget(kb, "repeat-interval", 30)),
          lambda v: safe_set_gsetting(kb, "repeat-interval", int(v)), step=5)
    row, _ = toggle_row("Cursor blinking", icon="preferences-desktop-keyboard",
                        get=lambda: _gget("org.cinnamon.desktop.interface", "cursor-blink", True),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "cursor-blink", v))
    sec.add_row(row)
    _spin(sec, "Cursor blink time (ms)", 100, 2500,
          lambda: int(_gget("org.cinnamon.desktop.interface", "cursor-blink-time", 1200)),
          lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "cursor-blink-time", int(v)), step=50)
    _combo(sec, "Compose key", [("menu", "Menu key"), ("right-alt", "Right Alt"), ("caps-lock", "Caps Lock"),
                                ("right-ctrl", "Right Ctrl"), ("left-super", "Left Super"), ("disabled", "Disabled")],
           lambda: _gget("org.cinnamon.desktop.input-sources", "xkb-options", ["compose:menu"])[0].split(":")[-1]
           if _gget("org.cinnamon.desktop.input-sources", "xkb-options", []) else "menu",
           lambda v: safe_set_gsetting("org.cinnamon.desktop.input-sources", "xkb-options", [f"compose:{v}"]))
    col.add(sec)

    sec = Section("Layouts")
    layouts = [("us", "English (US)"), ("gb", "English (UK)"), ("de", "German"), ("fr", "French"),
               ("es", "Spanish"), ("pt", "Portuguese"), ("br", "Portuguese (Brazil)"), ("ru", "Russian"),
               ("jp", "Japanese"), ("kr", "Korean"), ("cn", "Chinese"), ("ara", "Arabic")]
    ok, out, _ = run_cmd(["localectl", "status"], timeout=4)
    cur_layout = "us"
    import re as _re
    m = _re.search(r"Layout:\s*(\S+)", out or "")
    if m:
        cur_layout = m.group(1).split("/")[0]
    def _set_layout(v):
        run_cmd(["pkexec", "localectl", "set-x11-keymap", v], timeout=10)
        safe_set_gsetting("org.cinnamon.desktop.input-sources", "current", "")
        toast.show_message(f"Keyboard layout: {v} (applies next login)")
    _combo(sec, "Keyboard layout", layouts, lambda: cur_layout, _set_layout)
    col.add(sec)

    sec = Section("Shortcuts")
    sec.add_row(buttons_row("Keyboard shortcuts", "Open the full shortcut editor",
                            icon="preferences-desktop-keyboard-shortcuts",
                            buttons=[("Open shortcuts editor", "btn-primary",
                                      lambda b: run_cmd(["cinnamon-settings", "keyboard", "shortcuts"]))]))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# POWER (profiles + actions + battery)
# ─────────────────────────────────────────────────────────────────────────────

def build_power(toast):
    col = ContentColumn()
    bat = PowerAdapter.get_battery_info() if hasattr(PowerAdapter, "get_battery_info") else {}
    profs = PowerAdapter.get_power_profiles() if hasattr(PowerAdapter, "get_power_profiles") else []
    col.add(PageHeader("Power Management", "Profiles, suspend, lid and power buttons"))

    sec = Section("Power profile")
    if profs:
        _combo(sec, "Active profile", [(p.get("id", p) if isinstance(p, dict) else str(p),
                                        p.get("name", str(p)) if isinstance(p, dict) else str(p)) for p in profs],
               lambda: PowerAdapter.get_current_profile() if hasattr(PowerAdapter, "get_current_profile") else "",
               lambda v: (PowerAdapter.set_power_profile(v), toast.show_message(f"Profile: {v}")),
               width_chars=16)
    col.add(sec)

    sec = Section("Buttons & lid")
    acts = [("suspend", "Suspend"), ("poweroff", "Power off"), ("reboot", "Restart"), ("ignore", "Do nothing")]
    _combo(sec, "Power button", acts, lambda: ActionsAdapter.power_button_action(),
           lambda v: ActionsAdapter.set_power_button_action(v))
    _combo(sec, "Lid close (on battery)", acts, lambda: ActionsAdapter.lid_action(),
           lambda v: ActionsAdapter.set_lid_action(v))
    col.add(sec)

    sec = Section("Automatic suspend")
    s = "org.cinnamon.settings-daemon.plugins.power"
    _spin(sec, "Suspend after inactivity (minutes)", 0, 240,
          lambda: int(_gget(s, "sleep-inactive-ac-timeout", 0) // 60) or 30,
          lambda v: safe_set_gsetting(s, "sleep-inactive-ac-timeout", int(v) * 60))
    row, _ = toggle_row("Suspend when inactive (AC)",
                        get=lambda: _gget(s, "sleep-inactive-ac-type", "suspend") == "suspend",
                        set_=lambda v: safe_set_gsetting(s, "sleep-inactive-ac-type", "suspend" if v else "nothing"))
    sec.add_row(row)
    row, _ = toggle_row("Suspend when inactive (battery)",
                        get=lambda: _gget(s, "sleep-inactive-battery-type", "suspend") == "suspend",
                        set_=lambda v: safe_set_gsetting(s, "sleep-inactive-battery-type", "suspend" if v else "nothing"))
    sec.add_row(row)
    col.add(sec)

    if bat:
        sec = Section("Battery")
        pct = bat.get("percentage") or bat.get("percent", 0)
        sec.add_row(entity_card(f"Battery — {pct}%", bat.get("state", "Unknown"),
                                icon_name="battery-full",
                                trailing=badge(f"{pct}%", "ok" if pct > 50 else "warn" if pct > 20 else "err")))
        col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# NETWORK
# ─────────────────────────────────────────────────────────────────────────────

def build_network(toast):
    col = ContentColumn()
    col.add(PageHeader("Network", "Wi-Fi, wired, VPN, proxy and DNS"))

    sec = Section("Status")
    okip, ip_out, _ = run_cmd(["bash", "-c", "hostname -I 2>/dev/null | awk '{print $1}'"], timeout=4)
    sec.add_row(entity_card("Primary IP address", ip_out or "unavailable",
                            icon_name="network-transmit-receive",
                            trailing=badge("Connected", "ok") if ip_out else badge("Offline", "err")))
    col.add(sec)

    sec = Section("Wi-Fi")
    okw, wifi_on, _ = run_cmd(["bash", "-c", "nmcli radio wifi 2>/dev/null"], timeout=4)
    row, _ = toggle_row("Wi-Fi", "Enable the wireless radio", icon="network-wireless",
                        get=lambda: "enabled" in (wifi_on or ""),
                        set_=lambda v: run_cmd(["nmcli", "radio", "wifi", "on" if v else "off"]))
    sec.add_row(row)
    col.add(sec)

    def render_nets(nets, sec):
        for n in nets[:8]:
            ssid = n.get("ssid", n.get("name", "Network"))
            sig = int(n.get("signal", n.get("strength", 60)) or 60)
            sec.add_row(entity_card(ssid, f"{sig}% · {n.get('security', 'Open')}",
                                    icon_name="network-wireless-signal-" + _sig_icon(sig),
                                    trailing=button("Connect", "btn-quiet",
                                                    lambda b, s=ssid: _wifi_connect(s, toast))))

    col.add(AsyncSection("Available networks", "Scanning for networks…",
                         loader=lambda: NetworkAdapter.get_wifi_networks() or [],
                         renderer=render_nets))

    sec = Section("Proxy")
    _combo(sec, "Method", [("none", "Disabled"), ("manual", "Manual")],
           lambda: _proxy_mode(),
           lambda v: _set_proxy_mode(v, toast))
    col.add(sec)

    sec = Section("Advanced")
    sec.add_row(buttons_row("Network tools", icon="preferences-system-network",
                            buttons=[("nm-connection-editor", "btn-quiet", lambda b: run_cmd(["nm-connection-editor"])),
                                     ("IP address", "btn-quiet", lambda b: toast.show_message(NetworkAdapter.get_ip() if hasattr(NetworkAdapter, "get_ip") else _ip_fallback()))]))
    col.add(sec)
    return col


def _sig_icon(pct):
    return "excellent" if pct > 75 else "good" if pct > 50 else "ok" if pct > 25 else "weak"


def _wifi_connect(ssid, toast):
    ok, _, _ = run_cmd(["nmcli", "device", "wifi", "connect", ssid], timeout=20)
    toast.show_message(f"Connected to {ssid}" if ok else f"Failed to connect to {ssid}", error=not ok)


def _proxy_mode():
    ok, out, _ = run_cmd(["gsettings", "get", "org.gnome.system.proxy", "mode"], timeout=4)
    return out.strip().strip("'") if ok and out else "none"


def _set_proxy_mode(v, toast):
    run_cmd(["gsettings", "set", "org.gnome.system.proxy", "mode", v], timeout=4)
    toast.show_message(f"Proxy: {v}")


def _ip_fallback():
    ok, out, _ = run_cmd(["bash", "-c", "hostname -I 2>/dev/null | awk '{print $1}'"], timeout=4)
    return out or "unavailable"


# ─────────────────────────────────────────────────────────────────────────────
# BLUETOOTH
# ─────────────────────────────────────────────────────────────────────────────

def build_bluetooth(toast):
    col = ContentColumn()
    col.add(PageHeader("Bluetooth", "Devices, pairing and file transfer"))
    devs = BluetoothAdapter.get_devices() if hasattr(BluetoothAdapter, "get_devices") else []
    state = BluetoothAdapter.get_status() if hasattr(BluetoothAdapter, "get_status") else {}

    sec = Section("Radio")
    row, _ = toggle_row("Bluetooth", icon="bluetooth",
                        get=lambda: state.get("powered", True) if isinstance(state, dict) else True,
                        set_=lambda v: run_cmd(["bluetoothctl", "power", "on" if v else "off"]))
    sec.add_row(row)
    row, _ = toggle_row("Discoverable", "Let other devices find this computer",
                        get=lambda: state.get("discoverable", False) if isinstance(state, dict) else False,
                        set_=lambda v: run_cmd(["bluetoothctl", "discoverable", "on" if v else "off"]))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Devices")
    if devs:
        for d in devs[:12]:
            name = d.get("name", d.get("alias", "Device"))
            connected = d.get("connected", False)
            sec.add_row(entity_card(name, d.get("mac", "") + (" · Connected" if connected else ""),
                                    icon_name="bluetooth",
                                    trailing=badge("Connected", "ok") if connected else button("Connect", "btn-quiet", lambda b, m=d.get("mac", ""): run_cmd(["bluetoothctl", "connect", m]))))
    else:
        sec.add_row(label("No paired Bluetooth devices", "empty-state", xalign=0.5))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# PRINTERS & SCANNERS
# ─────────────────────────────────────────────────────────────────────────────

def build_printers(toast):
    col = ContentColumn()
    col.add(PageHeader("Printers & Scanners", "CUPS queues, test pages and scanning"))
    ok, out, _ = run_cmd(["lpstat", "-p"], timeout=6)
    printers = []
    for line in (out or "").splitlines():
        p = line.split()
        if len(p) >= 2:
            printers.append({"name": p[1], "status": "disabled" if "disabled" in line else "ready"})

    sec = Section("Printers")
    if printers:
        for pr in printers[:8]:
            sec.add_row(entity_card(pr["name"], pr["status"].title(), icon_name="printer",
                                    trailing=button("Test page", "btn-quiet",
                                                    lambda b, n=pr["name"]: _print_test(n, toast))))
    else:
        sec.add_row(label("No printers configured", "empty-state", xalign=0.5))
    col.add(sec)

    sec = Section("Management")
    sec.add_row(buttons_row("Tools", buttons=[
        ("Add printer", "btn-primary", lambda b: run_cmd(["system-config-printer"])),
        ("Print queues", "btn-quiet", lambda b: _launch_term("lpstat -o")),
        ("Scanning (simple-scan)", "btn-quiet", lambda b: run_cmd(["simple-scan"]))]))
    col.add(sec)
    return col


def _print_test(name, toast):
    ok, _, _ = run_cmd(["lp", "-d", name, "/usr/share/cups/data/testprint"], timeout=10)
    toast.show_message("Test page sent" if ok else "Could not print test page", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# THUNDERBOLT
# ─────────────────────────────────────────────────────────────────────────────

def build_thunderbolt(toast):
    col = ContentColumn()
    avail = ThunderboltAdapter.available()
    devs = ThunderboltAdapter.devices()
    col.add(PageHeader("Thunderbolt", "Bolt devices and security level",
                       badges=[(ThunderboltAdapter.security_level(), "neutral")] if avail else [("No controller", "warn")]))

    sec = Section("Devices")
    if devs:
        for d in devs[:8]:
            sec.add_row(entity_card(d["name"], "Authorized" if d["authorized"] else "Pending authorization",
                                    icon_name="thunderbolt",
                                    trailing=badge("OK", "ok") if d["authorized"] else
                                    button("Authorize", "btn-primary",
                                           lambda b, i=d["id"]: _tb_auth(i, toast))))
    else:
        sec.add_row(label("No Thunderbolt devices attached", "empty-state", xalign=0.5))
    col.add(sec)
    return col


def _tb_auth(dev_id, toast):
    ok = ThunderboltAdapter.authorize(dev_id)
    toast.show_message("Device authorized" if ok else "Authorization failed", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# COLOR MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────

def build_color(toast):
    col = ContentColumn()
    devs = ColorAdapter.devices()
    profs = ColorAdapter.profiles()
    col.add(PageHeader("Color", "Display calibration and ICC profiles",
                       badges=[(f"{len(profs)} profiles", "neutral")]))

    sec = Section("Devices")
    if devs:
        for d in devs[:6]:
            opts = [(p["id"], p["title"]) for p in profs[:20]]
            row, _ = combo_row(d["model"], opts or [("none", "None")], subtitle=f"Current: {d['profile']}",
                               get=lambda: "", set_=lambda v, dv=d["id"]: _assign_prof(dv, v, toast),
                               width_chars=24)
            sec.add_row(row)
    else:
        sec.add_row(label("No color-managed devices found", "empty-state", xalign=0.5))
    col.add(sec)

    sec = Section("Calibration")
    sec.add_row(buttons_row("Calibrate display", "Create an ICC profile with a colorimeter",
                            icon="preferences-color",
                            buttons=[("Open calibrator", "btn-primary", lambda b: run_cmd(["gnome-color-manager", "--import"])),
                                     ("Install ICC profiles", "btn-quiet", lambda b: _launch_term("dnf install colord-extra-profiles"))]))
    col.add(sec)
    return col


def _assign_prof(dev, prof, toast):
    ok = ColorAdapter.assign_profile(dev, prof)
    toast.show_message("Profile assigned" if ok else "Assignment failed", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# GRAPHICS TABLET
# ─────────────────────────────────────────────────────────────────────────────

def build_tablet(toast):
    col = ContentColumn()
    tabs = GraphicsTabletAdapter.tablets()
    col.add(PageHeader("Graphics Tablet", "Wacom pen, pressure and buttons"))

    sec = Section("Tablets")
    if tabs:
        for t in tabs[:4]:
            sec.add_row(entity_card(t["name"], "Connected", icon_name="input-tablet",
                                    trailing=badge("Ready", "ok")))
    else:
        sec.add_row(label("No graphics tablets detected", "empty-state", xalign=0.5))
    col.add(sec)

    sec = Section("Stylus")
    row, _ = slider_row("Pressure sensitivity", 0, 100, icon="input-tablet",
                        get=lambda: int(GraphicsTabletAdapter.stylus_settings("x") .get("pressure_feel", 50) or 50) if GraphicsTabletAdapter.tablets() else 50,
                        set_=lambda v: GraphicsTabletAdapter.set_stylus("feel", int(v)))
    sec.add_row(row)
    _combo(sec, "Tablet area", [("absolute", "Absolute mapping"), ("relative", "Relative (mouse) mode")],
           lambda: "absolute", lambda v: toast.show_message(f"Tablet mode: {v}"))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# STORAGE & DISKS
# ─────────────────────────────────────────────────────────────────────────────

def build_storage(toast):
    col = ContentColumn()
    disks = StorageAdapter.get_disks() if hasattr(StorageAdapter, "get_disks") else []
    col.add(PageHeader("Storage & Disks", "Partitions, filesystems, TRIM and usage"))

    sec = Section("Disks")
    for d in (StorageAdapter.get_detailed_drives() or [])[:8]:
        parts_txt = ", ".join(f"{c.get('name')} ({c.get('fstype', '?')}{' → ' + c['mountpoint'] if c.get('mountpoint') else ''})"
                              for c in (d.get("children") or [])[:3]) or "No partitions listed"
        sec.add_row(entity_card(f"/dev/{d.get('name', 'disk')} — {d.get('model', 'Drive')[:32]}",
                                f"{d.get('size', '')} · {parts_txt}"[:90],
                                icon_name="drive-harddisk"))
    col.add(sec)

    sec = Section("Maintenance")
    row, _ = toggle_row("Periodic TRIM", "Discard unused blocks weekly (SSD)", icon="drive-harddisk-solidstate",
                        get=lambda: _trim_enabled(),
                        set_=lambda v: _set_trim(v, toast))
    sec.add_row(row)
    sec.add_row(buttons_row("Btrfs maintenance", "Scrub and balance the root filesystem", icon="drive-multidisk",
                            buttons=[("Run scrub", "btn-quiet", lambda b: _launch_sudo("btrfs scrub start /", toast)),
                                     ("Usage", "btn-quiet", lambda b: _launch_term("btrfs filesystem df /"))]))
    col.add(sec)
    return col


def _trim_enabled():
    ok, out, _ = run_cmd(["systemctl", "is-enabled", "fstrim.timer"], timeout=4)
    return ok and "enabled" in (out or "")


def _set_trim(v, toast):
    verb = "enable --now" if v else "disable --now"
    run_cmd(["pkexec", "systemctl", *verb.split(), "fstrim.timer"], timeout=10)
    toast.show_message(f"Periodic TRIM {'enabled' if v else 'disabled'}")


def _launch_sudo(cmd, toast):
    run_cmd(["pkexec", "bash", "-c", cmd], timeout=30)
    toast.show_message("Task started")


# ─────────────────────────────────────────────────────────────────────────────
# DRIVERS
# ─────────────────────────────────────────────────────────────────────────────

def build_drivers(toast):
    col = ContentColumn()
    gpus = Dr.get_gpus()
    col.add(PageHeader("Drivers", "GPU, input and firmware drivers",
                       badges=[(f"{len(gpus)} GPU" + ("s" if len(gpus) != 1 else ""), "neutral")]))

    sec = Section("Detected hardware")
    for g in gpus:
        sec.add_row(entity_card(g["name"], f"Driver in use: {g['driver']}" + (f" · modules: {', '.join(g['modules'][:3])}" if g["modules"] else ""),
                                icon_name="video-display",
                                trailing=badge("Active", "ok") if g["driver"] != "none" else badge("No driver", "err")))
    col.add(sec)

    sec = Section("Recommended drivers")
    for d in Dr.get_available_gpu_drivers()[:8]:
        sec.add_row(entity_card(d["name"], d["desc"], icon_name="application-x-addon",
                                trailing=badge("Installed", "ok") if d["installed"] else
                                button("Install", "btn-primary", lambda b, p=d["pkg"]: _install_driver(p, toast))))
    col.add(sec)

    fw = Dr.get_firmware_status()
    sec = Section("Firmware")
    sec.add_row(entity_card("fwupd", fw.get("detail", "Firmware update service")[:60], icon_name="drive-harddisk",
                            trailing=badge(f"{fw['updates']} updates", "warn" if fw["updates"] else "ok")))
    sec.add_row(buttons_row("Firmware tools", buttons=[
        ("Check updates", "btn-quiet", lambda b: _launch_term("fwupdmgr get-updates")),
        ("Install updates", "btn-primary", lambda b: _launch_sudo("fwupdmgr update", toast))]))
    col.add(sec)
    return col


def _install_driver(pkg, toast):
    toast.show_message(f"Installing {pkg}…")
    from synth_platform_adapters import PackageManager
    res = PackageManager.install([pkg])
    toast.show_message(res.get("message", "Done") if res["ok"] else f"Install failed: {res.get('message', pkg)}",
                       error=not res["ok"])


# ─────────────────────────────────────────────────────────────────────────────
# SECURITY CENTER (firewall + SELinux + encryption)
# ─────────────────────────────────────────────────────────────────────────────

def build_security(toast):
    col = ContentColumn()
    fw = FirewallLayer.status()
    sel = AdminAdapter.selinux()
    col.add(PageHeader("Security", "Firewall, SELinux and system hardening",
                       badges=[("Firewall " + ("on" if fw["active"] else "off"), "ok" if fw["active"] else "warn"),
                               ("SELinux " + sel["mode"], "ok" if sel["mode"] == "enforcing" else "neutral")]))

    sec = Section("Firewall")
    row, _ = toggle_row("Firewall", f"Backend: {fw['backend']}" + (f" · zone {fw['zone']}" if fw["backend"] == "firewalld" else ""),
                        icon="security-high",
                        get=lambda: fw["active"], set_=lambda v: FirewallLayer.set_enabled(v))
    sec.add_row(row)
    if fw["services"]:
        sec.add_row(label("Allowed services: " + ", ".join(fw["services"][:10]), "row-sub"))
    services = FirewallLayer.list_known_services()[:40]
    add_grid = Gtk.FlowBox(max_children_per_line=4, selection_mode=Gtk.SelectionMode.NONE)
    for svc in ["ssh", "http", "https", "samba", "ipp", "mdns", "vnc-server", "syncthing"]:
        on = svc in fw["services"]
        b = button(("✓ " if on else "") + svc, "btn-quiet" if not on else "btn-primary",
                   lambda btn, s=svc, is_on=on: _toggle_svc(s, not is_on, toast))
        add_grid.add(b)
    wrap = Gtk.Box(border_width=8)
    wrap.pack_start(add_grid, True, True, 0)
    sec.add_widget(wrap)
    col.add(sec)

    sec = Section("SELinux (Synthex hardening)")
    _combo(sec, "Mode", [("enforcing", "Enforcing"), ("permissive", "Permissive"), ("disabled", "Disabled")],
           lambda: sel["boot_mode"], lambda v: _set_selinux(v, toast))
    col.add(sec)

    sec = Section("Encryption & secure boot")
    ok, out, _ = run_cmd(["bash", "-c", "lsblk -no TYPE | grep -q crypt && echo yes || echo no"], timeout=5)
    sec.add_row(entity_card("Disk encryption", "LUKS container detected" if "yes" in (out or "") else "No LUKS encryption found",
                            icon_name="security-high",
                            trailing=badge("Encrypted", "ok") if "yes" in (out or "") else badge("Not encrypted", "warn")))
    ok, out, _ = run_cmd(["bash", "-c", "mokutil --sb-state 2>/dev/null || bootctl status 2>/dev/null | grep -i 'secure boot' | head -1"], timeout=5)
    sec.add_row(entity_card("Secure Boot", (out or "Unknown").strip()[:50], icon_name="application-certificate",
                            trailing=badge("Enabled", "ok") if "enabled" in (out or "").lower() else badge("Check", "neutral")))
    col.add(sec)
    return col


def _toggle_svc(svc, enable, toast):
    ok = FirewallLayer.add_service(svc) if enable else FirewallLayer.remove_service(svc)
    toast.show_message(f"{svc} {'allowed' if enable else 'blocked'}" if ok else f"Failed to update {svc}",
                       error=not ok)


def _set_selinux(mode, toast):
    if not AdminAdapter.selinux()["available"]:
        toast.show_message("SELinux not available on this system", error=True)
        return
    AdminAdapter.set_selinux(mode)
    run_cmd(["pkexec", "bash", "-c", f"sed -i 's/^SELINUX=.*/SELINUX={mode}/' /etc/selinux/config"], timeout=8)
    toast.show_message(f"SELinux: {mode} (boot default updated)")


# ─────────────────────────────────────────────────────────────────────────────
# SOFTWARE SOURCES
# ─────────────────────────────────────────────────────────────────────────────

def build_sources(toast):
    col = ContentColumn()
    col.add(PageHeader("Software Sources", "Repositories, Copr and third-party software"))

    sec = Section("RPM Fusion")
    sec.add_row(entity_card("RPM Fusion", "Free + Nonfree multimedia and driver repositories",
                            icon_name="package",
                            trailing=badge("Installed", "ok") if rf["installed"] else badge("Not installed", "warn")))
    if not rf["free"]:
        sec.add_row(button("Enable RPM Fusion Free", "btn-primary",
                           lambda b: _enable_repo("free", toast)))
    if not rf["nonfree"]:
        sec.add_row(button("Enable RPM Fusion Nonfree", "btn-quiet",
                           lambda b: _enable_repo("nonfree", toast)))
    col.add(sec)

    def render_repos(repos, sec):
        for r in repos[:16]:
            sw = Gtk.Switch(valign=Gtk.Align.CENTER)
            sw.set_active(r.get("enabled", True))
            def on_set(b, st, rid=r["id"]):
                ok = ReposAdapter.set_repo_enabled(rid, st)
                toast.show_message(f"{rid} {'enabled' if st else 'disabled'}" if ok else "Failed (needs dnf on Synthex)",
                                   error=not ok)
            sw.connect("state-set", on_set)
            sec.add_row(entity_card(r.get("name", r["id"])[:44], r.get("url", "")[:60], icon_name="package-x-generic",
                                    trailing=sw))

    col.add(AsyncSection("Repositories", loader=lambda: ReposAdapter.list_repos(),
                         renderer=render_repos))

    sec = Section("Flatpak remotes")
    for remote in _flatpak_remotes():
        sec.add_row(entity_card(f"Flatpak: {remote['name']}", remote.get("url", ""), icon_name="package-x-generic",
                                trailing=badge("Active", "ok") if not remote.get("disabled") else badge("Disabled", "neutral")))
    col.add(sec)
    return col


def _enable_repo(which, toast):
    from synth_platform_adapters import PackageManager
    res = PackageManager.install([f"rpmfusion-{which}-release"])
    toast.show_message(f"RPM Fusion {which} enabled" if res["ok"] else f"Failed: {res.get('message', 'dnf required')}",
                       error=not res["ok"])


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE MANAGER
# ─────────────────────────────────────────────────────────────────────────────

def build_updates(toast):
    col = ContentColumn()
    col.add(PageHeader("Update Manager", "System updates and automatic upgrades",
                       badges=[("Checking…", "neutral")]))

    def render_upd(upd, sec):
        shown = upd["rpm"][:14] + [{"name": f, "version": "", "repo": "flathub"} for f in upd["flatpak"][:4]]
        if shown:
            for u in shown:
                sec.add_row(entity_card(u["name"], f"{u['version']} · {u['repo']}" if u["version"] else u["repo"],
                                        icon_name="software-update-available"))
            sec.add_row(button("Install all updates", "btn-primary", lambda b: _apply_updates(toast)))
        else:
            sec.add_row(entity_card("System is up to date", "All packages current", icon_name="object-select",
                                    trailing=badge("OK", "ok")))

    col.add(AsyncSection("Available updates", "RPM packages and Flatpaks",
                         loader=lambda: UpdatesAdapter.check_updates(),
                         renderer=render_upd))
    auto = UpdatesAdapter.get_auto_update_status()

    sec = Section("Automatic updates")
    row, _ = toggle_row("Unattended updates (dnf-automatic)", "Install security updates automatically",
                        icon="system-software-update",
                        get=lambda: auto["enabled"],
                        set_=lambda v: UpdatesAdapter.set_auto_update(v))
    sec.add_row(row)
    sec.add_row(button("Refresh metadata", "btn-quiet", lambda b: _refresh_pkgs(toast)))
    col.add(sec)

    def render_hist(hist, sec):
        if hist:
            for h in hist[:8]:
                sec.add_row(entity_card(h["action"][:40], h["date"], icon_name="document-open-recent"))
        else:
            sec.add_row(label("No transaction history", "empty-state", xalign=0.5))

    col.add(AsyncSection("Recent transactions", loader=lambda: UpdatesAdapter.get_history(8),
                         renderer=render_hist))
    return col


def _apply_updates(toast):
    toast.show_message("Installing updates — this may take a while…", seconds=6)
    def work():
        res = UpdatesAdapter.apply_updates()
        GLib.idle_add(lambda: toast.show_message(res["message"][:80], error=not res["ok"], seconds=6))
    import threading
    threading.Thread(target=work, daemon=True).start()


def _refresh_pkgs(toast):
    from synth_platform_adapters import PackageManager
    res = PackageManager.refresh_cache()
    toast.show_message(res["message"][:80], error=not res["ok"])


# ─────────────────────────────────────────────────────────────────────────────
# TIMESHIFT BACKUPS
# ─────────────────────────────────────────────────────────────────────────────

def build_timeshift(toast):
    avail = TimeshiftAdapter.is_available()
    col = ContentColumn()
    col.add(PageHeader("Timeshift Backups", "BTRFS snapshots, restore and rollback",
                       badges=[("Available" if avail else "Not installed", "ok" if avail else "err")]))

    def render_snaps(snaps, sec):
        if snaps:
            for sn in snaps[:12]:
                trailing = Gtk.Box(spacing=6)
                trailing.pack_start(button("Restore", "btn-primary",
                                           lambda b, n=sn["num"]: _ts_restore(n, toast)), False, False, 0)
                trailing.pack_start(button("Delete", "btn-destructive",
                                           lambda b, n=sn["num"]: _ts_delete(n, toast)), False, False, 0)
                sec.add_row(entity_card(f"Snapshot {sn['num']}", f"{sn['date']} · {sn['type']} · {sn['tag']}",
                                        icon_name="timebench", trailing=trailing))
        else:
            sec.add_row(label("No snapshots yet — create your first restore point", "empty-state", xalign=0.5))
        sec.add_row(button("Create snapshot now", "btn-primary", lambda b: _ts_create(toast)))

    col.add(AsyncSection("Snapshots", "Restore points on this system",
                         loader=lambda: TimeshiftAdapter.list_snapshots(),
                         renderer=render_snaps))

    sec = Section("Bootable recovery")
    sec.add_row(entity_card("Timeshift GRUB integration", "Boot menu 'Synthex Recovery' lists all snapshots for rollback",
                            icon_name="system-restart", trailing=badge("Check GRUB", "neutral")))
    col.add(sec)
    return col


def _ts_create(toast):
    toast.show_message("Creating snapshot…", seconds=5)
    def work():
        res = TimeshiftAdapter.create_snapshot(tag="O", desc="Synthex Settings")
        GLib.idle_add(lambda: toast.show_message(res["message"][:80], error=not res["ok"], seconds=5))
    import threading
    threading.Thread(target=work, daemon=True).start()


def _ts_restore(num, toast):
    toast.show_message(f"Restoring snapshot {num} — a reboot will follow", seconds=6)
    def work():
        res = TimeshiftAdapter.restore_snapshot(num)
        GLib.idle_add(lambda: toast.show_message(res["message"][:80], error=not res["ok"], seconds=6))
    import threading
    threading.Thread(target=work, daemon=True).start()


def _ts_delete(num, toast):
    res = TimeshiftAdapter.delete_snapshot(num)
    toast.show_message(res["message"][:80], error=not res["ok"])


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN WINDOW
# ─────────────────────────────────────────────────────────────────────────────

def build_login(toast):
    col = ContentColumn()
    st = LoginScreenAdapter.get_settings()
    col.add(PageHeader("Login Window", f"Display manager: {st['dm'].upper()} — themes and auto-login"))

    sec = Section("Appearance")
    _combo(sec, "Greeter theme", [(t, t) for t in st["themes"]],
           lambda: st["theme"], lambda v: _set_login("Theme", "Current", v, toast), width_chars=22)
    col.add(sec)

    sec = Section("Automatic login")
    import pwd
    users = [(u.pw_name, u.pw_name) for u in pwd.getpwall() if u.pw_uid >= 1000 and "nobody" not in u.pw_name][:8]
    _combo(sec, "Auto-login user", [("", "Disabled")] + users,
           lambda: st["autologin_user"],
           lambda v: (LoginScreenAdapter.set_autologin(v, True),
                      toast.show_message(f"Auto-login: {v or 'disabled'}")), width_chars=14)
    col.add(sec)

    sec = Section("Session")
    sessions = []
    for d in ["/usr/share/xsessions", "/usr/share/wayland-sessions"]:
        if os.path.isdir(d):
            import glob as _g
            sessions += [(f[:-8], f[:-8].replace("-", " ").title()) for f in sorted(os.listdir(d)) if f.endswith(".desktop")]
    if sessions:
        _combo(sec, "Default session", sessions[:12], lambda: sessions[0][0],
               lambda v: _set_login("Autologin", "Session", v, toast), width_chars=20)
    col.add(sec)
    return col


def _set_login(section, key, value, toast):
    ok = LoginScreenAdapter.set_setting(section, key, value)
    toast.show_message("Login screen updated" if ok else "Failed to write config", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# DATE & TIME
# ─────────────────────────────────────────────────────────────────────────────

def build_datetime(toast):
    col = ContentColumn()
    ok, out, _ = run_cmd(["timedatectl", "show"], timeout=5)
    state = dict()
    for line in (out or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            state[k] = v
    ntp = state.get("NTP", "no") == "yes"
    col.add(PageHeader("Date & Time", "Network time sync and timezone",
                       badges=[("NTP sync" if ntp else "Manual", "ok" if ntp else "neutral")]))

    sec = Section("Automatic time")
    row, _ = toggle_row("Network time synchronization (NTP)", "Keep the clock accurate automatically",
                        icon="preferences-system-time",
                        get=lambda: ntp, set_=lambda v: _timedatectl(("ntpd" if False else "ntp"), v, toast))
    sec.add_row(row)
    row, _ = toggle_row("RTC in local timezone", "Store hardware clock locally (dual-boot compatibility)",
                        get=lambda: state.get("LocalRTC", "no") == "yes",
                        set_=lambda v: _timedatectl("local-rtc", v, toast))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Timezone")
    zones = ["UTC", "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
             "America/Toronto", "Europe/London", "Europe/Berlin", "Europe/Paris", "Asia/Tokyo", "Asia/Kolkata"]
    cur = state.get("Timezone", "UTC")
    if cur not in zones:
        zones = [cur] + zones
    _combo(sec, "Timezone", [(z, z) for z in zones], lambda: cur,
           lambda v: run_cmd(["pkexec", "timedatectl", "set-timezone", v]) or toast.show_message(f"Timezone: {v}"),
           width_chars=22)
    sec.add_row(entity_card("Current time", state.get("Timezone", "") + " · " + ("NTP" if ntp else "manual"),
                            icon_name="preferences-system-time"))
    col.add(sec)
    return col


def _timedatectl(prop, value, toast):
    if prop == "ntp":
        run_cmd(["pkexec", "timedatectl", "set-ntp", "true" if value else "false"], timeout=8)
        toast.show_message("NTP " + ("enabled" if value else "disabled"))
    else:
        run_cmd(["pkexec", "timedatectl", "set-local-rtc", "1" if value else "0"], timeout=8)
        toast.show_message("RTC set to " + ("local" if value else "UTC"))


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM INFO / ADMINISTRATION
# ─────────────────────────────────────────────────────────────────────────────

def build_system_info(toast):
    col = ContentColumn()
    sysinfo = SystemAdapter.get_system_info() if hasattr(SystemAdapter, "get_system_info") else {}
    col.add(PageHeader("System Information", "Hardware and SynthOS release details"))

    ok, out, _ = run_cmd(["bash", "-c",
                          "uname -r; grep -m1 'model name' /proc/cpuinfo; free -h | awk 'NR==2{print $2}'; "
                          "lspci | grep -c VGA"], timeout=6)
    kernel = mem = cpu = gpu = ""
    lines = (out or "").splitlines()
    if len(lines) >= 4:
        kernel, cpu, mem, gpu = lines[0].strip(), lines[1].split(":")[-1].strip(), lines[2], lines[3]

    sec = Section("About this system")
    sec.add_widget(info_grid([
        ("Operating system", sysinfo.get("pretty_name", "SynthOS Linux")),
        ("Kernel", kernel or "-"),
        ("Processor", cpu or "-"),
        ("Memory", mem or "-"),
        ("Graphics", gpu + " GPU(s)" if gpu else "-"),
        ("Hostname", AdminAdapter.hostname()),
    ]))
    col.add(sec)

    sec = Section("Administration")
    host_entry_row, host_entry = entry_row("Hostname", "Changes the machine's network name",
                                           icon="computer",
                                           get=lambda: AdminAdapter.hostname(),
                                           set_=lambda v: _set_hostname(v, toast))
    sec.add_row(host_entry_row)
    jh = AdminAdapter.journal_health()
    sec.add_row(entity_card("Systemd journal", jh["disk_usage"][:50], icon_name="edit-paste",
                            trailing=badge(f"{len(jh['failed_units'])} failed", "err" if jh["failed_units"] else "ok")))
    if jh["failed_units"]:
        for u in jh["failed_units"][:6]:
            sec.add_row(buttons_row(u, "Failed unit", buttons=[("Restart", "btn-primary", lambda b, uu=u: _restart_unit(uu, toast))]))
    sec.add_row(buttons_row("Diagnostics", buttons=[
        ("Journal", "btn-quiet", lambda b: _launch_term("journalctl -p err -b --no-pager | tail -40")),
        ("Services", "btn-quiet", lambda b: _launch_term("systemctl --failed")),
        ("Synthex report", "btn-quiet", lambda b: run_cmd(["synthex-system-report"]))]))
    col.add(sec)
    return col


def _set_hostname(v, toast):
    if v and v != AdminAdapter.hostname():
        ok = AdminAdapter.set_hostname(v)
        toast.show_message(f"Hostname → {v}" if ok else "Failed to set hostname", error=not ok)


def _restart_unit(u, toast):
    ok = AdminAdapter.restart_unit(u)
    toast.show_message(f"{u} restarted" if ok else f"Failed to restart {u}", error=not ok)


# ─────────────────────────────────────────────────────────────────────────────
# SCREENSAVER / LOCK
# ─────────────────────────────────────────────────────────────────────────────

def build_screensaver(toast):
    col = ContentColumn()
    st = ScreensaverAdapter.idle_settings()
    col.add(PageHeader("Screen Lock & Saver", "Idle locking and screensaver behavior",
                       badges=[("Locking", "ok") if st["lock_enabled"] else ("No lock", "warn")]))

    sec = Section("Idle & lock")
    _combo(sec, "Blank screen after", [(0, "Never"), (60, "1 minute"), (300, "5 minutes"),
                                       (600, "10 minutes"), (1800, "30 minutes")],
           lambda: st["idle_delay"] * 60,
           lambda v: ScreensaverAdapter.set_idle_delay(int(v) // 60 if int(v) else 0), width_chars=14)
    row, _ = toggle_row("Lock screen when idle", icon="system-lock-screen",
                        get=lambda: st["lock_enabled"],
                        set_=lambda v: ScreensaverAdapter.set("lock-enabled", v))
    sec.add_row(row)
    _combo(sec, "Lock after screensaver", [(0, "Immediately"), (15, "15 seconds"), (60, "1 minute"),
                                           (300, "5 minutes"), (1800, "30 minutes")],
           lambda: int(st.get("lock_delay", 0)), lambda v: ScreensaverAdapter.set("lock-delay", int(v)),
           width_chars=14)
    row, _ = toggle_row("Lock on suspend", "Lock before going to sleep",
                        get=lambda: st.get("ubuntu_lock_on_suspend", True),
                        set_=lambda v: ScreensaverAdapter.set("ubuntu-lock-on-suspend", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Saver content")
    row, _ = toggle_row("Show clock", icon="preferences-system-time",
                        get=lambda: st.get("show_clock", True),
                        set_=lambda v: ScreensaverAdapter.set("show-clock", v))
    sec.add_row(row)
    sec.add_row(button("Lock screen now", "btn-quiet", lambda b: ScreensaverAdapter.lock_now()))
    col.add(sec)
    return col
