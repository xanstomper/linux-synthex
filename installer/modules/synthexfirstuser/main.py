#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: synthexfirstuser
# Extends the standard "users" module:
#   • Adds the user to all SynthOS-relevant groups
#   • Sets up XDG dirs, fish shell defaults, Flatpak user repo
#   • Creates ~/.config/synthex/user.json

import os, json, subprocess, grp

try:
    import calamares
    from calamares.utils import debug, warning
except ImportError:
    class _FakeCal:
        class globalstorage:
            _d = {"rootMountPoint": "/mnt", "users": [{"username":"user","autologin":True}]}
            @classmethod
            def value(cls,k,d=None): return cls._d.get(k,d)
            @classmethod
            def insert(cls,k,v): cls._d[k]=v
        @staticmethod
        def prettyStatus(m): print(f"[firstuser] {m}")
    calamares = _FakeCal()
    def debug(m):   print(f"[firstuser] {m}")
    def warning(m): print(f"[firstuser] WARN: {m}")

# Groups to add the primary user to
SYNTHEX_GROUPS = [
    "wheel",       # sudo
    "audio",       # ALSA direct
    "video",       # GPU access
    "input",       # gamepad / keyboard access without root
    "gamemode",    # Feral GameMode
    "render",      # VKMS / GPU render nodes
    "kvm",         # Virtual machines
    "libvirt",     # libvirt VMs
    "docker",      # Docker (if installed)
    "dialout",     # Serial ports / Arduino
    "plugdev",     # USB devices (udev rules)
    "optical",     # Optical drives
    "disk",        # Block devices
    "lp",          # Printers
    "scanner",     # Scanners (SANE)
    "floppy",      # Legacy / removable
    "cdrom",       # CD/DVD
    "tape",        # Tape drives
    "network",     # NetworkManager polkit
]


def chroot_run(root: str, cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    full = ["chroot", root] + cmd
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout + r.stderr
    except Exception as e:
        return 1, str(e)


def pretty_name() -> str:
    return "First User Configuration"


def run() -> None | str:
    root = calamares.globalstorage.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set"

    # Get user info from globalStorage (set by Calamares "users" module)
    users_list = calamares.globalstorage.value("users") or []
    if not users_list:
        # Try single-user keys (older Calamares)
        username = calamares.globalstorage.value("username") or ""
        if not username:
            warning("No users found in globalStorage — skipping firstuser setup")
            return None
        users_list = [{"username": username}]

    primary = users_list[0]
    username  = primary.get("username", "")
    autologin = primary.get("autologin", False)
    fullname  = primary.get("fullName", username)

    if not username:
        return "No username in globalStorage"

    profile     = calamares.globalstorage.value("synthexProfile")    or "classic"
    look_feel   = calamares.globalstorage.value("synthexLookAndFeel") or ""
    gpu_vendor  = calamares.globalstorage.value("synthexGPUVendor")   or "unknown"

    calamares.prettyStatus(f"Configuring user: {username}…")
    debug(f"Primary user: {username!r}  autologin={autologin}  profile={profile}")

    # ── 1. Add to groups ──────────────────────────────────────────────────────
    for grp_name in SYNTHEX_GROUPS:
        # Check if group exists in chroot
        rc, out = chroot_run(root, ["getent", "group", grp_name])
        if rc == 0:
            chroot_run(root, ["usermod", "-aG", grp_name, username])
            debug(f"  + group: {grp_name}")
        else:
            debug(f"  ~ group {grp_name!r} does not exist — skipping")

    # ── 2. Set fish as interactive shell (keep bash as login) ─────────────────
    fish_path = os.path.join(root, "usr/bin/fish")
    if os.path.exists(fish_path):
        # Create ~/.config/fish/config.fish with nice defaults
        fish_cfg_dir = os.path.join(root, "home", username, ".config", "fish")
        os.makedirs(fish_cfg_dir, mode=0o700, exist_ok=True)
        with open(os.path.join(fish_cfg_dir, "config.fish"), "w") as f:
            f.write(
                "# SynthOS fish config\n"
                "set -gx EDITOR nvim\n"
                "set -gx VISUAL nvim\n"
                "set -gx PAGER less\n"
                f"set -gx SYNTHEX_PROFILE {profile}\n"
                "fish_add_path ~/.local/bin\n"
                "fish_add_path /usr/local/bin\n"
                "\n# Greeting\nfunction fish_greeting\n"
                "    echo '🚀 Welcome to SynthOS Linux — ' (hostname)\n"
                "end\n"
            )
        debug("fish config.fish written")

    # ── 3. Flatpak user repo ──────────────────────────────────────────────────
    rc, out = chroot_run(root, [
        "sudo", "-u", username, "flatpak", "remote-add", "--user",
        "--if-not-exists", "flathub",
        "https://dl.flathub.org/repo/flathub.flatpakrepo"
    ], timeout=30)
    if rc == 0:
        debug("Flatpak user Flathub remote added")
    else:
        debug(f"Flatpak user remote (non-fatal): {out[:100]}")

    # ── 4. Write ~/.config/synthex/user.json ─────────────────────────────────
    cfg_dir = os.path.join(root, "home", username, ".config", "synthex")
    os.makedirs(cfg_dir, mode=0o700, exist_ok=True)
    user_cfg = {
        "username":       username,
        "fullName":       fullname,
        "profile":        profile,
        "look_and_feel":  look_feel,
        "gpu_vendor":     gpu_vendor,
        "autologin":      autologin,
        "setup_complete": False,  # set True after OOBE wizard
        "version":        "2026.10",
        "first_login":    True,
    }
    with open(os.path.join(cfg_dir, "user.json"), "w") as f:
        json.dump(user_cfg, f, indent=2)
    debug("~/.config/synthex/user.json written")

    # ── 5. Fix ownership of all user home dirs ────────────────────────────────
    chroot_run(root, ["chown", "-R", f"{username}:{username}",
                       f"/home/{username}"], timeout=30)

    # ── 6. Autologin (SDDM) ──────────────────────────────────────────────────
    if autologin:
        sddm_conf = os.path.join(root, "etc/sddm.conf.d/autologin.conf")
        os.makedirs(os.path.dirname(sddm_conf), exist_ok=True)
        with open(sddm_conf, "w") as f:
            f.write(f"[Autologin]\nUser={username}\nSession=plasmawayland\n")
        debug(f"SDDM autologin configured for: {username}")

    # ── 7. Emit to globalStorage ──────────────────────────────────────────────
    calamares.globalstorage.insert("synthexPrimaryUser", username)
    calamares.globalstorage.insert("synthexUserConfigured", True)

    debug(f"firstuser complete: {username}")
    return None
