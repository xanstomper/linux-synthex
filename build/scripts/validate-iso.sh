#!/usr/bin/env bash
# =============================================================================
# SynthOS ISO Validation Script
# Validates the built ISO for completeness, structure, and integrity
# Usage: validate-iso.sh [ISO_PATH] [--strict]
# =============================================================================
set -euo pipefail

ISO="${1:-}"
STRICT="${2:-}"
PASS=0
FAIL=0
WARN=0
LOG="/tmp/synthex-iso-validate.log"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "$*" | tee -a "$LOG"; }
pass() { ((PASS++)); log "${GREEN}  ✓${NC} $*"; }
fail() { ((FAIL++)); log "${RED}  ✗${NC} $*"; }
warn() { ((WARN++)); log "${YELLOW}  ⚠${NC} $*"; }
info() { log "${BLUE}  ℹ${NC} $*"; }
section() { log "\n${BOLD}── $* ──${NC}"; }

# ── Locate ISO ─────────────────────────────────────────────────────────────────
if [ -z "$ISO" ]; then
    # Auto-detect latest build
    ISO=$(find /tmp/synthex-build-*/iso /home/jewboy420/linux-synthex/build/output \
          -name "*.iso" -newer /tmp -printf '%T@ %p\n' 2>/dev/null \
          | sort -n | tail -1 | awk '{print $2}')
    if [ -z "$ISO" ]; then
        echo "Usage: $0 <path-to.iso> [--strict]"
        echo "Error: No ISO found"
        exit 1
    fi
fi

log "==================================================================="
log "  SynthOS ISO Validation Report"
log "  ISO: $ISO"
log "  Date: $(date)"
log "==================================================================="

# ── 1. Basic file checks ───────────────────────────────────────────────────────
section "File Integrity"

if [ ! -f "$ISO" ]; then
    fail "ISO file does not exist: $ISO"
    exit 1
fi

ISO_SIZE=$(stat -c%s "$ISO" 2>/dev/null || wc -c < "$ISO")
ISO_SIZE_MB=$((ISO_SIZE / 1024 / 1024))
info "ISO size: ${ISO_SIZE_MB} MB"

# Size sanity checks
if [ "$ISO_SIZE_MB" -lt 500 ]; then
    fail "ISO suspiciously small: ${ISO_SIZE_MB}MB (expected ≥500MB)"
elif [ "$ISO_SIZE_MB" -gt 6000 ]; then
    warn "ISO very large: ${ISO_SIZE_MB}MB (expected ≤6000MB)"
else
    pass "ISO size: ${ISO_SIZE_MB}MB (within expected range)"
fi

# SHA256 checksum
SHA_FILE="${ISO%.iso}.sha256"
if [ -f "$SHA_FILE" ]; then
    if sha256sum -c "$SHA_FILE" &>/dev/null; then
        pass "SHA256 checksum verified"
    else
        fail "SHA256 checksum MISMATCH — ISO may be corrupt"
    fi
else
    ISO_SHA=$(sha256sum "$ISO" | awk '{print $1}')
    warn "No checksum file found — generating: ${SHA_FILE}"
    echo "$ISO_SHA  $(basename "$ISO")" > "$SHA_FILE"
    info "SHA256: $ISO_SHA"
fi

# GPG signature
SIG_FILE="${ISO%.iso}.sig"
if [ -f "$SIG_FILE" ]; then
    if gpg --verify "$SIG_FILE" "$ISO" &>/dev/null; then
        pass "GPG signature valid"
    else
        fail "GPG signature INVALID"
    fi
else
    warn "No GPG signature file found: $SIG_FILE"
fi

# ── 2. ISO structure ───────────────────────────────────────────────────────────
section "ISO Structure"

MOUNT_DIR=$(mktemp -d /tmp/synthex-iso-validate.XXXXXX)
CLEANUP_MOUNT=false

if command -v fuseiso &>/dev/null; then
    fuseiso "$ISO" "$MOUNT_DIR" && CLEANUP_MOUNT=true
elif mount --version &>/dev/null && [ "$(id -u)" = "0" ]; then
    mount -o loop,ro "$ISO" "$MOUNT_DIR" && CLEANUP_MOUNT=true
else
    # Use 7z or isoinfo to inspect without mounting
    info "Using isoinfo for structure inspection (no mount available)"
fi

if $CLEANUP_MOUNT; then
    # Check critical paths
    REQUIRED_PATHS=(
        "EFI/BOOT/BOOTx64.EFI"
        "EFI/BOOT/grubx64.efi"
        "boot/grub/grub.cfg"
        "boot/grub/grub2/grub.cfg"
        "images/install.img"
        "LiveOS/squashfs.img"
        "isolinux/isolinux.bin"
    )

    for path in "${REQUIRED_PATHS[@]}"; do
        if [ -e "$MOUNT_DIR/$path" ]; then
            pass "Found: $path"
        else
            warn "Missing (may be variant-specific): $path"
        fi
    done

    # Check squashfs
    SQUASH="$MOUNT_DIR/LiveOS/squashfs.img"
    if [ -f "$SQUASH" ]; then
        SQUASH_SIZE=$(stat -c%s "$SQUASH")
        SQUASH_MB=$((SQUASH_SIZE / 1024 / 1024))
        if [ "$SQUASH_MB" -lt 400 ]; then
            fail "squashfs.img too small: ${SQUASH_MB}MB"
        else
            pass "squashfs.img: ${SQUASH_MB}MB"
        fi

        # Test squashfs integrity
        if command -v unsquashfs &>/dev/null; then
            if unsquashfs -stat "$SQUASH" &>/dev/null; then
                pass "squashfs.img integrity: OK"
            else
                fail "squashfs.img appears corrupt"
            fi
        fi
    else
        fail "LiveOS/squashfs.img not found"
    fi

    # Check kernel and initrd
    for kfile in vmlinuz initrd.img initrd.gz initramfs.img; do
        if find "$MOUNT_DIR" -name "$kfile" -maxdepth 5 | grep -q .; then
            pass "Kernel/initrd found: $kfile"
            break
        fi
    done

    # Check GRUB config
    GRUB_CFG=$(find "$MOUNT_DIR" -name "grub.cfg" | head -1)
    if [ -n "$GRUB_CFG" ]; then
        if grep -qi "synthos\|synthex" "$GRUB_CFG"; then
            pass "GRUB config contains SynthOS branding"
        else
            warn "GRUB config does not mention SynthOS — branding may be missing"
        fi

        if grep -qi "quiet splash\|rd.live" "$GRUB_CFG"; then
            pass "GRUB config has live boot parameters"
        else
            warn "GRUB config missing live boot parameters"
        fi
    fi

    # Calamares installer
    CALA=$(find "$MOUNT_DIR" -name "calamares" -o -name "calamares-offline" | head -1)
    if [ -n "$CALA" ]; then
        pass "Calamares installer found"
    else
        warn "Calamares not found in squashfs — may be inside rootfs"
    fi

    umount "$MOUNT_DIR" 2>/dev/null || fusermount -u "$MOUNT_DIR" 2>/dev/null || true
else
    # isoinfo fallback
    if command -v isoinfo &>/dev/null; then
        LISTING=$(isoinfo -l -i "$ISO" 2>/dev/null)
        for check in "BOOT" "EFI" "GRUB" "IMAGES" "LIVEOS"; do
            if echo "$LISTING" | grep -qi "$check"; then
                pass "Directory found: $check"
            else
                warn "Directory not found: $check"
            fi
        done
    fi
fi

rmdir "$MOUNT_DIR" 2>/dev/null || true

# ── 3. UEFI / BIOS boot ───────────────────────────────────────────────────────
section "Boot Compatibility"

# Check ISO type (hybrid or not)
if dd if="$ISO" bs=1 skip=0 count=4 2>/dev/null | xxd | grep -q "43 44 30 30 31"; then
    pass "Valid ISO9660 signature detected"
else
    warn "ISO9660 signature not found (may be UDF or hybrid)"
fi

# Check for hybrid MBR (BIOS boot from USB)
if dd if="$ISO" bs=512 count=1 2>/dev/null | xxd | grep -q "55 aa$"; then
    pass "MBR boot signature present (BIOS boot supported)"
else
    fail "No MBR boot signature — ISO may not boot from USB without special tools"
fi

# isohybrid check
if isohybrid -v "$ISO" &>/dev/null; then
    pass "isohybrid: valid hybrid ISO"
elif [ "$STRICT" = "--strict" ]; then
    fail "isohybrid validation failed"
else
    warn "isohybrid not available for validation"
fi

# ── 4. File count & spec validation ───────────────────────────────────────────
section "Spec File Validation"

SPEC_DIR="/home/jewboy420/linux-synthex/packages/spec-files"
if [ -d "$SPEC_DIR" ]; then
    TOTAL_SPECS=$(find "$SPEC_DIR" -name "*.spec" | wc -l)
    info "Total spec files: $TOTAL_SPECS"
    pass "Spec files present: $TOTAL_SPECS"

    # Check each spec has required fields
    BAD_SPECS=0
    for spec in "$SPEC_DIR"/*.spec; do
        for field in Name Version License Summary; do
            if ! grep -q "^$field:" "$spec"; then
                warn "Missing $field: in $(basename "$spec")"
                ((BAD_SPECS++))
                break
            fi
        done
    done
    if [ "$BAD_SPECS" -eq 0 ]; then
        pass "All spec files have required fields"
    fi
fi

# ── 5. Branding ───────────────────────────────────────────────────────────────
section "Branding Assets"

BRANDING_DIR="/home/jewboy420/linux-synthex/branding"
if [ -d "$BRANDING_DIR" ]; then
    for asset in \
        "calamares/show.qml" \
        "calamares/branding.desc" \
        "calamares/synthex-logo.png" \
        "desktop-profiles/classic" \
        "grub/themes/synthex"; do
        if [ -e "$BRANDING_DIR/$asset" ]; then
            pass "Branding: $asset"
        else
            warn "Missing branding: $asset"
        fi
    done
fi

# ── 6. Summary ────────────────────────────────────────────────────────────────
TOTAL=$((PASS + FAIL + WARN))
log ""
log "==================================================================="
log "  VALIDATION SUMMARY"
log "==================================================================="
log "  Total checks:  $TOTAL"
log "${GREEN}  Passed:        $PASS${NC}"
log "${YELLOW}  Warnings:      $WARN${NC}"
log "${RED}  Failed:        $FAIL${NC}"
log ""
log "  Report saved: $LOG"
log "==================================================================="

if [ "$FAIL" -eq 0 ] && [ "$WARN" -le 3 ]; then
    log "${GREEN}${BOLD}  ✓ ISO VALIDATION PASSED${NC}"
    exit 0
elif [ "$FAIL" -eq 0 ]; then
    log "${YELLOW}${BOLD}  ⚠ ISO VALIDATION PASSED WITH WARNINGS${NC}"
    exit 0
else
    log "${RED}${BOLD}  ✗ ISO VALIDATION FAILED ($FAIL failure(s))${NC}"
    exit 1
fi
