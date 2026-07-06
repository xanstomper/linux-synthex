#!/usr/bin/env bash
#===============================================================================
# Solus GPU Setup — Intel GPU Driver Installer
#===============================================================================
# Ensures Intel GPU drivers are installed and configured.
# Intel graphics are already supported in the kernel; this script ensures
# Mesa, Vulkan (ANV), and VA-API media drivers are present.
#
# Packages:
#   - mesa-dri-drivers (iris for Gen8+, crocus for older)
#   - mesa-vulkan-drivers (ANV)
#   - intel-media-driver (VA-API hardware encoding/decoding)
#   - libva-intel-driver (legacy VA-API for older gen)
#
# Usage:
#   sudo bash install-intel.sh

set -euo pipefail

echo "🎨 Solus Intel GPU Driver Setup"
echo "════════════════════════════════"

# Pre-install snapshot
echo "📸 Creating pre-install snapshot..."
snapper -c root create -d "pre-intel-driver" 2>/dev/null || true

# --- Constants ---------------------------------------------------------------
readonly SELF="install-intel.sh"
readonly LOG_FILE="/var/log/solus-gpu-setup-intel.log"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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
log "=== Solus Intel GPU Setup ==="
log "Starting at $(date)"

# --- Parse Arguments ---------------------------------------------------------
CHECK_ONLY=false
NON_INTERACTIVE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --check|-c)   CHECK_ONLY=true; shift ;;
        --yes|-y)     NON_INTERACTIVE=true; shift ;;
        --help|-h)
            echo "Usage: sudo ./${SELF} [options]"
            echo "  --check, -c       Check compatibility only"
            echo "  --yes, -y         Non-interactive mode"
            echo "  --help, -h        Show this help"
            exit 0
            ;;
        *) die "Unknown option: $1" ;;
    esac
done

# --- Functions ---------------------------------------------------------------

detect_intel_gpu() {
    local gpu_info
    gpu_info="$(lspci -nn | grep -i 'vga.*intel\|3d.*intel\|display.*intel' | head -1 | sed 's/.*: //')"
    echo "${gpu_info:-Unknown Intel GPU}"
}

get_intel_gen() {
    local gpu_info
    gpu_info="$(detect_intel_gpu)"
    # Attempt to determine the generation from lspci info
    if echo "${gpu_info}" | grep -qiE 'HD Graphics [56]|UHD 6[0-9]|Iris Plus|Ice Lake'; then
        echo "gen11+"  # Ice Lake or newer
    elif echo "${gpu_info}" | grep -qiE 'HD Graphics [45]|UHD 4[0-9]|Kaby Lake|Coffee Lake|Whiskey Lake|Comet Lake'; then
        echo "gen9-10" # Gen9+
    elif echo "${gpu_info}" | grep -qiE 'HD Graphics [23]|Haswell|Broadwell|Skylake|Braswell|Cherryview'; then
        echo "gen8-"   # Pre-Gen9 (need crocus driver)
    else
        echo "unknown"
    fi
}

install_intel_drivers() {
    log "Installing Intel GPU drivers..."

    local gen
    gen="$(get_intel_gen)"
    log "Intel GPU generation: ${gen}"

    # Base Mesa packages
    local packages=(
        mesa-dri-drivers
        mesa-vulkan-drivers
        vulkan-intel
        intel-media-driver
        intel-vaapi-driver
        intel-compute-runtime
        intel-gpu-tools
        libva
        libva-utils
        linux-firmware-intel
    )

    if [[ "${gen}" == "gen8-" ]]; then
        packages+=(libva-intel-driver)
        warn "Older Intel GPU detected; installing legacy VA-API driver."
    fi

    dnf install -y "${packages[@]}" 2>&1 | tee -a "${LOG_FILE}"

    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        die "Package installation failed."
    fi

    log "Intel GPU packages installed: ${packages[*]}"
}

verify_anv() {
    log "Verifying ANV Vulkan driver..."
    if command -v vulkaninfo &>/dev/null; then
        if vulkaninfo --summary 2>/dev/null | grep -qi 'intel.*anv\|ANV'; then
            log "✓ ANV Vulkan driver detected."
        else
            warn "ANV Vulkan driver not detected. Check Mesa Vulkan installation."
        fi
    else
        warn "vulkaninfo not installed (install vulkan-tools for verification)."
    fi
}

verify_vaapi() {
    log "Verifying Intel VA-API..."
    if command -v vainfo &>/dev/null; then
        local va_output
        va_output="$(vainfo 2>/dev/null | grep -i 'intel\|iHD\|i965' | head -5 || true)"
        if [[ -n "${va_output}" ]]; then
            log "✓ Intel VA-API driver detected:"
            echo "${va_output}" | tee -a "${LOG_FILE}"
        else
            warn "Intel VA-API not detected. Check intel-media-driver."
        fi
    else
        warn "vainfo not installed (install libva-utils for verification)."
    fi
}

check_kernel_module() {
    log "Checking kernel modules..."
    if lsmod | grep -q i915; then
        log "✓ i915 kernel module loaded."
    else
        warn "i915 module not loaded. It will load on boot."
    fi
}

print_summary() {
    echo ""
    echo -e "${GREEN}✓ Intel GPU setup complete.${NC}"
    echo "  GPU: $(detect_intel_gpu)"
    echo "  Mesa: $(dnf list installed mesa-dri-drivers 2>/dev/null | tail -1 | awk '{print $2}')"
    echo "  ANV: $(vulkaninfo --summary 2>/dev/null | grep driverInfo | head -1 | cut -d= -f2 || echo 'check with vulkaninfo')"
    echo "  No reboot required (Mesa updates are runtime-switchable)."
}

# --- Main --------------------------------------------------------------------

GPU_NAME="$(detect_intel_gpu)"
log "Detected GPU: ${GPU_NAME}"

if [[ -z "${GPU_NAME}" || "${GPU_NAME}" == "Unknown Intel GPU" ]]; then
    warn "No Intel GPU detected. Proceeding with base driver installation."
fi

if [[ "${CHECK_ONLY}" == "true" ]]; then
    echo "GPU:         ${GPU_NAME}"
    echo "Gen:         $(get_intel_gen)"
    echo "Kernel:      $(uname -r)"
    echo "i915:        $(lsmod | grep -q i915 && echo 'loaded' || echo 'not loaded')"
    echo "Mesa:        $(dnf list installed mesa-dri-drivers 2>/dev/null | tail -1 | awk '{print $2}' || echo 'not installed')"
    echo "ANV:         $(command -v vulkaninfo &>/dev/null && vulkaninfo --summary 2>/dev/null | grep driverInfo | grep -i intel | head -1 | cut -d= -f2 || echo 'check with vulkaninfo')"
    exit 0
fi

if [[ "${NON_INTERACTIVE}" != "true" ]]; then
    echo ""
    echo -e "${BOLD}Intel Driver Installation${NC}"
    echo "  GPU:              ${GPU_NAME}"
    echo "  Generation:       $(get_intel_gen)"
    echo "  Mesa + Vulkan:    Yes (ANV)"
    echo "  VA-API:           Yes (intel-media-driver)"
    echo ""
    echo -n "Proceed? [Y/n]: "
    read -r answer
    case "${answer}" in
        n|N|no) die "Cancelled." ;;
        *) ;;
    esac
fi

install_intel_drivers
verify_anv
verify_vaapi
check_kernel_module
print_summary

log "=== Intel GPU Setup Complete ==="
exit 0
