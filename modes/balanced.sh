#!/usr/bin/env bash
# Synthex Balanced Mode (Default)
# Resets system to balanced defaults

set -euo pipefail

echo "⚖ Activating Balanced Mode..."

# CPU governor to ondemand
echo "⚡ Setting CPU governor to ondemand..."
cpupower frequency-set -g ondemand 2>/dev/null || true

# GPU to auto
echo "🖥  Setting GPU to auto..."
if [ -d /sys/class/drm/card0/device ]; then
    echo "auto" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Enable compositor with default settings
echo "🎨 Enabling compositor with defaults..."
qdbus org.kde.KWin /Compositor resume 2>/dev/null || true
kwriteconfig6 --file ~/.config/kwinrc --group Compositing --key Enabled true 2>/dev/null || true

# Restart normal services
echo "🔄 Starting normal services..."
for svc in bluetooth cups; do
    systemctl start "$svc" 2>/dev/null || true
done

# Set tuned profile
echo "🔧 Setting tuned profile..."
tuned-adm profile desktop 2>/dev/null || true

# Apply balanced layout
echo "🎨 Applying balanced layout..."
synthex-layout set balanced 2>/dev/null || true

# Notify
notify-send -i preferences "Balanced Mode" "System set to balanced defaults" 2>/dev/null || echo "✅ Balanced Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  ⚖ Balanced Mode Activated"
echo "  • CPU: Ondemand governor"
echo "  • GPU: Auto"
echo "  • Compositor: Enabled"
echo "  • Services: Normal"
echo "  • Tuned: Desktop profile"
echo "═══════════════════════════════════"
