#!/bin/bash
# Solus GRUB2 Configuration Generator
# Generates /etc/grub.d/ files for Solus-branded GRUB with recovery and snapshot entries
# Run after kernel updates: grub2-mkconfig -o /boot/grub2/grub.cfg

SOLUS_THEME="/usr/share/grub/themes/solus/theme.txt"
GRUB_CONFIG_DIR="/etc/grub.d"

# ─── 00_header — Basic GRUB settings ──────────────────────────────

cat > "${GRUB_CONFIG_DIR}/00_header" << 'HEADER'
#!/bin/sh
set -e

# Solus GRUB Configuration
GRUB_TIMEOUT=10
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=saved
GRUB_SAVEDEFAULT=true
GRUB_GFXMODE=1920x1080,auto
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_TERMINAL_OUTPUT=gfxterm
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash rd.luks=1 rd.lvm=1 rd.md=1 rd.dm=1 rd.auto=1"
GRUB_CMDLINE_LINUX=""
GRUB_DISABLE_RECOVERY=false
GRUB_DISABLE_OS_PROBER=false
GRUB_ENABLE_BLSCFG=false

# Enable serial console for debugging
GRUB_SERIAL_COMMAND="serial --speed=115200 --unit=0 --word=8 --parity=no --stop=1"

# Theme
GRUB_THEME=/usr/share/grub/themes/solus/theme.txt

# Background
GRUB_BACKGROUND=/usr/share/wallpapers/solus/grub-background.png

# Color
GRUB_COLOR_NORMAL="white/black"
GRUB_COLOR_HIGHLIGHT="$SOLUS_AMBER/black"
HEADER
chmod +x "${GRUB_CONFIG_DIR}/00_header"

# ─── 10_linux — Enhanced Linux boot entries ───────────────────────

cat > "${GRUB_CONFIG_DIR}/10_linux" << 'LINUX'
#!/bin/sh
set -e

. /usr/lib/grub/grub-mkconfig_lib

# Find all kernels
for kernel in /boot/vmlinuz-*; do
    [ -f "$kernel" ] || continue
    version="${kernel#/boot/vmlinuz-}"
    initrd="/boot/initramfs-${version}.img"
    
    if [ ! -f "$initrd" ]; then
        continue
    fi
    
    # Check if this is the latest kernel
    latest_kernel=$(ls -1 /boot/vmlinuz-* | sort -V | tail -1)
    is_latest="false"
    [ "$kernel" = "$latest_kernel" ] && is_latest="true"
    
    echo ""
    
    if [ "$is_latest" = "true" ]; then
        echo "menuentry '☀️ Solus Linux ($version)' --class solus --class gnu-linux --class gnu --class os {"
    else
        echo "menuentry '☀️ Solus Linux ($version)' --class solus --class gnu-linux --class gnu --class os --unrestricted {"
    fi
    
    cat << ENTRY
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    insmod btrfs
    
    search --no-floppy --fs-uuid --set=root $(grub2-get-kernel-uuid $kernel 2>/dev/null || echo "ROOT_UUID")
    
    echo "Loading kernel $version ..."
    linux ${kernel} root=UUID=$(blkid -s UUID -o value /dev/root 2>/dev/null || echo "ROOT_UUID") ro quiet splash rd.luks=1 rd.lvm=1
    echo "Loading initial ramdisk ..."
    initrd ${initrd}
}
ENTRY
    
    # Recovery entry
    echo "menuentry '☀️ Solus Linux ($version) — Recovery Mode' --class recovery --class gnu-linux --class gnu --class os {"
    cat << RECOVERY
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    insmod btrfs
    
    search --no-floppy --fs-uuid --set=root ROOT_UUID
    
    echo "Loading kernel $version (recovery mode)..."
    linux ${kernel} root=UUID=ROOT_UUID ro single quiet splash systemd.unit=rescue.target
    echo "Loading initial ramdisk ..."
    initrd ${initrd}
}
RECOVERY
    
done
LINUX
chmod +x "${GRUB_CONFIG_DIR}/10_linux"

# ─── 30_solus — Solus-specific entries ────────────────────────────

cat > "${GRUB_CONFIG_DIR}/30_solus" << 'SOLUS'
#!/bin/sh
set -e

echo ""
echo "# Solus Recovery and Utility Entries"
echo ""

# Last Known Good entry
echo "menuentry '🔄 Solus — Last Known Good' --class recovery --class gnu-linux --class gnu --class os {"
cat << RECOVERY
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    insmod btrfs
    
    search --no-floppy --fs-uuid --set=root ROOT_UUID
    
    # Mount root and rollback to previous snapshot
    echo "Rolling back to last known good state..."
    linux /boot/vmlinuz-* root=UUID=ROOT_UUID ro quiet splash solus.recovery=rollback
    initrd /boot/initramfs-*.img
}
RECOVERY

# Snapshot Boot entry
echo "menuentry '📸 Solus — Boot from Snapshot' --class recovery --class gnu-linux --class gnu --class os {"
cat << SNAPSHOT
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    insmod btrfs
    
    search --no-floppy --fs-uuid --set=root ROOT_UUID
    
    echo "Loading snapshot boot environment..."
    linux /boot/vmlinuz-* root=UUID=ROOT_UUID ro quiet splash solus.recovery=list
    initrd /boot/initramfs-*.img
}
SNAPSHOT

# Recovery Mode
echo "menuentry '🔧 Solus — Recovery Environment' --class recovery --class gnu-linux --class gnu --class os {"
cat << RECOVERY_MENU
    load_video
    set gfxpayload=keep
    insmod gzio
    insmod part_gpt
    insmod ext2
    insmod btrfs
    
    search --no-floppy --fs-uuid --set=root ROOT_UUID
    
    echo "Loading recovery environment..."
    linux /boot/vmlinuz-* root=UUID=ROOT_UUID ro quiet splash solus.recovery=1 systemd.unit=multi-user.target
    initrd /boot/initramfs-*.img
}
RECOVERY_MENU

# Firmware Setup
echo "menuentry '⚙ System Firmware Setup' --class firmware --class os {"
cat << FIRMWARE
    fwsetup
}
FIRMWARE

# Memory Test
if [ -f /boot/memtest86+/memtest.bin ]; then
    echo "menuentry '🧠 Memory Test (memtest86+)' --class memtest86 --class os {"
    echo "    linux16 /boot/memtest86+/memtest.bin"
    echo "}"
fi
SOLUS
chmod +x "${GRUB_CONFIG_DIR}/30_solus"

# ─── 40_custom — User custom entries ──────────────────────────────

cat > "${GRUB_CONFIG_DIR}/40_custom" << 'CUSTOM'
#!/bin/sh
set -e

# Add custom boot entries here
# This file will be preserved on updates
CUSTOM
chmod +x "${GRUB_CONFIG_DIR}/40_custom"

# ─── Generate GRUB config ─────────────────────────────────────────

echo "📝 Generating GRUB configuration..."
grub2-mkconfig -o /boot/grub2/grub.cfg

echo "✅ GRUB configuration complete!"
echo ""
echo "Boot entries created:"
echo "  1. ☀️ Solus Linux (latest kernel)"
echo "  2. ☀️ Solus Linux (previous kernel)"
echo "  3. ☀️ Solus Linux (Recovery Mode)"
echo "  4. 🔄 Solus — Last Known Good"
echo "  5. 📸 Solus — Boot from Snapshot"
echo "  6. 🔧 Solus — Recovery Environment"
echo "  7. ⚙ System Firmware Setup"
echo ""
echo "Theme: Solus Amber (#FFB300)"
echo "Timeout: 10 seconds"
echo "Default: Saved last boot"
