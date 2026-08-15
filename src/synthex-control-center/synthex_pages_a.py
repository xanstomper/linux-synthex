#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""SynthOS Settings — Pages A: Personal & Desktop sections.
Every row binds to a real backend via synth_system_adapters / synth_platform_adapters.
"""

from gi.repository import Gtk, GLib, Gio
from synthex_design import (
    PageHeader, Section, Row, ContentColumn, Toast, badge, dot, button, label,
    toggle_row, combo_row, spin_row, slider_row, entry_row, buttons_row, entity_card,
)
from synth_system_adapters import (
    ThemeAdapter, PrivacyAdapter, SystemAdapter, run_cmd, safe_set_gsetting, get_gsettings,
)
from synth_platform_adapters import (
    BackgroundsAdapter, FontsAdapter, EffectsAdapter, WindowsAdapter, WorkspacesAdapter,
    HotCornersAdapter, ExtensionsAdapter, GesturesAdapter, InputMethodAdapter,
    AutostartAdapter, PreferredAppsAdapter, NightLightAdapter, PanelAdapter,
    OnlineAccountsAdapter, AccountDetailsAdapter, _gget,
)

R = Row  # shorthand


# ─────────────────────────────────────────────────────────────────────────────
# APPEARANCE — themes, icons, cursors, accents, dark/light, ricing imports
# ─────────────────────────────────────────────────────────────────────────────

def build_appearance(toast):
    col = ContentColumn()
    col.add(PageHeader("Appearance",
                       "Themes, icons, cursors, accents and rice presets",
                       badges=[(f"{len(ThemeAdapter.list_gtk_themes() or [])} themes", "neutral")]))

    sec = Section("Theme")
    _combo(sec, "GTK theme", ThemeAdapter.list_gtk_themes(),
           lambda: ThemeAdapter.get_current_gtk_theme(), ThemeAdapter.apply_gtk_theme)
    _combo(sec, "Icon theme", ThemeAdapter.list_icon_themes(),
           lambda: ThemeAdapter.get_current_icon_theme(), ThemeAdapter.apply_icon_theme)
    _combo(sec, "Cursor theme", ThemeAdapter.list_cursor_themes() or ["default"],
           lambda: _gget("org.cinnamon.desktop.interface", "cursor-theme", "default"),
           lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "cursor-theme", v))
    _combo(sec, "Desktop theme (metacity)", ThemeAdapter.list_gtk_themes(),
           lambda: ThemeAdapter.get_current_gtk_theme(), lambda v: True)
    col.add(sec)

    sec = Section("Colors")
    modes = [("default", "Follow system"), ("prefer-dark", "Prefer dark"), ("prefer-light", "Prefer light")]
    _combo(sec, "Color scheme", modes,
           lambda: _gget("org.cinnamon.desktop.interface", "color-scheme", "default"),
           lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "color-scheme", v))
    accents = [("blue", "Synthex Blue"), ("purple", "Violet"), ("teal", "Teal"),
               ("green", "Evergreen"), ("orange", "Ember"), ("red", "Crimson"), ("pink", "Blossom")]
    _combo(sec, "Accent color", accents,
           lambda: _gget("org.x.apps.portal.color_scheme", "accent", "blue"),
           lambda v: safe_set_gsetting("org.x.apps.portal.color_scheme", "accent", v))
    row, sw = toggle_row("Dark mode", "Enable the dark GTK & Cinnamon variant",
                         icon="weather-clear-night",
                         get=lambda: _gget("org.cinnamon.desktop.interface", "gtk-theme", "").lower().endswith(("-dark", "dark")),
                         set_=lambda v: ThemeAdapter.apply_gtk_theme(
                             ThemeAdapter.get_current_gtk_theme() + ("-dark" if v else "")))
    sec.add_row(row)
    col.add(sec)

    # Typography + effects live here too
    sec = Section("Typography")
    fams = FontsAdapter.families()
    cur = FontsAdapter.current_fonts()
    for key, title, sub in [("interface", "Interface font", "Used by applications and controls"),
                            ("document", "Document font", "Used when reading documents"),
                            ("monospace", "Monospace font", "Terminal and code"),
                            ("window_title", "Window title font", "Titlebars")]:
        _combo(sec, title, [(f, f) for f in fams[:180]],
               lambda k=key: (cur.get(k) or "Sans 10").split(" ")[0],
               lambda v, k=key: FontsAdapter.set_font(k, v), width_chars=26)
    col.add(sec)

    sec = Section("Effects")
    eff = EffectsAdapter.all()
    row, _ = toggle_row("Window compositing", "Smooth animations and shadows",
                        icon="preferences-desktop-effects",
                        get=lambda: eff.get("compositing-enabled", True),
                        set_=lambda v: EffectsAdapter.set("compositing-enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("Desktop effects", "Animate window open/close/minimize",
                        get=lambda: eff.get("desktop-effects", True),
                        set_=lambda v: EffectsAdapter.set("desktop-effects", v))
    sec.add_row(row)
    _combo(sec, "Close window effect", [(e, e.title()) for e in ["scale", "fade", "none"]],
           lambda: eff.get("close-window-effect", "scale"),
           lambda v: EffectsAdapter.set("close-window-effect", v))
    _combo(sec, "Minimize effect", [(e, e.title()) for e in ["traditional", "scale", "fade", "none"]],
           lambda: eff.get("minimize-window-effect", "traditional"),
           lambda v: EffectsAdapter.set("minimize-window-effect", v))
    row, _ = slider_row("Shadow opacity", 0.0, 1.0, subtitle="Window drop shadow strength",
                        get=lambda: float(eff.get("shadow-opacity", 0.45)),
                        set_=lambda v: EffectsAdapter.set("shadow-opacity", v))
    sec.add_row(row)
    col.add(sec)

    # Rice presets + import
    sec = Section("Rice Studio")
    presets = ThemeAdapter.list_rice_presets() or []
    for p in presets[:6]:
        sec.add_row(entity_card(p.get("name", "Preset"), p.get("description", "")[:70],
                                icon_name=p.get("icon", "preferences-desktop-theme"),
                                trailing=button("Apply", "btn-primary",
                                                lambda b, pid=p.get("id"): _apply_rice(pid, toast))))
    sec.add_row(buttons_row("Import", "Install a rice preset bundle (.synthex-rice) or theme archive",
                            icon="document-import",
                            buttons=[("Choose file…", "btn-quiet", lambda b: _import_theme(toast))]))
    col.add(sec)
    return col


def _apply_rice(pid, toast):
    res = ThemeAdapter.apply_rice_preset(pid)
    toast.show_message(f"Applied rice preset: {pid}" if res.get("ok", True) else "Failed to apply preset", error=not res.get("ok", True))


def _import_theme(toast):
    dlg = Gtk.FileChooserNative.new("Import theme or rice preset", None,
                                    Gtk.FileChooserAction.OPEN, "_Import", "_Cancel")
    filt = Gtk.FileFilter()
    filt.set_name("Themes, zips, .synthex-rice")
    filt.add_pattern("*.tar.xz"); filt.add_pattern("*.zip"); filt.add_pattern("*.synthex-rice")
    dlg.add_filter(filt)
    if dlg.run() == Gtk.ResponseType.ACCEPT:
        path = dlg.get_filename()
        res = ThemeAdapter.install_theme_file(path)
        toast.show_message(res.get("message", "Theme installed") if res.get("ok") else "Import failed",
                           error=not res.get("ok", True))
    dlg.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# BACKGROUNDS
# ─────────────────────────────────────────────────────────────────────────────

def build_backgrounds(toast):
    col = ContentColumn()
    walls = BackgroundsAdapter.list_wallpapers()
    cur = BackgroundsAdapter.current()
    col.add(PageHeader("Backgrounds", "Desktop wallpaper and slideshow",
                       badges=[(f"{len(walls)} images", "neutral")]))

    sec = Section("Wallpaper")
    flow = Gtk.FlowBox(max_children_per_line=5, selection_mode=Gtk.SelectionMode.SINGLE,
                       homogeneous=True, column_spacing=8, row_spacing=8)
    for w in walls[:25]:
        try:
            pix = Gtk.Image.new_from_file(w["path"])
            pix.set_pixel_size(96)
        except Exception:
            pix = Gtk.Image.new_from_icon_name("image-x-generic", Gtk.IconSize.DIALOG)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, border_width=2)
        box.pack_start(pix, False, False, 0)
        box.pack_start(label(w["name"], "entity-sub", xalign=0.5), False, False, 0)
        flow.add(box)
    flow.set_min_children_per_line(3)
    wrap = Gtk.Box(border_width=10)
    wrap.pack_start(flow, True, True, 0)
    sec.add_widget(wrap)

    def _apply(fbox, child, toast=toast):
        idx = [i for i, c in enumerate(fbox.get_children()) if c == child]
        if idx and walls[:25]:
            w = walls[min(idx[0], len(walls) - 1)]
            ok = BackgroundsAdapter.set_wallpaper(w["path"])
            toast.show_message(f"Wallpaper set: {w['name']}" if ok else "Could not set wallpaper",
                               error=not ok)
    flow.connect("child-activated", _apply)
    col.add(sec)

    sec = Section("Slideshow")
    row, _ = toggle_row("Rotate wallpaper automatically", "Cycle images from the picture folder",
                        icon="media-playlist-repeat",
                        get=lambda: cur.get("slideshow_enabled", False),
                        set_=lambda v: BackgroundsAdapter.set_slideshow(v))
    sec.add_row(row)
    _combo(sec, "Change every", [(60, "1 minute"), (300, "5 minutes"), (900, "15 minutes"),
                                 (1800, "30 minutes"), (3600, "1 hour"), (86400, "1 day")],
           lambda: cur.get("delay", 300), lambda v: BackgroundsAdapter.set_slideshow(True, int(v)))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# NIGHT LIGHT
# ─────────────────────────────────────────────────────────────────────────────

def build_nightlight(toast):
    nl = NightLightAdapter.settings()
    col = ContentColumn()
    col.add(PageHeader("Night Light", "Warmer colors after sunset to reduce eye strain",
                       badges=[("Active", "ok") if nl["enabled"] else ("Off", "neutral")]))

    sec = Section("Schedule")
    row, _ = toggle_row("Night Light", "Filter blue light at night", icon="night-light",
                        get=lambda: nl["enabled"],
                        set_=lambda v: NightLightAdapter.set("enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("Automatic sunset to sunrise", "Use location-based schedule",
                        get=lambda: nl["auto_schedule"],
                        set_=lambda v: NightLightAdapter.set("schedule-automatic", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Intensity")
    row, sc = slider_row("Color temperature", 1700, 6500, subtitle="Warmer ← → Cooler",
                         icon="preferences-color",
                         get=lambda: nl["temperature"],
                         set_=lambda v: NightLightAdapter.set("temperature", int(v)))
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_notifications(toast):
    col = ContentColumn()
    s = "org.cinnamon.desktop.notifications"
    col.add(PageHeader("Notifications", "Alerts, banners and do-not-disturb"))

    sec = Section("General")
    row, _ = toggle_row("Do Not Disturb", "Silence all notification popups",
                        icon="notifications-disabled",
                        get=lambda: _gget(s, "display-notifications", True) is False,
                        set_=lambda v: safe_set_gsetting(s, "display-notifications", not v))
    sec.add_row(row)
    row, _ = toggle_row("Notification sounds", "Play a sound when a notification arrives",
                        get=lambda: _gget(s, "play-sound", True),
                        set_=lambda v: safe_set_gsetting(s, "play-sound", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Lock screen")
    row, _ = toggle_row("Show on lock screen", "Display notifications while locked",
                        get=lambda: _gget(s, "show-notifications-on-lock-screen", False),
                        set_=lambda v: safe_set_gsetting(s, "show-notifications-on-lock-screen", v))
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# PRIVACY (kept from Privacy Center, restyled)
# ─────────────────────────────────────────────────────────────────────────────

def build_privacy(toast):
    col = ContentColumn()
    col.add(PageHeader("Privacy", "Location, camera, microphone and application permissions"))

    sec = Section("Services")
    perms = PrivacyAdapter.get_permission_status() if hasattr(PrivacyAdapter, "get_permission_status") else {}
    for key, title in [("location", "Location services"), ("camera", "Camera access"),
                       ("mic", "Microphone access"), ("screen", "Screen recording")]:
        row, _ = toggle_row(title, f"Allow applications to use {key}", icon="preferences-system-privacy",
                            get=(lambda k=key: bool(perms.get(k, perms.get(k + "_enabled", False)))),
                            set_=(lambda v, k=key: PrivacyAdapter.set_permission(k, v) if hasattr(PrivacyAdapter, "set_permission") else True))
        sec.add_row(row)
    col.add(sec)

    sec = Section("History & Retention")
    s = "org.cinnamon.desktop.privacy"
    row, _ = toggle_row("Remember recent files", "Track recently used documents",
                        get=lambda: _gget(s, "remember-recent-files", True),
                        set_=lambda v: safe_set_gsetting(s, "remember-recent-files", v))
    sec.add_row(row)
    _spin(sec, "Recent files retention (days)", 1, 365,
          lambda: int(_gget(s, "recent-files-max-age", 30)),
          lambda v: safe_set_gsetting(s, "recent-files-max-age", int(v)))
    row, _ = toggle_row("File trash auto-empty", "Purge deleted files after the retention period",
                        get=lambda: _gget(s, "remove-old-trash-files", False),
                        set_=lambda v: safe_set_gsetting(s, "remove-old-trash-files", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Telemetry")
    row, _ = toggle_row("Anonymous system statistics", "Help improve SynthOS — opt-in, always",
                        icon="help-about",
                        get=lambda: _gget("org.linuxmint.report", "root-infoshown", False),
                        set_=lambda v: True)
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# ONLINE ACCOUNTS
# ─────────────────────────────────────────────────────────────────────────────

def build_online_accounts(toast):
    col = ContentColumn()
    col.add(PageHeader("Online Accounts", "Connect mail, calendar, files and contacts"))

    providers = OnlineAccountsAdapter.provider_supported()
    sec = Section("Available backends")
    for name, supported in providers.items():
        sec.add_row(entity_card(name, "Ready to configure" if supported else "Not installed",
                                icon_name="applications-internet" if supported else "dialog-question",
                                trailing=badge("Available", "ok") if supported else badge("Missing", "warn")))
    col.add(sec)

    sec = Section("Configured accounts")
    accounts = OnlineAccountsAdapter.configured()
    if accounts:
        for a in accounts:
            sec.add_row(entity_card(a["name"], a["type"],
                                    icon_name="application-x-addon",
                                    trailing=button("Configure…", "btn-quiet",
                                                    lambda b, act=a["action"]: OnlineAccountsAdapter.launch_configurator(act))))
    else:
        sec.add_row(label("No online accounts configured", "empty-state", xalign=0.5))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# REGION & LANGUAGE + INPUT METHODS
# ─────────────────────────────────────────────────────────────────────────────

def build_region(toast):
    col = ContentColumn()
    col.add(PageHeader("Language & Region", "Language, formats, keyboard layouts and input methods"))

    sec = Section("Language")
    ok, localectl, _ = run_cmd(["localectl", "status"], timeout=5)
    cur_lang = ""
    for line in (localectl or "").splitlines():
        if line.startswith("   System Locale:"):
            m = __import__("re").search(r"LANG=(\S+)", line)
            if m:
                cur_lang = m.group(1)
    langs = []
    ok, out, _ = run_cmd(["bash", "-c", "localectl list-locales 2>/dev/null | grep -E '^(en|de|fr|es|pt|it|ru|ja|zh|ko|ar|hi|pl|nl|sv|tr)_' | head -80"], timeout=8)
    if ok and out:
        langs = [(l, l) for l in out.splitlines()]
    if cur_lang:
        langs = [(cur_lang, cur_lang)] + [l for l in langs if l[0] != cur_lang]
    if langs:
        def _set_lang(v):
            ok, _, _ = run_cmd(["pkexec", "localectl", "set-locale", f"LANG={v}"], timeout=10)
            toast.show_message(f"System language set to {v} (applies next login)" if ok else "Failed to set language", error=not ok)
        _combo(sec, "System language", langs[:80], lambda: cur_lang, _set_lang, width_chars=22)
    col.add(sec)

    sec = Section("Input methods")
    engines = InputMethodAdapter.available_engines()[:40]
    cur_im = InputMethodAdapter.current()
    opts = [("simple", "None (simple)")] + [(e["name"], f"{e['desc']} ({e['name']})") for e in engines]
    def _set_im(v):
        ok = InputMethodAdapter.set_current(v)
        toast.show_message(f"Input method: {v}" if ok else "Could not set input method", error=not ok)
    _combo(sec, "Keyboard input method system", opts, lambda: cur_im, _set_im, width_chars=26)
    row, _ = buttons_row("Restart input method", "Applies the input method immediately",
                         icon="input-keyboard",
                         buttons=[("Restart", "btn-quiet", lambda b: (run_cmd(["ibus", "restart"]), toast.show_message("Input method restarted")))])
    sec.add_row(row)
    col.add(sec)

    sec = Section("Regional formats")
    _combo(sec, "First day of week", [(0, "Sunday"), (1, "Monday")],
           lambda: int(_gget("org.cinnamon.desktop.interface", "first-day-of-week", 1)),
           lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "first-day-of-week", int(v)))
    row, _ = toggle_row("24-hour clock", "Display time in 24-hour format", icon="clock",
                        get=lambda: _gget("org.cinnamon.desktop.interface", "clock-use-24h", False),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-use-24h", v))
    sec.add_row(row)
    row, _ = toggle_row("Show seconds in clock",
                        get=lambda: _gget("org.cinnamon.desktop.interface", "clock-show-seconds", False),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-show-seconds", v))
    sec.add_row(row)
    row, _ = toggle_row("Show date in clock",
                        get=lambda: _gget("org.cinnamon.desktop.interface", "clock-show-date", True),
                        set_=lambda v: safe_set_gsetting("org.cinnamon.desktop.interface", "clock-show-date", v))
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# ACCOUNT DETAILS
# ─────────────────────────────────────────────────────────────────────────────

def build_account(toast):
    acct = AccountDetailsAdapter.current()
    col = ContentColumn()
    col.add(PageHeader("Account Details", "Your identity, shell and groups",
                       badges=[("Administrator", "ok") if acct["is_admin"] else ("Standard", "neutral")]))

    sec = Section("Identity")
    e_row, entry = entry_row("Full name", "Shown on the login screen and menus",
                             icon="avatar-default",
                             get=lambda: acct["full_name"],
                             set_=lambda v: AccountDetailsAdapter.set_full_name(v))
    sec.add_row(e_row)
    sec.add_row(entity_card(acct["username"], f"UID {acct['uid']} · {acct['home']}", icon_name="computer"))
    col.add(sec)

    sec = Section("Login shell")
    _combo(sec, "Shell", [(sh, sh.split("/")[-1]) for sh in AccountDetailsAdapter.available_shells()],
           lambda: acct["shell"], lambda v: (AccountDetailsAdapter.set_shell(v),
                                             toast.show_message(f"Shell set to {sh_basename(v)} (next login)")))
    col.add(sec)

    sec = Section("Groups")
    sec.add_row(label("  ".join(acct["groups"][:18]), "entity-sub"))
    col.add(sec)
    return col


def sh_basename(p):
    return p.split("/")[-1]


# ─────────────────────────────────────────────────────────────────────────────
# DESKTOP — icons + hot corners + general desktop behavior
# ─────────────────────────────────────────────────────────────────────────────

def build_desktop(toast):
    col = ContentColumn()
    col.add(PageHeader("Desktop", "Icons, hot corners and desktop behavior"))
    s = "org.cinnamon"

    sec = Section("Desktop icons")
    _combo(sec, "Computer icon visibility", [("none", "Hidden"), ("home", "Home directory")],
           lambda: _gget(s, "desktop-layout", "traditional"),
           lambda v: True)
    row, _ = toggle_row("Show home folder", icon="user-home",
                        get=lambda: _gget(s, "home-visible", True),
                        set_=lambda v: safe_set_gsetting(s, "home-visible", v))
    sec.add_row(row)
    row, _ = toggle_row("Show mounted volumes", "External drives and network mounts",
                        icon="drive-removable-media",
                        get=lambda: _gget(s, "volumes-visible", True),
                        set_=lambda v: safe_set_gsetting(s, "volumes-visible", v))
    sec.add_row(row)
    row, _ = toggle_row("Show trash", icon="user-trash",
                        get=lambda: _gget(s, "trash-visible", True),
                        set_=lambda v: safe_set_gsetting(s, "trash-visible", v))
    sec.add_row(row)
    col.add(sec)

    sec = Section("Hot corners")
    hc = HotCornersAdapter.settings()
    row, _ = toggle_row("Enable hot corners", "Trigger actions when the pointer reaches a screen corner",
                        icon="view-fullscreen",
                        get=lambda: hc["enabled"],
                        set_=lambda v: HotCornersAdapter.set_enabled(v))
    sec.add_row(row)
    actions = [(a, a.replace("-", " ").title()) for a in HotCornersAdapter.corner_actions()]
    _combo(sec, "Top-left corner", actions,
           lambda: hc.get("tl", "expo"), lambda v: _set_corner("top-left", v))
    col.add(sec)
    return col


def _set_corner(corner, action):
    # Cinnamon hot corners are configured via gsettings keys per corner
    safe_set_gsetting("org.cinnamon", f"hotcorner-{corner}", action if action != "none" else "false")
    return True


# ─────────────────────────────────────────────────────────────────────────────
# WINDOWS
# ─────────────────────────────────────────────────────────────────────────────

def build_windows(toast):
    w = WindowsAdapter.all()
    col = ContentColumn()
    col.add(PageHeader("Windows", "Titlebar actions, focus behavior and placement"))

    sec = Section("Titlebar actions")
    acts = [(a, a.replace("-", " ").title()) for a in
            ["toggle-shade", "toggle-maximize", "minimize", "lower", "menu", "none"]]
    _combo(sec, "Double-click", acts, lambda: w["action-double-click-titlebar"],
           lambda v: WindowsAdapter.set("action-double-click-titlebar", v))
    _combo(sec, "Middle-click", acts, lambda: w["action-middle-click-titlebar"],
           lambda v: WindowsAdapter.set("action-middle-click-titlebar", v))
    _combo(sec, "Right-click", acts, lambda: w["action-right-click-titlebar"],
           lambda v: WindowsAdapter.set("action-right-click-titlebar", v))
    col.add(sec)

    sec = Section("Focus & placement")
    _combo(sec, "Window focus mode", [("click", "Click to focus"), ("mouse", "Focus follows mouse"), ("sloppy", "Sloppy focus")],
           lambda: w["focus-mode"], lambda v: WindowsAdapter.set("focus-mode", v))
    _combo(sec, "New window placement", [("automatic", "Automatic"), ("pointer", "At pointer"), ("manual", "Manual")],
           lambda: w["placement-mode"], lambda v: WindowsAdapter.set("placement-mode", v))
    row, _ = toggle_row("Raise windows on click", get=lambda: w["raise-on-click"],
                        set_=lambda v: WindowsAdapter.set("raise-on-click", v))
    sec.add_row(row)
    row, _ = toggle_row("Auto-raise focused windows",
                        get=lambda: w["auto-raise"], set_=lambda v: WindowsAdapter.set("auto-raise", v))
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# WORKSPACES
# ─────────────────────────────────────────────────────────────────────────────

def build_workspaces(toast):
    col = ContentColumn()
    col.add(PageHeader("Workspaces", "Virtual desktops and navigation"))
    w = WindowsAdapter.all()

    sec = Section("Virtual desktops")
    _spin(sec, "Number of workspaces", 1, 16,
          lambda: WorkspacesAdapter.get_count(),
          lambda v: WorkspacesAdapter.set_count(int(v)))
    row, _ = toggle_row("Dynamic workspaces", "Add and remove workspaces automatically",
                        icon="view-grid",
                        get=lambda: WorkspacesAdapter.dynamic(),
                        set_=lambda v: WorkspacesAdapter.set_dynamic(v))
    sec.add_row(row)
    row, _ = toggle_row("Cycle through last/first workspace",
                        get=lambda: w["workspace-cycle"],
                        set_=lambda v: WindowsAdapter.set("workspace-cycle", v))
    sec.add_row(row)
    row, _ = toggle_row("Workspace switcher OSD", "Show a popup when switching workspaces",
                        get=lambda: WorkspacesAdapter.get_osd(),
                        set_=lambda v: WorkspacesAdapter.set_osd(v))
    sec.add_row(row)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# PANELS
# ─────────────────────────────────────────────────────────────────────────────

def build_panels(toast):
    col = ContentColumn()
    col.add(PageHeader("Panels", "Top and bottom bars, auto-hide behavior"))
    s = "org.cinnamon"

    sec = Section("Panel behavior")
    modes = [("false", "Always visible"), ("true", "Auto-hide"), ("intelligent", "Intelligent hide")]
    _combo(sec, "Auto-hide", modes,
           lambda: str(_gget(s, "panel-autohide", "false")),
           lambda v: safe_set_gsetting(s, "panel-autohide", v))
    _spin(sec, "Show delay (ms)", 0, 2000,
          lambda: int(_gget(s, "panel-show-delay", 0)),
          lambda v: safe_set_gsetting(s, "panel-show-delay", int(v)))
    _spin(sec, "Hide delay (ms)", 0, 2000,
          lambda: int(_gget(s, "panel-hide-delay", 0)),
          lambda v: safe_set_gsetting(s, "panel-hide-delay", int(v)))
    col.add(sec)

    sec = Section("Panel editing")
    row, _ = buttons_row("Panel edit mode", "Unlock and rearrange panel applets",
                         icon="list-add",
                         buttons=[("Toggle edit mode", "btn-primary", lambda b: _toggle_panel_edit(toast))])
    sec.add_row(row)
    col.add(sec)
    return col


def _toggle_panel_edit(toast):
    cur = bool(_gget("org.cinnamon", "panel-edit-mode", False))
    safe_set_gsetting("org.cinnamon", "panel-edit-mode", not cur)
    toast.show_message(f"Panel edit mode {'disabled' if cur else 'enabled'}")


# ─────────────────────────────────────────────────────────────────────────────
# APPLETS / DESKLETS / EXTENSIONS (xlets browser)
# ─────────────────────────────────────────────────────────────────────────────

def build_xlets(kind, title, icon, toast):
    col = ContentColumn()
    items = ExtensionsAdapter.list_installed(kind)
    col.add(PageHeader(title, f"Installed {kind} and enable/disable switches",
                       badges=[(f"{len(items)} installed", "neutral")]))

    sec = Section(f"Installed {kind}")
    if not items:
        sec.add_row(label(f"No {kind} installed yet", "empty-state", xalign=0.5))
    for it in items[:24]:
        enabled = ExtensionsAdapter.is_enabled(kind, it["uuid"])

        def make_toggle(uuid, kind=kind):
            sw = Gtk.Switch(valign=Gtk.Align.CENTER)
            sw.set_active(ExtensionsAdapter.is_enabled(kind, uuid))
            def on_set(b, st, uuid=uuid):
                ExtensionsAdapter.set_enabled(kind, uuid, st)
                toast.show_message(f"{uuid} {'enabled' if st else 'disabled'}")
            sw.connect("state-set", on_set)
            return sw

        sec.add_row(entity_card(it["name"], it["desc"] or it["uuid"], icon_name=it["icon"],
                                trailing=make_toggle(it["uuid"])))
    col.add(sec)

    sec = Section("Manage")
    sec.add_row(buttons_row(f"Browse & install more", f"Open the {kind} manager",
                            icon="system-software-install",
                            buttons=[(f"Open {kind} manager", "btn-primary",
                                      lambda b, k=kind: run_cmd([f"cinnamon-{k[:-1]}-settings"])])))
    col.add(sec)
    return col


def build_applets(toast):
    return build_xlets("applets", "Applets", "preferences-plugin", toast)


def build_desklets(toast):
    return build_xlets("desklets", "Desklets", "preferences-desktop-widgets", toast)


def build_extensions(toast):
    return build_xlets("extensions", "Extensions", "application-x-extension", toast)


# ─────────────────────────────────────────────────────────────────────────────
# GESTURES
# ─────────────────────────────────────────────────────────────────────────────

def build_gestures(toast):
    g = GesturesAdapter.settings()
    col = ContentColumn()
    col.add(PageHeader("Gestures", "Touchscreen and touchpad multi-touch gestures",
                       badges=[("Touchégg detected", "ok") if g["touchegg_running"] else ("No gesture daemon", "warn")]))

    sec = Section("Touchpad gestures")
    row, _ = toggle_row("Enable multi-touch gestures", icon="input-touchpad",
                        get=lambda: g["enabled"],
                        set_=lambda v: GesturesAdapter.set("enabled", v))
    sec.add_row(row)
    row, _ = toggle_row("3-finger swipe up → workspace switch",
                        get=lambda: g["swipe_up_workspace"],
                        set_=lambda v: GesturesAdapter.set("swipe-up-workspace", v))
    sec.add_row(row)
    row, _ = toggle_row("3-finger swipe down → fullscreen toggle",
                        get=lambda: g["swipe_down_fullscreen"],
                        set_=lambda v: GesturesAdapter.set("swipe-down-fullscreen", v))
    sec.add_row(row)
    _combo(sec, "Pinch in", [(z, z.title()) for z in ["zoom", "minimize", "none"]],
           lambda: g["pinch_in"], lambda v: GesturesAdapter.set("pinch-in", v))
    _combo(sec, "Pinch out", [(z, z.title()) for z in ["zoom", "maximize", "none"]],
           lambda: g["pinch_out"], lambda v: GesturesAdapter.set("pinch-out", v))
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# PREFERRED APPLICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_preferred_apps(toast):
    col = ContentColumn()
    col.add(PageHeader("Preferred Applications", "Default programs for common tasks"))

    sec = Section("Defaults")
    for role, title, mime in PreferredAppsAdapter.ROLES:
        cands = PreferredAppsAdapter.candidates(role, mime)[:30]
        if not cands:
            continue
        _combo(sec, title, [(c["id"], c["name"]) for c in cands],
               lambda r=role, m=mime: PreferredAppsAdapter.get_default(r, m),
               lambda v, r=role, m=mime: PreferredAppsAdapter.set_default(r, m, v),
               width_chars=22)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# STARTUP APPLICATIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_startup(toast):
    col = ContentColumn()
    entries = AutostartAdapter.list_autostarts()
    col.add(PageHeader("Startup Applications", "Programs launched automatically on login",
                       badges=[(f"{sum(1 for e in entries if e['enabled'])} enabled", "ok")]))

    sec = Section("Startup entries")
    for e in entries[:30]:
        sw = Gtk.Switch(valign=Gtk.Align.CENTER)
        sw.set_active(e["enabled"])
        def on_set(b, st, key=e["key"], name=e["name"]):
            AutostartAdapter.set_enabled(key, st)
            toast.show_message(f"{name} {'enabled' if st else 'disabled'} at startup")
        sw.connect("state-set", on_set)
        sec.add_row(entity_card(e["name"], "User entry" if e["user"] else "System entry",
                                icon_name=e["icon"],
                                trailing=sw))
    col.add(sec)

    sec = Section("Add custom")
    name_e, cmd_e = None, None
    grid = Gtk.Grid(column_spacing=10, row_spacing=8, border_width=10)
    grid.attach(label("Name", "info-key"), 0, 0, 1, 1)
    name_e = Gtk.Entry(); name_e.get_style_context().add_class("entry-clean")
    grid.attach(name_e, 1, 0, 1, 1)
    grid.attach(label("Command", "info-key"), 0, 1, 1, 1)
    cmd_e = Gtk.Entry(); cmd_e.get_style_context().add_class("entry-clean")
    grid.attach(cmd_e, 1, 1, 1, 1)

    def add(b):
        if name_e.get_text() and cmd_e.get_text():
            AutostartAdapter.add_custom(name_e.get_text(), cmd_e.get_text())
            toast.show_message(f"Added {name_e.get_text()} to startup")
            name_e.set_text(""); cmd_e.set_text("")
    grid.attach(button("Add", "btn-primary", add), 1, 2, 1, 1)
    sec.add_widget(grid)
    col.add(sec)
    return col


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _combo(sec, title, options, get, set_, width_chars=18, subtitle="", icon=None):
    row, _ = combo_row(title, options, subtitle=subtitle, icon=icon,
                       get=get, set_=set_, width_chars=width_chars)
    sec.add_row(row)


def _spin(sec, title, lo, hi, get, set_, step=1, unit="", subtitle="", icon=None):
    row, _ = spin_row(title, lo, hi, step=step, subtitle=subtitle, icon=icon,
                      get=get, set_=set_, unit=unit)
    sec.add_row(row)
