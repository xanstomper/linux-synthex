#!/usr/bin/env python3
"""Record systemd boot times to /var/lib/synthex/boot-times.json for trending."""
import json, os, subprocess, datetime

P = "/var/lib/synthex/boot-times.json"
os.makedirs("/var/lib/synthex", exist_ok=True)

history = []
if os.path.exists(P):
    try:
        with open(P) as f:
            raw = json.load(f)
            history = raw if isinstance(raw, list) else []
    except (json.JSONDecodeError, OSError):
        pass

result = subprocess.run(["systemd-analyze"], capture_output=True, text=True)
output = result.stdout
boot_time = None
if "=" in output:
    tail = output.rsplit("=", 1)[-1].strip()
    if tail:
        try:
            boot_time = float(tail.replace("s", ""))
        except ValueError:
            pass

entry = {
    "date": datetime.datetime.now().isoformat(),
    "kernel": os.uname().release,
    "boot_time_ms": round(boot_time * 1000, 1) if boot_time else None,
}
history.append(entry)
history = history[-100:]  # Keep last 100 entries

with open(P, "w") as f:
    json.dump(history, f, indent=2)
