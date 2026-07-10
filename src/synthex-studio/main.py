#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Studio — creative workstation launcher and profile manager
# Opens a specialized Studio environment with audio/video/graphics tools

import sys, os, subprocess, shutil
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib

APP_ID = "org.synthos.Studio"

TOOLS = {
    "Audio Production": [
        ("Ardour",       "ardour",               "Professional DAW",               "org.ardour.Ardour"),
        ("LMMS",         "lmms",                 "Music production suite",         "io.lmms.LMMS"),
        ("Carla",        "carla",                "Audio plugin host",              "studio.kx.carla"),
        ("Audacity",     "audacity",             "Audio editor",                   "org.audacityteam.Audacity"),
        ("Reaper",       "reaper",               "Professional DAW (Reaper)",      None),
        ("EasyEffects",  "com.github.wwmm.easyeffects","Audio effects",           "com.github.wwmm.easyeffects"),
    ],
    "Video Production": [
        ("Kdenlive",     "kdenlive",             "Video editor",                   "org.kde.kdenlive"),
        ("DaVinci Resolve","resolve",            "Professional video editor",      None),
        ("Shotcut",      "shotcut",              "Free video editor",              "org.shotcut.Shotcut"),
        ("OBS Studio",   "obs",                  "Streaming & recording",          "com.obsproject.Studio"),
        ("Handbrake",    "handbrake",            "Video converter",                "fr.handbrake.ghb"),
    ],
    "Graphics & Illustration": [
        ("GIMP",         "gimp",                 "Image editor",                   "org.gimp.GIMP"),
        ("Inkscape",     "inkscape",             "Vector editor",                  "org.inkscape.Inkscape"),
        ("Blender",      "blender",              "3D creation suite",              "org.blender.Blender"),
        ("Krita",        "krita",                "Digital painting",               "org.kde.krita"),
        ("darktable",    "darktable",            "RAW photo editor",               "org.darktable.Darktable"),
        ("RawTherapee",  "rawtherapee",          "RAW processing",                 "com.rawtherapee.RawTherapee"),
    ],
    "3D & Animation": [
        ("Blender",      "blender",              "3D creation & animation",        "org.blender.Blender"),
        ("FreeCAD",      "freecad",              "Parametric 3D modeling",         "org.freecadweb.FreeCAD"),
        ("OpenSCAD",     "openscad",             "Programmatic 3D modeling",       "org.openscad.OpenSCAD"),
        ("MeshLab",      "meshlab",              "3D mesh processing",             "net.meshlab.MeshLab"),
    ],
    "Writing & Publishing": [
        ("LibreOffice Writer","libreoffice-writer","Word processor",                "org.libreoffice.LibreOffice"),
        ("Scribus",      "scribus",              "Desktop publishing",             "net.scribus.Scribus"),
        ("Manuskript",   "manuskript",           "Novel writing",                  "io.github.olivierkes.manuskript"),
        ("Obsidian",     "obsidian",             "Knowledge management",           "md.obsidian.Obsidian"),
    ],
}


class StudioWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Studio")
        self.set_default_size(900, 680)
        self._build()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)

        hb = Adw.HeaderBar()
        hb.set_title_widget(Adw.WindowTitle(
            title="SynthOS Studio",
            subtitle="Creative Workstation"
        ))

        # JACK button
        jack_btn = Gtk.ToggleButton(label="🎵 JACK")
        jack_btn.set_tooltip_text("Toggle JACK audio server")
        jack_btn.connect("toggled", self._on_jack_toggle)
        hb.pack_start(jack_btn)

        outer.append(hb)

        # Category tabs
        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(16); box.set_margin_bottom(16)
        box.set_margin_start(24); box.set_margin_end(24)
        scroll.set_child(box)
        outer.append(scroll)

        # Studio profile banner
        banner = Adw.Banner(
            title="Studio Mode: Low-latency kernel settings and realtime audio are active.",
            revealed=self._is_studio_mode_active()
        )
        outer.append(banner)

        for category, tools in TOOLS.items():
            grp = Adw.PreferencesGroup(title=category)
            for label, binary, desc, flatpak_id in tools:
                row = Adw.ActionRow(title=label, subtitle=desc)

                # Check availability
                is_available = bool(shutil.which(binary)) or \
                               (flatpak_id and self._is_flatpak(flatpak_id))

                if is_available:
                    launch_btn = Gtk.Button(label="Launch")
                    launch_btn.add_css_class("flat")
                    launch_btn.set_valign(Gtk.Align.CENTER)
                    launch_btn.connect("clicked", lambda _, b=binary, fid=flatpak_id:
                        self._launch(b, fid))
                    row.add_suffix(launch_btn)
                else:
                    install_btn = Gtk.Button(label="Install")
                    install_btn.set_valign(Gtk.Align.CENTER)
                    install_btn.connect("clicked", lambda _, fid=flatpak_id, b=binary:
                        self._install(fid, b))
                    row.add_suffix(install_btn)
                    row.add_css_class("dim-label")

                grp.add(row)
            box.append(grp)

        # Status bar
        self._status = Gtk.Label(label="")
        self._status.set_xalign(0)
        self._status.set_margin_start(12)
        self._status.set_margin_bottom(4)
        self._status.add_css_class("dim-label")
        outer.append(self._status)

    def _is_flatpak(self, app_id):
        return subprocess.run(["flatpak","info",app_id],
                              capture_output=True, timeout=3).returncode == 0

    def _is_studio_mode_active(self):
        r = subprocess.run(["systemctl","--user","is-active","--quiet","jack.service"],
                           capture_output=True)
        return r.returncode == 0

    def _launch(self, binary, flatpak_id):
        if shutil.which(binary):
            subprocess.Popen([binary])
        elif flatpak_id:
            subprocess.Popen(["flatpak","run",flatpak_id])

    def _install(self, flatpak_id, binary):
        if flatpak_id:
            self._status.set_label(f"Installing {flatpak_id}…")
            import threading
            threading.Thread(
                target=lambda: subprocess.run(
                    ["flatpak","install","--noninteractive","-y",flatpak_id],
                    timeout=300
                ),
                daemon=True
            ).start()
        else:
            self._status.set_label(f"Use: sudo dnf install {binary}")

    def _on_jack_toggle(self, btn):
        action = "start" if btn.get_active() else "stop"
        subprocess.Popen(["systemctl","--user", action,"jack.service"],
                         stderr=subprocess.DEVNULL)
        self._status.set_label(
            "JACK audio server started" if btn.get_active() else "JACK stopped"
        )


class StudioApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: StudioWindow(a).present())

if __name__ == "__main__":
    StudioApp().run(sys.argv)
