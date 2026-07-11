#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Gaming Center — GameMode, per-game profiles, GPU tuning, library

import sys, os, subprocess, threading, json, glob
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio

APP_ID = "org.synthos.GamingCenter"

GPU_PRESETS = {
    "performance": {
        "label": "Performance",
        "desc":  "Max clocks, all cores, no power saving",
        "scaling": "performance",
        "mangohud": True,
    },
    "balanced": {
        "label": "Balanced",
        "desc":  "Adaptive clocks, moderate power",
        "scaling": "schedutil",
        "mangohud": False,
    },
    "battery": {
        "label": "Battery Saver",
        "desc":  "Conservative clocks, low power",
        "scaling": "powersave",
        "mangohud": False,
    },
}


def shell(cmd, timeout=5):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, shell=isinstance(cmd, str)).stdout.strip()
    except Exception:
        return ""


def is_active(unit):
    return subprocess.run(["systemctl", "--user", "is-active", "--quiet", unit]).returncode == 0


class GamingCenterWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Gaming Center")
        self.set_default_size(860, 640)
        self._current_preset = "balanced"
        self._build_ui()
        threading.Thread(target=self._detect_state, daemon=True).start()

    def _build_ui(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        hb = Adw.HeaderBar()
        hb.set_title_widget(Adw.WindowTitle(title="Gaming Center", subtitle="SynthOS"))
        outer.append(hb)

        # Navigation pages
        nav_view = Adw.NavigationView()
        outer.append(nav_view)

        # Main page with tabs
        page = Adw.NavigationPage(title="Gaming Center")
        nav_view.push(page)

        tab_view = Adw.ViewStack()
        page.set_child(tab_view)

        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(tab_view)
        switcher_bar.set_reveal(True)

        stack_outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        stack_outer.append(tab_view)
        stack_outer.append(switcher_bar)
        page.set_child(stack_outer)

        # Tab 1: Overview
        tab_view.add_titled(self._build_overview(), "overview", "Overview")
        tab_view.get_page(tab_view.get_child_by_name("overview")).set_icon_name("applications-games")

        # Tab 2: GPU / Performance
        tab_view.add_titled(self._build_gpu(), "gpu", "GPU & Performance")
        tab_view.get_page(tab_view.get_child_by_name("gpu")).set_icon_name("video-display")

        # Tab 3: MangoHud / Overlay
        tab_view.add_titled(self._build_overlay(), "overlay", "Overlay")
        tab_view.get_page(tab_view.get_child_by_name("overlay")).set_icon_name("view-more-symbolic")

        # Tab 4: Controllers
        tab_view.add_titled(self._build_controllers(), "controllers", "Controllers")
        tab_view.get_page(tab_view.get_child_by_name("controllers")).set_icon_name("input-gaming")

        # Tab 5: Launchers
        tab_view.add_titled(self._build_launchers(), "launchers", "Launchers")
        tab_view.get_page(tab_view.get_child_by_name("launchers")).set_icon_name("system-run")

    # ── Overview ──────────────────────────────────────────────────────────────
    def _build_overview(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box)

        # GameMode toggle
        gm_group = Adw.PreferencesGroup(title="GameMode")
        gm_row = Adw.ActionRow(
            title="Enable GameMode",
            subtitle="Boosts CPU, GPU and I/O priority while gaming"
        )
        self._gm_switch = Gtk.Switch()
        self._gm_switch.set_valign(Gtk.Align.CENTER)
        self._gm_switch.connect("state-set", self._on_gamemode_toggle)
        gm_row.add_suffix(self._gm_switch)
        gm_group.add(gm_row)

        gm_status_row = Adw.ActionRow(title="GameMode Status")
        self._gm_status_lbl = Gtk.Label(label="Checking…")
        self._gm_status_lbl.add_css_class("dim-label")
        gm_status_row.add_suffix(self._gm_status_lbl)
        gm_group.add(gm_status_row)
        box.append(gm_group)

        # Performance preset
        perf_group = Adw.PreferencesGroup(title="Performance Preset")
        for preset_id, preset in GPU_PRESETS.items():
            row = Adw.ActionRow(
                title=preset["label"],
                subtitle=preset["desc"]
            )
            radio = Gtk.CheckButton()
            radio.set_valign(Gtk.Align.CENTER)
            if preset_id == "balanced":
                radio.set_active(True)
                self._preset_first_radio = radio
            else:
                radio.set_group(self._preset_first_radio)
            radio.connect("toggled", self._on_preset_toggle, preset_id)
            row.add_prefix(radio)
            perf_group.add(row)
        box.append(perf_group)

        # Quick stats
        stats_group = Adw.PreferencesGroup(title="System Stats")
        self._cpu_row = Adw.ActionRow(title="CPU Governor")
        self._cpu_val = Gtk.Label(label="…")
        self._cpu_row.add_suffix(self._cpu_val)
        stats_group.add(self._cpu_row)

        self._gpu_row = Adw.ActionRow(title="GPU Driver")
        self._gpu_val = Gtk.Label(label="…")
        self._gpu_row.add_suffix(self._gpu_val)
        stats_group.add(self._gpu_row)

        self._ram_row = Adw.ActionRow(title="Available RAM")
        self._ram_val = Gtk.Label(label="…")
        self._ram_row.add_suffix(self._ram_val)
        stats_group.add(self._ram_row)
        box.append(stats_group)

        return scroll

    # ── GPU / Performance ──────────────────────────────────────────────────────
    def _build_gpu(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box)

        # GPU info
        gpu_group = Adw.PreferencesGroup(title="GPU Information")
        self._gpu_info_rows = {}
        for key in ["Model", "Driver", "VRAM", "Temperature", "Utilization"]:
            row = Adw.ActionRow(title=key)
            val = Gtk.Label(label="Detecting…")
            val.add_css_class("dim-label")
            row.add_suffix(val)
            self._gpu_info_rows[key] = val
            gpu_group.add(row)
        box.append(gpu_group)

        # Proton / Wine settings
        proton_group = Adw.PreferencesGroup(title="Proton / Wine")
        proton_row = Adw.ActionRow(
            title="Proton Version",
            subtitle="Default Proton used for Steam games"
        )
        self._proton_combo = Gtk.DropDown.new_from_strings([
            "Proton Experimental", "Proton 9.0 (Stable)", "Proton 8.0",
            "GE-Proton Latest", "Wine-GE Latest",
        ])
        self._proton_combo.set_valign(Gtk.Align.CENTER)
        proton_row.add_suffix(self._proton_combo)
        proton_group.add(proton_row)

        esync_row = Adw.ActionRow(title="Esync", subtitle="Improved synchronization objects")
        self._esync_sw = Gtk.Switch(); self._esync_sw.set_active(True)
        self._esync_sw.set_valign(Gtk.Align.CENTER)
        esync_row.add_suffix(self._esync_sw)
        proton_group.add(esync_row)

        fsync_row = Adw.ActionRow(title="Fsync", subtitle="Linux futex-based sync (kernel 5.16+)")
        self._fsync_sw = Gtk.Switch(); self._fsync_sw.set_active(True)
        self._fsync_sw.set_valign(Gtk.Align.CENTER)
        fsync_row.add_suffix(self._fsync_sw)
        proton_group.add(fsync_row)
        box.append(proton_group)

        # Apply button
        apply_btn = Gtk.Button(label="Apply GPU Settings")
        apply_btn.add_css_class("suggested-action")
        apply_btn.set_halign(Gtk.Align.CENTER)
        apply_btn.connect("clicked", self._apply_gpu_settings)
        box.append(apply_btn)

        # Refresh GPU info
        GLib.timeout_add_seconds(5, self._refresh_gpu_info)
        GLib.idle_add(self._refresh_gpu_info)

        return scroll

    # ── Overlay (MangoHud) ─────────────────────────────────────────────────────
    def _build_overlay(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box)

        mg_group = Adw.PreferencesGroup(
            title="MangoHud Overlay",
            description="In-game performance overlay (FPS, temps, CPU/GPU usage)"
        )

        enable_row = Adw.ActionRow(title="Enable MangoHud globally")
        self._mangohud_sw = Gtk.Switch()
        self._mangohud_sw.set_valign(Gtk.Align.CENTER)
        self._mangohud_sw.connect("state-set", self._on_mangohud_toggle)
        enable_row.add_suffix(self._mangohud_sw)
        mg_group.add(enable_row)

        for label in ["FPS Counter", "CPU Usage", "GPU Usage", "RAM Usage",
                       "GPU Temperature", "Frame Time", "Resolution"]:
            row = Adw.ActionRow(title=label)
            sw = Gtk.Switch(); sw.set_active(True)
            sw.set_valign(Gtk.Align.CENTER)
            row.add_suffix(sw)
            mg_group.add(row)

        box.append(mg_group)

        # Preset corner
        corner_group = Adw.PreferencesGroup(title="Overlay Position")
        corner_row = Adw.ActionRow(title="Corner")
        corner_combo = Gtk.DropDown.new_from_strings(
            ["Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right", "Top-Center"]
        )
        corner_combo.set_valign(Gtk.Align.CENTER)
        corner_row.add_suffix(corner_combo)
        corner_group.add(corner_row)
        box.append(corner_group)

        edit_btn = Gtk.Button(label="Edit MangoHud Config…")
        edit_btn.set_halign(Gtk.Align.CENTER)
        edit_btn.connect("clicked", lambda _: subprocess.Popen(
            ["xdg-open", os.path.expanduser("~/.config/MangoHud/MangoHud.conf")]
        ))
        box.append(edit_btn)

        return scroll

    # ── Controllers ────────────────────────────────────────────────────────────
    def _build_controllers(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box)

        ctrl_group = Adw.PreferencesGroup(
            title="Controller Support",
            description="Detected input devices"
        )

        # DS4 / DualSense
        ds_row = Adw.ActionRow(
            title="DualSense / DualShock 4",
            subtitle="PlayStation controller via USB or Bluetooth"
        )
        ds_sw = Gtk.Switch(); ds_sw.set_valign(Gtk.Align.CENTER)
        ds_row.add_suffix(ds_sw)
        ctrl_group.add(ds_row)

        # Xbox
        xbox_row = Adw.ActionRow(
            title="Xbox Controller",
            subtitle="xpadneo driver (improved Xbox One/Series)"
        )
        xbox_sw = Gtk.Switch(); xbox_sw.set_valign(Gtk.Align.CENTER)
        xbox_row.add_suffix(xbox_sw)
        ctrl_group.add(xbox_row)

        # Steam Input
        steam_row = Adw.ActionRow(
            title="Steam Input",
            subtitle="Use Steam's controller remapping"
        )
        steam_sw = Gtk.Switch(); steam_sw.set_active(True)
        steam_sw.set_valign(Gtk.Align.CENTER)
        steam_row.add_suffix(steam_sw)
        ctrl_group.add(steam_row)
        box.append(ctrl_group)

        # Remap button
        remap_btn = Gtk.Button(label="Open Input Remapper")
        remap_btn.set_halign(Gtk.Align.CENTER)
        remap_btn.connect("clicked", lambda _: subprocess.Popen(["input-remapper-gtk"]))
        box.append(remap_btn)

        return scroll

    # ── Launchers ─────────────────────────────────────────────────────────────
    def _build_launchers(self):
        scroll = Gtk.ScrolledWindow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box)

        launchers_group = Adw.PreferencesGroup(title="Game Launchers")
        launchers = [
            ("Steam",   "com.valvesoftware.Steam",        "Valve game platform"),
            ("Lutris",  "net.lutris.Lutris",              "Open gaming platform"),
            ("Heroic",  "com.heroicgameslauncher.hgl",    "Epic & GOG via Heroic"),
            ("Bottles", "com.usebottles.bottles",         "Run Windows games"),
            ("Proton",  "proton-ge-custom",               "Community Proton builds"),
        ]
        for name, app_id, desc in launchers:
            row = Adw.ActionRow(title=name, subtitle=desc)
            launch_btn = Gtk.Button(label="Open")
            launch_btn.set_valign(Gtk.Align.CENTER)
            launch_btn.connect(
                "clicked",
                lambda _, aid=app_id: subprocess.Popen(["flatpak","run", aid])
            )
            row.add_suffix(launch_btn)
            launchers_group.add(row)
        box.append(launchers_group)
        return scroll

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _detect_state(self):
        gm_on = is_active("gamescoped.service") or is_active("gamemode.service")
        gov = shell("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        gpu_driver = shell("lspci -k | grep -A2 'VGA\\|3D' | grep 'Kernel driver' | head -1 | awk '{print $NF}'")
        try:
            mem_free = int(open("/proc/meminfo").read().split("MemAvailable:")[1].split()[0])
            ram_str = f"{mem_free // 1024} MB free"
        except Exception:
            ram_str = "Unknown"

        GLib.idle_add(self._update_overview, gm_on, gov, gpu_driver, ram_str)

    def _update_overview(self, gm_on, gov, gpu_driver, ram_str):
        self._gm_switch.set_active(gm_on)
        self._gm_status_lbl.set_label("Running ✓" if gm_on else "Stopped")
        self._cpu_val.set_label(gov or "Unknown")
        self._gpu_val.set_label(gpu_driver or "Unknown")
        self._ram_val.set_label(ram_str)
        return False

    def _refresh_gpu_info(self):
        def _worker():
            info = {}
            # Try nvidia-smi first
            nv = shell(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,temperature.gpu,utilization.gpu",
                         "--format=csv,noheader,nounits"])
            if nv:
                parts = [p.strip() for p in nv.split(",")]
                if len(parts) >= 5:
                    info["Model"]       = parts[0]
                    info["Driver"]      = f"nvidia {parts[1]}"
                    info["VRAM"]        = f"{parts[2]} MiB"
                    info["Temperature"] = f"{parts[3]} °C"
                    info["Utilization"] = f"{parts[4]}%"
            else:
                # AMD fallback
                info["Model"]  = shell("lspci -mm | grep -i 'VGA\\|3D' | head -1 | cut -d'\"' -f6")
                info["Driver"] = shell("lspci -k | grep -A2 'VGA\\|3D' | grep driver | awk '{print $NF}'")
                info["VRAM"]   = "See /sys/class/drm"
                info["Temperature"] = shell("sensors 2>/dev/null | grep -i 'edge\\|junction\\|GPU' | head -1 | awk '{print $2}'") or "N/A"
                info["Utilization"] = "N/A"
            GLib.idle_add(self._set_gpu_info, info)
        threading.Thread(target=_worker, daemon=True).start()
        return True  # Keep timer running

    def _set_gpu_info(self, info):
        for key, val in info.items():
            if key in self._gpu_info_rows:
                self._gpu_info_rows[key].set_label(val or "N/A")
        return False

    def _on_gamemode_toggle(self, sw, state):
        action = "start" if state else "stop"
        subprocess.Popen(["systemctl", "--user", action, "synthex-gaming-mode.service"])
        return False

    def _on_mangohud_toggle(self, sw, state):
        conf = os.path.expanduser("~/.config/MangoHud/MangoHud.conf")
        os.makedirs(os.path.dirname(conf), exist_ok=True)
        with open(conf, "w") as f:
            if state:
                f.write("fps\ncpu_stats\ngpu_stats\nram\ngpu_temp\nframe_timing\nresolution\n")
            else:
                f.write("# MangoHud disabled\n")
        return False

    def _on_preset_toggle(self, radio, preset_id):
        if radio.get_active():
            self._current_preset = preset_id

    def _apply_gpu_settings(self, _btn):
        preset = GPU_PRESETS.get(self._current_preset, GPU_PRESETS["balanced"])
        gov = preset["scaling"]
        for cpu in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"):
            try:
                subprocess.run(["pkexec", "tee", cpu], input=gov, text=True,
                                capture_output=True, timeout=5)
            except Exception:
                pass  # preset apply is best-effort
        subprocess.Popen(["systemctl", "--user",
                          "start" if preset["mangohud"] else "stop",
                          "mangohud-helper.service"],
                         stderr=subprocess.DEVNULL)


class GamingCenterApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: GamingCenterWindow(a).present())


if __name__ == "__main__":
    app = GamingCenterApp()
    sys.exit(app.run(sys.argv))
