#!/usr/bin/env bash
#===============================================================================
# Synthex GPU Setup — AMD Driver Installer
#===============================================================================
# Installs and configures AMD GPU drivers on SynthOS.
#
# Packages:
#   - Mesa DRI drivers (radeonsi for GCN+, amdgpu for newer)
#   - Mesa Vulkan drivers (RADV)
#   - Mesa OpenGL libraries
#   - AMD GPU firmware
#   - ROCm (optional): rocm-opencl, rocm-hip
#
# Usage:
#   sudo ./install-amd.sh           Interactive install
#   sudo ./install-amd.sh --yes     Non-interactive install
#   sudo ./install-amd.sh --rocm    Include ROCm stack
#   sudo ./install-amd.sh --check   Only check compatibility
#===============================================================================

set -euo pipefail

# --- Constants ---------------------------------------------------------------
readonly SELF="install-amd.sh"
readonly LOG_FILE="/var/log/synthex-gpu-setup-amd.log"
readonly SNAPSHOT_PREFIX="amd-install-"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $*" | tee -a "${LOG_FILE}"; }
warn()  { echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "${LOG_FILE}"; }
error() { echo -e "${RED}[ERROR]${NC} $*" | tee -a "${LOG_FILE}" >&2; }
die()   { error "$*"; exit 1; }

# --- Preamble ----------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    die "This script must be run as root. Use: sudo ./${SELF}"
fi

touch "${LOG_FILE}" 2>/dev/null || true
log "=== Synthex AMD GPU Setup ==="
log "Starting at $(date)"

# --- Parse Arguments ---------------------------------------------------------
CHECK_ONLY=false
NON_INTERACTIVE=false
INSTALL_ROCM=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check|-c)      CHECK_ONLY=true; shift ;;
        --yes|-y)        NON_INTERACTIVE=true; shift ;;
        --rocm)          INSTALL_ROCM=true; shift ;;
        --help|-h)
            echo "Usage: sudo ./${SELF} [options]"
            echo "  --check, -c       Check compatibility only"
            echo "  --yes, -y         Non-interactive mode"
            echo "  --rocm            Also install ROCm stack (OpenCL + HIP)"
            echo "  --help, -h        Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# --- Functions ---------------------------------------------------------------

detect_amd_gpu() {
    local gpu_info
    gpu_info="$(lspci -nn | grep -i 'vga.*amd\|3d.*amd\|vga.*ati\|3d.*ati\|vga.*advanced micro' | head -1 | sed 's/.*: //')"
    echo "${gpu_info:-Unknown AMD GPU}"
}

check_btrfs() {
    [[ "$(findmnt -n -o FSTYPE / 2>/dev/null)" == "btrfs" ]]
}

create_snapshot() {
    local label="${SNAPSHOT_PREFIX}$(date +%Y%m%d%H%M%S)"
    if check_btrfs && command -v snapper &>/dev/null; then
        snapper -c root create -d "${label}" && log "Snapshot '${label}' created." || warn "Snapshot creation failed."
    else
        log "BTRFS snapshot not available; continuing."
    fi
}

install_amd_base() {
    log "Installing AMD GPU base drivers..."

    dnf install -y \
        mesa-dri-drivers \
        mesa-vulkan-drivers \
        mesa-libGL \
        mesa-va-drivers \
        mesa-vdpau-drivers \
        libva \
        libva-utils \
        libdrm \
        libdrm-amdgpu \
        linux-firmware-amd \
        2>&1 | tee -a "${LOG_FILE}"

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        die "Base package installation failed."
    fi
    log "AMD base drivers installed."

    # Install ROCm if requested
    if [[ "${INSTALL_ROCM}" == "true" ]]; then
        log "Installing ROCm stack..."
        dnf install -y \
            rocm-opencl \
            rocm-hip \
            rocm-smi \
            rocm-device-libs \
            rocm-comgr \
            2>&1 | tee -a "${LOG_FILE}" || warn "ROCm installation had issues (check log)."

        if command -v rocm-smi &>/dev/null; then
            log "✓ ROCm-SMI available."
        fi
    fi
}

configure_amd_gpu() {
    log "Configuring AMD GPU settings..."

    # Ensure amdgpu kernel module is loaded
    if ! lsmod | grep -q amdgpu; then
        modprobe amdgpu 2>/dev/null || warn "Could not load amdgpu module (will load on boot)."
    fi

    # Create modprobe config for AMD
    local amd_conf="/etc/modprobe.d/amdgpu.conf"
    cat > "${amd_conf}" <<'CONF'
# AMD GPU configuration — installed by Synthex GPU Setup
# Enable amdgpu driver (default for GCN+)
options amdgpu si_support=1
options amdgpu cik_support=1
# Enable GPU scheduling
options amdgpu gpu_sched=1
# Enable compute (ROCm)
options amdgpu ppfeaturemask=0xffffffff
CONF
    log "Created ${amd_conf}"
}

verify_vulkan() {
    log "Verifying Vulkan support..."
    if command -v vulkaninfo &>/dev/null; then
        vulkaninfo --summary 2>/dev/null | grep -i 'radv\|amd' | head -5 | tee -a "${LOG_FILE}" || true
        vulkaninfo --summary 2>/dev/null | grep -q 'RADV' && log "✓ RADV Vulkan driver detected." || warn "RADV not detected."
    elif command -v vulkaninfo &>/dev/null; then
        # For systems that have vulkaninfo from vulkan-tools
        if vulkaninfo 2>/dev/null | grep -qi 'radv'; then
            log "✓ RADV Vulkan driver detected."
        else
            warn "RADV not detected. Check Mesa Vulkan drivers."
        fi
    else
        warn "vulkaninfo not installed (install vulkan-tools for verification)."
    fi
}

verify_vaapi() {
    log "Verifying VA-API support..."
    if command -v vainfo &>/dev/null; then
        vainfo 2>/dev/null | grep -i 'amd\|radeon' | head -5 | tee -a "${LOG_FILE}" || true
    else
        warn "vainfo not installed (install libva-utils for verification)."
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}✓ AMD GPU setup complete.${NC}"
    echo "  GPU: $(detect_amd_gpu)"
    echo "  Mesa: $(dnf list installed mesa-dri-drivers 2>/dev/null | tail -1 | awk '{print $2}')"
    echo "  RADV: $(vulkaninfo --summary 2>/dev/null | grep driverInfo | head -1 || echo 'check with vulkaninfo')"
    if [[ "${INSTALL_ROCM}" == "true" ]]; then
        echo "  ROCm: installed"
    fi
    echo "  A system reboot may be required."
}

# --- Main --------------------------------------------------------------------

GPU_NAME="$(detect_amd_gpu)"
log "Detected GPU: ${GPU_NAME}"

if [[ -z "${GPU_NAME}" || "${GPU_NAME}" == "Unknown AMD GPU" ]]; then
    warn "No AMD GPU detected. Proceeding anyway (may have integrated AMD graphics)."
fi

if [[ "${CHECK_ONLY}" == "true" ]]; then
    echo "GPU:         ${GPU_NAME}"
    echo "Kernel:      $(uname -r)"
    echo "Mesa:        $(dnf list installed mesa-dri-drivers 2>/dev/null | tail -1 | awk '{print $2}' || echo 'not installed')"
    echo "RADV:        $(command -v vulkaninfo &>/dev/null && vulkaninfo --summary 2>/dev/null | grep driverInfo | head -1 | cut -d= -f2 || echo 'check with vulkaninfo')"
    echo "BTRFS:       $(check_btrfs && echo 'yes' || echo 'no')"
    exit 0
fi

# Confirm
if [[ "${NON_INTERACTIVE}" != "true" ]]; then
    echo ""
    echo -e "${BOLD}AMD Driver Installation${NC}"
    echo "  GPU:             ${GPU_NAME}"
    echo "  Mesa + Vulkan:   Yes (RADV)"
    echo "  ROCm:            ${INSTALL_ROCM}"
    echo "  BTRFS snapshot:  $(check_btrfs && echo 'Yes' || echo 'Not available')"
    echo ""
    echo -n "Proceed? [Y/n]: "
    read -r answer
    case "${answer}" in
        n|N|no) die "Cancelled." ;;
        *) ;;
    esac
fi

create_snapshot
install_amd_base
configure_amd_gpu
verify_vulkan
verify_vaapi
print_summary

log "=== AMD GPU Setup Complete ==="
exit 0
