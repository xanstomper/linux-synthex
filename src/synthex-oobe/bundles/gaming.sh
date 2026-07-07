#!/usr/bin/env bash
# Synthex OOBE Bundle — Gaming
# Installs the gaming launcher + emulator-adjacent set after first boot.
set -euo pipefail
LOG="/var/log/synthex-oobe-gaming.log"
exec 2> >(tee -a "$LOG")

echo "[gaming-bundle] installing gaming launchers + tools"
dnf install -y \
    lutris heroic-games-launcher bottles prism-launcher \
    obs-studio discord protonup-qt protontricks \
    gamescope goverlay vkbasalt \
    retroarch dolphin-emu rpcs3 pcsx2 2>/dev/null || true

# Flatpak fallbacks for apps not in rpm repos
flatpak install -y flathub com.discordapp.Discord 2>/dev/null || true
flatpak install -y flathub net.lutris.Lutris 2>/dev/null || true

echo "[gaming-bundle] done"
