#!/usr/bin/env bash
#===============================================================================
# Synthex Workspace — Balanced Mode (Default)
#===============================================================================
# Default system mode for everyday use:
#   - CPU governor: ondemand (good balance)
#   - GPU: auto power level
#   - Services: normal desktop services running
#   - Tuned: desktop
#   - Layout: balanced
#===============================================================================

set -euo pipefail

notify_user() {
    local title="$1" msg="$2"
    command -v notify-send &>/dev/null && notify-send -i preferences-system "Synthex Workspace" "${title}: ${msg}" 2>/dev/null || true
    echo "[${title}] ${msg}"
}

# --- CPU Governor: Ondemand --------------------------------------------------
notify_user "Balanced Mode" "Setting CPU governor to ondemand..."
if command -v cpupower &>/dev/null; then
    cpupower frequency-set -g ondemand 2>/dev/null || true
elif [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "ondemand" > "${gov}" 2>/dev/null || true
    done
fi

# Set balanced energy_performance_preference
for pref in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    [[ -w "${pref}" ]] && echo "normal" > "${pref}" 2>/dev/null || true
done

# --- GPU: Auto Power Level ---------------------------------------------------
notify_user "Balanced Mode" "Setting GPU to auto power level..."
for gpu_dev in /sys/class/drm/card?/device/power_dpm_force_performance_level; do
    if [[ -w "${gpu_dev}" ]]; then
        echo "auto" > "${gpu_dev}" 2>/dev/null || true
    fi
done

# --- Restore Compositor ------------------------------------------------------
notify_user "Balanced Mode" "Restoring desktop compositor..."
if command -v qdbus &>/dev/null; then
    qdbus org.kde.KWin /Compositor resume 2>/dev/null || true
fi

# If plasmashell was killed, restart it
if ! pgrep -x plasmashell &>/dev/null; then
    kstart5 plasmashell 2>/dev/null || plasmashell --replace &>/dev/null &
    disown
fi

# --- Services: Start Normal Services -----------------------------------------
notify_user "Balanced Mode" "Starting normal desktop services..."
for svc in bluetooth cups; do
    systemctl start --user "${svc}" 2>/dev/null || true
    sudo systemctl start "${svc}" 2>/dev/null || true
done

# --- Tuned Profile ----------------------------------------------------------
if command -v tuned-adm &>/dev/null; then
    notify_user "Balanced Mode" "Setting tuned profile to desktop..."
    tuned-adm profile desktop 2>/dev/null || true
fi

# --- Synthex Layout -----------------------------------------------------------
if command -v synthex-layout &>/dev/null; then
    sudo synthex-layout set balanced 2>/dev/null || true
fi

# --- Restore normal swappiness -----------------------------------------------
if [[ $EUID -eq 0 ]]; then
    echo 60 > /proc/sys/vm/swappiness 2>/dev/null || true
fi

notify_user "Balanced Mode" "Balanced mode restored"
echo "Balanced mode active."
echo "  CPU: ondemand"
echo "  GPU: auto"
echo "  Compositor: restored"
echo "  Services: normal"
