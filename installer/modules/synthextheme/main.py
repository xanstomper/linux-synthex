#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthextheme
# Applies the SynthOS visual theme to the installed system

import os, shutil, subprocess, json
import libcalamares

THEME_SOURCE = "/usr/share/synthex"
THEMES_MAP = {
    "default":     "SynthDark",
    "dark":        "SynthDark",
    "light":       "SynthLight",
    "midnight":    "SynthMidnight",
    "amber":       "SynthAmber",
    "focus":       "SynthFocus",
}
COLOR_SCHEMES_MAP = {
    "SynthDark":     "SynthexDark",
    "SynthLight":    "SynthexLight",
    "SynthMidnight": "SynthexMidnight",
    "SynthAmber":    "SynthexAmber",
    "SynthFocus":    "SynthexFocus",
}


def _write_kwinrc(root: str, username: str, theme: str):
    """Write KWin compositor settings."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    os.makedirs(config_dir, exist_ok=True)

    kwinrc_path = os.path.join(config_dir, "kwinrc")
    kwinrc_content = f"""[Compositing]
Enabled=true
Backend=OpenGL
GLCore=true
OpenGLIsUnsafe=false
WindowsBlockCompositing=false

[Effect-blur]
BlurStrength=6

[Windows]
BorderlessMaximizedWindows=true

[Plugins]
blurEnabled=true
contrastEnabled=true
overview_enabled=true
"""
    with open(kwinrc_path, "w") as f:
        f.write(kwinrc_content)
    libcalamares.utils.debug(f"[synthextheme] kwinrc written for {username}")


def _write_kdeglobals(root: str, username: str, theme_name: str, color_scheme: str):
    """Write KDE global theme settings."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    os.makedirs(config_dir, exist_ok=True)

    kdeglobals_path = os.path.join(config_dir, "kdeglobals")
    kdeglobals_content = f"""[General]
ColorScheme={color_scheme}
Name={theme_name}
shadeSortColumn=true
widgetStyle=Breeze

[Icons]
Theme=synthex-icons

[KDE]
AnimationDurationFactor=0.5
LookAndFeelPackage=org.synthos.desktop.{theme_name.lower()}
SingleClick=false
widgetStyle=Breeze

[WM]
activeBackground=12,12,20
activeBlend=12,12,20
activeForeground=255,255,255
inactiveBackground=18,18,26
inactiveBlend=18,18,26
inactiveForeground=120,120,140
"""
    with open(kdeglobals_path, "w") as f:
        f.write(kdeglobals_content)


def _write_plasmarc(root: str, username: str, theme_name: str):
    """Write Plasma shell theme config."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    plasmarc_path = os.path.join(config_dir, "plasmarc")
    plasmarc_content = f"""[Theme]
name={theme_name}

[ContrastEffect]
Enabled=true
Contrast=0.3
Intensity=0.9
Saturation=1.9
"""
    with open(plasmarc_path, "w") as f:
        f.write(plasmarc_content)


def _write_breezerc(root: str, username: str):
    """Write Breeze decoration settings."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    breezerc_path = os.path.join(config_dir, "breezerc")
    breezerc_content = """[Common]
OutlineIntensity=OutlineOff
ShadowSize=ShadowVeryLarge
ShadowStrength=192
ShadowColor=0,0,0

[Windeco Exception 0]
BorderSize=BorderNoSides
Enabled=true
ExceptionPattern=.*
ExceptionType=2
HideTitleBar=false
Mask=64
"""
    with open(breezerc_path, "w") as f:
        f.write(breezerc_content)


def _write_sddm_conf(root: str, theme_name: str):
    """Configure SDDM login screen theme."""
    sddm_conf_dir = os.path.join(root, "etc/sddm.conf.d")
    os.makedirs(sddm_conf_dir, exist_ok=True)

    sddm_conf_path = os.path.join(sddm_conf_dir, "synthex-theme.conf")
    sddm_content = f"""[Theme]
Current=synthex-sddm-theme
ThemeDir=/usr/share/sddm/themes
CursorTheme=Bibata-Modern-Amber
CursorSize=24
Font=Noto Sans

[General]
GreeterEnvironment=QT_SCREEN_SCALE_FACTORS=1
"""
    with open(sddm_conf_path, "w") as f:
        f.write(sddm_content)
    libcalamares.utils.debug("[synthextheme] SDDM config written")


def _write_gtk_theme(root: str, username: str, is_dark: bool):
    """Write GTK theme settings for cross-toolkit consistency."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    os.makedirs(config_dir, exist_ok=True)

    gtk_theme = "Breeze-Dark" if is_dark else "Breeze"
    icon_theme = "synthex-icons"

    # GTK3
    gtk3_dir = os.path.join(config_dir, "gtk-3.0")
    os.makedirs(gtk3_dir, exist_ok=True)
    with open(os.path.join(gtk3_dir, "settings.ini"), "w") as f:
        f.write(f"""[Settings]
gtk-theme-name={gtk_theme}
gtk-icon-theme-name={icon_theme}
gtk-font-name=Noto Sans 10
gtk-cursor-theme-name=Bibata-Modern-Amber
gtk-cursor-theme-size=24
gtk-toolbar-style=GTK_TOOLBAR_BOTH_HORIZ
gtk-xft-antialias=1
gtk-xft-hinting=1
gtk-xft-hintstyle=hintfull
gtk-xft-rgba=rgb
gtk-application-prefer-dark-theme={'1' if is_dark else '0'}
""")

    # GTK4
    gtk4_dir = os.path.join(config_dir, "gtk-4.0")
    os.makedirs(gtk4_dir, exist_ok=True)
    with open(os.path.join(gtk4_dir, "settings.ini"), "w") as f:
        f.write(f"""[Settings]
gtk-theme-name={gtk_theme}
gtk-icon-theme-name={icon_theme}
gtk-font-name=Noto Sans 10
gtk-cursor-theme-name=Bibata-Modern-Amber
gtk-cursor-theme-size=24
gtk-application-prefer-dark-theme={'1' if is_dark else '0'}
""")

    # Color scheme portal preference
    portals_dir = os.path.join(config_dir, "xdg-desktop-portal")
    os.makedirs(portals_dir, exist_ok=True)
    color_pref = 1 if is_dark else 2  # 1=dark, 2=light, 0=no preference
    with open(os.path.join(portals_dir, "synthex-color-scheme"), "w") as f:
        f.write(str(color_pref))


def _write_fonts_conf(root: str, username: str):
    """Configure system fonts for the user."""
    config_dir = os.path.join(root, f"home/{username}/.config")
    fonts_dir = os.path.join(config_dir, "fontconfig")
    os.makedirs(fonts_dir, exist_ok=True)
    fonts_conf = os.path.join(fonts_dir, "fonts.conf")
    with open(fonts_conf, "w") as f:
        f.write("""<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- SynthOS font preferences -->
  <alias>
    <family>sans-serif</family>
    <prefer>
      <family>Noto Sans</family>
      <family>DejaVu Sans</family>
    </prefer>
  </alias>
  <alias>
    <family>serif</family>
    <prefer>
      <family>Noto Serif</family>
      <family>DejaVu Serif</family>
    </prefer>
  </alias>
  <alias>
    <family>monospace</family>
    <prefer>
      <family>JetBrains Mono</family>
      <family>Noto Sans Mono</family>
      <family>DejaVu Sans Mono</family>
    </prefer>
  </alias>

  <!-- Enable sub-pixel rendering -->
  <match target="font">
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintfull</const></edit>
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="lcdfilter" mode="assign"><const>lcddefault</const></edit>
  </match>
</fontconfig>
""")


def _set_wallpaper(root: str, username: str, theme_name: str):
    """Set the default Plasma wallpaper via plasma-setdefaults."""
    wallpaper_src = f"/usr/share/wallpapers/SynthOS/{theme_name}"
    wp_link = os.path.join(root, f"home/{username}/.config/synthex-wallpaper")
    with open(wp_link, "w") as f:
        f.write(wallpaper_src)


def _fix_permissions(root: str, username: str):
    """Fix ownership of config files written as root."""
    home = os.path.join(root, f"home/{username}")
    subprocess.run(
        ["chown", "-R", f"{username}:{username}", home],
        capture_output=True, timeout=30
    )


def run():
    gs = libcalamares.globalStorage
    root       = gs.value("rootMountPoint") or "/mnt/synthex"
    profile    = gs.value("synthexProfile")  or "default"
    users      = gs.value("users")           or []
    theme_pref = gs.value("synthexTheme")    or "default"

    if not os.path.isdir(root):
        return (f"Target root {root!r} not found", "synthextheme: root missing")

    # Resolve theme name from profile + explicit preference
    theme_name   = THEMES_MAP.get(theme_pref, "SynthDark")
    color_scheme = COLOR_SCHEMES_MAP.get(theme_name, "SynthexDark")
    is_dark      = theme_name not in ("SynthLight",)

    libcalamares.utils.debug(
        f"[synthextheme] Applying theme={theme_name} color={color_scheme} dark={is_dark}"
    )

    # ── System-wide theme (SDDM, global) ─────────────────────────────────────
    _write_sddm_conf(root, theme_name)

    # System-wide color scheme preset
    kde_globals_sys = os.path.join(root, "etc/xdg/kdeglobals")
    os.makedirs(os.path.dirname(kde_globals_sys), exist_ok=True)
    try:
        with open(kde_globals_sys, "w") as f:
            f.write(f"[KDE]\nLookAndFeelPackage=org.synthos.desktop.{theme_name.lower()}\n\n[General]\nColorScheme={color_scheme}\n")
    except Exception as e:
        libcalamares.utils.warning(f"[synthextheme] Could not write system kdeglobals: {e}")

    # ── Per-user configuration ────────────────────────────────────────────────
    for user_data in users:
        username = user_data.get("username", "")
        if not username or username in ("root",):
            continue

        libcalamares.utils.debug(f"[synthextheme] Configuring theme for user: {username}")

        _write_kdeglobals(root, username, theme_name, color_scheme)
        _write_plasmarc(root, username, theme_name)
        _write_kwinrc(root, username, theme_name)
        _write_breezerc(root, username)
        _write_gtk_theme(root, username, is_dark)
        _write_fonts_conf(root, username)
        _set_wallpaper(root, username, theme_name)
        _fix_permissions(root, username)

    # ── Apply theme via plasma-setdefaults if available ───────────────────────
    plasma_setdefaults = os.path.join(root, "usr/bin/plasma-setdefaults")
    if os.path.exists(plasma_setdefaults):
        laf_pkg = f"org.synthos.desktop.{theme_name.lower()}"
        subprocess.run(
            ["chroot", root, "plasma-setdefaults", laf_pkg],
            capture_output=True, timeout=30
        )
        libcalamares.utils.debug(f"[synthextheme] plasma-setdefaults applied: {laf_pkg}")

    libcalamares.utils.debug("[synthextheme] Theme configuration complete.")
    return None
