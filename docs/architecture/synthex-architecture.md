# Synthex System Architecture Guide

> **Audience:** System administrators, developers, and advanced users  
> **Last updated:** July 2026  
> **Synthex version:** 4.6 "Fortitude"

---

## Table of Contents

1. [Overall Architecture Layer Diagram](#1-overall-architecture-layer-diagram)
2. [Boot Sequence](#2-boot-sequence)
3. [Kernel/Userspace Boundary](#3-kerneluserspace-boundary)
4. [System Services Architecture](#4-system-services-architecture)
5. [D-Bus Topology](#5-d-bus-topology)
6. [Graphics Stack](#6-graphics-stack)
7. [Audio Stack](#7-audio-stack)
8. [Network Stack](#8-network-stack)
9. [Storage Stack](#9-storage-stack)
10. [Package Management Stack](#10-package-management-stack)
11. [Security Architecture Interconnects](#11-security-architecture-interconnects)
12. [Performance Optimization Flow](#12-performance-optimization-flow)
13. [Power Management Architecture](#13-power-management-architecture)

---

## 1. Overall Architecture Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER APPLICATIONS                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐   │
│  │  Plasma  │ │  Firefox │ │  Games   │ │  Flatpak / Container │   │
│  │  Desktop │ │  /Chrom  │ │ (Steam)  │ │  Apps (Podman/Docker)│   │
│  └────┬─────┘ └──────────┘ └──────────┘ └──────────────────────┘   │
├───────┴────────────────────────────────────────────────────────────┤
│                      GRAPHICS & AUDIO                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐    │
│  │ Wayland / X11    │  │   PipeWire       │  │  Vulkan / GL   │    │
│  │ Compositor(KWin) │  │   Audio Stack    │  │  Mesa Drivers  │    │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘    │
├───────────┴─────────────────────┴────────────────────┴────────────┤
│                     SYSTEM SERVICES (systemd)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │NetworkMgr│ │ firewalld│ │  D-Bus   │ │  udisks2 / upower  │    │
│  │          │ │          │ │  (IPC)   │ │  / colord / ...    │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘    │
├────────────────────────────────────────────────────────────────────┤
│                      PACKAGE MANAGEMENT                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │   DNF5   │ │ Flatpak  │ │rpm-ostree│ │   Synthex Software   │    │
│  │ (RPM)    │ │(Flathub) │ │(Atomic)  │ │   Center (GUI)     │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘    │
├────────────────────────────────────────────────────────────────────┤
│                         STORAGE LAYER                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐    │
│  │      BTRFS       │  │  LUKS2 (dm-crypt)│  │ systemd-gpt-   │    │
│  │  (subvolumes)    │  │  (full disk)     │  │ auto (mount)   │    │
│  └────────┬─────────┘  └────────┬─────────┘  └────────────────┘    │
├───────────┴─────────────────────┴─────────────────────────────────┤
│                      LINUX KERNEL                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐    │
│  │  DRM/KMS │ │  V4L2    │ │  ALSA    │ │  Namespaces /      │    │
│  │ (GPU)    │ │ (Video)  │ │ (Audio)  │ │  Cgroups (systemd) │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────────┘    │
├────────────────────────────────────────────────────────────────────┤
│                    BOOT FIRMWARE (UEFI)                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │
│  │  UEFI Firmware │  │  Shim (SB)     │  │  Secure Boot DB    │    │
│  │  (BIOS Setup)  │  │  / GRUB        │  │  (MOK)             │    │
│  └────────────────┘  └────────────────┘  └────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

| Layer | Components | Purpose |
|-------|-----------|---------|
| **Boot Firmware** | UEFI, Shim, GRUB/systemd-boot | Hardware init, bootloader, Secure Boot |
| **Linux Kernel** | DRM, ALSA, V4L2, cgroups | Hardware abstraction, resource management |
| **Storage** | BTRFS, LUKS2, systemd-gpt-auto | Filesystem, encryption, auto-mounting |
| **Package Mgmt** | DNF5, Flatpak, rpm-ostree | Software installation, updates, atomic ops |
| **System Services** | systemd, NetworkManager, D-Bus | Daemon management, IPC, networking |
| **Graphics/Audio** | Mesa, Wayland, PipeWire | Display, rendering, sound |
| **User Space** | KDE Plasma, apps, containers | User-facing environment |

---

## 2. Boot Sequence

Synthex uses a streamlined UEFI-first boot chain. Legacy BIOS boot is supported but not recommended for new installations.

### 2.1 Boot Flow Diagram

```
┌──────────────┐
│ Power On /   │
│ UEFI Firmware│
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────────────┐
│ UEFI POST    │────>│ Secure Boot          │
│ (self-test)  │     │ Verification         │
└──────┬───────┘     └──────────┬───────────┘
       │                        │
       ▼                        ▼
┌──────────────┐     ┌──────────────────────┐
│ Boot Manager │     │ Shim (signed by      │
│ selects      │     │ Microsoft) verifies  │
│ boot entry   │     │ GRUB signature       │
└──────┬───────┘     └──────────┬───────────┘
       │                        │
       ▼                        ▼
┌─────────────────────────────────────────────┐
│           GRUB 2 (or systemd-boot)          │
│  • Loads config from ESP (/boot)            │
│  • Presents menu (default: 5s timeout)      │
│  • Loads kernel + initramfs                 │
│  • Optionally verifies kernel signature     │
│  (MOK verification if Secure Boot active)   │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         Kernel Initialization               │
│  • Decompresses itself                      │
│  • Enumerates hardware (PCI, USB, ACPI)     │
│  • Mounts initramfs as rootfs               │
│  • Starts init process (/sbin/init →        │
│    systemd)                                 │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         initramfs (dracut-generated)        │
│  • Loads storage drivers (BTRFS, LUKS)      │
│  • Unlocks LUKS encrypted volumes           │
│    (password prompt or TPM unlock)          │
│  • Mounts real root filesystem              │
│  • Pivots to real root (switch_root)        │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│              systemd (PID 1)                │
│  • Reads /etc/systemd/system/default.target │
│  • Executes bootup targets sequentially:    │
│    - local-fs.target (mount all filesystems)│
│    - swap.target                            │
│    - sysinit.target (basic system init)     │
│    - basic.target (D-Bus, sockets)          │
│    - multi-user.target (all services)       │
│    - graphical.target (display manager)     │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         Display Manager (SDDM)              │
│  • Starts KDE Plasma session                │
│  • Wayland compositor (KWin) launches       │
│  • User login prompt displayed              │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         KDE Plasma Desktop                  │
│  • kwin_wayland (compositor)                │
│  • plasmashell (desktop shell)              │
│  • kded (KDE daemon)                        │
│  • User applications start                  │
│  • Welcome wizard on first boot             │
└─────────────────────────────────────────────┘
```

### 2.2 Detailed Boot Phase Explanation

| Phase | Duration (typical) | Description |
|-------|-------------------|-------------|
| UEFI POST | 1–5s | Hardware initialization, memory training |
| Boot Manager | 0.5–2s | Shim/GRUB selection, BootNext processing |
| GRUB | 1–3s | Config load, menu display, kernel+initramfs load |
| Kernel | 2–5s | Decompression, hardware probe, driver loading |
| initramfs | 3–10s | Storage setup, decryption (if LUKS), root mount |
| systemd | 5–15s | Service parallel startup, socket activation |
| SDDM+Plasma | 3–8s | Display manager, compositor, desktop shell |

**Total typical boot time:** 15–45s (SSD + modern hardware)

### 2.3 UEFI → Shim → GRUB

```bash
# EFI boot entry layout (on ESP - EFI System Partition)
/boot/efi/
├── EFI/
│   ├── BOOT/
│   │   └── BOOTX64.EFI           # Fallback bootloader
│   ├── synthex/
│   │   ├── shimx64.efi           # Shim (SB first-stage)
│   │   ├── grubx64.efi           # GRUB (signed)
│   │   ├── MokManager.efi        # MOK enrollment utility
│   │   └── grub.cfg              # GRUB configuration
│   └── vendor/                    # OEM entries
├── loader/
│   └── entries/
│       └── synthex.conf            # systemd-boot entry (if used)
└── kernels/                       # UKI kernels (if used)
```

**Secure Boot chain of trust:**
1. UEFI firmware validates Shim's signature (signed by Microsoft)
2. Shim validates GRUB via MOK (Machine Owner Key) or SBAT
3. GRUB validates kernel + initramfs via MOK
4. Kernel validates modules via kernel keyring

### 2.4 GRUB Configuration

GRUB config is stored at `/boot/grub2/grub.cfg` (auto-generated) with user overrides in `/etc/default/grub`:

```bash
# /etc/default/grub
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="Synthex"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash rd.luks.options=discard"
GRUB_CMDLINE_LINUX=""
GRUB_ENABLE_CRYPTODISK=y
GRUB_GFXMODE=1920x1080,auto
GRUB_SAVEDEFAULT=true
GRUB_DISABLE_RECOVERY=false
GRUB_THEME=/boot/grub2/themes/synthex/theme.txt
```

### 2.5 systemd-boot Alternative

```bash
# Install systemd-boot
sudo bootctl install

# Entry at /boot/efi/loader/entries/synthex.conf
title   SynthOS
linux   /vmlinuz-linux
initrd  /initramfs-linux.img
options root=UUID=... rw quiet splash
```

### 2.6 Initramfs (dracut)

Synthex uses **dracut** for initramfs generation:

```bash
# Regenerate initramfs
sudo dracut --force --hostonly

# Components loaded in initramfs:
# - btrfs (root filesystem)
# - dm_crypt (LUKS)
# - dm_mod, dm_integrity
# - kernel/drivers/usb/storage (keyfile unlock)
# - systemd (systemd in initramfs)
```

---

## 3. Kernel/Userspace Boundary

### 3.1 System Call Interface

```
┌─────────────────────────────────────┐
│         Userspace (Ring 3)           │
│  Applications, system libraries      │
│  glibc / musl / rust std             │
└──────────────┬──────────────────────┘
               │ syscall instruction
               │ (x86-64: `syscall`)
               ▼
┌─────────────────────────────────────┐
│       Linux Kernel (Ring 0)         │
│  VFS │ Scheduler │ MM │ Net │ FS    │
│  ~450 system calls on x86-64        │
└─────────────────────────────────────┘
```

### 3.2 Key Kernel Subsystems

| Subsystem | Role | Userspace Interface |
|-----------|------|-------------------|
| **VFS** | Virtual Filesystem | `open()`, `read()`, `write()`, `stat()` |
| **Process Scheduler** | CFS / EEVDF task scheduling | `sched_setattr()`, `nice()` |
| **Memory Manager** | MMU, page cache, swapping | `mmap()`, `brk()`, `madvise()` |
| **Network Stack** | TCP/IP, netfilter | `socket()`, `bind()`, `sendmsg()` |
| **DRM/KMS** | Display, GPU | `/dev/dri/card0`, `libdrm` |
| **ALSA** | Audio hardware | `/dev/snd/*`, `alsa-lib` |
| **V4L2** | Video capture | `/dev/video*` |
| **io_uring** | Async I/O | `io_uring_setup()`, `io_uring_enter()` |

### 3.3 Synthex Kernel Configuration

Synthex ships a custom kernel with specific tuning:

```bash
# Key kernel config differences from generic distro kernels
CONFIG_SCHED_EEVDF=y           # Modern scheduler
CONFIG_BTRFS_FS=y              # BTRFS built-in (not module)
CONFIG_DM_CRYPT=y              # LUKS built-in
CONFIG_IO_URING=y              # Async I/O
CONFIG_KSM=y                   # Kernel Same-page Merging
CONFIG_ZRAM=y                  # Compressed RAM swap
CONFIG_BPF_SYSCALL=y           # BPF/eBPF
CONFIG_SECCOMP_FILTER=y        # seccomp-bpf
CONFIG_LANDLOCK=y              # Landlock LSM
CONFIG_INTEL_TEE=y             # Intel SGX/TDX
CONFIG_AMD_TEE_AMDSP=y         # AMD SEV/PSP
CONFIG_NFTABLES=y              # nftables (firewall)
CONFIG_IP_SET=y                # IP set support
# Performance tuning
CONFIG_HZ_1000=y               # 1000Hz timer
CONFIG_PREEMPT_VOLUNTARY=y     # Voluntary preemption
CONFIG_CGROUP_BPF=y            # cgroup BPF
```

### 3.4 Special Filesystem Mounts

```
proc      /proc       proc   defaults                 0 0
sys       /sys        sysfs  defaults                 0 0
devtmpfs  /dev        devtmpfs mode=0755              0 0
devpts    /dev/pts    devpts  gid=5,mode=620           0 0
tmpfs     /run        tmpfs   mode=0755,nosuid,nodev   0 0
cgroup2   /sys/fs/cgroup cgroup2 defaults             0 0
efivarfs  /sys/firmware/efi/efivars efivarfs defaults 0 0
```

---

## 4. System Services Architecture

### 4.1 Services Overview

Synthex runs a curated set of systemd services optimized for desktop use:

```bash
# View all running services
systemctl list-units --type=service --state=running

# Output (typical Synthex 4.6 desktop):
#
# UNIT                     LOAD   ACTIVE SUB     DESCRIPTION
# accounts-daemon.service  loaded active running Accounts Service
# bluetooth.service        loaded active running Bluetooth service
# colord.service           loaded active running Manage color profiles
# cups.service             loaded active running CUPS Scheduler
# cronie.service           loaded active running Cronie NTP client
# dbus-broker.service      loaded active running D-Bus System Message Bus
# firewalld.service        loaded active running firewalld - firewall
# fstrim.service           loaded active running Trim filesystems (weekly)
# geoclue.service          loaded active running Location lookups
# NetworkManager.service   loaded active running Network Manager
# pipewire.service         loaded active running PipeWire (user)
# pipewire-pulse.service   loaded active running PipeWire PulseAudio compat
# polkit.service           loaded active running Authorization Manager
# rtkit-daemon.service     loaded active running RealtimeKit
# sddm.service             loaded active running Display Manager
# smb.service              loaded active running Samba
# sshd.service             loaded active running OpenSSH server
# systemd-journald.service loaded active running Journal Service
# systemd-logind.service   loaded active running Login Manager
# systemd-oomd.service     loaded active running Userspace OOM Killer
# systemd-resolved.service loaded active running Network Name Resolution
# systemd-timesyncd.service loaded active running NTP client
# thermald.service         loaded active running Thermal Monitoring
# tuned.service            loaded active running Tuning daemon
# udisks2.service          loaded active running Disk Manager
# ufw.service              loaded active running Uncomplicated Firewall
# upower.service           loaded active running Power Manager
# user@1000.service        loaded active running User Manager for UID 1000
```

### 4.2 Service Rationale

| Service | Why included | Can disable? | Impact of disabling |
|---------|-------------|-------------|-------------------|
| `systemd-oomd` | Prevents OOM hangs | Yes | System may freeze under memory pressure |
| `systemd-resolved` | Modern DNS with DNSSEC | Yes | Falls back to `/etc/resolv.conf` |
| `firewalld` | Dynamic firewall | Consider `ufw` instead | No firewall warnings |
| `tuned` | Auto-tuning for workloads | Yes | Default kernel params only |
| `thermald` | Thermal throttling protection | Yes | No active thermal management |
| `rtkit-daemon` | Real-time priorities for audio | Yes | Audio may glitch under load |
| `colord` | Color management for displays | Yes | No ICC profile management |
| `geoclue` | Location services for apps | Yes | No location-aware features |
| `cups` | Printer support | Yes | No printing |
| `bluetooth` | Bluetooth devices | Yes | No Bluetooth |

### 4.3 Systemd Boot Analysis

```bash
# Analyze boot performance
systemd-analyze
# Startup finished in 2.847s (kernel) + 4.123s (initrd) + 8.456s (userspace) = 15.426s

# Service-level breakdown
systemd-analyze blame
# 3.201s NetworkManager-wait-online.service
# 2.847s dev-sda2.device
# 1.234s systemd-udev-settle.service
# 0.987s firewalld.service
# ...

# Critical chain
systemd-analyze critical-chain
# graphical.target @8.456s
# └─multi-user.target @8.456s
#   └─sddm.service @8.321s
#     └─ ... 
```

### 4.4 User Services

Synthex uses `systemd --user` for per-user service management:

```bash
# User services (run as user)
systemctl --user list-units

# Key user services:
# - pipewire.service           (audio server)
# - pipewire-pulse.service     (PulseAudio compat)
# - wireplumber.service        (session/policy manager)
# - xdg-desktop-portal.service (portal interface)
# - kdeconnect.service         (phone integration)
```

---

## 5. D-Bus Topology

### 5.1 Bus Architecture

Synthex uses **dbus-broker** (not the reference dbus-daemon):

```
┌────────────────────────────────────────────────────────────┐
│                    D-Bus Architecture                       │
│                                                            │
│  ┌─────────────────────────┐  ┌─────────────────────────┐ │
│  │    System Bus           │  │  Session Bus (per-user)  │ │
│  │    (dbus-broker)        │  │  (dbus-broker)           │ │
│  │    privileged services  │  │  desktop services        │ │
│  │                         │  │                          │ │
│  │  • NetworkManager       │  │  • KDE Plasma            │ │
│  │  • firewalld            │  │  • KWin                  │ │
│  │  • udisks2              │  │  • kded                 │ │
│  │  • upower               │  │  • pipewire              │ │
│  │  • polkit               │  │  • wireplumber           │ │
│  │  • systemd-logind       │  │  • xdg-desktop-portal    │ │
│  └─────────────────────────┘  └─────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 5.2 D-Bus Monitoring

```bash
# Monitor system bus
dbus-monitor --system

# Monitor session bus
dbus-monitor --session

# List all system bus services
busctl list

# Introspect a service
busctl introspect org.freedesktop.NetworkManager /org/freedesktop/NetworkManager
```

### 5.3 Polkit Authorization

```bash
# Polkit rules stored at:
# /usr/share/polkit-1/rules.d/    (distribution defaults)
# /etc/polkit-1/rules.d/          (system admin overrides)

# Example: Allow passwordless suspend
cat /etc/polkit-1/rules.d/10-suspend.rules
polkit.addRule(function(action, subject) {
    if (action.id == "org.freedesktop.login1.suspend" &&
        subject.isInGroup("wheel")) {
        return polkit.Result.YES;
    }
});
```

---

## 6. Graphics Stack

### 6.1 Stack Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ KDE Apps │ │ Firefox  │ │  Games   │ │ Flatpak Apps     │  │
│  │ (Qt6)    │ │ (Web)    │ │ (Steam)  │ │ (sandboxed)      │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│       │            │            │                 │            │
│       ▼            ▼            ▼                 ▼            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   KWin Compositor                        │  │
│  │  • Wayland (default) / X11 (fallback)                   │  │
│  │  • Scene graph (OpenGL/Vulkan renderer)                 │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Mesa 3D Graphics Library                    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────────────┐ │  │
│  │  │ Vulkan   │ │ OpenGL   │ │  VA-API / VDPAU          │ │  │
│  │  │ (radv/   │ │ (iris/   │ │  (video encode/decode)   │ │  │
│  │  │  amdvlk) │ │  zink/)  │ │                          │ │  │
│  │  └──────────┘ └──────────┘ └──────────────────────────┘ │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Kernel DRM/KMS                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │ amdgpu   │ │ i915     │ │ nvidia   │ │ simpledrm  │  │  │
│  │  │ (AMD)    │ │(Intel)   │ │(propri.) │ │(fallback)  │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│                      HARDWARE (GPU)                            │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Display Server: Wayland (Default)

```bash
# Current display server
echo $XDG_SESSION_TYPE
# → wayland (or x11 if fallback)

# Wayland info
wayland-info
```

**Wayland protocol extensions supported:**
- `wl_compositor` — Base compositor
- `xdg_shell` — Desktop window management
- `zwlr_layer_shell_v1` — Panel/notification surfaces
- `zwp_relative_pointer_v1` — Relative pointer (games)
- `zwp_pointer_constraints_v1` — Pointer lock (games)
- `wp_fractional_scale_v1` — Per-output fractional scaling
- `ext_image_copy_capture_v1` — Efficient screen capture

### 6.3 Graphics Drivers

#### AMD (Recommended)
```bash
lsmod | grep amdgpu
# Vulkan driver: radv (open-source) or amdvlk (AMD official)
```

#### Intel
```bash
lsmod | grep i915
# Drivers: iris (OpenGL Gen8+), ANV (Vulkan)
```

#### NVIDIA
```bash
# Synthex supports NVIDIA proprietary driver
sudo dnf5 install nvidia-driver nvidia-driver-cuda
```

### 6.4 Display Configuration

```bash
# Using kscreen (KDE)
kscreen-doctor

# Using wlr-randr (Wayland)
wlr-randr
```

---

## 7. Audio Stack

### 7.1 PipeWire Architecture

Synthex uses **PipeWire** as the primary audio server:

```
┌────────────────────────────────────────────────────────────────┐
│                      APPLICATIONS                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Media    │ │ Browser  │ │ DAW/     │ │ Games            │  │
│  │ Player   │ │ (WebRTC) │ │ JACK app │ │ (Steam Proton)   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│       │            │            │                 │            │
│       ▼            ▼            ▼                 ▼            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Client Libraries                               │  │
│  │  libpipewire (native) │ libpulse (pw-pulse compat)       │  │
│  │  libjack (pw-jack compat) │ ALSA via libasound           │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PipeWire Core + Graph                       │  │
│  │  • Real-time audio processing (RTKit)                    │  │
│  │  • Node graph routing                                    │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              WirePlumber (Session Manager)                │  │
│  │  • Device discovery, policy, Bluetooth management        │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  ALSA (Kernel)                            │  │
│  │  • Hardware drivers (HDA, USB, ASoC)                     │  │
│  │  • /dev/snd/* (device nodes)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│                      HARDWARE (Sound Card)                     │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 PipeWire Components

| Component | Role | Configuration |
|-----------|------|---------------|
| `pipewire.service` | Main daemon (user) | `~/.config/pipewire/pipewire.conf` |
| `pipewire-pulse.service` | PulseAudio compat | `~/.config/pipewire/pipewire-pulse.conf` |
| `wireplumber.service` | Session manager | `/etc/wireplumber/` |

### 7.3 Audio Configuration

```bash
# Check audio devices
pw-cli list-objects | grep -A5 "node.*output"
pactl info

# Volume control
pactl set-sink-volume @DEFAULT_SINK@ 50%

# PipeWire graph
pw-top         # Real-time audio monitoring
pw-dump        # Full graph dump (JSON)
```

### 7.4 Bluetooth Audio

```bash
# Install codec support
sudo dnf5 install pipewire-codec-aptx pipewire-codec-ldac

# Supported codecs: SBC, AAC, aptX, LDAC, LC3
```

---

## 8. Network Stack

### 8.1 Overall Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      APPLICATIONS                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ Browser  │ │ SSH      │ │ Git      │ │ Flatpak Apps     │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘  │
│       │            │            │                 │            │
│       ▼            ▼            ▼                 ▼            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Application Firewall (firewalld)               │  │
│  │  • nftables backend, zones (public, home, work, trusted) │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            NetworkManager (Connection Mgmt)               │  │
│  │  • Wired / Wi-Fi / Mobile broadband / VPN / Bonding      │  │
│  │  • nmcli/nmtui/plasma-nm (frontends)                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      systemd-resolved (DNS Resolution)                    │  │
│  │  • DNSSEC, mDNS, LLMNR, DNS over TLS                     │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                    │
│                           ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Kernel Network Stack                         │  │
│  │  • TCP/IP (IPv4/IPv6), netfilter, wireless drivers       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 8.2 NetworkManager

```bash
# Status
nmcli general status
nmcli device status

# Manage connections
nmcli connection show
nmcli connection add type ethernet con-name "Home" ifname eth0

# Wi-Fi
nmcli device wifi list
nmcli device wifi connect "SSID" password "password"
```

### 8.3 firewalld

```bash
# Status
sudo firewall-cmd --state
sudo firewall-cmd --get-default-zone
sudo firewall-cmd --list-all

# Zones: block, dmz, drop, external, home, internal, public, trusted, work
sudo firewall-cmd --set-default-zone=home

# Allow service
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 8.4 systemd-resolved

```bash
# Status
resolvectl status

# DNS-over-TLS configuration
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1
DNSOverTLS=yes
DNSSEC=allow-downgrade
```

---

## 9. Storage Stack

### 9.1 Default Layout

Synthex defaults to **BTRFS on LUKS2** with automatic subvolume layout:

```
┌──────────────────────────────────────────────────────────────┐
│                    Physical Disk Layout                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │           /dev/sda (NVMe/SSD/HDD)                      │  │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────────┐  │  │
│  │  │ /dev/sda1│ │ /dev/sda2│ │ /dev/sda3              │  │  │
│  │  │ ESP      │ │ /boot    │ │ LUKS2 Encrypted        │  │  │
│  │  │ FAT32    │ │ ext4     │ │ (or no encryption)      │  │  │
│  │  │ 512 MiB  │ │ 1 GiB    │ │ ──────────────────     │  │  │
│  │  │          │ │          │ │ │ BTRFS (pool)  │       │  │  │
│  │  │          │ │          │ │ ├───────────────┤       │  │  │
│  │  │          │ │          │ │ │ @ (root)       │       │  │  │
│  │  │          │ │          │ │ │ @home          │       │  │  │
│  │  │          │ │          │ │ │ @snapshots     │       │  │  │
│  │  └──────────┘ └──────────┘ │ └────────────────┘       │  │  │
│  │                             └─────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │  │
└──────────────────────────────────────────────────────────────┘
```

### 9.2 Partition Layout

| Partition | Size | Type | Filesystem | Mount | Purpose |
|-----------|------|------|-----------|-------|---------|
| `/dev/sda1` | 512 MiB | EFI System | FAT32 | `/boot/efi` | Boot loader, kernels |
| `/dev/sda2` | 1 GiB | Linux boot | ext4 | `/boot` | GRUB stage 2 |
| `/dev/sda3` | Rest | Linux LUKS | BTRFS (inside LUKS) | `/` | Root with subvolumes |

### 9.3 BTRFS Features

```bash
# Mount options (from /etc/fstab)
UUID=... / btrfs rw,relatime,compress=zstd:3,
  ssd,discard=async,space_cache=v2,
  subvol=@ 0 0

# compress=zstd:3  — Transparent compression
# ssd              — SSD optimization
# discard=async    — Queued TRIM
# space_cache=v2   — Block group cache

# Snapshot with snapper
sudo snapper -c root create -d "pre-update"
sudo dnf5 update
sudo snapper -c root create -d "post-update"
```

### 9.4 Encryption (LUKS2)

```bash
# LUKS2 configuration
sudo cryptsetup luksDump /dev/sda3

# Key features:
# - LUKS2 header (Argon2 PBKDF)
# - aes-xts-plain64 cipher
# - 512-bit key (XTS halves to 256-bit AES)

# TPM2 auto-unlock
sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=0+7 /dev/sda3
```

### 9.5 Swap Strategy

```bash
# ZRAM (default) - compressed RAM swap
# /etc/systemd/zram-generator.conf
[zram0]
zram-size = ram / 2
compression-algorithm = zstd
```

---

## 10. Package Management Stack

### 10.1 Stack Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    PACKAGE MANAGEMENT                           │
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐   │
│  │   DNF5 (Primary PM)   │  │     Flatpak (Sandboxed Apps)│   │
│  │   RPM Package Manager │  │     Flathub                 │   │
│  │                       │  │                              │   │
│  │  • System packages    │  │  • GUI apps (sandboxed)     │   │
│  │  • Libraries          │  │  • Runtimes (KDE, GNOME,   │   │
│  │  • Drivers/kernel     │  │    Freedesktop, Steam)      │   │
│  └───────────────────────┘  └─────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │     rpm-ostree (Atomic, optional)                      │   │
│  │  • Image-based updates (immutable root)                │   │
│  │  • A/B updates (boot into previous deployment)         │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │     Synthex Software Center (GUI)                        │   │
│  │  • Unifies DNF5 + Flatpak + rpm-ostree                 │   │
│  └────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 10.2 DNF5

```bash
# Basic usage
sudo dnf5 install <package>
sudo dnf5 remove <package>
sudo dnf5 update
sudo dnf5 search <query>
sudo dnf5 info <package>
sudo dnf5 list installed
sudo dnf5 provides </path/to/file>

# Repository management
sudo dnf5 repolist
sudo dnf5 config-manager --add-repo <url>

# History and rollback
sudo dnf5 history
sudo dnf5 history undo <transaction-id>
```

### 10.3 Flatpak

```bash
flatpak install flathub org.mozilla.firefox
flatpak run org.mozilla.firefox
flatpak update
flatpak list
```

### 10.4 rpm-ostree (Atomic Mode)

```bash
rpm-ostree status
rpm-ostree upgrade
rpm-ostree rollback
rpm-ostree install <package>
```

---

## 11. Security Architecture Interconnects

### 11.1 Security Stack Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              USERSPACE SECURITY                          │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Polkit   │ │ Accounts │ │ firewalld│ │ SELinux  │   │   │
│  │  │ (authz)  │ │ (auth)   │ │ (net)    │ │ (MAC)    │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              KERNEL SECURITY                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │ Seccomp  │ │ Landlock │ │ Namespace│ │ LSM      │   │   │
│  │  │ (syscall)│ │ (filesys)│ │ (contain)│ │ (SELinux)│   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                  │
│                             ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              FIRMWARE / HARDWARE SECURITY                 │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │   │
│  │  │Secure Boot│ │ TPM 2.0  │ │ ME/PSP   │                 │   │
│  │  │(UEFI)     │ │(measured)│ │(firmware)│                 │   │
│  │  └──────────┘ └──────────┘ └──────────┘                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 11.2 LSM (Linux Security Module) Configuration

```bash
# SELinux status
getenforce
# → Enforcing

# SELinux policy type
sestatus
# → Loaded policy name: targeted
```

### 11.3 Security Components Interaction

| Scenario | Components Involved |
|----------|-------------------|
| **User login** | accounts-daemon → PAM → systemd-logind → SELinux |
| **Package install** | DNF → RPM → SELinux (transition) → file contexts |
| **Network access** | firewalld → nftables → SELinux net_context |
| **App sandboxing** | Flatpak → bubblewrap → namespaces → seccomp → Landlock |
| **Privilege escalation** | polkit → D-Bus → authorization check → pkexec |
| **Disk encryption** | systemd-cryptsetup → LUKS2 → TPM2 → dm-crypt |

---

## 12. Performance Optimization Flow

### 12.1 Performance Stack

```
┌────────────────────────────────────────────────────────────────┐
│                   PERFORMANCE OPTIMIZATION                      │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Auto-tuning (systemd/tuned)                 │   │
│  │  • tuned-adm profile selection                          │   │
│  │  • systemd-oomd (memory pressure)                       │   │
│  │  • sysctl.d / sysfs.d settings                          │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CPU Optimization                            │   │
│  │  • CPU governor: schedutil / performance                │   │
│  │  • P-state management (intel_pstate / amd_pstate)       │   │
│  │  • IRQ balancing (irqbalance)                           │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Memory Optimization                         │   │
│  │  • ZRAM (compressed swap)                               │   │
│  │  • vm.swappiness=10                                     │   │
│  │  • THP (madvise)                                        │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Storage Optimization                        │   │
│  │  • BTRFS: compress=zstd:3, ssd, discard=async           │   │
│  │  • I/O scheduler: none (NVMe) / mq-deadline (SSD)      │   │
│  │  • noatime mount option, fstrim.timer                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 12.2 tuned Profiles

```bash
# Available profiles
tuned-adm list

# Set profile for gaming
sudo tuned-adm profile latency-performance
```

### 12.3 Memory Tuning

```bash
# Current ZRAM configuration
zramctl

# Tuning for desktop responsiveness
sudo tee /etc/sysctl.d/99-desktop-tuning.conf <<EOF
vm.swappiness=10
vm.vfs_cache_pressure=50
vm.watermark_boost_factor=15000
vm.watermark_scale_factor=200
vm.dirty_background_ratio=5
vm.dirty_ratio=10
EOF
```

### 12.4 GPU Performance

```bash
# Mesa shader cache (default: ~1GB limit)
# ~/.cache/mesa_shader_cache/
```

---

## 13. Power Management Architecture

### 13.1 Power Management Stack

```
┌────────────────────────────────────────────────────────────────┐
│                   POWER MANAGEMENT                              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Desktop Environment (KDE Plasma)            │   │
│  │  • Power Management settings in System Settings          │   │
│  │  • Screen blanking, sleep/hibernate                      │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              upower (Device power abstraction)            │   │
│  │  • Battery monitoring, power source detection            │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              systemd-logind (Session management)          │   │
│  │  • HandleLidSwitch, IdleAction, Inhibit locks            │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                      │
│                         ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Kernel PM subsystems                        │   │
│  │  • ACPI, CPU idle (cpuidle), CPU freq (cpufreq)         │   │
│  │  • PCIe ASPM, Runtime PM, S2idle / S3 deep sleep        │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 13.2 Sleep States

| State | ACPI | Description | Resume time |
|-------|------|-------------|-------------|
| S0 | Working | System fully on | N/A |
| S0ix | Modern standby | Intel Low Power Idle | <1s |
| S3 | Suspend-to-RAM (deep) | RAM self-refresh | 3-10s |
| S4 | Hibernate | State saved to disk | 10-30s |
| S5 | Soft-off | System powered off | Boot time |

```bash
# Check available sleep states
cat /sys/power/state
# → freeze mem disk

# Preferred sleep mode
sudo tee /etc/systemd/sleep.conf <<EOF
[Sleep]
SuspendState=mem
HibernateState=disk
EOF
```

### 13.3 CPU Power Management

```bash
# CPU frequency governors
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
# → powersave (on battery) / schedutil (on AC)
```

### 13.4 Laptop-Specific (TLP)

```bash
sudo dnf5 install tlp tlp-rdw
sudo systemctl enable --now tlp

# /etc/tlp.conf
CPU_SCALING_GOVERNOR_ON_AC=performance
CPU_SCALING_GOVERNOR_ON_BAT=powersave
USB_AUTOSUSPEND=1
WIFI_PWR_SAVE_ON_BAT=on
```

---

## Appendix A: Architecture Decision Records

### ADR-001: DNF5 over apt/zypper/pacman
- **Status:** Adopted
- **Context:** Needed a modern RPM package manager with C API
- **Decision:** DNF5 (successor to DNF) for performance and SAT solver

### ADR-002: PipeWire over PulseAudio
- **Status:** Adopted
- **Context:** Desktop audio + professional audio + video routing
- **Decision:** PipeWire with WirePlumber session manager

### ADR-003: BTRFS as default filesystem
- **Status:** Adopted
- **Context:** Needed snapshots, compression, checksums
- **Decision:** BTRFS with zstd compression and snapper

### ADR-004: Wayland as primary display server
- **Status:** Adopted
- **Context:** X11 legacy issues, security, multi-monitor
- **Decision:** Wayland with KWin compositor, X11 fallback

## Appendix B: System Information Commands

```bash
# Architecture summary
uname -a                           # Kernel version + architecture
lscpu                              # CPU details
lspci -k                           # PCI devices with drivers
lsusb                              # USB devices
lsmod                              # Loaded kernel modules

# System health
uptime                             # System uptime + load
free -h                            # Memory usage
df -hT                             # Disk usage with filesystem type
journalctl -p 3 -xb                # Errors in current boot
```
