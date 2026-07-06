#!/usr/bin/env bash
# setup-flathub.sh — Flathub auto-setup for Solus
# Configures Flathub repository and essential runtimes
set -euo pipefail

echo "📦 Setting up Flathub..."
echo "═" $(printf '═%.0s' $(seq 1 30))

# Install flatpak if not present
if ! command -v flatpak &>/dev/null; then
    echo "Installing Flatpak..."
    sudo dnf install -y flatpak
fi

# Add Flathub remote
echo "Adding Flathub remote..."
sudo flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Add Solus-specific remote
sudo flatpak remote-add --if-not-exists solus https://flatpak.solus-project.org/repo/ 2>/dev/null || true

# Install essential runtimes
echo "Installing essential Flatpak runtimes..."
flatpak install --system -y flathub org.freedesktop.Platform//24.08 2>/dev/null || true
flatpak install --system -y flathub org.freedesktop.Platform.GL.default//24.08 2>/dev/null || true
flatpak install --system -y flathub org.freedesktop.Platform.GL32.default//24.08 2>/dev/null || true
flatpak install --system -y flathub org.kde.Platform//6.8 2>/dev/null || true
flatpak install --system -y flathub org.gnome.Platform//47 2>/dev/null || true

# Install essential apps
echo "Installing recommended Flatpak apps..."
flatpak install --system -y flathub org.mozilla.firefox 2>/dev/null || true
flatpak install --system -y flathub org.gimp.GIMP 2>/dev/null || true

echo ""
echo "✅ Flathub configured"
echo "   Browse: flatpak search <app>"
echo "   Install: flatpak install flathub <app-id>"
