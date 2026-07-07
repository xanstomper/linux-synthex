# SynthOS Kernel Patches

This directory contains patches applied to the SynthOS kernel for performance,
desktop responsiveness, gaming, and security enhancements.

## Patch Index

| # | Patch | Source | Description |
|---|-------|--------|-------------|
| 1 | `sched_bore.patch` | [firelzrd/bore-scheduler](https://github.com/firelzrd/bore-scheduler) | **BORE Scheduler**: Burst-Oriented Response Enhancer. Improves desktop interactivity by boosting the priority of tasks that wake up after sleeping (interactive workloads) while preventing CPU-bound tasks from monopolizing cores. |
| 2 | `cachyos-harder.patch` | [CachyOS/kernel-patches](https://github.com/CachyOS/kernel-patches) | **Hardening & Performance**: Additional compiler hardening (CFI, struct randomization), scheduler tweaks, and cache optimizations from the CachyOS project. |
| 3 | `futex2.patch` | [CachyOS/kernel-patches](https://github.com/CachyOS/kernel-patches) | **Futex2 Support**: Enables the futex2 syscall interface required by modern Proton/Wine (PROTON_GE) and other gaming compatibility layers for improved synchronization performance. |
| 4 | `btrfs-zstd-fast.patch` | [CachyOS/kernel-patches](https://github.com/CachyOS/kernel-patches) | **BTRFS zstd-fast**: Adds faster BTRFS compression levels for zstd, allowing compression at levels 1-3 with better throughput while maintaining reasonable compression ratios. |
| 5 | `clear-pkeys.patch` | [Clear Linux](https://clearlinux.org) | **Memory Protection Keys**: Enables userspace protection keys for finer-grained memory protection, improving security isolation between processes. |
| 6 | `lru-multigen.patch` | Linux Kernel (backport) | **Multi-Gen LRU**: Multi-Generational LRU framework for more efficient page reclaim, reducing memory pressure during gaming and heavy workloads. |
|| 5 | `synthex-0005-rust-for-linux.patch` | SynthOS Team | **Rust for Linux**: Enables Rust support on x86_64 (upstream in 6.14+). Adds `CONFIG_RUST=y` and Rust-based PHY driver support to the default kernel configuration. Requires rustc >= 1.80.0 to build. |
|| 7 | `bcachefs.patch` | [bcachefs](https://bcachefs.org) | **bcachefs Filesystem**: Support for the bcachefs copy-on-write filesystem (if not yet merged upstream at the time of this kernel build). |

## Applying Patches

Patches are applied automatically by `build.sh` during the build process.
To apply manually:

```bash
cd linux-<version>
patch -p1 < patches/sched_bore.patch
patch -p1 < patches/cachyos-harder.patch
patch -p1 < patches/futex2.patch
patch -p1 < patches/btrfs-zstd-fast.patch
```

## Patch Order

Patches must be applied in the order listed above — later patches may depend
on context established by earlier ones. The `build.sh` script handles this ordering.

## Customizing Patch Selection

To disable a patch during build, either:
1. Remove or rename the patch file (e.g., `mv futex2.patch futex2.patch.disabled`)
2. Edit `build.sh` and comment out the `apply_patch` line for that patch

## Obtaining Patches

The BORE scheduler patch for the current kernel version can be downloaded from:
https://github.com/firelzrd/bore-scheduler

CachyOS patches for the current kernel version can be found at:
https://github.com/CachyOS/kernel-patches

## Compatibility

Patches are version-specific. Each patch targets a particular kernel version
(e.g., 6.14.x). Using patches from a different kernel version will likely
result in patch failures. Check the `build.sh` `DEFAULT_KERNEL_VERSION` variable
to ensure patches match.
