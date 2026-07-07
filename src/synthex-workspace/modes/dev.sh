#!/usr/bin/env bash
#===============================================================================
# Synthex Workspace — Developer Mode
#===============================================================================
# Configures the system for development work:
#   - CPU governor: schedutil (good responsiveness + power efficiency)
#   - Services: start Podman, Docker
#   - Tuned: desktop profile
#   - Layout: dev
#===============================================================================

set -euo pipefail

notify_user() {
    local title="$1" msg="$2"
    command -v notify-send &>/dev/null && notify-send -i utilities-terminal "Synthex Workspace" "${title}: ${msg}" 2>/dev/null || true
    echo "[${title}] ${msg}"
}

# --- CPU Governor: SchedUtil -------------------------------------------------
notify_user "Dev Mode" "Setting CPU governor to schedutil..."
if command -v cpupower &>/dev/null; then
    cpupower frequency-set -g schedutil 2>/dev/null || true
elif [[ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo "schedutil" > "${gov}" 2>/dev/null || true
    done
fi

# --- Start Developer Services ------------------------------------------------
notify_user "Dev Mode" "Starting developer services (Podman, Docker)..."
for svc in podman docker; do
    systemctl start --user "${svc}" 2>/dev/null && notify_user "Dev Mode" "${svc} started" || true
done

# Also try system-level if needed
for svc in podman docker; do
    sudo systemctl start "${svc}" 2>/dev/null || true
done

# Enable developer-friendly sysctls
if [[ $EUID -eq 0 ]]; then
    # Lower swappiness for responsiveness during development
    echo 10 > /proc/sys/vm/swappiness 2>/dev/null || true
fi

# --- Tuned Profile ----------------------------------------------------------
if command -v tuned-adm &>/dev/null; then
    notify_user "Dev Mode" "Setting tuned profile to desktop..."
    tuned-adm profile desktop 2>/dev/null || true
fi

# --- Synthex Layout -----------------------------------------------------------
if command -v synthex-layout &>/dev/null; then
    sudo synthex-layout set dev 2>/dev/null || true
fi

notify_user "Dev Mode" "Developer mode active"
echo "Developer mode active."
echo "  CPU: schedutil"
echo "  Services: Docker, Podman started"
echo "  Profile: desktop"
