#!/usr/bin/env bash
# build-all-rpms.sh — Build all Solus RPM packages from spec files
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

echo "📦 Solus Linux — Building all RPM packages"
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
cp "$ROOT/src/solus-ujust/ujust"                              "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-nvidia-installer/solus-nvidia-installer"  "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-codec-installer/solus-codec-installer"    "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-kernel-manager/solus-kernel-manager"      "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-service-manager/solus-service-manager"    "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-log-viewer/solus-log-viewer"              "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-locale-setup/solus-locale-setup"          "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-cachy-tuning/apply-cachy-tuning.sh"       "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-cachy-tuning/tuned-profiles/solus-gaming/tuned.conf"   "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-cachy-tuning/tuned-profiles/solus-balanced/tuned.conf" "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-cachy-tuning/tuned-profiles/solus-powersave/tuned.conf" "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-cachy-tuning/ananicy-rules/solus-rules.conf"           "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-nobara-fixes/apply-nobara-fixes.sh"      "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-welcome/solus-welcome"                   "$BUILDROOT/SOURCES/"
cp "$ROOT/desktop/applications/solus-welcome.desktop"        "$BUILDROOT/SOURCES/"
cp "$ROOT/src/solus-installer/post-install.sh"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/src/solus-installer/hardware-detect.sh"            "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/src/solus-installer/apply-theme.sh"                "$BUILDROOT/SOURCES/" 2>/dev/null || true

# System config sources (for solus-system-config.spec)
cp "$ROOT/configs/dracut/dracut-solus.conf"                   "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/grub/grub-default"                          "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/sddm/sddm-solus.conf"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/plymouth/plymouthd-solus.conf"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/networkmanager/nm-solus.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/firewalld/solus.xml"                        "$BUILDROOT/SOURCES/solus-firewalld.xml" 2>/dev/null || true
cp "$ROOT/configs/flatpak/flathub.flatpakrepo"                "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/flatpak/solus.flatpakrepo"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/snapper/snapper-root.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/sudoers/solus-sudoers"                      "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/polkit/49-solus-nopasswd.rules"             "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/dnf/dnf-automatic.conf"                     "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/journald/journald-solus.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/timesyncd/timesyncd-solus.conf"             "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/solus-blacklist.conf"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/solus-nvidia.conf"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/solus-audio.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/modprobe/solus-thinkpad.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/crypttab/crypttab"                          "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/locale.conf"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/vconsole.conf"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/locale/solus-locale-gen"                    "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/secureboot/solus-shim.conf"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/btrfs/btrfs-scrub-timer.conf"               "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/btrfs/solus-btrfs-balance"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/solus-live-setup.service"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/live-setup.sh"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/live/install-solus.desktop"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Calamares branding sources
cp "$ROOT/branding/calamares/branding.desc"                   "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/calamares-branding/show.qml"                "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/branding/logo/solus-logo.svg"                       "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Gaming optimization sources
cp "$ROOT/configs/gaming/limits.conf"                         "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/gaming/sysctl-gaming.conf"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/configs/gaming/environment-gaming.conf"             "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Kernel sources (config + patches)
cp "$ROOT/kernel/configs/solus-x86_64-defconfig"              "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/kernel/patches/"*.patch                             "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Theme sources
cp "$ROOT/branding/theme/solus-gtk4/gtk.css"                  "$BUILDROOT/SOURCES/gtk4.css" 2>/dev/null || true
cp "$ROOT/branding/theme/solus-gtk3/gtk.css"                  "$BUILDROOT/SOURCES/gtk3.css" 2>/dev/null || true
cp "$ROOT/branding/theme/solus-sddm-theme/Main.qml"           "$BUILDROOT/SOURCES/sddm-Main.qml" 2>/dev/null || true
cp "$ROOT/branding/theme/solus-sddm-theme/metadata.desktop"   "$BUILDROOT/SOURCES/sddm-metadata.desktop" 2>/dev/null || true
cp "$ROOT/branding/theme/solus-sddm-theme/theme.conf"         "$BUILDROOT/SOURCES/sddm-theme.conf" 2>/dev/null || true

# Hyprland sources
cp "$ROOT/desktop/hyprland/waybar-style.css"                  "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/desktop/hyprland/wlogout-layout"                    "$BUILDROOT/SOURCES/" 2>/dev/null || true
cp "$ROOT/desktop/hyprland/wlogout-style.css"                 "$BUILDROOT/SOURCES/" 2>/dev/null || true
# Rust daemon binaries (from workspace)
for binary in solus-hwdaemon solus-desktopd solus-stored solus-gpu-setupd solus-cli \
              solus-system-daemon solus-ai-daemon solus-installer-detect solus-control-center; do
    src_bin="target/release/$binary"
    [ -f "$ROOT/$src_bin" ] && cp "$ROOT/$src_bin" "$BUILDROOT/SOURCES/"
done

# AI daemon systemd unit
cp "$ROOT/systemd/solus-ai-daemon.service" "$BUILDROOT/SOURCES/" 2>/dev/null || true

# Installer hook script
cp "$ROOT/installer/scripts/solus-installer-hook" "$BUILDROOT/SOURCES/" 2>/dev/null || true

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
    export GNUPGHOME="${GPG_HOME:-$HOME/.gnupg-solus}"
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
