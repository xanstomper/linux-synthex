#!/usr/bin/env bash
# =============================================================================
# SynthOS ISO Build Pipeline
# Generates bootable ISO images for all SynthOS editions
#
# Usage: ./build-iso.sh [OPTIONS] [EDITION]
#
# EDITION: plasma (default) | hyprland | gnome | gaming | minimal
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ─── Defaults ─────────────────────────────────────────────────────────────────
EDITION="${1:-plasma}"
VERSION="${VERSION:-2026.10}"
VARIANT="${VARIANT:-v3}"
AMBER="${AMBER:-}"                 # amber/gold suffix for special builds
PROFILES="${PROFILES:-}"           # custom profiles override

OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/build/out}"
WORK_DIR="${WORK_DIR:-$REPO_ROOT/build/rpmbuild/WORK}"
KS_DIR="$REPO_ROOT/build/kickstart"
LIVECD_DIR="$REPO_ROOT/build/livecd"

JOBS="${JOBS:-$(nproc)}"
SKIP_SIGN="${SKIP_SIGN:-false}"

# ─── Colors ───────────────────────────────────────────────────────────────────
G='\e[32m'; Y='\e[33m'; R='\e[31m'; B='\e[1m'; NC='\e[0m'
log()  { echo -e "${G}[ISO]${NC}  $*"; }
warn() { echo -e "${Y}[WARN]${NC} $*" >&2; }
fail() { echo -e "${R}[FAIL]${NC} $*" >&2; exit 1; }

# ─── Usage ────────────────────────────────────────────────────────────────────
usage() {
    cat <<USAGE
${B}SynthOS ISO Builder${NC}

Usage: $(basename "$0") [OPTIONS] [EDITION]

Editions:
  plasma      KDE Plasma 6 desktop (default, ~3.2 GB)
  hyprland    Hyprland tiling WM  (~2.8 GB)
  gnome       GNOME desktop       (~3.0 GB)
  gaming      Gaming-optimized KDE (~3.8 GB)
  minimal     CLI base only       (~900 MB)
  all         Build all editions

Options:
  --version VER       ISO version string (default: $VERSION)
  --variant VAR       Build variant — v3, lts, etc. (default: $VARIANT)
  --output DIR        Output directory (default: $OUTPUT_DIR)
  --skip-sign         Skip GPG signing of ISOs
  --no-cleanup        Keep work directory after build
  --help              Show this help

Environment Variables:
  VERSION             Version string
  JOBS                Parallel jobs for package build
  OUTPUT_DIR          Where to put finished ISOs
  GPG_KEY_ID          GPG key ID for signing

Examples:
  # Build KDE Plasma ISO
  ./build-iso.sh plasma

  # Build all editions
  ./build-iso.sh all

  # Build gaming ISO with custom version
  VERSION=2026.10-rc1 ./build-iso.sh gaming

USAGE
    exit 0
}

# ─── Dependency Check ─────────────────────────────────────────────────────────
check_deps() {
    log "Checking build dependencies..."
    local MISSING=()
    for cmd in livemedia-creator lorax pykickstart xorriso isohybrid dnf; do
        command -v "$cmd" &>/dev/null || MISSING+=("$cmd")
    done

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        warn "Missing: ${MISSING[*]}"
        echo "Install with: sudo dnf install lorax livemedia-creator pykickstart xorriso syslinux"
        fail "Missing required build tools"
    fi
    log "All dependencies satisfied ✓"
}

# ─── Kickstart Validation ─────────────────────────────────────────────────────
validate_kickstart() {
    local KS_FILE="$1"
    log "Validating kickstart: $(basename "$KS_FILE")"
    if ! ksvalidate "$KS_FILE" 2>/dev/null; then
        warn "ksvalidate not available or found issues — continuing anyway"
    fi
}

# ─── Build Single Edition ─────────────────────────────────────────────────────
build_edition() {
    local EDITION_NAME="$1"
    local KS_FILE="$KS_DIR/synthex-${EDITION_NAME}.ks"

    log "${B}Building SynthOS ${EDITION_NAME^^} Edition${NC}"
    log "  Version  : $VERSION"
    log "  Variant  : $VARIANT"
    log "  Kickstart: $KS_FILE"

    [[ -f "$KS_FILE" ]] || fail "Kickstart not found: $KS_FILE"

    validate_kickstart "$KS_FILE"

    mkdir -p "$OUTPUT_DIR" "$WORK_DIR/$EDITION_NAME"

    local ISO_NAME="synthex-${EDITION_NAME}-${VERSION}-${VARIANT}.iso"
    local RESULTISO="$OUTPUT_DIR/$ISO_NAME"

    log "Starting livemedia-creator..."
    sudo livemedia-creator \
        --ks "$KS_FILE" \
        --no-virt \
        --resultdir "$OUTPUT_DIR" \
        --project "SynthOS ${EDITION_NAME^}" \
        --make-iso \
        --volid "SynthOS-${EDITION_NAME^^}-${VERSION}" \
        --iso-only \
        --iso-name "$ISO_NAME" \
        --releasever "${VERSION%%.*}" \
        --tmp "$WORK_DIR/$EDITION_NAME" \
        --logfile "$OUTPUT_DIR/build-${EDITION_NAME}.log" \
        --macboot \
        --nomacboot \
        2>&1 | grep -E "^(INFO|WARNING|ERROR|Wrote|Creating|Done)" || true

    # Make hybrid (bootable from USB + CD)
    if [[ -f "$RESULTISO" ]]; then
        log "Making ISO hybrid (USB-bootable)..."
        isohybrid --uefi "$RESULTISO" 2>/dev/null || \
            warn "isohybrid failed — ISO may not be USB-bootable"

        # Checksum
        local SHA_FILE="$OUTPUT_DIR/${ISO_NAME}.sha256"
        sha256sum "$RESULTISO" > "$SHA_FILE"
        log "SHA256: $(cat "$SHA_FILE")"

        # GPG sign
        if [[ "$SKIP_SIGN" != "true" ]] && [[ -n "${GPG_KEY_ID:-}" ]]; then
            log "Signing with GPG key: $GPG_KEY_ID"
            gpg --detach-sign --armor \
                --default-key "$GPG_KEY_ID" \
                "$RESULTISO" || warn "GPG signing failed"
        fi

        local SIZE
        SIZE=$(du -sh "$RESULTISO" | cut -f1)
        log "${G}${B}✅ ISO complete: $RESULTISO ($SIZE)${NC}"
    else
        fail "ISO not generated — check $OUTPUT_DIR/build-${EDITION_NAME}.log"
    fi
}

# ─── Argument Parsing ─────────────────────────────────────────────────────────
NO_CLEANUP=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)   VERSION="$2"; shift 2 ;;
        --variant)   VARIANT="$2"; shift 2 ;;
        --output)    OUTPUT_DIR="$2"; shift 2 ;;
        --skip-sign) SKIP_SIGN=true; shift ;;
        --no-cleanup)NO_CLEANUP=true; shift ;;
        --help|-h)   usage ;;
        all|plasma|hyprland|gnome|gaming|minimal) EDITION="$1"; shift ;;
        *) warn "Unknown option: $1"; shift ;;
    esac
done

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
    echo -e "${B}☀️  SynthOS ISO Build Pipeline${NC}"
    echo "  Edition  : $EDITION"
    echo "  Version  : $VERSION"
    echo "  Output   : $OUTPUT_DIR"
    echo ""

    check_deps

    if [[ "$EDITION" == "all" ]]; then
        for ed in plasma hyprland gnome gaming minimal; do
            build_edition "$ed"
        done
    else
        build_edition "$EDITION"
    fi

    echo ""
    echo -e "${G}${B}=== SynthOS ISO Build Summary ===${NC}"
    find "$OUTPUT_DIR" -name "*.iso" -newer "$REPO_ROOT/Makefile" 2>/dev/null | \
        while read -r iso; do
            echo "  📀 $(basename "$iso")  $(du -sh "$iso" | cut -f1)"
        done
    echo ""
    echo -e "${G}ISOs ready in: $OUTPUT_DIR${NC}"
}

main
