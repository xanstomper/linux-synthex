#!/usr/bin/env bash
#===============================================================================
# Synthex GPU Setup — NVIDIA Driver Installer
#===============================================================================
# Installs and configures NVIDIA proprietary drivers on SynthOS.
#
# Steps:
#   1. Detect GPU model via nvidia-smi or lspci
#   2. Check kernel version compatibility
#   3. Create BTRFS snapshot before installation
#   4. Install akmod-nvidia + CUDA packages via dnf
#   5. Configure nvidia.conf with optimal settings
#   6. Enable nvidia-persistenced
#   7. Rebuild initramfs with dracut
#   8. Verify driver loaded
#   9. Rollback instructions if installation fails
#
# Usage:
#   sudo ./install-nvidia.sh          Interactive install
#   sudo ./install-nvidia.sh --yes    Non-interactive install
#   sudo ./install-nvidia.sh --check  Only check compatibility
#   sudo ./install-nvidia.sh --rollback  Restore last snapshot
#===============================================================================

set -euo pipefail

# --- Constants ---------------------------------------------------------------
readonly SELF="install-nvidia.sh"
readonly LOG_FILE="/var/log/synthex-gpu-setup-nvidia.log"
readonly SNAPSHOT_PREFIX="nvidia-install-"
readonly NVIDIA_CONF="/etc/modprobe.d/nvidia.conf"
readonly PERSISTENCED_SERVICE="nvidia-persistenced"

# Print helpers
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()    { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*" | tee -a "${LOG_FILE}"; }
warn()   { echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE}"; }
error()  { echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}" >&2; }
die()    { error "$*"; exit 1; }

# --- Preamble ----------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Use: sudo ./${SELF}"
fi

# Set up logging
touch "${LOG_FILE}" 2>/dev/null || true
chmod 644 "${LOG_FILE}" 2>/dev/null || true

log "=== Synthex NVIDIA GPU Setup ==="
log "Starting installation at $(date)"

# --- Parse Arguments ---------------------------------------------------------
CHECK_ONLY=false
NON_INTERACTIVE=false
DO_ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check|-c)    CHECK_ONLY=true; shift ;;
        --yes|-y)      NON_INTERACTIVE=true; shift ;;
        --rollback|-r) DO_ROLLBACK=true; shift ;;
        --help|-h)
            echo "Usage: sudo ./${SELF} [options]"
            echo "  --check, -c       Only check compatibility, don't install"
            echo "  --yes, -y         Non-interactive mode"
            echo "  --rollback, -r    Rollback to last pre-install snapshot"
            echo "  --help, -h        Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# --- Functions ---------------------------------------------------------------

detect_nvidia_gpu() {
    local gpu_info=""
    # nvidia-smi gives the most reliable info
    if command -v nvidia-smi &>/dev/null; then
        gpu_info="$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null | head -1)"
    fi
    if [[ -z "${gpu_info}" ]]; then
        # Fallback to lspci
        gpu_info="$(lspci -nn | grep -i 'vga.*nvidia\|3d.*nvidia' | head -1 | sed 's/.*: //')"
    fi
    echo "${gpu_info:-Unknown NVIDIA GPU}"
}

check_kernel_compat() {
    local kernel_ver
    kernel_ver="$(uname -r)"
    log "Kernel version: ${kernel_ver}"

    # Check if akmod-nvidia is available for this kernel
    if command -v dnf &>/dev/null; then
        if dnf list available akmod-nvidia &>/dev/null 2>&1; then
            log "akmod-nvidia is available in repositories."
            return 0
        fi
    fi

    warn "Cannot verify akmod-nvidia availability. Proceeding anyway."
    return 0
}

check_btrfs() {
    local fstype
    fstype="$(findmnt -n -o FSTYPE / 2>/dev/null || echo 'unknown')"
    [[ "${fstype}" == "btrfs" ]]
}

create_snapshot() {
    local label="${SNAPSHOT_PREFIX}$(date +%Y%m%d%H%M%S)"
    log "Creating BTRFS snapshot: ${label}..."

    if check_btrfs; then
        if command -v snapper &>/dev/null; then
            snapper -c root create -d "${label}" && log "Snapshot '${label}' created via snapper." && return 0
        fi
        # Fallback: direct btrfs subvolume snapshot
        if [[ -d /.snapshots ]]; then
            btrfs subvolume snapshot / "/.snapshots/${label}" 2>/dev/null && log "Snapshot created at /.snapshots/${label}" && return 0
        fi
        warn "Could not create automatic snapshot. Continuing without snapshot."
    else
        log "Not on BTRFS filesystem; skipping snapshot."
    fi
    return 0
}

rollback_snapshot() {
    log "=== Rollback ==="
    # Find the last snapshot created by this script
    local snaps=()
    if command -v snapper &>/dev/null; then
        while IFS= read -r line; do
            snaps+=("${line}")
        done < <(snapper -c root list --output=number,description 2>/dev/null | grep "${SNAPSHOT_PREFIX}" || true)
    fi

    if [[ ${#snaps[@]} -eq 0 ]]; then
        warn "No snapshots found with prefix '${SNAPSHOT_PREFIX}'."
        echo "Manual rollback instructions:"
        echo "  1. Reboot and select a previous kernel from GRUB"
        echo "  2. Run: dnf remove akmod-nvidia xorg-x11-drv-nvidia-cuda"
        echo "  3. Run: dracut --force"
        return 1
    fi

    echo "Available snapshots:"
    for i in "${!snaps[@]}"; do
        echo "  $((i+1)). ${snaps[$i]}"
    done

    if [[ "${NON_INTERACTIVE}" != "true" ]]; then
        echo -n "Select snapshot to rollback to (1-${#snaps[@]}): "
        read -r selection
        local idx=$((selection - 1))
        [[ idx -ge 0 && idx -lt ${#snaps[@]} ]] || die "Invalid selection"
        local snap_num
        snap_num="$(echo "${snaps[$idx]}" | awk '{print $1}')"
        snapper -c root undochange "${snap_num}..0" && log "Rollback to snapshot ${snap_num} complete." && return 0
    fi
    return 1
}

install_nvidia_drivers() {
    log "Starting NVIDIA driver installation..."

    # Install prerequisite packages
    log "Installing NVIDIA driver packages..."
    dnf install -y \
        akmod-nvidia \
        xorg-x11-drv-nvidia-cuda \
        xorg-x11-drv-nvidia-power \
        nvidia-persistenced \
        2>&1 | tee -a "${LOG_FILE}"

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        die "Package installation failed. See ${LOG_FILE} for details."
    fi
    log "NVIDIA packages installed successfully."
}

configure_nvidia() {
    log "Configuring NVIDIA settings..."

    # Create modprobe config
    cat > "${NVIDIA_CONF}" <<'CONF'
# NVIDIA driver configuration — installed by Synthex GPU Setup
# Preserve video memory allocations across suspend/resume
options nvidia NVreg_PreserveVideoMemoryAllocations=1
# Enable runtime power management
options nvidia NVreg_DynamicPowerManagement=0x02
# Disable modeset for legacy compatibility where needed
# options nvidia-drm modeset=1
CONF
    log "Created ${NVIDIA_CONF}"

    # Enable and start nvidia-persistenced
    if systemctl enable "${PERSISTENCED_SERVICE}" 2>/dev/null; then
        systemctl start "${PERSISTENCED_SERVICE}" 2>/dev/null || warn "Could not start nvidia-persistenced (will start on boot)"
        log "Enabled ${PERSISTENCED_SERVICE}"
    else
        warn "Could not enable nvidia-persistenced"
    fi
}

rebuild_initramfs() {
    log "Rebuilding initramfs..."
    dracut --force
    log "Initramfs rebuilt."
}

verify_driver() {
    log "Verifying NVIDIA driver..."
    sleep 2

    # Check if nvidia module is loaded
    if lsmod | grep -q nvidia; then
        log "✓ nvidia kernel module loaded."
    else
        warn "nvidia module not loaded yet (expected — may need reboot)."
    fi

    # Try nvidia-smi
    if command -v nvidia-smi &>/dev/null; then
        local smi_output
        smi_output="$(nvidia-smi --query-gpu=name,driver_version,pci.link.gen.current --format=csv,noheader 2>/dev/null || nvidia-smi 2>/dev/null | head -5 || true)"
        if [[ -n "${smi_output}" ]]; then
            log "✓ nvidia-smi detected:"
            echo "${smi_output}" | tee -a "${LOG_FILE}"
        else
            warn "nvidia-smi available but no output. May need reboot."
        fi
    fi

    # Check driver version
    if [[ -f /proc/driver/nvidia/version ]]; then
        cat /proc/driver/nvidia/version | tee -a "${LOG_FILE}"
    fi
}

print_rollback_instructions() {
    echo ""
    echo -e "${YELLOW}=== If something went wrong ===${NC}"
    echo "  1. Reboot and select 'Advanced options for SynthOS' in GRUB"
    echo "     then choose the previous kernel."
    echo "  2. Once booted, run:"
    echo "     sudo dnf remove akmod-nvidia xorg-x11-drv-nvidia-cuda"
    echo "  3. Rebuild initramfs: sudo dracut --force"
    echo "  4. Reboot normally."
    echo ""
    if check_btrfs && command -v snapper &>/dev/null; then
        echo "  To rollback via snapper:"
        echo "    sudo snapper -c root list | grep ${SNAPSHOT_PREFIX}"
        echo "    sudo snapper -c root undochange <number>..0"
        echo "    sudo reboot"
    fi
}

# --- Main --------------------------------------------------------------------

GPU_NAME="$(detect_nvidia_gpu)"
log "Detected GPU: ${GPU_NAME}"

if [[ "${DO_ROLLBACK}" == "true" ]]; then
    rollback_snapshot
    exit $?
fi

check_kernel_compat

if [[ "${CHECK_ONLY}" == "true" ]]; then
    log "Compatibility check passed."
    echo ""
    echo "GPU:         ${GPU_NAME}"
    echo "Kernel:      $(uname -r)"
    echo "Drivers:     $(dnf list installed akmod-nvidia 2>/dev/null | tail -1 || echo 'not installed')"
    echo "BTRFS:       $(check_btrfs && echo 'yes' || echo 'no')"
    exit 0
fi

# Confirm with user
if [[ "${NON_INTERACTIVE}" != "true" ]]; then
    echo ""
    echo -e "${BOLD}NVIDIA Driver Installation${NC}"
    echo "  GPU detected:          ${GPU_NAME}"
    echo "  Kernel:                $(uname -r)"
    echo "  Packages to install:   akmod-nvidia, xorg-x11-drv-nvidia-cuda, nvidia-persistenced"
    echo "  BTRFS snapshot:        $(check_btrfs && echo 'Yes (automatic)' || echo 'Not available')"
    echo "  Target config:         ${NVIDIA_CONF}"
    echo ""
    echo -n "Proceed with installation? [Y/n]: "
    read -r answer
    case "${answer}" in
        n|N|no|NO) die "Installation cancelled by user." ;;
        *) ;;
    esac
fi

# Create snapshot
create_snapshot

# Install
install_nvidia_drivers

# Configure
configure_nvidia

# Rebuild initramfs
rebuild_initramfs

# Verify
verify_driver

# Print rollback instructions
print_rollback_instructions

log "=== NVIDIA GPU Setup Complete ==="
echo ""
echo -e "${GREEN}✓ NVIDIA driver installation complete.${NC}"
echo "  GPU: ${GPU_NAME}"
echo "  A system reboot is recommended to load the new driver."
echo "  After reboot, verify with: nvidia-smi"
exit 0