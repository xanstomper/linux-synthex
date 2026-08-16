# Kernel Configuration Files (reference)

These are the **in-repo kernel reference files**. Important context:
**we ship the official Fedora kernel**, not a build from these. They are
kept as documentation of the intended tuning and as an aspirational
build spec. (See also `docs/KERNEL.md`.)

## `kernel/synthex-kernel.spec` (322 lines)

The **aspirational custom-kernel RPM** spec. Not built on the host
today. Variants: `--with v3` (x86-64-v3, default),
`--with v4` (x86-64-v4), `--without custom` (generic).

Highlights:
- BORE scheduler patch (`firelzrd/bore-scheduler` target patchset).
- CachyOS hardening, futex2, btrfs zstd-fast, CPU-optimization patches.
- `CONFIG_RUST=y` support (why it can’t build here — ken needs matching
  rust-toolchain/clang/rust-std).
- Multiple subpackages: `core`, `devel`, `modules`, `headers`.
- It references external patch URLs (may not exist at the exact path).

> **Decision:** we do NOT build this. We vendor the Fedora kernel RPMs
> instead. See `docs/KERNEL.md`.

## `kernel/config-x86_64` (875 lines) — the (renamed) "-solus" config

This is a full `.config` for an `x86_64` build. Milestones:

- `CONFIG_LOCALVERSION="-solus"` ← **leftover branding (Solus)**
- `CONFIG_SCHED_BORE=y` + BORE tuning
- `CONFIG_SCHED_CLUSTER=y`
- `CONFIG_PREEMPT_FULL=y`, `CONFIG_PREEMPT_DYNAMIC=y`
- `CONFIG_NO_HZ=y`, `CONFIG_NO_HZ_IDLE=y`, `CONFIG_NO_HZ_FULL=y`
- `CONFIG_HZ_1000=y`
- `CONFIG_X86_INTEL_PSTATE=y`, `CONFIG_X86_AMD_PSTATE_CPPC=y`,
  `CONFIG_X86_AMD_PSTATE_DEFAULT_MODE=3`
- `CONFIG_DRM_I915=y`, `CONFIG_DRM_AMDGPU=y`
- `CONFIG_IO_URING=y`

It is saved with the localversion `-solus` which is **incorrect** for
the renamed distro. If it is ever revived, `CONFIG_LOCALVERSION` should
become `-synthex` (or leave it unset and let the pkg set it).

## `kernel/configs/synthex-x86_64-defconfig` (202 lines)

The human-readable **defconfig** (the "read me" version of the config).
Same idea; documented with comments. Key differences to stock kernel:

- `CONFIG_PREEMPT=y` (low latency)
- `CONFIG_HZ=1000`
- `CONFIG_NO_HZ_FULL=y`
- `CONFIG_SCHED_BORE=y`
- `CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y`
- `CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=y`
- `CONFIG_ZRAM=y`
- `CONFIG_BTRFS_FS=y`
- `CONFIG_ZSTD_COMPRESSION=y`

## `kernel/cmdline.default` (80 lines)

The intended boot command line (used by GRUB/systemd-boot). Contents
(and, again, titled "Linux Solus" — legacy):

```
quiet splash
rw
nowatchdog
amd-pstate=active
intel_pstate=active
cpufreq.default_governor=schedutil
processor.max_freq=0
rd.luks=1 rd.lvm=1 rd.md=1 rd.dm=1
```

## `kernel/dracut.conf` (44 lines)

Initramfs generation policy:

- `hostonly="yes"`
- `compress="zstd"` `compress_args="-1"` (fastest decompression)
- `add_drivers+=" btrfs crc32c-intel nvme ahci xhci-pci amdgpu i915
  nvidia_drm nvidia_modeset nvidia btrfs ext4 xfs vfat "`

## `kernel/synthex-kernel-config.md` (197 lines)

A markdown explanation of the kernel tuning (scheduler, IO scheduling,
GPU, storage, security) — the rationale behind the `-solus`-era config.

## `kernel/build.sh` (376 lines)

The kernel builder wrapper (on the Fedora/host side). Downloads kernel
source, applies patches, configures, runs `make`, packages.

---

## Re-name / hygiene TODO

Because the project renamed from **Solus** to **Synth/Synthex**, and
because we **don’t build a custom kernel**, these files are best:

1. `kernel/config-x86_64` → set `CONFIG_LOCALVERSION="-synthex"` if ever
   revived, and fix the local `-solus` string.
2. `kernel/cmdline.default` → change the header comment "Linux Solus" →
   "SynthOS".
3. `kernel/configs/synthex-x86_64-defconfig` → same cleanup.
4. Decide: keep as reference (recommended) or delete.

This is documentation, not runtime — nothing ships these values.

## Related

- `docs/KERNEL.md` — why we use the Fedora kernel + what it enables.
- `docs/PERFORMANCE.md` — the userspace tuning that rides on top.