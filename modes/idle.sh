#!/usr/bin/env bash
# Solus Idle Mode — minimize background activity for lowest footprint
# Use when stepping away: quiet fans, no indexers, powersave clocks.

set -euo pipefail

echo "🛌 Activating Idle Mode..."

# CPU governor to powersave (lowest clocks)
echo "⚡ Setting CPU governor to powersave..."
cpupower frequency-set -g powersave 2>/dev/null || true

# Energy Performance Preference: power
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    [ -w "$cpu" ] && echo "power" > "$cpu" 2>/dev/null || true
done

# GPU to low power
if [ -d /sys/class/drm/card0/device ]; then
    echo "low" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Stop background miners/indexers/telemetry (system + user)
echo "🛑 Stopping background activity..."
for svc in tracker-miner-fs tracker-extract geoclue packagekit abrtd baloo; do
    systemctl stop "$svc" 2>/dev/null || true
    systemctl --user stop "$svc" 2>/dev/null || true
done

# Reclaim memory immediately
echo "🧹 Reclaiming memory..."
sync 2>/dev/null || true
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true

# NVMe autosuspend to save idle power
for dev in /sys/class/nvme/nvme*/device/power/control; do
    [ -w "$dev" ] && echo "auto" > "$dev" 2>/dev/null || true
done

notify-send -i preferences-system-power "Idle Mode" "Background activity minimized" 2>/dev/null || echo "✅ Idle Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  🛌 Idle Mode Activated"
echo "  • CPU: Powersave governor + EPP power"
echo "  • GPU: Low power"
echo "  • Indexers/miners: Stopped"
echo "  • Memory: Caches dropped"
echo "  • NVMe: Autosuspend"
echo "═══════════════════════════════════"
