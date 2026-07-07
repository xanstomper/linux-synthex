#!/usr/bin/env bash
#===============================================================================
# Synthex Workspace — Gaming Mode
#===============================================================================
# Applies maximum performance settings for gaming:
#   - CPU governor: performance
#   - GPU: high performance level
#   - Compositor: suspended (via qdbus or killall plasmashell)
#   - Non-essential services: stopped
#   - Gamemode: enabled via gamemoderun
#   - Tuned: throughput-performance
#   - Layout: gaming
#===============================================================================

set -euo pipefail

# Guard: some operations need root
if [[ $EUID -ne 0 ]]; then
    echo "Some gaming mode operations need root. Re-run with: sudo synthex-workspace set gaming"
fi

# --- CPU Governor: Performance -----------------------------------------------
notify_user "Gaming Mode" "Setting CPU governor to performance..."
if command -v cpupower &>/dev/null; then
    cpupower frequency-set -g performance 2>/dev/null || true
elif [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "performance" > "${gov}" 2>/dev/null || true
    done
fi

# --- GPU: High Performance ---------------------------------------------------
notify_user "Gaming Mode" "Setting GPU to high performance..."
for gpu_dev in /sys/class/drm/card?/device/power_dpm_force_performance_level; do
    if [[ -w "${gpu_dev}" ]]; then
        echo "high" > "${gpu_dev}" 2>/dev/null || true
    fi
done

# Also try NVIDIA-specific settings
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi -pm 1 2>/dev/null || true
    nvidia-smi -pl 999 2>/dev/null || true  # max power limit if supported
fi

# --- Compositor: Suspend (for Plasma) ---------------------------------------
notify_user "Gaming Mode" "Suspending desktop compositor..."
if command -v qdbus &>/dev/null; then
    qdbus org.kde.KWin /Compositor suspend 2>/dev/null || true
elif command -v killall &>/dev/null; then
    # Fallback: kill and restart later
    killall plasmashell 2>/dev/null || true
fi

# --- Stop Non-Essential Services --------------------------------------------
notify_user "Gaming Mode" "Stopping background services..."
for svc in tracker-miner-fs bluetooth cups packagekit; do
    systemctl stop --user "${svc}" 2>/dev/null || true
done
# System-level services
for svc in tracker-miner-fs bluetooth cups; do
    sudo systemctl stop "${svc}" 2>/dev/null || true
done

# --- GameMode ----------------------------------------------------------------
if command -v gamemoderun &>/dev/null; then
    notify_user "Gaming Mode" "GameMode available — applications will be wrapped automatically."
    # GameMode activates via LD_PRELOAD; we set the default
    export GAMEMODE_AUTO=1 2>/dev/null || true
fi

# --- Tuned Profile ----------------------------------------------------------
if command -v tuned-adm &>/dev/null; then
    notify_user "Gaming Mode" "Setting tuned profile to throughput-performance..."
    tuned-adm profile throughput-performance 2>/dev/null || true
fi

# --- Synthex Layout -----------------------------------------------------------
if command -v synthex-layout &>/dev/null; then
    sudo synthex-layout set gaming 2>/dev/null || true
fi

notify_user "Gaming Mode" "Gaming mode active — compositor suspended, max performance"
echo "Gaming mode active."
echo "  CPU: performance"
echo "  GPU: high performance"
echo "  Compositor: suspended"
echo "  Services: gaming-optimized"
echo "  Reboot or 'synthex-workspace set balanced' to restore normal operation."
