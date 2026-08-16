#!/usr/bin/env bash
# One-shot build: assemble the Synthex live ISO using the official Fedora 42
# kernel + our local repo, inside a Fedora builder image.
#
# Preconditions already met:
#   - Docker daemon running; fedora:41 pulled
#   - local repo populated: build/repo/{noarch,x86_64} (60+ local packages +
#     official Fedora 41 kernel: kernel/kernel-core/modules(-core/-extra))
#   - patched kickstart: build/kickstart/synthex-hyprland-local.ks
#   - build/scripts/build-iso-fixed.sh enforces the 3.8 GiB squashfs gate + unsquashfs check
set -euo pipefail

echo "Running the live-ISO assembly is a LARGE, long network+disk job (installs a full Fedora root ~ several GB)."
echo "It is intended to run as a monitored long job (e.g. overnight). This wrapper documents the exact steps."

PROJECT_ROOT="/home/jewboy420/linux-synthex"
KS="${PROJECT_ROOT}/build/kickstart/synthex-hyprland-local.ks"
OUT="${PROJECT_ROOT}/build/iso-out"
VER="2026.10"

echo "[1/3] build slim Fedora builder image (lorax/livemedia-creator) ..."
cat > /tmp/builder.Dockerfile <<'EOF'
FROM fedora:41
RUN dnf install -y --setopt=install_weak_deps=False --skip-unavailable \
      lorax livemedia-creator pykickstart xorriso squashfs-tools syslinux \
      genisoimage isomd5sum grub2 grub2-tools grub2-efi grub2-pc \
      dnf dnf-utils createrepo_c rpm-build \
    && dnf clean all
EOF
sudo docker build -f /tmp/builder.Dockerfile -t synthex-builder .

echo "[2/3] assembling ISO ..."
sudo docker run --rm --privileged \
  -v "${PROJECT_ROOT}:${PROJECT_ROOT}" \
  -e "KS=$KS" -e "OUT=$OUT" -e "VER=$VER" -e "PR=$PROJECT_ROOT" \
  synthex-builder bash -cx '
      cd "$PR/build" || exit 1
      livecd-creator --verbose --config="$KS" --releasever=42 \
        --title="SynthOS" --product="SynthOS" --vol="SYNTHEX_${VER//./_}" \
        --tmp=/tmp/livecd --compression-type=zstd \
        --keep-image -o "$OUT/Synthex-Hyprland-$VER-x86_64.iso"'

echo "[3/3] validate ..."
ISO="$OUT/Synthex-Hyprland-$VER-x86_64.iso"
if [ -f "$ISO" ]; then
  echo "ISO: $ISO ($(du -h "$ISO"|cut -f1))"
else
  echo "ISO not produced - review livecd-creator output above."
fi