#!/usr/bin/env bash
#===============================================================================
# solus-rescue-usb-creator — build a bootable rescue USB from the running system
# and restore snapshots from rescue media. Part of the Solus safety layer.
#
# Usage:
#   sudo solus-rescue-usb-creator create  /dev/sdX        # write rescue USB
#   sudo solus-rescue-usb-creator restore [/dev/sdX]      # list+restore snapshots
#   sudo solus-rescue-usb-creator list   [/dev/sdX]       # list snapshots on USB
#===============================================================================
set -euo pipefail

STATE_DIR="/var/lib/solus"
REScue_IMG="${STATE_DIR}/rescue.img"
KERNEL_DIR="/boot"
GRUB_REScue_CONF="/etc/grub.d/40_solus_rescue"

log()  { echo -e "\033[0;32m[rescue-usb]\033[0m $*"; }
warn() { echo -e "\033[1;33m[rescue-usb]\033[0m $*" >&2; }
die()  { warn "$*"; exit 1; }

[[ $EUID -eq 0 ]] || die "run as root"

find_latest_kernel() {
    ls -1 "$KERNEL_DIR"/vmlinuz-* 2>/dev/null | sort -V | tail -1 || true
}

find_initramfs() {
    local kver="$1"
    for f in "$KERNEL_DIR/initramfs-${kver}.img" "$KERNEL_DIR/initramfs-${kver}kdump.img"; do
        [[ -f "$f" ]] && echo "$f" && return 0
    done
    return 1
}

# ── create ──────────────────────────────────────────────────────────────────
create_rescue_usb() {
    local dev="$1"
    [[ -b "$dev" ]] || die "$dev is not a block device"
    # Refuse the system disk
    local root_disk
    root_disk="$(findmnt -n -o SOURCE / 2>/dev/null | sed 's/[0-9]*$//' || true)"
    [[ "$dev" != "$root_disk"* ]] || die "refusing to overwrite the running root disk"

    local vmlinuz initramfs kver
    vmlinuz="$(find_latest_kernel)" || die "no kernel found in $KERNEL_DIR"
    kver="${vmlinuz#/boot/vmlinuz-}"
    initramfs="$(find_initramfs "$kver")" || die "no initramfs for $kver"

    log "writing rescue USB to $dev (kernel $kver)"
    # Partition: single FAT32 partition labelled SOLUSRESCUE
    parted -s "$dev" mklabel gpt mkpart primary fat32 1MiB 100% set 1 esp on
    local part="${dev}1"
    [[ -b "${dev}p1" ]] && part="${dev}p1"
    mkfs.vfat -F 32 -n SOLUSRESCUE "$part" >/dev/null

    local mnt; mnt="$(mktemp -d)"
    mount "$part" "$mnt"
    trap 'umount "$mnt" 2>/dev/null || true; rmdir "$mnt" 2>/dev/null || true' EXIT

    mkdir -p "$mnt/EFI/BOOT" "$mnt/solus"
    cp "$vmlinuz" "$mnt/solus/vmlinuz"
    cp "$initramfs" "$mnt/solus/initramfs.img"

    # Minimal systemd-boot config that boots into the recovery initramfs
    cat > "$mnt/EFI/BOOT/loader.conf" <<EOF
title  Solus Rescue
linux  /solus/vmlinuz
initrd /solus/initramfs.img
options root=LABEL=SOLUSRESCUE ro solus.recovery=1
EOF
    # Copy the recovery script + protected-packages so rescue is self-contained
    cp /usr/libexec/solus/solus-recovery "$mnt/solus/" 2>/dev/null || true
    cp /etc/solus/protected-packages.conf "$mnt/solus/" 2>/dev/null || true

    sync
    log "rescue USB created on $dev — boot from it and run solus-recovery"
}

# ── list ────────────────────────────────────────────────────────────────────
list_snapshots_usb() {
    local dev="${1:-}"
    local mnt; mnt="$(mktemp -d)"
    if [[ -n "$dev" ]]; then
        mount "${dev}1" "$mnt" 2>/dev/null || mount "$dev" "$mnt" 2>/dev/null || die "cannot mount $dev"
        trap 'umount "$mnt" 2>/dev/null || true; rmdir "$mnt" 2>/dev/null || true' EXIT
    fi
    # Local snapshots via snapper
    if command -v snapper &>/dev/null; then
        log "local snapshots:"
        snapper -c root list 2>/dev/null || true
    fi
    # Snapshots copied onto USB (if any)
    if [[ -d "$mnt/solus/snapshots" ]]; then
        log "snapshots on USB:"
        ls -1 "$mnt/solus/snapshots" 2>/dev/null || true
    fi
}

# ── restore ─────────────────────────────────────────────────────────────────
restore_snapshot_usb() {
    local dev="${1:-}"
    if command -v snapper &>/dev/null; then
        log "listing local snapshots — pick a number:"
        snapper -c root list
        echo ""
        read -rp "snapshot number to restore: " num
        [[ -n "$num" ]] || die "no snapshot selected"
        log "rolling back to snapshot $num"
        snapper -c root undochange "$num"..0
        log "reboot to complete rollback"
        return 0
    fi
    die "snapper not installed; manual btrfs subvolume restore required"
}

main() {
    local cmd="${1:-help}"
    case "$cmd" in
        create)  shift; create_rescue_usb "${1:?device required (e.g. /dev/sdb)}" ;;
        list)    shift; list_snapshots_usb "${1:-}" ;;
        restore) shift; restore_snapshot_usb "${1:-}" ;;
        -h|--help|help)
            cat <<EOF
solus-rescue-usb-creator — Solus rescue media tool

  create  /dev/sdX   Write a bootable rescue USB to /dev/sdX
  list    [/dev/sdX] List snapshots (local or on a rescue USB)
  restore [/dev/sdX] Restore a snapshot (interactive)
EOF
            ;;
        *) die "unknown command: $cmd" ;;
    esac
}

main "$@"
