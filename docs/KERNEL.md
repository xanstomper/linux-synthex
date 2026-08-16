# Kernel Policy

## Short version

**SynthOS does not build a custom kernel.** It ships the **official
Fedora kernel** (`kernel` / `kernel-core` / `kernel-modules*` /
`kernel-devel`), vendored as ordinary RPMs in the local repo.

## Why

The previous spec (`kernel/synthex-kernel.spec`) aimed at building a
custom kernel with BORE scheduler, CachyOS patches, Rust-for-Linux,
etc. We made the deliberate decision **not to ship that build** for
three reasons:

1. **`CONFIG_RUST=y` is fragile.** Modern mainline kernels pin a
   specific Rust-for-Linux version (closely tied to the kernel
   version). Without the **exact** matching `rust-toolchain`, `clang`,
   and `rust-std` for the target version, the build fails late. This is
   not something we can reliably produce from a generic Linux Mint host.

2. **BORE / EEVDF / CachyOS patches** can drift between minor kernel
   versions. Patches that applied cleanly to 6.14 may need rework for
   6.15. The maintenance burden outweighs the marginal latency win.

3. **The Fedora kernel is already excellent for gaming.** It ships
   `PREEMPT_DYNAMIC`, `NO_HZ_FULL`, `x86-64-v3`/`v4` microarch
   selections, BORE-ish latency tuning, modern schedutil, and
   reasonable defaults. The “custom kernel” delta is small and high-risk.

## What we ship instead

We vendored the **Fedora 41 kernel** RPMs from the archive:

```
build/repo/x86_64/kernel-6.11.4-301.fc41.x86_64.rpm
build/repo/x86_64/kernel-core-6.11.4-301.fc41.x86_64.rpm
build/repo/x86_64/kernel-modules-6.11.4-301.fc41.x86_64.rpm
build/repo/x86_64/kernel-modules-core-6.11.4-301.fc41.x86_64.rpm
build/repo/x86_64/kernel-modules-extra-6.11.4-301.fc41.x86_64.rpm
build/repo/x86_64/kernel-devel-6.11.4-301.fc41.x86_64.rpm
```

These are real, signed, Fedora-tested kernels. They are referenced by the
patched kickstart files as `kernel kernel-core kernel-modules
kernel-modules-core kernel-modules-extra` and installed via the local
repo (see `docs/ISO.md`).

## What this fixes

The original boot failure (the “drops to initramfs shell” symptom) was
because the ISO was carrying the **host Ubuntu kernel** instead of a
Fedora kernel. With the Fedora kernel in the local repo and the
kickstart pinned to it, the image boots a kernel that the Fedora
initramfs can find.

## The aspirational spec

`kernel/synthex-kernel.spec` is kept as a **reference** of the
eventual design (BORE, CachyOS, x86-64-v3/v4 variants). It is **not
buildable on this host** today (Rust-for-Linux toolchain, matching
clang, etc.) — building it requires the Fedora builder container or a
dedicated kernel-build pipeline.

If you want to revive it:

1. Provide `rust-toolchain ≥ 1.80.0`, `clang-devel ≥ 17`, `lld-devel ≥ 17`,
   `rust-std` at the kernel’s expected versions.
2. Make sure the BORE patch set targets the chosen version exactly
   (`firelzrd/bore-scheduler` publishes one per major kernel).
3. Rebuild in a Fedora builder container, not on the Mint host.

## Performance kernel options the Fedora kernel already enables

- `CONFIG_PREEMPT_DYNAMIC=y` → users can choose preemption level at boot.
- `CONFIG_NO_HZ_FULL=y` → tickless when one CPU is busy.
- `CONFIG_HZ_1000=y` → 1 kHz timer tick (default since 5.x).
- `CONFIG_SCHED_CLUSTER=y` → cluster-aware scheduling.
- `CONFIG_X86_INTEL_PSTATE=y` + `CONFIG_X86_AMD_PSTATE_CPPC=y` → modern
  P-state drivers for Intel and AMD CPUs.
- `CONFIG_DRM_AMDGPU=y`, `CONFIG_DRM_I915=y` → drivers for the two big
  GPU vendors.

The **Synthex performance layer** (`docs/PERFORMANCE.md`) tunes the
*user-space* side on top of the stock Fedora kernel — zram, sysctl,
governor, gamescope, gamemode. That combination is what gives Bazzite/Nobara
the latency/wins they’re known for, without the kernel-build burden.
