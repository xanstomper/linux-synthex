#!/usr/bin/env python3
"""
Synthex Tray — system tray integration for Synthex services
Shows update status, gaming mode, GPU mode in the system tray.

Usage:
    synthex-tray                    — Run tray daemon
    synthex-tray status            — Show current status
"""
import os, sys, subprocess, json, signal, time, logging
log = logging.getLogger("synthex-tray")

STATE_FILE = "/var/lib/synthex/tray-state.json"

def get_updates_count():
    cache = "/var/cache/synthex/updates.json"
    if os.path.exists(cache):
        try:
            with open(cache) as f:
                data = json.load(f)
            return data.get("total", 0)
        except Exception as e: log.debug("tray: %s", e)
    return 0

def get_gaming_mode():
    return os.path.exists("/var/lib/synthex/gaming-mode")

def get_gpu_mode():
    state_file = "/var/lib/synthex/gpu-mode"
    if os.path.exists(state_file):
        return open(state_file).read().strip()
    return "auto"

def get_tray_status():
    """Collect status for tray display"""
    updates = get_updates_count()
    gaming = get_gaming_mode()
    gpu = get_gpu_mode()
    
    status = {}
    if updates > 0:
        status["updates"] = {"count": updates, "icon": "system-software-update"}
    if gaming:
        status["gaming"] = {"active": True, "icon": "applications-games"}
    status["gpu"] = {"mode": gpu, "icon": "video-card"}
    
    return status

def daemon_loop():
    """Main tray daemon loop"""
    print("[tray] Synthex Tray starting...")
    while True:
        try:
            status = get_tray_status()
            # In a real implementation, this would use Qt/KDE status notifier
            # For now, output JSON for integration with KDE's system tray
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump(status, f)
            time.sleep(5)   # Brain OS: poll every 5 s for snappy tray status
        except KeyboardInterrupt:
            break
        except Exception as e: log.debug("tray: %s", e)

def show_status():
    status = get_tray_status()
    updates = status.get("updates", {}).get("count", 0)
    gaming = status.get("gaming", {}).get("active", False)
    gpu = status.get("gpu", {}).get("mode", "auto")
    
    print("Synthex System Status:")
    print(f"  Updates: {'📦 ' + str(updates) if updates > 0 else '✅ Up to date'}")
    print(f"  Gaming Mode: {'🟢 Active' if gaming else '⚪ Inactive'}")
    print(f"  GPU Mode: {gpu}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        daemon_loop()
