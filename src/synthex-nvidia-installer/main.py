#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS NVIDIA Driver Installer — auto-selects correct driver branch

import sys, subprocess, os, threading
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib

APP_ID = "org.synthos.NvidiaInstaller"

DRIVER_BRANCHES = {
    "open": {
        "label": "NVIDIA Open (Recommended for RTX 2000+)",
        "pkg":   "nvidia-open",
        "desc":  "Open-source kernel module — best for RTX 20xx, 30xx, 40xx, 50xx",
    },
    "proprietary": {
        "label": "NVIDIA Proprietary (Legacy & GTX)",
        "pkg":   "nvidia-driver",
        "desc":  "Closed-source driver — supports GTX 900/1000 and older",
    },
    "nouveau": {
        "label": "Nouveau (Open-source, no CUDA)",
        "pkg":   "xorg-x11-drv-nouveau",
        "desc":  "Community reverse-engineered driver — lowest performance",
    },
}

def detect_gpu():
    try:
        out = subprocess.check_output(["lspci","-mm"], text=True)
        for line in out.splitlines():
            if "NVIDIA" in line.upper() or "GeForce" in line or "Quadro" in line:
                return line
    except Exception:
        pass  # GPU detection best-effort; non-NVIDIA paths handled below
    return "No NVIDIA GPU detected"

def detect_best_branch(gpu_line: str) -> str:
    gpu = gpu_line.upper()
    # RTX 20xx and newer → open
    for series in ["RTX 20","RTX 30","RTX 40","RTX 50","A100","A4000","A6000"]:
        if series.upper() in gpu:
            return "open"
    # GTX 900/1000/1600 → proprietary
    for series in ["GTX 9","GTX 10","GTX 16","QUADRO","TESLA"]:
        if series.upper() in gpu:
            return "proprietary"
    return "open"  # default to open for unknown modern cards


class NvidiaInstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="NVIDIA Driver Installer")
        self.set_default_size(640, 480)
        self._selected = "open"
        self._build()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)
        outer.append(Adw.HeaderBar())

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(24); box.set_margin_end(24)
        scroll.set_child(box); outer.append(scroll)

        # GPU Detection
        gpu_line = detect_gpu()
        gpu_group = Adw.PreferencesGroup(title="Detected GPU")
        gpu_row = Adw.ActionRow(title=gpu_line)
        best = detect_best_branch(gpu_line)
        gpu_row.set_subtitle(f"Recommended driver branch: {best}")
        gpu_group.add(gpu_row)
        box.append(gpu_group)

        # Driver selection
        drv_group = Adw.PreferencesGroup(title="Select Driver Branch")
        first_radio = None
        for branch_id, branch in DRIVER_BRANCHES.items():
            row = Adw.ActionRow(title=branch["label"], subtitle=branch["desc"])
            radio = Gtk.CheckButton()
            radio.set_valign(Gtk.Align.CENTER)
            if first_radio is None:
                first_radio = radio
            else:
                radio.set_group(first_radio)
            if branch_id == best:
                radio.set_active(True)
                self._selected = branch_id
            radio.connect("toggled", self._on_select, branch_id)
            row.add_prefix(radio)
            drv_group.add(row)
        box.append(drv_group)

        # Options
        opts_group = Adw.PreferencesGroup(title="Options")
        cuda_row = Adw.ActionRow(title="Install CUDA Toolkit",
                                  subtitle="Required for AI/ML workloads")
        self._cuda_sw = Gtk.Switch(); self._cuda_sw.set_valign(Gtk.Align.CENTER)
        cuda_row.add_suffix(self._cuda_sw)
        opts_group.add(cuda_row)

        vk_row = Adw.ActionRow(title="Install Vulkan layers",
                                subtitle="Recommended for gaming")
        self._vk_sw = Gtk.Switch(); self._vk_sw.set_active(True)
        self._vk_sw.set_valign(Gtk.Align.CENTER)
        vk_row.add_suffix(self._vk_sw)
        opts_group.add(vk_row)
        box.append(opts_group)

        # Progress
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        box.append(self._progress)

        self._status_lbl = Gtk.Label(label="")
        self._status_lbl.set_xalign(0)
        box.append(self._status_lbl)

        # Install button
        btn = Gtk.Button(label="Install Driver")
        btn.add_css_class("suggested-action")
        btn.add_css_class("pill")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_margin_top(8)
        btn.connect("clicked", self._on_install)
        box.append(btn)

    def _on_select(self, radio, branch_id):
        if radio.get_active():
            self._selected = branch_id

    def _on_install(self, btn):
        btn.set_sensitive(False)
        self._progress.set_visible(True)
        self._tid = GLib.timeout_add(100, lambda: self._progress.pulse() or True)
        threading.Thread(target=self._install_worker, args=(btn,), daemon=True).start()

    def _install_worker(self, btn):
        branch = DRIVER_BRANCHES[self._selected]
        pkgs = [branch["pkg"]]
        if self._cuda_sw.get_active():
            pkgs += ["cuda", "cuda-toolkit"]
        if self._vk_sw.get_active():
            pkgs += ["vulkan-tools", "nvidia-vaapi-driver"]

        cmd = ["pkexec", "dnf", "install", "-y"] + pkgs
        GLib.idle_add(lambda: self._status_lbl.set_label(f"Installing: {', '.join(pkgs)}…"))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        GLib.idle_add(self._install_done, r.returncode == 0, btn)

    def _install_done(self, ok, btn):
        GLib.source_remove(self._tid)
        self._progress.set_visible(False)
        if ok:
            self._status_lbl.set_markup(
                '<span foreground="#44CC88">✓ Driver installed! Reboot to activate.</span>'
            )
        else:
            self._status_lbl.set_markup(
                '<span foreground="#FF4444">✗ Installation failed. Check dnf logs.</span>'
            )
        btn.set_sensitive(True)
        return False


class NvidiaInstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: NvidiaInstallerWindow(a).present())

if __name__ == "__main__":
    NvidiaInstallerApp().run(sys.argv)
