#!/usr/bin/env bash
# SynthOS Nova — apply GNOME defaults for the current user (real gsettings calls)
set -euo pipefail
gsettings set org.gnome.desktop.interface gtk-theme 'Synthex-dark'
gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark'
gsettings set org.gnome.desktop.interface cursor-theme 'Synthex-Cursor'
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface font-name 'Inter 10'
gsettings set org.gnome.desktop.interface monospace-font-name 'JetBrains Mono 10'
gsettings set org.gnome.desktop.background picture-uri-dark 'file:///usr/share/wallpapers/synthex-nova.png'
gsettings set org.gnome.shell favorite-apps "['firefox.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.Console.desktop', 'synthex-control-center.desktop']"
echo "SynthOS GNOME defaults applied."
