#!/usr/bin/env python3
"""
Calamares Module: synthexprofile
Shown as a wizard page — merges QML profile/app selections into the
Calamares global storage so downstream modules (packages, synthexpostinstall)
can act on them.
"""
import os
import json
import logging
from pathlib import Path
try:
    import libcalamares as calamares
    HAS_CALAMARES = True
except ImportError:
    # Allow standalone testing outside Calamares
    HAS_CALAMARES = False
    class _FakeGS:
        _d: dict = {}
        def value(self, k): return self._d.get(k)
        def insert(self, k, v): self._d[k] = v
    class _FakeJob:
        def setProgress(self, p): pass
    class _FakeCalamares:
        globalstorage = _FakeGS()
        job = _FakeJob()
        class utils:
            @staticmethod
            def debug(msg): logging.debug(msg)
            @staticmethod
            def warning(msg): logging.warning(msg)
    calamares = _FakeCalamares()

log = logging.getLogger(__name__)

# ── Profile definitions ────────────────────────────────────────────────────────
PROFILES = {
    "classic": {
        "display": "Classic",
        "description": "Familiar Windows-like layout for new Linux users",
        "packages": ["synthex-desktop-classic", "synthex-profile-classic"],
        "features": ["taskbar", "start-menu", "file-manager"],
        "look_and_feel": "org.synthos.desktop.classic",
    },
    "gaming": {
        "display": "Gaming",
        "description": "Big Picture mode, Steam, Proton, MangoHUD",
        "packages": ["synthex-desktop-gaming", "synthex-profile-gaming",
                     "synthex-gaming-platform", "steam", "gamemode", "gamescope"],
        "features": ["steam", "proton", "mangohud", "gamescope", "bore-kernel"],
        "look_and_feel": "org.synthos.desktop.gaming",
    },
    "focus": {
        "display": "Focus",
        "description": "Minimal, keyboard-driven, distraction-free",
        "packages": ["synthex-desktop-focus", "synthex-profile-focus"],
        "features": ["minimal", "tiling", "keyboard-shortcuts"],
        "look_and_feel": "org.synthos.desktop.focus",
    },
    "pro": {
        "display": "Pro",
        "description": "Developer cockpit: Rust, Python, Docker, VS Code",
        "packages": ["synthex-desktop-pro", "synthex-profile-pro",
                     "rust", "python3", "podman", "git"],
        "features": ["dev-tools", "containers", "vscode", "rust"],
        "look_and_feel": "org.synthos.desktop.pro",
    },
    "studio": {
        "display": "Studio",
        "description": "Creative suite: Kdenlive, Krita, Blender, OBS",
        "packages": ["synthex-desktop-studio", "synthex-profile-studio",
                     "kdenlive", "krita", "blender", "obs-studio"],
        "features": ["creative", "video-editing", "3d", "streaming"],
        "look_and_feel": "org.synthos.desktop.studio",
    },
    "ai": {
        "display": "AI Hub",
        "description": "Ollama, Whisper, local LLM workspace",
        "packages": ["synthex-desktop-ai", "synthex-profile-ai",
                     "ollama", "synthex-ai-hub"],
        "features": ["ollama", "whisper", "synth-ai", "local-llm"],
        "look_and_feel": "org.synthos.desktop.ai",
    },
    "lite": {
        "display": "Lite",
        "description": "Lightweight for older/low-RAM hardware",
        "packages": ["synthex-desktop-lite", "synthex-profile-lite"],
        "features": ["lightweight", "low-ram", "fast-boot"],
        "look_and_feel": "org.synthos.desktop.lite",
    },
}

# App bundles — added to packages list when selected
BUNDLES = {
    "gaming":      ["steam", "heroic-games-launcher", "lutris", "gamemode", "gamescope",
                    "mangohud", "protonup-qt", "wine-staging"],
    "development": ["code", "git", "python3-pip", "rust", "nodejs", "podman",
                    "podman-desktop", "make", "cmake", "neovim"],
    "creative":    ["kdenlive", "krita", "blender", "obs-studio", "gimp",
                    "inkscape", "audacity", "darktable"],
    "productivity":["libreoffice", "thunderbird", "nextcloud-client",
                    "obsidian", "notion-app-enhanced"],
    "ai":          ["ollama", "synthex-ai-hub", "anythingllm"],
    "emulation":   ["retroarch", "dolphin-emu", "rpcs3", "pcsx2",
                    "prism-launcher", "ppsspp"],
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _gs_get(key, default=None):
    val = calamares.globalstorage.value(key)
    return val if val is not None else default

def _gs_set(key, val):
    calamares.globalstorage.insert(key, val)

def _debug(msg):
    calamares.utils.debug(f"[synthexprofile] {msg}")

# ── Module functions ──────────────────────────────────────────────────────────
def pretty_name():
    return "Choose Your SynthOS Profile"

def required():
    return []

def weight():
    return 5

def run():
    """Called by Calamares to execute this module."""
    # ── Read selections from global storage (set by QML page) ────────────────
    profile_id   = _gs_get("synthexProfile",  "classic")
    theme_id     = _gs_get("synthexTheme",    "dark-amber")
    selected_bundles = _gs_get("synthexBundles", [])
    selected_apps    = _gs_get("synthexApps",    [])

    _debug(f"Profile: {profile_id}, Theme: {theme_id}, "
           f"Bundles: {selected_bundles}, Extra apps: {len(selected_apps)}")

    # ── Resolve profile ───────────────────────────────────────────────────────
    profile = PROFILES.get(profile_id, PROFILES["classic"])
    base_pkgs = list(profile["packages"])

    # ── Resolve bundle packages ───────────────────────────────────────────────
    bundle_pkgs = []
    for bundle in (selected_bundles or []):
        bundle_pkgs.extend(BUNDLES.get(bundle, []))

    # ── Combine all packages ──────────────────────────────────────────────────
    all_pkgs = list(dict.fromkeys(base_pkgs + bundle_pkgs + (selected_apps or [])))
    _debug(f"Total packages to install: {len(all_pkgs)}")

    # ── Write back to global storage ──────────────────────────────────────────
    _gs_set("synthexPackages",     all_pkgs)
    _gs_set("synthexProfileData",  profile)
    _gs_set("synthexLookAndFeel",  profile["look_and_feel"])

    # Store the install profile JSON for post-install module
    install_profile = {
        "edition":   _gs_get("synthexEdition", "plasma"),
        "profile":   profile_id,
        "version":   "2026.10",
        "variant":   "v3",
        "theme":     theme_id,
        "bundles":   selected_bundles,
        "features":  profile.get("features", []),
        "look_and_feel": profile["look_and_feel"],
    }
    _gs_set("synthex_install_profile", install_profile)
    _gs_set("synthex_oobe_apps",       {"flatpak_apps": [], "dnf_apps": selected_apps})

    _debug(f"Profile '{profile['display']}' ({len(all_pkgs)} packages) written to globalstorage")
    calamares.job.setProgress(1.0)
    return None


if __name__ == "__main__":
    # Standalone test
    logging.basicConfig(level=logging.DEBUG)
    calamares.globalstorage.insert("synthexProfile", "gaming")
    calamares.globalstorage.insert("synthexBundles", ["gaming", "development"])
    result = run()
    print("Result:", result)
    print("Packages:", calamares.globalstorage.value("synthexPackages"))
