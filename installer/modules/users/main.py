#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: users
# Creates the primary user account in the installed chroot.
# Reads from GlobalStorage: loginName, userPassword, fullName, autoLoginUser,
# rootPassword, and users[] list populated by the Calamares users view.

import crypt
import json
import os
import re
import subprocess

try:
    import libcalamares
    from libcalamares.utils import debug, warning
    _GS      = libcalamares.globalStorage
    _JOB_CFG = libcalamares.job.configuration
except (ImportError, AttributeError):
    class _FakeGS:
        _d = {
            "rootMountPoint":  "/mnt",
            "loginName":       "synthos",
            "userPassword":    "changeme",
            "fullName":        "SynthOS User",
            "autoLoginUser":   "synthos",
            "rootPassword":    "",
            "synthexProfile":  "classic",
            "synthexLookAndFeel": "org.synthos.desktop.classic",
            "users": [],
        }
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "defaultGroups": [
                "users", "wheel", "audio", "video", "cdrom",
                "docker", "libvirt", "kvm", "input", "storage",
                "adm", "networkmanager", "lp",
            ],
            "doAutologin":      True,
            "setRootPassword":  True,
            "userShell":        "/bin/bash",
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[users] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[users] {m}")
    def warning(m): print(f"[users] WARN: {m}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chroot(root: str, cmd: list, timeout: int = 60, input: str | None = None):
    try:
        r = subprocess.run(
            ["chroot", root] + cmd,
            capture_output=True, text=True, timeout=timeout,
            input=input,
            env={
                **os.environ,
                "DEBIAN_FRONTEND": "noninteractive",
                "HOME":            "/root",
                "PATH":            "/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin",
            },
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            debug(f"[users] rc={r.returncode} {' '.join(cmd)}: {out[:300]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        warning(f"[users] timed out: {' '.join(cmd)}")
        return 1, "timeout"
    except Exception as exc:
        warning(f"[users] error: {exc}")
        return 1, str(exc)


def _write(path: str, content: str, mode: int = 0o644) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, mode)


def _hash_password(plaintext: str) -> str:
    """SHA-512 shadow hash compatible with /etc/shadow."""
    return crypt.crypt(plaintext, crypt.mksalt(crypt.METHOD_SHA512))


def _sanitise_username(name: str) -> str:
    """Return a POSIX-safe username (lowercase, starts with letter/underscore)."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9_\-]", "", name)
    if not name or name[0].isdigit():
        name = "user" + name
    return name[:32] or "synthos"


def _group_exists(root: str, group: str) -> bool:
    group_file = os.path.join(root, "etc/group")
    if not os.path.isfile(group_file):
        return False
    with open(group_file) as fh:
        return any(line.split(":")[0] == group for line in fh)


# ---------------------------------------------------------------------------
# Sub-steps
# ---------------------------------------------------------------------------

def _create_user(root: str, username: str, fullname: str, shell: str,
                 password_hash: str, groups: list[str]) -> list[str]:
    errors = []

    # Build group list (only include groups that exist in the chroot)
    valid_groups = [g for g in groups if _group_exists(root, g)]
    skipped_groups = [g for g in groups if g not in valid_groups]
    if skipped_groups:
        debug(f"[users] Skipping non-existent groups: {skipped_groups}")

    # Check if user already exists
    passwd_file = os.path.join(root, "etc/passwd")
    user_exists = False
    if os.path.isfile(passwd_file):
        with open(passwd_file) as fh:
            user_exists = any(line.split(":")[0] == username for line in fh)

    if not user_exists:
        # useradd: create home dir, set shell, comment (GECOS), primary group=users
        cmd = [
            "useradd",
            "--create-home",
            "--shell", shell,
            "--comment", fullname,
            "--user-group",
        ]
        if valid_groups:
            cmd += ["--groups", ",".join(valid_groups)]
        cmd.append(username)
        rc, out = _chroot(root, cmd, timeout=30)
        if rc != 0:
            errors.append(f"useradd failed (rc={rc}): {out[:200]}")
            return errors
        debug(f"[users] Created user {username!r} (shell={shell!r})")
    else:
        warning(f"[users] User {username!r} already exists — skipping useradd")
        # Still ensure group membership
        if valid_groups:
            _chroot(root, ["usermod", "-aG", ",".join(valid_groups), username], timeout=30)

    # Set password via chpasswd (accepts "user:hash" for pre-hashed passwords)
    if password_hash:
        rc, out = _chroot(root, ["chpasswd", "--encrypted"],
                          input=f"{username}:{password_hash}\n", timeout=30)
        if rc != 0:
            # Fallback: pipe plaintext (if hash failed due to chpasswd version)
            errors.append(f"chpasswd (encrypted) failed (rc={rc}) — check chpasswd version")
        else:
            debug(f"[users] Password set for {username!r}")

    return errors


def _set_root_password(root: str, root_hash: str) -> list[str]:
    errors = []
    if not root_hash:
        # Lock root account (best practice: use sudo instead)
        _chroot(root, ["passwd", "--lock", "root"], timeout=20)
        debug("[users] root account locked (sudo-only access)")
        return errors

    rc, out = _chroot(root, ["chpasswd", "--encrypted"],
                      input=f"root:{root_hash}\n", timeout=30)
    if rc != 0:
        errors.append(f"root chpasswd failed (rc={rc}): {out[:200]}")
    else:
        debug("[users] root password set")
    return errors


def _configure_sudo(root: str, username: str) -> None:
    """Give the primary user passwordless sudo via /etc/sudoers.d/."""
    sudoers_d = os.path.join(root, "etc/sudoers.d")
    os.makedirs(sudoers_d, exist_ok=True)
    sudoers_file = os.path.join(sudoers_d, f"10-{username}")
    _write(sudoers_file,
           f"# SynthOS: {username} is a sudoer\n"
           f"{username} ALL=(ALL:ALL) ALL\n",
           mode=0o440)
    debug(f"[users] /etc/sudoers.d/10-{username} written")

    # Also ensure the wheel group has sudo access (RPM-based distros)
    wheel_sudoers = os.path.join(root, "etc/sudoers.d/wheel")
    if not os.path.exists(wheel_sudoers):
        _write(wheel_sudoers,
               "# Allow wheel group members to use sudo\n"
               "%wheel ALL=(ALL:ALL) ALL\n",
               mode=0o440)


def _configure_autologin(root: str, username: str) -> None:
    """Configure SDDM autologin for the given user."""
    sddm_conf_d = os.path.join(root, "etc/sddm.conf.d")
    os.makedirs(sddm_conf_d, exist_ok=True)
    _write(
        os.path.join(sddm_conf_d, "autologin.conf"),
        "[Autologin]\n"
        f"User={username}\n"
        "Session=plasma\n"
        "Relogin=false\n",
    )
    debug(f"[users] SDDM autologin configured for {username!r}")


def _write_user_profile(root: str, username: str, fullname: str,
                        profile: str, look_and_feel: str) -> None:
    """Write ~/.config/synthex/user.json for OOBE / first-boot setup."""
    user_cfg_dir = os.path.join(root, f"home/{username}/.config/synthex")
    os.makedirs(user_cfg_dir, exist_ok=True)

    user_json = {
        "username":    username,
        "fullName":    fullname,
        "profile":     profile,
        "lookAndFeel": look_and_feel,
        "firstLogin":  True,
        "version":     "2026.10",
    }
    cfg_path = os.path.join(user_cfg_dir, "user.json")
    with open(cfg_path, "w", encoding="utf-8") as fh:
        json.dump(user_json, fh, indent=2)
    os.chmod(cfg_path, 0o600)

    # Fix ownership – chown -R username:username home dir
    _chroot(root, ["chown", "-R", f"{username}:{username}", f"/home/{username}"],
            timeout=30)
    debug(f"[users] User profile written: {cfg_path}")


def _setup_fish_config(root: str, username: str) -> None:
    """Write a minimal fish shell greeting config (if fish is installed)."""
    fish_bin = os.path.join(root, "bin/fish")
    if not os.path.isfile(fish_bin):
        return
    fish_cfg_dir = os.path.join(root, f"home/{username}/.config/fish")
    os.makedirs(fish_cfg_dir, exist_ok=True)
    _write(
        os.path.join(fish_cfg_dir, "config.fish"),
        "# SynthOS fish config\n"
        "set -gx EDITOR nvim\n"
        "set -gx VISUAL nvim\n"
        f"set -gx SYNTHEX_PROFILE {{}}\n"
        "fish_add_path /usr/local/bin ~/.local/bin\n\n"
        'function fish_greeting\n'
        f'    echo "Welcome to SynthOS, {username}!"\n'
        'end\n',
    )
    debug(f"[users] fish config written for {username!r}")


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "Create User Account"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    cfg = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}

    # ── Gather user info from GlobalStorage ──────────────────────────────────
    # Calamares users module populates a "users" list; fall back to flat keys
    users_list = _GS.value("users") or []
    if users_list and isinstance(users_list[0], dict):
        primary = users_list[0]
        username = _sanitise_username(primary.get("username", "") or
                                       primary.get("loginName", "synthos"))
        fullname  = primary.get("fullName", "") or primary.get("fullname", username)
        password  = primary.get("userPassword", "") or primary.get("password", "")
        autologin = primary.get("autologin",
                                bool(cfg.get("doAutologin", True)))
    else:
        username  = _sanitise_username(_GS.value("loginName") or "synthos")
        fullname  = _GS.value("fullName") or username
        password  = _GS.value("userPassword") or ""
        autologin = bool(_GS.value("autoLoginUser") or cfg.get("doAutologin", True))

    shell          = cfg.get("userShell", "/bin/bash")
    groups         = cfg.get("defaultGroups", [
        "users", "wheel", "audio", "video", "cdrom",
        "input", "storage", "adm", "networkmanager", "lp",
    ])
    root_password  = _GS.value("rootPassword") or ""
    set_root_pw    = bool(cfg.get("setRootPassword", True))
    profile        = _GS.value("synthexProfile")        or "classic"
    look_and_feel  = _GS.value("synthexLookAndFeel")    or ""

    if not username:
        return "No username found in GlobalStorage"

    debug(f"[users] Creating user {username!r} ({fullname!r}) "
          f"autologin={autologin} shell={shell!r}")

    errors = []

    # ── Hash passwords ────────────────────────────────────────────────────────
    libcalamares.prettyStatus(f"Creating user account: {username}…")
    pw_hash   = _hash_password(password)   if password   else ""
    root_hash = _hash_password(root_password) if (root_password and set_root_pw) else ""

    # ── Create user ───────────────────────────────────────────────────────────
    errors += _create_user(root, username, fullname, shell, pw_hash, groups)
    if errors:
        # Fatal: cannot proceed without a user
        return ("User creation failed", f"users: {errors[0]}")

    # ── Root password ─────────────────────────────────────────────────────────
    if set_root_pw:
        libcalamares.prettyStatus("Setting root password…")
        errors += _set_root_password(root, root_hash)

    # ── sudo ──────────────────────────────────────────────────────────────────
    libcalamares.prettyStatus("Configuring sudo…")
    _configure_sudo(root, username)

    # ── Autologin ─────────────────────────────────────────────────────────────
    if autologin:
        libcalamares.prettyStatus("Configuring autologin…")
        _configure_autologin(root, username)

    # ── User profile JSON & optional shell config ─────────────────────────────
    libcalamares.prettyStatus("Writing user profile…")
    _write_user_profile(root, username, fullname, profile, look_and_feel)
    _setup_fish_config(root, username)

    if errors:
        warning(f"[users] Completed with warnings: {errors}")
    else:
        debug("[users] User configuration complete.")

    _GS.insert("synthexPrimaryUser", username)
    _GS.insert("synthexUserConfigured", True)
    return None
