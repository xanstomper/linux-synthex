#!/bin/bash
# Generate Synthex wallpapers
# Requires imagemagick

DIR="/usr/share/wallpapers"
sudo mkdir -p "$DIR"

for theme in graphite frost midnight mint latte; do
    case $theme in
        graphite) c1="#0B0F1A"; c2="#1A1A2E" ;;
        frost)    c1="#F5F5F7"; c2="#D0D0D8" ;;
        midnight) c1="#000000"; c2="#111111" ;;
        mint)     c1="#F0F5F0"; c2="#C8D8C8" ;;
        latte)    c1="#EFF1F5"; c2="#DCE0E8" ;;
    esac
    convert -size 3840x2160 gradient:"$c1"-"$c2" "synthex-$theme.png" 2>/dev/null || \
        echo "Warning: ImageMagick not installed. Skipping $theme wallpaper."
done

sudo cp synthex-*.png "$DIR/" 2>/dev/null || true
echo "Wallpapers generated. Install ImageMagick for full quality."
