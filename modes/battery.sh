#!/usr/bin/env bash
# Solus Battery Mode
# Optimizes system for maximum battery life

set -euo pipefail

echo "🔋 Activating Battery Saving Mode..."

# CPU governor to powersave
echo "⚡ Setting CPU governor to powersave..."
cpupower frequency-set -g powersave 2>/dev/null || true

# GPU to low power
echo "🖥  Setting GPU to low power..."
if [ -d /sys/class/drm/card0/device ]; then
    echo "low" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Enable compositor but reduce effects
echo "🎨 Optimizing compositor..."
kwriteconfig6 --file ~/.config/kwinrc --group Compositing --key Enabled true 2>/dev/null || true
kwriteconfig6 --file ~/.config/kwinrc --group Compositing --key OpenGLIsUnsafe false 2>/dev/null || true

# Stop unnecessary services
echo "🛑 Stopping background services..."
for svc in geoclue tracker-miner-fs abrtd; do
    systemctl stop "$svc" 2>/dev/null || true
done

# Stop bluetooth if not in use
if ! bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
    systemctl stop bluetooth 2>/dev/null || true
fi

# Set tuned profile
echo "🔧 Setting tuned profile..."
tuned-adm profile powersave 2>/dev/null || true

# Reduce screen brightness on laptops
if command -v brightnessctl &>/dev/null; then
    brightnessctl set 30% 2>/dev/null || true
fi

# Notify
notify-send -i battery "Battery Mode" "Power saving settings applied" 2>/dev/null || echo "✅ Battery Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  🔋 Battery Mode Activated"
echo "  • CPU: Powersave governor"
echo "  • GPU: Low power"
echo "  • Background services: Reduced"
echo "  • Tuned: Powersave profile"
echo "  • Screen: Dimmed to 30%"
echo "═══════════════════════════════════"
