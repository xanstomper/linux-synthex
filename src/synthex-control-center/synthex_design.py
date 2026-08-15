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
   SynthOS Settings — Premium macOS-grade Design System
   Vibrancy surfaces, pill controls, crisp typography, buttery transitions.
   ══════════════════════════════════════════════════════════════════════════ */

.settings-window {
  font-family: "Inter", "Cantarell", "SF Pro Text", "Noto Sans", "Ubuntu", sans-serif;
}

/* ── Switches: macOS-style pills ─────────────────────────────────────── */
switch {
  border-radius: 999px;
  min-width: 50px;
  min-height: 28px;
  background-color: alpha(@theme_fg_color, 0.15);
  background-image: none;
  outline-style: none;
  transition: background-color 200ms cubic-bezier(0.4, 0, 0.2, 1);
}
switch:checked { background-color: shade(@theme_selected_bg_color, 1.05); }
switch:disabled { opacity: 0.4; }
switch slider {
  min-width: 22px;
  min-height: 22px;
  margin: 3px;
  border: none;
  border-radius: 50%;
  background-color: white;
  box-shadow: 0 2px 5px alpha(black, 0.35), 0 0 1px alpha(black, 0.25);
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Sliders ─────────────────────────────────────────────────────────── */
.scale-ok trough {
  min-height: 6px;
  border-radius: 3px;
  background-color: alpha(@theme_fg_color, 0.13);
  outline-style: none;
}
.scale-ok highlight {
  border-radius: 3px;
  min-height: 6px;
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.25), shade(@theme_selected_bg_color, 0.95));
}
.scale-ok slider, scale slider {
  min-width: 20px;
  min-height: 20px;
  margin: -8px;
  border-radius: 50%;
  background-color: white;
  border: 0.5px solid alpha(black, 0.12);
  box-shadow: 0 2px 6px alpha(black, 0.30), 0 0 0 0.5px alpha(black, 0.06);
  background-image: none;
  transition: box-shadow 150ms ease;
}
.scale-ok slider:hover, scale slider:hover {
  box-shadow: 0 3px 10px alpha(black, 0.40), 0 0 0 6px alpha(@theme_selected_bg_color, 0.12);
}

/* ── Check / radio ───────────────────────────────────────────────────── */
checkbutton check {
  min-width: 20px;
  min-height: 20px;
  border-radius: 6px;
  border: 1.5px solid alpha(@theme_fg_color, 0.28);
  background-color: transparent;
  transition: all 160ms ease;
}
checkbutton check:checked {
  background-color: @theme_selected_bg_color;
  border-color: @theme_selected_bg_color;
}
radiobutton radio {
  min-width: 20px;
  min-height: 20px;
  border-radius: 50%;
  border: 1.5px solid alpha(@theme_fg_color, 0.28);
  transition: all 160ms ease;
}
radiobutton radio:checked { border-color: @theme_selected_bg_color; }

/* ── Spinbuttons / comboboxes ────────────────────────────────────────── */
spinbutton {
  border-radius: 9px;
  border: 1px solid alpha(@theme_fg_color, 0.12);
  background-color: alpha(@theme_fg_color, 0.05);
  padding: 0 4px;
}
spinbutton entry { border: none; background: transparent; }

.combo-compact button {
  background-color: alpha(@theme_fg_color, 0.055);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 6px 11px;
  font-size: 9.5pt;
  background-image: none;
  transition: all 150ms ease;
  outline-style: none;
}
.combo-compact button:hover { background-color: alpha(@theme_fg_color, 0.10); }
.combo-compact button:checked { background-color: alpha(@theme_fg_color, 0.13); }
.combo-compact .cellview { padding-right: 4px; }

/* ── Entries ─────────────────────────────────────────────────────────── */
.entry-clean, entry {
  background-color: alpha(@theme_fg_color, 0.05);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 6px 12px;
  font-size: 9.5pt;
  box-shadow: none;
  outline-style: none;
  transition: all 180ms cubic-bezier(0.4, 0, 0.2, 1);
}
.entry-clean:focus, entry:focus {
  border-color: @theme_selected_bg_color;
  box-shadow: 0 0 0 3.5px alpha(@theme_selected_bg_color, 0.20);
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
button { outline-style: none; transition: all 150ms ease; }

.btn-quiet {
  background-color: alpha(@theme_fg_color, 0.055);
  border: 1px solid alpha(@theme_fg_color, 0.13);
  border-radius: 9px;
  padding: 7px 16px;
  font-size: 9.5pt;
  font-weight: 600;
}
.btn-quiet:hover { background-color: alpha(@theme_fg_color, 0.11); }
.btn-quiet:active { background-color: alpha(@theme_fg_color, 0.16); }

.btn-primary {
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.16), shade(@theme_selected_bg_color, 0.94));
  color: @theme_selected_fg_color;
  border: none;
  border-radius: 9px;
  padding: 8px 19px;
  font-size: 9.5pt;
  font-weight: 700;
  box-shadow: 0 2px 10px alpha(@theme_selected_bg_color, 0.40), inset 0 1px 0 alpha(white, 0.22);
  text-shadow: none;
}
.btn-primary:hover {
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.24), shade(@theme_selected_bg_color, 1.02));
  box-shadow: 0 4px 16px alpha(@theme_selected_bg_color, 0.50), inset 0 1px 0 alpha(white, 0.28);
}
.btn-primary:active {
  background-image: none;
  background-color: shade(@theme_selected_bg_color, 0.88);
  box-shadow: inset 0 2px 6px alpha(black, 0.22);
}
.btn-primary:disabled { opacity: 0.5; }

.btn-destructive {
  color: @error_color;
  background-color: alpha(@error_color, 0.07);
  border: 1px solid alpha(@error_color, 0.40);
  border-radius: 9px;
  padding: 7px 16px;
  font-size: 9.5pt;
  font-weight: 600;
}
.btn-destructive:hover { background-color: alpha(@error_color, 0.15); }

/* ── Scrollbars: invisible until hover ───────────────────────────────── */
scrollbar { background-color: transparent; opacity: 0.55; transition: opacity 300ms ease; }
scrollbar:hover { opacity: 1; }
scrollbar slider {
  min-width: 10px;
  min-height: 42px;
  border-radius: 999px;
  border: none;
  margin: 3px 3px;
  background-color: alpha(@theme_fg_color, 0.24);
}
scrollbar slider:hover { background-color: alpha(@theme_fg_color, 0.45); }

/* ── Header ──────────────────────────────────────────────────────────── */
headerbar {
  background-image: none;
  background-color: @theme_base_color;
  border-bottom: 1px solid alpha(@theme_fg_color, 0.08);
  box-shadow: none;
}
.app-title {
  font-size: 14pt;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.settings-search {
  border-radius: 999px;
  padding: 7px 18px;
  background-color: alpha(@theme_fg_color, 0.055);
  border: 1px solid alpha(@theme_fg_color, 0.11);
  font-size: 10pt;
  outline-style: none;
  transition: all 180ms ease;
}
.settings-search:focus {
  border-color: @theme_selected_bg_color;
  box-shadow: 0 0 0 3.5px alpha(@theme_selected_bg_color, 0.18);
  background-color: @theme_base_color;
}

/* ── Sidebar: vibrancy panel ─────────────────────────────────────────── */
.sidebar, .sidebar-scroll { background-color: transparent; }
.sidebar {
  background-image: linear-gradient(to bottom,
    alpha(@theme_fg_color, 0.045), alpha(@theme_fg_color, 0.025));
  border-right: 1px solid alpha(@theme_fg_color, 0.07);
}
.sidebar-item {
  border-radius: 9px;
  margin: 1px 12px;
  padding: 7px 10px;
  transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
  outline-style: none;
}
.sidebar-item:hover { background-color: alpha(@theme_fg_color, 0.07); }
.sidebar-item:active { background-color: alpha(@theme_fg_color, 0.12); }
.sidebar-item:selected {
  background-image: linear-gradient(to bottom,
    shade(@theme_selected_bg_color, 1.14), shade(@theme_selected_bg_color, 0.96));
  color: @theme_selected_fg_color;
  box-shadow: 0 2px 8px alpha(@theme_selected_bg_color, 0.35);
}
.sidebar-item:selected .sidebar-title { color: @theme_selected_fg_color; font-weight: 700; }
.sidebar-item:selected image { color: @theme_selected_fg_color; }

.sidebar-title { font-size: 10pt; font-weight: 500; }
.sidebar-group {
  font-size: 7.5pt;
  font-weight: 800;
  letter-spacing: 0.15em;
  color: alpha(@theme_fg_color, 0.36);
  padding: 18px 24px 6px 24px;
}
.sidebar-sep { background-color: transparent; }

/* ── Content & cards ─────────────────────────────────────────────────── */
.content-scroll { background-color: @theme_base_color; }
.content-column { margin: 0 6px; }

.page-header { padding: 2px 8px 8px 8px; }
.page-title { font-size: 23pt; font-weight: 800; letter-spacing: -0.025em; }
.page-subtitle { font-size: 10pt; color: alpha(@theme_fg_color, 0.55); padding-top: 5px; }

.card {
  background-color: alpha(@theme_fg_color, 0.038);
  border-radius: 18px;
  border: 1px solid alpha(@theme_fg_color, 0.075);
  box-shadow: 0 1px 2px alpha(black, 0.04), 0 8px 28px alpha(black, 0.05);
}
.card-dark {
  background-color: alpha(@theme_fg_color, 0.065);
  border-radius: 18px;
  border: 1px solid alpha(@theme_fg_color, 0.075);
}
.card-padding { padding: 5px 5px; }

.section-title-box { padding: 7px 12px 11px 12px; }
.section-title {
  font-size: 9.5pt;
  font-weight: 800;
  letter-spacing: 0.09em;
  color: alpha(@theme_fg_color, 0.55);
}
.section-sub { font-size: 9pt; color: alpha(@theme_fg_color, 0.46); padding-top: 2px; }

.row {
  padding: 12px 12px;
  border-radius: 11px;
  transition: background-color 150ms ease;
  outline-style: none;
}
.row:hover { background-color: alpha(@theme_fg_color, 0.05); }
.row-title { font-size: 10.5pt; font-weight: 500; }
.row-sub { font-size: 9pt; color: alpha(@theme_fg_color, 0.52); padding-top: 2px; }
.row-sep { background-color: transparent; }

/* ── Badges / dots ───────────────────────────────────────────────────── */
.badge {
  border-radius: 999px;
  padding: 3.5px 12px;
  font-size: 8.5pt;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.badge-ok { background-color: alpha(#2ecc71, 0.16); color: shade(#2ecc71, 0.80); }
.badge-warn { background-color: alpha(#e67e22, 0.16); color: shade(#e67e22, 0.80); }
.badge-err { background-color: alpha(@error_color, 0.15); color: @error_color; }
.badge-neutral { background-color: alpha(@theme_fg_color, 0.10); color: alpha(@theme_fg_color, 0.72); }
.settings-window.dark .badge-ok { color: #5df0b4; }
.settings-window.dark .badge-warn { color: #ffb969; }

.dot { border-radius: 50%; min-width: 9px; min-height: 9px; padding: 0; }
.dot-ok { background-color: #2ecc71; box-shadow: 0 0 6px alpha(#2ecc71, 0.6); }
.dot-warn { background-color: #e67e22; box-shadow: 0 0 6px alpha(#e67e22, 0.6); }
.dot-err { background-color: @error_color; box-shadow: 0 0 6px alpha(@error_color, 0.6); }
.dot-off { background-color: alpha(@theme_fg_color, 0.28); }

/* ── Info grid ───────────────────────────────────────────────────────── */
.info-key { font-size: 9.5pt; color: alpha(@theme_fg_color, 0.56); }
.info-val { font-size: 9.5pt; font-weight: 500; }

/* ── Toast: frosted glass pill ───────────────────────────────────────── */
.toast {
  background-color: alpha(#0e1013, 0.92);
  color: #f5f6f8;
  border-radius: 13px;
  padding: 12px 22px;
  font-size: 10pt;
  font-weight: 600;
  box-shadow: 0 10px 34px alpha(black, 0.42), inset 0 1px 0 alpha(white, 0.10);
}
.toast-error { background-color: alpha(#8e2b2b, 0.95); color: white; }

/* ── Progress ────────────────────────────────────────────────────────── */
.pbar-ok trough {
  min-height: 6px;
  border-radius: 3px;
  background-color: alpha(@theme_fg_color, 0.10);
}
.pbar-ok progress {
  border-radius: 3px;
  min-height: 6px;
  background-image: linear-gradient(to right,
    shade(@theme_selected_bg_color, 0.95), shade(@theme_selected_bg_color, 1.2));
}

/* ── Entity cards ────────────────────────────────────────────────────── */
.entity-card {
  background-color: alpha(@theme_fg_color, 0.045);
  border: 1px solid alpha(@theme_fg_color, 0.07);
  border-radius: 13px;
  padding: 13px 16px;
  box-shadow: 0 1px 2px alpha(black, 0.03);
  transition: all 170ms cubic-bezier(0.4, 0, 0.2, 1);
}
.entity-card:hover {
  border-color: alpha(@theme_selected_bg_color, 0.40);
  box-shadow: 0 5px 18px alpha(black, 0.08);
}
.entity-title { font-size: 10.5pt; font-weight: 600; }
.entity-sub { font-size: 9pt; color: alpha(@theme_fg_color, 0.53); }

.empty-state {
  color: alpha(@theme_fg_color, 0.40);
  font-size: 10pt;
  padding: 28px;
  font-style: italic;
}

/* ── Spinner / loading ───────────────────────────────────────────────── */
spinner { color: @theme_selected_bg_color; }
.async-loading { padding: 4px 4px; }

/* ── Lists inside cards ──────────────────────────────────────────────── */
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
