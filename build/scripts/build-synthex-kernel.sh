#!/usr/bin/env bash
# =============================================================================
# SynthOS Kernel Build Script
# Builds the synthex-kernel RPM with BORE scheduler + gaming patches
# Usage: ./build-synthex-kernel.sh [--version X.Y.Z] [--release N] [--help]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORK_DIR="${WORK_DIR:-$HOME/rpmbuild}"
LOG="$WORK_DIR/BUILD/synthex-kernel-build.log"

# Defaults
KERNEL_VERSION="${KERNEL_VERSION:-6.12}"
RELEASE="${RELEASE:-1}"
FEDORA_KERNEL_VERSION="${FEDORA_KERNEL_VERSION:-6.12.0}"
SPEC_FILE="$REPO_ROOT/packages/spec-files/synthex-kernel.spec"
PATCH_DIR="$REPO_ROOT/packages/kernel-patches"

# Colors
GREEN='\e[32m'; YELLOW='\e[33m'; RED='\e[31m'; BOLD='\e[1m'; NC='\e[0m'

log()  { echo -e "${GREEN}[BUILD]${NC} $*" | tee -a "$LOG" 2>/dev/null || echo "[BUILD] $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*" >&2; }
fail() { echo -e "${RED}[FAIL]${NC}  $*" >&2; exit 1; }

usage() {
    cat <<USAGE
SynthOS Kernel Build Script

Usage: $(basename "$0") [OPTIONS]

Options:
  --version VER     Kernel version to build against (default: $KERNEL_VERSION)
  --release N       RPM release number (default: $RELEASE)
  --no-bore         Skip BORE scheduler patch
  --no-futex        Skip FUTEX2/futex_waitv patches
  --no-hdr          Skip HDR/color management patches
  --patches-only    Only apply patches, don't build RPM
  --check-deps      Check build dependencies and exit
  --help            Show this help

Environment Variables:
  KERNEL_VERSION    Base kernel version (default: $KERNEL_VERSION)
  WORK_DIR          RPM build directory (default: ~/rpmbuild)
  JOBS              Parallel make jobs (default: nproc)

Examples:
  # Build default kernel
  ./build-synthex-kernel.sh

  # Build specific version
  KERNEL_VERSION=6.12.5 ./build-synthex-kernel.sh --release 2

  # Check what dependencies are needed
  ./build-synthex-kernel.sh --check-deps

USAGE
    exit 0
}

# Argument parsing
OPT_BORE=true
OPT_FUTEX=true
OPT_HDR=true
OPT_PATCHES_ONLY=false
OPT_CHECK_DEPS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)   KERNEL_VERSION="$2"; shift 2 ;;
        --release)   RELEASE="$2"; shift 2 ;;
        --no-bore)   OPT_BORE=false; shift ;;
        --no-futex)  OPT_FUTEX=false; shift ;;
        --no-hdr)    OPT_HDR=false; shift ;;
        --patches-only) OPT_PATCHES_ONLY=true; shift ;;
        --check-deps)   OPT_CHECK_DEPS=true; shift ;;
        --help|-h)   usage ;;
        *) warn "Unknown option: $1"; shift ;;
    esac
done

# =============================================================================
# Dependency Check
# =============================================================================
check_deps() {
    log "Checking build dependencies..."
    local MISSING=()
    local DEPS=(
        gcc g++ make binutils flex bison
        rpm-build rpmlint dnf
        openssl openssl-devel
        elfutils-libelf-devel
        bc perl python3
        ncurses-devel
        rsync tar xz zstd
    )
    for dep in "${DEPS[@]}"; do
        if ! command -v "$dep" &>/dev/null && ! rpm -q "$dep" &>/dev/null; then
            MISSING+=("$dep")
        fi
    done

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        warn "Missing dependencies: ${MISSING[*]}"
        echo "Install with: sudo dnf install ${MISSING[*]}"
        [[ "$OPT_CHECK_DEPS" == "true" ]] && exit 1
    else
        log "All dependencies satisfied ✓"
        [[ "$OPT_CHECK_DEPS" == "true" ]] && exit 0
    fi
}

# =============================================================================
# Setup Build Environment
# =============================================================================
setup_build_env() {
    log "Setting up RPM build environment in $WORK_DIR"
    mkdir -p "$WORK_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
    mkdir -p "$LOG_DIR"

    # Copy spec file
    cp "$SPEC_FILE" "$WORK_DIR/SPECS/synthex-kernel.spec"

    # Apply version overrides
    sed -i "s/^Version:.*/Version:        $KERNEL_VERSION/" \
        "$WORK_DIR/SPECS/synthex-kernel.spec"
    sed -i "s/^Release:.*/Release:        ${RELEASE}%{?dist}/" \
        "$WORK_DIR/SPECS/synthex-kernel.spec"

    log "Spec prepared for kernel $KERNEL_VERSION-$RELEASE"
}

LOG_DIR="$WORK_DIR/BUILD"

# =============================================================================
# Download Kernel Sources
# =============================================================================
download_sources() {
    log "Downloading kernel sources for $KERNEL_VERSION..."
    local KERNEL_TARBALL="$WORK_DIR/SOURCES/linux-${KERNEL_VERSION}.tar.xz"

    if [[ -f "$KERNEL_TARBALL" ]]; then
        log "Kernel tarball already present, skipping download"
    else
        # Try kernel.org first, fall back to Fedora's sources
        local MAJVER="${KERNEL_VERSION%%.*}"
        local KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v${MAJVER}.x/linux-${KERNEL_VERSION}.tar.xz"
        log "Downloading: $KERNEL_URL"
        curl -L --retry 3 --retry-delay 5 \
            -o "$KERNEL_TARBALL" "$KERNEL_URL" || {
            warn "kernel.org download failed, trying Fedora koji..."
            # Fallback: use Fedora's kernel SRPM
            local KOJI_URL="https://koji.fedoraproject.org/koji/packageinfo?packageID=8"
            warn "Please download kernel SRPM from Fedora Koji manually"
            fail "Cannot download kernel sources automatically"
        }
    fi

    # Verify tarball
    log "Verifying kernel tarball..."
    if ! xz -t "$KERNEL_TARBALL" &>/dev/null; then
        rm -f "$KERNEL_TARBALL"
        fail "Kernel tarball corrupted; re-run to re-download"
    fi

    cp "$KERNEL_TARBALL" "$WORK_DIR/SOURCES/"
}

# =============================================================================
# Apply Patches
# =============================================================================
apply_patches() {
    log "Staging patches into SOURCES..."
    mkdir -p "$WORK_DIR/SOURCES/patches"

    if [[ "$OPT_BORE" == "true" ]]; then
        if [[ -f "$PATCH_DIR/bore-scheduler.patch" ]]; then
            cp "$PATCH_DIR/bore-scheduler.patch" "$WORK_DIR/SOURCES/"
            log "  ✓ BORE scheduler patch staged"
        else
            warn "  BORE patch not found at $PATCH_DIR/bore-scheduler.patch"
            warn "  Download from: https://github.com/firelzrd/bore-scheduler"
        fi
    fi

    if [[ "$OPT_FUTEX" == "true" ]]; then
        if [[ -f "$PATCH_DIR/futex2.patch" ]]; then
            cp "$PATCH_DIR/futex2.patch" "$WORK_DIR/SOURCES/"
            log "  ✓ FUTEX2 patch staged"
        else
            warn "  FUTEX2 patch not found — skipping (may already be upstream)"
        fi
    fi

    if [[ "$OPT_HDR" == "true" ]]; then
        if [[ -f "$PATCH_DIR/hdr-patches.patch" ]]; then
            cp "$PATCH_DIR/hdr-patches.patch" "$WORK_DIR/SOURCES/"
            log "  ✓ HDR color management patches staged"
        else
            warn "  HDR patches not found — skipping"
        fi
    fi

    # Always stage the synthex kernel config
    if [[ -f "$REPO_ROOT/configs/kernel/synthex-kernel.config" ]]; then
        cp "$REPO_ROOT/configs/kernel/synthex-kernel.config" \
            "$WORK_DIR/SOURCES/synthex-kernel.config"
        log "  ✓ SynthOS kernel config staged"
    else
        warn "  Kernel config not found; rpmbuild will use Fedora default"
    fi

    # Logo / branding
    if [[ -f "$REPO_ROOT/branding/theme/logo/synthex-logo.png" ]]; then
        cp "$REPO_ROOT/branding/theme/logo/synthex-logo.png" \
            "$WORK_DIR/SOURCES/synthex-tux.png"
        log "  ✓ SynthOS Tux logo staged"
    fi
}

# =============================================================================
# Build RPM
# =============================================================================
build_rpm() {
    log "Building synthex-kernel RPM (this will take 30–90 min)..."
    local JOBS="${JOBS:-$(nproc)}"
    log "Using $JOBS parallel jobs"

    rpmbuild \
        -ba "$WORK_DIR/SPECS/synthex-kernel.spec" \
        --define "_topdir $WORK_DIR" \
        --define "jobs $JOBS" \
        --define "synthex_bore $OPT_BORE" \
        --define "synthex_futex $OPT_FUTEX" \
        --define "synthex_hdr $OPT_HDR" \
        2>&1 | tee -a "$LOG" | grep -E "^(Processing|Building|Wrote|error:|warning:|\[BUILD\])" || true

    # Show output RPMs
    echo ""
    log "${BOLD}Build complete! Generated RPMs:${NC}"
    find "$WORK_DIR/RPMS" -name "synthex-kernel*.rpm" | while read -r rpm; do
        echo "  📦 $rpm  ($(du -sh "$rpm" | cut -f1))"
    done
}

# =============================================================================
# Validate RPM
# =============================================================================
validate_rpm() {
    log "Validating generated RPMs with rpmlint..."
    find "$WORK_DIR/RPMS" -name "synthex-kernel*.rpm" | while read -r rpm; do
        rpmlint "$rpm" 2>&1 | grep -v "^0 errors" || true
    done

    # Check SRPM too
    local SRPM
    SRPM=$(find "$WORK_DIR/SRPMS" -name "synthex-kernel*.src.rpm" | head -1)
    if [[ -f "$SRPM" ]]; then
        log "SRPM: $SRPM  ($(du -sh "$SRPM" | cut -f1))"
    fi
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo -e "${BOLD}☀️  SynthOS Kernel Builder${NC}"
    echo "  Kernel version : $KERNEL_VERSION"
    echo "  Release        : $RELEASE"
    echo "  BORE scheduler : $OPT_BORE"
    echo "  FUTEX2         : $OPT_FUTEX"
    echo "  HDR patches    : $OPT_HDR"
    echo "  Build dir      : $WORK_DIR"
    echo ""

    check_deps
    setup_build_env
    download_sources
    apply_patches

    if [[ "$OPT_PATCHES_ONLY" == "true" ]]; then
        log "Patches staged (--patches-only mode). Not building RPM."
        exit 0
    fi

    build_rpm
    validate_rpm

    echo ""
    echo -e "${GREEN}${BOLD}✅ synthex-kernel $KERNEL_VERSION-$RELEASE build complete!${NC}"
    echo ""
    echo "Install with:"
    echo "  sudo dnf install $WORK_DIR/RPMS/x86_64/synthex-kernel-${KERNEL_VERSION}-${RELEASE}.*.x86_64.rpm"
}

main "$@"
