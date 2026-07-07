#!/usr/bin/env bash
# build-all-rpms.sh — Build all Synthex RPM packages from spec files
# Usage: ./build-all-rpms.sh [--sign] [--noarch-only]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILDROOT="${BUILDROOT:-$ROOT/build/rpmbuild}"
REPO_DIR="${REPO_DIR:-$ROOT/build/repo}"
SIGN=false
NOARCH_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --sign) SIGN=true ;;
        --noarch-only) NOARCH_ONLY=true ;;
    esac
done

echo "📦 SynthOS — Building all RPM packages"
echo "  Build root: $BUILDROOT"
echo "  Repo dir:   $REPO_DIR"
echo ""

# Set up RPM build tree
echo "🔧 Setting up RPM build tree..."
mkdir -p "$BUILDROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "$REPO_DIR"/{x86_64,noarch}

# Copy spec files
echo "📋 Copying spec files..."
cp "$ROOT"/packages/spec-files/*.spec "$BUILDROOT/SPECS/"

# Copy source files to SOURCES
echo "📁 Copying source files..."
# Shell tools
cp "$ROOT/src/synthex-ujust/ujust"                              "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-nvidia-installer/synthex-nvidia-installer"  "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-codec-installer/synthex-codec-installer"    "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-kernel-manager/synthex-kernel-manager"      "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-service-manager/synthex-service-manager"    "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-log-viewer/synthex-log-viewer"              "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-locale-setup/synthex-locale-setup"          "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-cachy-tuning/apply-cachy-tuning.sh"       "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-cachy-tuning/tuned-profiles/synthex-gaming/tuned.conf"   "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-cachy-tuning/tuned-profiles/synthex-balanced/tuned.conf" "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-cachy-tuning/tuned-profiles/synthex-powersave/tuned.conf" "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-cachy-tuning/ananicy-rules/synthex-rules.conf"           "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-nobara-fixes/apply-nobara-fixes.sh"      "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-welcome/synthex-welcome"                   "$BUILDROOT/SOURCES/"
cp "$ROOT/desktop/applications/synthex-welcome.desktop"        "$BUILDROOT/SOURCES/"
cp "$ROOT/src/synthex-installer/post-install.sh"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/src/synthex-installer/hardware-detect.sh"            "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/src/synthex-installer/apply-theme.sh"                "$BUILDROOT/SOURCES/" 2>/dev/null || true

# System config sources (for synthex-system-config.spec)
cp "$ROOT/configs/dracut/dracut-synthex.conf"                   "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/grub/grub-default"                          "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/sddm/sddm-synthex.conf"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/plymouth/plymouthd-synthex.conf"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/networkmanager/nm-synthex.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/firewalld/synthex.xml"                        "$BUILDROOT/SOURCES/synthex-firewalld.xml" 2>/dev/null || true
cp "$ROOT/configs/flatpak/flathub.flatpakrepo"                "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/flatpak/synthex.flatpakrepo"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/snapper/snapper-root.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/sudoers/synthex-sudoers"                      "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/polkit/49-synthex-nopasswd.rules"             "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/dnf/dnf-automatic.conf"                     "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/journald/journald-synthex.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/timesyncd/timesyncd-synthex.conf"             "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/synthex-blacklist.conf"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/synthex-nvidia.conf"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/synthex-audio.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/synthex-thinkpad.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/crypttab/crypttab"                          "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/locale.conf"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/vconsole.conf"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/synthex-locale-gen"                    "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/secureboot/synthex-shim.conf"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/btrfs/btrfs-scrub-timer.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/btrfs/synthex-btrfs-balance"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/synthex-live-setup.service"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/live-setup.sh"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/install-synthex.desktop"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Calamares branding sources
cp "$ROOT/branding/calamares/branding.desc"                   "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/calamares-branding/show.qml"                "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/branding/logo/synthex-logo.svg"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Gaming optimization sources
cp "$ROOT/configs/gaming/limits.conf"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/gaming/sysctl-gaming.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/gaming/environment-gaming.conf"             "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Kernel sources (config + patches)
cp "$ROOT/kernel/configs/synthex-x86_64-defconfig"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/kernel/patches/"*.patch                             "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Theme sources
cp "$ROOT/branding/theme/synthex-gtk4/gtk.css"                  "$BUILDROOT/SOURCES/gtk4.css" 2>/dev/null || true
cp "$ROOT/branding/theme/synthex-gtk3/gtk.css"                  "$BUILDROOT/SOURCES/gtk3.css" 2>/dev/null || true
cp "$ROOT/branding/theme/synthex-sddm-theme/Main.qml"           "$BUILDROOT/SOURCES/sddm-Main.qml" 2>/dev/null || true
cp "$ROOT/branding/theme/synthex-sddm-theme/metadata.desktop"   "$BUILDROOT/SOURCES/sddm-metadata.desktop" 2>/dev/null || true
cp "$ROOT/branding/theme/synthex-sddm-theme/theme.conf"         "$BUILDROOT/SOURCES/sddm-theme.conf" 2>/dev/null || true

# Hyprland sources
cp "$ROOT/desktop/hyprland/waybar-style.css"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/desktop/hyprland/wlogout-layout"                    "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/desktop/hyprland/wlogout-style.css"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
# Rust daemon binaries (from workspace)
for binary in synthex-hwdaemon synthex-desktopd synthex-stored synthex-gpu-setupd synthex-cli \
              synthex-system-daemon synthex-ai-daemon synthex-installer-detect synthex-control-center; do
    src_bin="target/release/$binary"
    [ -f "$ROOT/$src_bin" ] && cp "$ROOT/$src_bin" "$BUILDROOT/SOURCES/"
done

# AI daemon systemd unit
cp "$ROOT/systemd/synthex-ai-daemon.service" "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Installer hook script
cp "$ROOT/installer/scripts/synthex-installer-hook" "$BUILDROOT/SOURCES/" 2>/dev/null || true

echo "  Source files copied."
echo ""

# Build each spec
SPECS=$(ls "$BUILDROOT/SPECS"/*.spec | sort)
TOTAL=$(echo "$SPECS" | wc -l)
CURRENT=0
BUILT=0
FAILED=0
FAILED_SPECS=""

echo "🔨 Building $TOTAL spec files..."
echo ""

for spec in $SPECS; do
    CURRENT=$((CURRENT + 1))
    name=$(basename "$spec" .spec)

    if $NOARCH_ONLY; then
        grep -q 'BuildArch.*noarch' "$spec" || { echo "  [$CURRENT/$TOTAL] SKIP $name (not noarch)"; continue; }
    fi

    printf "  [%d/%d] Building %-35s ... " "$CURRENT" "$TOTAL" "$name"

    if rpmbuild -bb \
        --define "_topdir $BUILDROOT" \
        --define "_rpmdir $BUILDROOT/RPMS" \
        "$spec" > "$BUILDROOT/build-$name.log" 2>&1; then
        echo "OK"
        BUILT=$((BUILT + 1))
    else
        echo "FAILED"
        FAILED=$((FAILED + 1))
        FAILED_SPECS="$FAILED_SPECS $name"
    fi
done

echo ""
echo "Results: $BUILT built, $FAILED failed"

if [ $FAILED -gt 0 ]; then
    echo "Failed specs:$FAILED_SPECS"
    echo "Check: $BUILDROOT/build-*.log"
fi

# Collect RPMs into repo
echo ""
echo "Collecting RPMs into repository..."
find "$BUILDROOT/RPMS" -name '*.rpm' -exec cp {} "$REPO_DIR/x86_64/" \; 2>/dev/null || true
for rpm in "$REPO_DIR/x86_64"/*.noarch.rpm; do
    [ -f "$rpm" ] && mv "$rpm" "$REPO_DIR/noarch/" 2>/dev/null || true
done

RPM_COUNT=$(find "$REPO_DIR" -name '*.rpm' | wc -l)
echo "  $RPM_COUNT RPMs collected."

# Sign packages
if $SIGN && [ $RPM_COUNT -gt 0 ]; then
    echo ""
    echo "Signing packages..."
    export GNUPGHOME="${GPG_HOME:-$HOME/.gnupg-synthex}"
    find "$REPO_DIR" -name '*.rpm' -exec rpm --addsign {} \; 2>/dev/null || \
        echo "  Sign failed — run generate-gpg-keys.sh first"
fi

# Create repository metadata
echo ""
echo "Creating repository metadata..."
createrepo_c "$REPO_DIR" 2>/dev/null || createrepo "$REPO_DIR" 2>/dev/null || \
    echo "  Install createrepo_c: sudo dnf install createrepo_c"

echo ""
echo "Build complete!"
echo "  Repository: $REPO_DIR"
echo "  RPMs: $RPM_COUNT"
