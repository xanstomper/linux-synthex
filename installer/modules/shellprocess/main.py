#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Calamares module: shellprocess
# Runs a list of shell commands / scripts inside the installed chroot target.
# Command list is read from the "scripts" key in shellprocess.conf (job config).

import os
import subprocess
import shlex
import time

try:
    import libcalamares
    from libcalamares.utils import debug, warning
    _GS      = libcalamares.globalStorage
    _JOB_CFG = libcalamares.job.configuration
except (ImportError, AttributeError):
    class _FakeGS:
        _d = {"rootMountPoint": "/mnt"}
        @classmethod
        def value(cls, k, d=None): return cls._d.get(k, d)
        @classmethod
        def insert(cls, k, v): cls._d[k] = v

    class _FakeJob:
        configuration = {
            "scripts": [
                {
                    "name":             "Synthex Post-Install",
                    "command":          "/usr/libexec/synthex/post-install.sh",
                    "workingDirectory": "/",
                    "runInTarget":      True,
                    "runAsUser":        "root",
                    "timeout":          120,
                },
            ]
        }

    class _FakeCal:
        globalstorage = _FakeGS()
        job = _FakeJob()
        @staticmethod
        def prettyStatus(m): print(f"[shellprocess] {m}")

    libcalamares = _FakeCal()
    _GS      = libcalamares.globalstorage
    _JOB_CFG = libcalamares.job.configuration

    def debug(m):   print(f"[shellprocess] {m}")
    def warning(m): print(f"[shellprocess] WARN: {m}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_in_chroot(root: str, command: str, working_dir: str, timeout: int) -> tuple[int, str]:
    """Execute *command* inside the chroot at *root*."""
    # Split a single-string command into argv list
    argv = shlex.split(command) if isinstance(command, str) else list(command)

    full_cmd = ["chroot", root] + argv
    env = {
        **os.environ,
        "DEBIAN_FRONTEND": "noninteractive",
        "HOME":            "/root",
        "PATH":            "/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/sbin:/usr/local/bin",
    }

    try:
        r = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir if os.path.isdir(working_dir) else "/",
            env=env,
        )
        out = (r.stdout + r.stderr).strip()
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 1, f"Command timed out after {timeout}s"
    except FileNotFoundError as exc:
        return 1, f"Executable not found: {exc}"
    except Exception as exc:
        return 1, str(exc)


def _run_on_host(command: str, working_dir: str, timeout: int) -> tuple[int, str]:
    """Execute *command* on the live host (runInTarget=false)."""
    argv = shlex.split(command) if isinstance(command, str) else list(command)
    env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    try:
        r = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir if os.path.isdir(working_dir) else "/",
            env=env,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return 1, f"Command timed out after {timeout}s"
    except Exception as exc:
        return 1, str(exc)


def _resolve_command(root: str, command: str, run_in_target: bool) -> str:
    """
    If run_in_target is True and the command binary does not exist in the
    chroot, log a warning.  Returns the command unchanged (chroot handles it).
    """
    if not run_in_target:
        return command
    argv0 = shlex.split(command)[0] if command else ""
    if argv0 and argv0.startswith("/"):
        host_path = os.path.join(root, argv0.lstrip("/"))
        if not os.path.isfile(host_path):
            warning(f"[shellprocess] Binary {argv0!r} not found in chroot — "
                    "command will likely fail")
    return command


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------

def pretty_name() -> str:
    return "Post-Install Shell Scripts"


def run():
    root = _GS.value("rootMountPoint") or ""
    if not root:
        return "rootMountPoint not set in GlobalStorage"
    if not os.path.isdir(root):
        return f"Target root {root!r} does not exist"

    cfg     = _JOB_CFG if isinstance(_JOB_CFG, dict) else {}
    scripts = cfg.get("scripts", cfg.get("commands", []))

    if not scripts:
        debug("[shellprocess] No scripts defined in configuration — nothing to do")
        return None

    errors:  list[str] = []
    total             = len(scripts)

    debug(f"[shellprocess] Running {total} post-install script(s) in {root}")

    for idx, entry in enumerate(scripts, start=1):
        # Normalise: entries may be plain strings or dicts
        if isinstance(entry, str):
            entry = {"command": entry}

        name          = entry.get("name", f"script-{idx}")
        command       = entry.get("command", "").strip()
        working_dir   = entry.get("workingDirectory", "/")
        run_in_target = bool(entry.get("runInTarget", True))
        timeout       = int(entry.get("timeout", 120))
        required      = bool(entry.get("required", True))   # fatal if True
        env_override  = entry.get("environment", {})        # optional extra env

        if not command:
            warning(f"[shellprocess] Script {idx}/{total} ({name!r}): empty command, skipping")
            continue

        libcalamares.prettyStatus(f"Running: {name}…")
        debug(f"[shellprocess] [{idx}/{total}] {name!r}: {command!r}  "
              f"(target={run_in_target}, timeout={timeout}s)")

        _resolve_command(root, command, run_in_target)

        t0 = time.monotonic()
        if run_in_target:
            rc, out = _run_in_chroot(root, command, working_dir, timeout)
        else:
            rc, out = _run_on_host(command, working_dir, timeout)
        elapsed = time.monotonic() - t0

        if out:
            # Truncate very long output in the debug log
            log_out = out if len(out) <= 1000 else out[:1000] + "…(truncated)"
            debug(f"[shellprocess] {name!r} output:\n{log_out}")

        if rc == 0:
            debug(f"[shellprocess] {name!r} OK ({elapsed:.1f}s)")
        else:
            msg = f"Script {name!r} failed (rc={rc}, {elapsed:.1f}s)"
            if required:
                # Abort installation
                return (msg, f"shellprocess: {msg}\n{out[:500]}")
            else:
                warning(f"[shellprocess] {msg} (non-fatal, continuing)")
                errors.append(msg)

    if errors:
        warning(f"[shellprocess] Completed with {len(errors)} non-fatal error(s): {errors}")
    else:
        debug(f"[shellprocess] All {total} script(s) completed successfully.")

    _GS.insert("shellprocessCompleted", True)
    return None
