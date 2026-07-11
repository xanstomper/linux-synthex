#!/usr/bin/env bash
# SynthOS Plymouth Theme Installer
# SPDX-License-Identifier: GPL-3.0-or-later
set -euo pipefail

THEME_NAME="synthex"
THEME_SRC="$(dirname "$(realpath "$0")")/theme"
THEME_DEST="/usr/share/plymouth/themes/${THEME_NAME}"

usage() {
    echo "Usage: $0 [--install|--uninstall|--preview|--rebuild]"
    echo ""
    echo "  --install    Install theme to system (requires root)"
    echo "  --uninstall  Remove theme from system (requires root)"
    echo "  --preview    Preview theme in a window (no root needed)"
    echo "  --rebuild    Rebuild initrd with current default theme (requires root)"
    exit 1
}

check_root() {
    [[ $EUID -eq 0 ]] || { echo "Error: This operation requires root." >&2; exit 1; }
}

# Convert SVG → PNG if needed (build-time)
generate_pngs() {
    local src="$THEME_SRC"
    echo "Generating Plymouth PNG assets..."

    for svg in logo spinner bullet bullet-highlight watermark; do
        local svg_file="${src}/${svg}.svg"
        local png_file="${src}/${svg}.png"

        if [ ! -f "$png_file" ] && [ -f "$svg_file" ]; then
            if command -v rsvg-convert &>/dev/null; then
                rsvg-convert -w 400 "$svg_file" -o "$png_file" 2>/dev/null && echo "  ✓ ${svg}.png"
            elif command -v inkscape &>/dev/null; then
                inkscape --export-type=png --export-filename="$png_file" "$svg_file" &>/dev/null && echo "  ✓ ${svg}.png"
            elif command -v convert &>/dev/null; then
                convert -background none "$svg_file" "$png_file" 2>/dev/null && echo "  ✓ ${svg}.png"
            else
                echo "  ⚠ No SVG converter found — using placeholder for ${svg}.png"
                convert -size 1x1 xc:'#0B0F1A' "$png_file" 2>/dev/null || true
            fi
        elif [ -f "$png_file" ]; then
            echo "  ✓ ${svg}.png (exists)"
        fi
    done
}

do_install() {
    check_root
    generate_pngs
    echo "Installing SynthOS Plymouth theme..."
    install -d "$THEME_DEST"
    install -m 644 "${THEME_SRC}/synthex.plymouth" "${THEME_DEST}/"
    install -m 644 "${THEME_SRC}/synthex.script"   "${THEME_DEST}/"
    # Install PNG assets
    for png in logo spinner bullet bullet-highlight watermark; do
        [ -f "${THEME_SRC}/${png}.png" ] && install -m 644 "${THEME_SRC}/${png}.png" "${THEME_DEST}/" || true
    done
    # Install SVG sources
    for svg in logo spinner bullet bullet-highlight watermark; do
        [ -f "${THEME_SRC}/${svg}.svg" ] && install -m 644 "${THEME_SRC}/${svg}.svg" "${THEME_DEST}/" || true
    done
    echo "✓ Theme installed to ${THEME_DEST}"
    echo ""
    echo "Setting ${THEME_NAME} as default Plymouth theme..."
    plymouth-set-default-theme "${THEME_NAME}"
    echo "✓ Default theme set"
    echo ""
    echo "Rebuilding initrd (this may take a moment)..."
    plymouth-set-default-theme "${THEME_NAME}" --rebuild-initrd
    echo "✓ initrd rebuilt"
    echo ""
    echo "SynthOS Plymouth theme installation complete."
}

do_uninstall() {
    check_root
    echo "Removing SynthOS Plymouth theme..."
    if plymouth-get-default-theme 2>/dev/null | grep -q "${THEME_NAME}"; then
        plymouth-set-default-theme bgrt 2>/dev/null || \
        plymouth-set-default-theme spinner 2>/dev/null || true
        plymouth-set-default-theme --rebuild-initrd 2>/dev/null || true
    fi
    rm -rf "$THEME_DEST"
    echo "✓ Theme removed"
}

do_preview() {
    echo "Launching Plymouth preview for theme: ${THEME_NAME}"
    if command -v plymouthd &>/dev/null; then
        sudo plymouthd --no-daemon --debug 2>/dev/null &
        PLYM_PID=$!
        sleep 1
        sudo plymouth --show-splash 2>/dev/null || true
        sleep 5
        sudo plymouth --quit 2>/dev/null || true
        wait "$PLYM_PID" 2>/dev/null || true
    else
        echo "plymouthd not available — install plymouth package first"
    fi
}

do_rebuild() {
    check_root
    plymouth-set-default-theme --rebuild-initrd
    echo "✓ initrd rebuilt"
}

case "${1:---install}" in
    --install)   do_install   ;;
    --uninstall) do_uninstall ;;
    --preview)   do_preview   ;;
    --rebuild)   do_rebuild   ;;
    *)           usage        ;;
esac
