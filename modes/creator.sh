#!/usr/bin/env bash
# Synthex Creator Mode
# Optimizes for creative workloads (Blender, OBS, Krita, DaVinci)

set -euo pipefail

echo "🎨 Activating Creator Mode..."

# CPU governor to performance
echo "⚡ Setting CPU governor to performance..."
cpupower frequency-set -g performance 2>/dev/null || true

# GPU to high performance for compute
echo "🖥  Setting GPU to high performance..."
if [ -d /sys/class/drm/card0/device ]; then
    echo "high" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Enable compositor (creators need preview)
echo "🎨 Enabling compositor with quality settings..."
qdbus org.kde.KWin /Compositor resume 2>/dev/null || true

# Start media services
echo "🎵 Starting audio services..."
systemctl start --user pipewire wireplumber 2>/dev/null || true

# Set tuned profile for latency
echo "🔧 Setting tuned profile..."
tuned-adm profile latency-performance 2>/dev/null || true

# Increase inotify watches for media files
echo "📁 Configuring file watchers..."
sysctl fs.inotify.max_user_watches=524288 2>/dev/null || true

# Notify
notify-send -i video "Creator Mode" "Optimized for creative workloads" 2>/dev/null || echo "✅ Creator Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  🎨 Creator Mode Activated"
echo "  • CPU: Performance governor"
echo "  • GPU: High performance (compute)"
echo "  • Audio: PipeWire optimized"
echo "  • Tuned: Latency-performance"
echo "  • Inotify: 524288 watches"
echo "═══════════════════════════════════"
