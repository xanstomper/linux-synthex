#!/usr/bin/env bash
# Synthex OOBE Bundle — RGB & Peripherals
set -euo pipefail
LOG="/var/log/synthex-oobe-rgb.log"
exec 2> >(tee -a "$LOG")

echo "[rgb-bundle] installing RGB + peripheral tools"
dnf install -y \
    openrgb piper solaar \
    corectrl lact 2>/dev/null || true

flatpak install -y flathub org.openrgb.OpenRGB 2>/dev/null || true

# Enable the openrgb system service if present
systemctl enable --now openrgb.service 2>/dev/null || true

echo "[rgb-bundle] done"
