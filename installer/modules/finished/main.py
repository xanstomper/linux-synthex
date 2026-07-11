#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: finished
# Performs final cleanup after installation, writes install metadata to
# /etc/synthex/install.json, and handles the reboot/shutdown selection.

import datetime
import json
import os
import platform
import subprocess

try:
    import libcalamares
    from libcalamares.utils import debug, warning
    _GS      = libcalamares.globalStorage
    _JOB_CFG = libcalamares.job.configuration
except (ImportError, AttributeError):
    class _FakeGS:
        _d = {
            "rootMountPoint":       "/mnt",
            "synthexEdition":       "Plasma",
            "synthexProfile":       "classic",
            "synthexPrimaryUser":   "synthos",
            "synthexLookAndFeel":   "org.synthos.desktop.classic",
            "locale":               "en_US.UTF-8",
            "timezone":             "America/New_York",
            "keyboardLayout":       "us",
            "restartNowEnabled":    True,
            "restartNowChecked":    True,
            "localeConfigured":     True,
            "networkcfgConfigured": True,
            "servicesConfigured":   True,
            "synthexUserConfigured": True,
            "shellprocessCompleted": True,
        }
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "restartNowEnabled":  True,
            "restartNowChecked":  True,
            "show":               True,
            "actions":            ["restart", "eject", "close"],
            "message":            "Installation complete! Welcome to SynthOS!",
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[finished] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[finished] {m}")
    def warning(m): print(f"[finished] WARN: {m}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chroot(root: str, cmd: list, timeout: int = 60):
    try:
        r = subprocess.run(
            ["chroot", root] + cmd,
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            debug(f"[finished] rc={r.returncode} {' '.join(cmd)}: {out[:300]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except Exception as exc:
        return 1, str(exc)


def _write(path: str, content: str, mode: int = 0o644) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, mode)


def _write_json(path: str, data: dict, mode: int = 0o644) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    os.chmod(path, mode)


# ---------------------------------------------------------------------------
# Sub-steps
# ---------------------------------------------------------------------------

def _write_install_metadata(root: str) -> None:
    """Write /etc/synthex/install.json with installation details."""
    now = datetime.datetime.utcnow().isoformat() + "Z"

    # Collect kernel version from chroot
    kernel = ""
    rc, out = _chroot(root, ["uname", "-r"], timeout=10)
    if rc == 0:
        kernel = out.strip()
    if not kernel:
        # Peek at installed kernels
        try:
            vmlinuz_dir = os.path.join(root, "boot")
            if os.path.isdir(vmlinuz_dir):
                vmlinuz = [f for f in os.listdir(vmlinuz_dir) if f.startswith("vmlinuz-")]
                if vmlinuz:
                    kernel = sorted(vmlinuz)[-1].replace("vmlinuz-", "")
        except OSError:
            pass

    metadata = {
        "synthosVersion":   "2026.10",
        "edition":          _GS.value("synthexEdition")     or "Plasma",
        "profile":          _GS.value("synthexProfile")     or "classic",
        "installedAt":      now,
        "timezone":         _GS.value("timezone")           or "UTC",
        "locale":           _GS.value("locale")             or "en_US.UTF-8",
        "keyboardLayout":   _GS.value("keyboardLayout")     or "us",
        "primaryUser":      _GS.value("synthexPrimaryUser") or "",
        "lookAndFeel":      _GS.value("synthexLookAndFeel") or "",
        "kernel":           kernel,
        "installerVersion": "calamares-3.3",
        "steps": {
            "locale":       bool(_GS.value("localeConfigured")),
            "networkcfg":   bool(_GS.value("networkcfgConfigured")),
            "services":     bool(_GS.value("servicesConfigured")),
            "users":        bool(_GS.value("synthexUserConfigured")),
            "shellprocess": bool(_GS.value("shellprocessCompleted")),
        },
    }

    meta_path = os.path.join(root, "etc/synthex/install.json")
    _write_json(meta_path, metadata, mode=0o644)
    debug(f"[finished] Install metadata written to {meta_path}")


def _final_mkinitcpio(root: str) -> None:
    """Regenerate initramfs to include all installed modules (best-effort)."""
    # Try dracut first (SynthOS default), then mkinitcpio (Arch-style)
    dracut = os.path.join(root, "usr/bin/dracut")
    if os.path.isfile(dracut):
        libcalamares.prettyStatus("Regenerating initramfs (dracut)…")
        rc, _ = _chroot(root, ["dracut", "--force", "--regenerate-all"], timeout=180)
        if rc == 0:
            debug("[finished] dracut initramfs regenerated")
            return
        warning("[finished] dracut failed — trying mkinitcpio")

    mkinitcpio = os.path.join(root, "usr/bin/mkinitcpio")
    if os.path.isfile(mkinitcpio):
        libcalamares.prettyStatus("Regenerating initramfs (mkinitcpio)…")
        rc, _ = _chroot(root, ["mkinitcpio", "-P"], timeout=180)
        if rc == 0:
            debug("[finished] mkinitcpio initramfs regenerated")
            return
        warning("[finished] mkinitcpio also failed")

    debug("[finished] No initramfs tool found — skipping regeneration")


def _final_grub_update(root: str) -> None:
    """Update GRUB boot configuration (best-effort)."""
    grub2_cfg  = "/boot/grub2/grub.cfg"
    grub_cfg   = "/boot/grub/grub.cfg"
    mkconfig   = os.path.join(root, "usr/sbin/grub2-mkconfig")
    mkconfig_a = os.path.join(root, "usr/sbin/grub-mkconfig")

    if os.path.isfile(mkconfig):
        libcalamares.prettyStatus("Updating GRUB configuration…")
        rc, _ = _chroot(root, ["grub2-mkconfig", "-o", grub2_cfg], timeout=60)
        if rc != 0:
            _chroot(root, ["grub2-mkconfig", "-o", grub_cfg], timeout=60)
        debug("[finished] GRUB config updated (grub2-mkconfig)")
    elif os.path.isfile(mkconfig_a):
        libcalamares.prettyStatus("Updating GRUB configuration…")
        rc, _ = _chroot(root, ["grub-mkconfig", "-o", grub_cfg], timeout=60)
        debug(f"[finished] GRUB config updated (grub-mkconfig), rc={rc}")
    else:
        debug("[finished] grub-mkconfig not found — skipping GRUB update")


def _clean_installer_artifacts(root: str) -> None:
    """Remove live-ISO / installer-only files from the target."""
    artifacts = [
        "etc/calamares",
        "root/calamares",
        "usr/share/calamares",
        "etc/calamares.conf",
        # Live-system scripts that must not persist
        "usr/libexec/calamares-runner",
    ]
    for rel in artifacts:
        full = os.path.join(root, rel)
        if os.path.islink(full):
            os.remove(full)
            debug(f"[finished] Removed symlink: /{rel}")
        elif os.path.isfile(full):
            os.remove(full)
            debug(f"[finished] Removed file: /{rel}")
        # Intentionally not recursively removing directories to avoid accidents

    # Clear pacman/dnf/apt caches to save space
    for cache_dir in ["var/cache/dnf", "var/cache/pacman/pkg", "var/cache/apt/archives"]:
        full = os.path.join(root, cache_dir)
        if os.path.isdir(full):
            _chroot(root, ["sh", "-c", f"rm -rf /{cache_dir}/*.rpm "
                                        f"/{cache_dir}/*.deb "
                                        f"/{cache_dir}/*.pkg.tar.* 2>/dev/null || true"],
                    timeout=30)
            debug(f"[finished] Cleared cache: /{cache_dir}")


def _sync_filesystems() -> None:
    """Flush all pending writes to disk."""
    try:
        subprocess.run(["sync"], timeout=60)
        debug("[finished] Filesystem sync complete")
    except Exception as exc:
        warning(f"[finished] sync failed: {exc}")


def _handle_reboot(cfg: dict) -> None:
    """
    Signal reboot or shutdown if requested.
    In Calamares this is handled by the finished *view* module; the job module
    just records the intent so the view can act on it.
    """
    restart_enabled = bool(cfg.get("restartNowEnabled", True))
    restart_checked = bool(cfg.get("restartNowChecked", True))

    _GS.insert("restartNowEnabled", restart_enabled)
    _GS.insert("restartNowChecked", restart_checked)

    if restart_enabled and restart_checked:
        debug("[finished] System will restart after installer closes")
    else:
        debug("[finished] No automatic restart configured")


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "Finishing Installation"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    cfg = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}

    debug(f"[finished] Final cleanup in {root}")

    # ── 1. Write installation metadata ────────────────────────────────────────
    libcalamares.prettyStatus("Writing installation metadata…")
    try:
        _write_install_metadata(root)
    except Exception as exc:
        warning(f"[finished] Could not write install.json: {exc}")

    # ── 2. Regenerate initramfs ───────────────────────────────────────────────
    _final_mkinitcpio(root)

    # ── 3. Update GRUB ────────────────────────────────────────────────────────
    _final_grub_update(root)

    # ── 4. Clean installer artifacts ──────────────────────────────────────────
    libcalamares.prettyStatus("Cleaning up…")
    try:
        _clean_installer_artifacts(root)
    except Exception as exc:
        warning(f"[finished] Cleanup error (non-fatal): {exc}")

    # ── 5. Sync filesystems ───────────────────────────────────────────────────
    libcalamares.prettyStatus("Syncing filesystems…")
    _sync_filesystems()

    # ── 6. Record reboot preference ──────────────────────────────────────────
    _handle_reboot(cfg)

    # ── 7. Completion log ─────────────────────────────────────────────────────
    edition = _GS.value("synthexEdition") or "SynthOS"
    user    = _GS.value("synthexPrimaryUser") or "synthos"
    debug(
        f"[finished] ✓ {edition} installation complete. "
        f"Primary user: {user!r}. "
        f"Kernel: {platform.release()}."
    )
    libcalamares.prettyStatus("Installation complete! Welcome to SynthOS.")

    _GS.insert("installationFinished", True)
    return None
