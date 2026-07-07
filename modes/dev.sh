#!/usr/bin/env bash
# Synthex Developer Mode
# Optimizes system for development work

set -euo pipefail

echo "💻 Activating Developer Mode..."

# CPU governor to schedutil (balanced with good responsiveness)
echo "⚡ Setting CPU governor to schedutil..."
cpupower frequency-set -g schedutil 2>/dev/null || true

# GPU to balanced
echo "🖥  Setting GPU to balanced..."
if [ -d /sys/class/drm/card0/device ]; then
    echo "auto" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
fi

# Enable compositor
echo "🎨 Enabling compositor..."
qdbus org.kde.KWin /Compositor resume 2>/dev/null || true

# Start container services
echo "📦 Starting container services..."
systemctl start podman 2>/dev/null || true
systemctl start docker 2>/dev/null || true

# Enable tracker for file search (useful for devs)
systemctl start --user tracker-miner-fs 2>/dev/null || true

# Set tuned profile
echo "🔧 Setting tuned profile..."
tuned-adm profile desktop 2>/dev/null || true

# Apply dev layout
echo "🎨 Applying dev layout..."
synthex-layout set balanced 2>/dev/null || true

# Notify
notify-send -i terminal "Developer Mode" "Development environment ready" 2>/dev/null || echo "✅ Developer Mode active"

echo ""
echo "═══════════════════════════════════"
echo "  💻 Developer Mode Activated"
echo "  • CPU: Schedutil governor"
echo "  • GPU: Balanced"
echo "  • Podman/Docker: Started"
echo "  • Compositor: Enabled"
echo "═══════════════════════════════════"
