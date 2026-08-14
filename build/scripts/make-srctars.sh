#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  make-srctars.sh — generate every Source0 tarball the specs   ║
# ║  need, straight from the repo (no network, reproducible).     ║
# ╚══════════════════════════════════════════════════════════════╝
# Usage: build/scripts/make-srctars.sh [VERSION] [OUTDIR]
#   VERSION defaults to the VERSION file (or 2026.10)
#   OUTDIR  defaults to ~/rpmbuild/SOURCES
#
# Strategy
# ────────
# * Workspace Rust crates (members of the root Cargo workspace) use
#   `workspace = true` deps, so their Source0 is a FULL WORKSPACE tarball
#   (topdir %{name}-%{version}) and specs run plain `cargo build --release`,
#   which resolves every member correctly.
# * Standalone crates (synthex-temporal, aether/*) get their own dir tar.
# * Python/shell components tar their src/<name> dir.
# * desktop/, branding/, installer/, configs/ tar as whole trees.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="${1:-$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo 2026.10)}"
OUTDIR="${2:-$HOME/rpmbuild/SOURCES}"
mkdir -p "$OUTDIR"

cd "$REPO_ROOT"
made=0

tar_make() {  # tar_make <topdir-name> <out-tarname> <path...>
    local top="$1" out="$OUTDIR/$2" outname="$2"; shift 2
    # tolerate missing optional paths; fail only if ALL inputs are missing
    local paths=() p
    for p in "$@"; do
        if compgen -G "$p" >/dev/null; then paths+=("$p"); fi
    done
    if [[ ${#paths[@]} -eq 0 ]]; then
        echo "  ! SKIP $outname (no source paths exist: $*)" >&2
        return 0
    fi
    tar czf "$out" --transform "s|^|$top/|" --exclude='__pycache__' \
        --exclude='.git' --exclude='target' "${paths[@]}"
    made=$((made+1))
}

# ── 1. Full-workspace tarball for every workspace-member crate spec ────────
mapfile -t MEMBERS < <(sed -n '/^\[workspace\]/,/^\[/p' Cargo.toml | grep -oP '"\Ksrc/[^"]+' | sort -u)
# spec name = crate dir basename with any -rs / rust-tools suffix normalization handled below
WORKSPACE_SPECS=()
for m in "${MEMBERS[@]}"; do
    name="$(basename "$m")"
    [[ "$name" == rust-tools ]] && continue   # sub-crates handled separately
    # crate → spec name mapping (spec may append -rs)
    for cand in "$name" "${name%-rs}" "${name#synthex-}"; do
        [[ -f "packages/spec-files/$cand.spec" ]] && WORKSPACE_SPECS+=("$cand|$m") && break
    done
done
# sub-crates of synthex-rust-tools
for sub in pkg update-manager driver-manager; do
    WORKSPACE_SPECS+=("synthex-$sub|src/synthex-rust-tools/synthex-$sub")
done

for entry in "${WORKSPACE_SPECS[@]}"; do
    spec="${entry%%|*}"; srcdir="${entry##*|}"
    [[ -f "packages/spec-files/$spec.spec" ]] || continue
    tar_make "$spec-$VERSION" "$spec-$VERSION.tar.gz" \
        Cargo.toml Cargo.lock src build/scripts
    echo "  ✓ $spec-$VERSION.tar.gz (workspace)"
done

# ── 2. Standalone crates ────────────────────────────────────────────────────
for sc in src/synthex-temporal; do
    name="$(basename "$sc")"
    [[ -f "packages/spec-files/$name.spec" ]] && {
        tar_make "$name-$VERSION" "$name-$VERSION.tar.gz" "$sc"; echo "  ✓ $name (standalone)"; }
done
for w in aether/core aether/sentinel; do
    name="$(basename "$(dirname "$w")")-$(basename "$w")"
    tar_make "$name-$VERSION" "$name-$VERSION.tar.gz" "$w" 2>/dev/null && echo "  ✓ $name" || true
done

# ── 3. Python / shell components (src dirs with their own launcher) ───────
for d in src/synthex-app-manager src/synthex-studio src/synthex-blueprint \
         src/synthex-boot src/synthex-webapp-engine src/synthex-predictive-launch \
         src/synthex-agent src/synthex-ai-hub src/synthex-control-center \
         src/synthex-oobe src/synthex-welcome src/synthex-gaming-center \
         src/synthex-software-center src/synthex-security-dashboard \
         src/synthex-disk-health src/synthex-log-viewer src/synthex-ujust \
         src/synthex-cachy-tuning src/synthex-nvidia-installer \
         src/synthex-codec-installer src/synthex-locale-setup \
         src/synthex-service-manager src/synthex-update-manager \
         src/synthex-kernel-manager src/synthex-hwdaemon src/synthex-desktopd \
         src/synthex-gpu-setupd src/synthex-stored src/synthex-term \
         src/synthex-tray src/synthex-appimage src/synthex-marketplace \
         src/synthex-tour src/synthex-upgrade src/synthex-usb-writer \
         src/synthex-aur src/synthex-input-remapper src/synthex-layout \
         src/synthex-driver-manager src/synthex-firmware src/synthex-vpn \
         src/synthex-neurofeedback src/synthex-timeshift; do
    name="$(basename "$d")"
    [[ -f "packages/spec-files/$name.spec" ]] || continue
    tar_make "$name-$VERSION" "$name-$VERSION.tar.gz" "$d"
    echo "  ✓ $name (component)"
done

# ── 4. Whole-tree tarballs (desktop / branding / installer / configs) ─────
for tree in desktop branding installer configs systemd services safety dbus; do
    tar_make "$tree-$VERSION" "$tree-$VERSION.tar.gz" "$tree"
    echo "  ✓ $tree (tree)"
done

echo "──────────────────────────────────────────────"
echo "  $made source tarballs → $OUTDIR"
