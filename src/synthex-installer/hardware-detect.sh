#!/usr/bin/env bash
# hardware-detect.sh — Detect hardware and configure drivers
# Runs during install to auto-configure the target system
set -euo pipefail

echo "🖥️  Synthex hardware detection..."

HW_PROFILE="/var/run/synthex-hw-profile.json"
mkdir -p "$(dirname "$HW_PROFILE")"

# ─── Detect GPU ───────────────────────────────────────────────────────
GPU=""
GPU_VENDOR=""
GPU_NVIDIA=false
GPU_AMD=false
GPU_INTEL=false

if lspci | grep -qi 'VGA.*NVIDIA'; then
    GPU="NVIDIA"; GPU_VENDOR="nvidia"; GPU_NVIDIA=true
    GPU_MODEL=$(lspci | grep -i 'VGA.*NVIDIA' | sed 's/.*NVIDIA //' | head -1)
elif lspci | grep -qi 'VGA.*AMD\|VGA.*ATI\|Display.*AMD'; then
    GPU="AMD"; GPU_VENDOR="amd"; GPU_AMD=true
    GPU_MODEL=$(lspci | grep -iE 'VGA.*AMD|Display.*AMD' | sed 's/.*AMD/AMD/' | head -1)
elif lspci | grep -qi 'VGA.*Intel'; then
    GPU="Intel"; GPU_VENDOR="intel"; GPU_INTEL=true
    GPU_MODEL=$(lspci | grep -i 'VGA.*Intel' | sed 's/.*Intel //' | head -1)
fi

echo "  GPU: ${GPU:-unknown} (${GPU_MODEL:-N/A})"

# ─── Detect CPU ───────────────────────────────────────────────────────
CPU=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')
CPU_VENDOR=$(grep -m1 'vendor_id' /proc/cpuinfo | cut -d: -f2 | sed 's/^ *//' | tr '[:upper:]' '[:lower:]')
CPU_CORES=$(grep -c '^processor' /proc/cpuinfo)
CPU_THREADS=$(nproc 2>/dev/null || echo "$CPU_CORES")

echo "  CPU: $CPU ($CPU_CORES cores / $CPU_THREADS threads)"

# ─── Detect RAM ───────────────────────────────────────────────────────
RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
RAM_GB=$((RAM_KB / 1024 / 1024))
echo "  RAM: ${RAM_GB} GB"

# ─── Detect form factor ───────────────────────────────────────────────
FORM_FACTOR="desktop"
if [ -d /sys/class/power_supply ]; then
    if ls /sys/class/power_supply/*/type 2>/dev/null | head -1 | xargs cat 2>/dev/null | grep -qi battery; then
        FORM_FACTOR="laptop"
    fi
fi
# Detect handhelds
DMI_PRODUCT=$(cat /sys/class/dmi/id/product_name 2>/dev/null || echo "")
if echo "$DMI_PRODUCT" | grep -qi "Jupiter\|Galileo"; then
    FORM_FACTOR="steamdeck"
elif echo "$DMI_PRODUCT" | grep -qi "ROG Ally\|RC71L\|Legion Go"; then
    FORM_FACTOR="handheld"
fi
echo "  Form factor: $FORM_FACTOR"

# ─── Detect storage type ──────────────────────────────────────────────
STORAGE_TYPE="hdd"
if lsblk -d -o ROTA 2>/dev/null | grep -q "^0$"; then
    if lsblk -d -o TRAN 2>/dev/null | grep -q nvme; then
        STORAGE_TYPE="nvme"
    else
        STORAGE_TYPE="ssd"
    fi
fi
echo "  Storage: $STORAGE_TYPE"

# ─── Detect monitor / display ─────────────────────────────────────────
MONITOR=""
if command -v xrandr &>/dev/null; then
    MONITOR=$(xrandr --current 2>/dev/null | grep ' connected' | head -1 | awk '{print $1}')
fi

# ─── Write profile JSON ───────────────────────────────────────────────
cat > "$HW_PROFILE" << EOF
{
  "gpu": {
    "vendor": "$GPU_VENDOR",
    "model": "$GPU_MODEL",
    "nvidia": $GPU_NVIDIA,
    "amd": $GPU_AMD,
    "intel": $GPU_INTEL
  },
  "cpu": {
    "model": "$CPU",
    "vendor": "$CPU_VENDOR",
    "cores": $CPU_CORES,
    "threads": $CPU_THREADS
  },
  "ram_gb": $RAM_GB,
  "form_factor": "$FORM_FACTOR",
  "storage_type": "$STORAGE_TYPE",
  "monitor": "$MONITOR",
  "dmi_product": "$DMI_PRODUCT",
  "timestamp": "$(date -Iseconds)"
}
EOF

echo "  Profile written to $HW_PROFILE"

# ─── Auto-install GPU drivers ─────────────────────────────────────────
echo "  Configuring GPU drivers..."
if [ "$GPU_NVIDIA" = "true" ]; then
    echo "  → Installing NVIDIA drivers..."
    dnf install -y akmod-nvidia nvidia-settings nvidia-prime 2>/dev/null || true
    echo "options nvidia-drm modeset=1" > /etc/modprobe.d/nvidia.conf 2>/dev/null || true
elif [ "$GPU_AMD" = "true" ]; then
    echo "  → AMD: ensuring Mesa + RADV..."
    dnf install -y mesa-vulkan-drivers mesa-dri-drivers 2>/dev/null || true
elif [ "$GPU_INTEL" = "true" ]; then
    echo "  → Intel: ensuring Mesa + media drivers..."
    dnf install -y mesa-vulkan-drivers intel-media-driver 2>/dev/null || true
fi

# ─── Configure ZRAM based on RAM ──────────────────────────────────────
echo "  Configuring ZRAM..."
if [ "$RAM_GB" -lt 8 ]; then
    ZRAM_FRAC=1.0  # Low RAM: full ZRAM
elif [ "$RAM_GB" -lt 16 ]; then
    ZRAM_FRAC=0.5
else
    ZRAM_FRAC=0.25  # High RAM: less ZRAM
fi
cat > /etc/systemd/zram-generator.conf << EOF
[zram0]
zram-fraction = $ZRAM_FRAC
max-zram-size = 16384
compression-algorithm = zstd
EOF

# ─── Configure I/O scheduler ──────────────────────────────────────────
echo "  Configuring I/O scheduler..."
case "$STORAGE_TYPE" in
    nvme) SCHED="none" ;;
    ssd)  SCHED="mq-deadline" ;;
    *)    SCHED="bfq" ;;
esac
for dev in /sys/block/sd*/queue/scheduler /sys/block/nvme*/queue/scheduler; do
    [ -f "$dev" ] && echo "$SCHED" > "$dev" 2>/dev/null || true
done

echo "✅ Hardware detection complete"
