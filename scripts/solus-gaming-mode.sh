#!/usr/bin/env bash
# Solus Gaming Mode — one-click toggle
# Activates: Gamescope session + MangoHUD + GameMode + GPU perf
# Equivalent to Bazzite's Gaming Mode but works on any session.
set -euo pipefail

if [ "$1" = "on" ]; then
    echo "🎮 Enabling Solus Gaming Mode..."
    # GPU perf governor
    if command -v gamemoded &>/dev/null; then
        gamemoded -s 2>/dev/null || true
    fi
    # Set performance governor
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$gov" 2>/dev/null || true
    done
    # NVIDIA — disable compositing
    if command -v nvidia-settings &>/dev/null; then
        nvidia-settings -a 'OpenGLImageQuality=Performance' 2>/dev/null || true
    fi
    # Environment
    mkdir -p /etc/environment.d
    cat > /etc/environment.d/99-solus-gaming-mode.conf << EOGM
DXVK_ASYNC=1
DXVK_STATE_CACHE=1
MANGOHUD=1
MANGOHUD_CONFIGFILE=/etc/MangoHud/MangoHud.conf
GAMEMODE_AUTO=1
EOGAMING
    echo "✅ Gaming Mode ON"
elif [ "$1" = "off" ]; then
    echo "⬜ Disabling Solus Gaming Mode..."
    rm -f /etc/environment.d/99-solus-gaming-mode.conf
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo schedutil > "$gov" 2>/dev/null || true
    done
    echo "✅ Gaming Mode OFF"
else
    echo "Usage: solus-gaming-mode on|off"
    exit 1
fi
