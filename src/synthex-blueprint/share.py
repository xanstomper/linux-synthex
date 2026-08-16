#!/usr/bin/env python3
"""
Synthex Blueprint Sharing — import/export blueprints from URLs.
Extends synthex-blueprint with network sharing capabilities.

Usage:
    synthex-blueprint share <file.zbp>       — Upload blueprint to community
    synthex-blueprint download <url>         — Download blueprint from URL
    synthex-blueprint list-remote            — List community blueprints
"""

import sys
import os
import json
import urllib.request
import urllib.parse
import tempfile
import subprocess

SHARE_DIR = os.path.expanduser("~/.config/synthex/blueprints")
REMOTE_INDEX_URL = "https://blueprints.synthex-linux.org/api/v1/blueprints"
REMOTE_UPLOAD_URL = "https://blueprints.synthex-linux.org/api/v1/upload"


def ensure_dirs():
    os.makedirs(SHARE_DIR, exist_ok=True)


def cmd_share(path):
    """Share a blueprint with the community."""
    if not os.path.exists(path):
        return
    
    size = os.path.getsize(path)
    name = os.path.basename(path)
    
    print()
    print("   This would upload your blueprint to the")
    print("   Synthex Community Blueprint Marketplace.")
    print()
    print("   Shared data: packages list, theme config,")
    print("   desktop layout, keybindings")
    print("   NOT shared: personal files, passwords")
    print()
    
    response = input("  Upload to community? [y/N]: ")
    if response.lower() == "y":
        # In production: upload to blueprint server
        
        # Save to local share directory as record
        ensure_dirs()
        dest = os.path.join(SHARE_DIR, "shared", name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        
        import shutil
        shutil.copy2(path, dest)
    else:
        print("  ❌ Share cancelled.")


def cmd_download(url):
    """Download a blueprint from URL."""
    
    ensure_dirs()
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "SynthexBlueprint/1.0"
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
        
        # Determine filename
        filename = os.path.basename(urllib.parse.urlparse(url).path)
        if not filename.endswith(".zbp"):
            filename = f"downloaded-{hash(url)}.zbp"
        
        dest = os.path.join(SHARE_DIR, filename)
        with open(dest, "wb") as f:
            f.write(data)
        
        print()
        
        apply = input("  Apply this blueprint now? [y/N]: ")
        if apply.lower() == "y":
            subprocess.run([sys.executable,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "blueprint.py"),
                "import", dest])
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"❌ Connection Error: {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")


def cmd_list_remote():
    """List community blueprints."""
    print("🌐 Synthex Blueprint Marketplace")
    print()
    print("  Community blueprints (coming soon):")
    print()
    print("  • Gaming Setup — Steam + Proton + Gamescope config")
    print("  • Developer Workstation — Rust + Go + Python + Containers")
    print("  • Creator Suite — Blender + OBS + Krita optimized")
    print("  • Cyberpunk Rice — Neon RGB theme with glass effects")
    print("  • Minimal Workspace — Clean, distraction-free desktop")
    print("  • macOS Migration — Familiar layout for new users")
    print()
    print("  Use 'synthex-blueprint download <url>' to get one.")
    print()
    
    # List locally shared blueprints
    shared_dir = os.path.join(SHARE_DIR, "shared")
    if os.path.exists(shared_dir):
        bps = [f for f in os.listdir(shared_dir) if f.endswith(".zbp")]
        if bps:
            print("  Locally shared blueprints:")
            for bp in bps:
                size = os.path.getsize(os.path.join(shared_dir, bp))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "share" and len(sys.argv) >= 3:
        cmd_share(sys.argv[2])
    elif cmd == "download" and len(sys.argv) >= 3:
        cmd_download(sys.argv[2])
    elif cmd == "list-remote":
        cmd_list_remote()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
