#!/usr/bin/env bash
# synthex-hardware-detect.sh — Hardware detection and optimization
# Installed to /usr/libexec/synthex/hardware-detect.sh
set -euo pipefail

LOG="/var/log/synthex-hardware-detect.log"
echo "=== Hardware Detection $(date) ===" | tee "$LOG"

# CPU detection
echo "CPU:" | tee -a "$LOG"
grep "^model name" /proc/cpuinfo | head -1 | tee -a "$LOG"
CORES=$(nproc)
echo "  Cores: $CORES" | tee -a "$LOG"

# RAM detection
TOTAL_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM / 1024 / 1024))
echo "RAM: ${TOTAL_RAM_GB}GB" | tee -a "$LOG"

# GPU detection
echo "GPU:" | tee -a "$LOG"
lspci -nn -d ::0300 2>/dev/null | head -3 | tee -a "$LOG" || echo "  No GPU found" | tee -a "$LOG"

# Disk detection
echo "Disks:" | tee -a "$LOG"
lsblk -d -o NAME,SIZE,TYPE,MOUNTPOINT 2>/dev/null | head -10 | tee -a "$LOG" || true

# Form factor
if [ -f /sys/class/dmi/id/chassis_type ]; then
    CHASSIS=$(cat /sys/class/dmi/id/chassis_type)
    case "$CHASSIS" in
        3|4|5|6|7|15|16) echo "Form Factor: Desktop" | tee -a "$LOG" ;;
        8|9|10|31)       echo "Form Factor: Laptop" | tee -a "$LOG" ;;
        *)               echo "Form Factor: Unknown ($CHASSIS)" | tee -a "$LOG" ;;
    esac
fi

# Save detection results
mkdir -p /etc/synthex-installer
lspci -nn 2>/dev/null > /etc/synthex-installer/lspci.txt || true
cat /proc/cpuinfo > /etc/synthex-installer/cpuinfo.txt 2>/dev/null || true

# Apply optimizations based on RAM
if [ "$TOTAL_RAM_GB" -lt 4 ]; then
    echo "Low RAM: enabling zram..." | tee -a "$LOG"
    echo 'zram' > /etc/modules-load.d/zram.conf 2>/dev/null || true
fi

echo "=== Hardware detection complete ===" | tee -a "$LOG"
exit 0
