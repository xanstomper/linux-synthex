#!/bin/bash
# Solus First Boot — Enhanced with timeout/retry and hardware detection
# Part of solus-firstboot.service

set -euo pipefail

STATE_DIR="/var/lib/solus"
FIRSTBOOT_FLAG="${STATE_DIR}/firstboot-complete"
LOG_FILE="/var/log/solus-firstboot.log"
MAX_RETRIES=3
RETRY_DELAY=5

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# Timeout wrapper — kills command if it takes too long
run_with_timeout() {
    local timeout=$1
    local cmd=$2
    shift 2
    
    timeout "$timeout" "$cmd" "$@" 2>/dev/null || {
        log "⚠ Command timed out after ${timeout}s: $cmd"
        return 1
    }
}

retry() {
    local n=0
    local cmd="$@"
    until $cmd; do
        n=$((n+1))
        if [ "$n" -ge "$MAX_RETRIES" ]; then
            log "⚠ Failed after $MAX_RETRIES attempts: $cmd"
            return 1
        fi
        log "Retrying ($n/$MAX_RETRIES)..."
        sleep "$RETRY_DELAY"
    done
}

is_live_mode() { [ -f "/run/solus-live-mode" ]; }

is_first_boot() { [ ! -f "$FIRSTBOOT_FLAG" ]; }

mark_complete() {
    mkdir -p "$STATE_DIR"
    date > "$FIRSTBOOT_FLAG"
    log "✅ First boot setup complete"
}

do_hardware_detection() {
    log "🔍 Detecting hardware..."
    
    # CPU
    if [ -f /proc/cpuinfo ]; then
        CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^ //' || echo "Unknown")
        CPU_CORES=$(nproc 2>/dev/null || echo "?")
        log "  CPU: $CPU_MODEL ($CPU_CORES cores)"
    fi
    
    # RAM
    if [ -f /proc/meminfo ]; then
        MEM_TOTAL=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2/1024/1024" GB"}' || echo "?")
        log "  RAM: $MEM_TOTAL"
    fi
    
    # GPU — try multiple methods
    GPU_INFO=""
    if command -v lspci &>/dev/null; then
        GPU_INFO=$(lspci 2>/dev/null | grep -i "vga\|3d\|display" | head -1 | cut -d: -f3 | sed 's/^ //' || true)
    fi
    if [ -z "$GPU_INFO" ] && [ -d /sys/class/drm ]; then
        for card in /sys/class/drm/card*; do
            if [ -f "$card/device/vendor" ]; then
                VENDOR=$(cat "$card/device/vendor" 2>/dev/null || true)
                case "$VENDOR" in
                    "0x10de") GPU_INFO="NVIDIA GPU";;
                    "0x1002") GPU_INFO="AMD GPU";;
                    "0x8086") GPU_INFO="Intel GPU";;
                esac
                [ -n "$GPU_INFO" ] && break
            fi
        done
    fi
    log "  GPU: ${GPU_INFO:-Unknown}"
    
    # Storage
    if command -v lsblk &>/dev/null; then
        DISKS=$(lsblk -dno NAME,SIZE 2>/dev/null | grep -v loop | head -3 | tr '\n' ' ')
        log "  Storage: $DISKS"
    fi
    
    # WiFi
    if command -v iw &>/dev/null && iw dev 2>/dev/null | grep -q "Interface"; then
        log "  WiFi: Detected"
    fi
    
    # Bluetooth
    if command -v bluetoothctl &>/dev/null; then
        log "  Bluetooth: checking..."
    fi
    
    # Save hardware profile
    mkdir -p /var/lib/solus
    {
        echo "CPU=$CPU_MODEL"
        echo "CORES=$CPU_CORES"
        echo "RAM=$MEM_TOTAL"
        echo "GPU=$GPU_INFO"
        echo "DATE=$(date -I)"
    } > /var/lib/solus/hardware-profile 2>/dev/null || true
}

do_driver_setup() {
    # Try GPU driver setup (non-fatal if it fails)
    if [ -x /usr/bin/solus-gpu-setupd ]; then
        log "🔧 Setting up GPU drivers..."
        run_with_timeout 60 /usr/bin/solus-gpu-setupd --auto || log "⚠ GPU setup deferred"
    fi
    
    # WiFi setup
    if [ -x /usr/share/solus/scripts/wifi-setup.sh ]; then
        log "📡 Configuring WiFi..."
        run_with_timeout 30 /usr/share/solus/scripts/wifi-setup.sh || true
    fi

    # Flatpak / Flathub setup
    if [ -x /usr/libexec/solus/setup-flatpak.sh ]; then
        log "📦 Enabling Flathub..."
        run_with_timeout 30 /usr/libexec/solus/setup-flatpak.sh || true
    fi
}

do_selinux_relabel() {
    log "🔒 Relabeling SELinux contexts..."
    if command -v restorecon &>/dev/null; then
        run_with_timeout 120 restorecon -Rv /etc /usr /var /opt 2>/dev/null || log "⚠ SELinux relabel incomplete"
    fi
}

do_system_tuning() {
    log "⚙ Applying system tuning..."
    
    # Apply sysctl
    if [ -d /etc/sysctl.d ]; then
        sysctl --system 2>/dev/null || true
    fi
    
    # CPU governor (safe default)
    if command -v cpupower &>/dev/null; then
        cpupower frequency-set -g schedutil 2>/dev/null || cpupower frequency-set -g ondemand 2>/dev/null || true
    fi
    
    # Set tuned profile if available
    if command -v tuned-adm &>/dev/null; then
        tuned-adm profile desktop 2>/dev/null || true
    fi
}

do_snapshot_initial() {
    log "📸 Creating initial system snapshot..."
    if command -v snapper &>/dev/null; then
        snapper -c root create -d "fresh-install" 2>/dev/null || log "⚠ Snapshot creation skipped"
    fi
}

main() {
    log "═══════════════════════════════════"
    log "  ☀️ Solus First Boot Setup"
    log "═══════════════════════════════════"
    
    if is_live_mode; then
        log "Live mode — skipping first boot setup"
        exit 0
    fi
    
    if ! is_first_boot; then
        log "First boot already completed $(cat "$FIRSTBOOT_FLAG" 2>/dev/null || true)"
        exit 0
    fi
    
    # Run each step with retry support, non-fatal failures
    retry do_hardware_detection || true
    do_driver_setup || true
    retry do_selinux_relabel || true
    do_system_tuning || true
    do_snapshot_initial || true
    
    mark_complete
    
    log "═══════════════════════════════════"
    log "  🎉 Solus is ready!"
    log "═══════════════════════════════════"
}

main "$@"
