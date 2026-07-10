#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Welcome App — shown after first login

import sys, os, subprocess, json
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1")
from gi.repository import Gtk, Adw, GLib, Gio

APP_ID  = "org.synthos.Welcome"
VERSION = "2026.10"
STATE_FILE = os.path.expanduser("~/.config/synthex-welcome-done")

TIPS = [
    ("🎮","GameMode","Press Super+G to toggle GameMode for instant gaming performance."),
    ("🎨","Themes","Open Control Center → Appearance to switch between SynthOS themes."),
    ("📦","Apps","Use App Manager or Software Center to install thousands of apps via Flatpak & DNF."),
    ("🔒","Security","The Security Dashboard monitors your firewall, updates, and system hardening."),
    ("🖥️","Multi-Monitor","Drag displays in System Settings → Display to arrange your setup."),
    ("⌨️","Shortcuts","Super key opens the app launcher. Super+T opens the terminal."),
    ("📸","Snapshots","BTRFS snapshots run automatically. Open Disk Health to manage them."),
    ("🤖","AI Assistant","Click the AI icon in the panel to get help from your local SynthOS assistant."),
]

def launch(cmd):
    try: subprocess.Popen(cmd)
    except Exception: pass


class WelcomePage(Gtk.Box):
    def __init__(self, nav_view):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._nav = nav_view
        self._build()

    def _build(self):
        # Big hero section
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        hero.set_valign(Gtk.Align.CENTER)
        hero.set_vexpand(True)
        hero.set_margin_top(60)

        logo = Gtk.Image.new_from_icon_name("synthex")
        logo.set_pixel_size(128)
        hero.append(logo)

        title = Gtk.Label()
        title.set_markup(f'<span font="40" weight="bold" color="#B8D4FF">SynthOS</span>')
        hero.append(title)

        subtitle = Gtk.Label()
        subtitle.set_markup(
            f'<span font="18" color="#8899AA">Your Desktop, Illuminated</span>'
        )
        hero.append(subtitle)

        ver = Gtk.Label(label=f"Version {VERSION}  ·  Ignition Release")
        ver.add_css_class("dim-label")
        hero.append(ver)

        self.append(hero)

        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.set_margin_top(32)
        btn_box.set_margin_bottom(40)

        setup_btn = Gtk.Button(label="Set Up My Desktop")
        setup_btn.add_css_class("suggested-action")
        setup_btn.add_css_class("pill")
        setup_btn.connect("clicked", lambda _: self._go_next("setup"))
        btn_box.append(setup_btn)

        tips_btn = Gtk.Button(label="Explore Tips & Tricks")
        tips_btn.add_css_class("pill")
        tips_btn.connect("clicked", lambda _: self._go_next("tips"))
        btn_box.append(tips_btn)

        skip_btn = Gtk.Button(label="Skip")
        skip_btn.add_css_class("flat")
        skip_btn.connect("clicked", lambda _: self._go_next("skip"))
        btn_box.append(skip_btn)

        self.append(btn_box)

    def _go_next(self, which):
        if which == "skip":
            self._mark_done()
            Gtk.main_quit()
        elif which == "setup":
            self._nav.push(SetupPage(self._nav))
        elif which == "tips":
            self._nav.push(TipsPage(self._nav))

    def _mark_done(self):
        open(STATE_FILE, "w").close()


class SetupPage(Adw.NavigationPage):
    def __init__(self, nav_view):
        super().__init__(title="Set Up My Desktop")
        self._nav = nav_view
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(box)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        box.append(scroll)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(24); inner.set_margin_end(24)
        scroll.set_child(inner)

        setup_items = [
            ("🎨","Choose Theme",       "Pick your SynthOS color theme and wallpaper",
             lambda: launch(["systemsettings5","kcm_lookandfeel"])),
            ("📦","Install Apps",       "Add applications from the Software Center",
             lambda: launch(["/usr/lib/synthex/synthex-software-center"])),
            ("🌐","Set Up Network",     "Configure Wi-Fi, VPN and connections",
             lambda: launch(["nm-connection-editor"])),
            ("🔒","Security Check",    "Review and harden your system security",
             lambda: launch(["/usr/lib/synthex/synthex-security-dashboard"])),
            ("🎮","Gaming Setup",      "Install Steam, GameMode and GPU drivers",
             lambda: launch(["/usr/lib/synthex/synthex-gaming-center"])),
            ("💾","Connect Accounts",  "Link cloud services and sync calendars",
             lambda: launch(["systemsettings5","kcm_kaccounts"])),
        ]

        for icon, title, desc, action in setup_items:
            group = Adw.PreferencesGroup()
            row = Adw.ActionRow(title=f"{icon} {title}", subtitle=desc)
            btn = Gtk.Button(label="Open →")
            btn.add_css_class("flat")
            btn.set_valign(Gtk.Align.CENTER)
            btn.connect("clicked", lambda _, a=action: a())
            row.add_suffix(btn)
            group.add(row)
            inner.append(group)

        done_btn = Gtk.Button(label="All Done!")
        done_btn.add_css_class("suggested-action")
        done_btn.add_css_class("pill")
        done_btn.set_halign(Gtk.Align.CENTER)
        done_btn.set_margin_top(8)
        done_btn.connect("clicked", lambda _: self._finish())
        inner.append(done_btn)

    def _finish(self):
        open(STATE_FILE, "w").close()
        self._nav.push(TipsPage(self._nav))


class TipsPage(Adw.NavigationPage):
    def __init__(self, nav_view):
        super().__init__(title="Tips & Tricks")
        self._nav = nav_view
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(box)

        scroll = Gtk.ScrolledWindow(); scroll.set_vexpand(True)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        inner.set_margin_top(20); inner.set_margin_bottom(20)
        inner.set_margin_start(24); inner.set_margin_end(24)
        scroll.set_child(inner)
        box.append(scroll)

        hdr = Gtk.Label()
        hdr.set_markup('<span size="large" weight="bold">Tips &amp; Tricks</span>')
        hdr.set_xalign(0)
        inner.append(hdr)

        for emoji, title, text in TIPS:
            grp = Adw.PreferencesGroup()
            row = Adw.ActionRow(title=f"{emoji}  {title}", subtitle=text)
            grp.add(row)
            inner.append(grp)

        close_btn = Gtk.Button(label="Start Using SynthOS")
        close_btn.add_css_class("suggested-action")
        close_btn.add_css_class("pill")
        close_btn.set_halign(Gtk.Align.CENTER)
        close_btn.set_margin_top(12)
        close_btn.connect("clicked", lambda _: (open(STATE_FILE,"w").close(), Gtk.main_quit()))
        inner.append(close_btn)


class WelcomeWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=f"Welcome to SynthOS {VERSION}")
        self.set_default_size(760, 580)
        nav = Adw.NavigationView()
        page = Adw.NavigationPage(title="Welcome")
        page.set_child(WelcomePage(nav))
        nav.push(page)
        self.set_content(nav)


class WelcomeApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.connect("activate", self._on_activate)

    def _on_activate(self, _):
        # If already completed, don't show again (unless --force)
        if os.path.exists(STATE_FILE) and "--force" not in sys.argv:
            sys.exit(0)
        WelcomeWindow(self).present()


if __name__ == "__main__":
    app = WelcomeApp()
    sys.exit(app.run(sys.argv))
