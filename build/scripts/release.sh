#!/usr/bin/env bash
# =============================================================================
# SynthOS Release Script
# Tags the repo, generates checksums, creates the full release artifact set
# =============================================================================
set -euo pipefail

VERSION="${1:-2026.10}"
CODENAME="Ignition"
EDITION="${2:-all}"
OUTPUT="build/release/${VERSION}"

G='\e[32m'; Y='\e[33m'; R='\e[31m'; B='\e[1m'; NC='\e[0m'
log()  { echo -e "${G}[RELEASE]${NC}  $*"; }
warn() { echo -e "${Y}[WARN]${NC}    $*"; }
fail() { echo -e "${R}[FAIL]${NC}    $*" >&2; exit 1; }
step() { echo -e "\n${B}══ $* ══${NC}"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

step "Pre-flight checks"
[ -f "Cargo.toml" ]                   || fail "Must run from repo root"
[ -f "build/kickstart/synthex-plasma.ks" ] || fail "Kickstart files missing"
command -v cargo >/dev/null            || fail "cargo not found"

step "Validate kickstarts"
for ks in build/kickstart/*.ks; do
  name=$(basename "$ks" .ks)
  log "  Validating $name..."
  errs=0
  grep -q "^%packages"                              "$ks" || ((errs++))
  grep -q "^%end"                                   "$ks" || ((errs++))
  grep -qE "^clearpart|^part |^autopart|^zerombr"  "$ks" || ((errs++))
  [ "$errs" -eq 0 ] || fail "KS validation failed: $ks ($errs errors)"
done
log "✓ All kickstart files valid"

step "Build Rust workspace"
log "cargo build --release --workspace..."
cargo build --release --workspace 2>&1 | tail -3
BINARY_COUNT=$(ls target/release/ | grep -v '\.d$\|\.rlib$\|deps\|build\|incremental\|examples' | wc -l)
[ "$BINARY_COUNT" -ge 28 ] || fail "Expected ≥28 binaries, got $BINARY_COUNT"
log "✓ $BINARY_COUNT binaries built"

step "Validate installer modules"
FAIL=0
for py in installer/modules/synthex*/main.py; do
  python3 -m py_compile "$py" || { warn "Syntax error: $py"; FAIL=1; }
done
[ "$FAIL" -eq 0 ] || fail "Installer module syntax errors found"
log "✓ All 9 custom Calamares modules valid"

step "Create release directory"
mkdir -p "$OUTPUT"/{iso,src,checksums}

step "Create source tarballs"
log "Packing source tarballs..."
tar czf "$OUTPUT/src/synthex-installer-${VERSION}.tar.gz" \
    --transform "s|^installer/|synthex-installer-${VERSION}/|" installer/
tar czf "$OUTPUT/src/synthex-branding-${VERSION}.tar.gz" \
    --transform "s|^branding/|synthex-branding-${VERSION}/|" branding/
tar czf "$OUTPUT/src/synthex-desktop-${VERSION}.tar.gz" \
    --transform "s|^desktop/|synthex-desktop-${VERSION}/|" desktop/
log "✓ Source tarballs created in $OUTPUT/src/"

step "Generate ISO(s)"
if [ "$EDITION" = "all" ]; then
  EDITIONS="plasma hyprland gnome gaming minimal"
else
  EDITIONS="$EDITION"
fi

for ed in $EDITIONS; do
  log "Building $ed ISO..."
  if command -v livemedia-creator &>/dev/null; then
    VERSION="$VERSION" EDITION="$ed" \
      OUTPUT_DIR="$OUTPUT/iso" \
      bash build/scripts/build-iso.sh "$ed" 2>&1 | tail -5
  else
    warn "livemedia-creator not found — skipping ISO build for $ed"
    warn "Install: sudo dnf install lorax livemedia-creator"
  fi
done

step "Generate checksums"
if ls "$OUTPUT/iso/"*.iso &>/dev/null; then
  sha256sum "$OUTPUT/iso/"*.iso > "$OUTPUT/checksums/SHA256SUMS"
  log "✓ SHA256SUMS written"

  if command -v gpg &>/dev/null && gpg --list-secret-keys &>/dev/null; then
    gpg --clearsign "$OUTPUT/checksums/SHA256SUMS"
    log "✓ SHA256SUMS.asc (GPG signed)"
  else
    warn "GPG not available — checksums not signed"
  fi
fi

step "Copy release notes"
cp docs/RELEASE-NOTES-${VERSION}.md "$OUTPUT/" 2>/dev/null || \
  warn "Release notes not found: docs/RELEASE-NOTES-${VERSION}.md"

step "Release summary"
echo ""
echo "  Version   : SynthOS ${VERSION} — ${CODENAME}"
echo "  Edition(s): ${EDITIONS}"
echo "  Output    : ${OUTPUT}/"
echo ""
if ls "$OUTPUT/iso/"*.iso &>/dev/null 2>&1; then
  echo "  ISOs:"
  ls -lh "$OUTPUT/iso/"*.iso | awk '{print "    "$5"  "$9}'
  echo ""
fi
echo "  Sources:"
ls -lh "$OUTPUT/src/"*.tar.gz 2>/dev/null | awk '{print "    "$5"  "$9}'
echo ""
log "✓ SynthOS ${VERSION} release complete!"
