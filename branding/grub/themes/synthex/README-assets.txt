# GRUB Theme Asset Generation
#
# The following image assets are generated at build time from SVG sources:
#
#   background.png   ← background.svg   (1920×1080)
#   select_c.png     ← generated        (600×36, amber highlight)
#   select_e.png     ← generated        (1×36,   left cap)
#   select_w.png     ← generated        (1×36,   right cap)
#   terminal_c.png   ← generated        (1×1,    terminal bg)
#   terminal_e.png   ← generated        (1×1,    terminal border)
#
# Generation happens in build/scripts/build-iso.sh via:
#   rsvg-convert background.svg -o background.png  (or ImageMagick)
#   python3 scripts/gen-grub-assets.py
#
# For development, run:
#   cd branding/grub/themes/synthex
#   bash ../../../../build/scripts/gen-grub-assets.sh
