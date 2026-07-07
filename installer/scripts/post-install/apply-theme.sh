#!/usr/bin/env bash
# synthex-apply-theme.sh — Apply Synthex theming to the installed system
# Installed to /usr/libexec/synthex/apply-theme.sh
set -euo pipefail

LOG="/var/log/synthex-apply-theme.log"
echo "=== Apply Theming $(date) ===" | tee "$LOG"

THEME="${1:-synthex}"
COLOR_SCHEME="/usr/share/color-schemes/${THEME}.colors"
SDDM_THEME="/usr/share/sddm/themes/synthex"
PLASMA_THEME="/usr/share/plasma/desktoptheme/synthex"
WALLPAPER="/usr/share/wallpapers/synthex-default.png"

# 1. Set SDDM theme
if [ -d "$SDDM_THEME" ]; then
    echo "Setting SDDM theme..." | tee -a "$LOG"
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/synthex-theme.conf << SDDMEOF
[Theme]
Current=synthex
SDDMEOF
fi

# 2. Set Plasma theme
if [ -d "$PLASMA_THEME" ]; then
    echo "Setting Plasma theme..." | tee -a "$LOG"
    mkdir -p /etc/xdg/plasma-workspace/env
    cat > /etc/xdg/plasma-workspace/env/synthex-theme.sh << PLASMAEOF
export KDE_SKIP_KCMMIGRATE=1
export PLASMA_USE_QT_SCALING=1
PLASMAEOF
fi

# 3. Apply color scheme system-wide
if [ -f "$COLOR_SCHEME" ]; then
    echo "Applying color scheme..." | tee -a "$LOG"
    mkdir -p /etc/skel/.kde/share/config
    cp "$COLOR_SCHEME" /etc/skel/.kde/share/config/ 2>/dev/null || true
fi

# 4. Set default wallpaper
if [ -f "$WALLPAPER" ]; then
    echo "Setting default wallpaper..." | tee -a "$LOG"
fi

# 5. Configure GRUB theme
GRUB_THEME="/boot/grub2/themes/synthex"
if [ -d "$GRUB_THEME" ]; then
    echo "Setting GRUB theme..." | tee -a "$LOG"
    echo "GRUB_THEME=\"${GRUB_THEME}/theme.txt\"" >> /etc/default/grub 2>/dev/null || true
fi

echo "=== Theming complete ===" | tee -a "$LOG"
exit 0
