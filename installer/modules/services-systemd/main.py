#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: services-systemd
# Enables/disables systemd services in the installed chroot based on the
# services list in services-systemd.conf and the active SynthOS profile.

import os
import subprocess

try:
    import libcalamares
    from libcalamares.utils import debug, warning
    _GS      = libcalamares.globalStorage
    _JOB_CFG = libcalamares.job.configuration
except (ImportError, AttributeError):
    class _FakeGS:
        _d = {
            "rootMountPoint": "/mnt",
            "synthexProfile": "classic",
            "users": [{"username": "synthos"}],
        }
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "services": [
                {"name": "NetworkManager", "action": "enable"},
                {"name": "sddm",           "action": "enable"},
                {"name": "firewalld",      "action": "enable"},
            ],
            "defaultTarget": "graphical.target",
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[services-systemd] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[services-systemd] {m}")
    def warning(m): print(f"[services-systemd] WARN: {m}")


# ---------------------------------------------------------------------------
# Profile-specific service overrides
# (merged on top of whatever the .conf file declares)
# ---------------------------------------------------------------------------

# Extra services to enable per profile (if the unit exists in the chroot)
_PROFILE_ENABLE: dict[str, list[str]] = {
    "gaming":     ["synthex-gaming-mode.service", "gamemode.service",
                   "gamescope-session.service"],
    "pro-gaming": ["synthex-gaming-mode.service", "gamemode.service",
                   "gamescope-session.service", "mangohud.service"],
    "studio":     ["jack.service", "jackd.service", "pipewire-jack.service",
                   "ardour.service"],
    "pro":        ["jack.service", "pipewire-jack.service"],
    "focus":      ["synthex-focus-daemon.service"],
    "lite":       [],
    "classic":    [],
}

# User-level services to linger / enable for the first user
_USER_SERVICES: list[str] = [
    "pipewire.service",
    "pipewire-pulse.service",
    "wireplumber.service",
    "synthex-tray.service",
    "synthex-agent.service",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chroot(root: str, cmd: list, timeout: int = 60):
    try:
        r = subprocess.run(
            ["chroot", root] + cmd,
            capture_output=True, text=True, timeout=timeout,
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            debug(f"[services-systemd] rc={r.returncode} {' '.join(cmd)}: {out[:300]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        warning(f"[services-systemd] timed out: {' '.join(cmd)}")
        return 1, "timeout"
    except Exception as exc:
        warning(f"[services-systemd] error: {exc}")
        return 1, str(exc)


def _unit_exists(root: str, unit: str) -> bool:
    """Return True if *unit* is present anywhere systemd would find it."""
    search_dirs = [
        "usr/lib/systemd/system",
        "lib/systemd/system",
        "etc/systemd/system",
    ]
    return any(
        os.path.exists(os.path.join(root, d, unit))
        for d in search_dirs
    )


def _bulk_action(root: str, action: str, units: list[str]) -> list[str]:
    """Run `systemctl <action> <units...>` in the chroot; return error messages."""
    if not units:
        return []
    rc, out = _chroot(root, ["systemctl", action] + units, timeout=90)
    if rc != 0:
        return [f"systemctl {action} failed (rc={rc}): {out[:200]}"]
    debug(f"[services-systemd] systemctl {action}: {len(units)} unit(s)")
    return []


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "System Services (systemd)"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    systemctl_bin = os.path.join(root, "usr/bin/systemctl")
    if not os.path.isfile(systemctl_bin):
        warning("[services-systemd] systemctl not found in chroot — skipping")
        return None

    cfg     = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}
    profile = (_GS.value("synthexProfile") or "classic").lower()
    errors  = []

    # ── 1. Parse the conf services list ──────────────────────────────────────
    to_enable:  list[str] = []
    to_disable: list[str] = []
    to_mask:    list[str] = []

    for entry in cfg.get("services", []):
        name   = entry.get("name", "").strip()
        action = entry.get("action", "enable").lower()
        if not name:
            continue

        if action == "enable":
            to_enable.append(name)
        elif action == "disable":
            to_disable.append(name)
        elif action == "mask":
            to_mask.append(name)
        else:
            warning(f"[services-systemd] Unknown action {action!r} for {name!r}")

    # ── 2. Profile-specific additions ────────────────────────────────────────
    for svc in _PROFILE_ENABLE.get(profile, []):
        if svc not in to_enable:
            to_enable.append(svc)
    debug(f"[services-systemd] Profile={profile!r}: "
          f"{len(to_enable)} enable, {len(to_disable)} disable, {len(to_mask)} mask")

    # ── 3. Filter to units that actually exist in the chroot ─────────────────
    libcalamares.prettyStatus("Enabling system services…")
    available_enable = [u for u in to_enable  if _unit_exists(root, u)]
    skipped          = [u for u in to_enable  if not _unit_exists(root, u)]
    if skipped:
        debug(f"[services-systemd] Not installed (skipped): {skipped}")

    errors += _bulk_action(root, "enable",  available_enable)

    libcalamares.prettyStatus("Disabling unnecessary services…")
    available_disable = [u for u in to_disable if _unit_exists(root, u)]
    errors += _bulk_action(root, "disable", available_disable)

    available_mask = [u for u in to_mask if _unit_exists(root, u)]
    errors += _bulk_action(root, "mask", available_mask)

    # ── 4. Set default systemd target ────────────────────────────────────────
    default_target = cfg.get("defaultTarget", "graphical.target")
    libcalamares.prettyStatus(f"Setting default target: {default_target}…")
    rc, out = _chroot(root, ["systemctl", "set-default", default_target], timeout=30)
    if rc != 0:
        errors.append(f"set-default {default_target} failed: {out[:200]}")
    else:
        debug(f"[services-systemd] Default target → {default_target}")

    # ── 5. User-level service linger & wants symlinks ─────────────────────────
    users = _GS.value("users") or []
    if not users:
        # Fall back to the GlobalStorage key used by the users module
        first_user = _GS.value("loginName") or ""
    else:
        first_user = users[0].get("username", "") if isinstance(users[0], dict) else ""

    if first_user:
        libcalamares.prettyStatus(f"Enabling user services for {first_user}…")
        _chroot(root, ["loginctl", "enable-linger", first_user], timeout=15)

        wants_dir = os.path.join(
            root, f"home/{first_user}/.config/systemd/user/default.target.wants"
        )
        os.makedirs(wants_dir, exist_ok=True)

        for svc in _USER_SERVICES:
            src = os.path.join(root, f"usr/lib/systemd/user/{svc}")
            dst = os.path.join(wants_dir, svc)
            if os.path.isfile(src) and not os.path.exists(dst):
                os.symlink(f"/usr/lib/systemd/user/{svc}", dst)
                debug(f"[services-systemd] User service enabled: {svc}")

    # ── 6. Vendor preset pass (honours upstream defaults) ────────────────────
    _chroot(root, ["systemctl", "preset-all", "--preset-mode=enable-only"], timeout=120)
    # Re-assert our enables in case preset overrode them
    errors += _bulk_action(root, "enable", available_enable)

    if errors:
        warning(f"[services-systemd] Completed with warnings: {errors}")
    else:
        debug("[services-systemd] Service configuration complete.")

    _GS.insert("servicesConfigured", True)
    return None
