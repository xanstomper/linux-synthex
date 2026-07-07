#!/usr/bin/env bash
# SynthOS - Reproducible ISO Build Script
# Uses livecd-creator (lorax) in a clean container environment
# Supports Plasma, Hyprland, and GNOME editions
#
# Usage:
#   ./build-iso.sh [edition] [options]
#
# Editions:
#   plasma   - KDE Plasma edition (default)
#   hyprland - Hyprland edition
#   gnome    - GNOME edition
#
# Options:
#   --releasever=VER    Fedora release version (default: rawhide)
#   --output-dir=DIR    Output directory for artifacts (default: ./output)
#   --build-dir=DIR     Temporary build directory (default: ./build-work)
#   --keep-cache        Don't clean the cache after build
#   --gpg-key=KEY       GPG key ID for signing (default: auto-detect)
#   --no-sign           Skip GPG signing
#   --no-torrent        Skip torrent file generation
#   --no-checksum       Skip SHA256 checksum generation
#   --docker            Build inside Docker container using our Dockerfile
#   --push              Push artifacts to release server after build
#   --ci                CI mode: automated, less verbose
#   --version=VER       Set ISO version string (default: date-based)
#   --help              Show this help

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
EDITION="${1:-plasma}"
RELEASEVER="rawhide"
OUTPUT_DIR="$PROJECT_ROOT/build/output"
BUILD_DIR="$PROJECT_ROOT/build/build-work"
KEEP_CACHE=false
GPG_KEY=""
NO_SIGN=false
NO_TORRENT=false
NO_CHECKSUM=false
USE_DOCKER=false
PUSH_ARTIFACTS=false
CI_MODE=false
VERSION=""
ARCH="x86_64"

# Color output
if [ -t 1 ] && ! ${CI_MODE:-false}; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    NC=''
fi

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()  { echo -e "${CYAN}[STEP]${NC}  $*"; }
log_debug() { ${CI_MODE} || echo -e "${BLUE}[DEBUG]${NC} $*"; }

# =============================================================================
# Helper Functions
# =============================================================================

usage() {
    sed -n '2,/^$/p' "${BASH_SOURCE[0]}" | head -n -1 | sed 's/^# //; s/^#$//'
    exit 0
}

check_dependencies() {
    local deps=("livecd-creator" "mksquashfs" "xorriso" "grub2-mkrescue" "sha256sum" "gpg" "git")
    local missing=()

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            missing+=("$dep")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing[*]}"
        log_info "Install them with: sudo dnf install lorax squashfs-tools xorriso grub2-tools-extra gnupg2"
        exit 1
    fi

    # Optional dependencies
    if ! command -v transmission-create &>/dev/null; then
        log_warn "transmission-cli not found. Torrent generation will be skipped."
        NO_TORRENT=true
    fi
}

get_kickstart_path() {
    case "$EDITION" in
        plasma|kde)   echo "$PROJECT_ROOT/build/kickstart/synthex-plasma.ks" ;;
        hyprland)     echo "$PROJECT_ROOT/build/kickstart/synthex-hyprland.ks" ;;
        gnome)        echo "$PROJECT_ROOT/build/kickstart/synthex-gnome.ks" ;;
        *)            log_error "Unknown edition: $EDITION"; usage ;;
    esac
}

get_iso_name() {
    local edition_label
    case "$EDITION" in
        plasma|kde)   edition_label="Plasma" ;;
        hyprland)     edition_label="Hyprland" ;;
        gnome)        edition_label="GNOME" ;;
    esac
    echo "Synthex-${edition_label}-${VERSION}-${ARCH}.iso"
}

get_iso_label() {
    local edition_short
    case "$EDITION" in
        plasma|kde)   edition_short="PLASMA" ;;
        hyprland)     edition_short="HYPRLAND" ;;
        gnome)        edition_short="GNOME" ;;
    esac
    echo "SYNTHEX_${edition_short}_${VERSION//./_}"
}

# =============================================================================
# Build Functions
# =============================================================================

build_iso() {
    local kickstart
    kickstart="$(get_kickstart_path)"
    local iso_name
    iso_name="$(get_iso_name)"
    local iso_label
    iso_label="$(get_iso_label)"

    if [ ! -f "$kickstart" ]; then
        log_error "Kickstart file not found: $kickstart"
        exit 1
    fi

    log_step "Building Synthex ${EDITION^} ISO (${VERSION})"
    log_info "  Kickstart: $kickstart"
    log_info "  Output:    $OUTPUT_DIR/$iso_name"
    log_info "  Label:     $iso_label"

    mkdir -p "$OUTPUT_DIR" "$BUILD_DIR"

    local cache_args=""
    ${KEEP_CACHE} && cache_args="--cache=$BUILD_DIR/cache"

    # Build with livecd-creator
    sudo livecd-creator \
        --verbose \
        --config="$kickstart" \
        --releasever="$RELEASEVER" \
        --title="SynthOS ${EDITION^}" \
        --product="Synthex" \
        --volid="$iso_label" \
        $cache_args \
        --tmp="$BUILD_DIR/tmp" \
        --compression-type="zstd" \
        --compression-args="-Xcompression-level=19" \
        --keep-image \
        -o "$OUTPUT_DIR/$iso_name"

    if [ $? -ne 0 ]; then
        log_error "ISO build failed. Check logs above."
        exit 1
    fi

    log_info "ISO built successfully: $OUTPUT_DIR/$iso_name"
}

sign_iso() {
    local iso_name
    iso_name="$(get_iso_name)"
    local iso_path="$OUTPUT_DIR/$iso_name"

    if ${NO_SIGN}; then
        log_warn "Skipping GPG signing (--no-sign)"
        return 0
    fi

    if [ ! -f "$iso_path" ]; then
        log_error "ISO not found for signing: $iso_path"
        return 1
    fi

    local gpg_key="${GPG_KEY}"
    if [ -z "$gpg_key" ]; then
        # Auto-detect first available signing key
        gpg_key=$(gpg --list-secret-keys --with-colons 2>/dev/null | \
                  awk -F: '/^sec:/ {print $5}' | head -1)
        if [ -z "$gpg_key" ]; then
            log_warn "No GPG key found. Generating a build key..."
            cat > /tmp/gpg-batch << 'EOGPG'
%no-protection
Key-Type: RSA
Key-Length: 4096
Key-Usage: sign
Name-Real: Synthex Build Bot
Name-Email: build@getsynthex.org
Expire-Date: 0
%commit
EOGPG
            gpg --batch --gen-key /tmp/gpg-batch
            rm -f /tmp/gpg-batch
            gpg_key=$(gpg --list-secret-keys --with-colons | awk -F: '/^sec:/ {print $5}' | head -1)
        fi
    fi

    log_step "Signing ISO with GPG key: $gpg_key"

    # Detached signature
    gpg --detach-sign \
        --armor \
        --default-key="$gpg_key" \
        --output="${iso_path}.sig" \
        "$iso_path"

    # Embedded signature (via isohybrid)
    if command -v isohybrid &>/dev/null; then
        sudo isohybrid --uefi "$iso_path" 2>/dev/null || true
        gpg --detach-sign \
            --default-key="$gpg_key" \
            --output="${iso_path}.gpg" \
            "$iso_path"
    fi

    log_info "ISO signed: ${iso_path}.sig"
}

generate_checksums() {
    local iso_name
    iso_name="$(get_iso_name)"

    if ${NO_CHECKSUM}; then
        log_warn "Skipping checksum generation (--no-checksum)"
        return 0
    fi

    log_step "Generating SHA256 checksums"

    local checksum_file="$OUTPUT_DIR/Synthex-${EDITION^}-${VERSION}-SHA256SUMS"
    cd "$OUTPUT_DIR"

    # Clear existing checksum file
    > "$checksum_file"

    # Compute checksums for all artifacts
    for file in "$iso_name" "${iso_name}.sig" "${iso_name}.gpg"; do
        if [ -f "$file" ]; then
            sha256sum "$file" >> "$checksum_file"
        fi
    done

    # Sign the checksum file
    if ! ${NO_SIGN}; then
        gpg --detach-sign --armor \
            --output="${checksum_file}.sig" \
            "$checksum_file"
    fi

    log_info "Checksums written to: $checksum_file"
    cat "$checksum_file"
}

generate_torrent() {
    local iso_name
    iso_name="$(get_iso_name)"

    if ${NO_TORRENT}; then
        log_warn "Skipping torrent generation (--no-torrent)"
        return 0
    fi

    if ! command -v transmission-create &>/dev/null; then
        log_warn "transmission-create not found. Skipping torrent."
        return 0
    fi

    log_step "Generating BitTorrent metadata"

    local torrent_file="$OUTPUT_DIR/Synthex-${EDITION^}-${VERSION}-${ARCH}.torrent"
    local announce_url="https://tracker.getsynthex.org/announce"

    transmission-create \
        --comment="SynthOS ${EDITION^} ${VERSION} ${ARCH}" \
        --tracker="$announce_url" \
        --private \
        --outfile="$torrent_file" \
        "$OUTPUT_DIR/$iso_name"

    if [ -f "$torrent_file" ]; then
        log_info "Torrent created: $torrent_file"
        # Generate magnet link
        local info_hash
        info_hash=$(transmission-show "$torrent_file" 2>/dev/null | grep "^  Hash:" | awk '{print $2}')
        echo "magnet:?xt=urn:btih:${info_hash}&dn=Synthex-${EDITION^}-${VERSION}-${ARCH}" \
            > "${torrent_file}.magnet"
        log_info "Magnet link: $(cat ${torrent_file}.magnet)"
    fi
}

create_build_manifest() {
    log_step "Creating build manifest"

    local manifest_file="$OUTPUT_DIR/Synthex-${EDITION^}-${VERSION}-manifest.txt"
    local iso_name
    iso_name="$(get_iso_name)"

    {
        echo "SynthOS Build Manifest"
        echo "========================="
        echo "Edition:     ${EDITION^}"
        echo "Version:     ${VERSION}"
        echo "Arch:        ${ARCH}"
        echo "Build Date:  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
        echo "Kickstart:   $(get_kickstart_path)"
        echo "Releasever:  ${RELEASEVER}"
        echo ""
        echo "Build Host:  $(hostname -f 2>/dev/null || echo 'unknown')"
        echo "Kernel:      $(uname -r)"
        echo "User:        $(whoami)"
        echo ""
        echo "Git Commit:  $(cd "$PROJECT_ROOT" && git describe --always --dirty 2>/dev/null || echo 'N/A')"
        echo "Git Branch:  $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'N/A')"
        echo ""
        echo "Installed Packages:"
        echo "------------------"
        rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' | sort
    } > "$manifest_file"

    log_info "Manifest: $manifest_file"
}

push_artifacts() {
    if ! ${PUSH_ARTIFACTS}; then
        return 0
    fi

    log_step "Pushing artifacts to release server"

    local remote_user="${REMOTE_USER:-builder}"
    local remote_host="${REMOTE_HOST:-releases.getsynthex.org}"
    local remote_path="${REMOTE_PATH:-/var/www/releases/synthex}"

    rsync -avzP \
        --include="Synthex-${EDITION^}-${VERSION}-*" \
        --exclude="*" \
        "$OUTPUT_DIR/" \
        "${remote_user}@${remote_host}:${remote_path}/"

    log_info "Artifacts pushed to ${remote_host}:${remote_path}/"
}

cleanup_build() {
    if ${KEEP_CACHE}; then
        log_info "Keeping build cache at $BUILD_DIR/cache"
    else
        log_step "Cleaning up build artifacts"
        if [ -d "$BUILD_DIR" ]; then
            sudo rm -rf "$BUILD_DIR/tmp" 2>/dev/null || true
        fi
    fi
}

# =============================================================================
# Main Build Pipeline
# =============================================================================

main() {
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            plasma|kde|hyprland|gnome)
                EDITION="$1"
                shift
                ;;
            --releasever=*) RELEASEVER="${1#*=}"; shift ;;
            --output-dir=*) OUTPUT_DIR="${1#*=}"; shift ;;
            --build-dir=*)  BUILD_DIR="${1#*=}"; shift ;;
            --keep-cache)   KEEP_CACHE=true; shift ;;
            --gpg-key=*)    GPG_KEY="${1#*=}"; shift ;;
            --no-sign)      NO_SIGN=true; shift ;;
            --no-torrent)   NO_TORRENT=true; shift ;;
            --no-checksum)  NO_CHECKSUM=true; shift ;;
            --docker)       USE_DOCKER=true; shift ;;
            --push)         PUSH_ARTIFACTS=true; shift ;;
            --ci)           CI_MODE=true; shift ;;
            --version=*)    VERSION="${1#*=}"; shift ;;
            --help|-h)      usage ;;
            *)              log_error "Unknown option: $1"; usage ;;
        esac
    done

    # Set version if not specified
    if [ -z "$VERSION" ]; then
        VERSION="$(date -u '+%Y%m%d')"
        # Try to get from git tag
        if git_tag=$(cd "$PROJECT_ROOT" && git describe --tags --abbrev=0 2>/dev/null); then
            VERSION="$git_tag-$(date -u '+%Y%m%d')"
        fi
    fi

    # Docker mode: run inside container
    if ${USE_DOCKER}; then
        log_step "Running build inside Docker container"
        local dockerfile="$SCRIPT_DIR/Dockerfile"

        if [ ! -f "$dockerfile" ]; then
            log_error "Dockerfile not found: $dockerfile"
            exit 1
        fi

        # Build the container image
        local container_tag="synthex-builder:${VERSION}"
        docker build \
            --tag "$container_tag" \
            --build-arg "EDITION=$EDITION" \
            --build-arg "VERSION=$VERSION" \
            --build-arg "RELEASEVER=$RELEASEVER" \
            -f "$dockerfile" \
            "$SCRIPT_DIR"

        # Run the build inside container
        docker run --rm \
            --privileged \
            -v "$OUTPUT_DIR:/output" \
            -v "$PROJECT_ROOT/build/kickstart:/kickstart:ro" \
            -e "EDITION=$EDITION" \
            -e "VERSION=$VERSION" \
            -e "RELEASEVER=$RELEASEVER" \
            -e "CI=$CI_MODE" \
            "$container_tag"

        log_info "Docker build complete. Artifacts in: $OUTPUT_DIR"
        exit 0
    fi

    # Native build pipeline
    log_step "=== SynthOS ISO Build Pipeline ==="
    log_info "Edition:   ${EDITION^}"
    log_info "Version:   ${VERSION}"
    log_info "Output:    ${OUTPUT_DIR}"
    log_info "Start:     $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    # Check dependencies
    check_dependencies

    # Check if running as root (needed for livecd-creator)
    if [ "$(id -u)" -ne 0 ]; then
        log_warn "livecd-creator requires root. Re-running with sudo..."
        exec sudo "$0" "$@"
    fi

    # Build ISO
    build_iso

    # Post-build steps
    create_build_manifest
    sign_iso
    generate_checksums
    generate_torrent

    # Push if requested
    push_artifacts

    # Cleanup
    cleanup_build

    log_step "=== Build Complete ==="
    log_info "Edition:   ${EDITION^}"
    log_info "Version:   ${VERSION}"
    log_info "Artifacts: ${OUTPUT_DIR}"
    log_info "Finished:  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    # Summary
    echo ""
    echo "============================================"
    echo " Build Summary"
    echo "============================================"
    echo " ISO:         $(get_iso_name)"
    echo " Size:        $(ls -lh "$OUTPUT_DIR/$(get_iso_name)" 2>/dev/null | awk '{print $5}')"
    echo " SHA256:      ${OUTPUT_DIR}/Synthex-${EDITION^}-${VERSION}-SHA256SUMS"
    if [ -f "$OUTPUT_DIR/$(get_iso_name).sig" ]; then
        echo " Signature:   ${OUTPUT_DIR}/$(get_iso_name).sig"
    fi
    if [ -f "$OUTPUT_DIR/Synthex-${EDITION^}-${VERSION}-${ARCH}.torrent" ]; then
        echo " Torrent:     ${OUTPUT_DIR}/Synthex-${EDITION^}-${VERSION}-${ARCH}.torrent"
    fi
    echo "============================================"
}

# Run main
main "$@"
