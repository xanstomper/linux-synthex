#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Desktop Daemon — background compositor helper and session manager

import sys, os, signal, time, threading, subprocess, logging
logging.basicConfig(level=logging.INFO, format="[desktopd] %(levelname)s %(message)s")
log = logging.getLogger("desktopd")

POLL_INTERVAL = 10  # seconds — compositor health check every 10 s (was 30)

def run(cmd, timeout=5):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None

def ensure_compositor():
    """Make sure KWin compositor is running."""
    r = run(["pgrep","-x","kwin_wayland"])
    if not r or r.returncode != 0:
        r2 = run(["pgrep","-x","kwin_x11"])
        if not r2 or r2.returncode != 0:
            log.warning("KWin not running, attempting restart")
            subprocess.Popen(["kwin_wayland","--replace"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def apply_night_color():
    """Enable/disable night color based on time of day."""
    hour = time.localtime().tm_hour
    if 21 <= hour or hour < 7:
        run(["kwriteconfig5","--file","kwinrc",
             "--group","NightColor","--key","Active","true"])
    else:
        run(["kwriteconfig5","--file","kwinrc",
             "--group","NightColor","--key","Active","false"])

def sync_wallpaper():
    """Apply wallpaper if it was changed by theme."""
    wp_file = os.path.expanduser("~/.config/synthex-wallpaper")
    if os.path.exists(wp_file):
        wp_dir = open(wp_file).read().strip()
        if wp_dir and os.path.isdir(wp_dir):
            run(["plasma-apply-wallpaperimage", wp_dir], timeout=10)

def main():
    log.info(f"SynthOS Desktop Daemon starting (pid={os.getpid()})")

    # Graceful shutdown
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: sys.exit(0))

    # Initial setup
    time.sleep(5)  # Wait for session to settle
    ensure_compositor()
    sync_wallpaper()
    apply_night_color()

    # Main loop
    while True:
        time.sleep(POLL_INTERVAL)
        ensure_compositor()
        apply_night_color()

if __name__ == "__main__":
    main()
