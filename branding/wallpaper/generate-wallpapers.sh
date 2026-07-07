#!/usr/bin/env bash
#
# generate-wallpapers.sh - Linux Synthex Branded Wallpaper Generator
#
# Generates Synthex-branded wallpapers using ImageMagick.
# Supports multiple resolutions and editions.
#
# Requirements:
#   - ImageMagick (convert, magick)
#   - Font: Inter (or fallback to DejaVu Sans)
#
# Usage:
#   ./generate-wallpapers.sh [output_dir] [edition]
#
# Editions: default, plasma, hyprland, gnome
# Default output: ./output/
#

set -euo pipefail

OUTPUT_DIR="${1:-./output}"
EDITION="${2:-default}"

# ---- Configuration ----
SYNTHEX_AMBER="#FFB300"
SYNTHEX_DEEP_BLUE="#1565C0"
SYNTHEX_DARK_BASE="#1A1A2E"
SYNTHEX_DARK_SURFACE="#16213E"
SYNTHEX_DARK_ELEVATED="#0F3460"
SYNTHEX_DEEP_PURPLE="#6A1B9A"
SYNTHEX_TEAL="#00897B"

# Edition colour mapping
case "$EDITION" in
  default)
    ACCENT="$SYNTHEX_AMBER"
    SECONDARY="$SYNTHEX_DEEP_PURPLE"
    LABEL="Synthex"
    ;;
  plasma)
    ACCENT="$SYNTHEX_AMBER"
    SECONDARY="$SYNTHEX_DEEP_BLUE"
    LABEL="Synthex Plasma"
    ;;
  hyprland)
    ACCENT="$SYNTHEX_DEEP_PURPLE"
    SECONDARY="$SYNTHEX_AMBER"
    LABEL="Synthex Hyprland"
    ;;
  gnome)
    ACCENT="$SYNTHEX_TEAL"
    SECONDARY="$SYNTHEX_DEEP_BLUE"
    LABEL="Synthex GNOME"
    ;;
  *)
    echo "Unknown edition: $EDITION. Using default."
    ACCENT="$SYNTHEX_AMBER"
    SECONDARY="$SYNTHEX_DEEP_PURPLE"
    LABEL="Synthex"
    ;;
esac

# Resolutions
RESOLUTIONS=(
  "3840x2160"   # 4K UHD
  "2560x1440"   # QHD
  "1920x1080"   # Full HD
  "2560x1600"   # MacBook Pro 16"
  "2880x1800"   # MacBook Pro 14"
  "1366x768"    # Common laptop
)

mkdir -p "$OUTPUT_DIR"

FONT="Inter-Regular"
FONT_BOLD="Inter-Bold"
FONT_LIGHT="Inter-Light"

# Check Inter availability
if ! convert -list font 2>/dev/null | grep -qi "inter"; then
  echo "Warning: Inter font not found. Falling back to DejaVu Sans."
  FONT="DejaVu-Sans"
  FONT_BOLD="DejaVu-Sans-Bold"
  FONT_LIGHT="DejaVu-Sans"
fi

echo "=== Synthex Wallpaper Generator ==="
echo "Edition:    $EDITION"
echo "Accent:     $ACCENT"
echo "Secondary:  $SECONDARY"
echo "Output:     $OUTPUT_DIR"
echo ""

generate_wallpaper() {
  local res="$1"
  local label="$2"
  local filename="${OUTPUT_DIR}/synthex-${EDITION}-${res}.png"

  echo "Generating ${filename}..."

  magick -size "$res" \
    -define gradient:direction=south \
    "gradient:${SYNTHEX_DARK_BASE}-${SYNTHEX_DARK_SURFACE}" \
    \
    \( +clone \
      -fill "${ACCENT}" -draw "circle $(( ${res%%x*} / 2 )),$(( ${res##*x} / 2 )) $(( ${res%%x*} / 2 + ${res%%x*} / 6 )),$(( ${res##*x} / 2 ))" \
      -blur 0x80 \
      -fill "${SECONDARY}44" -draw "circle $(( ${res%%x*} * 3 / 4 )),$(( ${res##*x} / 3 )) $(( ${res%%x*} * 3 / 4 + ${res%%x*} / 8 )),$(( ${res##*x} / 3 ))" \
      -blur 0x60 \
    \) \
    -compose Screen -composite \
    \
    \( +clone \
      -fill "${SYNTHEX_DARK_BASE}88" -draw "rectangle 0,$(( ${res##*x} - 120 )) ${res%%x*},${res##*x}" \
    \) \
    -compose Over -composite \
    \
    \( +clone \
      -fill "${ACCENT}" \
      -font "$FONT_BOLD" -pointsize $(( ${res##*x} / 24 )) \
      -gravity center \
      -annotate +0-$(( ${res##*x} / 12 )) "${label}" \
    \) \
    -compose Over -composite \
    \
    \( +clone \
      -fill "#C0C0D0" \
      -font "$FONT" -pointsize $(( ${res##*x} / 48 )) \
      -gravity center \
      -annotate +0+$(( ${res##*x} / 24 )) "Illuminate Your Desktop" \
    \) \
    -compose Over -composite \
    \
    \( +clone \
      -fill "${ACCENT}22" \
      -draw "roundrectangle $(( ${res%%x*} / 2 - 80 )),$(( ${res##*x} / 2 + ${res##*x} / 20 )) $(( ${res%%x*} / 2 + 80 )),$(( ${res##*x} / 2 + ${res##*x} / 20 + 2 )) 1,1" \
    \) \
    -compose Over -composite \
    \
    "$filename"
}

for res in "${RESOLUTIONS[@]}"; do
  generate_wallpaper "$res" "$LABEL"
done

# Also generate the default-dark.png symlink/copy
cp "${OUTPUT_DIR}/synthex-${EDITION}-1920x1080.png" "${OUTPUT_DIR}/default-dark.png"

echo ""
echo "=== Wallpaper generation complete! ==="
echo "Generated ${#RESOLUTIONS[@]} wallpapers in ${OUTPUT_DIR}/"
echo "Default: ${OUTPUT_DIR}/default-dark.png"
echo ""
echo "Wallpaper files:"
ls -lh "${OUTPUT_DIR}"/*.png
