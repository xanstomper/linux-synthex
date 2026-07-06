#!/bin/bash
# Solus ISO Build Pipeline — End-to-End ISO Generator
# Usage: ./build-solus-iso.sh [--edition plasma|hyprland|gnome] [--variant v3|v4|generic] [--profile gaming|dev|full|minimal]

set -euo pipefail

VERSION="${VERSION:-0.1.0}"
EDITION="${1:-plasma}"
VARIANT="${2:-v3}"
PROFILE="${3:-full}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_DIR}/build/iso-out"
WORK_DIR="/tmp/solus-build-$$"

SOLUS_AMBER='\033[38;5;214m'
NC='\033[0m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'

echo -e "${SOLUS_AMBER}════════════════════════════════════════════════════${NC}"
echo -e "${SOLUS_AMBER}  ☀️  Solus Linux ISO Builder v${VERSION}${NC}"
echo -e "${SOLUS_AMBER}  Edition: ${EDITION}  |  Variant: ${VARIANT}  |  Profile: ${PROFILE}${NC}"
echo -e "${SOLUS_AMBER}════════════════════════════════════════════════════${NC}"

# ─── Prerequisites check ──────────────────────────────────────────

check_prereqs() {
    local missing=0
    for cmd in dnf lorax livemedia-creator mkisofs isohybrid; do
        if ! command -v "$cmd" &>/dev/null; then
            echo -e "${RED}❌ Missing: $cmd${NC}"
            missing=$((missing + 1))
        fi
    done
    
    if [ "$missing" -gt 0 ]; then
        echo ""
        echo "Install missing tools:"
        echo "  sudo dnf install lorax livemedia-creator pykickstart xorriso"
        exit 1
    fi
    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# ─── Setup build environment ──────────────────────────────────────

setup_workdir() {
    echo -e "\n${BOLD}📁 Setting up build environment...${NC}"
    rm -rf "$WORK_DIR" "$OUTPUT_DIR"
    mkdir -p "$WORK_DIR" "$OUTPUT_DIR"
    echo "  Work: $WORK_DIR"
    echo "  Output: $OUTPUT_DIR"
}

# ─── Prepare kickstart with edition-specific config ───────────────

prepare_kickstart() {
    local ks_template="${PROJECT_DIR}/build/kickstart/solus-${EDITION}.ks"
    local ks_output="${WORK_DIR}/solus-${EDITION}-${VERSION}.ks"
    
    if [ ! -f "$ks_template" ]; then
        echo -e "${RED}❌ Kickstart template not found: $ks_template${NC}"
        exit 1
    fi
    
    echo -e "\n${BOLD}📝 Preparing kickstart...${NC}"
    
    # Copy and patch kickstart
    cp "$ks_template" "$ks_output"
    
    # Add profile-specific package groups
    case "$PROFILE" in
        gaming)
            echo "%include ${PROJECT_DIR}/build/kickstart/solus-gaming-packages.ksinc" >> "$ks_output"
            ;;
        dev|developer)
            cat >> "$ks_output" << 'DEVEOF'
%packages --exclude=weak-deps
@development-tools
gcc gcc-c++ make cmake
rust cargo golang nodejs python3-devel
git podman podman-compose
%end
DEVEOF
            ;;
        minimal)
            # Just the base
            ;;
        full|*)
            echo "%include ${PROJECT_DIR}/build/kickstart/solus-gaming-packages.ksinc" >> "$ks_output"
            cat >> "$ks_output" << 'FULLEOF'
%packages --exclude=weak-deps
@development-tools
gcc gcc-c++ make cmake
rust cargo golang nodejs python3-devel
git podman podman-compose
blender krita gimp obs-studio
%end
FULLEOF
            ;;
    esac
    
    echo "  Kickstart: $ks_output"
}

# ─── Install Solus packages into rootfs ────────────────────────────

build_rootfs() {
    echo -e "\n${BOLD}📦 Building root filesystem...${NC}"
    
    # Use livemedia-creator with our kickstart
    livemedia-creator \
        --ks="${WORK_DIR}/solus-${EDITION}-${VERSION}.ks" \
        --no-virt \
        --resultdir="${WORK_DIR}/live" \
        --project="Solus Linux" \
        --make-iso \
        --iso-only \
        --iso-name="solus-${EDITION}-${VERSION}-${VARIANT}.iso" \
        --volid="SOLUS" \
        --squashfs-only 2>&1 | tee "${WORK_DIR}/build.log"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Rootfs build failed. Check: ${WORK_DIR}/build.log${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Rootfs built successfully${NC}"
}

# ─── Create bootable ISO ───────────────────────────────────────────

create_iso() {
    local iso_name="solus-${EDITION}-${VERSION}-${VARIANT}.iso"
    local iso_path="${OUTPUT_DIR}/${iso_name}"
    
    echo -e "\n${BOLD}💿 Creating bootable ISO...${NC}"
    
    # Find the generated ISO
    local generated_iso=$(find "${WORK_DIR}/live" -name "*.iso" 2>/dev/null | head -1)
    
    if [ -z "$generated_iso" ]; then
        echo -e "${RED}❌ No ISO generated${NC}"
        exit 1
    fi
    
    # Copy to output
    cp "$generated_iso" "$iso_path"
    
    # Create hybrid ISO (supports both USB and optical)
    isohybrid --uefi "$iso_path" 2>/dev/null || true
    
    # Create checksums
    cd "$OUTPUT_DIR"
    sha256sum "$iso_name" > "${iso_name}.sha256"
    b2sum "$iso_name" > "${iso_name}.b2" 2>/dev/null || true
    
    echo -e "${GREEN}✅ ISO created: ${iso_path}${NC}"
}

# ─── Sign ISO ──────────────────────────────────────────────────────

sign_iso() {
    local iso_name="solus-${EDITION}-${VERSION}-${VARIANT}.iso"
    local iso_path="${OUTPUT_DIR}/${iso_name}"
    
    if command -v gpg &>/dev/null && [ -n "${GPG_KEY_ID:-}" ]; then
        echo -e "\n${BOLD}🔐 Signing ISO...${NC}"
        gpg --batch --yes --detach-sign \
            --default-key "$GPG_KEY_ID" \
            "$iso_path" 2>/dev/null || echo "  ⚠ Signing skipped (no key)"
    fi
}

# ─── Verify ISO ────────────────────────────────────────────────────

verify_iso() {
    local iso_name="solus-${EDITION}-${VERSION}-${VARIANT}.iso"
    local iso_path="${OUTPUT_DIR}/${iso_name}"
    
    echo -e "\n${BOLD}🔍 Verifying ISO...${NC}"
    
    # Check size
    local size=$(stat --format=%s "$iso_path" 2>/dev/null || echo 0)
    echo "  Size: $(numfmt --to=iec $size)"
    
    # Verify checksum
    cd "$OUTPUT_DIR"
    sha256sum -c "${iso_name}.sha256" 2>/dev/null && \
        echo -e "  ${GREEN}✅ Checksum verified${NC}" || \
        echo -e "  ${RED}❌ Checksum mismatch${NC}"
    
    # Check ISO structure
    if command -v isoinfo &>/dev/null; then
        isoinfo -d -i "$iso_path" 2>/dev/null | head -10
    fi
}

# ─── Cleanup ───────────────────────────────────────────────────────

cleanup() {
    echo -e "\n${BOLD}🧹 Cleaning up...${NC}"
    rm -rf "$WORK_DIR"
    echo "  Removed: $WORK_DIR"
}

# ─── Main ──────────────────────────────────────────────────────────

main() {
    echo ""
    echo -e "${SOLUS_AMBER}┌─────────────────────────────────────────────────┐${NC}"
    echo -e "${SOLUS_AMBER}│  ☀️  Solus Linux ISO Build Pipeline            │${NC}"
    echo -e "${SOLUS_AMBER}│  Edition: ${EDITION}  Variant: ${VARIANT}            │${NC}"
    echo -e "${SOLUS_AMBER}│  Profile: ${PROFILE}  Version: ${VERSION}            │${NC}"
    echo -e "${SOLUS_AMBER}└─────────────────────────────────────────────────┘${NC}"
    echo ""
    
    check_prereqs
    setup_workdir
    prepare_kickstart
    build_rootfs
    create_iso
    sign_iso
    verify_iso
    cleanup
    
    echo ""
    echo -e "${SOLUS_AMBER}════════════════════════════════════════════════════${NC}"
    echo -e "${SOLUS_AMBER}  🎉  Solus Linux ISO Build Complete!${NC}"
    echo -e "${SOLUS_AMBER}════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  📀 ISO: ${OUTPUT_DIR}/solus-${EDITION}-${VERSION}-${VARIANT}.iso"
    echo "  📏 Size: $(du -h "${OUTPUT_DIR}"/*.iso 2>/dev/null | cut -f1)"
    echo "  🔑 SHA256: ${OUTPUT_DIR}/*.sha256"
    echo ""
    echo "  To write to USB:"
    echo "    sudo dd if=${OUTPUT_DIR}/solus-${EDITION}-${VERSION}-${VARIANT}.iso of=/dev/sdX bs=4M status=progress"
    echo "    sync"
    echo ""
}

main "$@"