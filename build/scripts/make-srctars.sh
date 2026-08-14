#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  make-srctars.sh — generate all Source0 inputs the specs need ║
# ║  straight from the repo (no network, reproducible).           ║
# ╚══════════════════════════════════════════════════════════════╝
# Usage: build/scripts/make-srctars.sh [VERSION] [OUTDIR]
#   VERSION defaults to the VERSION file (or 2026.10)
#   OUTDIR  defaults to ~/rpmbuild/SOURCES
#
# Outputs
# ───────
# 1. synthex-repo-<VERSION>.tar.gz — the monorepo tarball (topdir
#    synthex-repo-<VERSION>). Every first-party spec uses it as Source0
#    with `%setup -q -n synthex-repo-%{version}`, so any spec can reach
#    any repo path (Cargo workspace builds included).
# 2. Single-file sources (bare Source0 basenames) copied verbatim.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="${1:-$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo 2026.10)}"
OUTDIR="${2:-$HOME/rpmbuild/SOURCES}"
mkdir -p "$OUTDIR"
cd "$REPO_ROOT"

# ── 1. Monorepo tarball ────────────────────────────────────────────────────
REPO_TAR="$OUTDIR/synthex-repo-$VERSION.tar.gz"
tar czf "$REPO_TAR" \
    --transform "s|^|synthex-repo-$VERSION/|" \
    --exclude='.git' --exclude='target' --exclude='.venv' \
    --exclude='.claude' --exclude='.commandcode' \
    --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='build/out' --exclude='build/rpms' --exclude='build/repo' \
    --exclude='build/srpms' --exclude='build/rpmbuild' --exclude='*.log' \
    Cargo.toml Cargo.lock VERSION Makefile Justfile \
    src aether desktop branding configs systemd services safety security \
    dbus docs installer kernel udev etc packages/groups \
    2>/dev/null || \
tar czf "$REPO_TAR" \
    --transform "s|^|synthex-repo-$VERSION/|" \
    --exclude='.git' --exclude='target' --exclude='.venv' \
    --exclude='.claude' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='build/out' --exclude='build/rpms' --exclude='build/repo' \
    --exclude='*.log' \
    $(ls -d */ | grep -vE '^(\.git|target|\.venv|\.claude|\.commandcode)$')
echo "  ✓ synthex-repo-$VERSION.tar.gz ($(du -h "$REPO_TAR" | cut -f1))"

# ── 2. Single-file sources (bare Source0 basenames) ───────────────────────
declare -A SINGLE=(
    [ujust]=src/synthex-ujust/ujust
    [synthex-welcome]=src/synthex-welcome/synthex-welcome
    [synthex-service-manager]=src/synthex-service-manager/synthex-service-manager
    [synthex-log-viewer]=src/synthex-log-viewer/synthex-log-viewer
    [synthex-locale-setup]=src/synthex-locale-setup/synthex-locale-setup
    [synthex-kernel-manager]=src/synthex-kernel-manager/synthex-kernel-manager
    [synthex-nvidia-installer]=src/synthex-nvidia-installer/synthex-nvidia-installer
    [synthex.repo]=packages/synthex-repos/synthex.repo
    [limits.conf]=security/hardening/limits.conf
    [sysctl.conf]=security/hardening/sysctl.conf
    [auditd.rules]=security/hardening/auditd.rules
    [security-deploy.sh]=security/scripts/security-deploy.sh
    [dracut-synthex.conf]=configs/dracut/dracut-synthex.conf
    [apply-nobara-fixes.sh]=src/synthex-nobara-fixes/apply-nobara-fixes.sh
    [apply-cachy-tuning.sh]=src/synthex-cachy-tuning/apply-cachy-tuning.sh
)
for name in "${!SINGLE[@]}"; do
    src="${SINGLE[$name]}"
    if [ -f "$src" ]; then
        cp -f "$src" "$OUTDIR/$name"
        echo "  ✓ $name"
    else
        echo "  ! MISSING single-file source: $name ← $src" >&2
    fi
done

echo "──────────────────────────────────────────────"
echo "  sources ready → $OUTDIR"
