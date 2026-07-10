#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Locale Setup — region, language, format configurator

import sys, os, subprocess
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib

APP_ID = "org.synthos.LocaleSetup"


class LocaleWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Language & Region")
        self.set_default_size(680, 520)
        self._build()

    def _build(self):
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)
        outer.append(Adw.HeaderBar())

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        outer.append(scroll)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_margin_top(20); box.set_margin_bottom(20)
        box.set_margin_start(24); box.set_margin_end(24)
        scroll.set_child(box)

        # Language
        lang_group = Adw.PreferencesGroup(title="Language & Region")
        lang_row = Adw.ActionRow(title="System Language",
                                  subtitle="Requires re-login to apply")
        lang_btn = Gtk.Button(label="Change…")
        lang_btn.set_valign(Gtk.Align.CENTER)
        lang_btn.connect("clicked", lambda _: subprocess.Popen(
            ["systemsettings5", "kcm_translations"]
        ))
        lang_row.add_suffix(lang_btn)
        lang_group.add(lang_row)

        # Show current locale
        curr = subprocess.run(["localectl","status"],capture_output=True,text=True).stdout
        lang_val = next((l.split(":")[1].strip() for l in curr.splitlines()
                         if "System Locale" in l), "Unknown")
        curr_row = Adw.ActionRow(title="Current Locale", subtitle=lang_val)
        lang_group.add(curr_row)
        box.append(lang_group)

        # Timezone
        tz_group = Adw.PreferencesGroup(title="Timezone")
        tz_out = subprocess.run(["timedatectl","show","--property=Timezone","--value"],
                                capture_output=True,text=True).stdout.strip()
        tz_row = Adw.ActionRow(title="Timezone", subtitle=tz_out or "Unknown")
        tz_btn = Gtk.Button(label="Change…")
        tz_btn.set_valign(Gtk.Align.CENTER)
        tz_btn.connect("clicked", lambda _: subprocess.Popen(
            ["systemsettings5","kcm_clock"]
        ))
        tz_row.add_suffix(tz_btn)
        tz_group.add(tz_row)

        # NTP
        ntp_val = subprocess.run(["timedatectl","show","--property=NTP","--value"],
                                 capture_output=True,text=True).stdout.strip()
        ntp_row = Adw.ActionRow(title="Sync with Internet Time (NTP)")
        ntp_sw = Gtk.Switch()
        ntp_sw.set_active(ntp_val == "yes")
        ntp_sw.set_valign(Gtk.Align.CENTER)
        ntp_sw.connect("state-set", lambda sw, s:
            subprocess.run(["pkexec","timedatectl","set-ntp","1" if s else "0"])
            or False)
        ntp_row.add_suffix(ntp_sw)
        tz_group.add(ntp_row)
        box.append(tz_group)

        # Input method
        im_group = Adw.PreferencesGroup(title="Input Method")
        im_row = Adw.ActionRow(title="Input Method",
                                subtitle="Configure Fcitx5 / IBus for CJK/IME input")
        im_btn = Gtk.Button(label="Open…")
        im_btn.set_valign(Gtk.Align.CENTER)
        im_btn.connect("clicked", lambda _: subprocess.Popen(
            ["fcitx5-configtool"] if subprocess.run(
                ["which","fcitx5-configtool"],capture_output=True).returncode==0
            else ["ibus-setup"]
        ))
        im_row.add_suffix(im_btn)
        im_group.add(im_row)
        box.append(im_group)


class LocaleApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", lambda a: LocaleWindow(a).present())

if __name__ == "__main__":
    LocaleApp().run(sys.argv)
