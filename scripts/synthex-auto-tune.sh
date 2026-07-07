#!/usr/bin/env bash
# Synthex Auto-Tuning Engine
# Runs on first boot and on hardware changes. Detects GPU, CPU, RAM,
# storage, laptop/desktop/handheld, then auto-tunes everything.
set -euo pipefail

STATE_DIR="/var/lib/synthex"
STATE_FILE="$STATE_DIR/auto-tune-state.json"
LOG_FILE="/var/log/synthex-auto-tune.log"
mkdir -p "$STATE_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

log "=== Synthex Auto-Tuning Engine ==="

# ─── Detect GPU ──────────────────────────────────────────────────────
GPU_VENDOR="unknown"
if lspci -nn | grep -qi '10de'; then
    GPU_VENDOR="nvidia"
elif lspci -nn | grep -qi '1002'; then
    GPU_VENDOR="amd"
elif lspci -nn | grep -qi '8086'; then
    GPU_VENDOR="intel"
fi
log "GPU: $GPU_VENDOR"

# ─── Detect chassis ───────────────────────────────────────────────────
CHASSIS="desktop"
if [ -f /sys/class/dmi/id/chassis_type ]; then
    case "$(cat /sys/class/dmi/id/chassis_type 2>/dev/null)" in
        8|9|10|14) CHASSIS="laptop" ;;
        13) CHASSIS="handheld" ;;
    esac
fi
log "Chassis: $CHASSIS"

# ─── Detect storage ───────────────────────────────────────────────────
STORAGE_TYPE="hdd"
if ls /dev/nvme* 2>/dev/null | head -1 >/dev/null; then
    STORAGE_TYPE="nvme"
elif lsblk -d -o NAME,TYPE,RM 2>/dev/null | awk 'NR>1 && $2=="disk" && $3=="0" {print "ssd"; exit}' | grep -q ssd; then
    STORAGE_TYPE="ssd"
fi
log "Storage: $STORAGE_TYPE"

# ─── Detect RAM ──────────────────────────────────────────────────────
RAM_GB=4
if [ -f /proc/meminfo ]; then
    RAM_KB=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
    RAM_GB=$(( RAM_KB / 1048576 ))
fi
log "RAM: ${RAM_GB}GB"

# ─── Apply ZRAM (all systems) ─────────────────────────────────────────
log "Configuring ZRAM (zstd, ${RAM_GB}GB system)..."
mkdir -p /etc/systemd/zram-generator.conf.d
cat > /etc/systemd/zram-generator.conf.d/synthex-zram.conf << EOZRAM
[zram0]
zram-fraction = 0.5
compression-algorithm = zstd
mount-options = noatime
EOZRAM

# ─── Apply CPU scheduler (BORE/EEVDF) ─────────────────────────────────
log "Configuring CPU scheduler (BORE + EEVDF)..."
mkdir -p /etc/sysctl.d
cat > /etc/sysctl.d/99-synthex-scheduler.conf << EOSCHED
# Synthex gaming-optimized scheduler
kernel.sched_min_granularity_ns = 10000000
kernel.sched_wakeup_granularity_ns = 15000000
kernel.sched_migration_cost_ns = 5000000
kernel.sched_rt_runtime_us = 995000
kernel.sched_rt_period_us = 1000000
EOSCHED

# ─── Apply memory tuning ──────────────────────────────────────────────
cat > /etc/sysctl.d/99-synthex-memory.conf << EOMEM
# Desktop / gaming memory tuning
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_ratio = 10
vm.dirty_background_ratio = 3
vm.laptop_mode = 0
vm.page-cluster = 0
vm.compact_memory = 1
EOMEM

# ─── Storage tuning ───────────────────────────────────────────────────
log "Applying $STORAGE_TYPE storage tuning..."
if [ "$STORAGE_TYPE" = "nvme" ] || [ "$STORAGE_TYPE" = "ssd" ]; then
    cat > /etc/udev/rules.d/60-synthex-ssd.rules << EOSSD
KERNEL=="sd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
KERNEL=="nvme[0-9]*", ATTR{queue/scheduler}="none"
KERNEL=="vd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="mq-deadline"
EOSSD
    cat > /etc/sysctl.d/99-synthex-io.conf << EOIO
# SSD / NVMe tuning
vm.dirty_ratio = 5
vm.dirty_background_ratio = 2
vm.swappiness = 5
EOIO
fi

# ─── Gaming defaults ──────────────────────────────────────────────────
log "Applying gaming optimizations..."
mkdir -p /etc/environment.d
cat > /etc/environment.d/99-synthex-gaming.conf << EOGAMING
# Synthex gaming stack defaults
DXVK_ASYNC=1
DXVK_STATE_CACHE=1
MANGOHUD=1
GAMEMODE_AUTO=1
EOGAMING

# ─── PipeWire audio tuning ────────────────────────────────────────────
mkdir -p /etc/pipewire/pipewire.conf.d
cat > /etc/pipewire/pipewire.conf.d/99-synthex-audio.conf << EOAUDIO
# Synthex audio tuning (low latency + gaming + Hi-Res)
context.properties = {
    default.clock.rate = 48000
    default.clock.allowed-rates = [ 44100 48000 88200 96000 176400 192000 ]
    default.clock.quantum = 256
    default.clock.min-quantum = 64
    default.clock.max-quantum = 8192
}
EOAUDIO

# ─── systemd-resolved + DNSSEC ────────────────────────────────────────
log "Configuring systemd-resolved + DNSSEC..."
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/synthex.conf << EORESOLVED
[Resolve]
# Fast + secure DNS (Cloudflare + Quad9 fallbacks)
DNS=1.1.1.1 9.9.9.9
FallbackDNS=1.0.0.1 149.112.112.112
DNSSEC=true
Cache=yes
CacheFromLocalhost=yes
EORESOLVED

# ─── Laptop-specific ──────────────────────────────────────────────────
if [ "$CHASSIS" = "laptop" ]; then
    log "Applying laptop optimizations..."
    systemctl enable --now power-profiles-daemon 2>/dev/null || true
    # Undervolt hint (Intel only)
    if [ "$GPU_VENDOR" = "intel" ]; then
        cat > /etc/udev/rules.d/99-synthex-throttle.rules << EOTHROTTLE
# Intel thermal trip point adjustments for laptops
SUBSYSTEM=="thermal", ATTR{thermal_zone*/trip_point_0_temp}="95000"
EOTHROTTLE
    fi
fi

# ─── Handheld-specific ────────────────────────────────────────────────
if [ "$CHASSIS" = "handheld" ]; then
    log "Applying handheld optimizations..."
    cat > /etc/environment.d/99-synthex-handheld.conf << EOHANDHELD
STEAM_DISABLE_VR_LAYER=1
STEAM_GAME_INPUT=1
MANGOHUD=1
EOHANDHELD
fi

# ─── NVIDIA-specific (if detected) ───────────────────────────────────
if [ "$GPU_VENDOR" = "nvidia" ]; then
    log "Applying NVIDIA optimizations..."
    cat > /etc/modprobe.d/nvidia-synthex.conf << EONVIDIA
options nvidia NVreg_UsePageAttributeTable=1
options nvidia NVreg_TemporaryFilePath=/var/tmp
options nvidia NVreg_PreserveVideoMemoryAllocations=1
options nvidia_drm modeset=1
EONVIDIA
    cat > /etc/environment.d/99-synthex-nvidia.conf << EONVENV
__GL_SHADER_DISK_CACHE=1
__GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1
__GL_YIELD=usleep
EONVENV
fi

# ─── AMD-specific ─────────────────────────────────────────────────────
if [ "$GPU_VENDOR" = "amd" ]; then
    log "Applying AMD optimizations..."
    cat > /etc/environment.d/99-synthex-amd.conf << EOAMD
RADV_PERFTEST=aco
AMD_DEBUG=zeroets
EOAMD
fi

# ─── High-RAM tuning ──────────────────────────────────────────────────
if [ "$RAM_GB" -ge 16 ]; then
    log "Applying 16GB+ RAM tuning..."
    sed -i 's/^vm.swappiness = .*/vm.swappiness = 5/' /etc/sysctl.d/99-synthex-memory.conf 2>/dev/null || true
fi

# ─── Record state ─────────────────────────────────────────────────────
cat > "$STATE_FILE" << EOSTATE
{
    "version": 1,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "gpu": "$GPU_VENDOR",
    "chassis": "$CHASSIS",
    "storage": "$STORAGE_TYPE",
    "ram_gb": $RAM_GB,
    "tuned": true
}
EOSTATE

log "=== Auto-Tuning Complete ==="
