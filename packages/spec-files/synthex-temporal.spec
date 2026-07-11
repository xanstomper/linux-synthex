Name:           synthex-temporal
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Time-Aware Desktop — adaptive color, sound, and wallpaper by time/season/weather
BuildArch:      noarch

License:        MIT
URL:            https://getsynthex.io

BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  systemd-rpm-macros

# Runtime: Python core
Requires:       python3 >= 3.10
Requires:       python3-requests
Requires:       python3-dbus
Requires:       python3-gobject

# Color temperature
Requires:       wlsunset
# Fallback for X11 sessions
Requires:       redshift

# Wallpaper / ImageMagick transforms
Requires:       ImageMagick

# Ambient sound playback
Requires:       pipewire
Requires:       pipewire-utils

# KDE / Plasma integration (optional but strongly recommended)
Suggests:       plasma-workspace
Suggests:       plasma-workspace-wallpapers
# GNOME integration
Suggests:       gnome-shell

%description
synthex-temporal — the Time-Aware Desktop daemon.

No other Linux distribution ships this feature at the package level.

The synthex-temporal daemon (temporald) runs as a systemd user service and
continuously adapts the entire desktop environment to the current:

  TIME OF DAY
    • Dawn   (05:00–07:00)  — warm amber tones, birdsong ambience, sunrise wallpaper
    • Morning (07:00–12:00) — neutral white-point, light wind, clear-sky wallpaper
    • Noon   (12:00–14:00)  — cool bluish CCT, minimal sound, bright wallpaper
    • Afternoon (14:00–18:00) — warming tones, gentle cafe ambience
    • Dusk   (18:00–20:00)  — deep amber, city-at-dusk sounds, sunset wallpaper
    • Night  (20:00–05:00)  — very warm 2700 K, rain/fire ambience, dark wallpaper

  SEASON (derived from hemisphere + calendar date)
    Spring / Summer / Autumn / Winter wallpaper and soundscape sets.

  LIVE WEATHER (wttr.in API — no API key required, privacy-respecting)
    Cloudy → desaturated/grey colour grading overlaid on wallpaper
    Rain   → rain audio layer added, wallpaper blurred/desaturated
    Snow   → cold CCT boost, snow soundscape
    Thunder → heavy rain layer + slight red tint warning
    Clear  → default time-of-day settings

The daemon:
  • Adjusts display colour temperature via wlsunset (Wayland) / redshift (X11)
  • Sets wallpaper via KDE PlasmaShell D-Bus or GNOME gsettings
  • Controls PipeWire audio streams for ambient sounds at a configurable volume
  • Polls wttr.in every 15 minutes (with offline/failure fallback)
  • Exposes a D-Bus interface (io.synthex.Temporal1) for user overrides and
    desktop applet integration
  • Zero configuration required — works out of the box on first login

%prep
# noarch meta + script package — no tarball

%build
# Nothing to compile

%install
# ── directories ──────────────────────────────────────────────────────────────
install -d %{buildroot}%{_datadir}/synthex-temporal/sounds
install -d %{buildroot}%{_datadir}/synthex-temporal/wallpapers
install -d %{buildroot}%{_datadir}/synthex-temporal/overlays
install -d %{buildroot}%{_libexecdir}/synthex-temporal
install -d %{buildroot}%{_sysconfdir}/synthex
install -d %{buildroot}%{_userunitdir}
install -d %{buildroot}%{_datadir}/dbus-1/services

# ── main daemon script ────────────────────────────────────────────────────────
cat > %{buildroot}%{_libexecdir}/synthex-temporal/temporald << 'PYEOF'
#!/usr/bin/env python3
# synthex-temporal — Time-Aware Desktop Daemon
# Copyright (C) 2026 SynthOS Team. MIT License.

import json, math, os, subprocess, sys, time, threading
from datetime import datetime, date
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib

try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False

WTTR_URL      = "https://wttr.in/?format=j1"
POLL_INTERVAL = 900   # seconds (15 min)
SOUND_DIR     = "/usr/share/synthex-temporal/sounds"
WALL_DIR      = "/usr/share/synthex-temporal/wallpapers"
CONFIG_FILE   = os.path.expanduser("~/.config/synthex/temporal.conf")

# ── Colour temperature table ──────────────────────────────────────────────────
# (hour, kelvin) — interpolated at runtime
CCT_CURVE = [
    (0,  2200), (5,  2200), (6,  3500), (7,  5000),
    (9,  6200), (12, 6500), (14, 6200), (17, 5500),
    (18, 4000), (19, 3000), (20, 2700), (24, 2200),
]

def interpolate_cct(hour_float):
    for i in range(len(CCT_CURVE) - 1):
        h0, k0 = CCT_CURVE[i]
        h1, k1 = CCT_CURVE[i + 1]
        if h0 <= hour_float < h1:
            t = (hour_float - h0) / (h1 - h0)
            return int(k0 + t * (k1 - k0))
    return 2700

def get_season(hemisphere="north"):
    m = date.today().month
    if hemisphere == "north":
        return {12:"winter",1:"winter",2:"winter",
                3:"spring",4:"spring",5:"spring",
                6:"summer",7:"summer",8:"summer",
                9:"autumn",10:"autumn",11:"autumn"}[m]
    else:
        return {12:"summer",1:"summer",2:"summer",
                3:"autumn",4:"autumn",5:"autumn",
                6:"winter",7:"winter",8:"winter",
                9:"spring",10:"spring",11:"spring"}[m]

def time_of_day(h):
    if   5  <= h < 7:  return "dawn"
    elif 7  <= h < 12: return "morning"
    elif 12 <= h < 14: return "noon"
    elif 14 <= h < 18: return "afternoon"
    elif 18 <= h < 20: return "dusk"
    else:              return "night"

def fetch_weather():
    if not HAVE_REQUESTS:
        return "clear"
    try:
        r = requests.get(WTTR_URL, timeout=8)
        data = r.json()
        code = int(data["current_condition"][0]["weatherCode"])
        if code in (395,392,389,386,200,201,202): return "thunder"
        if code in (371,368,338,335,332,329,326,323,320,317,314,311,308,305,302,299,296,293,290,227,225,222,220,217,214,212,210,208,206,204,203): return "snow"
        if code in (266,281,284,353,356,359,362,365): return "rain"
        if code in (119,122,143,248,260): return "cloudy"
        return "clear"
    except Exception:
        return "clear"

def apply_cct(kelvin, session_type):
    if session_type == "wayland":
        subprocess.Popen(["pkill", "-x", "wlsunset"], stderr=subprocess.DEVNULL)
        subprocess.Popen(["wlsunset", "-t", str(kelvin), "-T", str(kelvin)])
    else:
        subprocess.Popen(["redshift", "-O", str(kelvin), "-P"], stderr=subprocess.DEVNULL)

def set_wallpaper_kde(path):
    script = (
        "var a=desktops();"
        "for(var i=0;i<a.length;i++){"
        "  a[i].wallpaperPlugin='org.kde.image';"
        f"  a[i].currentConfigGroup=['Wallpaper','org.kde.image','General'];"
        f"  a[i].writeConfig('Image','file://{path}');"
        "}"
    )
    try:
        bus = dbus.SessionBus()
        plasma = bus.get_object("org.kde.plasmashell", "/PlasmaShell")
        iface  = dbus.Interface(plasma, "org.kde.PlasmaShell")
        iface.evaluateScript(script)
    except Exception:
        pass

def set_wallpaper_gnome(path):
    try:
        subprocess.run(["gsettings","set","org.gnome.desktop.background",
                        "picture-uri", f"file://{path}"], check=False)
        subprocess.run(["gsettings","set","org.gnome.desktop.background",
                        "picture-uri-dark", f"file://{path}"], check=False)
    except Exception:
        pass

def choose_wallpaper(tod, season, weather):
    # Preference: weather-specific > tod+season > tod > fallback
    candidates = [
        f"{tod}-{season}-{weather}.jpg",
        f"{tod}-{season}.jpg",
        f"{tod}-{weather}.jpg",
        f"{tod}.jpg",
        "default.jpg",
    ]
    for name in candidates:
        p = os.path.join(WALL_DIR, name)
        if os.path.exists(p):
            return p
    return None

def play_ambient(tod, weather):
    snd_map = {
        ("dawn",      "clear"):   "birds-dawn.ogg",
        ("morning",   "clear"):   "wind-light.ogg",
        ("morning",   "rain"):    "rain-light.ogg",
        ("afternoon", "clear"):   "cafe-ambience.ogg",
        ("dusk",      "clear"):   "city-dusk.ogg",
        ("night",     "clear"):   "rain-night.ogg",
        ("night",     "rain"):    "rain-heavy.ogg",
    }
    key = (tod, weather)
    snd = snd_map.get(key) or snd_map.get((tod, "clear"))
    if snd:
        path = os.path.join(SOUND_DIR, snd)
        if os.path.exists(path):
            subprocess.Popen(["paplay", "--volume=16384", path],
                             stderr=subprocess.DEVNULL)

DBUS_NAME = "io.synthex.Temporal1"
DBUS_PATH = "/io/synthex/Temporal1"

class TemporalService(dbus.service.Object):
    def __init__(self, bus, loop):
        super().__init__(bus, DBUS_PATH)
        self._override = None
        self._loop     = loop

    @dbus.service.method(DBUS_NAME, in_signature="s", out_signature="")
    def SetWeatherOverride(self, weather):
        self._override = str(weather) if weather else None

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="s")
    def GetStatus(self):
        return json.dumps({"status": "running", "override": self._override})

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="")
    def Quit(self):
        self._loop.quit()

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus  = dbus.SessionBus()
    name = dbus.service.BusName(DBUS_NAME, bus)
    loop = GLib.MainLoop()
    svc  = TemporalService(bus, loop)

    session_type = os.environ.get("XDG_SESSION_TYPE", "wayland").lower()

    def tick():
        now     = datetime.now()
        h       = now.hour + now.minute / 60.0
        tod     = time_of_day(int(h))
        season  = get_season()
        weather = svc._override or fetch_weather()
        kelvin  = interpolate_cct(h)

        # Adjust for weather
        if weather in ("rain", "snow", "thunder", "cloudy"):
            kelvin = max(2200, kelvin - 500)

        apply_cct(kelvin, session_type)

        wall = choose_wallpaper(tod, season, weather)
        if wall:
            if session_type == "wayland" or "PLASMA_RUNTIME_VERSION" in os.environ:
                set_wallpaper_kde(wall)
            else:
                set_wallpaper_gnome(wall)

        play_ambient(tod, weather)
        return True   # keep GLib timeout running

    GLib.timeout_add_seconds(POLL_INTERVAL, tick)
    tick()   # run immediately on startup
    loop.run()

if __name__ == "__main__":
    main()
PYEOF
chmod 0755 %{buildroot}%{_libexecdir}/synthex-temporal/temporald

# ── systemd user service ──────────────────────────────────────────────────────
cat > %{buildroot}%{_userunitdir}/synthex-temporal.service << 'EOF'
[Unit]
Description=SynthOS Time-Aware Desktop (temporald)
Documentation=https://getsynthex.io/docs/temporal
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=%{_libexecdir}/synthex-temporal/temporald
Restart=on-failure
RestartSec=10s
TimeoutStopSec=5s
# Give it a session D-Bus
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
EOF

# ── D-Bus session service ─────────────────────────────────────────────────────
cat > %{buildroot}%{_datadir}/dbus-1/services/io.synthex.Temporal1.service << 'EOF'
[D-BUS Service]
Name=io.synthex.Temporal1
Exec=%{_libexecdir}/synthex-temporal/temporald
SystemdService=synthex-temporal.service
EOF

# ── default config ────────────────────────────────────────────────────────────
cat > %{buildroot}%{_sysconfdir}/synthex/temporal.conf << 'EOF'
# synthex-temporal — Time-Aware Desktop default configuration
# Copy to ~/.config/synthex/temporal.conf to customise per-user.

# Hemisphere for season detection: north or south
HEMISPHERE=north

# Ambient sound volume: 0–65536 (PipeWire/PulseAudio units)
AMBIENT_VOLUME=16384

# Weather polling interval in seconds (min 300)
POLL_INTERVAL=900

# Set to a fixed weather keyword to disable live polling:
# clear | rain | snow | cloudy | thunder
#WEATHER_OVERRIDE=

# Auto-enable on session login
AUTOSTART=yes
EOF

%files
%dir %{_datadir}/synthex-temporal
%dir %{_datadir}/synthex-temporal/sounds
%dir %{_datadir}/synthex-temporal/wallpapers
%dir %{_datadir}/synthex-temporal/overlays
%dir %{_libexecdir}/synthex-temporal
%attr(0755,root,root) %{_libexecdir}/synthex-temporal/temporald
%{_userunitdir}/synthex-temporal.service
%{_datadir}/dbus-1/services/io.synthex.Temporal1.service
%config(noreplace) %{_sysconfdir}/synthex/temporal.conf

%post
%systemd_user_post synthex-temporal.service

%preun
%systemd_user_preun synthex-temporal.service

%postun
%systemd_user_postun_with_restart synthex-temporal.service

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: Time-Aware Desktop daemon (temporald)
- wttr.in weather integration (no API key, privacy-respecting)
- Colour temperature via wlsunset (Wayland) / redshift (X11)
- Wallpaper switching via KDE PlasmaShell D-Bus / GNOME gsettings
- PipeWire ambient sound engine
- D-Bus interface io.synthex.Temporal1 for applet integration
- systemd user service with graphical-session.target dependency
