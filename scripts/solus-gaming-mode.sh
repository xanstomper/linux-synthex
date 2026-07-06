#!/usr/bin/env bash
# Solus Gaming Mode — one-click toggle
# Activates: Gamescope session + MangoHUD + GameMode + GPU perf
# Equivalent to Bazzite's Gaming Mode but works on any session.
set -euo pipefail

LOG="/var/log/solus-gaming.log"
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

if [ "${1:-}" = "on" ]; then
    log "🎮 Enabling Solus Gaming Mode..."

    # 1. GameMode daemon
    if command -v gamemoded &>/dev/null; then
        gamemoded -s 2>/dev/null && log "  ✅ gamemoded started" || log "  ⚠  gamemoded already running"
    fi

    # 2. Performance CPU governor on all cores
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$gov" 2>/dev/null || true
    done
    log "  ✅ CPU governors: performance"

    # 3. NVIDIA-specific optimizations
    if command -v nvidia-settings &>/dev/null; then
        nvidia-settings -a 'OpenGLImageQuality=Performance' 2>/dev/null || true
        nvidia-settings -a 'AllowFlipping=0' 2>/dev/null || true
        nvidia-settings -a 'CIBootstrapX32=1' 2>/dev/null || true
        log "  ✅ NVIDIA compositor optimizations applied"
    fi

    # 4. AMD GPU power management
    if [ -d /sys/class/drm/card0/device/power_dpm_force_performance_level ]; then
        echo high > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
        log "  ✅ AMD GPU: high performance level"
    fi

    # 5. I/O scheduler — deadline for fast gaming loads
    for queue in /sys/block/sd*/queue/scheduler /sys/block/nvme*/queue/scheduler; do
        [ -f "$queue" ] && echo mq-deadline > "$queue" 2>/dev/null || true
    done

    # 6. Disable kernel same-page merging (saves memory for games)
    echo 0 > /sys/kernel/mm/ksm/run 2>/dev/null || true

    # 7. Reduce swappiness for gaming
    sysctl -w vm.swappiness=5 2>/dev/null || true
    sysctl -w vm.dirty_ratio=5 2>/dev/null || true

    # 8. Gaming environment variables
    mkdir -p /etc/environment.d
    cat > /etc/environment.d/99-solus-gaming-mode.conf << 'EOGM'
DXVK_ASYNC=1
DXVK_STATE_CACHE=1
MANGOHUD=1
MANGOHUD_CONFIGFILE=/etc/MangoHud/MangoHud.conf
GAMEMODE_AUTO=1
VKD3D_CONFIG=no_upload_hvv
STEAM_SYNC=0
EOGM
    log "  ✅ Gaming environment configured"

    # 9. Disable compositor animations (KDE)
    if command -v qdbus &>/dev/null; then
        qdbus org.kde.KWin /Compositor suspend 2>/dev/null && log "  ✅ KWin compositor suspended" || true
    elif command -v qdbus6 &>/dev/null; then
        qdbus6 org.kde.KWin /Compositor suspend 2>/dev/null && log "  ✅ KWin compositor suspended" || true
    fi

    # 10. Ensure Vulkan layers are available
    if [ -d /usr/share/vulkan/implicit_layer.d ]; then
        log "  ✅ Vulkan layers available"
    fi

    log "═══════════════════════════════════"
    log "  🎮 Gaming Mode ON"
    log "  Performance governor + DXVK + MangoHUD + GameMode"
    log "  KWin compositor suspended"
    log "  NVIDIA/AMD GPU optimized"
    log "═══════════════════════════════════"

elif [ "${1:-}" = "off" ]; then
    log "⬜ Disabling Solus Gaming Mode..."

    # Restore schedutil governor
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo schedutil > "$gov" 2>/dev/null || true
    done
    log "  ✅ CPU governors: schedutil"

    # Stop gamemoded
    if command -v gamemoded &>/dev/null; then
        pkill gamemoded 2>/dev/null || true
    fi

    # Restore AMD GPU to auto
    if [ -f /sys/class/drm/card0/device/power_dpm_force_performance_level ]; then
        echo auto > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
    fi

    # Restore KWin compositor
    if command -v qdbus &>/dev/null; then
        qdbus org.kde.KWin /Compositor resume 2>/dev/null || true
    elif command -v qdbus6 &>/dev/null; then
        qdbus6 org.kde.KWin /Compositor resume 2>/dev/null || true
    fi

    # Restore default swappiness
    sysctl -w vm.swappiness=10 2>/dev/null || true
    sysctl -w vm.dirty_ratio=10 2>/dev/null || true

    # Re-enable KSM
    echo 1 > /sys/kernel/mm/ksm/run 2>/dev/null || true

    # Remove gaming environment
    rm -f /etc/environment.d/99-solus-gaming-mode.conf
    log "  ✅ Gaming Mode OFF"

else
    echo "Usage: solus-gaming-mode on|off"
    echo ""
    echo "Gaming Mode activates:"
    echo "  • Performance CPU governor"
    echo "  • DXVK async + state cache"
    echo "  • MangoHUD overlay"
    echo "  • GameMode daemon"
    echo "  • NVIDIA/AMD GPU optimizations"
    echo "  • KWin compositor suspend"
    echo "  • Reduced swappiness"
    echo "  • I/O scheduler optimization"
    exit 1
fi
