#!/usr/bin/env bash
# build-synthex-kernel.sh — Build the Synthex custom kernel with patches
# Applies BORE scheduler, gaming latency, tickless, and VM tuning patches
# Usage: ./build-synthex-kernel.sh [--install]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KERNEL_SRC="${KERNEL_SRC:-$ROOT/kernel/linux-source}"
KERNEL_VERSION="${KERNEL_VERSION:-$(uname -r | cut -d- -f1)}"
PATCH_DIR="$ROOT/kernel/patches"
CONFIG_DIR="$ROOT/kernel/configs"
BUILD_JOBS="${BUILD_JOBS:-$(nproc)}"

echo "🔨 Synthex Kernel Builder"
echo "  Kernel version: $KERNEL_VERSION"
echo "  Source:         $KERNEL_SRC"
echo "  Patches:        $PATCH_DIR"
echo "  Jobs:           $BUILD_JOBS"
echo ""

# ─── Download kernel source if not present ────────────────────────────
if [ ! -d "$KERNEL_SRC" ]; then
    echo "📥 Downloading kernel $KERNEL_VERSION source..."
    mkdir -p "$KERNEL_SRC"
    cd "$(dirname "$KERNEL_SRC")"
    wget -q "https://cdn.kernel.org/pub/linux/kernel/v$(echo $KERNEL_VERSION | cut -d. -f1).x/linux-$KERNEL_VERSION.tar.xz"
    tar xf "linux-$KERNEL_VERSION.tar.xz"
    mv "linux-$KERNEL_VERSION" "$(basename "$KERNEL_SRC")"
    rm -f "linux-$KERNEL_VERSION.tar.xz"
fi

cd "$KERNEL_SRC"

# ─── Apply patches ────────────────────────────────────────────────────
echo ""
echo "🩹 Applying Synthex kernel patches..."
PATCHES=(
    "synthex-0001-bore-scheduler.patch"
    "synthex-0002-gaming-latency.patch"
    "synthex-0003-tickless-gaming.patch"
    "synthex-0004-vm-gaming-tuning.patch"
)
for patch in "${PATCHES[@]}"; do
    PATCHFILE="$PATCH_DIR/$patch"
    if [ -f "$PATCHFILE" ]; then
        echo "  Applying $patch..."
        if git apply --check "$PATCHFILE" 2>/dev/null || patch -p1 --dry-run < "$PATCHFILE" &>/dev/null; then
            git apply "$PATCHFILE" 2>/dev/null || patch -p1 < "$PATCHFILE"
        else
            echo "  ⚠️  $patch may already be applied, skipping"
        fi
    else
        echo "  ⚠️  $patch not found, skipping"
    fi
done

# ─── Copy defconfig ───────────────────────────────────────────────────
echo ""
echo "📋 Copying Synthex defconfig..."
cp "$CONFIG_DIR/synthex-x86_64-defconfig" "$KERNEL_SRC/.config"
make olddefconfig

# ─── Build kernel ─────────────────────────────────────────────────────
echo ""
echo "🏗️  Building kernel (this takes 10-30 minutes)..."
make -j"$BUILD_JOBS"

# ─── Install (optional) ───────────────────────────────────────────────
if [ "${1:-}" = "--install" ]; then
    echo ""
    echo "📦 Installing kernel..."
    sudo make modules_install
    sudo make install
    echo "  Generating initramfs..."
    sudo dracut --force --regenerate-all
    echo "  Updating GRUB..."
    sudo grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || \
        sudo grub2-mkconfig -o /boot/efi/EFI/synthex/grub.cfg 2>/dev/null || true
    echo ""
    echo "✅ Kernel installed. Reboot to use."
else
    echo ""
    echo "✅ Kernel built. Run with --install to install."
    echo "  Output: $KERNEL_SRC/arch/x86/boot/bzImage"
fi
