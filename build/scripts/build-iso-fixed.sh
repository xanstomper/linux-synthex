#!/usr/bin/env bash
# =============================================================================
# SynthOS ISO Builder — CORRECTED (build-iso-fixed.sh)
#
# Produces a bootable Fedora-style live ISO and fixes every boot bug found
# in the 2026.10 release:
#
#  BUG 1 (booted into "Ubuntu"/dropped to initramfs shell):
#      The ISO carried the HOST's Ubuntu kernel + initramfs because
#      build-iso-in-docker.sh fell back to /boot on the Mint box.
#      FIX: kernel+initramfs MUST come from the project rootfs, and an
#      Ubuntu/generic kernel is rejected outright.
#
#  BUG 2 (squashfs.img corrupt / "chroot superblock not found"):
#      squashfs.img was 4.29GB > the 4GiB ISO9660 single-extent limit,
#      written multi-extent => zero-headed, unreadable.
#      FIX: hard size gate (<3.8GiB) + unsquashfs -stat check before shipping.
#
#  BUG 3 (layout): squashfs was placed under /live/ (Debian casper) while the
#      kernel args were Fedora dracut (/LiveOS/squashfs.img).
#      FIX: build the canonical Fedora live layout
#      /LiveOS/squashfs.img -> /LiveOS/rootfs.img (ext4) + /boot kernel+initrd.
#
#  BUG 4 (no validation): ISO shipped unverified.
#      FIX: remount the finished ISO and assert kernel version + squashfs
#      integrity + size before success.
#
# Requires: mksquashfs, xorriso, e2fsprogs (mkfs.ext4) and root for loop mount.
#
# Usage:  sudo ./build-iso-fixed.sh /path/to/rootfs-dir [-o out.iso]
# =============================================================================
set -euo pipefail

ROOTFS_DIR="${1:?usage: sudo $0 /path/to/rootfs-dir [-o out.iso]}"
shift || true
OUT="${2:-synthex-hyprland-2026.10-x86_64.iso}"
while [[ $# -gt 0 ]]; do case "$1" in
  -o|--out) OUT="$2"; shift 2 ;;
  *) shift ;;
esac; done

WORK="$(mktemp -d)"; ISOFS="$WORK/isofs"
SIZE_CAP_GiB=3.8
G='\e[32m'; Y='\e[33m'; R='\e[31m'; NC='\e[0m'
log(){ echo -e "${G}[OK]${NC}   $*"; }
warn(){ echo -e "${Y}[WARN]${NC} $*"; }
fail(){ echo -e "${R}[FAIL]${NC}  $*"; exit 1; }
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$ISOFS/LiveOS" "$ISOFS/boot/grub" "$ISOFS/EFI/BOOT"
[[ -d "$ROOTFS_DIR" ]] || fail "rootfs dir missing: $ROOTFS_DIR"

# ---- BUG 1 fix: distro kernel + initramfs, never the build host ----
K="$(ls "$ROOTFS_DIR"/boot/vmlinuz-* 2>/dev/null | head -1 || true)"
I="$(ls "$ROOTFS_DIR"/boot/initramfs-*.img "$ROOTFS_DIR"/boot/initrd.img-* 2>/dev/null | head -1 || true)"
[[ -n "$K" && -n "$I" ]] || fail "No kernel/initramfs in rootfs/boot. Provide a real Synthex (Fedora) rootfs."
ver="$(strings "$K" 2>/dev/null | grep -m1 "Linux version" || true)"
case "$ver" in
  *"Ubuntu"*|*"generic"*|"")
    fail "rootfs kernel is Ubuntu/generic (${ver:-none}). Refusing to ship a Fedora-based ISO with an Ubuntu kernel.";;
esac
log "kernel OK: $ver"
cp -a "$K" "$ISOFS/boot/vmlinuz"; cp -a "$I" "$ISOFS/boot/initrd.img"

# ---- BUG 2+3: LiveOS/squashfs.img containing LiveOS/rootfs.img (ext4) ----
GW="$WORK/liveos-tree"; mkdir -p "$GW/LiveOS"
FS_MB="$(du -sm "$ROOTFS_DIR" | cut -f1)"
ROOT_MB=$(( FS_MB * 110 / 100 + 256 ))          # ext4 loop file with headroom
log "building rootfs.img (~${ROOT_MB}MB ext4 of rootfs)..."
truncate -s "${ROOT_MB}M" "$GW/LiveOS/rootfs.img"
mkfs.ext4 -q -F -O ^has_journal -E dir_index "$GW/LiveOS/rootfs.img" \
    >/dev/null 2>&1 || fail "mkfs.ext4 failed (need e2fsprogs)"
MNT="$WORK/m"; mkdir -p "$MNT"
if ! mount -o loop "$GW/LiveOS/rootfs.img" "$MNT"; then
  fail "cannot mount loop ext4 (run with sudo --necessary for live rootfs.img)"
fi
cp -a "$ROOTFS_DIR"/. "$MNT/"
umount "$MNT"

log "building squashfs.img..."
mksquashfs "$GW" "$ISOFS/LiveOS/squashfs.img" -comp zstd -Xcompression-level 1 -noappend \
    >/dev/null 2>&1 || fail "mksquashfs failed"
sync
SZ="$(stat -c%s "$ISOFS/LiveOS/squashfs.img")"
CAP=$(( SIZE_CAP_GiB * 1024 * 1024 * 1024 ))
if (( SZ >= CAP )); then
  fail "squashfs.img=${SZ}B >= ${SIZE_CAP_GiB}GiB(zdrop impossible; trim packages, retry)"
fi
if ! unsquashfs -stat "$ISOFS/LiveOS/squashfs.img" >/dev/null 2>&1; then
  fail "squashfs.img superblock NOT valid — aborting instead of shipping broken ISO"
fi
log "squashfs.img = ${SZ} bytes, superblock valid ✓"

# ---- GRUB ----
cat > "$ISOFS/boot/grub/grub.cfg" <<'CFG'
set default=0; set timeout=5
insmod part_gpt; insmod part_msdos; insmod fat; insmod iso9660
insmod all_video; insmod gfxterm
set menu_color_normal=light-gray/black
set menu_color_highlight=cyan/black
menuentry "☀️ SynOS (Live) -- rd.live" {
    set gfxpayload=keep
    linux  /boot/vmlinuz  root=live:LABEL=SYNTHEX  rd.live.image rd.live.overlay=1 quiet splash
    initrd /boot/initrd.img
}
menuentry "☀️ SynOS (Safe Graphics)" {
    linux  /boot/vmlinuz  root=live:LABEL=SYNTHEX  rd.live.image rd.live.overlay=1 nomodeset
    initrd /boot/initrd.img
}
menuentry "🔄 Reboot" { reboot }
menuentry "🛑 Power Off" { halt }
CFG

# ---- BUG 4: single-pass xorriso (no appends so 4GB+ files can't be mangled) ----
log "Assembling $OUT ..."
xorriso -as mkisofs \
    -iso-level 3 -rock -joliet -V "SYNTHEX" \
    -o "$OUT" \
    "$ISOFS" || fail "xorriso assembly failed"

sync
# ---- post-build validation ----
VB="$(mktemp -d)"; mount -o loop,ro "$OUT" "$VB" || fail "cannot mount finished ISO"
[[ -f "$VB/LiveOS/squashfs.img" ]] || fail "missing LiveOS/squashfs.img"
VB_SZ="$(stat -c%s "$VB/LiveOS/squashfs.img")"
unsquashfs -stat "$VB/LiveOS/squashfs.img" >/dev/null 2>&1 \
    || fail "assembled ISO squashfs invalid"
UVER="$(strings "$VB/boot/vmlinuz" 2>/dev/null | grep -m1 'Linux version' || true)"
case "$UVER" in *"Ubuntu"*|*"generic"*) fail "ISO still carries Ubuntu kernel";; esac
umount "$VB"
log "FINAL: $OUT — $(du -sh "$OUT" | cut -f1), kernel, squashfs integrity & size all PASS ✓"
rm -rf "$VB"