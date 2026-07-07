#!/usr/bin/env bash
#
# synthex-desktop-config.sh — Synthex Plasma First Boot Configuration
# Applies Synthex-branded Plasma desktop settings on first boot.
# Runs as the target user, not root.
#
# Part of: synthex-plasma-desktop
# Installed to: /usr/share/synthex/plasma/scripts/
#

set -euo pipefail

echo "🔧 Synthex Plasma — Applying desktop configuration..."

USER_HOME="${HOME}"
USERNAME="${USER}"
CONFIG_DIR="${USER_HOME}/.config"
KNSRC_FILE="/usr/share/synthex/plasma/config/default-settings.knsrc"
PLASMA_SESSION_DIR="${USER_HOME}/.config/plasma-org.kde.plasma.desktop-appletsrc"
LOCK_FILE="${USER_HOME}/.config/synthex-desktop-config.lock"

# ─── Guard: only run once ─────────────────────────────────────────────────
if [[ -f "${LOCK_FILE}" ]]; then
    echo "✔ Synthex desktop configuration already applied. Skipping."
    exit 0
fi

# ─── Import default settings ──────────────────────────────────────────────
if [[ -f "${KNSRC_FILE}" ]]; then
    echo "   Loading default settings from ${KNSRC_FILE}..."
    kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" --input "${KNSRC_FILE}"
    echo "   Base globals imported."
else
    echo "⚠  Default settings file not found: ${KNSRC_FILE}"
    echo "   Falling back to system defaults."
fi

# ─── Apply Plasma Theme ───────────────────────────────────────────────────
echo "   Setting Plasma theme to Synthex Fluent Material..."
lookandfeeltool -a org.synthex.desktop 2>/dev/null || \
    plasma-apply-lookandfeel -a org.synthex.desktop 2>/dev/null || \
    echo "⚠  Look-and-feel package not found. Install synthex-plasma-theme."

# ─── Wallpaper ────────────────────────────────────────────────────────────
WALLPAPER="/usr/share/wallpapers/synthex-default.jpg"
if [[ -f "${WALLPAPER}" ]]; then
    echo "   Setting default wallpaper..."
    plasma-apply-wallpaperimage "${WALLPAPER}" 2>/dev/null || \
        kwriteconfig6 --file "${PLASMA_SESSION_DIR}" \
            --group "Wallpaper" \
            --key "Image" "${WALLPAPER}"
else
    echo "⚠  Default wallpaper not found at ${WALLPAPER}"
fi

# ─── Color Scheme ─────────────────────────────────────────────────────────
echo "   Applying Synthex Fluent color scheme..."
plasma-apply-colorscheme SynthexFluent 2>/dev/null || \
    kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" \
        --group "General" --key "ColorScheme" "SynthexFluent"

# ─── Panel Layout ─────────────────────────────────────────────────────────
echo "   Configuring panel layout (Windows 11 style)..."
# Reset panels to default
plasma-apply-panelreset 2>/dev/null || true

# ─── Fonts ────────────────────────────────────────────────────────────────
echo "   Setting fonts..."
kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" \
    --group "General" \
    --key "font" "Inter,10,-1,5,50,0,0,0,0,0"

kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" \
    --group "General" \
    --key "fixed" "JetBrains Mono,10,-1,5,50,0,0,0,0,0"

kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" \
    --group "General" \
    --key "smallestReadableFont" "Inter,8,-1,5,50,0,0,0,0,0"

# ─── Icons ────────────────────────────────────────────────────────────────
echo "   Setting icon theme to Synthex Tela Circle..."
kwriteconfig6 --file "${CONFIG_DIR}/kdeglobals" \
    --group "Icons" \
    --key "Theme" "Synthex-Tela-circle"

# ─── Cursor ───────────────────────────────────────────────────────────────
echo "   Setting cursor theme..."
kwriteconfig6 --file "${CONFIG_DIR}/kcminputrc" \
    --group "Mouse" \
    --key "cursorTheme" "Synthex-Cursor"
kwriteconfig6 --file "${CONFIG_DIR}/kcminputrc" \
    --group "Mouse" \
    --key "cursorSize" "24"

# ─── KWin Configuration ───────────────────────────────────────────────────
echo "   Applying KWin compositor settings..."
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Compositing" \
    --key "Enabled" "true"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Compositing" \
    --key "Backend" "OpenGL"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Compositing" \
    --key "OpenGLIsUnsafe" "false"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Compositing" \
    --key "AnimationSpeed" "1"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Compositing" \
    --key "AnimationCurve" "MaterialEased"

# Window corner radius (requires KDE 6.x)
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Windows" \
    --key "WindowCornerRadius" "12"

# Blur
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Blur" \
    --key "BlurStrength" "30"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Blur" \
    --key "Enabled" "true"

# ─── Virtual Desktops ─────────────────────────────────────────────────────
echo "   Setting up 4 virtual desktops (2×2 grid)..."
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Desktops" \
    --key "Number" "4"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "Desktops" \
    --key "Rows" "2"

# ─── Task Manager ─────────────────────────────────────────────────────────
echo "   Configuring task manager..."
kwriteconfig6 --file "${PLASMA_SESSION_DIR}" \
    --group "Containments" \
    --group "1" \
    --group "Applets" \
    --group "1" \
    --group "Configuration" \
    --key "groupingStrategy" "ByApplication"
kwriteconfig6 --file "${PLASMA_SESSION_DIR}" \
    --group "Containments" \
    --group "1" \
    --group "Applets" \
    --group "1" \
    --group "Configuration" \
    --key "launcher" "true"

# ─── System Tray ──────────────────────────────────────────────────────────
echo "   Enabling system tray items..."
# This is typically done interactively; we set the preferred defaults via
# plasmoids layout override.

# ─── Night Color ──────────────────────────────────────────────────────────
echo "   Enabling Night Color (auto dark mode)..."
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "NightColor" \
    --key "Active" "true"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "NightColor" \
    --key "Mode" "Auto"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "NightColor" \
    --key "Latitude" "40.7128"
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "NightColor" \
    --key "Longitude" "-74.0060"

# ─── Screen Locking ───────────────────────────────────────────────────────
echo "   Configuring screen lock..."
kwriteconfig6 --file "${CONFIG_DIR}/kscreensaverrc" \
    --group "KScreenSaver" \
    --key "AutoLock" "true"
kwriteconfig6 --file "${CONFIG_DIR}/kscreensaverrc" \
    --group "KScreenSaver" \
    --key "Timeout" "5"
kwriteconfig6 --file "${CONFIG_DIR}/kscreensaverrc" \
    --group "KScreenSaver" \
    --key "Lock" "true"

# ─── Privacy ──────────────────────────────────────────────────────────────
echo "   Configuring privacy settings..."
kwriteconfig6 --file "${CONFIG_DIR}/kactivitymanagerdrc" \
    --group "plugins" \
    --key "telemetryEnabled" "false"

# ─── KDE Wallet (disabled by default) ─────────────────────────────────────
echo "   Disabling KDE Wallet (can be enabled manually)..."
kwriteconfig6 --file "${CONFIG_DIR}/kwalletrc" \
    --group "Wallet" \
    --key "Enabled" "false"

# ─── Shortcuts ────────────────────────────────────────────────────────────
echo "   Applying Synthex custom shortcuts..."
# Super+Space → Application Launcher
kwriteconfig6 --file "${CONFIG_DIR}/kglobalshortcutsrc" \
    --group "krunner.desktop" \
    --key "_launch" "Ctrl+Space,Ctrl+Space,Run Command"

# Super+D → Show Desktop
kwriteconfig6 --file "${CONFIG_DIR}/kglobalshortcutsrc" \
    --group "kwin" \
    --key "Show Desktop" "Meta+D,Meta+D,Show Desktop"

# Super+N → Notifications
kwriteconfig6 --file "${CONFIG_DIR}/kglobalshortcutsrc" \
    --group "plasmashell" \
    --key "show-bring-to-front-or-toggle" "Meta+N,Meta+N,Toggle Notifications"

# Super+E → File Manager
kwriteconfig6 --file "${CONFIG_DIR}/kglobalshortcutsrc" \
    --group "dolphin.desktop" \
    --key "_launch" "Meta+E,Meta+E,Dolphin"

# Super+L → Lock Screen
kwriteconfig6 --file "${CONFIG_DIR}/kglobalshortcutsrc" \
    --group "kscreenlocker" \
    --key "Lock Session" "Meta+L,Meta+L,Lock Screen"

# Super+Tab → Window Switcher (thumbnail)
kwriteconfig6 --file "${CONFIG_DIR}/kwinrc" \
    --group "TabBox" \
    --key "LayoutName" "thumbnailGrid"

# ─── Apply All ────────────────────────────────────────────────────────────
echo "   Reloading Plasma configuration..."
# Signal KDE to reload configs
dbus-send --session --type=signal \
    /KDEPlatformTheme \
    org.kde.KDEPlatformTheme.reconfigure 2>/dev/null || true

kquitapp6 plasmashell 2>/dev/null || true
kstart6 plasmashell 2>/dev/null || true

# ─── Lock File ────────────────────────────────────────────────────────────
echo "${USERNAME}" > "${LOCK_FILE}"
echo "✔ Synthex desktop configuration applied successfully."
echo "   (Lock file created: ${LOCK_FILE})"
echo ""
echo "🎉 Welcome to Synthex Plasma!"
