#!/bin/bash
# Synthex Asset Installer — install all branding assets system-wide
# Run as root: sudo ./install-assets.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Color scheme files → /usr/share/color-schemes/
echo "Installing color schemes..."
for f in "$SCRIPT_DIR"/theme/synthex-*/colors "$SCRIPT_DIR"/theme/synthex-*-theme/colors; do
    if [ -f "$f" ]; then
        name=$(basename "$(dirname "$f")")
        cp "$f" "/usr/share/color-schemes/${name}.colors"
        echo "  ${name}.colors"
    fi
done

# Desktop profiles → /usr/share/synthex/desktop-profiles/
echo "Installing desktop profiles..."
mkdir -p /usr/share/synthex/desktop-profiles
cp -r "$SCRIPT_DIR"/desktop-profiles/{focus,gaming,pro,touch,classic,lite,studio,ai} /usr/share/synthex/desktop-profiles/
cp "$SCRIPT_DIR"/desktop-profiles/synthex-desktop /usr/bin/synthex-desktop
chmod +x /usr/bin/synthex-desktop
cp "$SCRIPT_DIR"/desktop-profiles/profiles-index.json /usr/share/synthex/
echo "  done"

# Wallpapers → /usr/share/wallpapers/
echo "Installing wallpapers..."
mkdir -p /usr/share/wallpapers
cp "$SCRIPT_DIR"/wallpapers/synthex-*.svg /usr/share/wallpapers/ 2>/dev/null || true
cp "$SCRIPT_DIR"/wallpaper/*.svg /usr/share/wallpapers/ 2>/dev/null || true
echo "  done"

# Icons → /usr/share/icons/hicolor/
echo "Installing icons..."
for svg in "$SCRIPT_DIR"/icons/*.svg; do
    name=$(basename "$svg" .svg)
    size_dir="/usr/share/icons/hicolor/scalable/apps"
    mkdir -p "$size_dir"
    cp "$svg" "$size_dir/${name}.svg"
done
echo "  done"

# SDDM Theme → /usr/share/sddm/themes/synthex/
echo "Installing SDDM theme..."
cp -r "$SCRIPT_DIR"/theme/synthex-sddm-theme /usr/share/sddm/themes/synthex 2>/dev/null || true
echo "  done"

# Plymouth Theme → /usr/share/plymouth/themes/synthex/
echo "Installing Plymouth theme..."
mkdir -p /usr/share/plymouth/themes/synthex
cp "$SCRIPT_DIR"/plymouth/theme/synthex.plymouth /usr/share/plymouth/themes/synthex/ 2>/dev/null || true
echo "  done"

# GRUB Theme → /boot/grub2/themes/synthex/
echo "Installing GRUB theme..."
mkdir -p /boot/grub2/themes/synthex
cp "$SCRIPT_DIR"/grub/* /boot/grub2/themes/synthex/ 2>/dev/null || true
echo "  done"

# Plasma Themes → /usr/share/plasma/desktoptheme/
echo "Installing Plasma themes..."
cp -r "$SCRIPT_DIR"/desktop-themes/* /usr/share/plasma/desktoptheme/ 2>/dev/null || true
echo "  done"

# KWin Scripts → /usr/share/kwin/scripts/
echo "Installing KWin scripts..."
cp -r "$SCRIPT_DIR"/kwin-scripts/* /usr/share/kwin/scripts/ 2>/dev/null || true
echo "  done"

# KCM → /usr/share/kcm_solus_profiles/
echo "Installing KCM module..."
mkdir -p /usr/share/kcm_solus_profiles
cp "$SCRIPT_DIR"/kcm-synthex-profiles/main.qml /usr/share/kcm_solus_profiles/ 2>/dev/null || true
echo "  done"

# GTK Themes
if [ -d "$SCRIPT_DIR/theme/synthex-gtk3" ]; then
    cp -r "$SCRIPT_DIR"/theme/synthex-gtk3/* /usr/share/themes/Synthex/gtk-3.0/ 2>/dev/null || true
fi
if [ -d "$SCRIPT_DIR/theme/synthex-gtk4" ]; then
    cp -r "$SCRIPT_DIR"/theme/synthex-gtk4/* /usr/share/themes/Synthex/gtk-4.0/ 2>/dev/null || true
fi

echo ""
echo "All Synthex branding assets installed!"
echo "Apply a profile: synthex-desktop apply <profile>"
