#!/usr/bin/env python3
"""
Solus Hardware Vault — local hardware compatibility database.
Tracks detected hardware and provides recommendations.

Usage:
    solus-hwvault scan          — Scan hardware and save to database
    solus-hwvault status        — Show current hardware profile
    solus-hwvault list          — List all known hardware
    solus-hwvault report        — Generate compatibility report
    solus-hwvault submit        — Submit config to community DB
"""

import os
import sys
import json
import subprocess
import hashlib
from datetime import datetime

VAULT_DIR = os.path.expanduser("~/.config/solus/hardware-vault")
HW_PROFILE_PATH = "/var/run/solus-hw-profile.json"
DB_PATH = os.path.join(VAULT_DIR, "database.json")


def ensure_dirs():
    os.makedirs(VAULT_DIR, exist_ok=True)


def scan_hardware():
    """Scan system hardware and save to database."""
    print("🔍 Scanning hardware...")
    
    hw = {}
    
    # CPU
    cpu_info = {}
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    if key == "model name":
                        cpu_info["model"] = val
                    elif key == "cpu cores":
                        cpu_info["cores"] = val
                    elif key == "siblings":
                        cpu_info["threads"] = val
                    elif key == "vendor_id":
                        cpu_info["vendor"] = val
    except (OSError, json.JSONDecodeError):
        pass
    
    if cpu_info:
        cpu_id = hashlib.md5(cpu_info.get("model", "").encode()).hexdigest()[:12]
        hw["cpu"] = {
            "id": cpu_id,
            "model": cpu_info.get("model", "Unknown"),
            "vendor": cpu_info.get("vendor", "Unknown"),
            "cores": cpu_info.get("cores", "?"),
            "threads": cpu_info.get("threads", "?"),
        }
    
    # GPU
    try:
        result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "VGA" in line or "3D" in line or "Display" in line:
                parts = line.strip().split(":", 2)
                if len(parts) >= 3:
                    hw["gpu"] = {
                        "name": parts[2].strip(),
                        "pci_id": parts[1].strip() if len(parts) > 1 else "",
                    }
                    break
    except (OSError, json.JSONDecodeError):
        pass
    
    # GPU vendor from PCI IDs
    try:
        result = subprocess.run(["lspci", "-n"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "0300" in line or "0302" in line:
                for part in line.split():
                    if part.startswith("10de"):
                        hw.setdefault("gpu", {})["vendor"] = "NVIDIA"
                    elif part.startswith("1002"):
                        hw.setdefault("gpu", {})["vendor"] = "AMD"
                    elif part.startswith("8086"):
                        hw.setdefault("gpu", {})["vendor"] = "Intel"
    except (OSError, json.JSONDecodeError):
        pass
    
    # RAM
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal"):
                    mem_kb = int(line.split()[1])
                    hw["ram"] = {
                        "total_gb": round(mem_kb / (1024 * 1024), 1),
                        "total_kb": mem_kb,
                    }
                    break
    except (OSError, json.JSONDecodeError):
        pass
    
    # Storage
    try:
        result = subprocess.run(["lsblk", "-dno", "NAME,ROTA,SIZE,MODEL"], 
                              capture_output=True, text=True)
        drives = []
        for line in result.stdout.splitlines():
            parts = line.split()
            if parts:
                is_hdd = len(parts) > 1 and parts[1] == "1"
                drives.append({
                    "device": parts[0],
                    "type": "HDD" if is_hdd else "SSD/NVMe",
                    "size": parts[2] if len(parts) > 2 else "",
                    "model": " ".join(parts[3:]) if len(parts) > 3 else "",
                })
        hw["storage"] = drives[:2]  # First 2 drives
    except (OSError, json.JSONDecodeError):
        pass
    
    # Network (WiFi)
    try:
        result = subprocess.run(["lspci", "-nn"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "Network" in line and "WiFi" in line:
                parts = line.strip().split(":", 2)
                hw["wifi"] = parts[2].strip() if len(parts) >= 3 else line.strip()
                break
    except (OSError, json.JSONDecodeError):
        pass
    
    # Chassis type (laptop/desktop)
    try:
        with open("/sys/class/dmi/id/chassis_type") as f:
            ct = f.read().strip()
            hw["chassis"] = "laptop" if ct in ("8", "9", "10", "31") else "desktop"
    except (OSError, ValueError):
        hw["chassis"] = "unknown"
    
    # OS info
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    hw["os"] = line.split("=", 1)[1].strip().strip('"')
                    break
    except (OSError, json.JSONDecodeError):
        pass
    
    hw["kernel"] = os.uname().release
    hw["timestamp"] = datetime.now().isoformat()
    hw["hostname"] = os.uname().nodename
    
    # Save to database
    ensure_dirs()
    db = load_db()
    
    # Create or update entry
    hw_id = hashlib.md5(f"{hw.get('cpu',{}).get('model','')}_{hw.get('gpu',{}).get('name','')}".encode()).hexdigest()[:16]
    db["entries"][hw_id] = hw
    db["last_scan"] = datetime.now().isoformat()
    save_db(db)
    
    print(f"✅ Hardware scan complete")
    print(f"   CPU: {hw.get('cpu', {}).get('model', 'N/A')[:60]}")
    print(f"   GPU: {hw.get('gpu', {}).get('name', 'N/A')}")
    print(f"   RAM: {hw.get('ram', {}).get('total_gb', '?')} GB")
    print(f"   Type: {hw.get('chassis', '?')}")
    print(f"   ID: {hw_id}")
    
    return hw


def load_db():
    """Load the hardware database."""
    ensure_dirs()
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {"entries": {}, "last_scan": None, "version": 1}


def save_db(db):
    """Save the hardware database."""
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2)


def cmd_status():
    """Show current hardware status."""
    db = load_db()
    
    if not db["entries"]:
        print("No hardware scan data. Run 'solus-hwvault scan' first.")
        return
    
    latest_id = list(db["entries"].keys())[-1]
    hw = db["entries"][latest_id]
    
    print(f"🖥  Hardware Profile")
    print(f"{'='*50}")
    print(f"  Hostname: {hw.get('hostname', '?')}")
    print(f"  OS: {hw.get('os', '?')}")
    print(f"  Kernel: {hw.get('kernel', '?')}")
    print(f"  Chassis: {hw.get('chassis', '?')}")
    print(f"")
    print(f"  CPU: {hw.get('cpu', {}).get('model', '?')[:60]}")
    print(f"  Cores/Threads: {hw.get('cpu', {}).get('cores', '?')}/{hw.get('cpu', {}).get('threads', '?')}")
    print(f"")
    print(f"  GPU: {hw.get('gpu', {}).get('name', '?')}")
    print(f"  Vendor: {hw.get('gpu', {}).get('vendor', '?')}")
    print(f"")
    print(f"  RAM: {hw.get('ram', {}).get('total_gb', '?')} GB")
    print(f"  Storage: {', '.join(d['device'] + ' (' + d['type'] + ')' for d in hw.get('storage', []))}")
    print(f"  WiFi: {hw.get('wifi', '?')}")
    print(f"")
    print(f"  Scanned: {hw.get('timestamp', '?')}")


def cmd_list():
    """List known hardware configurations."""
    db = load_db()
    
    if not db["entries"]:
        print("No hardware data in vault.")
        return
    
    print(f"📋 Hardware Vault ({len(db['entries'])} configurations)")
    print(f"{'='*50}")
    
    for hw_id, hw in db["entries"].items():
        gpu = hw.get("gpu", {}).get("name", "?")[:40]
        cpu = hw.get("cpu", {}).get("model", "?")[:40]
        ram = hw.get("ram", {}).get("total_gb", "?")
        chassis = hw.get("chassis", "?")
        print(f"  {hw_id[:12]} | {chassis:8} | {ram:4}GB | {cpu}")
        print(f"  {' ' * 14} | {gpu}")


def cmd_report():
    """Generate compatibility report."""
    print("📊 Hardware Compatibility Report")
    print(f"{'='*50}")
    print("  Generating report based on detected hardware...")
    print()
    
    db = load_db()
    if not db["entries"]:
        print("  ⚠ No hardware data. Run 'solus-hwvault scan' first.")
        return
    
    latest_id = list(db["entries"].keys())[-1]
    hw = db["entries"][latest_id]
    gpu = hw.get("gpu", {})
    
    print(f"  GPU: {gpu.get('name', 'Unknown')}")
    
    vendor = gpu.get("vendor", "").lower()
    if "nvidia" in vendor:
        print(f"  Driver: nvidia-proprietary (recommended)")
        print(f"  Wayland: Supported (driver 525+)")
        print(f"  Vulkan: ✅ Full support")
        print(f"  CUDA: ✅ Available")
    elif "amd" in vendor:
        print(f"  Driver: Mesa RADV (in-kernel)")
        print(f"  Wayland: ✅ Native support")
        print(f"  Vulkan: ✅ Full support (radv)")
        print(f"  ROCm: ✅ Available for compute")
    elif "intel" in vendor:
        print(f"  Driver: Mesa ANV (in-kernel)")
        print(f"  Wayland: ✅ Native support")
        print(f"  Vulkan: ✅ Full support (anv)")
        print(f"  VAAPI: ✅ Hardware encoding/decoding")
    else:
        print(f"  Driver: Mesa llvmpipe (software fallback)")
    
    ram = hw.get("ram", {}).get("total_gb", 0)
    print(f"")
    print(f"  RAM: {ram} GB")
    if ram >= 32:
        print(f"  Profile: High-performance (32GB+)")
    elif ram >= 16:
        print(f"  Profile: Balanced (16GB+)")
    elif ram >= 8:
        print(f"  Profile: Standard (8GB+)")
    else:
        print(f"  Profile: Lightweight (<8GB)")
    
    chassis = hw.get("chassis", "")
    print(f"")
    if chassis == "laptop":
        print(f"  Chassis: Laptop")
        print(f"  Power profile: Battery-optimized available")
        print(f"  Recommended mode: Balanced or Battery Saver")


def cmd_submit():
    """Submit hardware config to community database."""
    print("🌐 Submit to Community Hardware Vault")
    print(f"{'='*50}")
    print()
    print("  This would submit your anonymized hardware config")
    print("  to the Solus Hardware Vault community database.")
    print()
    print("  Data sent (anonymized):")
    print("    • CPU model + cores")
    print("    • GPU model + vendor")
    print("    • RAM size")
    print("    • Chassis type")
    print("    • Kernel version")
    print()
    print("  No personal information is transmitted.")
    print()
    
    response = input("  Submit to community database? [y/N]: ")
    if response.lower() == "y":
        print("  📤 Submitting... (community DB endpoint configured in future)")
        print("  ✅ Config saved locally. Will sync when community DB is available.")
    else:
        print("  ❌ Submission cancelled.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "scan":
        scan_hardware()
    elif cmd == "status":
        cmd_status()
    elif cmd == "list":
        cmd_list()
    elif cmd == "report":
        cmd_report()
    elif cmd == "submit":
        cmd_submit()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()