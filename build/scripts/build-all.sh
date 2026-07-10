#!/usr/bin/env bash
# =============================================================================
# SynthOS — Build All Editions
# Builds every ISO edition in sequence (or in parallel with --parallel)
# Usage: ./build-all.sh [--parallel] [--editions "plasma gaming gnome"]
#        [--version X.Y] [--sign] [--upload]
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ALL_EDITIONS="plasma gaming gnome hyprland minimal"
EDITIONS="${EDITIONS:-$ALL_EDITIONS}"
PARALLEL=false
SIGN=false
UPLOAD=false
VERSION="${VERSION:-2026.10}"
OUTPUT_DIR="${OUTPUT_DIR:-$REPO_ROOT/build/out}"
LOG_DIR="$OUTPUT_DIR/logs"
START=$(date +%s)

G='\e[32m'; Y='\e[33m'; R='\e[31m'; B='\e[1m'; NC='\e[0m'
log()  { echo -e "${G}[ALL]${NC}  $*"; }
warn() { echo -e "${Y}[WARN]${NC} $*" >&2; }
fail() { echo -e "${R}[FAIL]${NC} $*" >&2; exit 1; }
hr()   { echo "────────────────────────────────────────────────────────────────────────"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --parallel)  PARALLEL=true; shift ;;
        --sign)      SIGN=true; shift ;;
        --upload)    UPLOAD=true; shift ;;
        --version)   VERSION="$2"; shift 2 ;;
        --editions)  EDITIONS="$2"; shift 2 ;;
        --output)    OUTPUT_DIR="$2"; shift 2 ;;
        -h|--help)   grep '^# ' "$0" | head -8 | sed 's/^# //'; exit 0 ;;
        *) fail "Unknown arg: $1" ;;
    esac
done

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"
export VERSION OUTPUT_DIR SIGN

hr
log "${B}SynthOS Build-All — Version $VERSION${NC}"
log "Editions: $EDITIONS"
log "Parallel: $PARALLEL"
log "Output:   $OUTPUT_DIR"
hr

RESULTS=()
build_edition() {
    local ed="$1"
    local log="$LOG_DIR/${ed}.log"
    log "Starting edition: $ed"
    if EDITION="$ed" bash "$SCRIPT_DIR/build-iso.sh" "$ed" > "$log" 2>&1; then
        log "${G}✓ $ed — complete${NC}"
        RESULTS+=("PASS:$ed")
    else
        warn "✗ $ed — FAILED (see $log)"
        RESULTS+=("FAIL:$ed")
    fi
}

if $PARALLEL; then
    pids=()
    for ed in $EDITIONS; do
        build_edition "$ed" &
        pids+=($!)
    done
    for pid in "${pids[@]}"; do wait "$pid" || true; done
else
    for ed in $EDITIONS; do
        build_edition "$ed"
    done
fi

hr
ELAPSED=$(( $(date +%s) - START ))
log "${B}Build Summary${NC}  (${ELAPSED}s total)"
hr
PASS=0; FAIL=0
for r in "${RESULTS[@]}"; do
    status="${r%%:*}"; edition="${r##*:}"
    if [[ "$status" == "PASS" ]]; then
        echo -e "  ${G}PASS${NC}  $edition"
        ((PASS++))
    else
        echo -e "  ${R}FAIL${NC}  $edition"
        ((FAIL++))
    fi
done
echo ""
log "Passed: $PASS / $((PASS+FAIL))"
hr

if $UPLOAD && [ -n "${UPLOAD_TARGET:-}" ]; then
    log "Uploading ISOs to $UPLOAD_TARGET …"
    rsync -avP --progress "$OUTPUT_DIR/"*.iso "$UPLOAD_TARGET/" || warn "Upload failed"
fi

[ $FAIL -eq 0 ] && exit 0 || exit 1
