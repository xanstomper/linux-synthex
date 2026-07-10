#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Kernel Manager — list, install, remove kernel variants

import sys, subprocess, threading, re
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib

APP_ID = "org.synthos.KernelManager"

KERNEL_VARIANTS = [
    ("linux-synthex",           "SynthOS Kernel",       "Custom kernel with BFQ, BORE, FUTEX2, SynthOS patches"),
    ("linux-synthex-lts",       "SynthOS LTS Kernel",   "Long-term stable branch for maximum reliability"),
    ("linux-synthex-hardened",  "Hardened Kernel",      "Security-hardened with extra exploit mitigations"),
    ("linux-synthex-zen",       "Zen Kernel",           "Optimized for desktop responsiveness"),
    ("linux-synthex-gaming",    "Gaming Kernel",        "Maximum FPS: BORE, Cachy, HDR, FUTEX2"),
    ("kernel",                  "Fedora Kernel",        "Upstream Fedora kernel (fallback)"),
    ("kernel-lts",              "Fedora LTS",           "Fedora long-term support kernel"),
]

def get_installed_kernels():
    try:
        out = subprocess.check_output(
            ["rpm","-qa","--qf","%{NAME} %{VERSION}-%{RELEASE}\\n"],
            text=True, timeout=15
        )
        installed = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and ("kernel" in parts[0] or "linux" in parts[0]):
                installed[parts[0]] = parts[1]
        return installed
    except Exception:
        return {}

def get_current_kernel():
    try:
        return subprocess.check_output(["uname","-r"], text=True).strip()
    except Exception:
        return "unknown"

def get_available_versions():
    try:
        out = subprocess.check_output(
            ["dnf","repoquery","--latest-limit=3","--qf","%{name} %{version}-%{release}"] +
            [v[0] for v in KERNEL_VARIANTS],
            text=True, timeout=30, stderr=subprocess.DEVNULL
        )
        available = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                available.setdefault(parts[0], []).append(parts[1])
        return available
    except Exception:
        return {}


class KernelManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Kernel Manager")
        self.set_default_size(720, 580)
        self._installed = {}
        self._current   = get_current_kernel()
        self._build()
        threading.Thread(target=self._load, daemon=True).start()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        hb = Adw.HeaderBar()
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.connect("clicked", lambda _: threading.Thread(target=self._load, daemon=True).start())
        hb.pack_end(refresh_btn)
        outer.append(hb)

        # Current kernel info
        self._cur_banner = Adw.Banner(
            title=f"Running: {self._current}",
            revealed=True
        )
        outer.append(self._cur_banner)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box); outer.append(scroll)

        # Kernel list
        self._kernel_group = Adw.PreferencesGroup(
            title="Available Kernel Variants",
            description="Installed kernels are shown with a checkmark. Reboot after changing."
        )
        self._rows = {}
        for pkg, label, desc in KERNEL_VARIANTS:
            row = Adw.ActionRow(title=label, subtitle=desc)

            status_lbl = Gtk.Label(label="Checking…")
            status_lbl.add_css_class("dim-label")
            row.add_suffix(status_lbl)

            btn = Gtk.Button(label="…")
            btn.set_valign(Gtk.Align.CENTER)
            btn.set_sensitive(False)
            btn.connect("clicked", self._on_kernel_action, pkg, btn, status_lbl)
            row.add_suffix(btn)

            self._kernel_group.add(row)
            self._rows[pkg] = (row, status_lbl, btn)

        box.append(self._kernel_group)

        # GRUB options
        grub_group = Adw.PreferencesGroup(title="Boot Options")
        boot_row = Adw.ActionRow(title="Default Boot Entry",
                                  subtitle="Select which kernel boots by default")
        grub_btn = Gtk.Button(label="Open GRUB Config")
        grub_btn.set_valign(Gtk.Align.CENTER)
        grub_btn.connect("clicked", lambda _: subprocess.Popen(
            ["pkexec","nano","/etc/default/grub"]
        ))
        boot_row.add_suffix(grub_btn)
        grub_group.add(boot_row)

        maint_row = Adw.ActionRow(title="Remove Old Kernels",
                                   subtitle="Keep only the 2 most recent kernels")
        clean_btn = Gtk.Button(label="Clean Up")
        clean_btn.set_valign(Gtk.Align.CENTER)
        clean_btn.connect("clicked", self._clean_old_kernels)
        maint_row.add_suffix(clean_btn)
        grub_group.add(maint_row)
        box.append(grub_group)

        # Progress
        self._progress = Gtk.ProgressBar(); self._progress.set_visible(False)
        box.append(self._progress)

    def _load(self):
        self._installed = get_installed_kernels()
        GLib.idle_add(self._update_ui)

    def _update_ui(self):
        for pkg, (row, status_lbl, btn) in self._rows.items():
            if pkg in self._installed:
                ver = self._installed[pkg]
                status_lbl.set_markup(
                    f'<span foreground="#44CC88">✓ {ver}</span>'
                )
                btn.set_label("Remove")
                btn.remove_css_class("suggested-action")
                btn.add_css_class("destructive-action")
            else:
                status_lbl.set_label("Not installed")
                btn.set_label("Install")
                btn.add_css_class("suggested-action")
                btn.remove_css_class("destructive-action")
            btn.set_sensitive(True)
        return False

    def _on_kernel_action(self, _btn, pkg, btn, status_lbl):
        if pkg in self._installed:
            # Confirm remove
            dlg = Adw.MessageDialog(
                heading=f"Remove {pkg}?",
                body="The kernel will be removed from your system. Make sure you have another kernel installed.",
            )
            dlg.add_response("cancel", "Cancel")
            dlg.add_response("remove", "Remove")
            dlg.set_response_appearance("remove", Adw.ResponseAppearance.DESTRUCTIVE)
            dlg.set_default_response("cancel")
            dlg.set_transient_for(self)
            dlg.connect("response", lambda d, r: self._do_action(pkg, "remove", btn) if r == "remove" else None)
            dlg.present()
        else:
            self._do_action(pkg, "install", btn)

    def _do_action(self, pkg, action, btn):
        btn.set_sensitive(False)
        btn.set_label("…")
        self._progress.set_visible(True)
        tid = GLib.timeout_add(80, lambda: self._progress.pulse() or True)
        threading.Thread(
            target=self._action_worker, args=(pkg, action, btn, tid), daemon=True
        ).start()

    def _action_worker(self, pkg, action, btn, tid):
        r = subprocess.run(
            ["pkexec","dnf", action,"-y","--",pkg],
            capture_output=True, text=True, timeout=300
        )
        ok = r.returncode == 0
        GLib.idle_add(self._action_done, ok, tid)
        threading.Thread(target=self._load, daemon=True).start()

    def _action_done(self, ok, tid):
        GLib.source_remove(tid)
        self._progress.set_visible(False)
        return False

    def _clean_old_kernels(self, _btn):
        subprocess.Popen(["pkexec","dnf","remove","$(dnf repoquery --installonly --latest-limit=-2 -q)"],
                         shell=False)


class KernelManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: KernelManagerWindow(a).present())

if __name__ == "__main__":
    KernelManagerApp().run(sys.argv)
