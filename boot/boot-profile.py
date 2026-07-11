#!/usr/bin/env python3
"""
SynthOS boot-time profiler.

Records each systemd boot time to /var/lib/synthex/boot-times.json for
trending, anomaly detection, and per-kernel comparisons.  The file is a
JSON array (newest last, capped at 100 entries).
"""
import json
import os
import platform
import socket
import subprocess
import datetime

STORE = "/var/lib/synthex/boot-times.json"
os.makedirs("/var/lib/synthex", exist_ok=True)

# ── Load history ─────────────────────────────────────────────────────────────
history: list = []
if os.path.exists(STORE):
    try:
        with open(STORE) as fh:
            raw = json.load(fh)
            history = raw if isinstance(raw, list) else []
    except (json.JSONDecodeError, OSError, ValueError):
        history = []   # first boot or corrupted file — start fresh

# ── Parse systemd-analyze output ─────────────────────────────────────────────
def _parse_boot_time() -> dict | None:
    """
    Return a dict with kernel_s, initrd_s, userspace_s, total_s (all floats
    in seconds) or None when systemd-analyze is unavailable / fails.

    systemd-analyze stdout looks like:
        Startup finished in 1.234s (kernel) + 2.345s (initrd) + 5.678s (userspace) = 9.257s
    or (EFI):
        Startup finished in 0.456s (firmware) + 1.234s (loader) + 0.876s (kernel) + 5.678s (userspace) = 8.244s
    """
    try:
        result = subprocess.run(
            ["systemd-analyze"],
            capture_output=True, text=True, timeout=10
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    line = result.stdout.strip()
    if not line or "=" not in line:
        return None

    import re
    # Total (right-hand side of the = sign)
    total_match = re.search(r"=\s*([\d.]+)(?:min\s*)?([\d.]+)?s", line)
    total_s: float | None = None
    if total_match:
        if total_match.group(2):                           # Xmin Y.YYYs
            total_s = float(total_match.group(1)) * 60 + float(total_match.group(2))
        else:
            # could be "= X.XXXmin" (unusual) or "= X.XXXs"
            raw_tail = line.rsplit("=", 1)[-1].strip()
            if "min" in raw_tail:
                mins = float(raw_tail.replace("min", "").strip())
                total_s = mins * 60
            else:
                try:
                    total_s = float(raw_tail.replace("s", "").strip())
                except ValueError:
                    pass
    elif "=" in line:
        raw_tail = line.rsplit("=", 1)[-1].strip()
        try:
            total_s = float(raw_tail.replace("s", "").strip())
        except ValueError:
            pass

    # Individual phases
    def _phase(name: str) -> float | None:
        m = re.search(rf"([\d.]+)s\s*\({name}\)", line)
        return float(m.group(1)) if m else None

    return {
        "firmware_s":  _phase("firmware"),
        "loader_s":    _phase("loader"),
        "kernel_s":    _phase("kernel"),
        "initrd_s":    _phase("initrd"),
        "userspace_s": _phase("userspace"),
        "total_s":     total_s,
    }

timing = _parse_boot_time()

# ── Build entry ──────────────────────────────────────────────────────────────
entry: dict = {
    "date":    datetime.datetime.now().isoformat(timespec="seconds"),
    "kernel":  platform.release(),
    "host":    socket.gethostname(),
}
if timing:
    entry.update({k: (round(v, 3) if v is not None else None) for k, v in timing.items()})
    if timing.get("total_s") is not None:
        entry["boot_time_ms"] = round(timing["total_s"] * 1000, 1)
else:
    entry["boot_time_ms"] = None

# ── Trend / anomaly note ─────────────────────────────────────────────────────
recent_totals = [
    e["boot_time_ms"]
    for e in history[-10:]
    if isinstance(e.get("boot_time_ms"), (int, float))
]
if recent_totals and entry.get("boot_time_ms") is not None:
    avg = sum(recent_totals) / len(recent_totals)
    entry["avg_10_boot_ms"] = round(avg, 1)
    delta_pct = (entry["boot_time_ms"] - avg) / avg * 100
    entry["delta_pct"] = round(delta_pct, 1)
    if delta_pct > 20:
        entry["trend_flag"] = "SLOW"
    elif delta_pct < -15:
        entry["trend_flag"] = "FAST"
    else:
        entry["trend_flag"] = "NORMAL"

# ── Persist ──────────────────────────────────────────────────────────────────
history.append(entry)
history = history[-100:]   # keep last 100 entries

with open(STORE, "w") as fh:
    json.dump(history, fh, indent=2)
