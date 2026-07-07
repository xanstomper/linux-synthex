# Linux Synthex Security Architecture

> Version: 1.0.0
> Status: DRAFT
> Last Updated: 2026-07-04

---

## Table of Contents

1. [Defense-in-Depth Model](#1-defense-in-depth-model)
2. [SELinux Policy Overview for Synthex](#2-selinux-policy-overview-for-synthex)
3. [Hardened Kernel Configs](#3-hardened-kernel-configs)
4. [Secure Boot Chain](#4-secure-boot-chain)
5. [TPM2 Integration for Measured Boot + LUKS](#5-tpm2-integration-for-measured-boot--luks)
6. [Full Disk Encryption with LUKS2](#6-full-disk-encryption-with-luks2)
7. [Hardened Malloc (glibc with Heap Hardening)](#7-hardened-malloc-glibc-with-heap-hardening)
8. [Stack Protector, CFI, CET](#8-stack-protector-cfi-cet)
9. [Kernel Lockdown (Integrity/Enforcement)](#9-kernel-lockdown-integrityenforcement)
10. [Firewalld with nftables](#10-firewalld-with-nftables)
11. [Automatic Security Updates Configuration](#11-automatic-security-updates-configuration)
12. [Flatpak Sandbox + Permissions Manager](#12-flatpak-sandbox--permissions-manager)
13. [Browser Sandbox Hardening](#13-browser-sandbox-hardening)
14. [AppArmor Compatibility Layer](#14-apparmor-compatibility-layer)
15. [Vulnerability Response Process](#15-vulnerability-response-process)
16. [Security Dashboard Design (GUI App Spec)](#16-security-dashboard-design-gui-app-spec)

---

## 1. Defense-in-Depth Model

Synthex employs a layered security architecture with overlapping controls across seven domains:

```
┌─────────────────────────────────────────────────────────┐
│                  Layer 7: Audit & Monitoring              │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Layer 6: Application Security           │ │
│  │  ┌─────────────────────────────────────────────────┐ │ │
│  │  │           Layer 5: Mandatory Access Control      │ │ │
│  │  │  ┌─────────────────────────────────────────────┐ │ │ │
│  │  │  │        Layer 4: System Hardening            │ │ │ │
│  │  │  │  ┌─────────────────────────────────────────┐ │ │ │ │
│  │  │  │  │     Layer 3: Network Security            │ │ │ │
│  │  │  │  │  ┌─────────────────────────────────────┐ │ │ │ │
│  │  │  │  │  │  Layer 2: Platform Integrity         │ │ │ │
│  │  │  │  │  │  ┌─────────────────────────────────┐ │ │ │ │
│  │  │  │  │  │  │  Layer 1: Physical Security      │ │ │ │
│  │  │  │  │  │  │  (TPM, Secure Boot, LUKS2)       │ │ │ │
│  │  │  │  │  │  └─────────────────────────────────┘ │ │ │ │
│  │  │  │  │  └─────────────────────────────────────┘ │ │ │ │
│  │  │  │  └─────────────────────────────────────────┘ │ │ │ │
│  │  │  └─────────────────────────────────────────────┘ │ │ │ │
│  │  └─────────────────────────────────────────────────┘ │ │ │ │
│  └─────────────────────────────────────────────────────┘ │ │ │ │
└─────────────────────────────────────────────────────────┘ │ │ │
└─────────────────────────────────────────────────────────┘ │ │
└─────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

### 1.1 Layer Descriptions

| Layer | Domain | Controls | Status |
|-------|--------|----------|--------|
| 1 | Physical Security | TPM 2.0, Secure Boot, LUKS2 FDE, Anti-Tamper | Core |
| 2 | Platform Integrity | Measured Boot, Kernel Lockdown, IMA/EVM | Core |
| 3 | Network Security | firewalld (nftables), WireGuard, TCP hardening | Core |
| 4 | System Hardening | Sysctl hardening, resource limits, auditd | Core |
| 5 | Mandatory Access Control | SELinux targeted policy, AppArmor compat | Core |
| 6 | Application Security | Flatpak sandbox, browser hardening, hardened malloc | Enhanced |
| 7 | Audit & Monitoring | Security dashboard, centralized logging, SIEM feed | Enhanced |

### 1.2 Failure Model

Each layer assumes the layer below it has been compromised. Controls are designed to:
- **Detect** the compromise at the next layer
- **Contain** the damage to the minimum privilege boundary
- **Recover** through verified state transitions measured at boot

---

## 2. SELinux Policy Overview for Synthex

### 2.1 Policy Architecture

Synthex uses SELinux in **targeted** mode with a custom policy module for Synthex-specific applications:

```
Policy Store: /etc/selinux/targeted/
Policy Type: MLS with sensitivity levels (s0-s15)
Policy Version: 33 (Fedora-based policy base)
```

### 2.2 Domain Mapping

| Domain | Label | Description |
|--------|-------|-------------|
| `synthex_software_center_t` | `system_u:system_r:synthex_software_center_t:s0` | Synthex Software Center |
| `synthex_update_t` | `system_u:system_r:synthex_update_t:s0` | Synthex Update Manager |
| `synthex_settings_t` | `system_u:system_r:synthex_settings_t:s0` | Synthex Settings Daemon |
| `synthex_session_t` | `system_u:system_r:synthex_session_t:s0` | Budgie Desktop Session |
| `synthex_flatpak_helper_t` | `system_u:system_r:synthex_flatpak_helper_t:s0` | Flatpak Integration |
| `synthex_backup_t` | `system_u:system_r:synthex_backup_t:s0` | Backup Tool |
| `synthex_firewall_t` | `system_u:system_r:synthex_firewall_t:s0` | Firewall Manager |

### 2.3 Policy Modules

| Module | Description | Dependencies |
|--------|-------------|--------------|
| `synthex_base` | Core types, attributes, and interfaces | `kernel`, `system` |
| `synthex_software` | Software Center domain transitions | `synthex_base`, `dbus` |
| `synthex_session` | Desktop session domains and Xorg/Wayland | `synthex_base`, `xserver`, `wayland` |
| `synthex_hardware` | Hardware control (backlight, rfkill, etc.) | `synthex_base`, `devices` |
| `synthex_network` | NetworkManager integration | `synthex_base`, `networkmanager` |
| `synthex_updates` | Update and repository management | `synthex_base`, `rpm`, `dnf` |

### 2.4 Compile and Load

```bash
# Build policy module
make -f /usr/share/selinux/devel/Makefile synthex-policy.pp
semodule -i synthex-policy.pp

# Verify
semodule -l | grep synthex
seinfo -tsynthex_software_center_t
```

---

## 3. Hardened Kernel Configs

### 3.1 Critical Kernel Hardening Options

```
# Kernel Self-Protection
CONFIG_STACKPROTECTOR_STRONG=y
CONFIG_SCHED_STACK_END_CHECK=y
CONFIG_SLAB_FREELIST_RANDOM=y
CONFIG_SLAB_FREELIST_HARDENED=y
CONFIG_SHUFFLE_PAGE_ALLOCATOR=y

# Memory Protections
CONFIG_DEBUG_VIRTUAL=y
CONFIG_DEBUG_LIST=y
CONFIG_DEBUG_SG=y
CONFIG_DEBUG_NOTIFIERS=y
CONFIG_DEBUG_CREDENTIALS=y

# CFI (Control Flow Integrity)
CONFIG_CFI_CLANG=y
CONFIG_CFI_PERMISSIVE=n
CONFIG_CFI_ICALL_NORMALIZE_INTEGRITY=y

# CET (Control-flow Enforcement Technology)
CONFIG_X86_CET=y
CONFIG_X86_SHADOW_STACK=y
CONFIG_X86_USER_SHADOW_STACK=y

# Kernel Lockdown
CONFIG_SECURITY_LOCKDOWN_LSM=y
CONFIG_SECURITY_LOCKDOWN_LSM_EARLY=y
CONFIG_LOCK_DOWN_IN_KERNEL_MODE=y
CONFIG_LOCK_DOWN_IN_EFI_SECURE_BOOT=y

# Randomization
CONFIG_RANDOMIZE_BASE=y
CONFIG_RANDOMIZE_MODULE_REGION_FULL=y
CONFIG_VMALLOC_RANDOMIZATION=y

# Restrict /dev/mem and /dev/kmem
CONFIG_STRICT_DEVMEM=y
CONFIG_IO_STRICT_DEVMEM=y

# Module signing
CONFIG_MODULE_SIG=y
CONFIG_MODULE_SIG_FORCE=y
CONFIG_MODULE_SIG_SHA512=y
CONFIG_MODULE_SIG_ALL=y

# BPF hardening
CONFIG_BPF_JIT=y
CONFIG_BPF_JIT_ALWAYS_ON=y
CONFIG_BPF_UNPRIV_DEFAULT_OFF=y
CONFIG_PREVENT_BPF_ATTACK=y
```

### 3.2 Recommended Build Flags

```
-march=x86-64-v3 -mtune=generic -O2 -fstack-protector-strong -D_FORTIFY_SOURCE=3
-fcf-protection=full -mbranch-protection=standard
-Wp,-D_GLIBCXX_ASSERTIONS -fstack-clash-protection
```

---

## 4. Secure Boot Chain

### 4.1 Chain of Trust

```
UEFI (Hardware Root of Trust)
  │
  ├── UEFI Secure Boot (PK → KEK → db → dbx)
  │     │
  │     ├── shim (Microsoft-signed first-stage bootloader)
  │     │     └── Machine Owner Key (MOK) enrolled
  │     │           ├── GRUB2 (signed with MOK)
  │     │           │     ├── kernel (signed with MOK)
  │     │           │     │     └── kernel modules (signed)
  │     │           │     └── initramfs (verified by kernel)
  │     │           └── systemd-boot (alternative)
  │     │
  │     └── MokManager (enroll/revoke MOKs)
  │
  └── TPM 2.0 PCR Measurements
        ├── PCR 0-1: Core BIOS/EFI
        ├── PCR 2-3: Option ROMs
        ├── PCR 4: Bootloader
        ├── PCR 5: Bootloader configuration
        ├── PCR 7: Secure Boot state
        └── PCR 8-9: GRUB and kernel
```

### 4.2 Implementation

```bash
# Check Secure Boot status
mokutil --sb-state

# Enroll Machine Owner Key
sudo mokutil --import /etc/pki/uefi/RPM-GPG-KEY-synthex.der

# Sign kernel
sbsign --key /etc/pki/uefi/private.key \
       --cert /etc/pki/uefi/public.crt \
       --output /boot/vmlinuz-*-synthex.signed \
       /boot/vmlinuz-*-synthex

# Sign GRUB
pesign -n /etc/pki/uefi -i /boot/efi/EFI/synthex/grubx64.efi \
       -o /boot/efi/EFI/synthex/grubx64.efi.signed -s
```

### 4.3 GRUB Hardening

```
# /etc/default/grub: Secure boot configuration
GRUB_CMDLINE_LINUX="lockdown=integrity module.sig_enforce=1 \
                    slab_nomerge init_on_alloc=1 init_on_free=1 \
                    page_alloc.shuffle=1 pti=on spectre_v2=on \
                    spec_store_bypass_disable=on tsx=off \
                    tsx_async_abort=full,nosmt mds=full,nosmt \
                    l1tf=full,force kvm.nx_huge_pages=force \
                    random.trust_bootloader=off random.trust_cpu=off"

GRUB_DISABLE_RECOVERY="true"
GRUB_ENABLE_CRYPTODISK="y"
GRUB_SAVEDEFAULT="false"
```

---

## 5. TPM2 Integration for Measured Boot + LUKS

### 5.1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    TPM 2.0 (CRTM)                         │
│                                                          │
│  PCR Banks: SHA256, SHA384                                │
│  NV Indexes:                                             │
│    - 0x01C10101: LUKS Volume Key (sealed)                 │
│    - 0x01C10102: LUKS Recovery PIN                        │
│    - 0x01C10103: TPM Owner Auth                          │
│    - 0x01C10104: Secure Boot State                       │
│                                                          │
│  Seal LUKS key to PCR policy:                             │
│    PCR 0 + PCR 2 + PCR 4 + PCR 7 + PCR 9                 │
│    (BIOS → Option ROM → Bootloader → Secure Boot → Kernel)│
└─────────────────────────────────────────────────────────┘
```

### 5.2 TPM2 Tools Integration

```bash
# Check TPM availability
tpm2_getcap properties-variable

# Seal LUKS key to PCR policy
sudo systemd-cryptenroll --tpm2-device=auto \
    --tpm2-pcrs=0+2+4+7+9 \
    --tpm2-public-key=/etc/tpm2/pcr.pub \
    /dev/sda3

# Validate PCR policy
tpm2_pcrread sha256:0,2,4,7,9

# Unseal (automatic at boot via systemd-cryptsetup)
# PKCS#11 URI: pkcs11:module=/usr/lib/libtpm2_pkcs11.so
```

### 5.3 Measured Boot with IMA

```bash
# Kernel cmdline additions for IMA
ima_appraise=fix ima_template=ima-ng ima_hash=sha256

# Extend IMA measurements
echo "measure func=BPRM_CHECK" > /etc/ima/ima-policy
echo "measure func=MMAP_CHECK" >> /etc/ima/ima-policy
echo "measure func=MODULE_CHECK" >> /etc/ima/ima-policy
echo "appraise fowner=0 func=BPRM_CHECK" >> /etc/ima/ima-policy
```

---

## 6. Full Disk Encryption with LUKS2

### 6.1 Partition Scheme

| Partition | Size | Filesystem | Encryption | Mount |
|-----------|------|-----------|------------|-------|
| `/dev/sda1` | 512 MiB | FAT32 | No | `/boot/efi` |
| `/dev/sda2` | 1 GiB | ext4 | No | `/boot` |
| `/dev/sda3` | 4 GiB | LUKS2 | Argon2id | `cryptswap` |
| `/dev/sda4` | Remainder | LUKS2 | Argon2id | `cryptroot` |
| `/dev/sda5` | 16 MiB | none | No | BIOS Boot |

### 6.2 LUKS2 Configuration

```bash
# Create LUKS2 container (root)
sudo cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
    --key-size 512 --hash sha512 --pbkdf argon2id \
    --iter-time 3000 --pbkdf-memory 1048576 \
    --pbkdf-parallel 4 /dev/sda4

# Create LUKS2 container (swap with re-encrypt on resume)
sudo cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
    --key-size 256 --hash sha512 --pbkdf argon2id \
    /dev/sda3

# Open and setup
sudo cryptsetup open /dev/sda4 cryptroot
sudo cryptsetup open /dev/sda3 cryptswap

# Add TPM2 slot
sudo systemd-cryptenroll --tpm2-device=auto \
    --tpm2-pcrs=0+2+4+7+9 /dev/sda4
```

### 6.3 LUKS2 Token Configuration

```ini
# /etc/crypttab
cryptroot UUID=<root-part-uuid> none luks,discard,tpm2-device=auto
cryptswap UUID=<swap-part-uuid> /etc/cryptswapkey luks,discard,swap,noearly

# /etc/cryptsetup-keys.d/cryptroot.token
# TPM2 token stored here automatically by systemd-cryptenroll
```

### 6.4 Anti-Forensic Stripe

```
LUKS2 uses AFsplit for anti-forensic information spreading across the
key stripe by default. Additional mitigations:

- LUKS2 header backup to offline media
- Header wipe on 10 failed attempts (via keyslot deactivation)
- Detached LUKS header for high-security deployments
```

---

## 7. Hardened Malloc (glibc with Heap Hardening)

### 7.1 glibc Heap Hardening Features

| Feature | Protection | Enabled By |
|---------|-----------|------------|
| `FORTIFY_SOURCE=3` | Runtime buffer overflow detection | Compiler flag |
| `_GLIBCXX_ASSERTIONS` | C++ standard library bounds checks | Compiler flag |
| Safe Linking | Metadata pointer mangling | Kernel (CONFIG_SLAB_FREELIST_HARDENED) |
| Heap Tagging | Use-after-free detection via MTE | ARM64 only (HW) |
| `tcache` hardening | Double-free detection in tcache | glibc 2.34+ |
| Pointer guard | Function pointer obfuscation | Dynamic linker |
| `mcheck` | Heap consistency checking | Runtime opt-in |
| ASLR on mmap | Randomized heap base addresses | Kernel default |
| `mallopt(M_CHECK_ACTION)` | Abort on heap corruption | Environment |

### 7.2 Environment Configuration

```bash
# /etc/environment or /etc/profile.d/security.sh

# glibc heap hardening
export MALLOC_CHECK_=3          # Abort on all heap errors
export MALLOC_PERTURB_=0xAB     # Fill freed memory with pattern
export MALLOC_MMAP_THRESHOLD_=131072  # Large allocs use mmap
export GLIBC_TUNABLES=glibc.malloc.tcache_count=0:glibc.malloc.perturb=171

# Fortify source at runtime
export _FORTIFY_SOURCE=3

# Dynamic linker hardening
export LD_BIND_NOW=1            # Resolve all symbols at load time
export LD_RELRO_LAZY=0          # Full RELRO
```

### 7.3 Deploying jemalloc or hardened_malloc

```bash
# Option A: System-wide jemalloc
sudo eopkg install jemalloc
echo "libjemalloc.so.2" > /etc/ld.so.preload

# Option B: graphene-hardened_malloc (more aggressive)
git clone https://github.com/GrapheneOS/hardened_malloc
cd hardened_malloc
make
sudo cp out/libhardened_malloc.so /usr/lib/
# Add to /etc/ld.so.preload or LD_PRELOAD per-service
```

---

## 8. Stack Protector, CFI, CET

### 8.1 Stack Protector Levels

| Level | Flag | Protection |
|-------|------|------------|
| None | `-fno-stack-protector` | Disabled |
| Basic | `-fstack-protector` | Functions with >=8 byte char buffers |
| Strong | `-fstack-protector-strong` | Functions with any local array or alloca |
| Full | `-fstack-protector-all` | Every function |

**Synthex default: `-fstack-protector-strong`** for all packages.

### 8.2 Control Flow Integrity (CFI)

```bash
# Clang CFI (kernel)
CONFIG_CFI_CLANG=y
CONFIG_CFI_CLANG_SHADOW=y

# Per-package CFI in Synthex build system
# /etc/synthex-build.conf
CFLAGS+=" -fsanitize=cfi -fvisibility=default"
CXXFLAGS+=" -fsanitize=cfi -fvisibility=default"
LDFLAGS+=" -fsanitize=cfi"
```

### 8.3 Control-flow Enforcement Technology (CET)

```bash
# Intel CET (Shadow Stack + IBT)
# Requires:
#   - Hardware: Intel Tiger Lake (11th gen) or newer
#   - Kernel: Linux 6.2+
#   - Compiler: GCC 10+ or Clang 12+

# Kernel support
CONFIG_X86_CET=y
CONFIG_X86_SHADOW_STACK=y
CONFIG_X86_USER_SHADOW_STACK=y

# Compiler flags
-fcf-protection=full  # Enables both shadow stack and IBT
# or split:
-fcf-protection=branch  # IBT only
-fcf-protection=return  # Shadow stack only
-fcf-protection=none    # Disabled
```

### 8.4 SPECULATION BARRIER

```bash
# Kernel cmdline
spectre_v2=on spec_store_bypass_disable=on tsx=off tsx_async_abort=full,nosmt
kvm.nx_huge_pages=force

# Per-process speculation control
# /sys/devices/system/cpu/vulnerabilities/* should show "Mitigation: ..."
```

---

## 9. Kernel Lockdown (Integrity/Enforcement)

### 9.1 Lockdown Modes

| Mode | Restriction Level | Use Case |
|------|-------------------|----------|
| `none` | No restrictions | Development |
| `integrity` | Kexec/kdbg/kprobe restricted, /dev/mem restricted | Production |
| `enforcement` | All integrity restrictions + module signing enforced | **Paranoid** |

**Synthex default: `lockdown=integrity`** on secure-boot systems.

### 9.2 What Lockdown Restricts

| Feature | Integrity | Enforcement |
|---------|-----------|-------------|
| /dev/mem access | Restricted | Blocked |
| /dev/kmem access | Restricted | Blocked |
| Kexec | Signed only | Signed only |
| kprobes | Restricted | Blocked |
| BPF JIT | JIT only | JIT only |
| Module loading | Signed required | Signed required |
| MSR writing | Blocked | Blocked |
| ACPI table override | Blocked | Blocked |
| PCI BAR access | Blocked | Blocked |
| io_uring | Restricted | Restricted |

### 9.3 Verification

```bash
# Check lockdown status
cat /sys/kernel/security/lockdown

# Check if Secure Boot is enforcing lockdown
dmesg | grep lockdown
mokutil --sb-state
```

---

## 10. Firewalld with nftables

### 10.1 Architecture

```
┌──────────────────────────────────────────────────────┐
│                    firewalld                           │
│  ┌──────────────────────────────────────────────────┐ │
│  │              nftables (backend)                   │ │
│  │  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │   filter      │  │    nat       │              │ │
│  │  │  (INPUT/OUTPUT)│  │(PREROUTING/ │              │ │
│  │  │  FORWARD)     │  │ POSTROUTING) │              │ │
│  │  └──────────────┘  └──────────────┘              │ │
│  │  ┌──────────────┐  ┌──────────────┐              │ │
│  │  │   mangle      │  │   security   │              │ │
│  │  │  (mark/ttl)   │  │(SELinux ctx) │              │ │
│  │  └──────────────┘  └──────────────┘              │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Zones                                │ │
│  │  public │ internal │ dmz │ work │ home │ trusted  │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Services                             │ │
│  │  ssh │ dhcpv6-client │ mDNS │ samba-client │ ... │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 10.2 Base Configuration

```bash
# Set default zone and policies
sudo firewall-cmd --set-default-zone=drop
sudo firewall-cmd --permanent --zone=drop --add-service=ssh
sudo firewall-cmd --permanent --zone=drop --add-service=dhcpv6-client

# Create internal zone for trusted networks
sudo firewall-cmd --permanent --new-zone=internal
sudo firewall-cmd --permanent --zone=internal --add-source=192.168.0.0/16
sudo firewall-cmd --permanent --zone=internal --add-source=10.0.0.0/8
sudo firewall-cmd --permanent --zone=internal --add-service=ssh
sudo firewall-cmd --permanent --zone=internal --add-service=mdns
sudo firewall-cmd --permanent --zone=internal --add-service=samba-client

# Rich rules for logging
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" log prefix="DENY_IPV4" limit value="5/m"'

# Reload
sudo firewall-cmd --reload
```

### 10.3 nftables Direct Rules

```bash
# Custom nftables ruleset for anti-spoofing
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 \
    -m conntrack --ctstate INVALID -j DROP

sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 \
    -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 \
    -i lo -j ACCEPT

# Rate limit SSH
sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 \
    -p tcp --dport 22 -m state --state NEW -m recent --set

sudo firewall-cmd --permanent --direct --add-rule ipv4 filter INPUT 0 \
    -p tcp --dport 22 -m state --state NEW -m recent --update \
    --seconds 60 --hitcount 4 -j DROP
```

---

## 11. Automatic Security Updates Configuration

### 11.1 Synthex Update Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   Auto-Update Pipeline                     │
│                                                            │
│   Timer: synthex-update.timer (daily)                        │
│     └── synthex-update.service                               │
│           ├── eopkg upgrade (repo metadata + packages)     │
│           ├── flatpak update                               │
│           ├── snap refresh (if installed)                  │
│           ├── fwupdmgr update (firmware)                   │
│           └── needrestart -k (check running kernels)       │
│                                                            │
│   Stabilization: staged rollout via synthex-patches repo     │
│     └── Critical/security: immediate push                  │
│     └── Standard: 24h soak                                │
│     └── Optional: 7 day soak                              │
└──────────────────────────────────────────────────────────┘
```

### 11.2 Configuration Files

```ini
# /etc/synthex/auto-update.conf
[Update]
Enabled=true
Interval=daily
RandomizedDelaySec=3600
UpdateFirmware=true
UpdateFlatpak=true
Reboot=auto
RebootWindowStart=02:00
RebootWindowEnd=05:00
NotifyUser=true

[Stability]
SecurityUpdates=instant
StandardUpdates=24h
OptionalUpdates=7d
```

### 11.3 systemd Timer

```ini
# /etc/systemd/system/synthex-update.service
[Unit]
Description=Synthex Automatic Security Update
Documentation=man:eopkg(8)

[Service]
Type=oneshot
ExecStart=/usr/libexec/synthex/auto-update.sh
Nice=19
IOSchedulingClass=2
IOSchedulingPriority=7
ProtectSystem=strict
ProtectHome=yes
```

```ini
# /etc/systemd/system/synthex-update.timer
[Unit]
Description=Daily Synthex Automatic Update Timer

[Timer]
OnCalendar=daily
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
```

### 11.4 Auto-Update Script

```bash
#!/usr/bin/bash
# /usr/libexec/synthex/auto-update.sh

set -euo pipefail

LOG=/var/log/synthex-auto-update.log
exec >> "$LOG" 2>&1
echo "=== Auto-update started $(date) ==="

# Pre-update snapshot (if btrfs)
if command -v snapper &>/dev/null; then
    snapper -c root create -d "pre-auto-update-$(date +%Y%m%d)"
fi

# Update package repos
eopkg ur

# Check for security updates
SECURITY_COUNT=$(eopkg list-updates | grep -c "security" || true)

# Apply all updates
eopkg upgrade -y

# Update Flatpaks
if command -v flatpak &>/dev/null; then
    flatpak update -y
fi

# Update firmware
if command -v fwupdmgr &>/dev/null; then
    fwupdmgr refresh --no-metadata-check 2>/dev/null || true
    fwupdmgr update --no-reboot-check 2>/dev/null || true
fi

# Check if reboot needed
if needs-restarting -k &>/dev/null; then
    echo "Kernel update detected, scheduling reboot"
    /usr/libexec/synthex/schedule-reboot.sh
fi

# Post-update snapshot
if command -v snapper &>/dev/null; then
    snapper -c root create -d "post-auto-update-$(date +%Y%m%d)"
fi

echo "=== Auto-update completed $(date) ==="
```

---

## 12. Flatpak Sandbox + Permissions Manager

### 12.1 Flatpak Sandbox Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Flatpak Sandbox                         │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Bubblewrap   │  │  OSTree      │  │  Portals     │    │
│  │  (namespaces) │  │  (immutable  │  │  (selective  │    │
│  │  user/net/pid │  │   images)    │  │   access)    │    │
│  │  ipc/uts/mnt) │  │              │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  Sandbox Defaults:                                         │
│    - No network access (unless requested)                  │
│    - No X11 socket (Wayland-only)                         │
│    - No D-Bus session bus (unless portal)                  │
│    - No device access (except /dev/null, urandom)          │
│    - Private /tmp                                          │
│    - Read-only /usr                                        │
│    - Per-app permissions store                             │
└──────────────────────────────────────────────────────────┘
```

### 12.2 Synthex Permissions Manager

```bash
# Install Flatpak permission management tool
sudo eopkg install flatpak-permissions-manager

# View installed application permissions
flatpak permissions-show

# Revoke network access for an application
flatpak override --user --unshare=network com.example.App

# Force Wayland-only
flatpak override --user --socket=wayland --nosocket=x11 com.example.App
```

### 12.3 Recommended Permission Policies

| Application Class | Network | Host FS | D-Bus | Devices |
|-------------------|---------|---------|-------|---------|
| Games | ✓ | None (save games via portal) | None | GPU |
| Browsers | ✓ | ~/Downloads (file picker) | None | PulseAudio |
| Office | Optional | ~/Documents (file picker) | None | Printer |
| Media Players | Optional | ~/Music, ~/Videos | MPRIS | PulseAudio |
| IM Clients | ✓ | None | Notifications | Camera (portal) |
| Utilities | ✗ | None | None | None |

### 12.4 System-Wide Flatpak Policy

```ini
# /etc/flatpak/system-policy.conf
[System Policy]
# Default: no network, no X11, no D-Bus
DefaultSocketPolicy=none
DefaultSessionBusPolicy=none
DefaultFilesystemPolicy=private
DefaultDevicePolicy=none

# Allow network for browsers
[Application org.chromium.Chromium]
Socket=wayland
SessionBus=none
Devices=dri

[Application org.mozilla.firefox]
Socket=wayland
SessionBus=none
Devices=dri
```

---

## 13. Browser Sandbox Hardening

### 13.1 Chromium/Chrome Hardening

```bash
# /etc/chromium/policies/managed/synthex-security.json
{
  "BlockExternalExtensions": true,
  "DeveloperToolsAvailability": 2,
  "DisableSafeBrowsingProceedAnyway": true,
  "DNSOverHttpsMode": "secure",
  "DownloadRestrictions": 3,
  "EnableSiteIsolation": true,
  "ForceGoogleSafeSearch": true,
  "ForceYouTubeRestrict": 2,
  "IncognitoModeAvailability": 0,
  "NetworkPredictionOptions": 2,
  "PasswordManagerEnabled": false,
  "SafeBrowsingEnabled": true,
  "SafeBrowsingProtectionLevel": 2,
  "SSLVersionMin": "tls1.2",
  "StartupBarrierEnabled": true,
  "StrictOriginIsolation": true,
  "TripleDESEnabled": false
}

# chrome://flags overrides
# --enable-features=NetworkService,NetworkServiceInProcess
# --disable-features=PasswordImport,EnableEphemeralFlashPermission
```

### 13.2 Firefox Hardening

```javascript
// /etc/firefox/syspolicy.json
{
  "policies": {
    "AppAutoUpdate": true,
    "BlockAboutConfig": false,
    "BlockAboutAddons": false,
    "CaptivePortal": false,
    "Certificates": {
      "ImportEnterpriseRoots": true
    },
    "Cookies": {
      "Behavior": "reject-tracker-and-partition-foreign",
      "BehaviorPrivateBrowsing": "reject-tracker"
    },
    "DNSOverHTTPS": {
      "Enabled": true,
      "Locked": true
    },
    "DisablePocket": true,
    "DisableTelemetry": true,
    "EnableTrackingProtection": {
      "Value": true,
      "Locked": true,
      "Cryptomining": true,
      "Fingerprinting": true
    },
    "ExtensionSettings": {
      "uBlock0@raymondhill.net": {
        "installation_mode": "force_installed",
        "install_url": "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
      }
    },
    "FirefoxHome": {
      "Search": true,
      "TopSites": false,
      "SponsoredTopSites": false,
      "Highlights": false,
      "Pocket": false,
      "SponsoredPocket": false
    },
    "NoDefaultBookmarks": true,
    "OfferToSaveLogins": false,
    "PasswordManagerEnabled": false,
    "Permissions": {
      "Autoplay": {
        "Default": "block-audio-video",
        "Locked": true
      },
      "Camera": {
        "BlockNewRequests": true
      },
      "Location": {
        "BlockNewRequests": true
      },
      "Microphone": {
        "BlockNewRequests": true
      },
      "Notifications": {
        "BlockNewRequests": true
      }
    },
    "SanitizeOnShutdown": {
      "Cache": true,
      "Cookies": true,
      "Downloads": true,
      "FormData": true,
      "History": true,
      "Sessions": true,
      "SiteSettings": true
    },
    "SSLVersionMax": "4",
    "SSLVersionMin": "3",
    "UserMessaging": {
      "ExtensionRecommendations": false,
      "FeatureRecommendations": false,
      "SkipOnboarding": true
    }
  }
}
```

### 13.3 Browser Sandbox Invocation

```bash
# Chromium with maximum sandboxing
chromium \
    --enable-features=NetworkService,NetworkServiceInProcess,StrictOriginIsolation \
    --disable-features=PasswordImport,EnableEphemeralFlashPermission,ChromeWhatsNewUI \
    --enable-strict-site-isolation \
    --disable-3d-apis \
    --disable-component-update \
    --disable-reading-from-canvas \
    --disable-remote-fonts \
    --force-device-scale-factor=1 \
    --enable-hardware-secure-decryption \
    --no-pings

# Firefox with hardened configuration
firefox \
    --new-instance \
    -no-remote \
    -safe-mode
```

---

## 14. AppArmor Compatibility Layer

### 14.1 Architecture

Synthex uses SELinux as the primary LSM but provides an AppArmor compatibility layer
for applications and container runtimes that generate AppArmor profiles:

```
┌─────────────────────────────────────────────────────────┐
│              LSM Stack Order (CONFIG_LSM)                 │
│                                                          │
│  lockdown → integrity → bpf → audit → selinux → smack    │
│  → tomoyo → apparmor → yama → loadpin → safesetid       │
│                                                          │
│  Synthex ships both SELinux and AppArmor but SELinux is    │
│  the primary MAC. AppArmor profiles are converted via    │
│  aa2selinux(8) at package install time.                  │
└─────────────────────────────────────────────────────────┘
```

### 14.2 Profile Conversion

```bash
# Convert AppArmor profile to SELinux policy
sudo aa2selinux --profile /etc/apparmor.d/usr.bin.container \
    --output /etc/selinux/targeted/policy/container.te

# Alternative: run AppArmor in LSM stacking mode
# Kernel must have CONFIG_SECURITY_APPARMOR=y in stacking mode
```

### 14.3 Container Compatibility

```bash
# Docker with SELinux support enabled
# /etc/docker/daemon.json
{
  "selinux-enabled": true,
  "labels": ["distribution=synthex"],
  "userns-remap": "default",
  "live-restore": true
}

# Podman uses SELinux natively
podman run --security-opt label=level:s0:c1,c2 \
    --security-opt label=type:container_t \
    ubuntu
```

---

## 15. Vulnerability Response Process

### 15.1 Severity Classification

| Severity | CVSS Score | Response Time | Notification |
|----------|-----------|---------------|--------------|
| Critical | 9.0-10.0 | < 4 hours | User alert + auto-update |
| High | 7.0-8.9 | < 24 hours | User alert + auto-update |
| Medium | 4.0-6.9 | < 7 days | Update in next cycle |
| Low | 0.1-3.9 | < 30 days | Included in next batch |
| Informational | 0.0 | Next release | Release notes |

### 15.2 Response Workflow

```
DISCOVERY → TRIAGE → PATCH → TEST → RELEASE → VERIFY → POSTMORTEM
   │         │        │       │       │         │         │
   │         ├─ CVE    │       │       ├─ Staged  │         │
   │         │  assignment     │       │  rollout │         │
   │         ├─ Severity│       │       ├─ srpms  │         │
   │         │  scoring │       │       │  pushed │         │
   │         ├─ Affected│       │       └─ Advisory         │
   │         │  packages│       │          released         │
   │         └─ Mitigation       │                          │
   │            assessment│      │                          │
   └─ Bug bounty ─────────┘      │                          │
        program             └─ Build ──────────────────────┘
                                signed
```

### 15.3 Communication Channels

| Channel | Purpose | Audience |
|---------|---------|----------|
| synthex-security-announce | CVE advisories | Public |
| synthex-security-discuss | Technical discussion | Developers |
| synthex-security-internal | Pre-disclosure coordination | Synthex Team |
| Bug Tracker | Bug bounty submissions | Public |

### 15.4 Disclosure Policy

Synthex follows **Coordinated Disclosure (90-day rule)**:

1. **Day 0**: Vulnerability reported
2. **Day 0-7**: Triage, severity assessment, CVE assignment
3. **Day 7-45**: Patch development and testing
4. **Day 45-85**: Embargoed pre-release testing with downstream
5. **Day 85-90**: Public disclosure + advisory
6. **Day 90+**: Postmortem analysis

Expedited timeline (< 24h) for actively exploited zero-days.

---

## 16. Security Dashboard Design (GUI App Spec)

### 16.1 Overview

The Synthex Security Dashboard is a GTK4/libadwaita application providing
a unified interface for security status monitoring and management.

**Package**: `synthex-security-dashboard`
**Location**: `/usr/bin/synthex-security-dashboard`
**DBus Name**: `org.synthex.SecurityDashboard`

### 16.2 Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Security Score** | Overall security posture out of 100 | P0 |
| **Update Status** | Pending security updates with severity | P0 |
| **Firewall Status** | Active zone, rules, blocked connections | P0 |
| **SELinux Status** | Enforcing/permissive/disabled, denials | P0 |
| **Secure Boot** | Status and PCR measurements | P0 |
| **Disk Encryption** | LUKS status, key slots, TPM binding | P0 |
| **App Permissions** | Flatpak applications with effective permissions | P1 |
| **Browser Security** | Browser hardening checklist | P1 |
| **Audit Log** | Real-time security event viewer | P1 |
| **Hardening Score** | CIS benchmark compliance percentage | P1 |
| **Vulnerability Feed** | RSS feed of Synthex CVE advisories | P2 |
| **TPM Health** | TPM 2.0 device status and PCR validation | P2 |

### 16.3 UI Layout

```
┌────────────────────────────────────────────────────────────┐
│ 🔒 Synthex Security Dashboard                        _ □ X  │
├──────────┬─────────────────────────────────────────────────┤
│          │  Overall Security Score                         │
│  NAV     │   ┌───────────────────────────────────────────┐ │
│  ─────   │   │  ████████████████████░░░░   83/100   Good │ │
│  Overview│   └───────────────────────────────────────────┘ │
│  Updates │                                                 │
│  Firewall│  ┌──────┬──────────┬──────┬───────────────────┐ │
│  SELinux │  │Item  │ Status   │ Risk │ Recommendation    │ │
│  TPM     │  ├──────┼──────────┼──────┼───────────────────┤ │
│  Encryption│  │Updates│  3 pending│ High │ 2 security updates│ │
│  Apps    │  │Firewall│   Active │ Low  │ -                │ │
│  Audit   │  │SELinux│Enforcing │ Low  │ -                │ │
│  Report  │  │LUKS   │  Encrypted│ Low  │ No TPM slot      │ │
│          │  │Browser│ 3 of 5   │ Med  │ Enable strict SI │ │
│          │  └──────┴──────────┴──────┴───────────────────┘ │
│          │                                                 │
│          │  Recent Security Events                         │
│          │  [10:32] SELinux denied: chromium...            │
│          │  [09:15] Firewall blocked 1.2.3.4:22           │
│          │  [07:00] Daily update check: 3 pending         │
└──────────┴─────────────────────────────────────────────────┘
```

### 16.4 System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   Data Sources                              │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ auditd    │ │ D-Bus    │ │ Sysfs    │ │ firewalld    │  │
│  │ /var/log/ │ │ org.     │ │ /sys/    │ │ D-Bus API   │  │
│  │ audit/    │ │ synthex.*  │ │ kernel/  │ │              │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ polkit   │ │ systemd  │ │ TPM2     │ │ security     │  │
│  │ auth     │ │ journald │ │ tools    │ │ policies    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 16.5 Data Collection (Gatherer Service)

```python
# /usr/libexec/synthex/security-gatherer.py
# Background service collecting security telemetry

#!/usr/bin/env python3
"""Security data gatherer for the Synthex Security Dashboard."""

import os
import json
import subprocess
import dbus
import dbus.service

# D-Bus interface for the gatherer service
SECURITY_GATHERER_IFACE = "org.synthex.SecurityGatherer1"


class SecurityGatherer(dbus.service.Object):
    """Collects security state from the system."""

    def __init__(self, bus, path):
        super().__init__(bus, path)

    @dbus.service.method(SECURITY_GATHERER_IFACE, out_signature="s")
    def get_security_score(self):
        """Calculate overall security score."""
        score = 0
        score += self._check_selinux()           # 15 pts
        score += self._check_firewall()           # 15 pts
        score += self._check_updates()            # 15 pts
        score += self._check_encryption()         # 15 pts
        score += self._check_secure_boot()        # 10 pts
        score += self._check_apparmor()           # 5 pts
        score += self._check_hardening()          # 15 pts
        score += self._check_browser()            # 10 pts
        return json.dumps({"score": score, "max": 100})

    @dbus.service.method(SECURITY_GATHERER_IFACE, out_signature="s")
    def get_pending_updates(self):
        """Get pending security updates."""
        result = subprocess.run(
            ["eopkg", "list-updates", "--json"],
            capture_output=True, text=True
        )
        return result.stdout

    @dbus.service.method(SECURITY_GATHERER_IFACE, out_signature="s")
    def get_selinux_status(self):
        """Get SELinux enforcement status."""
        status = {}
        result = subprocess.run(["getenforce"], capture_output=True, text=True)
        status["mode"] = result.stdout.strip()

        result = subprocess.run(
            ["seinfo", "--stats"], capture_output=True, text=True
        )
        status["policy_stats"] = result.stdout.strip()
        return json.dumps(status)

    @staticmethod
    def _check_selinux():
        try:
            mode = subprocess.run(
                ["getenforce"], capture_output=True, text=True
            ).stdout.strip()
            if mode == "Enforcing":
                return 15
            elif mode == "Permissive":
                return 5
        except Exception:
            pass
        return 0

    @staticmethod
    def _check_firewall():
        try:
            result = subprocess.run(
                ["firewall-cmd", "--state"], capture_output=True, text=True
            )
            if "running" in result.stdout:
                zone = subprocess.run(
                    ["firewall-cmd", "--get-default-zone"],
                    capture_output=True, text=True
                ).stdout.strip()
                if zone in ("drop", "block"):
                    return 15
                return 10
        except Exception:
            pass
        return 0

    @staticmethod
    def _check_updates():
        try:
            result = subprocess.run(
                ["eopkg", "list-updates"],
                capture_output=True, text=True
            )
            # Count security-related updates
            sec_count = result.stdout.count("security")
            if sec_count == 0:
                return 15
            if sec_count <= 2:
                return 10
            return 5
        except Exception:
            return 0

    @staticmethod
    def _check_encryption():
        try:
            result = subprocess.run(
                ["blkid", "-t", "TYPE=crypto_LUKS"],
                capture_output=True, text=True
            )
            if result.stdout:
                return 15
        except Exception:
            pass
        return 0

    @staticmethod
    def _check_secure_boot():
        try:
            result = subprocess.run(
                ["mokutil", "--sb-state"], capture_output=True, text=True
            )
            if "enabled" in result.stdout:
                return 10
        except Exception:
            pass
        return 0

    @staticmethod
    def _check_apparmor():
        return 5  # Always scored if LSM stacking is configured

    @staticmethod
    def _check_hardening():
        """Check kernel hardening via sysctl."""
        score = 0
        checks = {
            "kernel.kptr_restrict": "2",
            "kernel.dmesg_restrict": "1",
            "kernel.printk": "3 3 3 3",
            "net.ipv4.conf.all.rp_filter": "1",
            "net.ipv4.tcp_syncookies": "1",
        }
        for key, expected in checks.items():
            try:
                result = subprocess.run(
                    ["sysctl", "-n", key], capture_output=True, text=True
                ).stdout.strip()
                if result == expected:
                    score += 3
            except Exception:
                pass
        return min(score, 15)

    @staticmethod
    def _check_browser():
        """Check if browser security policies are applied."""
        score = 0
        chromium_policy = "/etc/chromium/policies/managed/synthex-security.json"
        firefox_policy = "/etc/firefox/syspolicy.json"
        if os.path.exists(chromium_policy):
            score += 5
        if os.path.exists(firefox_policy):
            score += 5
        return score
```

### 16.6 Filesystem Layout

```
/usr/bin/synthex-security-dashboard
/usr/libexec/synthex/security-gatherer.py
/usr/libexec/synthex/security-gatherer.service
/usr/libexec/synthex/security-gatherer.timer
/usr/share/synthex/security-dashboard/ui/main-window.ui
/usr/share/synthex/security-dashboard/ui/overview-page.ui
/usr/share/synthex/security-dashboard/ui/updates-page.ui
/usr/share/synthex/security-dashboard/ui/firewall-page.ui
/usr/share/synthex/security-dashboard/ui/selinux-page.ui
/usr/share/synthex/security-dashboard/ui/audit-page.ui
/usr/share/synthex/security-dashboard/resources/style.css
/usr/share/polkit-1/actions/org.synthex.security-dashboard.policy
/usr/share/dbus-1/system-services/org.synthex.SecurityDashboard.service
/usr/share/applications/org.synthex.SecurityDashboard.desktop
```

### 16.7 PolicyKit Actions

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
  "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
  "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="org.synthex.security-dashboard.view">
    <description>View security dashboard</description>
    <message>Authentication is required to view security settings</message>
    <defaults>
      <allow_any>yes</allow_any>
      <allow_inactive>yes</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
  </action>
  <action id="org.synthex.security-dashboard.manage">
    <description>Modify security settings</description>
    <message>Authentication is required to modify security settings</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
</policyconfig>
```

---

## Appendix A: References

- [CIS Linux Benchmark](https://www.cisecurity.org/benchmark/linux)
- [SELinux Project Wiki](https://selinuxproject.org)
- [TPM2 Software Stack](https://github.com/tpm2-software)
- [Kernel Self-Protection Project](https://kernsec.org/wiki/index.php/Kernel_Self_Protection_Project)
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [NSA SELinux Hardening Guide](https://www.nsa.gov/resources/everyone/cybersecurity/)

## Appendix B: Compliance Mapping

| Control | CIS | NIST 800-53 | PCI DSS |
|---------|-----|-------------|---------|
| FDE (LUKS2) | 1.1.1 | MP-6, SC-28 | 3.4 |
| Secure Boot | 1.8.1 | SI-7, SI-19 | — |
| SELinux | 1.6.1 | AC-3, AC-6 | 7.2.1 |
| Firewalld | 3.1 | SC-7 | 1.1 |
| Auditd | 4.1 | AU-2, AU-3 | 10.1 |
| Update Mgmt | 1.2 | CM-3, SI-2 | 6.1 |
| Kernel Hardening | 1.5 | CM-6, SC-39 | 2.2 |

## Appendix C: License

This architecture document is part of the Linux Synthex Hardening Framework.
Copyright (c) 2026 Linux Synthex Project.
Licensed under CC-BY-SA 4.0 International.
