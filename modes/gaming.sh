#!/usr/bin/env bash
# Synthex Gaming Mode
# Optimizes system for maximum gaming performance

set -euo pipefail

echo "🎮 Activating Gaming Mode..."

# CPU governor to performance
echo "⚡ Setting CPU governor to performance..."
cpupower frequency-set -g performance 2>/dev/null || true

# GPU to high performance
echo "🖥  Setting GPU to high performance..."
if [ -d /sys/class/drm/card0/device ]; then
    echo "high" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Disable compositor effects
echo "🎨 Disabling compositor effects..."
qdbus org.kde.KWin /Compositor suspend 2>/dev/null || true
kwriteconfig6 --file ~/.config/kwinrc --group Compositing --key Enabled false 2>/dev/null || true

# Stop unnecessary services
echo "🛑 Stopping background services..."
for svc in bluetooth cups geoclue packagekit abrtd tracker-miner-fs; do
    systemctl stop "$svc" 2>/dev/null || true
done

# Enable gamemode
echo "🎯 Enabling GameMode..."
systemctl start gamemoded 2>/dev/null || true

# Set tuned profile
echo "🔧 Setting tuned profile..."
tuned-adm profile throughput-performance 2>/dev/null || true

# Apply gaming layout
echo "🎨 Applying gaming layout..."
synthex-layout set gaming 2>/dev/null || true

# Notify
notify-send -i games "Gaming Mode" "System optimized for gaming performance" 2>/dev/null || echo "✅ Gaming Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  🎮 Gaming Mode Activated"
echo "  • CPU: Performance governor"
echo "  • GPU: High performance"
echo "  • Compositor: Disabled"
echo "  • Background services: Stopped"
echo "  • GameMode: Enabled"
echo "═══════════════════════════════════"
