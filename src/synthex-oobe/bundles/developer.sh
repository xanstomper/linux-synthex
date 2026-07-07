#!/usr/bin/env bash
# Synthex OOBE Bundle — Developer
set -euo pipefail
LOG="/var/log/synthex-oobe-developer.log"
exec 2> >(tee -a "$LOG")

echo "[developer-bundle] installing dev toolchain + containers"
dnf install -y \
    git git-lfs \
    code 2>/dev/null || \
dnf install -y git git-lfs vim-enhanced 2>/dev/null || true

dnf install -y \
    gcc gcc-c++ clang rust cargo go nodejs npm \
    python3 python3-pip python3-virtualenv \
    docker podman buildah skopeo distrobox \
    qemu virt-manager 2>/dev/null || true

systemctl enable --now podman.socket 2>/dev/null || true
systemctl enable --now docker 2>/dev/null || true

flatpak install -y flathub com.visualstudio.code 2>/dev/null || true

echo "[developer-bundle] done"
