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
   SynthOS Settings — Modern Design System
   Clean, sleek, libadwaita-inspired surfaces that adapt to any GTK theme.
   ══════════════════════════════════════════════════════════════════════════ */

.settings-window {
  font-family: Cantarell, "Noto Sans", "Inter", "Ubuntu", sans-serif;
}

/* ── Global controls restyle ─────────────────────────────────────────── */

/* Switches: modern pill toggles */
switch {
  border-radius: 999px;
  min-width: 46px;
  min-height: 24px;
  background-color: alpha(@theme_fg_color, 0.16);
  background-image: none;
  transition: all 180ms ease;
}
switch:checked { background-color: @theme_selected_bg_color; }
switch slider {
  min-width: 19px;
  min-height: 19px;
  margin: 2px;
  border: none;
  border-radius: 50%;
  background-color: @theme_base_color;
  box-shadow: 0 1px 3px alpha(black, 0.30);
  transition: all 180ms ease;
}
switch:checked slider { background-color: @theme_selected_fg_color; }
switch:disabled { opacity: 0.45; }

/* Sliders */
.scale-ok trough {
  min-height: 5px;
  border-radius: 3px;
  background-color: alpha(@theme_fg_color, 0.12);
}
.scale-ok highlight {
  border-radius: 3px;
  min-height: 5px;
  background-color: @theme_selected_bg_color;
}
.scale-ok slider {
  min-width: 18px;
  min-height: 18px;
  margin: -7px;
  border-radius: 50%;
  background-color: @theme_base_color;
  border: 2px solid @theme_selected_bg_color;
  box-shadow: 0 1px 4px alpha(black, 0.22);
}

/* Check & radio */
checkbutton check {
  min-width: 18px;
  min-height: 18px;
  border-radius: 6px;
  border: 2px solid alpha(@theme_fg_color, 0.30);
  background-color: transparent;
  transition: all 150ms ease;
}
checkbutton check:checked {
  background-color: @theme_selected_bg_color;
  border-color: @theme_selected_bg_color;
}
radiobutton radio {
  min-width: 18px;
  min-height: 18px;
  border-radius: 50%;
  border: 2px solid alpha(@theme_fg_color, 0.30);
  transition: all 150ms ease;
}
radiobutton radio:checked { border-color: @theme_selected_bg_color; }

/* Spin buttons */
spinbutton {
  border-radius: 9px;
  border: 1px solid alpha(@theme_fg_color, 0.12);
  background-color: alpha(@theme_fg_color, 0.04);
  padding: 0 2px;
}
spinbutton entry { border: none; background: transparent; }

/* Scrollbars: thin overlay-style */
scrollbar { background-color: transparent; }
scrollbar slider {
  min-width: 9px;
  min-height: 36px;
  border-radius: 999px;
  border: none;
  margin: 3px 2px;
  background-color: alpha(@theme_fg_color, 0.22);
  transition: background-color 150ms ease;
}
scrollbar slider:hover { background-color: alpha(@theme_fg_color, 0.40); }

/* Spinner */
spinner { color: @theme_selected_bg_color; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
.sidebar { background-color: alpha(@theme_fg_color, 0.028); }
.sidebar-scroll { background: transparent; }

.sidebar-item {
  border-radius: 9px;
  margin: 1px 10px;
  padding: 7px 10px;
  transition: all 150ms ease;
}
.sidebar-item:hover { background-color: alpha(@theme_fg_color, 0.06); }
.sidebar-item:active { background-color: alpha(@theme_fg_color, 0.10); }
.sidebar-item:selected {
  background-color: @theme_selected_bg_color;
  color: @theme_selected_fg_color;
}
.sidebar-item:selected .sidebar-title { color: @theme_selected_fg_color; }

.sidebar-title { font-size: 10pt; font-weight: 500; }
.sidebar-sub { font-size: 8.5pt; color: alpha(@theme_fg_color, 0.50); }

.sidebar-group {
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: alpha(@theme_fg_color, 0.38);
  padding: 16px 22px 6px 22px;
}

.sidebar-sep { background-color: alpha(@theme_fg_color, 0.09); min-width: 1px; }

/* ── Header bar ──────────────────────────────────────────────────────── */
.app-title { font-size: 13pt; font-weight: 700; letter-spacing: -0.01em; }

.settings-search {
  border-radius: 999px;
  padding: 6px 16px;
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.10);
  transition: all 160ms ease;
}
.settings-search:focus {
  border-color: @theme_selected_bg_color;
  box-shadow: 0 0 0 3px alpha(@theme_selected_bg_color, 0.18);
}

/* ── Content column ──────────────────────────────────────────────────── */
.content-scroll { background-color: @theme_base_color; }
.content-column { margin: 0 8px; }

/* ── Page header ─────────────────────────────────────────────────────── */
.page-header { padding: 2px 6px 6px 6px; }
.page-title {
  font-size: 20pt;
  font-weight: 700;
  letter-spacing: -0.015em;
}
.page-subtitle {
  font-size: 10pt;
  color: alpha(@theme_fg_color, 0.58);
  padding-top: 4px;
}

/* ── Cards / sections ────────────────────────────────────────────────── */
.card {
  background-color: alpha(@theme_fg_color, 0.035);
  border-radius: 16px;
  border: 1px solid alpha(@theme_fg_color, 0.08);
  box-shadow: 0 1px 2px alpha(black, 0.03), 0 6px 18px alpha(black, 0.035);
}
.card-dark {
  background-color: alpha(@theme_fg_color, 0.06);
  border-radius: 16px;
  border: 1px solid alpha(@theme_fg_color, 0.08);
}
.card-padding { padding: 6px 4px; }

.section-title-box { padding: 6px 10px 10px 10px; }
.section-title {
  font-size: 9.5pt;
  font-weight: 700;
  letter-spacing: 0.06em;
  color: alpha(@theme_fg_color, 0.62);
}
.section-sub {
  font-size: 9pt;
  color: alpha(@theme_fg_color, 0.48);
  padding-top: 2px;
}

/* ── Rows ────────────────────────────────────────────────────────────── */
.row {
  padding: 12px 12px;
  border-radius: 10px;
  transition: background-color 150ms ease;
}
.row:hover { background-color: alpha(@theme_fg_color, 0.045); }

.row-title { font-size: 10.5pt; font-weight: 500; }
.row-sub {
  font-size: 9pt;
  color: alpha(@theme_fg_color, 0.55);
  padding-top: 2px;
}

.row-sep { background-color: transparent; }

/* ── Buttons ─────────────────────────────────────────────────────────── */
.btn-quiet {
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 7px 16px;
  font-size: 9.5pt;
  font-weight: 600;
  transition: all 150ms ease;
}
.btn-quiet:hover { background-color: alpha(@theme_fg_color, 0.10); }
.btn-quiet:active { background-color: alpha(@theme_fg_color, 0.14); }

.btn-primary {
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.12),
    shade(@theme_selected_bg_color, 0.96));
  color: @theme_selected_fg_color;
  border: none;
  border-radius: 9px;
  padding: 8px 18px;
  font-size: 9.5pt;
  font-weight: 700;
  box-shadow: 0 2px 8px alpha(@theme_selected_bg_color, 0.35);
  transition: all 150ms ease;
}
.btn-primary:hover {
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.20),
    shade(@theme_selected_bg_color, 1.02));
  box-shadow: 0 3px 12px alpha(@theme_selected_bg_color, 0.45);
}
.btn-primary:active {
  background-image: none;
  background-color: shade(@theme_selected_bg_color, 0.90);
}
.btn-primary:disabled { opacity: 0.5; }

.btn-destructive {
  color: @error_color;
  background-color: alpha(@error_color, 0.06);
  border: 1px solid alpha(@error_color, 0.38);
  border-radius: 9px;
  padding: 7px 16px;
  font-size: 9.5pt;
  font-weight: 600;
  transition: all 150ms ease;
}
.btn-destructive:hover { background-color: alpha(@error_color, 0.14); }

/* ── Combo & entry ───────────────────────────────────────────────────── */
.combo-compact button {
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 6px 10px;
  font-size: 9.5pt;
  transition: all 150ms ease;
}
.combo-compact button:hover { background-color: alpha(@theme_fg_color, 0.10); }
.combo-compact button:checked { background-color: alpha(@theme_fg_color, 0.12); }

.entry-clean {
  background-color: alpha(@theme_fg_color, 0.04);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 6px 11px;
  font-size: 9.5pt;
  box-shadow: none;
  transition: all 160ms ease;
}
.entry-clean:focus {
  border-color: @theme_selected_bg_color;
  box-shadow: 0 0 0 3px alpha(@theme_selected_bg_color, 0.18);
}

/* ── Badges & status ─────────────────────────────────────────────────── */
.badge {
  border-radius: 999px;
  padding: 3px 11px;
  font-size: 8.5pt;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.badge-ok { background-color: alpha(#2ecc71, 0.15); color: shade(#2ecc71, 0.82); }
.badge-warn { background-color: alpha(#e67e22, 0.15); color: shade(#e67e22, 0.82); }
.badge-err { background-color: alpha(@error_color, 0.14); color: @error_color; }
.badge-neutral { background-color: alpha(@theme_fg_color, 0.09); color: alpha(@theme_fg_color, 0.75); }
.settings-window.dark .badge-ok { color: #55efb8; }
.settings-window.dark .badge-warn { color: #ffb569; }

.dot { border-radius: 50%; min-width: 9px; min-height: 9px; padding: 0; }
.dot-ok { background-color: #2ecc71; }
.dot-warn { background-color: #e67e22; }
.dot-err { background-color: @error_color; }
.dot-off { background-color: alpha(@theme_fg_color, 0.3); }

/* ── Info grid ───────────────────────────────────────────────────────── */
.info-key { font-size: 9.5pt; color: alpha(@theme_fg_color, 0.58); }
.info-val { font-size: 9.5pt; font-weight: 500; }

/* ── Toast: dark glass pill ──────────────────────────────────────────── */
.toast {
  background-color: alpha(#14161c, 0.94);
  color: #f4f5f7;
  border-radius: 12px;
  padding: 11px 20px;
  font-size: 10pt;
  font-weight: 500;
  box-shadow: 0 6px 24px alpha(black, 0.35);
}
.toast-error { background-color: alpha(shade(@error_color, 0.55), 0.95); color: white; }

/* ── Progress ────────────────────────────────────────────────────────── */
.pbar-ok trough {
  min-height: 6px;
  border-radius: 3px;
  background-color: alpha(@theme_fg_color, 0.10);
}
.pbar-ok progress {
  border-radius: 3px;
  min-height: 6px;
  background-color: @theme_selected_bg_color;
}

/* ── Entity cards ────────────────────────────────────────────────────── */
.entity-card {
  background-color: alpha(@theme_fg_color, 0.04);
  border: 1px solid alpha(@theme_fg_color, 0.08);
  border-radius: 12px;
  padding: 13px 16px;
  box-shadow: 0 1px 2px alpha(black, 0.03);
  transition: all 160ms ease;
}
.entity-card:hover {
  border-color: alpha(@theme_selected_bg_color, 0.45);
  box-shadow: 0 4px 14px alpha(black, 0.07);
}
.entity-title { font-size: 10.5pt; font-weight: 600; }
.entity-sub { font-size: 9pt; color: alpha(@theme_fg_color, 0.55); }

.empty-state {
  color: alpha(@theme_fg_color, 0.42);
  font-size: 10pt;
  padding: 26px;
  font-style: italic;
}

/* Loading spinner row */
.async-loading { padding: 4px 2px; }
"""


def install_design(window):
    """Attach the design-system CSS to a window (and all its children)."""
    provider = Gtk.CssProvider()
    provider.load_from_data(_CSS.encode("utf-8"))
    style = window.get_style_context()
    style.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    # Dark detection for the few explicit dark rules
    try:
        theme = Gtk.Settings.get_default().get_property("gtk-application-prefer-dark-theme") or \
            "dark" in (Gtk.Settings.get_default().get_property("gtk-theme-name") or "").lower()
        ctx = window.get_style_context()
        ctx.add_class("settings-window")
        if theme:
            ctx.add_class("dark")
    except Exception:
        pass
    window.get_style_context().add_class("settings-window")


# ── Builder helpers ──────────────────────────────────────────────────────────

def label(text, css_class=None, xalign=0, wrap=True, **kw):
    l = Gtk.Label(label=text, xalign=xalign, wrap=wrap, **kw)
    if css_class:
        l.get_style_context().add_class(css_class)
    l.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
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


class PageHeader(Gtk.Box):
    """Title + subtitle + trailing badges row at the top of every page."""
    def __init__(self, title, subtitle="", badges=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("page-header")
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        top.pack_start(label(title, "page-title"), False, False, 0)
        for text, kind in (badges or []):
            top.pack_end(badge(text, kind), False, False, 0)
        self.pack_start(top, False, False, 0)
        if subtitle:
            self.pack_start(label(subtitle, "page-subtitle"), False, False, 0)


class Section(Gtk.Frame):
    """A settings card: one topic, many rows. GNOME-Settings style."""
    def __init__(self, title=None, subtitle=None):
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
    """Centered, width-constrained settings column used by every page."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=GAP_CARD)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_size_request(CONTENT_WIDTH, -1)
        self.set_border_width(PAD_PAGE)

    def add(self, w):
        self.pack_start(w, False, False, 0)

    def add_expand(self, w):
        self.pack_start(w, True, True, 0)


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
                GLib.idle_add(lambda: self._populate(payload, renderer))
            except Exception as exc:
                GLib.idle_add(lambda: self._fail(exc, on_error))
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
