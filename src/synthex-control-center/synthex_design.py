#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Synthex Design System — professional widget toolkit for SynthOS Settings
A GNOME-Settings/KDE-SystemSettings-inspired component library:
adaptive cards that follow the system theme, inset list rows with hover
states, refined typography, status badges, and data-driven row builders
(toggle / combo / spin / slider / entry / button) bound to real backends.

Every surface adapts to light & dark themes automatically by deriving
colors from GTK theme colors with alpha() overlays.
"""

import os
import subprocess
from gi.repository import Gtk, Gdk, GLib, Pango

# ── Design tokens ────────────────────────────────────────────────────────────

PAD_PAGE = 28        # outer page margin
PAD_CARD = 2        # card inner border padding
PAD_ROW = 14        # row vertical rhythm
GAP_CARD = 26       # gap between cards
GAP_ROW = 2         # gap between rows inside a card
CONTENT_WIDTH = 760  # max width of the settings column (centered)

_CSS = """
/* ══════════════════════════════════════════════════════════════════════════
   Synthex Control Center — Native Desktop Design System (HIG Compliant)
   Clean typography, grouped inset list rows, native switch proportions.
   ══════════════════════════════════════════════════════════════════════════ */

.settings-window {
  font-family: system-ui, -apple-system, "Inter", "Cantarell", "Ubuntu", "Segoe UI", sans-serif;
  background-color: @theme_base_color;
  color: @theme_fg_color;
}

/* ── Switches: Clean Native Proportions ───────────────────────────────── */
switch {
  border-radius: 12px;
  min-width: 44px;
  min-height: 24px;
  background-color: alpha(@theme_fg_color, 0.14);
  background-image: none;
  border: 1px solid alpha(@theme_fg_color, 0.08);
  outline-style: none;
  transition: background-color 150ms ease, border-color 150ms ease;
}
switch:checked {
  background-color: #3584e4;
  border-color: #3584e4;
}
switch:disabled { opacity: 0.35; }
switch slider {
  min-width: 18px;
  min-height: 18px;
  margin: 2px;
  border: none;
  border-radius: 50%;
  background-color: #ffffff;
  box-shadow: 0 1px 2px alpha(black, 0.25);
  transition: all 150ms ease;
}

/* ── Sliders ─────────────────────────────────────────────────────────── */
.scale-ok trough, scale trough {
  min-height: 4px;
  border-radius: 2px;
  background-color: alpha(@theme_fg_color, 0.12);
  outline-style: none;
}
.scale-ok highlight, scale highlight {
  border-radius: 2px;
  min-height: 4px;
  background-color: #3584e4;
}
.scale-ok slider, scale slider {
  min-width: 16px;
  min-height: 16px;
  margin: -6px;
  border-radius: 50%;
  background-color: #ffffff;
  border: 1px solid alpha(black, 0.15);
  box-shadow: 0 1px 3px alpha(black, 0.20);
  background-image: none;
}
.scale-ok slider:hover, scale slider:hover {
  box-shadow: 0 2px 6px alpha(black, 0.35);
}


/* ── Check / Radio ───────────────────────────────────────────────────── */
checkbutton check {
  min-width: 18px;
  min-height: 18px;
  border-radius: 4px;
  border: 1.5px solid alpha(@theme_fg_color, 0.28);
  background-color: transparent;
  transition: all 120ms ease;
}
checkbutton check:checked {
  background-color: #3584e4;
  border-color: #3584e4;
}
radiobutton radio {
  min-width: 18px;
  min-height: 18px;
  border-radius: 50%;
  border: 1.5px solid alpha(@theme_fg_color, 0.28);
  transition: all 120ms ease;
}
radiobutton radio:checked { border-color: #3584e4; }

/* ── Controls (Combo, Entry, Spin) ───────────────────────────────────── */
spinbutton {
  border-radius: 6px;
  border: 1px solid alpha(@theme_fg_color, 0.12);
  background-color: alpha(@theme_fg_color, 0.05);
  padding: 2px 6px;
}
spinbutton entry { border: none; background: transparent; }

.combo-compact button {
  background-color: alpha(@theme_fg_color, 0.06);
  border: 1px solid alpha(@theme_fg_color, 0.12);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 9pt;
  font-weight: 500;
  background-image: none;
  transition: background-color 120ms ease;
  outline-style: none;
}
.combo-compact button:hover { background-color: alpha(@theme_fg_color, 0.10); }

.entry-clean, entry {
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.12);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 9.5pt;
  box-shadow: none;
  outline-style: none;
  transition: border-color 150ms ease;
}
.entry-clean:focus, entry:focus {
  border-color: #3584e4;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
button { outline-style: none; }

.btn-quiet {
  background-color: alpha(@theme_fg_color, 0.06);
  border: 1px solid alpha(@theme_fg_color, 0.10);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 9pt;
  font-weight: 500;
}
.btn-quiet:hover { background-color: alpha(@theme_fg_color, 0.11); }
.btn-quiet:active { background-color: alpha(@theme_fg_color, 0.16); }

.btn-primary {
  background-color: #3584e4;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  font-size: 9pt;
  font-weight: 600;
  box-shadow: 0 1px 2px alpha(black, 0.15);
}
.btn-primary:hover { background-color: #2a76d2; }
.btn-primary:active { background-color: #2163b3; }
.btn-primary:disabled { opacity: 0.45; }

.btn-warn, .btn-destructive {
  color: #ef4444;
  background-color: alpha(#ef4444, 0.08);
  border: 1px solid alpha(#ef4444, 0.28);
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 9pt;
  font-weight: 500;
}
.btn-warn:hover, .btn-destructive:hover { background-color: alpha(#ef4444, 0.16); }

/* ── Headerbar & Search ──────────────────────────────────────────────── */
headerbar {
  background-image: none;
  background-color: @theme_base_color;
  border-bottom: 1px solid alpha(@theme_fg_color, 0.08);
  box-shadow: none;
}
.app-title {
  font-size: 11.5pt;
  font-weight: 700;
}
.settings-search {
  border-radius: 6px;
  padding: 6px 12px;
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.10);
  font-size: 9.5pt;
  outline-style: none;
}
.settings-search:focus {
  border-color: #3584e4;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
.sidebar, .sidebar-scroll { background-color: transparent; }
.sidebar {
  background-color: alpha(@theme_fg_color, 0.02);
  border-right: 1px solid alpha(@theme_fg_color, 0.08);
}
.sidebar-item {
  border-radius: 6px;
  margin: 1px 8px;
  padding: 6px 10px;
  transition: background-color 100ms ease;
  outline-style: none;
}
.sidebar-item:hover { background-color: alpha(@theme_fg_color, 0.06); }
.sidebar-item:selected {
  background-color: #3584e4;
  color: #ffffff;
}
.sidebar-item:selected .sidebar-title { color: #ffffff; font-weight: 600; }
.sidebar-item:selected image { color: #ffffff; }

.sidebar-title { font-size: 9.5pt; font-weight: 500; }
.sidebar-group {
  font-size: 7.5pt;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: alpha(@theme_fg_color, 0.40);
  padding: 14px 16px 4px 16px;
}
.sidebar-sep { background-color: transparent; }

/* ── Content & Grouped Inset Cards ───────────────────────────────────── */
.content-scroll { background-color: @theme_base_color; }
.content-column { margin: 0 4px; }

.page-header { padding: 4px 6px 12px 6px; }
.page-title { font-size: 17pt; font-weight: 700; }
.page-subtitle { font-size: 9.5pt; color: alpha(@theme_fg_color, 0.55); padding-top: 3px; }

.card {
  background-color: alpha(@theme_fg_color, 0.035);
  border-radius: 10px;
  border: 1px solid alpha(@theme_fg_color, 0.08);
  box-shadow: none;
}
.card-dark {
  background-color: alpha(@theme_fg_color, 0.055);
  border-radius: 10px;
  border: 1px solid alpha(@theme_fg_color, 0.08);
}
.card-padding { padding: 2px; }

.section-title-box { padding: 8px 6px 6px 6px; }
.section-title {
  font-size: 9.5pt;
  font-weight: 600;
  color: alpha(@theme_fg_color, 0.65);
}
.section-sub { font-size: 8.5pt; color: alpha(@theme_fg_color, 0.45); padding-top: 1px; }

.row {
  padding: 10px 14px;
  border-radius: 0;
  transition: background-color 100ms ease;
  outline-style: none;
}
.row:hover { background-color: alpha(@theme_fg_color, 0.035); }
.row-title { font-size: 9.5pt; font-weight: 500; }
.row-sub { font-size: 8.5pt; color: alpha(@theme_fg_color, 0.50); padding-top: 2px; }
.row-sep {
  background-color: alpha(@theme_fg_color, 0.06);
  min-height: 1px;
}

/* ── Badges ──────────────────────────────────────────────────────────── */
.badge {
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 8pt;
  font-weight: 600;
}
.badge-ok { background-color: alpha(#10b981, 0.13); color: #10b981; }
.badge-warn { background-color: alpha(#f59e0b, 0.13); color: #f59e0b; }
.badge-err { background-color: alpha(#ef4444, 0.13); color: #ef4444; }
.badge-neutral { background-color: alpha(@theme_fg_color, 0.08); color: alpha(@theme_fg_color, 0.65); }

.dot { border-radius: 50%; min-width: 8px; min-height: 8px; padding: 0; }
.dot-ok { background-color: #10b981; }
.dot-warn { background-color: #f59e0b; }
.dot-err { background-color: #ef4444; }
.dot-off { background-color: alpha(@theme_fg_color, 0.25); }

/* ── Info Grid ───────────────────────────────────────────────────────── */
.info-key { font-size: 9pt; color: alpha(@theme_fg_color, 0.50); }
.info-val { font-size: 9pt; font-weight: 500; }

/* ── Toast ───────────────────────────────────────────────────────────── */
.toast {
  background-color: #1e2129;
  color: #f3f4f6;
  border: 1px solid alpha(white, 0.12);
  border-radius: 8px;
  padding: 10px 18px;
  font-size: 9pt;
  font-weight: 500;
  box-shadow: 0 4px 16px alpha(black, 0.35);
}
.toast-error { background-color: #7f1d1d; color: #ffffff; }

/* ── Progress ────────────────────────────────────────────────────────── */
.pbar-ok trough {
  min-height: 4px;
  border-radius: 2px;
  background-color: alpha(@theme_fg_color, 0.08);
}
.pbar-ok progress {
  border-radius: 2px;
  min-height: 4px;
  background-color: #3584e4;
}

/* ── Entity Cards ────────────────────────────────────────────────────── */
.entity-card {
  background-color: alpha(@theme_fg_color, 0.03);
  border: 1px solid alpha(@theme_fg_color, 0.07);
  border-radius: 8px;
  padding: 10px 14px;
  transition: background-color 100ms ease;
}
.entity-card:hover {
  background-color: alpha(@theme_fg_color, 0.05);
}
.entity-title { font-size: 9.5pt; font-weight: 600; }

.entity-sub { font-size: 8.5pt; color: alpha(@theme_fg_color, 0.50); }

.empty-state {
  color: alpha(@theme_fg_color, 0.40);
  font-size: 9pt;
  padding: 20px;
}

/* ── Spinner / Loading ───────────────────────────────────────────────── */
spinner { color: #3584e4; }
.async-loading { padding: 4px; }

/* ── Lists inside Cards ──────────────────────────────────────────────── */
.card list, .card listbox {
  background-color: transparent;
  border: none;
}
list row { outline-style: none; }
"""


def install_design(window):
    """Attach the design-system CSS to a window (and all its children)."""
    provider = Gtk.CssProvider()
    provider.load_from_data(_CSS.encode("utf-8"))
    style = window.get_style_context()
    style.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    window.get_style_context().add_class("settings-window")



# ── Builder helpers ──────────────────────────────────────────────────────────

def label(text, css_class=None, xalign=0, wrap=True, **kw):
    l = Gtk.Label(label=text, xalign=xalign, wrap=wrap, **kw)
    if css_class:
        l.get_style_context().add_class(css_class)
    l.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    if wrap:
        # Cap natural width so long subtitles cannot stretch the column
        l.set_width_chars(30)
        l.set_max_width_chars(48)
    return l


def button(text, css="btn-quiet", clicked=None, tooltip=None):
    b = Gtk.Button.new_with_label(text)
    b.get_style_context().add_class(css)
    if tooltip:
        b.set_tooltip_text(tooltip)
    if clicked:
        b.connect("clicked", clicked)
    b.set_focus_on_click(False)
    return b


def badge(text, kind="neutral"):
    b = Gtk.Label(label=text)
    b.get_style_context().add_class("badge")
    b.get_style_context().add_class(f"badge-{kind}")
    return b


def dot(kind):
    d = Gtk.Box()
    d.get_style_context().add_class("dot")
    d.get_style_context().add_class(f"dot-{kind}")
    d.set_size_request(9, 9)
    return d


PAGE_ICONS = {
    "Appearance": "preferences-desktop-theme", "Backgrounds": "preferences-desktop-wallpaper",
    "Night Light": "night-light", "Notifications": "preferences-desktop-notification",
    "Privacy Center": "preferences-system-privacy", "SpoofGoof Shield": "network-vpn",
    "Online Accounts": "applications-internet", "Language & Region": "cs-language",
    "Account Details": "avatar-default", "Accessibility": "preferences-desktop-accessibility",
    "Installed Apps": "preferences-desktop-applications", "Desktop": "cs-desktop",
    "Windows": "preferences-system-windows", "Workspaces": "view-grid",
    "Panels": "cs-panel", "Applets": "preferences-plugin",
    "Desklets": "preferences-desktop-widgets", "Extensions": "application-x-extension",
    "Gestures": "input-touchpad", "Preferred Applications": "preferences-desktop-default-applications",
    "Startup Applications": "preferences-session", "Screen Lock & Saver": "system-lock-screen",
    "Display": "preferences-desktop-display", "Sound": "multimedia-volume-control",
    "Mouse & Touchpad": "input-mouse", "Keyboard": "preferences-desktop-keyboard",
    "Graphics Tablet": "input-tablet", "Printers & Scanners": "cs-printer",
    "Bluetooth": "bluetooth", "Thunderbolt": "thunderbolt", "Color": "preferences-color",
    "Power Management": "preferences-system-power", "Storage & Disks": "drive-harddisk",
    "Drivers": "applications-science", "Gaming": "applications-games",
    "Cameras & Gamepads": "camera-video", "Network": "preferences-system-network",
    "Aegis Security Center": "security-high", "Security": "security-high",
    "System Doctor": "applications-engineering", "Software Sources": "package-x-generic",
    "Update Manager": "system-software-update", "Timeshift": "timebench",
    "Login Window": "cs-user", "Date & Time": "preferences-system-time",
    "System Information": "dialog-information", "Users & Groups": "system-users",
}


class PageHeader(Gtk.Box):
    """Clean native desktop page header: icon + title + subtitle + badges."""
    def __init__(self, title, subtitle="", badges=None, icon_name=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.get_style_context().add_class("page-header")
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        icon_name = icon_name or PAGE_ICONS.get(title)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
            img.set_pixel_size(28)
            img.set_valign(Gtk.Align.CENTER)
            top.pack_start(img, False, False, 0)

        top.pack_start(label(title, "page-title", wrap=False), False, False, 0)
        for text, kind in (badges or []):
            top.pack_end(badge(text, kind), False, False, 0)
        self.pack_start(top, False, False, 0)
        if subtitle:
            self.pack_start(label(subtitle, "page-subtitle"), False, False, 0)


class Section(Gtk.Frame):
    """Grouped inset preferences section (Libadwaita style)."""
    def __init__(self, title=None, subtitle=None):
        super().__init__(shadow_type=Gtk.ShadowType.NONE)
        self.get_style_context().add_class("card")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.set_border_width(0)
        self.add(outer)
        if title:
            tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            tb.get_style_context().add_class("section-title-box")
            tb.pack_start(label(title, "section-title"), False, False, 0)
            if subtitle:
                tb.pack_start(label(subtitle, "section-sub"), False, False, 0)
            outer.pack_start(tb, False, False, 0)
        self.rows = Gtk.ListBox()
        self.rows.set_selection_mode(Gtk.SelectionMode.NONE)
        self.rows.get_style_context().add_class("card-padding")

        outer.pack_start(self.rows, False, False, 0)
        self._count = 0

    def add_row(self, child):
        row = Gtk.ListBoxRow(selectable=False, activatable=False)
        row.get_style_context().add_class("row")
        if self._count:
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.get_style_context().add_class("row-sep")
            self.rows.add(sep)
        self.rows.add(row)
        row.add(child)
        self._count += 1
        return row

    def add_widget(self, widget):
        """Full-card custom widget (progress areas, canvases, lists)."""
        outer = self.get_child()
        w = Gtk.Box(border_width=10)
        w.pack_start(widget, True, True, 0)
        outer.pack_start(w, False, False, 0)
        return w


class Row(Gtk.Box):
    """A single setting row: [icon] title/subtitle ......... [control]."""
    def __init__(self, title, subtitle="", icon_name=None, control=None, suffix=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        if icon_name:
            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
            img.set_opacity(0.8)
            self.pack_start(img, False, False, 0)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        text.pack_start(label(title, "row-title"), False, False, 0)
        if subtitle:
            text.pack_start(label(subtitle, "row-sub"), False, False, 0)
        self.pack_start(text, True, True, 0)
        if suffix is not None:
            self.pack_start(suffix, False, False, 0)
        if control is not None:
            self.pack_start(control, False, False, 0)


# ── Data-driven control rows (bound to real getters/setters) ────────────────

def _noop(*a):
    pass


def toggle_row(title, subtitle="", icon=None, get=None, set_=None, on_change=None):
    """Switch row. get()->bool, set_(bool)."""
    sw = Gtk.Switch()
    sw.set_valign(Gtk.Align.CENTER)
    if get:
        sw.set_active(bool(get()))
    sw.connect("state-set", lambda b, st: ((set_ or _noop)(st), (on_change or _noop)(st)) and None or True)
    return Row(title, subtitle, icon, control=sw), sw


def combo_row(title, options, subtitle="", icon=None, get=None, set_=None,
              on_change=None, width_chars=18):
    """Combobox row. options=[(value,label),...], get()->value, set_(value)."""
    store = Gtk.ListStore(str, str)
    for val, name in options:
        store.append([str(val), name])
    cb = Gtk.ComboBox.new_with_model(store)
    cb.set_valign(Gtk.Align.CENTER)
    rt = Gtk.CellRendererText()
    cb.pack_start(rt, True)
    cb.add_attribute(rt, "text", 1)
    cb.get_style_context().add_class("combo-compact")
    current = str(get()) if get else ""
    active_idx = 0
    for i, (val, _n) in enumerate(options):
        if str(val) == current:
            active_idx = i
            break
    cb.set_active(active_idx)
    cb.connect("changed", lambda c: ((set_ or _noop)(options[c.get_active()][0]),
                                     (on_change or _noop)(options[c.get_active()][0])) if c.get_active() >= 0 else None)
    return Row(title, subtitle, icon, control=cb), cb


def spin_row(title, lo, hi, step=1, subtitle="", icon=None, get=None, set_=None,
             on_change=None, unit="", digits=0):
    """Spinbutton row with live apply + numeric subtitle display."""
    adj = Gtk.Adjustment(value=float(get() if get else lo), lower=lo, upper=hi, step_increment=step)
    sp = Gtk.SpinButton(adjustment=adj, climb_rate=1.0, digits=digits)
    sp.set_valign(Gtk.Align.CENTER)
    sp.set_width_chars(6)
    sp.connect("value-changed", lambda s: ((set_ or _noop)(s.get_value()),
                                           (on_change or _noop)(s.get_value())))

    def with_unit():
        return Row(title, f"{subtitle}{' · ' + unit if unit else ''}".strip(" ·"), icon, control=sp)
    return with_unit(), sp


def slider_row(title, lo, hi, subtitle="", icon=None, get=None, set_=None,
               on_change=None, digits=2, width=220):
    adj = Gtk.Adjustment(value=float(get() if get else lo), lower=lo, upper=hi, step_increment=(hi - lo) / 100.0)
    sc = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
    sc.set_valign(Gtk.Align.CENTER)
    sc.set_size_request(width, -1)
    sc.set_draw_value(False)
    sc.set_digits(digits)
    sc.get_style_context().add_class("scale-ok")
    sc.connect("value-changed", lambda s: (set_ or _noop)(round(s.get_value(), 3)))

    def _on_release(w, ev):
        if on_change:
            on_change(w.get_value())
        return False
    sc.connect("button-release-event", _on_release)
    return Row(title, subtitle, icon, control=sc), sc


def entry_row(title, subtitle="", icon=None, get=None, set_=None, on_change=None,
              width_chars=24, button_text="Apply"):
    """Text entry + apply button row."""
    e = Gtk.Entry()
    e.get_style_context().add_class("entry-clean")
    e.set_width_chars(width_chars)
    e.set_valign(Gtk.Align.CENTER)
    if get:
        e.set_text(str(get()))
    btn = button(button_text, "btn-primary", clicked=lambda b: (set_ or _noop)(e.get_text()))

    def _enter(w):
        (set_ or _noop)(e.get_text())
        if on_change:
            on_change(e.get_text())
    e.connect("activate", _enter)
    return Row(title, subtitle, icon, control=btn, suffix=e), e


def buttons_row(title, subtitle="", icon=None, buttons=()):
    """Row with several trailing action buttons. buttons=[(label,css,cb,tooltip)]"""
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for spec in buttons:
        lbl, css, cb = spec[0], spec[1], spec[2]
        tip = spec[3] if len(spec) > 3 else None
        box.pack_start(button(lbl, css, cb, tip), False, False, 0)
    return Row(title, subtitle, icon, control=box)


def info_grid(pairs):
    """Professional key-value table for system info pages."""
    grid = Gtk.Grid()
    grid.get_style_context().add_class("info-grid")
    for i, (k, v) in enumerate(pairs):
        grid.attach(label(k, "info-key"), 0, i, 1, 1)
        val = label(str(v), "info-val")
        val.set_selectable(True)
        val.set_hexpand(True)
        grid.attach(val, 1, i, 1, 1)
    return grid


class ContentColumn(Gtk.Box):
    """Centered, exactly-width-constrained settings column for every page.

    Viewports force full-width allocation onto children, so halign, spacers
    and Gtk.Alignment all fail to center reliably. This subclass settles it
    deterministically in do_size_allocate: the inner column always receives
    exactly min(max_width, available) pixels, centered."""
    __gtype_name__ = "SynthexContentColumn"

    def __init__(self, max_width=CONTENT_WIDTH):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._max_width = max_width
        self._column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=GAP_CARD)
        self._column.set_border_width(PAD_PAGE)
        self.pack_start(self._column, True, True, 0)

    def do_size_allocate(self, allocation):
        Gtk.Box.do_size_allocate(self, allocation)
        w = min(self._max_width, allocation.width)
        rect = Gdk.Rectangle()
        rect.x = max(0, (allocation.width - w) // 2)
        rect.y = 0
        rect.width = w
        rect.height = allocation.height
        self._column.size_allocate(rect)
        import os as _os
        if _os.environ.get("SYNTHEX_LAYOUT_DEBUG"):
            with open("/tmp/layout_debug.log", "a") as _f:
                _f.write(f"alloc w={allocation.width} → column {rect.x}+{rect.width}\n")

    def add(self, w):
        self._column.pack_start(w, False, False, 0)

    def add_expand(self, w):
        self._column.pack_start(w, True, True, 0)


class AsyncSection(Gtk.Frame):
    """A Section card whose data loads in a background thread.
    Shows a subtle progress row immediately, then swaps in real content.
    loader() -> payload; renderer(payload, section) -> None (adds rows)."""
    def __init__(self, title=None, subtitle=None, loader=None, renderer=None, on_error=None):
        super().__init__(shadow_type=Gtk.ShadowType.NONE)
        self.get_style_context().add_class("card")
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=GAP_ROW)
        outer.set_border_width(PAD_CARD)
        self.add(outer)
        if title:
            tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            tb.get_style_context().add_class("section-title-box")
            tb.pack_start(label(title.upper(), "section-title"), False, False, 0)
            if subtitle:
                tb.pack_start(label(subtitle, "section-sub"), False, False, 0)
            outer.pack_start(tb, False, False, 0)
        self.outer = outer
        self.spinner_row = Gtk.Box(spacing=10, border_width=12)
        sp = Gtk.Spinner()
        sp.start()
        self.spinner_row.pack_start(sp, False, False, 0)
        self.spinner_row.pack_start(label("Loading…", "row-sub"), False, False, 0)
        outer.pack_start(self.spinner_row, True, True, 0)
        self.show_all()
        if loader:
            self.load(loader, renderer, on_error)

    def load(self, loader, renderer, on_error=None):
        import threading
        def work():
            try:
                payload = loader()
                GLib.idle_add(lambda p=payload: self._populate(p, renderer))
            except Exception as exc:
                err_msg = str(exc)
                GLib.idle_add(lambda e=err_msg: self._fail(e, on_error))
        threading.Thread(target=work, daemon=True).start()


    def _populate(self, payload, renderer):
        try:
            self.outer.remove(self.spinner_row)
            renderer(payload, self)
        except Exception:
            self.outer.remove(self.spinner_row)
            self.outer.pack_start(label("Could not display this section", "row-sub"), False, False, 0)
        self.show_all()
        return False

    def _fail(self, exc, on_error):
        self.outer.remove(self.spinner_row)
        if on_error:
            on_error(exc, self)
        else:
            self.outer.pack_start(label(f"Unavailable: {str(exc)[:80]}", "row-sub"), False, False, 0)
        self.show_all()
        return False

    def add_row(self, child):
        row = Gtk.ListBoxRow(selectable=False, activatable=False)
        row.get_style_context().add_class("row")
        row.add(child)
        w = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        w.get_style_context().add_class("card-padding")
        w.add(row)
        self.outer.pack_start(w, False, False, 0)
        return row


class Toast(Gtk.Revealer):
    """In-app transient notification (bottom of content column)."""
    def __init__(self):
        super().__init__(valign=Gtk.Align.END, halign=Gtk.Align.CENTER,
                         transition_type=Gtk.RevealerTransitionType.SLIDE_UP,
                         transition_duration=220)
        self.lbl = label("", None, xalign=0.5)
        box = Gtk.Box(border_width=4)
        box.get_style_context().add_class("toast")
        box.add(self.lbl)
        self.add(box)
        self.set_reveal_child(False)
        self._src = None

    def show_message(self, text, error=False, seconds=3):
        self.lbl.set_text(text)
        ctx = self.get_child().get_style_context()
        ctx.remove_class("toast-error")
        if error:
            ctx.add_class("toast-error")
        self.set_reveal_child(True)
        if self._src:
            GLib.source_remove(self._src)
        self._src = GLib.timeout_add_seconds(seconds, lambda: (self.set_reveal_child(False), False)[1])


def entity_card(title, subtitle="", icon_name=None, trailing=None, css="entity-card"):
    card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
    card.get_style_context().add_class(css)
    if icon_name:
        img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.DND)
        img.set_opacity(0.85)
        card.pack_start(img, False, False, 0)
    txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    txt.pack_start(label(title, "entity-title"), False, False, 0)
    if subtitle:
        txt.pack_start(label(subtitle, "entity-sub"), False, False, 0)
    card.pack_start(txt, True, True, 0)
    if trailing:
        if isinstance(trailing, (list, tuple)):
            tb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            for t in trailing:
                tb.pack_start(t, False, False, 0)
            card.pack_end(tb, False, False, 0)
        else:
            card.pack_end(trailing, False, False, 0)
    return card
