#!/usr/bin/env bash
# GRUB theme sync — ensure theme files are in /boot/grub2
set -euo pipefail
THEME_SRC="/usr/share/grub/themes/synthex"
THEME_DST="/boot/grub2/themes/synthex"
mkdir -p "$THEME_DST"
cp -a "$THEME_SRC"./* "$THEME_DST"/ 2>/dev/null || true
mkdir -p /boot/grub/synthex-logo.png 2>/dev/null || true
