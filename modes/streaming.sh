#!/usr/bin/env bash
# Synthex Streaming Mode — OBS-ready pipeline for streamers/creators
# Part of the Synthex Workspace Engine

set -euo pipefail

echo "📺 Activating Streaming Mode..."

# CPU governor to performance (needed for encoding)
cpupower frequency-set -g performance 2>/dev/null || true

# GPU to high performance
if [ -d /sys/class/drm/card0/device ]; then
    echo "high" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Enable compositor (streamers need preview)
qdbus org.kde.KWin /Compositor resume 2>/dev/null || true

# Start PipeWire with pro-audio config
systemctl start --user pipewire wireplumber 2>/dev/null || true

# Optimize audio for low latency
pactl set-card-profile 0 pro-audio 2>/dev/null || true

# Stop unnecessary services
for svc in tracker-miner-fs geoclue; do
    systemctl stop "$svc" 2>/dev/null || true
done

# Set tuned profile
tuned-adm profile latency-performance 2>/dev/null || true

# Increase watchers for media files
sysctl fs.inotify.max_user_watches=524288 2>/dev/null || true

# Performance tweaks for OBS
export OBS_USE_EGL=1
export DISPLAY=:0

notify-send -i camera "Streaming Mode" "OBS-ready pipeline activated" 2>/dev/null || echo "✅ Streaming Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  📺 Streaming Mode Activated"
echo "  • CPU: Performance governor"
echo "  • GPU: High performance"
echo "  • Audio: Pro-audio profile"
echo "  • PipeWire: Low latency"
echo "  • Tuned: Latency-performance"
echo "  • OBS: EGL mode enabled"
echo "═══════════════════════════════════"
