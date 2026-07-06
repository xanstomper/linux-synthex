#!/usr/bin/env python3
"""
Solus Web App Engine — Turn websites into native desktop apps
===============================================================
Daemon and CLI tool for creating, managing, and removing web applications.

Daemon mode (solus-webappd):
  - Listens on a Unix socket or D-Bus for app management requests
  - Manages sandbox profiles, .desktop files, and launcher scripts

CLI mode (solus-webapp):
  create <url>     Create a new web app
  list             List registered web apps
  remove <app-id>  Remove a web app

Features:
  - Generates .desktop entries in ~/.local/share/applications/
  - Creates sandbox profiles using bubblewrap (bwrap) when available
  - Generates SVG-based application icons
  - GPU acceleration presets for Chromium-based runtime
  - Native desktop notifications via notify-send
  - Config stored in ~/.config/solus/webapps/
"""

import argparse
import hashlib
import json
import logging
import os
import re
import socket
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

LOG = logging.getLogger("solus-webappd")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_DIR = Path.home() / ".config" / "solus" / "webapps"
ENGINE_CONFIG_DIR = Path.home() / ".config" / "solus" / "webapp-engine"
ENGINE_CONFIG_FILE = ENGINE_CONFIG_DIR / "config.json"
DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"
ICON_DIR = Path.home() / ".local" / "share" / "icons" / "solus-webapps"
BIN_DIR = Path.home() / ".local" / "bin"
SOCKET_PATH = Path("/tmp/solus-webappd.sock")

DEFAULT_CONFIG = {
    "browser": "chromium",
    "default_sandbox": "strict",
    "default_gpu": "balanced",
    "enable_notifications": True,
}

GPU_FLAGS = {
    "high": [
        "--enable-gpu-rasterization",
        "--enable-accelerated-video-decode",
        "--enable-accelerated-2d-canvas",
        "--enable-features=VaapiVideoDecoder,VaapiVideoEncoder,VaapiIgnoreDriverChecks",
        "--ignore-gpu-blocklist",
        "--enable-native-gpu-memory-buffers",
        "--enable-zero-copy",
        "--disable-software-rasterizer",
    ],
    "balanced": [
        "--enable-gpu-rasterization",
        "--enable-accelerated-video-decode",
        "--enable-features=VaapiVideoDecoder",
        "--ignore-gpu-blocklist",
        "--enable-native-gpu-memory-buffers",
    ],
}

BWRAP_TEMPLATE = """#!/bin/bash
# Solus Web App sandbox wrapper - {app_name}
set -euo pipefail
APP_NAME="{app_name}"
APP_URL="{app_url}"
APP_DIR="{app_dir}"
CHROMIUM="{browser}"
GPU_FLAGS=({gpu_flags})
if command -v bwrap &>/dev/null && [ "{sandbox}" = "strict" ]; then
    exec bwrap \\
        --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /lib64 /lib64 \\
        --ro-bind /bin /bin --ro-bind /etc /etc --proc /proc --dev /dev \\
        --ro-bind /sys /sys --bind "$HOME" "$HOME" --tmpfs /tmp \\
        --unshare-all --new-session --die-with-parent -- \\
        "$CHROMIUM" --app="$APP_URL" --no-first-run --no-default-browser-check \\
        --user-data-dir="$APP_DIR/chrome-data" "${{GPU_FLAGS[@]}}" "$@"
else
    exec "$CHROMIUM" --app="$APP_URL" --no-first-run --no-default-browser-check \\
        --user-data-dir="$APP_DIR/chrome-data" "${{GPU_FLAGS[@]}}" "$@"
fi
"""


def _load_engine_config() -> dict:
    if ENGINE_CONFIG_FILE.exists():
        try:
            with open(ENGINE_CONFIG_FILE) as fh:
                cfg = json.load(fh)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def _save_engine_config(cfg: dict) -> None:
    ENGINE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENGINE_CONFIG_FILE, "w") as fh:
        json.dump(cfg, fh, indent=2)


def _app_dir(app_id: str) -> Path:
    return CONFIG_DIR / app_id


def _app_metadata_path(app_id: str) -> Path:
    return _app_dir(app_id) / "metadata.json"


def _desktop_file_path(app_id: str) -> Path:
    return DESKTOP_DIR / f"webapp-{app_id}.desktop"


def _icon_path(app_id: str) -> Path:
    return ICON_DIR / f"{app_id}.svg"


def _launcher_path(app_id: str) -> Path:
    return BIN_DIR / f"webapp-{app_id}"


def _list_apps() -> List[Dict]:
    apps: List[Dict] = []
    if not CONFIG_DIR.exists():
        return apps
    for entry in sorted(CONFIG_DIR.iterdir()):
        mf = entry / "metadata.json"
        if mf.exists():
            try:
                data = json.loads(mf.read_text())
                data["app_id"] = entry.name
                apps.append(data)
            except (json.JSONDecodeError, OSError):
                pass
    return apps


def _get_app(app_id: str) -> Optional[Dict]:
    meta = _app_metadata_path(app_id)
    if meta.exists():
        try:
            data = json.loads(meta.read_text())
            data["app_id"] = app_id
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _generate_app_id(url: str, name: Optional[str] = None) -> str:
    if name:
        base = name.lower().replace(" ", "-").replace("_", "-")
        base = re.sub(r"[^a-z0-9-]", "", base)
        if base:
            return base[:32]
    h = hashlib.sha256(url.encode()).hexdigest()[:12]
    domain = re.sub(r"^https?://", "", url).split("/")[0].replace(".", "-")
    return f"{domain}-{h}"


def _generate_svg_icon(url: str, app_name: str, size: int = 128) -> str:
    letter = app_name[0].upper() if app_name else "W"
    domain = re.sub(r"^https?://", "", url).split("/")[0]
    h = hashlib.md5(domain.encode()).hexdigest()
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    text_color = "#ffffff" if brightness < 128 else "#1a1a1a"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:rgb({min(r+40,255)},{min(g+40,255)},{min(b+40,255)})"/>
      <stop offset="100%" style="stop-color:rgb({r},{g},{b})"/>
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" rx="{size//5}" fill="url(#bg)"/>
  <text x="50%" y="55%" dominant-baseline="middle" text-anchor="middle"
        font-family="sans-serif" font-size="{size//2}" font-weight="bold"
        fill="{text_color}">{letter}</text>
</svg>'''


def _generate_desktop_entry(app_id: str, name: str, url: str, category: str) -> str:
    cats = {
        "development": "Development;Web Development;", "social": "Network;InstantMessaging;",
        "office": "Office;", "media": "AudioVideo;", "games": "Game;",
        "news": "Network;News;", "utilities": "Utility;",
    }
    cat_str = cats.get(category, "Network;")
    return f"""[Desktop Entry]
Type=Application
Name={name}
Comment={name} - Solus Web App
Exec={_launcher_path(app_id)} %U
Icon={_icon_path(app_id)}
Terminal=false
Categories={cat_str}
Keywords=web;app;{name.lower()};
StartupNotify=true
X-Solus-WebApp=true
X-Solus-WebApp-Id={app_id}
X-Solus-WebApp-Url={url}
"""


def create_web_app(url: str, name: Optional[str] = None,
                   gpu: str = "balanced", sandbox: str = "strict",
                   category: str = "Network") -> bool:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    app_name = name or re.sub(r"^https?://", "", url).split("/")[0].capitalize()
    app_id = _generate_app_id(url, name)
    if _get_app(app_id):
        LOG.error("Web app '%s' already exists (ID: %s)", app_name, app_id)
        return False
    engine_cfg = _load_engine_config()
    browser = engine_cfg.get("browser", "chromium")

    _app_dir(app_id).mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    metadata = {
        "name": app_name, "url": url, "app_id": app_id,
        "gpu_profile": gpu, "sandbox": sandbox, "category": category,
        "created": datetime.now().isoformat(), "browser": browser, "version": 1,
    }
    _app_metadata_path(app_id).write_text(json.dumps(metadata, indent=2))
    LOG.info("Created metadata for %s", app_id)

    _icon_path(app_id).write_text(_generate_svg_icon(url, app_name))
    LOG.info("Created icon")

    gpu_flags = " ".join(GPU_FLAGS.get(gpu, GPU_FLAGS["balanced"]))
    launcher = BWRAP_TEMPLATE.format(
        app_name=app_name, app_url=url, app_dir=str(_app_dir(app_id)),
        browser=browser, gpu_flags=gpu_flags, sandbox=sandbox,
    )
    lp = _launcher_path(app_id)
    lp.write_text(launcher)
    lp.chmod(lp.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    LOG.info("Created launcher")

    _desktop_file_path(app_id).write_text(_generate_desktop_entry(app_id, app_name, url, category))
    LOG.info("Created desktop entry")

    if sandbox == "strict":
        profile = _app_dir(app_id) / "sandbox.conf"
        profile.write_text(f"# Sandbox profile for {app_name}\ntype=bwrap\nnet=yes\naudio=yes\ndri=yes\n")

    print(f"✓ Web app '{app_name}' created (ID: {app_id})")
    print(f"  URL: {url}  |  GPU: {gpu}  |  Sandbox: {sandbox}")
    return True


def remove_web_app(app_id: str) -> bool:
    app = _get_app(app_id)
    if not app:
        LOG.error("Web app '%s' not found", app_id)
        return False
    name = app.get("name", app_id)
    for p in [_desktop_file_path(app_id), _launcher_path(app_id), _icon_path(app_id)]:
        if p.exists(): p.unlink()
    d = _app_dir(app_id)
    if d.exists():
        import shutil
        shutil.rmtree(str(d), ignore_errors=True)
    print(f"✓ Web app '{name}' removed ({app_id})")
    return True


def list_web_apps() -> None:
    apps = _list_apps()
    if not apps:
        print("No web apps registered.")
        return
    print(f"Registered web apps ({len(apps)}):")
    print(f"  {'ID':<32} {'Name':<24} {'GPU':<10} {'Sandbox':<8}")
    print(f"  {'-'*32} {'-'*24} {'-'*10} {'-'*8}")
    for a in apps:
        print(f"  {a.get('app_id','?'):<32} {a.get('name','?'):<24} {a.get('gpu_profile','?'):<10} {a.get('sandbox','?'):<8}")


class WebAppDaemon:
    def __init__(self) -> None:
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"Solus Web App Daemon running (PID: {os.getpid()}, socket: {SOCKET_PATH})")

    def stop(self) -> None:
        self._running = False
        if SOCKET_PATH.exists(): SOCKET_PATH.unlink()

    def _run(self) -> None:
        if SOCKET_PATH.exists(): SOCKET_PATH.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(SOCKET_PATH))
        server.listen(5)
        server.settimeout(1.0)
        try:
            while self._running:
                try:
                    conn, _ = server.accept()
                    threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
                except socket.timeout: continue
        finally:
            server.close()
            if SOCKET_PATH.exists(): SOCKET_PATH.unlink()

    def _handle(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(65536).decode("utf-8")
            if not data: return
            req = json.loads(data)
            action = req.get("action")
            if action == "create":
                ok = create_web_app(req["url"], req.get("name"), req.get("gpu","balanced"),
                                     req.get("sandbox","strict"), req.get("category","Network"))
                conn.sendall(json.dumps({"status": "ok" if ok else "error"}).encode())
            elif action == "remove":
                ok = remove_web_app(req["app_id"])
                conn.sendall(json.dumps({"status": "ok" if ok else "error"}).encode())
            elif action == "list":
                conn.sendall(json.dumps({"status": "ok", "apps": _list_apps()}).encode())
            elif action == "info":
                app = _get_app(req["app_id"])
                conn.sendall(json.dumps({"status": "ok" if app else "not_found", "app": app}).encode())
            else:
                conn.sendall(json.dumps({"status": "error", "message": f"Unknown action: {action}"}).encode())
        except Exception:
            pass
        finally:
            conn.close()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Solus Web App Engine")
    p.add_argument("--daemon", action="store_true", help="Run as daemon")
    sub = p.add_subparsers(dest="command")
    pc = sub.add_parser("create", help="Create a web app")
    pc.add_argument("url", help="Website URL")
    pc.add_argument("--name", "-n", help="Friendly name")
    pc.add_argument("--gpu", choices=["high", "balanced"], default="balanced")
    pc.add_argument("--sandbox", choices=["strict", "none"], default="strict")
    pc.add_argument("--category", "-c", default="Network")
    sub.add_parser("list", help="List web apps")
    pr = sub.add_parser("remove", help="Remove a web app")
    pr.add_argument("app_id", help="App ID to remove")
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    if args.daemon:
        d = WebAppDaemon()
        try:
            d.start()
            while True: time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            d.stop()
        return 0
    if args.command == "create":
        return 0 if create_web_app(args.url, args.name, args.gpu, args.sandbox, args.category) else 1
    elif args.command == "list":
        list_web_apps(); return 0
    elif args.command == "remove":
        return 0 if remove_web_app(args.app_id) else 1
    print("Specify a command or --daemon"); return 1


if __name__ == "__main__":
    sys.exit(main())
