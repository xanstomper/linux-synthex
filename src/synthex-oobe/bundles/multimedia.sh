#!/usr/bin/env bash
# Synthex OOBE bundle: Multimedia
set -euo pipefail
echo "📦 Installing Multimedia bundle..."
sudo dnf install -y obs-studio kdenlive gimp krita inkscape blender
sudo dnf install -y vlc haruna elisa
sudo dnf install -y ffmpeg ffmpeg-plugins
sudo dnf install -y gstreamer1-plugins-ugly gstreamer1-plugins-bad-free gstreamer1-plugins-good
sudo dnf install -y pipewire wireplumber pipewire-alsa pipewire-pulseaudio
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
echo "✅ Multimedia bundle installed"
