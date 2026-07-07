#!/usr/bin/env bash
# Synthex OOBE Bundle — Creator
set -euo pipefail
LOG="/var/log/synthex-oobe-creator.log"
exec 2> >(tee -a "$LOG")

echo "[creator-bundle] installing content-creation suite"
dnf install -y \
    kdenlive blender gimp inkscape krita \
    obs-studio audacity handbrake \
    ffmpeg pipewire-pulseaudio easyeffects 2>/dev/null || true

flatpak install -y flathub org.blender.Blender 2>/dev/null || true
flatpak install -y flathub org.gimp.GIMP 2>/dev/null || true

echo "[creator-bundle] done"
