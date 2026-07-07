#!/usr/bin/env bash
# Synthex OOBE bundle: Development
set -euo pipefail
echo "📦 Installing Development bundle..."
sudo dnf install -y git git-core gcc gcc-c++ make cmake
sudo dnf install -y rust cargo rust-src rust-analyzer rustfmt clippy
sudo dnf install -y golang nodejs npm
sudo dnf install -y python3 python3-pip python3-virtualenv
sudo dnf install -y podman buildah skopeo distrobox
sudo dnf install -y podman-compose
sudo dnf install -y docker docker-compose 2>/dev/null || true
sudo dnf install -y qemu-kvm virt-manager libvirt
sudo dnf install -y systemtap gdb valgrind strace ltrace
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
flatpak install -y flathub com.visualstudio.code 2>/dev/null || true
echo "✅ Development bundle installed"
