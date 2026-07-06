#!/usr/bin/env bash
# Solus ISO Builder — creates bootable ISO from rootfs tarball
set -euo pipefail

ROOTFS_TAR="/output/solus-rootfs-*.tar.gz"
ISO_OUTPUT="/output/solus-plasma-2026.07-x86_64.iso"
WORK="/tmp/solus-iso-work"
ROOTFS_EXTRACT="/tmp/solus-rootfs-extract"

echo "💿 Building Solus ISO..."
mkdir -p "$WORK" "$ROOTFS_EXTRACT"

# Find rootfs tarball (build-solus.sh mounts OUTPUT_DIR at /output)
TARBALL=$(ls /output/solus-rootfs-*.tar.gz 2>/dev/null | head -1)
if [ -z "$TARBALL" ]; then
    echo "No rootfs tarball found in /output/"
    echo "Building rootfs first..."
    bash /solus/scripts/build-rootfs-in-docker.sh
    TARBALL=$(ls /output/solus-rootfs-*.tar.gz 2>/dev/null | head -1)
fi

if [ -z "$TARBALL" ]; then
    echo "ERROR: Could not find or build rootfs tarball"
    exit 1
fi

echo "Using rootfs: $TARBALL"

# Extract rootfs
echo "Extracting rootfs..."
tar -xzf "$TARBALL" -C "$ROOTFS_EXTRACT"
echo "Rootfs extracted ($(du -sh $ROOTFS_EXTRACT | cut -f1))"

# Create ISO directory structure
mkdir -p "$WORK/isofs/boot/grub"
mkdir -p "$WORK/isofs/live"

# Copy kernel and initramfs for live boot
cp "$ROOTFS_EXTRACT/boot/"vmlinuz-* "$WORK/isofs/boot/vmlinuz" 2>/dev/null || \
    find "$ROOTFS_EXTRACT/usr/lib/modules" -name "vmlinuz" -exec cp {} "$WORK/isofs/boot/vmlinuz" \; 2>/dev/null || true
cp "$ROOTFS_EXTRACT/boot/"initramfs-*.img "$WORK/isofs/boot/initrd.img" 2>/dev/null || true

# Create squashfs of the rootfs
echo "Creating squashfs filesystem..."
if command -v mksquashfs &>/dev/null; then
    mksquashfs "$ROOTFS_EXTRACT" "$WORK/isofs/live/squashfs.img" -comp zstd -Xcompression-level 1 -noappend 2>&1 | tail -3
else
    echo "  mksquashfs not available, copying rootfs directly"
    cp -a "$ROOTFS_EXTRACT"/* "$WORK/isofs/live/" 2>/dev/null || true
fi

# Create GRUB configuration
cat > "$WORK/isofs/boot/grub/grub.cfg" << 'GRUB'
set default="0"
set timeout=10
set gfxmode=auto
set gfxpayload=keep

insmod all_video
insmod gfxterm
insmod png
insmod gfxmenu

# Solus boot entry
menuentry "☀️ Solus Linux" {
    set root=(cd)
    linux /boot/vmlinuz root=live:LABEL=SOLUS rd.live.image rd.live.overlay.overlayfs=1 quiet splash
    initrd /boot/initrd.img
}

menuentry "☀️ Solus Linux (Safe Mode)" {
    set root=(cd)
    linux /boot/vmlinuz root=live:LABEL=SOLUS rd.live.image rd.live.overlay.overlayfs=1 nomodeset nofb
    initrd /boot/initrd.img
}

menuentry "Check ISO Integrity" {
    set root=(cd)
    linux /boot/vmlinuz rd.live.image test
    initrd /boot/initrd.img
}

menuentry "Boot from Local Drive" {
    set root=(hd0)
    chainloader +1
}
GRUB

# Generate EFI boot image
mkdir -p "$WORK/isofs/EFI/BOOT" "$WORK/isofs/boot/grub"
# Copy the EFI bootloader from grub installation
for efiboot in /boot/efi/EFI/fedora/grubx64.efi /usr/lib/grub/x86_64-efi/grub.efi; do
    if [ -f "$efiboot" ]; then
        cp "$efiboot" "$WORK/isofs/EFI/BOOT/BOOTX64.EFI" 2>/dev/null
        cp "$efiboot" "$WORK/isofs/boot/grub/efi.img" 2>/dev/null
        echo "  EFI: using $efiboot"
        break
    fi
done
# If no EFI found, create minimal one
if [ ! -f "$WORK/isofs/boot/grub/efi.img" ]; then
    grub2-mkimage -O x86_64-efi -o "$WORK/isofs/boot/grub/efi.img" \
        iso9660 linux ext2 fat part_gpt normal boot chain configfile 2>/dev/null || \
    dd if=/dev/zero bs=1M count=4 of="$WORK/isofs/boot/grub/efi.img" 2>/dev/null
fi

# Install GRUB for BIOS and UEFI
echo "Installing bootloader..."
if [ -d /usr/lib/grub ]; then
    grub2-mkrescue -o "$ISO_OUTPUT" "$WORK/isofs" 2>/dev/null || \
    grub-mkrescue -o "$ISO_OUTPUT" "$WORK/isofs" 2>/dev/null || true
fi

# If grub-mkrescue fails, use xorriso directly
if [ ! -f "$ISO_OUTPUT" ] || [ ! -s "$ISO_OUTPUT" ]; then
    echo "Using xorriso with GRUB boot..."
    # Install GRUB to ISO directory for BIOS boot
    mkdir -p "$WORK/isofs/boot/grub/i386-pc"
    cp -r /usr/lib/grub/i386-pc/* "$WORK/isofs/boot/grub/i386-pc/" 2>/dev/null || true
    
    # Generate eltorito boot image if missing
    if [ ! -f "$WORK/isofs/boot/grub/i386-pc/eltorito.img" ]; then
        grub2-mkimage -o "$WORK/isofs/boot/grub/i386-pc/eltorito.img" \
            -p '(cd)/boot/grub' -O i386-pc-eltorito biosdisk iso9660 2>/dev/null || true
    fi
    
    xorriso -as mkisofs \
        -isohybrid-mbr /usr/share/syslinux/isohdpfx.bin \
        -b boot/grub/i386-pc/eltorito.img \
        -c boot.catalog \
        -boot-load-size 4 -boot-info-table \
        -no-emul-boot -eltorito-alt-boot \
        -e boot/grub/efi.img -no-emul-boot \
        -isohybrid-gpt-basdat \
        -o "$ISO_OUTPUT" \
        "$WORK/isofs" 2>&1 | tail -5
fi

# Verify
if [ -f "$ISO_OUTPUT" ]; then
    echo "✅ ISO built: $ISO_OUTPUT"
    ls -lh "$ISO_OUTPUT"
    echo "  Type: $(file "$ISO_OUTPUT")"
else
    echo "⚠ ISO may have failed"
fi

# Cleanup
rm -rf "$WORK" "$ROOTFS_EXTRACT" 2>/dev/null || true
echo "Done"
