#!/usr/bin/env bash
# Install Synthex Plymouth Boot Splash Theme
set -euo pipefail

THEME_DIR="/usr/share/plymouth/themes/synthex"
PLYMOUTH_DIR="$(dirname "$0")"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

echo "🎨 Installing Synthex Plymouth theme..."

# Create theme directory
mkdir -p "$THEME_DIR"

# Copy theme files
cp "$PLYMOUTH_DIR/synthex.plymouth" "$THEME_DIR/"
cp "$PLYMOUTH_DIR/theme/"*.png "$THEME_DIR/" 2>/dev/null || echo "  ⚠ No PNG files found, using defaults"

# Generate logo if not present
if [ ! -f "$THEME_DIR/logo.png" ]; then
    echo "  Generating logo..."
    # Create a minimal 256x256 amber circle as logo
    python3 -c "
from PIL import Image, ImageDraw 2>/dev/null || {
        # Fallback: create a simple SVG that Plymouth can use
        cat > /tmp/synthex-logo.svg << 'SVG'
<svg xmlns='http://www.w3.org/2000/svg' width='256' height='256'>
  <circle cx='128' cy='128' r='64' fill='#FFB300'/>
  <circle cx='128' cy='128' r='24' fill='#0B0F1A'/>
</svg>
SVG
        convert /tmp/synthex-logo.svg "$THEME_DIR/logo.png" 2>/dev/null || true
    }"
fi

# Set as default theme
plymouth-set-default-theme synthex 2>/dev/null || true

# Rebuild initramfs with new splash
dracut --force --regenerate-all 2>/dev/null || dracut --force 2>/dev/null || true

echo "✅ Synthex Plymouth theme installed"
echo "   Theme: $THEME_DIR"
echo "   Default: $(plymouth-set-default-theme 2>/dev/null || echo 'synthex')"
