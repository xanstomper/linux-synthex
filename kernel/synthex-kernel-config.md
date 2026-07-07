# SynthOS Kernel Configuration Philosophy

## Overview

The SynthOS kernel configuration is designed around a single principle:
**maximum desktop responsiveness without sacrificing security or modern
hardware support**. It targets interactive users — developers, gamers,
creative professionals — who need a kernel that stays out of their way.

## Core Design Goals

### 1. Desktop Responsiveness (Primary)

- **PREEMPT_FULL** is enabled for the lowest possible scheduling latency.
  The kernel can preempt almost any task, including most kernel-internal
  operations, ensuring interactive workloads (UI, input, audio) get CPU time
  within milliseconds.
- **HZ=1000** provides 1ms timer granularity, reducing scheduling jitter.
- The **BORE scheduler** (Burst-Oriented Response Enhancer) replaces the
  stock CFS/EEVDF latency handling with a burst-aware mechanism that
  preferentially schedules tasks emerging from voluntary sleeps (i.e.,
  interactive tasks waiting on user input or I/O).
- **EEVDF improvements** (`SCHED_EEVDF_FIND_BETTER_CORE`,
  `SCHED_EEVDF_LATENCY_WEIGHT`) ensure better task placement on hybrid
  architectures (P-cores vs E-cores, AMD CCPC).

### 2. Gaming

- **Futex2** support enables modern Proton, Wine, and native game sync
  primitives (fsync, futex2) for reduced overhead in synchronization-heavy
  game engines.
- **Full HID support** for gaming peripherals: Xbox, PlayStation, Nintendo,
  Steam Controller, Razer, Logitech, and custom input mappings.
- **PROTON_GE compatibility**: the futex2 patches, combined with fsync
  (`CONFIG_FUTEX_PI`) and eventfd/io_uring, provide the kernel interface
  Proton-GE needs for optimal performance.
- **BFQ + Kyber I/O schedulers** give flexibility for both HDD and NVMe
  gaming workloads. Kyber is the default for its low overhead on fast SSDs.

### 3. Graphics & Wayland

- **DRM core** with full **amdgpu** (SI/CIK+), **i915** (Gen4+), and
  **Nouveau** (open-source NVIDIA) support.
- DC (Display Core) for AMD with HDCP support.
- Virtual GPU support (virtio-gpu, VMware) for VMs and containerized
  graphics workloads.
- DP auxiliary char devices for firmware updates on DP-connected monitors.

### 4. Filesystems & Storage

- **BTRFS** is the primary filesystem, configured with:
  - zstd:3 default compression (good ratio, minimal CPU impact)
  - RAID56 support for multi-disk setups
  - Integrity checking (non-debug level)
  - Subvolume and quota support
- **F2FS** for flash storage devices
- **EXT4** and **XFS** for compatibility
- **ZRAM** as the default swap mechanism (zstd compressed, writing to
  backing device if configured)
- **Multi-queue I/O** with Kyber scheduler as default for NVMe/low-latency
  devices

### 5. Memory Management

- **Transparent HugePages** set to `always` for reduced TLB pressure.
- **Zswap** enabled with zsmalloc backend for memory-compressed caching.
- **Multi-Gen LRU** (via patch) for improved page reclaim decisions.
- **KSM** for memory de-duplication in virtualized environments.
- Full cgroup memory controller for container workload isolation.

### 6. Security

- **SELinux** is the primary LSM (set as default), with **AppArmor**
  also available as a boot-time alternative.
- **Lockdown LSM** in integrity mode (`lockdown=integrity`) prevents
  runtime insertion of unsigned code (kexec, hibernation, unsigned modules).
- **Kernel hardening** enabled:
  - `CONFIG_STACKPROTECTOR_STRONG` — stack canary on all functions with
    local arrays
  - `CONFIG_FORTIFY_SOURCE` — compile-time and runtime buffer overflow
    detection
  - `CONFIG_INIT_STACK_ALL_ZERO` — zero-initialize all stack variables
  - `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` / `CONFIG_INIT_ON_FREE_DEFAULT_ON` —
    zero memory on allocation and free
  - `CONFIG_SLAB_FREELIST_HARDENED` — mitigate heap spraying
  - `CONFIG_SLAB_FREELIST_RANDOM` — randomize freelist ordering
  - `CONFIG_RANDOMIZE_KSTACK_OFFSET` — randomize kernel stack offset
    on each syscall
  - `CONFIG_PAGE_TABLE_CHECK` / `CONFIG_PAGE_TABLE_CHECK_ENFORCED` —
    detect malicious page table manipulation
  - All known CPU mitigations enabled (Spectre, Meltdown, MDS, TAA,
    MMIO Stale Data, SRBDS, SRSO, RFDS, GDS)
- **IOMMU strict mode** default (no DMA bypass).
- **YAMA** for ptrace scope restriction.
- **Landlock** for unprivileged sandboxing.
- **SAFESETID** for setuid sandboxing.

### 7. Container & Virtualization

- Full **cgroup v2** support with all controllers enabled (cpu, memory,
  io, pids, rdma, misc, hugetlb, net).
- All **namespace types** (user, pid, net, uts, ipc, time, cgroup).
- **KVM** with Intel and AMD virtualization, AMD SEV.
- **VirtIO** with full device support.
- **VSOCK** for host-guest communication.

### 8. Microarchitecture Variants

Three build variants are provided:

| Variant | Flags | Target Hardware |
|---------|-------|-----------------|
| **generic** | `-march=x86_64` | Any x86_64 CPU (2010+) |
| **v3** | `-march=x86-64-v3` | Haswell+ (2013), Excavator+ (2015): AVX2, BMI1/BMI2, F16C, FMA, LZCNT, MOVBE, POPCNT |
| **v4** | `-march=x86-64-v4` | Zen4+ (2022), Sapphire Rapids+ (2023): AVX512, AVX512BW, AVX512CD, AVX512DQ, AVX512VL |

The v3 variant is recommended for most modern desktops (Intel 4th gen+,
AMD Ryzen 1st gen+). V4 is forward-looking for AM5/LGA1851 platforms.

## Key Configuration Decisions

### Why PREEMPT_FULL and not PREEMPT_VOLUNTARY?

PREEMPT_FULL provides measurably lower scheduling latency at negligible
throughput cost on modern hardware. On a typical desktop, the difference
in compile times or batch throughput is under 1%, while the difference in
perceived smoothness (video, scrolling, audio) is substantial.

### Why BORE over stock EEVDF?

EEVDF (Earliest Eligible Virtual Deadline First) is the upstream scheduler
in Linux 6.6+. It improves fairness and latency over CFS. BORE builds on
top of EEVDF by adding burst-detection logic: tasks that sleep briefly
and wake (interactive pattern) get a temporary priority boost beyond what
EEVDF's latency_nice provides. The result is a snappier feel under load.

### Why BTRFS with zstd:3?

BTRFS copy-on-write + zstd compression gives excellent space efficiency
and snapshot support with minimal CPU overhead. Level 3 provides roughly
2:1 compression on typical package installations while using <5% CPU on
a modern core for sequential writes. The `compress-force=zstd` mount option
is recommended.

### Why both SELinux and AppArmor?

SELinux provides mandatory access control (MAC) at the filesystem level,
required for strict sandboxing. AppArmor provides path-based profiles
that many distributions (Debian, Ubuntu, openSUSE) depend on. Having both
available lets users choose at boot via `security=selinux` or
`security=apparmor` without rebuilding the kernel.

### Why HZ=1000 with PREEMPT_FULL?

While HZ=1000 adds ~1% overhead compared to HZ=250, it provides 4x better
timer resolution. Combined with PREEMPT_FULL, this means interactive
wake-up latency is bounded by ~1ms instead of ~4ms — the difference
between a click feeling instantaneous vs slightly delayed.

## BORE Tuning Parameters

The BORE scheduler exposes several sysctl knobs:

```bash
# Lower = more aggressive boosting (default 0). Values 0-10000.
echo 0 > /proc/sys/kernel/sched_bore/processor_friendly

# Disable load weight reduction for boosted tasks (default 0).
echo 0 > /proc/sys/kernel/sched_bore/disable_load
```

For gaming, leaving both at 0 (default) gives the best interactivity.
For servers/batch systems, setting `processor_friendly=50` reduces
BORE's impact on throughput-bound workloads.

## Power Efficiency

Despite the performance focus, idle power draw is preserved through:

- Modern cpuidle governors (menu, teo)
- Intel P-State / AMD CPPC active with `schedutil` scaling governor
- PCIe ASPM enabled (default)
- Device-level runtime PM for USB, SATA, NVMe
- CONFIG_PM_AUTOSLEEP for system-wide suspend

The kernel idles to <5W on modern hardware when configured with the
`performance` governor; the `schedutil` or `powersave` governors reduce
this further.

## Files Not Covered

This configuration document covers the ~300 most important CONFIG_*
options that differentiate Synthex kernel from a generic distribution
kernel. Options not mentioned (driver-specific modules, hardware support,
filesystems) follow upstream defaults or are set to modular (m) for
loading on demand. The full `.config` contains ~7000+ options; the
`config-x86_64` file in this directory is the authoritative source.
