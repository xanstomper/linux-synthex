#!/usr/bin/env bash
# Synthex Mint Desktop Configuration Script
# Applies Linux Mint-inspired KDE Plasma settings
set -euo pipefail

echo "🎨 Applying Synthex Mint desktop configuration..."

# ─── Panel Layout ─────────────────────────────────────────────────────
# Remove default panels, create Mint-style bottom panel
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "location" "Bottom"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "alignment" "Left"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "locking" "true"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "floating" "false"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "panelSize" "38"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "General" \
    --key "opacity" "95"

# ─── Task Manager (Window List) — Text+Icon like Mint ────────────────
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "2" \
    --group "Configuration" --group "General" \
    --key "groupingStrategy" "0"  # Never group
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "2" \
    --group "Configuration" --group "General" \
    --key "showApplicationIcons" "true"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "2" \
    --group "Configuration" --group "General" \
    --key "showToolTips" "true"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "2" \
    --group "Configuration" --group "General" \
    --key "showOnlyDesktop" "false"

# ─── Application Menu Style ──────────────────────────────────────────
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "3" \
    --group "Configuration" --group "General" \
    --key "appNameFormat" "1"  # Show icon + name
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "3" \
    --group "Configuration" --group "General" \
    --key "favorites" "[]"
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "3" \
    --group "Configuration" --group "General" \
    --key "showRecentApps" "true"

# ─── System Tray ─────────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "1" --group "Applets" --group "4" \
    --group "Configuration" --group "General" \
    --key "showAllItems" "false"
# Show: clock, volume, network, battery, bluetooth
for item in "org.kde.plasma.private.systemmonitor" "org.kde.plasma.notifications"; do
    kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
        --group "Containments" --group "1" --group "Applets" --group "4" \
        --group "Configuration" --group "ExtraItems" \
        --key "$item" "false"
done

# ─── Desktop Behavior ────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "2" --group "General" \
    --key "arrangement" "1"  # Rows layout
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "2" --group "General" \
    --key "iconSize" "3"  # Medium icons (48px)
kwriteconfig6 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc \
    --group "Containments" --group "2" --group "General" \
    --key "sorting" "1"  # Alphabetical

# ─── Window Behavior ─────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/kwinrc --group "Windows" --group "SeparateScreenFocus" \
    --key "focusPolicy" "FocusFollowsMouse"  # Like Mint/Cinnamon
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "Backend" "OpenGL"
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "OpenGLIsUnsafe" "false"
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "Enabled" "true"
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "LatencyPolicy" "1"  # Low latency
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "MaxFPS" "60"
kwriteconfig6 --file ~/.config/kwinrc --group "Compositing" \
    --key "RefreshRate" "60"

# ─── Workspace Switcher ──────────────────────────────────────────────
kwriteconfig6 --file ~/.config/kwinrc --group "Desktops" \
    --key "Number" "4"  # 2x2 grid like Mint
kwriteconfig6 --file ~/.config/kwinrc --group "Desktops" \
    --key "Rows" "2"

# ─── Window Decoration ────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/kwinrc --group "org.kde.kdecoration2" \
    --key "library" "org.kde.kwin.aurorae"
kwriteconfig6 --file ~/.config/kwinrc --group "org.kde.kwin.aurorae" \
    --key "theme" "synthex-mint"

# ─── Theme ────────────────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/kdeglobals --group "General" \
    --key "ColorScheme" "SynthexMint"
kwriteconfig6 --file ~/.config/kdeglobals --group "Icons" \
    --key "Theme" "Mint-Y"

# ─── Fonts ────────────────────────────────────────────────────────────
kwriteconfig6 --file ~/.config/kdeglobals --group "General" \
    --key "font" "Noto Sans,10,-1,5,50,0,0,0,0,0"
kwriteconfig6 --file ~/.config/kdeglobals --group "General" \
    --key "fixed" "JetBrains Mono,10,-1,5,50,0,0,0,0,0"
kwriteconfig6 --file ~/.config/kdeglobals --group "General" \
    --key "smallestReadableFont" "Noto Sans,8,-1,5,50,0,0,0,0,0"

# ─── Apply Changes ───────────────────────────────────────────────────
# Restart Plasma to apply
echo "🔄 Restarting Plasma shell..."
plasmashell --replace &>/dev/null &
disown

echo "✅ Synthex Mint desktop configuration applied!"
echo "   Panel: Bottom, 38px, opaque"
echo "   Taskbar: Text+Icon (Mint-style)"
echo "   Theme: SynthexMint (green #9BBD5C)"
echo "   Layout: 4 workspaces (2x2 grid)"
