#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: locale
# Sets system locale, timezone, and keyboard layout in the installed chroot.
# Reads from GlobalStorage: locale, timezone, keyboardLayout, keyboardVariant

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
            "locale":          "en_US.UTF-8",
            "timezone":        "America/New_York",
            "keyboardLayout":  "us",
            "keyboardVariant": "",
        }
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "localeGenPath":  "/usr/bin/locale-gen",
            "generateLocale": True,
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[locale] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[locale] {m}")
    def warning(m): print(f"[locale] WARN: {m}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _chroot(root: str, cmd: list, timeout: int = 60):
    """Run *cmd* inside the target chroot; returns (returncode, combined_output)."""
    try:
        r = subprocess.run(
            ["chroot", root] + cmd,
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
        )
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            debug(f"[locale] rc={r.returncode} {' '.join(cmd)}: {out[:300]}")
        return r.returncode, out
    except subprocess.TimeoutExpired:
        warning(f"[locale] timed out: {' '.join(cmd)}")
        return 1, "timeout"
    except Exception as exc:
        warning(f"[locale] error: {exc}")
        return 1, str(exc)


def _write(path: str, content: str, mode: int = 0o644) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    os.chmod(path, mode)


# ---------------------------------------------------------------------------
# Step 1 – Locale
# ---------------------------------------------------------------------------

def _configure_locale(root: str, locale: str, cfg: dict) -> list:
    errors = []
    lang = locale or "en_US.UTF-8"

    # /etc/locale.conf
    _write(
        os.path.join(root, "etc/locale.conf"),
        f"LANG={lang}\n"
        f"LC_ADDRESS={lang}\n"
        f"LC_IDENTIFICATION={lang}\n"
        f"LC_MEASUREMENT={lang}\n"
        f"LC_MONETARY={lang}\n"
        f"LC_NAME={lang}\n"
        f"LC_NUMERIC={lang}\n"
        f"LC_PAPER={lang}\n"
        f"LC_TELEPHONE={lang}\n"
        f"LC_TIME={lang}\n",
    )
    debug(f"[locale] /etc/locale.conf → LANG={lang}")

    # Uncomment the locale in /etc/locale.gen
    locale_gen_path = os.path.join(root, "etc/locale.gen")
    if os.path.isfile(locale_gen_path):
        bare = lang.split(".")[0]
        enc  = lang.split(".")[-1] if "." in lang else "UTF-8"
        pat  = re.compile(rf"^#\s*({re.escape(bare)}[\w@.]*\s+{re.escape(enc)})", re.I)
        new_lines = []
        with open(locale_gen_path, encoding="utf-8") as fh:
            for line in fh:
                m = pat.match(line)
                new_lines.append((m.group(1) + "\n") if m else line)
        with open(locale_gen_path, "w", encoding="utf-8") as fh:
            fh.writelines(new_lines)
        debug(f"[locale] /etc/locale.gen: uncommented {lang}")

    # Run locale-gen
    if cfg.get("generateLocale", True):
        gen_bin = cfg.get("localeGenPath", "/usr/bin/locale-gen")
        rc, out = _chroot(root, [gen_bin], timeout=120)
        if rc != 0:
            rc, out = _chroot(root, ["locale-gen"], timeout=120)
        if rc != 0:
            errors.append(f"locale-gen failed (rc={rc})")
        else:
            debug("[locale] locale-gen OK")

    return errors


# ---------------------------------------------------------------------------
# Step 2 – Timezone
# ---------------------------------------------------------------------------

def _configure_timezone(root: str, timezone: str) -> list:
    errors = []
    if not timezone:
        timezone = "UTC"

    zoneinfo = os.path.join(root, "usr/share/zoneinfo", timezone)
    if not os.path.isfile(zoneinfo):
        warning(f"[locale] zoneinfo not found for {timezone!r}; falling back to UTC")
        timezone = "UTC"
        zoneinfo = os.path.join(root, "usr/share/zoneinfo/UTC")

    localtime = os.path.join(root, "etc/localtime")
    if os.path.exists(localtime) or os.path.islink(localtime):
        os.remove(localtime)
    os.symlink(f"/usr/share/zoneinfo/{timezone}", localtime)
    debug(f"[locale] /etc/localtime → {timezone}")

    _write(os.path.join(root, "etc/timezone"), timezone + "\n")

    # timedatectl is best-effort inside chroot (no D-Bus)
    _chroot(root, ["timedatectl", "--no-ask-password", "set-timezone", timezone], timeout=15)

    return errors


# ---------------------------------------------------------------------------
# Step 3 – Keyboard
# ---------------------------------------------------------------------------

def _configure_keyboard(root: str, layout: str, variant: str) -> list:
    errors = []
    layout  = layout  or "us"
    variant = variant or ""

    # /etc/vconsole.conf  (virtual console / TTY)
    vconsole = f"KEYMAP={layout}\nFONT=eurlatgr\n"
    if variant:
        vconsole += f"XKBVARIANT={variant}\n"
    _write(os.path.join(root, "etc/vconsole.conf"), vconsole)
    debug(f"[locale] vconsole.conf → KEYMAP={layout}")

    # /etc/X11/xorg.conf.d/00-keyboard.conf
    variant_line = f'\n        Option "XkbVariant" "{variant}"' if variant else ""
    _write(
        os.path.join(root, "etc/X11/xorg.conf.d/00-keyboard.conf"),
        'Section "InputClass"\n'
        '        Identifier "system-keyboard"\n'
        '        MatchIsKeyboard "on"\n'
        f'        Option "XkbLayout" "{layout}"{variant_line}\n'
        '        Option "XkbOptions" "terminate:ctrl_alt_bksp"\n'
        'EndSection\n',
    )
    debug(f"[locale] X11 keyboard: layout={layout!r} variant={variant!r}")

    # /etc/default/keyboard  (initramfs / debian-style tools)
    _write(
        os.path.join(root, "etc/default/keyboard"),
        "# Generated by SynthOS Calamares locale module\n"
        f'XKBLAYOUT="{layout}"\n'
        f'XKBVARIANT="{variant}"\n'
        'XKBMODEL="pc105"\n'
        'XKBOPTIONS="terminate:ctrl_alt_bksp"\n'
        'BACKSPACE="guess"\n',
    )

    # localectl – best-effort (no D-Bus in chroot)
    _chroot(root, ["localectl", "--no-ask-password", "set-keymap", layout], timeout=15)

    return errors


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "System Locale & Keyboard"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    cfg = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}

    # Locale – may be a plain string or a dict with a "lang" key
    locale_val = _GS.value("locale") or ""
    if isinstance(locale_val, dict):
        locale = locale_val.get("lang", "en_US.UTF-8")
    else:
        locale = locale_val or "en_US.UTF-8"

    timezone = _GS.value("timezone") or "UTC"

    # keyboardLayout may be a plain string or a dict {layout, variant, model}
    kb = _GS.value("keyboardLayout")
    if isinstance(kb, dict):
        layout  = kb.get("layout", "us")
        variant = kb.get("variant", "")
    else:
        layout  = kb or "us"
        variant = _GS.value("keyboardVariant") or ""

    debug(f"[locale] locale={locale!r}  tz={timezone!r}  "
          f"layout={layout!r}  variant={variant!r}")

    errors = []

    libcalamares.prettyStatus("Configuring system locale…")
    errors += _configure_locale(root, locale, cfg)

    libcalamares.prettyStatus("Setting timezone…")
    errors += _configure_timezone(root, timezone)

    libcalamares.prettyStatus("Configuring keyboard layout…")
    errors += _configure_keyboard(root, layout, variant)

    if errors:
        warning(f"[locale] Finished with warnings: {errors}")
    else:
        debug("[locale] Locale configuration complete.")

    _GS.insert("localeConfigured", True)
    return None
