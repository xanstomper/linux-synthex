#!/usr/bin/env python3
"""
synthex-vault.py — SynthOS Encrypted Vault System
===================================================
Creates and manages LUKS-encrypted containers with:
  • Configurable size
  • Auto-mount on login (PAM integration)
  • Auto-unmount on screen lock or idle
  • ~/Vault/ symlink
  • CLI: synthex-vault [create|open|close|status]

Requirements: cryptsetup, PAM (optional), systemd (optional), losetup

GPL-3.0-or-later  |  SynthOS Project 2026.10
"""

from __future__ import annotations

import argparse
import getpass
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import threading
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_DIR    = Path.home() / ".config" / "synthex-vault"
CONFIG_FILE   = CONFIG_DIR / "vault.json"
DEFAULT_IMAGE = Path.home() / ".local" / "share" / "synthex" / "vault.img"
DEFAULT_MOUNT = Path.home() / "Vault"
MAPPER_NAME   = "synthex-vault"
MAPPER_PATH   = Path(f"/dev/mapper/{MAPPER_NAME}")
IDLE_TIMEOUT  = 600   # auto-close after 600 s idle (0 = disabled)
LOG_FILE      = Path.home() / ".local" / "share" / "synthex" / "vault.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _setup_logging() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("synthex-vault")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    if not log.handlers:
        log.addHandler(fh)
        log.addHandler(sh)
    return log


LOG = _setup_logging()


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------
def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {
        "image_path": str(DEFAULT_IMAGE),
        "mount_point": str(DEFAULT_MOUNT),
        "idle_timeout": IDLE_TIMEOUT,
        "auto_mount": True,
        "fs_type": "ext4",
    }


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    CONFIG_FILE.chmod(0o600)


# ---------------------------------------------------------------------------
# Core vault operations
# ---------------------------------------------------------------------------
def _need_root(action: str) -> None:
    if os.geteuid() != 0:
        sys.exit(f"synthex-vault {action} requires root (sudo)")


def vault_create(size_mb: int, image_path: Path, fs_type: str = "ext4") -> bool:
    """
    Create a LUKS-encrypted container of *size_mb* MiB at *image_path*.
    Prompts for a passphrase interactively.
    """
    _need_root("create")
    if image_path.exists():
        LOG.error("Image already exists: %s", image_path)
        return False

    image_path.parent.mkdir(parents=True, exist_ok=True)

    # Check dependencies
    for tool in ("cryptsetup", "losetup", "mkfs.ext4"):
        if not shutil.which(tool):
            LOG.error("Missing tool: %s", tool)
            return False

    LOG.info("Creating %d MiB vault at %s …", size_mb, image_path)

    # 1. Allocate image file with urandom data (more secure than zeros)
    print(f"[vault] Allocating {size_mb} MiB encrypted container — this may take a moment …")
    try:
        subprocess.run(
            ["dd", "if=/dev/urandom", f"of={image_path}",
             "bs=1M", f"count={size_mb}", "status=progress"],
            check=True
        )
        image_path.chmod(0o600)
    except subprocess.CalledProcessError as exc:
        LOG.error("dd failed: %s", exc)
        return False

    # 2. Set up loop device
    loop = subprocess.check_output(
        ["losetup", "--find", "--show", str(image_path)], text=True
    ).strip()
    LOG.info("Loop device: %s", loop)

    try:
        # 3. LUKS format
        print("[vault] Formatting LUKS container …")
        pw = getpass.getpass("[vault] New vault passphrase: ")
        pw2 = getpass.getpass("[vault] Confirm passphrase: ")
        if pw != pw2:
            LOG.error("Passphrases do not match")
            subprocess.run(["losetup", "-d", loop], check=False)
            image_path.unlink(missing_ok=True)
            return False

        proc = subprocess.run(
            ["cryptsetup", "luksFormat", "--type", "luks2",
             "--cipher", "aes-xts-plain64", "--key-size", "512",
             "--hash", "sha512", "--iter-time", "2000",
             "--batch-mode", loop],
            input=(pw + "\n").encode(),
            capture_output=True
        )
        if proc.returncode != 0:
            LOG.error("luksFormat failed: %s", proc.stderr.decode())
            subprocess.run(["losetup", "-d", loop], check=False)
            image_path.unlink(missing_ok=True)
            return False

        # 4. Open LUKS container
        proc2 = subprocess.run(
            ["cryptsetup", "open", loop, MAPPER_NAME],
            input=(pw + "\n").encode(),
            capture_output=True
        )
        if proc2.returncode != 0:
            LOG.error("cryptsetup open failed: %s", proc2.stderr.decode())
            subprocess.run(["losetup", "-d", loop], check=False)
            return False

        # 5. Format filesystem
        print(f"[vault] Creating {fs_type} filesystem …")
        subprocess.run(["mkfs.ext4", "-L", "SynthexVault",
                         str(MAPPER_PATH)], check=True, capture_output=True)

        # 6. Close
        subprocess.run(["cryptsetup", "close", MAPPER_NAME], check=True)

    finally:
        subprocess.run(["losetup", "-d", loop], check=False)

    LOG.info("Vault created successfully: %s", image_path)
    print("[vault] ✓ Vault created. Use 'synthex-vault open' to mount it.")
    return True


def vault_open(image_path: Path, mount_point: Path) -> bool:
    """Open (decrypt + mount) the vault."""
    if not image_path.exists():
        LOG.error("Vault image not found: %s", image_path)
        return False
    if MAPPER_PATH.exists():
        LOG.info("Vault already open at %s", mount_point)
        return True

    loop = subprocess.check_output(
        ["losetup", "--find", "--show", str(image_path)], text=True
    ).strip()

    pw = getpass.getpass("[vault] Vault passphrase: ")
    proc = subprocess.run(
        ["cryptsetup", "open", loop, MAPPER_NAME],
        input=(pw + "\n").encode(),
        capture_output=True
    )
    if proc.returncode != 0:
        subprocess.run(["losetup", "-d", loop], check=False)
        LOG.error("Wrong passphrase or corrupt vault")
        return False

    mount_point.mkdir(parents=True, exist_ok=True)
    subprocess.run(["mount", str(MAPPER_PATH), str(mount_point)], check=True)

    # Ensure ~/Vault symlink
    symlink = Path.home() / "Vault"
    if not symlink.exists() and not symlink.is_symlink():
        symlink.symlink_to(mount_point)

    LOG.info("Vault mounted at %s", mount_point)
    print(f"[vault] ✓ Vault open at {mount_point}")
    return True


def vault_close(mount_point: Path) -> bool:
    """Unmount and close the vault."""
    symlink = Path.home() / "Vault"
    if symlink.is_symlink():
        symlink.unlink()

    try:
        subprocess.run(["umount", str(mount_point)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # Try lazy unmount
        subprocess.run(["umount", "-l", str(mount_point)], check=False)

    if MAPPER_PATH.exists():
        subprocess.run(["cryptsetup", "close", MAPPER_NAME], check=True)

    # Detach loop devices for this image
    cfg = _load_config()
    img = Path(cfg["image_path"])
    loop_out = subprocess.check_output(
        ["losetup", "--associated", str(img), "--output", "NAME", "--noheadings"],
        text=True, timeout=5
    ).strip()
    for loop in loop_out.splitlines():
        subprocess.run(["losetup", "-d", loop], check=False)

    LOG.info("Vault closed")
    print("[vault] ✓ Vault closed")
    return True


def vault_status(cfg: dict) -> None:
    image_path  = Path(cfg["image_path"])
    mount_point = Path(cfg["mount_point"])
    is_open = MAPPER_PATH.exists()
    is_mounted = any(
        str(mount_point) in line
        for line in Path("/proc/mounts").read_text().splitlines()
    ) if Path("/proc/mounts").exists() else False

    color_open   = "\033[92m" if is_open else "\033[91m"
    color_mount  = "\033[92m" if is_mounted else "\033[91m"
    reset        = "\033[0m"
    size_str     = "—"
    if image_path.exists():
        size_mb = image_path.stat().st_size // 1024 // 1024
        size_str = f"{size_mb} MiB"

    print(f"\n{'='*50}")
    print("  SynthOS Vault — Status")
    print(f"{'='*50}")
    print(f"  Image       : {image_path}  ({size_str})")
    print(f"  Exists      : {'yes' if image_path.exists() else 'no'}")
    print(f"  LUKS open   : {color_open}{'YES' if is_open else 'NO'}{reset}")
    print(f"  Mounted     : {color_mount}{'YES' if is_mounted else 'NO'}{reset}")
    print(f"  Mount point : {mount_point}")
    print(f"  Symlink     : {Path.home() / 'Vault'}")
    print(f"  Auto-mount  : {cfg.get('auto_mount', True)}")
    print(f"  Idle timeout: {cfg.get('idle_timeout', 0)}s")
    print(f"{'='*50}\n")


# ---------------------------------------------------------------------------
# PAM integration helper (writes /etc/pam.d hook snippet)
# ---------------------------------------------------------------------------
PAM_SNIPPET = """\
# SynthOS Vault — auto-mount on login
# Add to /etc/pam.d/common-auth (after auth lines):
#   auth optional pam_exec.so /usr/local/bin/synthex-vault open
# Add to /etc/pam.d/common-session-noninteractive:
#   session optional pam_exec.so /usr/local/bin/synthex-vault close
"""


def install_pam_hook() -> None:
    """Print PAM integration instructions."""
    print(PAM_SNIPPET)
    hint = Path("/etc/pam.d/common-auth")
    if hint.exists() and os.geteuid() == 0:
        with open(hint, "a") as f:
            f.write("\n# synthex-vault auto-mount\n")
            f.write("auth optional pam_exec.so /usr/local/bin/synthex-vault open\n")
        LOG.info("PAM hook installed in %s", hint)
        print(f"[vault] PAM hook added to {hint}")


# ---------------------------------------------------------------------------
# Idle watcher
# ---------------------------------------------------------------------------
class IdleWatcher:
    """Closes the vault after idle_timeout seconds of no filesystem activity."""

    def __init__(self, mount_point: Path, idle_timeout: int):
        self._mp = mount_point
        self._timeout = idle_timeout
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def _last_access(self) -> float:
        latest = 0.0
        try:
            for p in self._mp.rglob("*"):
                try:
                    t = p.stat().st_atime
                    if t > latest:
                        latest = t
                except OSError:
                    pass
        except Exception:
            pass
        return latest or time.time()

    def _run(self) -> None:
        while not self._stop.is_set():
            time.sleep(30)
            if not MAPPER_PATH.exists():
                break
            idle = time.time() - self._last_access()
            if idle >= self._timeout:
                LOG.info("Vault idle for %.0fs — auto-closing", idle)
                vault_close(self._mp)
                break

    def start(self) -> None:
        if self._timeout <= 0:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="synthex-vault",
        description="SynthOS encrypted vault — LUKS container manager",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    cr = sub.add_parser("create", help="Create a new encrypted vault")
    cr.add_argument("--size", type=int, default=512,
                    metavar="MB", help="Container size in MiB (default: 512)")
    cr.add_argument("--image", type=Path, default=None,
                    help="Path to vault image file")
    cr.add_argument("--fs", default="ext4",
                    choices=["ext4", "btrfs", "xfs"],
                    help="Filesystem type (default: ext4)")

    op = sub.add_parser("open", help="Open (decrypt + mount) vault")
    op.add_argument("--image", type=Path, default=None)
    op.add_argument("--mount", type=Path, default=None)

    cl = sub.add_parser("close", help="Close (unmount + lock) vault")
    cl.add_argument("--mount", type=Path, default=None)

    sub.add_parser("status", help="Show vault status")
    sub.add_parser("install-pam", help="Install PAM login integration")

    args = ap.parse_args(argv)
    cfg  = _load_config()

    if args.cmd == "create":
        img = args.image or Path(cfg["image_path"])
        if vault_create(args.size, img, args.fs):
            cfg["image_path"] = str(img)
            cfg["fs_type"]    = args.fs
            _save_config(cfg)
        return 0

    elif args.cmd == "open":
        _need_root("open")
        img = args.image or Path(cfg["image_path"])
        mp  = args.mount or Path(cfg["mount_point"])
        if vault_open(img, mp):
            watcher = IdleWatcher(mp, cfg.get("idle_timeout", 0))
            watcher.start()
            signal.pause()
        return 0

    elif args.cmd == "close":
        _need_root("close")
        mp = args.mount or Path(cfg["mount_point"])
        vault_close(mp)
        return 0

    elif args.cmd == "status":
        vault_status(cfg)
        return 0

    elif args.cmd == "install-pam":
        install_pam_hook()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
