#!/usr/bin/env bash
# apply-theme.sh — Apply Synthex theming to the installed system
set -euo pipefail

echo "🎨 Applying Synthex theming..."

# ─── GRUB theme ───────────────────────────────────────────────────────
if [ -d /usr/share/grub/themes/synthex ]; then
    echo "  Setting GRUB theme..."
    if ! grep -q "GRUB_THEME=" /etc/default/grub 2>/dev/null; then
        echo 'GRUB_THEME="/usr/share/grub/themes/synthex/theme.txt"' >> /etc/default/grub
    fi
    # Set timeout
    sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=5/' /etc/default/grub 2>/dev/null || true
    # Regenerate GRUB config
    grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || \
        grub2-mkconfig -o /boot/efi/EFI/synthex/grub.cfg 2>/dev/null || true
fi

# ─── Plymouth boot splash ─────────────────────────────────────────────
if command -v plymouth-set-default-theme &>/dev/null; then
    if [ -f /usr/share/plymouth/themes/synthex/synthex.plymouth ]; then
        echo "  Setting Plymouth theme..."
        plymouth-set-default-theme synthex 2>/dev/null || true
        dracut --force 2>/dev/null || true
    fi
fi

# ─── SDDM theme ───────────────────────────────────────────────────────
if [ -d /usr/share/sddm/themes/synthex-sddm-theme ]; then
    echo "  Setting SDDM theme..."
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/theme.conf << 'EOF'
[Theme]
Current=synthex-sddm-theme
CursorTheme=Bibata-Modern-Classic
EOF
fi

# ─── KDE Plasma theme ─────────────────────────────────────────────────
if [ -d /usr/share/plasma/look-and-feel ]; then
    echo "  Setting Plasma look-and-feel..."
    mkdir -p /etc/skel/.config
    cat > /etc/skel/.config/kdeglobals << 'EOF'
[KDE]
widgetStyle=Breeze

[Icons]
Theme=Papirus-Dark

[Colors:View]
BackgroundNormal=#1a1a2e
ForegroundNormal=#ffffff
EOF
fi

# ─── GTK theme ────────────────────────────────────────────────────────
echo "  Setting GTK theme..."
mkdir -p /etc/skel/.config/gtk-3.0
cat > /etc/skel/.config/gtk-3.0/settings.ini << 'EOF'
[Settings]
gtk-theme-name=Synthex-Dark
gtk-icon-theme-name=Papirus-Dark
gtk-cursor-theme-name=Bibata-Modern-Classic
gtk-font-name=Inter 10
gtk-application-prefer-dark-theme=1
EOF

# ─── Cursor theme ─────────────────────────────────────────────────────
echo "  Setting cursor theme..."
mkdir -p /etc/skel/.icons/default
cat > /etc/skel/.icons/default/index.theme << 'EOF'
[Icon Theme]
Name=Default
Comment=Default Cursor Theme
Inherits=Bibata-Modern-Classic
EOF

# ─── Default wallpaper ────────────────────────────────────────────────
if [ -f /usr/share/backgrounds/synthex/synthex-dark-4k.png ] || \
   [ -f /usr/share/backgrounds/synthex/synthex-dark-4k.jpg ]; then
    echo "  Setting default wallpaper..."
    WALLPAPER=$(ls /usr/share/backgrounds/synthex/synthex-dark-4k.* 2>/dev/null | head -1)
    # Plasma
    mkdir -p /etc/skel/.config
    cat > /etc/skel/.config/plasma-localerc << EOF
[Wallpaper]
Image=$WALLPAPER
EOF
    # GNOME
    gsettings set org.gnome.desktop.background picture-uri "file://$WALLPAPER" 2>/dev/null || true
fi

# ─── Font configuration ───────────────────────────────────────────────
echo "  Setting default fonts..."
mkdir -p /etc/fonts/conf.d
cat > /etc/fonts/local.conf << 'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
    <edit name="lcdfilter" mode="assign"><const>lcddefault</const></edit>
  </match>
  <match target="pattern">
    <test name="family"><string>sans-serif</string></test>
    <edit name="family" mode="assign" binding="strong"><string>Inter</string></edit>
  </match>
  <match target="pattern">
    <test name="family"><string>monospace</string></test>
    <edit name="family" mode="assign" binding="strong"><string>JetBrains Mono</string></edit>
  </match>
</fontconfig>
EOF

echo "✅ Theming applied"
