# Boot & Live Session

What happens when a SynthOS ISO powers on, from firmware to the live
desktop. (The pre-existing `docs/architecture/synthex-architecture.md`
has a compat diagram too; this is the current walk-through.)

## Stage 0 — firmware / bootloader

```
[UEFI/BIOS firmware]
   → read the EFI System Partition
   → load shim (Secure Boot, optional)
   → BOOTX64.efi (grub2-efi)
       reads grub.cfg on the ISO
```

The ISO root carries GRUB 2 (EFI + BIOS). `grub.cfg` (written by
`build/scripts/build-iso-fixed.sh`) presents menu entries:

```
☀️ SynthOS (Live) -- rd.live
☀️ SynthOS (Safe Graphics)
🔄 Reboot
🛑 Power Off
```

Kernel args for Live:

```
linux /boot/vmlinuz \
   root=live:LABEL=SYNTHEX \
   rd.live.image rd.live.overlay=1 quiet splash
initrd /boot/initrd.img
```

Safe Graphics adds `nomodeset`.

## 2 — kernel + initramfs

- `vmlinuz` = the **Fedora 41 kernel** (6.11.4-301.fc41) vendored in
  `build/repo/x86_64/`. It is **never** the host's Ubuntu kernel
  (`build-iso-fixed.sh` rejects that).
- `initrd.img` = a Fedora dracut regular (or **host-only**) initramfs
  built from `kernel/dracut.conf` — zstd-compressed, includes
  `btrfs nvme ahci amdgpu i915 nvidia_drm …`.

Dracut reads `rd.live.image` and mounts the ISO's
`/LiveOS/squashfs.img`.

## 3 — the LiveOS squashfs

`/LiveOS/squashfs.img` (zstd, compressed) contains `/LiveOS/rootfs.img`
(an ext4 loopback). Dracut:

1. mounts `squashfs.img` (ro),
2. mounts `rootfs.img` (rw, overlay),
3. switches root to the mounted live root.

This is the canonical Fedora live-layout the corrected build produces
(`/LiveOS/squashfs.img` → `/LiveOS/rootfs.img`), not the older
Debian-casper `/live/` path.

## 4 — the Live session

Once root is switched, `systemd` takes over:

- `synthex-live-setup.service` (gated by `ConditionPathExists
  /etc/synthex/live-mode`) runs — see `configs/live/live-setup.sh`.
- `synthex-defaults.service` enables the differentiator units on the
  live session (predictive, brain, hermes, zram, snapper timers).
- GTK desktop (Hyprland) starts via greetd (Hyprland edition) or SDDM
  (Plasma edition). A `liveuser` is created.
- The user can:
  - click **Install SynthOS** (`install-synthex.desktop`) → Calamares
    writes the root filesystem to a target disk and reboots,
  - and/or explore the live environment.

## 5 — after install

On the installed disk, the bootloader now points at the installed
`/boot`, the installed kernel, and a Btrfs root. The
`synthex-firstboot.service` guides the new user (OOBE), and the
`%post`-enabled services (persona, AIOS, etc.) start normally.

---

## The two boot paths in one metro

```
FIRMWARE
   │
   ├─ (ISO, live)  GRUB → vmlinuz(initrd) → LiveOS squashfs → rootfs.img → desktop
   │                 (rd.live.image)  (ext4)      *
   └─ (disk)       GRUB → vmlinuz → initrd → btrfs root → desktop
```
`*` the corrected `build/scripts/build-iso-fixed.sh` enforces
`/LiveOS/squashfs.img` < 3.8 GiB and validates `unsquashfs -stat`.

## Boot-time performance knobs (from kernel/cmdline.default)

```
quiet splash           # Plymouth
nowatchdog
amd-pstate=active
intel_pstate=active
cpufreq.default_governor=schedutil
rd.luks=1 rd.lvm=1 rd.md=1 rd.dm=1   # LUKS/LVM/MD support
```

These are documentation (see `docs/KERNEL-CONFIG.md`); the live GRUB
entry uses the minimal `rd.live` set above.