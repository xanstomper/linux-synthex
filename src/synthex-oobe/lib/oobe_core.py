#!/usr/bin/env python3
"""
synthex-oobe core library
Handles state management, Flatpak/DNF app installation, profile application,
and QML launcher for the SynthOS Out-Of-Box Experience wizard.
"""
import os
import sys
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional, Callable

# ── State paths ────────────────────────────────────────────────────────────────
def _state_base() -> Path:
    if os.geteuid() == 0:
        return Path("/var/lib/synthex")
    # Non-root: user-local state
    return Path(os.environ.get("XDG_DATA_HOME",
                               str(Path.home() / ".local" / "share"))) / "synthex"

def _ensure(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

SYNTHEX_STATE     = _state_base()
OOBE_COMPLETE     = SYNTHEX_STATE / "oobe-complete"
OOBE_APPS_JSON    = SYNTHEX_STATE / "oobe-apps.json"
OOBE_PROFILE_JSON = SYNTHEX_STATE / "install-profile.json"
FIRSTBOOT_DONE    = SYNTHEX_STATE / "firstboot-complete"
OOBE_LOG          = SYNTHEX_STATE / "oobe.log"

log = logging.getLogger("synthex.oobe")

# ── Logging setup ──────────────────────────────────────────────────────────────
def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    _ensure(SYNTHEX_STATE)
    handlers = [logging.StreamHandler(sys.stderr)]
    try:
        handlers.append(logging.FileHandler(OOBE_LOG))
    except (PermissionError, OSError):
        pass
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

# ── State helpers ──────────────────────────────────────────────────────────────
def is_complete() -> bool:
    return OOBE_COMPLETE.exists()

def mark_complete() -> None:
    _ensure(SYNTHEX_STATE)
    try:
        OOBE_COMPLETE.touch()
        log.info("OOBE marked complete → %s", OOBE_COMPLETE)
    except PermissionError as exc:
        log.warning("Cannot mark OOBE complete: %s", exc)

def write_selections(
    profile: str,
    theme: str,
    bundles: list,
    apps: list,
    flatpak_apps: Optional[list] = None,
) -> None:
    """Persist user selections to disk for later apply steps."""
    _ensure(SYNTHEX_STATE)
    payload = {
        "profile":      profile,
        "theme":        theme,
        "bundles":      bundles,
        "dnf_apps":     apps,
        "flatpak_apps": flatpak_apps or [],
        "source":       "oobe",
        "timestamp":    int(time.time()),
    }
    try:
        OOBE_APPS_JSON.write_text(json.dumps(payload, indent=2))
        OOBE_PROFILE_JSON.write_text(json.dumps({
            "profile":  profile,
            "theme":    theme,
            "bundles":  bundles,
            "version":  "2026.10",
            "source":   "oobe",
        }, indent=2))
        log.info("Selections saved (profile=%s, %d apps, %d flatpaks)",
                 profile, len(apps), len(flatpak_apps or []))
    except PermissionError as exc:
        log.warning("Cannot write selections: %s", exc)

# ── Flatpak installation ───────────────────────────────────────────────────────
FLATPAK_APPS: dict[str, list[str]] = {
    # Browsers
    "firefox":          ["org.mozilla.firefox"],
    "brave":            ["com.brave.Browser"],
    "chromium":         ["org.chromium.Chromium"],
    "vivaldi":          ["com.vivaldi.Vivaldi"],
    # Messaging
    "discord":          ["com.discordapp.Discord"],
    "signal":           ["org.signal.Signal"],
    "telegram":         ["org.telegram.desktop"],
    "slack":            ["com.slack.Slack"],
    "element":          ["im.riot.Riot"],
    "zoom":             ["us.zoom.Zoom"],
    "whatsapp":         ["io.github.mimbrero.WhatsAppDesktop"],
    # Productivity
    "libreoffice":      ["org.libreoffice.LibreOffice"],
    "onlyoffice":       ["org.onlyoffice.desktopeditors"],
    "obsidian":         ["md.obsidian.Obsidian"],
    # Development
    "vscode":           ["com.visualstudio.code"],
    "cursor":           ["com.cursor.Cursor"],
    "zed":              ["dev.zed.Zed"],
    # Gaming
    "heroic":           ["com.heroicgameslauncher.hgl"],
    "lutris":           ["net.lutris.Lutris"],
    "bottles":          ["com.usebottles.bottles"],
    "protonup":         ["net.davidotek.pupgui2"],
    # Multimedia
    "kdenlive":         ["org.kde.kdenlive"],
    "obs":              ["com.obsproject.Studio"],
    "vlc":              ["org.videolan.VLC"],
    "spotify":          ["com.spotify.Client"],
    "krita":            ["org.kde.krita"],
    "blender":          ["org.blender.Blender"],
    "gimp":             ["org.gimp.GIMP"],
    "inkscape":         ["org.inkscape.Inkscape"],
    # AI
    "anythingllm":      ["com.mintplexlabs.anythingllm"],
    # Utilities
    "flatseal":         ["com.github.tchx84.Flatseal"],
    "warehouse":        ["io.github.flattool.Warehouse"],
}

def _flatpak(*args, timeout: int = 300) -> tuple[int, str, str]:
    """Run flatpak with given args; return (returncode, stdout, stderr)."""
    cmd = ["flatpak", "--noninteractive"] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError:
        return -127, "", "flatpak not found"

def ensure_flathub() -> bool:
    """Add Flathub remote if not present."""
    rc, out, _ = _flatpak("remotes", "--system", "--columns=name")
    if "flathub" in out.lower():
        log.debug("Flathub remote already present")
        return True
    log.info("Adding Flathub remote…")
    rc, _, err = _flatpak(
        "remote-add", "--if-not-exists", "--system",
        "flathub", "https://dl.flathub.org/repo/flathub.flatpakrepo",
        timeout=60,
    )
    if rc == 0:
        log.info("Flathub added ✓")
        return True
    log.warning("Failed to add Flathub: %s", err)
    return False

def install_flatpak_apps(
    app_keys: list[str],
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> dict[str, bool]:
    """
    Install a list of apps by key (from FLATPAK_APPS).
    progress_cb(current, total, app_name) for UI updates.
    Returns {app_key: success} mapping.
    """
    ensure_flathub()
    results: dict[str, bool] = {}
    total = len(app_keys)

    for idx, key in enumerate(app_keys):
        app_ids = FLATPAK_APPS.get(key, [])
        if not app_ids:
            log.warning("No Flatpak ID for app key '%s' — skipping", key)
            results[key] = False
            continue

        app_id = app_ids[0]
        log.info("[%d/%d] Installing %s (%s)…", idx + 1, total, key, app_id)

        if progress_cb:
            progress_cb(idx, total, key)

        rc, _, err = _flatpak(
            "install", "--system", "--assumeyes",
            "flathub", app_id,
            timeout=600,
        )
        results[key] = rc == 0
        if rc == 0:
            log.info("  ✓ %s installed", app_id)
        else:
            log.warning("  ✗ %s failed (rc=%d): %s", app_id, rc, err[:200])

    if progress_cb:
        progress_cb(total, total, "Done")

    return results

def install_dnf_apps(app_names: list[str]) -> dict[str, bool]:
    """Install a list of DNF packages."""
    if not app_names:
        return {}
    results: dict[str, bool] = {}
    try:
        r = subprocess.run(
            ["dnf", "install", "--assumeyes", "--quiet"] + app_names,
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode == 0:
            for name in app_names:
                results[name] = True
        else:
            log.warning("dnf install failed: %s", r.stderr[:500])
            for name in app_names:
                results[name] = False
    except Exception as exc:
        log.warning("DNF error: %s", exc)
        for name in app_names:
            results[name] = False
    return results

# ── Profile application ────────────────────────────────────────────────────────
def apply_profile(profile: str) -> bool:
    """Apply a desktop profile by calling the apply-profile.sh script."""
    script = Path("/usr/libexec/synthex/apply-profile.sh")
    if not script.exists():
        log.warning("apply-profile.sh not found; writing profile only")
        _ensure(SYNTHEX_STATE)
        existing = {}
        if OOBE_PROFILE_JSON.exists():
            try:
                existing = json.loads(OOBE_PROFILE_JSON.read_text())
            except Exception:
                pass
        existing["profile"] = profile
        OOBE_PROFILE_JSON.write_text(json.dumps(existing, indent=2))
        return True

    try:
        r = subprocess.run([str(script), profile], timeout=120)
        return r.returncode == 0
    except Exception as exc:
        log.warning("apply_profile failed: %s", exc)
        return False

def apply_theme(theme: str) -> bool:
    """Apply a color theme by calling apply-theme.sh or writing KDE config."""
    script = Path("/usr/libexec/synthex/apply-theme.sh")
    if script.exists():
        try:
            r = subprocess.run([str(script), theme], timeout=60)
            return r.returncode == 0
        except Exception as exc:
            log.warning("apply_theme script failed: %s", exc)

    # KDE Plasma fallback — write color scheme via kwriteconfig6
    if shutil.which("kwriteconfig6"):
        scheme_map = {
            "dark-amber":     "SynthexDarkAmber",
            "dark-navy":      "SynthexDarkNavy",
            "midnight-purple":"SynthexMidnightPurple",
            "ocean-blue":     "SynthexOceanBlue",
            "forest":         "SynthexForest",
            "graphite":       "SynthexGraphite",
        }
        scheme = scheme_map.get(theme, "SynthexDarkAmber")
        try:
            subprocess.run(
                ["kwriteconfig6", "--file", "kdeglobals",
                 "--group", "General", "--key", "ColorScheme", scheme],
                timeout=10,
            )
            return True
        except Exception as exc:
            log.warning("kwriteconfig6 failed: %s", exc)
    return False

# ── Selections apply (called from OOBE Finish page) ───────────────────────────
def apply_all_selections(
    profile: str,
    theme: str,
    bundles: list,
    dnf_apps: list,
    flatpak_apps: list,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> dict:
    """
    Full apply pipeline:
    1. Write selections to disk
    2. Apply profile
    3. Apply theme
    4. Install DNF packages
    5. Install Flatpak apps
    6. Mark complete
    """
    write_selections(profile, theme, bundles, dnf_apps, flatpak_apps)
    results = {
        "profile_ok": apply_profile(profile),
        "theme_ok":   apply_theme(theme),
        "dnf":        install_dnf_apps(dnf_apps) if dnf_apps else {},
        "flatpak":    install_flatpak_apps(flatpak_apps, progress_cb) if flatpak_apps else {},
    }
    mark_complete()
    log.info("OOBE apply_all_selections complete: %s", results)
    return results

# ── QML launcher ──────────────────────────────────────────────────────────────
def find_ui_dir() -> Optional[Path]:
    script_dir = Path(__file__).parent.parent
    candidates = [
        script_dir / "ui",
        Path("/usr/share/synthex/oobe/ui"),
        Path("/usr/lib/synthex/oobe/ui"),
    ]
    for c in candidates:
        if (c / "Main.qml").exists():
            return c.resolve()
    return None

def launch_qml(ui_dir: Path) -> bool:
    """Launch the OOBE QML UI and return True on clean exit."""
    qml_file = ui_dir / "Main.qml"
    env = os.environ.copy()
    env["SYNTHEX_STATE_DIR"]  = str(SYNTHEX_STATE)
    env["QML2_IMPORT_PATH"]   = str(ui_dir)
    env["QT_QUICK_CONTROLS_STYLE"] = "Material"
    env["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
    env["QT_QUICK_CONTROLS_MATERIAL_ACCENT"] = "#FFB300"

    for runner in ("qml6", "qml", "qmlscene"):
        if shutil.which(runner):
            log.info("Launching OOBE with %s %s", runner, qml_file)
            try:
                r = subprocess.run([runner, str(qml_file)], env=env)
                return r.returncode == 0
            except KeyboardInterrupt:
                return False
            except Exception as exc:
                log.warning("%s failed: %s", runner, exc)
    log.error("No QML runner found (tried qml6, qml, qmlscene)")
    return False
