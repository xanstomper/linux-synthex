#!/usr/bin/env bash
# synthex-gpu-setupd — GPU Auto-Detection and Driver Setup
# Detects GPU hardware and installs appropriate drivers
# Runs during first boot and on hardware changes

set -euo pipefail

VERSION="1.0.0"
LOG_FILE="/var/log/synthex-gpu-setup.log"
STATE_FILE="/var/lib/synthex/gpu-state.json"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

detect_nvidia() {
    if lspci -nn | grep -qi "10de" 2>/dev/null; then
        log "NVIDIA GPU detected"
        return 0
    fi
    return 1
}

detect_amd() {
    if lspci -nn | grep -qi "1002" 2>/dev/null; then
        log "AMD GPU detected"
        return 0
    fi
    return 1
}

detect_intel() {
    if lspci -nn | grep -qi "8086.*VGA" 2>/dev/null; then
        log "Intel GPU detected"
        return 0
    fi
    return 1
}

check_nvidia_compatibility() {
    # Check kernel version compatibility
    kernel_ver=$(uname -r | cut -d- -f1)
    log "Kernel version: $kernel_ver"
    
    # Check secure boot status
    if [ -f /sys/kernel/security/lockdown ]; then
        lockdown=$(cat /sys/kernel/security/lockdown)
        log "Kernel lockdown: $lockdown"
    fi
    
    # Check if secure boot is enabled
    if mokutil --sb-state 2>/dev/null | grep -q "enabled"; then
        log "⚠ Secure Boot enabled — NVIDIA driver may need MOK signing"
        return 1
    fi
    
    return 0
}

check_wayland_compatibility() {
    if detect_nvidia; then
        # Check if NVIDIA driver supports Wayland
        nvidia_ver=$(modinfo nvidia 2>/dev/null | grep "^version:" | awk '{print $2}')
        if [ -n "$nvidia_ver" ]; then
            log "NVIDIA driver version: $nvidia_ver"
            # Wayland support added in 525+
            if [[ "$nvidia_ver" =~ ^([0-9]+) ]]; then
                major="${BASH_REMATCH[1]}"
                if [ "$major" -ge 525 ]; then
                    log "✅ NVIDIA driver supports Wayland"
                    return 0
                fi
            fi
        fi
        log "⚠ NVIDIA Wayland support uncertain — using XWayland fallback"
        return 1
    fi
    return 0
}

install_nvidia() {
    log "Installing NVIDIA proprietary drivers..."
    
    # Pre-install snapshot
    snapper -c root create -d "pre-nvidia-driver" 2>/dev/null || true
    
    # Install driver
    dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda 2>&1 | tee -a "$LOG_FILE"
    
    # Configure NVIDIA
    cat > /etc/modprobe.d/nvidia-synthex.conf << 'EOF'
options nvidia NVreg_PreserveVideoMemoryAllocations=1
options nvidia NVreg_EnableGpuFirmware=0
options nvidia-drm modeset=1
EOF
    
    # Enable persistence daemon
    systemctl enable nvidia-persistenced 2>/dev/null || true
    
    # Regenerate initramfs
    dracut --force
    
    # Post-install snapshot
    snapper -c root create -d "post-nvidia-driver" 2>/dev/null || true
    
    log "✅ NVIDIA drivers installed successfully"
}

install_amd() {
    log "Installing AMD drivers..."
    
    # Pre-install snapshot
    snapper -c root create -d "pre-amd-driver" 2>/dev/null || true
    
    # AMD drivers are mostly in the kernel and Mesa
    dnf install -y mesa-dri-drivers mesa-vulkan-drivers mesa-libGL \
        amd-gpu-firmware mesa-va-drivers 2>&1 | tee -a "$LOG_FILE"
    
    # ROCm for compute (optional)
    dnf install -y rocm-opencl rocm-hip 2>/dev/null || log "ROCm not available in repo"
    
    # Post-install snapshot
    snapper -c root create -d "post-amd-driver" 2>/dev/null || true
    
    log "✅ AMD drivers installed successfully"
}

install_intel() {
    log "Setting up Intel graphics..."
    
    snapper -c root create -d "pre-intel-driver" 2>/dev/null || true
    
    dnf install -y mesa-dri-drivers mesa-vulkan-drivers \
        intel-media-driver 2>&1 | tee -a "$LOG_FILE"
    
    snapper -c root create -d "post-intel-driver" 2>/dev/null || true
    
    log "✅ Intel graphics configured"
}

install_fallback() {
    log "⚠ Unknown GPU — installing Mesa fallback (llvmpipe)"
    dnf install -y mesa-dri-drivers 2>&1 | tee -a "$LOG_FILE"
    log "⚠ System will use software rendering until GPU is recognized"
}

save_state() {
    mkdir -p "$(dirname "$STATE_FILE")"
    cat > "$STATE_FILE" << EOF
{
    "gpu_detected": "$1",
    "driver_installed": "$2",
    "wayland_supported": $3,
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "version": "$VERSION"
}
EOF
}

main() {
    log "═══════════════════════════════════"
    log "  Synthex GPU Setup Daemon v$VERSION"
    log "═══════════════════════════════════"
    
    # Detect GPU
    if detect_nvidia; then
        log "GPU Vendor: NVIDIA"
        if check_nvidia_compatibility; then
            install_nvidia
            save_state "nvidia" "nvidia-proprietary" true
        else
            log "⚠ NVIDIA conditions not optimal — deferring driver install"
            log "⚠ Using Mesa fallback for now"
            install_fallback
            save_state "nvidia" "deferred" false
        fi
    elif detect_amd; then
        log "GPU Vendor: AMD"
        install_amd
        save_state "amd" "mesa-radv" true
    elif detect_intel; then
        log "GPU Vendor: Intel"
        install_intel
        save_state "intel" "mesa-anv" true
    else
        log "⚠ No known GPU detected"
        install_fallback
        save_state "unknown" "mesa-llvmpipe" true
    fi
    
    log "═══════════════════════════════════"
    log "  GPU Setup Complete"
    log "═══════════════════════════════════"
}

main "$@"
