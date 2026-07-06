#!/usr/bin/env bash
# setup-build-env.sh — Set up the RPM build environment for Solus
# Installs all build dependencies needed to compile specs into RPMs
set -euo pipefail

echo "🔧 Setting up Solus RPM build environment..."
echo ""

# ─── Install build tools ───────────────────────────────────────────────
echo "📦 Installing build tools..."
BUILD_TOOLS=(
    rpm-build
    rpmdevtools
    createrepo_c
    dnf5
    dnf5-plugins
    fedpkg
    mock
    rpmlint
)

sudo dnf install -y "${BUILD_TOOLS[@]}" 2>/dev/null || {
    echo "  Some packages may not be available — this is OK on non-Fedora"
}

echo "  Build tools installed."

# ─── Set up RPM build tree ─────────────────────────────────────────────
echo ""
echo "📁 Setting up RPM build tree..."
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILDROOT="$ROOT/build/rpmbuild"

mkdir -p "$BUILDROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Configure ~/.rpmmacros
if ! grep -q '_topdir' "$HOME/.rpmmacros" 2>/dev/null; then
    echo "%_topdir $BUILDROOT" >> "$HOME/.rpmmacros"
    echo "%_smp_mflags -j$(nproc)" >> "$HOME/.rpmmacros"
fi

echo "  Build tree at: $BUILDROOT"

# ─── Generate GPG keys ─────────────────────────────────────────────────
echo ""
echo "🔐 Setting up GPG signing..."
if [ ! -f "$HOME/.gnupg-solus/RPM-GPG-KEY-solus" ]; then
    "$ROOT/scripts/generate-gpg-keys.sh"
else
    echo "  GPG keys already exist."
fi

echo ""
echo "✅ Build environment ready!"
echo "  Next: ./scripts/build-all-rpms.sh --sign"
