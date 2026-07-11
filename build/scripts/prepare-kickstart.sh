#!/usr/bin/env bash
# =============================================================================
# SynthOS Kickstart Preparation Script
# Validates, patches, and stages kickstart files for livemedia-creator
# Usage: ./prepare-kickstart.sh [EDITION] [--validate-only] [--output DIR]
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KS_DIR="$REPO_ROOT/build/kickstart"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/build/out/kickstart}"
EDITION="${1:-all}"
VALIDATE_ONLY=false
VERSION="${VERSION:-2026.10}"

G='\e[32m'; Y='\e[33m'; R='\e[31m'; NC='\e[0m'
log()  { echo -e "${G}[KS]${NC}  $*"; }
warn() { echo -e "${Y}[WARN]${NC} $*" >&2; }
fail() { echo -e "${R}[FAIL]${NC} $*" >&2; exit 1; }

[[ "${2:-}" == "--validate-only" ]] && VALIDATE_ONLY=true
mkdir -p "$OUTPUT_DIR"

# ── Validation rules ──────────────────────────────────────────────────────────
validate_ks() {
    local ks="$1" name="$2"
    local errors=0

    # 1. Required sections
    for section in "%packages" "%post" "%end"; do
        grep -q "$section" "$ks" || { warn "$name: missing $section"; (( errors++ )) || true; }
    done

    # 2. Must have synthex-core
    grep -q "^synthex-core" "$ks" || { warn "$name: missing synthex-core package"; (( errors++ )) || true; }

    # 3. Must have grub2 or bootloader
    grep -qiE "^grub2|^bootloader" "$ks" || { warn "$name: no bootloader package"; (( errors++ )) || true; }

    # 4. Must have synthex-kernel
    grep -q "^synthex-kernel" "$ks" || { warn "$name: missing synthex-kernel"; (( errors++ )) || true; }

    # 5. Must have plymouth
    grep -qE "^plymouth$|^plymouth-" "$ks" || { warn "$name: missing plymouth"; (( errors++ )) || true; }

    # 6. ksvalidate (if available)
    if command -v ksvalidate &>/dev/null; then
        ksvalidate "$ks" 2>/dev/null || { warn "$name: ksvalidate reported errors"; (( errors++ )) || true; }
    fi

    return $errors
}

# ── Template substitution ─────────────────────────────────────────────────────
patch_ks() {
    local src="$1" dst="$2"
    sed \
        -e "s|@VERSION@|$VERSION|g" \
        -e "s|@REPO_ROOT@|$REPO_ROOT|g" \
        -e "s|@BUILD_DATE@|$(date -u +%Y-%m-%d)|g" \
        -e "s|@BUILD_HOST@|$(hostname -f 2>/dev/null || echo build-host)|g" \
        "$src" > "$dst"
}

# ── Main loop ─────────────────────────────────────────────────────────────────
PASS=0; FAIL=0; ALL_KS=()

if [[ "$EDITION" == "all" ]]; then
    ALL_KS=( "$KS_DIR"/*.ks )
else
    ALL_KS=( "$KS_DIR/synthex-${EDITION}.ks" )
fi

for ks in "${ALL_KS[@]}"; do
    [ -f "$ks" ] || { warn "Not found: $ks"; (( FAIL++ )) || true; continue; }
    name=$(basename "$ks" .ks)
    dst="$OUTPUT_DIR/$name-$(date +%Y%m%d).ks"

    log "Processing $name …"

    # Validate
    err_count=0
    validate_ks "$ks" "$name"; err_count=$?

    if [ $err_count -gt 0 ]; then
        warn "$name: $err_count validation errors"
        (( FAIL++ )) || true
    else
        log "  ✓ Validated"
        (( PASS++ )) || true
    fi

    # Patch + stage (unless validate-only)
    if ! $VALIDATE_ONLY; then
        patch_ks "$ks" "$dst"
        log "  ✓ Staged → $dst"
    fi
done

echo ""
log "Done — Passed: $PASS / $((PASS+FAIL))"
[ $FAIL -eq 0 ] && exit 0 || exit 1
