#!/usr/bin/env bash
# Solus OOBE bundle: Office
set -euo pipefail
echo "📦 Installing Office bundle..."
sudo dnf install -y libreoffice libreoffice-langpack-en libreoffice-calc libreoffice-writer libreoffice-impress
sudo dnf install -y thunderbird
sudo dnf install -y evince
sudo dnf install -y okular
echo "✅ Office bundle installed"
