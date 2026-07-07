#!/usr/bin/env bash
#===============================================================================
# Synthex Workspace — Battery / Power Save Mode
#===============================================================================
# Maximizes battery life:
#   - CPU governor: powersave
#   - GPU: low power level
#   - Services: thermald enabled, non-essential stopped
#   - Backlight: reduced via i2c/ACPI
#   - Tuned: powersave
#===============================================================================

set -euo pipefail

notify_user() {
    local title="$1" msg="$2"
    command -v notify-send &>/dev/null && notify-send -i battery "Synthex Workspace" "${title}: ${msg}" 2>/dev/null || true
    echo "[${title}] ${msg}"
}

# --- CPU Governor: Powersave -------------------------------------------------
notify_user "Battery Mode" "Setting CPU governor to powersave..."
if command -v cpupower &>/dev/null; then
    cpupower frequency-set -g powersave 2>/dev/null || true
elif [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "powersave" > "${gov}" 2>/dev/null || true
    done
fi

# Also set CPU energy performance preference to power
for pref in /sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference; do
    [[ -w "${pref}" ]] && echo "power" > "${pref}" 2>/dev/null || true
done

# --- GPU: Low Power ----------------------------------------------------------
notify_user "Battery Mode" "Setting GPU to low power..."
for gpu_dev in /sys/class/drm/card?/device/power_dpm_force_performance_level; do
    if [[ -w "${gpu_dev}" ]]; then
        echo "low" > "${gpu_dev}" 2>/dev/null || true
    fi
done

# AMD GPU power management
for gpu_bapm in /sys/class/drm/card?/device/bapm; do
    [[ -w "${gpu_bapm}" ]] && echo "disable" > "${gpu_bapm}" 2>/dev/null || true
done

# NVIDIA power management
if command -v nvidia-smi &>/dev/null; then
    nvidia-smi -pm 1 2>/dev/null || true
    nvidia-smi -pl 50 2>/dev/null || true  # Power limit to 50W or min supported
fi

# --- Backlight Reduction -----------------------------------------------------
notify_user "Battery Mode" "Reducing display backlight..."
# Try i2c backlight control
if [[ -d /sys/class/backlight ]]; then
    for bl in /sys/class/backlight/*/brightness; do
        if [[ -w "${bl}" ]]; then
            local max_bl="${bl%/*}/max_brightness"
            if [[ -r "${max_bl}" ]]; then
                local max_val
                max_val=$(cat "${max_bl}")
                local low_val=$(( max_val / 3 ))  # ~33%
                echo "${low_val}" > "${bl}" 2>/dev/null || true
            fi
        fi
    done
fi

# --- Services ----------------------------------------------------------------
notify_user "Battery Mode" "Starting power-saving services..."
systemctl start --user thermald 2>/dev/null || true
sudo systemctl start thermald 2>/dev/null || true

# Stop non-essential services
for svc in tracker-miner-fs bluetooth cups packagekit; do
    systemctl stop --user "${svc}" 2>/dev/null || true
done
sudo systemctl stop bluetooth cups 2>/dev/null || true

# Disable WiFi power saving (ironically saves power)
for iface in /sys/class/net/wl*/power_save; do
    [[ -w "${iface}" ]] && echo "on" > "${iface}" 2>/dev/null || true
done

# --- Tuned Profile ----------------------------------------------------------
if command -v tuned-adm &>/dev/null; then
    notify_user "Battery Mode" "Setting tuned profile to powersave..."
    tuned-adm profile powersave 2>/dev/null || true
fi

# --- Enable PCIe ASPM for power saving ---------------------------------------
if [[ $EUID -eq 0 ]]; then
    echo "powersave" > /sys/module/pcie_aspm/parameters/policy 2>/dev/null || true
fi

notify_user "Battery Mode" "Battery saving mode active"
echo "Battery saving mode active."
echo "  CPU: powersave"
echo "  GPU: low power"
echo "  Backlight: reduced"
echo "  Profile: powersave"
