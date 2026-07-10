#!/usr/bin/env bash
# Generate GRUB theme PNG assets from SVG sources
# Requires: rsvg-convert (librsvg) or ImageMagick
set -euo pipefail

THEME_DIR="$(dirname "$0")/../../branding/grub/themes/synthex"
cd "$THEME_DIR"

log() { echo "[grub-assets] $*"; }

# Background
if command -v rsvg-convert &>/dev/null; then
    rsvg-convert background.svg -w 1920 -h 1080 -o background.png
    log "background.png generated (rsvg-convert)"
elif command -v convert &>/dev/null; then
    convert -size 1920x1080 background.svg background.png
    log "background.png generated (ImageMagick)"
else
    log "WARN: neither rsvg-convert nor ImageMagick found, skipping background.png"
fi

# Selection highlight bar — amber semi-transparent
if command -v convert &>/dev/null; then
    convert -size 600x36 xc:"#B87A0033" \
            -fill "#FFB30022" -draw "rectangle 0,0 599,35" \
            -fill "#FFB300"   -draw "line 0,0 599,0" \
            -fill "#FFB300"   -draw "line 0,35 599,35" \
            PNG32:select_c.png
    log "select_c.png generated"
    convert -size 4x36 xc:"#FFB30033" PNG32:select_e.png
    convert -size 4x36 xc:"#FFB30033" PNG32:select_w.png
    log "select cap images generated"
else
    log "WARN: ImageMagick not found, skipping selection images"
fi

log "Done."
