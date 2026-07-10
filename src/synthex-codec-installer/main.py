#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Codec Installer — multimedia codec manager

import sys, subprocess, threading, shutil
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib

APP_ID = "org.synthos.CodecInstaller"

CODEC_GROUPS = {
    "Video Codecs": [
        ("gstreamer1-plugins-good",         "GStreamer Good",    "VP8, VP9, Ogg, FLAC"),
        ("gstreamer1-plugins-bad-free",     "GStreamer Bad",     "AAC, H.264 (free)"),
        ("gstreamer1-plugins-ugly",         "GStreamer Ugly",    "MP3, MPEG-2 (license-restricted)"),
        ("gstreamer1-plugin-libav",         "FFmpeg/libav",      "Wide format support via FFmpeg"),
        ("ffmpeg",                          "FFmpeg CLI",        "Full-featured multimedia converter"),
    ],
    "Hardware Acceleration": [
        ("libva-intel-driver",              "Intel VA-API",      "Intel GPU hardware decode"),
        ("libva-nvidia-driver",             "NVIDIA VA-API",     "NVIDIA hardware decode"),
        ("mesa-va-drivers",                 "AMD VA-API",        "AMD GPU hardware decode (Mesa)"),
        ("nvidia-vaapi-driver",             "NVIDIA VAAPI",      "NVIDIA VAAPI bridge"),
        ("libva-utils",                     "VA-API Utils",      "Hardware acceleration info tools"),
    ],
    "Audio Codecs": [
        ("lame",                            "LAME MP3",          "MP3 encoder"),
        ("flac",                            "FLAC",              "Lossless audio"),
        ("opus-tools",                      "Opus",              "Modern high-quality codec"),
        ("faad2",                           "AAC Decoder",       "Advanced Audio Coding decode"),
    ],
    "DVD & Optical": [
        ("libdvdread",                      "DVD Read",          "DVD filesystem access"),
        ("libdvdcss",                       "DVD CSS",           "DVD content scramble decryption"),
        ("libbluray",                       "Blu-ray",           "Blu-ray disc support"),
    ],
}


def pkg_installed(pkg):
    return subprocess.run(["rpm","-q","--quiet",pkg], capture_output=True).returncode == 0


class CodecInstallerWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Codec Installer")
        self.set_default_size(700, 580)
        self._checks = {}
        self._build()
        threading.Thread(target=self._check_installed, daemon=True).start()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)
        outer.append(Adw.HeaderBar())

        # Banner
        banner = Adw.Banner(
            title="Some codecs may have licensing restrictions in certain countries.",
            button_label="Learn more",
            revealed=True
        )
        outer.append(banner)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(20); box.set_margin_end(20)
        scroll.set_child(box); outer.append(scroll)

        for group_name, codecs in CODEC_GROUPS.items():
            grp = Adw.PreferencesGroup(title=group_name)
            for pkg, label, desc in codecs:
                row = Adw.ActionRow(title=label, subtitle=desc)
                chk = Gtk.CheckButton()
                chk.set_active(True)
                chk.set_valign(Gtk.Align.CENTER)
                row.add_suffix(chk)
                self._checks[pkg] = chk

                status = Gtk.Label(label="…")
                status.add_css_class("dim-label")
                row.add_suffix(status)
                chk._status_lbl = status

                grp.add(row)
            box.append(grp)

        # Progress
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        box.append(self._progress)

        btn_box = Gtk.Box(spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(8)

        all_btn = Gtk.Button(label="Select All")
        all_btn.connect("clicked", lambda _: [c.set_active(True) for c in self._checks.values()])
        btn_box.append(all_btn)

        install_btn = Gtk.Button(label="Install Selected")
        install_btn.add_css_class("suggested-action")
        install_btn.connect("clicked", self._on_install)
        btn_box.append(install_btn)

        box.append(btn_box)
        self._install_btn = install_btn

    def _check_installed(self):
        for pkg, chk in self._checks.items():
            inst = pkg_installed(pkg)
            GLib.idle_add(self._update_status, pkg, chk, inst)

    def _update_status(self, pkg, chk, inst):
        chk._status_lbl.set_markup(
            '<span foreground="#44CC88">Installed</span>' if inst
            else '<span foreground="#888888">Not installed</span>'
        )
        if inst:
            chk.set_active(False)  # don't re-install
        return False

    def _on_install(self, btn):
        to_install = [pkg for pkg, chk in self._checks.items() if chk.get_active()]
        if not to_install:
            return
        btn.set_sensitive(False)
        self._progress.set_visible(True)
        self._tid = GLib.timeout_add(80, lambda: self._progress.pulse() or True)
        threading.Thread(
            target=self._install_worker, args=(to_install, btn), daemon=True
        ).start()

    def _install_worker(self, pkgs, btn):
        # Enable RPM Fusion if needed for codecs
        rpmfusion_cmd = [
            "pkexec","dnf","install","-y","--nogpgcheck",
            "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm",
            "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm",
        ]
        subprocess.run(" ".join(rpmfusion_cmd), shell=True, capture_output=True, timeout=120)

        r = subprocess.run(
            ["pkexec","dnf","install","-y","--"] + pkgs,
            capture_output=True, text=True, timeout=600
        )
        GLib.idle_add(self._install_done, r.returncode == 0, btn)

    def _install_done(self, ok, btn):
        GLib.source_remove(self._tid)
        self._progress.set_fraction(1.0 if ok else 0)
        self._progress.set_visible(False)
        btn.set_sensitive(True)
        btn.set_label("Done ✓" if ok else "Retry ✗")
        threading.Thread(target=self._check_installed, daemon=True).start()
        return False


class CodecInstallerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: CodecInstallerWindow(a).present())

if __name__ == "__main__":
    CodecInstallerApp().run(sys.argv)
