#!/usr/bin/env bash
# ==============================================================================
# Solus Linux Kernel Builder
# Build script for kernel-solus with BORE scheduler and desktop optimizations
#
# Usage:
#   ./build.sh                    # Build generic x86_64 variant
#   ./build.sh --variant v3       # Build with x86-64-v3 optimizations
#   ./build.sh --variant v4       # Build with x86-64-v4 optimizations
#   ./build.sh --variant generic  # Build generic x86_64 (default)
#   ./build.sh --clean            # Clean build artifacts
#   ./build.sh --help             # Show this help
#
# Prerequisites:
#   - rpm-build, dracut, grub2-tools (or equivalent)
#   - gcc, make, patch, bc, bison, flex
#   - openssl-devel, elfutils-libelf-devel, dwarves
#   - python3-devel, perl, rsync, kmod
#
# Environment variables:
#   KERNEL_VERSION    - Kernel version to build (default: 6.14.2)
#   BUILD_DIR         - Build output directory
#   RPM_TOPDIR        - RPM build root directory
#   CONCURRENCY       - Number of parallel make jobs (default: nproc)
# ==============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_KERNEL_VERSION="${KERNEL_VERSION:-6.14.2}"
KERNEL_MAJOR="${DEFAULT_KERNEL_VERSION%.*}"
BUILD_DIR="${BUILD_DIR:-${SCRIPT_DIR}/build}"
RPM_TOPDIR="${RPM_TOPDIR:-${SCRIPT_DIR}/rpmbuild}"
CONCURRENCY="${CONCURRENCY:-$(nproc)}"
PATCH_DIR="${SCRIPT_DIR}/patches"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${BLUE}[STEP]${NC}  $*"; }

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------
usage() {
    sed -n '/^# Usage:/,/^$/{ s/^#//; s/^ //; p; }' "$0"
    exit 0
}

# ----------------------------------------------------------------------------
# Parse arguments
# ----------------------------------------------------------------------------
VARIANT="generic"
DO_CLEAN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --variant)
            shift
            case "$1" in
                v3|v4|generic) VARIANT="$1" ;;
                *) log_error "Invalid variant '$1'. Must be v3, v4, or generic."; exit 1 ;;
            esac
            ;;
        --clean)      DO_CLEAN=true ;;
        --help|-h)    usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
    shift
done

# ----------------------------------------------------------------------------
# Configure variant-specific flags
# ----------------------------------------------------------------------------
case "${VARIANT}" in
    v3)
        VARIANT_SUFFIX="-solus-v3"
        RPM_BUILD_OPTS="--with v3"
        CONFIG_ARCH="x86-64-v3"
        log_info "Building variant: ${YELLOW}x86-64-v3${NC}"
        ;;
    v4)
        VARIANT_SUFFIX="-solus-v4"
        RPM_BUILD_OPTS="--with v4"
        CONFIG_ARCH="x86-64-v4"
        log_info "Building variant: ${YELLOW}x86-64-v4${NC}"
        ;;
    generic|*)
        VARIANT_SUFFIX="-solus"
        RPM_BUILD_OPTS="--without custom"
        CONFIG_ARCH="x86_64"
        log_info "Building variant: ${YELLOW}generic x86_64${NC}"
        ;;
esac

KERNEL_FULL_VERSION="${DEFAULT_KERNEL_VERSION}${VARIANT_SUFFIX}"

# ----------------------------------------------------------------------------
# Clean
# ----------------------------------------------------------------------------
cleanup() {
    log_step "Cleaning build artifacts..."
    rm -rf "${BUILD_DIR}" "${RPM_TOPDIR}"
    log_info "Cleaned ${BUILD_DIR} and ${RPM_TOPDIR}"
}

if [[ "${DO_CLEAN}" == true ]]; then
    cleanup
    exit 0
fi

# ============================================================================
# MAIN BUILD
# ============================================================================

log_step "=== Solus Kernel Builder ==="
log_info "Kernel version:  ${DEFAULT_KERNEL_VERSION}"
log_info "Variant:         ${VARIANT}"
log_info "Jobs:            ${CONCURRENCY}"
log_info "Build dir:       ${BUILD_DIR}"
log_info "Output dir:      ${RPM_TOPDIR}"
echo ""

# ----------------------------------------------------------------------------
# 1. Check prerequisites
# ----------------------------------------------------------------------------
log_step "1/7: Checking prerequisites..."

PREREQS=(gcc make patch bc bison flex rsync xz openssl python3 perl git kmod)
MISSING=()
for cmd in "${PREREQS[@]}"; do
    if ! command -v "${cmd}" &>/dev/null; then
        MISSING+=("${cmd}")
    fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
    log_error "Missing prerequisites: ${MISSING[*]}"
    log_error "Install them with your package manager, e.g.:"
    log_error "  sudo dnf install gcc make patch bc bison flex rsync xz openssl-devel python3-devel perl git kmod"
    exit 1
fi
log_info "All prerequisites found."

# ----------------------------------------------------------------------------
# 2. Download kernel source
# ----------------------------------------------------------------------------
log_step "2/7: Downloading kernel source..."

KERNEL_TARBALL="linux-${DEFAULT_KERNEL_VERSION}.tar.xz"
KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v${KERNEL_MAJOR}.x/${KERNEL_TARBALL}"
KERNEL_SRC_DIR="${BUILD_DIR}/linux-${DEFAULT_KERNEL_VERSION}"

mkdir -p "${BUILD_DIR}"

if [[ -d "${KERNEL_SRC_DIR}" ]]; then
    log_info "Kernel source already extracted at ${KERNEL_SRC_DIR}"
else
    if [[ ! -f "${BUILD_DIR}/${KERNEL_TARBALL}" ]]; then
        log_info "Downloading ${KERNEL_URL}..."
        wget -O "${BUILD_DIR}/${KERNEL_TARBALL}" "${KERNEL_URL}" || \
            curl -L -o "${BUILD_DIR}/${KERNEL_TARBALL}" "${KERNEL_URL}" || {
                log_error "Failed to download kernel source. Try setting KERNEL_VERSION."
                exit 1
            }
    else
        log_info "Kernel tarball already cached."
    fi

    log_info "Extracting kernel source..."
    tar -xf "${BUILD_DIR}/${KERNEL_TARBALL}" -C "${BUILD_DIR}"
    log_info "Kernel source extracted to ${KERNEL_SRC_DIR}"
fi

cd "${KERNEL_SRC_DIR}"

# ----------------------------------------------------------------------------
# 3. Apply patches
# ----------------------------------------------------------------------------
log_step "3/7: Applying Solus patches..."

apply_patch() {
    local patch_file="$1"
    local patch_desc="$2"
    local strip_level="${3:-1}"

    if [[ ! -f "${patch_file}" ]]; then
        log_warn "Patch not found: ${patch_file} (skipping ${patch_desc})"
        return 1
    fi

    log_info "Applying: ${patch_desc}"
    if patch -p"${strip_level}" --forward --quiet < "${patch_file}" 2>/dev/null; then
        log_info "  ✓ ${patch_desc} applied successfully"
        return 0
    else
        # Check if already applied
        if patch -p"${strip_level}" --dry-run --forward --quiet < "${patch_file}" 2>/dev/null; then
            log_info "  - ${patch_desc} already applied, skipping"
            return 0
        else
            log_warn "  ✗ ${patch_desc} failed to apply (may be incompatible)"
            return 1
        fi
    fi
}

# Apply patches in order
PATCHES_APPLIED=0

# BORE scheduler
apply_patch "${PATCH_DIR}/sched_bore.patch"   "BORE Scheduler" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true

# CachyOS hardening
apply_patch "${PATCH_DIR}/cachyos-harder.patch" "CachyOS Hardening" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true

# Futex2 for PROTON_GE
apply_patch "${PATCH_DIR}/futex2.patch"         "Futex2 / PROTON_GE" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true

# BTRFS zstd-fast
apply_patch "${PATCH_DIR}/btrfs-zstd-fast.patch" "BTRFS zstd-fast" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true

# Additional performance patches
apply_patch "${PATCH_DIR}/clear-pkeys.patch"     "Clear Linux pkeys" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true
apply_patch "${PATCH_DIR}/lru-multigen.patch"    "LRU Multi-Gen" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true
apply_patch "${PATCH_DIR}/bcachefs.patch"        "bcachefs support" && PATCHES_APPLIED=$((PATCHES_APPLIED+1)) || true

log_info "Applied ${PATCHES_APPLIED} patches successfully."

# ----------------------------------------------------------------------------
# 4. Configure kernel
# ----------------------------------------------------------------------------
log_step "4/7: Configuring kernel..."

SOLUS_CONFIG="${SCRIPT_DIR}/config-x86_64"
if [[ ! -f "${SOLUS_CONFIG}" ]]; then
    log_error "Solus kernel config not found at ${SOLUS_CONFIG}"
    exit 1
fi

cp "${SOLUS_CONFIG}" .config

# Adjust config for variant
log_info "Adjusting config for ${VARIANT} variant..."
case "${VARIANT}" in
    v3)
        scripts/config --enable CONFIG_GENERIC_CPU3
        scripts/config --disable CONFIG_GENERIC_CPU2
        scripts/config --disable CONFIG_GENERIC_CPU
        scripts/config --set-str CONFIG_LOCALVERSION "-solus-v3"
        ;;
    v4)
        scripts/config --enable CONFIG_GENERIC_CPU4
        scripts/config --disable CONFIG_GENERIC_CPU3
        scripts/config --disable CONFIG_GENERIC_CPU2
        scripts/config --disable CONFIG_GENERIC_CPU
        scripts/config --set-str CONFIG_LOCALVERSION "-solus-v4"
        ;;
    generic|*)
        scripts/config --enable CONFIG_GENERIC_CPU
        scripts/config --disable CONFIG_GENERIC_CPU2
        scripts/config --disable CONFIG_GENERIC_CPU3
        scripts/config --set-str CONFIG_LOCALVERSION "-solus"
        ;;
esac

# Fix any dependency issues
yes '' | make oldconfig >/dev/null 2>&1

log_info "Kernel configured for ${VARIANT} variant."

# Show diff from stock config
echo "---"
log_info "Key configuration highlights:"
grep -E '(CONFIG_SCHED_BORE|CONFIG_PREEMPT_FULL|CONFIG_HZ_1000|CONFIG_GENERIC_CPU|CONFIG_SECURITY_SELINUX|CONFIG_BTRFS_FS|CONFIG_DRM_AMDGPU|CONFIG_DRM_I915)' .config || true
echo "---"

# ----------------------------------------------------------------------------
# 5. Build kernel and modules
# ----------------------------------------------------------------------------
log_step "5/7: Building kernel (${CONCURRENCY} jobs)..."

BUILD_START=$(date +%s)

make -j"${CONCURRENCY}" CC=gcc HOSTCC=gcc 2>&1 | tee "${BUILD_DIR}/build.log"

BUILD_END=$(date +%s)
BUILD_DURATION=$((BUILD_END - BUILD_START))
log_info "Build completed in $((BUILD_DURATION / 60))m $((BUILD_DURATION % 60))s"

# ----------------------------------------------------------------------------
# 6. Package into RPMs
# ----------------------------------------------------------------------------
log_step "6/7: Building RPM packages..."

mkdir -p "${RPM_TOPDIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy spec and sources
cp "${SCRIPT_DIR}/solus-kernel.spec" "${RPM_TOPDIR}/SPECS/"
cp "${SOLUS_CONFIG}" "${RPM_TOPDIR}/SOURCES/config-x86_64"

# Create source tarball of the configured source
cd "${BUILD_DIR}"
tar -czf "${RPM_TOPDIR}/SOURCES/linux-${DEFAULT_KERNEL_VERSION}.tar.gz" \
    "linux-${DEFAULT_KERNEL_VERSION}"

# Build RPMs
rpmbuild \
    --define "_topdir ${RPM_TOPDIR}" \
    --define "_smp_mflags -j${CONCURRENCY}" \
    ${RPM_BUILD_OPTS} \
    -ba "${RPM_TOPDIR}/SPECS/solus-kernel.spec" 2>&1 | tee "${BUILD_DIR}/rpmbuild.log"

log_info "RPM packages built:"
find "${RPM_TOPDIR}/RPMS" -name "*.rpm" -type f 2>/dev/null | sort

# ----------------------------------------------------------------------------
# 7. Install to local repo
# ----------------------------------------------------------------------------
log_step "7/7: Installing to local repository..."

LOCAL_REPO="${SCRIPT_DIR}/repo/${VARIANT}"
mkdir -p "${LOCAL_REPO}"

# Copy RPMs to local repo
find "${RPM_TOPDIR}/RPMS" -name "*.rpm" -type f -exec cp {} "${LOCAL_REPO}/" \;

# Create/update repo metadata
if command -v createrepo_c &>/dev/null; then
    createrepo_c --update "${LOCAL_REPO}"
    log_info "Repository metadata created at ${LOCAL_REPO}"
elif command -v createrepo &>/dev/null; then
    createrepo --update "${LOCAL_REPO}"
    log_info "Repository metadata created at ${LOCAL_REPO}"
else
    log_warn "createrepo/createrepo_c not found. Skipping repo metadata."
    log_warn "Install with: sudo eopkg install createrepo_c"
fi

# Log installed files
echo "---"
log_info "Packages installed to local repo:"
ls -lh "${LOCAL_REPO}/"*.rpm 2>/dev/null || echo "(no RPMs copied)"

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
echo ""
log_info "============================================"
log_info " Build Complete: kernel-solus ${DEFAULT_KERNEL_VERSION} (${VARIANT})"
log_info "============================================"
log_info " Source:    ${KERNEL_SRC_DIR}"
log_info " Config:    ${SOLUS_CONFIG}"
log_info " RPMS:      ${RPM_TOPDIR}/RPMS/"
log_info " Local repo: ${LOCAL_REPO}/"
log_info " Duration:  $((BUILD_DURATION / 60))m $((BUILD_DURATION % 60))s"
log_info " Patches:   ${PATCHES_APPLIED} applied"
echo ""
log_info "To install: sudo rpm -ivh ${LOCAL_REPO}/kernel-solus-*.rpm"
log_info "Or add repo: sudo dnf config-manager --add-repo file://${LOCAL_REPO}"
echo ""

# Optional: prompt for installation
if [[ -t 0 ]]; then
    read -r -p "Install kernel now? [y/N]: " REPLY
    if [[ "${REPLY}" =~ ^[Yy]$ ]]; then
        sudo rpm -ivh "${LOCAL_REPO}/"*.rpm
        log_info "Kernel installed. Reboot to use it."
    fi
fi
