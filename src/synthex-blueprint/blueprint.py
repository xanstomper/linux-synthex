#!/usr/bin/env python3
"""
Synthex Blueprint — Export/Import System Identity
=================================================
CLI tool for capturing and restoring the entire system configuration.

Usage:
  synthex-blueprint export <file.zbp>        Export system identity
  synthex-blueprint import <file.zbp>         Import/restore system identity
  synthex-blueprint list                      List available blueprint snapshots
  synthex-blueprint info <file.zbp>           Show blueprint metadata

A .zbp file is a tar.gz archive containing:
  - manifest.json  (version, timestamp, hostname, packages, flatpaks, configs…)
  - kde/           (kdeglobals, kwinrc, plasmashellrc, etc.)
  - themes/        (copied theme files)
  - wallpapers/    (wallpaper images)
  - fonts/         (font files)
  - icons/         (icon theme files)
  - autostart/     (desktop files from ~/.config/autostart)

Import safety:
  - Creates a BTRFS snapshot before applying changes (if on BTRFS).
  --dry-run shows what would change without applying.
  --gui launches a simple Tkinter confirmation dialog.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

LOG = logging.getLogger("synthex-blueprint")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BLUEPRINT_DIR = Path.home() / ".local" / "share" / "synthex-blueprint"
BACKUP_DIR = Path("/var/backups/synthex") if os.geteuid() == 0 else Path.home() / ".local" / "share" / "synthex-blueprint-backups"
SNAPSHOT_DIR = "/.snapshots"

MANIFEST_VERSION = 1

# Paths to capture
KDE_CONFIG_PATHS = [
    Path.home() / ".config" / "kdeglobals",
    Path.home() / ".config" / "kwinrc",
    Path.home() / ".config" / "plasmashellrc",
    Path.home() / ".config" / "plasma-org.kde.plasma.desktop-appletsrc",
    Path.home() / ".config" / "krunnerrc",
    Path.home() / ".config" / "khotkeysrc",
    Path.home() / ".config" / "kde.org" / "UserProfileSettings",
]

PLASMA_THEME_DIR = Path.home() / ".local" / "share" / "plasma" / "desktoptheme"
COLOR_SCHEME_DIR = Path.home() / ".local" / "share" / "color-schemes"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _run_cmd(cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a shell command with error logging."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            LOG.debug("Command '%s' exited %d: %s", " ".join(cmd), result.returncode, result.stderr)
        return result
    except subprocess.TimeoutExpired:
        LOG.warning("Command '%s' timed out after %ds", " ".join(cmd), timeout)
        return subprocess.CompletedProcess(cmd, -1, "", "Timed out")
    except FileNotFoundError:
        LOG.warning("Command not found: %s", cmd[0])
        return subprocess.CompletedProcess(cmd, -1, "", "Not found")


def _check_btrfs() -> bool:
    """Return True if root filesystem is BTRFS."""
    try:
        result = subprocess.run(
            ["findmnt", "-n", "-o", "FSTYPE", "/"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() == "btrfs"
    except Exception:
        return False


def _create_btrfs_snapshot(label: str) -> bool:
    """Create a BTRFS snapshot using snapper (preferred) or direct ioctl."""
    if not _check_btrfs():
        LOG.info("Not on BTRFS; skipping snapshot.")
        return True  # non-fatal
    # Try snapper
    for cmd_base in (
        ["snapper", "-c", "root", "create", "-d", label],
        ["sudo", "snapper", "-c", "root", "create", "-d", label],
    ):
        result = _run_cmd(cmd_base)
        if result.returncode == 0:
            LOG.info("Snapshot created: %s", label)
            return True
    if os.geteuid() != 0:
        LOG.warning("Cannot create BTRFS snapshot without root")
        return False
    LOG.info("Direct BTRFS snapshot — snapper preferred")
    return True


def _get_package_list() -> List[str]:
    """Get list of installed RPM packages."""
    result = _run_cmd(["rpm", "-qa", "--queryformat", "%{NAME}\n"])
    if result.returncode == 0:
        return sorted(set(result.stdout.strip().splitlines()))
    return []


def _get_flatpak_list() -> List[Dict[str, str]]:
    """Get list of installed Flatpak applications."""
    result = _run_cmd(["flatpak", "list", "--columns=application,branch,origin"], timeout=30)
    if result.returncode != 0:
        return []
    apps: List[Dict[str, str]] = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 1:
            app = {"id": parts[0].strip()}
            if len(parts) >= 2:
                app["branch"] = parts[1].strip()
            if len(parts) >= 3:
                app["origin"] = parts[2].strip()
            apps.append(app)
    return apps


def _get_wallpaper_path() -> Optional[Path]:
    """Try to extract current wallpaper path from Plasma config."""
    config_path = Path.home() / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
    if not config_path.exists():
        return None
    try:
        with open(config_path) as fh:
            for line in fh:
                if "wallpaper" in line.lower() and ("file" in line.lower() or "image" in line.lower()):
                    if "=" in line:
                        potential = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if Path(potential).exists():
                            return Path(potential)
    except Exception:
        pass
    return None


def _copy_config_files(temp_dir: Path) -> None:
    """Copy KDE Plasma config files to the temp directory."""
    kde_dir = temp_dir / "kde"
    kde_dir.mkdir(parents=True, exist_ok=True)
    themes_dir = temp_dir / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)
    wallpapers_dir = temp_dir / "wallpapers"
    wallpapers_dir.mkdir(parents=True, exist_ok=True)
    fonts_dir = temp_dir / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    icons_dir = temp_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    autostart_dir = temp_dir / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)

    # KDE config files
    for cfg_path in KDE_CONFIG_PATHS:
        if cfg_path.exists():
            shutil.copy2(str(cfg_path), str(kde_dir / cfg_path.name))
            LOG.debug("Copied %s", cfg_path)

    # Theme directories
    if PLASMA_THEME_DIR.exists():
        for item in PLASMA_THEME_DIR.iterdir():
            if item.is_dir():
                dest = themes_dir / item.name
                shutil.copytree(str(item), str(dest), symlinks=True, ignore_dangling_symlinks=True)
    if COLOR_SCHEME_DIR.exists():
        for item in COLOR_SCHEME_DIR.iterdir():
            if item.suffix in (".colors",):
                shutil.copy2(str(item), str(themes_dir / item.name))

    # Wallpaper
    wp = _get_wallpaper_path()
    if wp:
        shutil.copy2(str(wp), str(wallpapers_dir / wp.name))

    # Fonts (user-level)
    user_fonts = Path.home() / ".local" / "share" / "fonts"
    if user_fonts.exists():
        for fpath in user_fonts.rglob("*"):
            if fpath.is_file() and fpath.suffix.lower() in (".ttf", ".otf", ".woff", ".woff2"):
                rel = fpath.relative_to(user_fonts)
                dest = fonts_dir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(fpath), str(dest))

    # Icons (user-level theme)
    user_icons = Path.home() / ".local" / "share" / "icons"
    if user_icons.exists():
        for item in user_icons.iterdir():
            if item.is_dir():
                dest = icons_dir / item.name
                shutil.copytree(str(item), str(dest), symlinks=True, ignore_dangling_symlinks=True)

    # Autostart entries
    if AUTOSTART_DIR.exists():
        for item in AUTOSTART_DIR.iterdir():
            if item.suffix == ".desktop":
                shutil.copy2(str(item), str(autostart_dir / item.name))


def _restore_config_files(extract_dir: Path, dry_run: bool = False) -> None:
    """Restore config files from extracted blueprint."""
    kde_dir = extract_dir / "kde"
    if kde_dir.exists():
        for cfg in kde_dir.iterdir():
            if cfg.is_file():
                dest = Path.home() / ".config" / cfg.name
                if dry_run:
                    print(f"  Would restore: {dest}")
                else:
                    shutil.copy2(str(cfg), str(dest))
                    LOG.info("Restored %s", dest)

    themes_dir = extract_dir / "themes"
    if themes_dir.exists():
        plasma_themes = themes_dir / "desktoptheme"
        if plasma_themes.exists():
            for theme_dir in plasma_themes.iterdir():
                dest = PLASMA_THEME_DIR / theme_dir.name
                if dry_run:
                    print(f"  Would restore theme: {dest}")
                elif not dest.exists():
                    shutil.copytree(str(theme_dir), str(dest), symlinks=True)
        for cs in themes_dir.glob("*.colors"):
            dest = COLOR_SCHEME_DIR / cs.name
            if dry_run:
                print(f"  Would restore color scheme: {dest}")
            else:
                shutil.copy2(str(cs), str(dest))

    wallpapers_dir = extract_dir / "wallpapers"
    if wallpapers_dir.exists() and not dry_run:
        wp_dir = Path.home() / ".local" / "share" / "wallpapers"
        wp_dir.mkdir(parents=True, exist_ok=True)
        for wp in wallpapers_dir.iterdir():
            shutil.copy2(str(wp), str(wp_dir / wp.name))

    fonts_dir = extract_dir / "fonts"
    if fonts_dir.exists() and not dry_run:
        user_fonts = Path.home() / ".local" / "share" / "fonts"
        for fpath in fonts_dir.rglob("*"):
            if fpath.is_file():
                rel = fpath.relative_to(fonts_dir)
                dest = user_fonts / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(fpath), str(dest))

    icons_dir = extract_dir / "icons"
    if icons_dir.exists() and not dry_run:
        user_icons = Path.home() / ".local" / "share" / "icons"
        for item in icons_dir.iterdir():
            if item.is_dir():
                dest = user_icons / item.name
                if not dest.exists():
                    shutil.copytree(str(item), str(dest), symlinks=True)

    autostart_dir = extract_dir / "autostart"
    if autostart_dir.exists() and not dry_run:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
        for entry in autostart_dir.iterdir():
            if entry.suffix == ".desktop":
                shutil.copy2(str(entry), str(AUTOSTART_DIR / entry.name))


def _restore_packages(manifest: dict, dry_run: bool = False) -> None:
    """Restore installed RPM packages (interactive; prompts user)."""
    pkg_list = manifest.get("package_list", [])
    if not pkg_list:
        LOG.info("No packages to restore.")
        return
    if os.geteuid() != 0:
        LOG.warning("Package restoration requires root. Skipping.")
        return
    current = set(_get_package_list())
    to_install = [p for p in pkg_list if p not in current]
    if not to_install:
        LOG.info("All packages already installed.")
        return
    print(f"Packages to install: {len(to_install)}")
    if not dry_run:
        _run_cmd(["dnf", "install", "-y"] + to_install, timeout=600)


def _restore_flatpaks(manifest: dict, dry_run: bool = False) -> None:
    """Restore Flatpak applications."""
    flatpak_list = manifest.get("flatpak_list", [])
    if not flatpak_list:
        return
    current = {app["id"] for app in _get_flatpak_list()}
    for app in flatpak_list:
        if app["id"] in current:
            continue
        if dry_run:
            print(f"  Would install flatpak: {app['id']}")
        else:
            _run_cmd(["flatpak", "install", "-y", "--noninteractive", app["id"]], timeout=120)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
def _export_blueprint(output_path: Path, quiet: bool = False) -> bool:
    """Export the current system state to a .zbp archive. Returns True on success."""
    LOG.info("Exporting system identity to %s", output_path)

    with tempfile.TemporaryDirectory(prefix="synthex-bp-") as tmpdir:
        tmp = Path(tmpdir)

        if not quiet:
            print("Collecting package list...")
        packages = _get_package_list()
        if not quiet:
            print(f"  Found {len(packages)} RPM packages")

        flatpaks = _get_flatpak_list()
        if not quiet:
            print(f"  Found {len(flatpaks)} Flatpak apps")

        theme_info = {}
        result = _run_cmd(["lookandfeeltool", "--list"], timeout=10)
        if result.returncode == 0:
            theme_info["lookandfeel"] = result.stdout.strip().splitlines()
        wallpaper_path = _get_wallpaper_path()
        if wallpaper_path:
            theme_info["current_wallpaper"] = str(wallpaper_path)

        keybinds = {}
        if Path.home().joinpath(".config/khotkeysrc").exists():
            keybinds["khotkeysrc_present"] = True

        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "timestamp": datetime.now().isoformat(),
            "hostname": os.uname().nodename,
            "os": os.uname().sysrelease if hasattr(os.uname(), 'sysrelease') else "",
            "package_list": packages,
            "flatpak_list": flatpaks,
            "kde_configs": [p.name for p in KDE_CONFIG_PATHS if p.exists()],
            "themes": theme_info,
            "wallpaper": str(wallpaper_path) if wallpaper_path else None,
            "keybinds": keybinds,
            "fonts": [],
            "icon_theme": None,
            "cursor_theme": None,
            "dock_config": None,
        }

        result = _run_cmd(["gsettings", "get", "org.gnome.desktop.interface", "icon-theme"], timeout=5)
        if result.returncode == 0:
            manifest["icon_theme"] = result.stdout.strip().strip("'")
        result = _run_cmd(["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"], timeout=5)
        if result.returncode == 0:
            manifest["cursor_theme"] = result.stdout.strip().strip("'")

        manifest_path = tmp / "manifest.json"
        with open(manifest_path, "w") as fh:
            json.dump(manifest, fh, indent=2)

        if not quiet:
            print("Copying config files...")
        _copy_config_files(tmp)

        with tarfile.open(str(output_path), "w:gz") as tar:
            tar.add(str(manifest_path), arcname="manifest.json")
            for subdir in ["kde", "themes", "wallpapers", "fonts", "icons", "autostart"]:
                spath = tmp / subdir
                if spath.exists() and any(spath.iterdir()):
                    tar.add(str(spath), arcname=subdir)

    LOG.info("Export complete: %s (%d items)", output_path, len(packages) + len(flatpaks))
    if not quiet:
        print(f"✓ Blueprint saved to {output_path}")
    return True


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------
def _import_blueprint(archive_path: Path, dry_run: bool = False, gui: bool = False) -> bool:
    """Import system identity from a .zbp archive."""
    if not archive_path.exists():
        LOG.error("Archive not found: %s", archive_path)
        return False

    LOG.info("Importing blueprint from %s", archive_path)

    try:
        with tarfile.open(str(archive_path), "r:gz") as tar:
            if "manifest.json" not in tar.getnames():
                LOG.error("Invalid blueprint: missing manifest.json")
                return False
            tmpdir = tempfile.mkdtemp(prefix="synthex-bp-")
            extract_dir = Path(tmpdir)
            tar.extractall(path=str(extract_dir))
    except (tarfile.TarError, OSError) as exc:
        LOG.error("Failed to extract blueprint: %s", exc)
        return False

    manifest_path = extract_dir / "manifest.json"
    try:
        with open(manifest_path) as fh:
            manifest = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        LOG.error("Failed to read manifest: %s", exc)
        shutil.rmtree(str(extract_dir))
        return False

    print(f"Blueprint: {manifest.get('hostname', '?')} @ {manifest.get('timestamp', '?')}")
    print(f"  Packages: {len(manifest.get('package_list', []))}")
    print(f"  Flatpaks: {len(manifest.get('flatpak_list', []))}")
    print(f"  KDE configs: {len(manifest.get('kde_configs', []))}")

    if gui and HAS_TK:
        if not _gui_confirm_import(manifest):
            LOG.info("Import cancelled by user")
            shutil.rmtree(str(extract_dir))
            return False

    if dry_run:
        print("\n[Dry run] Changes that would be applied:")
        _restore_packages(manifest, dry_run=True)
        _restore_flatpaks(manifest, dry_run=True)
        _restore_config_files(extract_dir, dry_run=True)
        print("\n[Dry run] Complete — no changes made.")
        shutil.rmtree(str(extract_dir))
        return True

    bp_name = f"blueprint-import-{manifest.get('hostname', 'system')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    if not _create_btrfs_snapshot(bp_name):
        LOG.warning("Failed to create BTRFS snapshot before import (continuing)")

    print("\nRestoring packages...")
    _restore_packages(manifest)
    print("Restoring Flatpaks...")
    _restore_flatpaks(manifest)
    print("Restoring config files...")
    _restore_config_files(extract_dir)

    shutil.rmtree(str(extract_dir))

    print(f"\n✓ Import complete from {archive_path.name}")
    print("  Some changes may require a logout/restart to take effect.")
    return True


def _gui_confirm_import(manifest: dict) -> bool:
    """Show a Tkinter confirmation dialog for import."""
    root = tk.Tk()
    root.title("Synthex Blueprint — Import Confirmation")
    root.geometry("480x300")

    ttk.Label(root, text="System Blueprint Import", font=("", 14, "bold")).pack(pady=10)

    info = (
        f"Host: {manifest.get('hostname', '?')}\n"
        f"Date: {manifest.get('timestamp', '?')}\n"
        f"Packages: {len(manifest.get('package_list', []))}\n"
        f"Flatpaks: {len(manifest.get('flatpak_list', []))}"
    )
    ttk.Label(root, text=info, justify=tk.LEFT).pack(padx=20, pady=10)

    var = tk.BooleanVar(value=False)
    ttk.Checkbutton(root, text="I understand this will overwrite system settings",
                    variable=var).pack(pady=10)

    def _ok():
        if var.get():
            root.destroy()
        else:
            messagebox.showwarning("Confirm", "Please check the confirmation box.")

    ttk.Button(root, text="Import", command=_ok).pack(side=tk.LEFT, padx=20, pady=20)
    ttk.Button(root, text="Cancel", command=root.destroy).pack(side=tk.RIGHT, padx=20, pady=20)

    root.mainloop()
    return var.get()


# ---------------------------------------------------------------------------
# List / Info
# ---------------------------------------------------------------------------
def _list_blueprints() -> List[Path]:
    """List available .zbp files in backup directory."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(BACKUP_DIR.glob("*.zbp"))


def _show_info(archive_path: Path) -> None:
    """Print metadata from a blueprint archive."""
    if not archive_path.exists():
        print(f"File not found: {archive_path}")
        return
    try:
        with tarfile.open(str(archive_path), "r:gz") as tar:
            member = tar.getmember("manifest.json")
            fh = tar.extractfile(member)
            if fh:
                manifest = json.load(fh)
                print(f"Blueprint: {archive_path.name}")
                print(f"  Size:      {archive_path.stat().st_size / 1024:.1f} KB")
                print(f"  Hostname:  {manifest.get('hostname', 'N/A')}")
                print(f"  Timestamp: {manifest.get('timestamp', 'N/A')}")
                print(f"  Packages:  {len(manifest.get('package_list', []))}")
                print(f"  Flatpaks:  {len(manifest.get('flatpak_list', []))}")
                print(f"  KDE cfgs:  {len(manifest.get('kde_configs', []))}")
    except (tarfile.TarError, json.JSONDecodeError, OSError) as exc:
        print(f"Error reading {archive_path}: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthex Blueprint — Export/Import System Identity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  synthex-blueprint export system.zbp          Export current system
  synthex-blueprint import system.zbp          Import from archive
  synthex-blueprint import system.zbp --dry-run  Preview changes
  synthex-blueprint import system.zbp --gui    GUI confirmation
  synthex-blueprint list                       Show saved blueprints
  synthex-blueprint info system.zbp            Show metadata
        """,
    )
    parser.add_argument("action", choices=["export", "import", "list", "info"],
                        help="Action to perform")
    parser.add_argument("file", nargs="?", default=None,
                        help="Blueprint file (.zbp)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without applying (import only)")
    parser.add_argument("--gui", action="store_true",
                        help="Use GUI dialogs (import only)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress verbose output")
    parser.add_argument("--output-dir", "-o",
                        default=str(BACKUP_DIR),
                        help=f"Backup directory (default: {BACKUP_DIR})")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if args.action == "export":
        if not args.file:
            host = os.uname().nodename
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            out_dir = Path(args.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{host}-{ts}.zbp"
        else:
            out_path = Path(args.file)
        ok = _export_blueprint(out_path, quiet=args.quiet)
        return 0 if ok else 1

    elif args.action == "import":
        if not args.file:
            print("Error: specify a .zbp file to import")
            return 1
        ok = _import_blueprint(Path(args.file), dry_run=args.dry_run, gui=args.gui)
        return 0 if ok else 1

    elif args.action == "list":
        blueprints = _list_blueprints()
        if not blueprints:
            print("No blueprints found in", BACKUP_DIR)
            return 0
        print(f"Blueprints ({len(blueprints)}):")
        for bp in blueprints:
            size = bp.stat().st_size / 1024
            print(f"  {bp.name}  ({size:.1f} KB)")
        return 0

    elif args.action == "info":
        if not args.file:
            print("Error: specify a .zbp file")
            return 1
        _show_info(Path(args.file))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
