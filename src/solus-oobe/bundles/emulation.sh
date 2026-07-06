#!/usr/bin/env bash
# Solus OOBE Bundle — Emulation
set -euo pipefail
LOG="/var/log/solus-oobe-emulation.log"
exec 2> >(tee -a "$LOG")

echo "[emulation-bundle] installing emulators + EmuDeck tooling"
dnf install -y \
    retroarch dolphin-emu rpcs3 pcsx2 \
    ppsspp mame mednafen 2>/dev/null || true

flatpak install -y flathub org.libretro.RetroArch 2>/dev/null || true
flatpak install -y flathub org.DolphinEmu.dolphin-emu 2>/dev/null || true
flatpak install -y flathub net.rpcs3.RPCS3 2>/dev/null || true

# EmuDeck installer (download + run)
if command -v flatpak &>/dev/null; then
    flatpak install -y flathub com.emudeck.EmuDeck 2>/dev/null || true
fi

echo "[emulation-bundle] done"
