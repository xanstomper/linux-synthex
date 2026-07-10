#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexprofile
# Saves desktop profile selection from the OOBE app-picker QML page
# into globalStorage so synthexpostinstall can apply it during finalize.
# ============================================================================

import os, json, subprocess, shutil

NAME    = "synthexprofile"
VERSION = "2026.10"

# Graceful calamares import (allows offline unit testing)
try:
    import calamares
    from calamares.utils import debug, warning, error
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {}
            @classmethod
            def value(cls, k, default=None): return cls._d.get(k, default)
            @classmethod
            def insert(cls, k, v): cls._d[k] = v
        @staticmethod
        def prettyStatus(msg): print(f"[synthexprofile] {msg}")
    calamares = _FakeCal()
    def debug(m): print(f"[synthexprofile] {m}")
    def warning(m): print(f"[synthexprofile] WARN: {m}")
    def error(m):   print(f"[synthexprofile] ERROR: {m}")

# ── Profile → bundle mapping ──────────────────────────────────────────────────
# Maps user-selected profile to:
#   look_and_feel     — Plasma LAF package
#   color_scheme      — KDE color scheme name
#   default_packages  — always-install packages for this profile
#   optional_packages — from OOBE picker (stored in synthexApps)
# ─────────────────────────────────────────────────────────────────────────────
PROFILES = {
    "classic": {
        "look_and_feel":  "org.synthos.desktop.classic",
        "color_scheme":   "SynthexDarkAmber",
        "wallpaper":      "synthos-classic",
        "default_packages": ["synthex-branding", "synthex-classic-theme"],
        "optional_packages": [],
    },
    "gaming": {
        "look_and_feel":  "org.synthos.desktop.gaming",
        "color_scheme":   "SynthexGamingDark",
        "wallpaper":      "synthos-gaming",
        "default_packages": [
            "synthex-gaming-mode", "gamemode", "mangohud",
            "synthex-gaming-packages", "synthex-branding"
        ],
        "optional_packages": ["steam", "lutris", "heroic"],
    },
    "focus": {
        "look_and_feel":  "org.synthos.desktop.focus",
        "color_scheme":   "SynthexFocusDark",
        "wallpaper":      "synthos-focus",
        "default_packages": ["synthex-branding", "synthex-focus-theme"],
        "optional_packages": [],
    },
    "pro": {
        "look_and_feel":  "org.synthos.desktop.pro",
        "color_scheme":   "SynthexProDark",
        "wallpaper":      "synthos-pro",
        "default_packages": [
            "synthex-branding", "libreoffice-draw", "libreoffice-writer",
            "libreoffice-calc", "libreoffice-impress"
        ],
        "optional_packages": [],
    },
    "studio": {
        "look_and_feel":  "org.synthos.desktop.studio",
        "color_scheme":   "SynthexStudio",
        "wallpaper":      "synthos-studio",
        "default_packages": [
            "synthex-branding", "synthex-studio",
            "kdenlive", "audacity", "inkscape", "gimp", "obs-studio"
        ],
        "optional_packages": ["blender", "darktable"],
    },
    "ai": {
        "look_and_feel":  "org.synthos.desktop.ai",
        "color_scheme":   "SynthexAI",
        "wallpaper":      "synthos-ai",
        "default_packages": [
            "synthex-branding", "synthex-ai-hub",
            "ollama", "python3-torch", "python3-transformers"
        ],
        "optional_packages": ["synthex-agent"],
    },
    "lite": {
        "look_and_feel":  "org.synthos.desktop.lite",
        "color_scheme":   "SynthexLite",
        "wallpaper":      "synthos-lite",
        "default_packages": ["synthex-branding"],
        "optional_packages": [],
    },
}

VALID_PROFILES = list(PROFILES.keys())
DEFAULT_PROFILE = "classic"


def pretty_name() -> str:
    return "SynthOS Profile Selection"


def run() -> None | str:
    """Main Calamares job entry point."""
    calamares.prettyStatus("Applying desktop profile selection…")

    # ── Read selections from globalStorage ────────────────────────────────────
    profile   = calamares.globalstorage.value("synthexProfile") or DEFAULT_PROFILE
    oobe_apps = calamares.globalstorage.value("synthexApps")    or []
    edition   = calamares.globalstorage.value("synthexEdition") or "plasma"
    theme     = calamares.globalstorage.value("synthexTheme")   or "dark-amber"

    # Validate
    if profile not in VALID_PROFILES:
        warning(f"Unknown profile '{profile}', falling back to '{DEFAULT_PROFILE}'")
        profile = DEFAULT_PROFILE

    debug(f"Profile: {profile}")
    debug(f"OOBE selected apps: {oobe_apps}")
    debug(f"Edition: {edition} | Theme: {theme}")

    pdata = PROFILES[profile]

    # ── Build package list ────────────────────────────────────────────────────
    packages: list[str] = []

    # Profile defaults
    packages.extend(pdata["default_packages"])

    # OOBE-selected apps (already resolved to package IDs by synthex-app-picker)
    for app in oobe_apps:
        if app and app not in packages:
            packages.append(app)

    # Deduplicate while preserving order
    seen:    set[str] = set()
    deduped: list[str] = []
    for p in packages:
        if p not in seen:
            seen.add(p)
            deduped.append(p)

    debug(f"Final package list ({len(deduped)} pkgs): {deduped}")

    # ── Write to globalStorage ────────────────────────────────────────────────
    # These keys are read by:
    #   • packages module → installs synthexPackages
    #   • synthexpostinstall → applies look-and-feel + color scheme
    calamares.globalstorage.insert("synthexProfile",     profile)
    calamares.globalstorage.insert("synthexPackages",    deduped)
    calamares.globalstorage.insert("synthexLookAndFeel", pdata["look_and_feel"])
    calamares.globalstorage.insert("synthexColorScheme", pdata["color_scheme"])
    calamares.globalstorage.insert("synthexWallpaper",   pdata["wallpaper"])
    calamares.globalstorage.insert("synthexTheme",       theme)

    # ── Write profile state file (picked up by postinstall in chroot) ─────────
    # Path inside chroot — Calamares mounts rootMountPoint before this runs
    root = calamares.globalstorage.value("rootMountPoint") or ""
    state_dir = os.path.join(root, "var", "lib", "synthex")
    os.makedirs(state_dir, mode=0o755, exist_ok=True)

    profile_state = {
        "profile":       profile,
        "look_and_feel": pdata["look_and_feel"],
        "color_scheme":  pdata["color_scheme"],
        "wallpaper":     pdata["wallpaper"],
        "edition":       edition,
        "theme":         theme,
        "packages":      deduped,
        "version":       VERSION,
        "installed_by":  "calamares/synthexprofile",
    }

    state_path = os.path.join(state_dir, "install-profile.json")
    try:
        with open(state_path, "w") as f:
            json.dump(profile_state, f, indent=2)
        debug(f"Profile state written to {state_path}")
    except OSError as e:
        warning(f"Could not write {state_path}: {e}")

    # Also write a flat /etc/synthex/profile (for shell scripts)
    etc_synthex = os.path.join(root, "etc", "synthex")
    os.makedirs(etc_synthex, mode=0o755, exist_ok=True)
    try:
        with open(os.path.join(etc_synthex, "profile"), "w") as f:
            f.write(f"{profile}\n")
        debug("Profile name written to /etc/synthex/profile")
    except OSError as e:
        warning(f"Could not write /etc/synthex/profile: {e}")

    debug(f"synthexprofile complete: profile={profile} packages={len(deduped)}")
    return None  # success
