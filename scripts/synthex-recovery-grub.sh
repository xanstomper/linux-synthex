#!/usr/bin/env bash
# Synthex GRUB Recovery Entry Generator
# Adds BTRFS snapshot rollback + rescue entries to GRUB.
# Run after kernel updates or at first boot if recovery entries are missing.
set -euo pipefail

GRUB_CFG="/boot/grub2/grub.cfg"
if [ ! -f "$GRUB_CFG" ]; then
    GRUB_CFG="/boot/efi/EFI/synthex/grub.cfg"
fi
if [ ! -f "$GRUB_CFG" ]; then
    echo "No GRUB config found"; exit 0
fi

RECOVERY_CFG="/etc/grub.d/15_synthex_recovery"
cat > "$RECOVERY_CFG" << 'EOGRUB'
#!/bin/bash
cat << 'RECENTRY'
menuentry "SynthOS (Recovery — Snapshot Rollback)" {
    set root=(cd)
    linux /boot/vmlinuz root=live:LABEL=SYNTHEX rd.live.image rd.live.overlay.overlayfs=1 quiet splash
    initrd /boot/initrd.img
}

menuentry "SynthOS (Rescue Shell)" {
    set root=(cd)
    linux /boot/vmlinuz root=live:LABEL=SYNTHEX rd.live.image rd.live.overlay.overlayfs=1 rescue quiet
    initrd /boot/initrd.img
}
RECENTRY
EOGRUB
chmod +x "$RECOVERY_CFG"

echo "Recovery GRUB entries configured"
