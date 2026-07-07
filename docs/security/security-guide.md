# Synthex Security Guide

> **Audience:** Security-conscious users, system administrators  
> **Last updated:** July 2026  
> **Synthex version:** 4.6 "Fortitude"

---

## Table of Contents

1. [Security Philosophy](#1-security-philosophy)
2. [Threat Model](#2-threat-model)
3. [Default Security Posture](#3-default-security-posture)
4. [SELinux Explained](#4-selinux-explained)
5. [Firewall Configuration](#5-firewall-configuration)
6. [Encryption Setup Guide](#6-encryption-setup-guide)
7. [Secure Boot Guide](#7-secure-boot-guide)
8. [AppArmor vs SELinux](#8-apparmor-vs-selinux)
9. [Application Sandboxing](#9-application-sandboxing)
10. [Browser Security](#10-browser-security)
11. [Hardening Guide (Advanced)](#11-hardening-guide-advanced)
12. [Security Audit How-To](#12-security-audit-how-to)
13. [Incident Response](#13-incident-response)
14. [Reporting Vulnerabilities](#14-reporting-vulnerabilities)

---

## 1. Security Philosophy

### 1.1 Core Principles

Synthex follows a **defense-in-depth** security philosophy:

```
┌────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                             │
│                                                                │
│  User Awareness       ← Most important, hardest to automate    │
│  ─────────────                                                   │
│  Application Sandboxing  (Flatpak, bubblewrap, Firejail)       │
│  ───────────────────────                                        │
│  MAC (SELinux)             (Mandatory Access Control)          │
│  ─────────────                                                   │
│  DAC (File Permissions)    (Traditional Unix rwx)              │
│  ───────────────────────                                        │
│  Encryption (LUKS)         (Data at rest)                      │
│  ───────────────────────                                        │
│  Firewall (firewalld)      (Network access control)            │
│  ───────────────────────                                        │
│  Secure Boot + TPM        (Hardware root of trust)             │
│  ───────────────────────                                        │
│  Kernel Hardening         (LSM, seccomp, namespaces)           │
│  ───────────────────────                                        │
│  Firmware Security        (UEFI, ME/PSP updates)               │
│  ───────────────────────                                        │
│  Physical Security        (Lock screen, disk encryption)       │
│  ───────────────────────                                        │
│                                                                │
│  Securing each layer provides protection even if               │
│  another layer is compromised.                                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SELinux enforcing by default** | Strong MAC protects against 0-days and misconfigurations |
| **firewalld with nftables** | Dynamic, zone-based firewall with modern backend |
| **LUKS2 + TPM2** | Full-disk encryption with optional auto-unlock |
| **Flatpak for apps** | Application sandboxing out of the box |
| **Wayland as default** | Better security than X11 (no keylogging, no screen grabbing) |
| **Systemd-oomd** | Prevents OOM hangs, limits DoS impact |
| **Seccomp in systemd** | Systemd services run with filtered syscalls |
| **No sudo password persistence** | Every sudo call requires authentication |

### 1.3 What Synthex Does NOT Do

- Synthex does **not** include an antivirus (not needed on Linux with proper configuration)
- Synthex does **not** include a VPN (user choice)
- Synthex does **not** restrict user freedoms (you can disable SELinux if needed)
- Synthex does **not** phone home with telemetry (privacy-respecting)

---

## 2. Threat Model

### 2.1 Threat Profiles

| Profile | Threat Actors | Primary Risks |
|---------|--------------|---------------|
| **Desktop User** | Malware, phishing, web tracking | Browser exploits, malicious downloads, credential theft |
| **Developer** | Supply chain attacks, code injection | Compromised dependencies, malicious packages |
| **System Admin** | Network attacks, privilege escalation | SSH brute force, vulnerable services, lateral movement |
| **Journalist/Activist** | Targeted surveillance, device seizure | Physical access, forensic analysis, network monitoring |
| **Enterprise** | Insider threats, compliance violations | Data exfiltration, policy violations |

### 2.2 Attack Surface

```
┌─────────────────────────────────────────────────────────────┐
│                    ATTACK SURFACE                            │
│                                                              │
│  Network-facing:                                             │
│  ├── Open ports (SSH, HTTP if enabled)                      │
│  ├── Browser (JavaScript, WebAssembly, WebGL)               │
│  ├── Email (phishing, malicious attachments)                 │
│  └── Network protocols (SMB, NFS, UPnP)                     │
│                                                              │
│  Local:                                                      │
│  ├── USB devices (BadUSB, Rubber Ducky)                     │
│  ├── Thunderbolt (DMA attacks)                               │
│  ├── Physical access (boot from USB, cold boot)             │
│  └── Side-channel (spectre, meltdown)                        │
│                                                              │
│  Software:                                                   │
│  ├── System services (D-Bus, polkit, systemd)               │
│  ├── SUID binaries                                           │
│  ├── Kernel exploits                                         │
│  └── Third-party software (Flatpak, containers)             │
│                                                              │
│  Supply chain:                                               │
│  ├── Compromised package repository                          │
│  ├── Malicious Flatpak apps                                  │
│  └── Dependency confusion                                    │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Mitigation by Layer

| Threat | Primary Mitigation | Secondary Mitigation |
|--------|-------------------|---------------------|
| Web browser exploit | SELinux + Wayland | Flatpak browser sandbox |
| Malicious download | Flatpak sandbox | Firejail for native apps |
| Network attack | firewalld (default deny) | SELinux network controls |
| Physical theft | LUKS full-disk encryption | TPM2 + Secure Boot |
| Privilege escalation | SELinux + no SUID | systemd hardening |
| USB attack | USBGuard | Disable USB autorun |
| DMA attack | IOMMU (VT-d/AMD-Vi) | Thunderbolt security level |
| Supply chain | GPG package signing | Reproducible builds |

---

## 3. Default Security Posture

### 3.1 Out-of-the-Box Security

```bash
# What's enabled by default:
✓ SELinux (enforcing mode)
✓ firewalld (default zone: public)
✓ LUKS2 (if chosen during install)
✓ Secure Boot (if hardware supports)
✓ Wayland display server
✓ systemd-oomd (OOM prevention)
✓ systemd-resolved (DNS-over-TLS)
✓ Automatic security updates
✓ Kernel lockdown (if Secure Boot active)
✓ seccomp for systemd services
✓ Address Space Layout Randomization (ASLR)
✓ Exec-Shield (NX bit enforcement)
✓ Kernel page table isolation (KPTI)
```

### 3.2 Default Open Ports

```bash
# Check what ports are open
sudo ss -tlnp

# Default: No inbound ports open
# firewalld in 'public' zone blocks all inbound traffic
# unless explicitly allowed

# Outbound: All allowed (default permit)
```

### 3.3 Default User Privileges

```bash
# User is in 'wheel' group → can sudo
$ sudo whoami
# → root

# Password required for sudo (every time)
# No password persistence

# Polkit requires authentication for system changes
# (installing software, modifying system settings)
```

### 3.4 Automatic Updates

```bash
# Security updates installed automatically
systemctl status dnf5-automatic.timer
# → dnf5-automatic.timer - Daily download of packages

# Configuration at /etc/dnf/automatic.conf
[commands]
apply_updates = yes
upgrade_type = security
random_sleep = 360

[emitters]
emit_via = stdio

[base]
debuglevel = 1
```

### 3.5 Checking Your Security Posture

```bash
# Overall security score (if installed)
sudo dnf5 install lynis
sudo lynis audit system

# Check SELinux status
getenforce
# → Enforcing

# Check firewall
sudo firewall-cmd --state
# → running

# Check encryption
sudo cryptsetup status luks-$(lsblk -o UUID /dev/nvme0n1p3 | tail -1)

# Check Secure Boot
mokutil --sb-state
# → SecureBoot enabled

# Check kernel security features
cat /proc/sys/kernel/randomize_va_space
# → 2 (full ASLR)
cat /proc/sys/kernel/kptr_restrict
# → 1 (restrict kernel pointer exposure)
cat /proc/sys/kernel/dmesg_restrict
# → 1 (restrict dmesg to root)
```

---

## 4. SELinux Explained

### 4.1 What is SELinux?

SELinux (Security-Enhanced Linux) implements **Mandatory Access Control (MAC)**, which means:

> **MAC:** System-wide policy defines what every process can do, regardless of the user running it.
> **DAC (Traditional):** Users control their own files. Root can do anything.

### 4.2 SELinux on Synthex

```bash
# Current status
sestatus
# SELinux status:                 enabled
# SELinuxfs mount:                /sys/fs/selinux
# SELinux root directory:         /etc/selinux
# Loaded policy name:             targeted
# Current mode:                   enforcing
# Mode from config file:          enforcing
# Policy MLS status:              enabled
# Policy deny_unknown:            denied
# Memory protection checking:     actual (secure)
# Max kernel policy version:      33
```

**Synthex runs SELinux in `targeted` mode:**
- Most processes run under their own confined domains
- User processes run under unconfined domains (limited restrictions for usability)
- Network-facing services are strictly confined
- This balances security with desktop usability

### 4.3 SELinux Modes

| Mode | Behavior | When to Use |
|------|----------|-------------|
| `enforcing` | Policy enforced, violations denied | Production (default) |
| `permissive` | Violations logged but allowed | Troubleshooting, policy development |
| `disabled` | SELinux turned off | Last resort (not recommended) |

```bash
# Temporarily switch modes (until reboot)
sudo setenforce 0    # permissive
sudo setenforce 1    # enforcing

# Permanent change (requires reboot)
sudo sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config
```

### 4.4 SELinux Contexts

Every file, process, port, and device has a SELinux context:

```bash
# File contexts
ls -Z /usr/bin/passwd
# system_u:object_r:passwd_exec_t:s0

# Process contexts
ps -eZ | grep sshd
# system_u:system_r:sshd_t:s0-s0:c0.c1023

# Format: user:role:type:sensitivity[:categories]
# Example: system_u:system_r:sshd_t:s0
```

**Context components:**
| Field | Description | Example |
|-------|-------------|---------|
| **user** | SELinux user identity | `system_u`, `user_u` |
| **role** | Role-based access control | `system_r`, `object_r` |
| **type** | Type (primary access control) | `sshd_t`, `passwd_exec_t` |
| **sensitivity** | MLS level | `s0` (unclassified) |

### 4.5 Common SELinux Commands

```bash
# Check context
ls -Z /path/to/file
id -Z                   # Your process context
ps -eZ | grep <proc>    # Process context

# Audit log
sudo ausearch -m avc -ts recent
sudo grep AVC /var/log/audit/audit.log | tail -20
sudo journalctl -t audit | grep AVC

# Interactive troubleshooting
sudo sealert -a /var/log/audit/audit.log

# Fix file context
sudo restorecon -Rv /path          # Restore to defaults
sudo restorecon -F -Rv /path       # Force restore
sudo chcon -t httpd_sys_content_t /path  # Manual change

# Boolean management
getsebool -a | grep httpd
sudo setsebool -P httpd_enable_cgi on
```

### 4.6 Troubleshooting SELinux Denials

```bash
# When an application fails, check if SELinux is blocking:

# 1. Check audit log
sudo journalctl -t audit -n 20
# Example denial:
# type=AVC msg=audit(1234567890.123:456): avc: denied { read } \
#   for pid=1234 comm="nginx" name="index.html" \
#   dev="dm-0" ino=5678 \
#   scontext=system_u:system_r:httpd_t:s0 \
#   tcontext=unconfined_u:object_r:admin_home_t:s0 \
#   tclass=file

# 2. Generate a policy module to fix it
sudo grep AVC /var/log/audit/audit.log | tail -1 | \
  audit2allow -M mymodule
sudo semodule -i mymodule.pp

# 3. Or temporarily set permissive for a domain
sudo semanage permissive -a httpd_t

# 4. Or fix file labeling
sudo restorecon -Rv /var/www/
```

### 4.7 SELinux Policies for Common Scenarios

```bash
# Web server (if running Apache/Nginx)
sudo setsebool -P httpd_can_network_connect on
sudo setsebool -P httpd_enable_homedirs on
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/www(/.*)?'
sudo restorecon -Rv /srv/www

# Custom application directory
sudo semanage fcontext -a -t bin_t '/opt/myapp/bin(/.*)?'
sudo restorecon -Rv /opt/myapp

# NFS home directories
sudo setsebool -P use_nfs_home_dirs on

# Samba sharing
sudo setsebool -P samba_enable_home_dirs on
sudo setsebool -P samba_export_all_rw on
```

### 4.8 When to Disable SELinux

> **General rule: Do not disable SELinux.** Instead, fix the policy.

Valid reasons to investigate:
- You're developing new SELinux policy
- A known application incompatibility (rare with targeted policy)
- Running specialized software that genuinely conflicts

Always try these before disabling:
1. Check audit logs for denials
2. Create custom policy module with audit2allow
3. Set the relevant domain to permissive (not global)
4. Ensure proper file contexts with restorecon

---

## 5. Firewall Configuration

### 5.1 firewalld Overview

Synthex uses **firewalld** with **nftables** as its backend:

```
┌────────────────────────────────────────────────────────────────┐
│                    FIREWALLD ARCHITECTURE                      │
│                                                                │
│   ┌──────────────────────────────────────────────────────┐    │
│   │                   firewalld                           │    │
│   │  • Dynamic zone-based firewall management             │    │
│   │  • D-Bus API for runtime changes                      │    │
│   │  • firewall-cmd CLI / firewall-config GUI             │    │
│   └──────────────────────┬───────────────────────────────┘    │
│                          │                                    │
│                          ▼                                    │
│   ┌──────────────────────────────────────────────────────┐    │
│   │        nftables backend (kernel netfilter)            │    │
│   │  • Tables: filter, nat, mangle, raw, security        │    │
│   │  • Chains: INPUT, FORWARD, OUTPUT                    │    │
│   │  • Rules: zone-based filtering                       │    │
│   └──────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Default Zones

```bash
# List zones
sudo firewall-cmd --get-zones
# → block dmz drop external home internal public trusted work

# Default zone
sudo firewall-cmd --get-default-zone
# → public

# Zone descriptions:
# drop:      All incoming packets dropped (no reply)
# block:     All incoming connections rejected (icmp-host-prohibited)
# public:    Default. Untrusted networks. Allow selected services.
# external:  For masquerading (NAT), like routers
# dmz:       For DMZ networks, limited access
# work:      Trusted work network, more services allowed
# home:      Trusted home network, even more services
# internal:  Very trusted network
# trusted:   All connections accepted
```

### 5.3 Basic Firewall Commands

```bash
# Status
sudo firewall-cmd --state
sudo firewall-cmd --list-all           # Current zone config
sudo firewall-cmd --list-all-zones     # All zones

# Zone management
sudo firewall-cmd --set-default-zone=home
sudo firewall-cmd --zone=public --change-interface=eth0
sudo firewall-cmd --get-active-zones

# Allow services (pre-defined)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=samba-client
sudo firewall-cmd --reload

# Allow ports
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=3000-3010/tcp
sudo firewall-cmd --reload

# Remove rules
sudo firewall-cmd --permanent --remove-service=ssh
sudo firewall-cmd --permanent --remove-port=8080/tcp
sudo firewall-cmd --reload
```

### 5.4 Advanced Rules

```bash
# Rich rules (granular control)
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" \
  source address="192.168.1.0/24" \
  port port="22" protocol="tcp" accept'

# Service definition
sudo firewall-cmd --permanent --new-service=myapp
sudo firewall-cmd --permanent --service=myapp --add-port=9000/tcp
sudo firewall-cmd --permanent --add-service=myapp
sudo firewall-cmd --reload

# Rate limiting (SSH brute force protection)
sudo firewall-cmd --permanent --add-rich-rule='rule service name="ssh" \
  limit value="5/m" accept'

# Logging
sudo firewall-cmd --permanent --add-rich-rule='rule \
  log prefix="DROPPED" limit value="3/m" drop'

# Masquerading (NAT)
sudo firewall-cmd --permanent --zone=external --add-masquerade
```

### 5.5 Firewall GUI

```bash
# Graphical firewall configuration
sudo firewall-config
```

Available in KDE: System Settings → Network → Firewall

### 5.6 Lockdown Whitelist

For applications that need port access (game servers, development tools):

```bash
# Add specific apps to lockdown whitelist
sudo firewall-cmd --permanent --add-lockdown-whitelist-command=/usr/bin/steam
sudo firewall-cmd --permanent --add-lockdown-whitelist-command=/usr/bin/node
sudo firewall-cmd --reload
```

### 5.7 UFW Alternative

If you prefer UFW over firewalld:

```bash
sudo dnf5 install ufw
sudo systemctl disable firewalld
sudo systemctl enable --now ufw

sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

---

## 6. Encryption Setup Guide

### 6.1 Full Disk Encryption (LUKS2)

Synthex uses **LUKS2** (Linux Unified Key Setup version 2) for full-disk encryption:

```bash
# Current LUKS status
sudo cryptsetup luksDump /dev/nvme0n1p3

# Key features:
# - Version: LUKS2
# - Cipher: aes-xts-plain64
# - Key size: 512 bits (256-bit AES effective)
# - PBKDF: argon2id (memory-hard, GPU-resistant)
# - Hash: SHA256
```

### 6.2 LUKS Operations

```bash
# Create encrypted partition
sudo cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --pbkdf argon2id \
  --hash sha256 \
  /dev/sdb1

# Open encrypted partition
sudo cryptsetup open /dev/sdb1 myvolume

# Close
sudo cryptsetup close myvolume

# Change passphrase
sudo cryptsetup luksChangeKey /dev/sdb1

# Add additional key slot
sudo cryptsetup luksAddKey /dev/sdb1

# Remove key slot
sudo cryptsetup luksRemoveKey /dev/sdb1 -S 1

# Backup LUKS header (IMPORTANT!)
sudo cryptsetup luksHeaderBackup /dev/sdb1 --header-backup-file luks-header.bak

# Restore header
sudo cryptsetup luksHeaderRestore /dev/sdb1 --header-backup-file luks-header.bak
```

### 6.3 TPM2 Auto-Unlock

For unattended boot:

```bash
# Prerequisites
sudo dnf5 install tpm2-tools systemd-cryptsetup

# Enroll TPM2
sudo systemd-cryptenroll --tpm2-device=auto \
  --tpm2-pcrs=0+7 \
  /dev/nvme0n1p3

# Configure crypttab
# /etc/crypttab
luks-<UUID> UUID=<UUID> /dev/null tpm2-device=auto,discard

# Regenerate initramfs
sudo dracut --force
```

### 6.4 FIDO2/Token Unlock

```bash
# With YubiKey or similar token
sudo systemd-cryptenroll --fido2-device=auto \
  --fido2-with-client-pin=yes \
  /dev/nvme0n1p3

# /etc/crypttab
luks-<UUID> UUID=<UUID> /dev/null fido2-device=auto
```

### 6.5 Recovery Key

```bash
# Generate a recovery key (backup this!)
sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3

# View (write down and store safely)
sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3 --show
```

### 6.6 File-Level Encryption

For encrypting individual files/directories:

```bash
# eCryptfs (encrypted home directory)
# Not recommended for new installations; use LUKS + BTRFS instead

# GPG file encryption
gpg -c myfile.txt                    # Symmetric encryption
gpg -e -r recipient@example.com myfile.txt  # Public key encryption
gpg -d myfile.txt.gpg                # Decrypt

# OpenSSL file encryption
openssl enc -aes-256-cbc -salt -in file.txt -out file.txt.enc
openssl enc -d -aes-256-cbc -in file.txt.enc -out file.txt

# 7-Zip (supports AES-256)
7z a -p archive.7z myfile.txt

# VeraCrypt (cross-platform container)
sudo dnf5 install veracrypt
```

### 6.7 Encrypted Messaging

```bash
# Signal (recommended for messaging)
flatpak install flathub org.signal.Signal

# Thunderbird with OpenPGP
# Settings → End-to-End Encryption → Add OpenPGP Key

# Element (Matrix client) with E2EE
flatpak install flathub im.riot.Riot
```

---

## 7. Secure Boot Guide

### 7.1 Understanding Secure Boot

Secure Boot ensures that only signed software runs during the boot process:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ UEFI Firmware│────>│ Shim         │────>│ GRUB         │
│ (Built-in KEK)│    │ (MS signed)  │     │ (MOK signed) │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                        ┌──────────────┐
                                        │ Linux Kernel │
                                        │ (MOK signed) │
                                        └──────────────┘
```

### 7.2 Checking Secure Boot Status

```bash
# Is Secure Boot enabled?
mokutil --sb-state
# → SecureBoot enabled

# List enrolled MOK keys
mokutil --list-enrolled

# List MOK keys in MOK database (pending)
mokutil --list-moks
```

### 7.3 Managing MOK Keys

```bash
# Enroll a new key (from file)
sudo mokutil --import /path/to/key.der
# → Set enrollment password, then reboot

# Remove a MOK key
sudo mokutil --delete
# → Interactive, select key to remove

# Reset MOK database (use with caution)
sudo mokutil --reset

# Generate a new MOK key pair
sudo mokutil --generate
```

### 7.4 Signing Custom Kernels

```bash
# Using sbsign
sudo dnf5 install sbsigntools

# Create signing key
openssl req -new -x509 -newkey rsa:2048 -keyout MOK.key \
  -out MOK.pem -days 3650 -subj "/CN=My Custom Kernel/"

# Sign kernel
sudo sbsign --key MOK.key --cert MOK.pem \
  --output /boot/vmlinuz-linux.signed \
  /boot/vmlinuz-linux

# Sign EFI binary
sudo sbsign --key MOK.key --cert MOK.pem \
  --output /boot/efi/EFI/synthex/grubx64.efi.signed \
  /boot/efi/EFI/synthex/grubx64.efi

# Enroll the key
sudo mokutil --import MOK.pem
# Reboot and follow MokManager prompts
```

### 7.5 Secure Boot Troubleshooting

| Symptom | Cause | Solution |
|---------|-------|----------|
| "Forbidden" at boot | Shim can't verify GRUB | Enroll MOK key with MokManager |
| "Invalid signature" | Kernel not signed for this MOK | Re-sign kernel, re-enroll key |
| "Boot Device Not Found" | ESP not properly configured | Reinstall GRUB to ESP |
| Stuck at MokManager | Wrong password | Reboot, try again or reset MOK |
| Windows won't boot | GRUB broke Windows entry | `sudo grub2-mkconfig -o /boot/grub2/grub.cfg` |

### 7.6 Disabling Secure Boot

```bash
# In UEFI settings:
# 1. Reboot and enter BIOS/UEFI (F2, Del, F10, etc.)
# 2. Navigate to Secure Boot / Security tab
# 3. Set Secure Boot to Disabled
# 4. Save and exit

# On some systems: Switch from "UEFI" to "CSM/Legacy" mode
```

---

## 8. AppArmor vs SELinux

### 8.1 Comparison

| Feature | SELinux | AppArmor |
|---------|---------|----------|
| **Type** | Label-based MAC | Path-based MAC |
| **Policy model** | Type Enforcement (TE) | Profile-based |
| **Granularity** | File labels, process types, security classes | File paths, network access |
| **Complexity** | Higher (requires understanding contexts) | Lower (easier to write profiles) |
| **Flexibility** | More granular control | Simpler, less flexible |
| **Learning curve** | Steep | Moderate |
| **Performance** | Slightly higher overhead | Minimal overhead |
| **Default on Synthex** | ✅ Yes | ❌ Not installed |

### 8.2 Why Synthex Uses SELinux

Synthex chose SELinux over AppArmor for several reasons:

1. **Granularity** — SELinux can distinguish between "Apache reading /var/www" and "Apache reading /etc/shadow" at the kernel level
2. **Fine-grained network control** — SELinux can control which ports a process can bind to
3. **Standardization** — SELinux is the standard for Red Hat/Fedora ecosystem (Synthex is RPM-based)
4. **Multi-level security** — MLS/MCS support for compartmentalized environments
5. **Established tooling** — audit2allow, semanage, sealert are mature

### 8.3 When AppArmor Might Be Preferred

- Simpler environments where ease of use matters more than granular control
- Systems with limited administration overhead
- Ubuntu/Debian-based environments (AppArmor is standard there)

### 8.4 Using AppArmor on Synthex (Optional)

```bash
# Install AppArmor alongside SELinux
sudo dnf5 install apparmor-utils apparmor-profiles

# Enable AppArmor
sudo systemctl enable --now apparmor

# Check status
sudo aa-status

# Note: SELinux and AppArmor can coexist, but managing both
# adds complexity. Stick with SELinux unless you have a specific need.
```

---

## 9. Application Sandboxing

### 9.1 Sandboxing Options

| Method | Technology | Isolation Level | Available on Synthex |
|--------|-----------|----------------|-------------------|
| **Flatpak** | bubblewrap + seccomp + namespaces | Strong, user-friendly | ✅ Default |
| **Firejail** | Namespaces + seccomp | Strong, manual config | ✅ `dnf5 install firejail` |
| **Docker/Podman** | Full container | Very strong (separate filesystem) | ✅ `dnf5 install podman` |
| **bubblewrap** | Direct namespace creation | Strong, low-level | ✅ `dnf5 install bubblewrap` |
| **KDE Plasma sandbox** | Application isolation | Moderate | ✅ Built-in |

### 9.2 Flatpak Sandbox Details

```bash
# Flatpak uses:
# - Bubblewrap: User namespace, PID namespace, mount namespace
# - Seccomp: Filtered system calls (~50% of syscalls blocked by default)
# - SELinux: Confined context
# - D-Bus proxy: Filtered IPC access
# - Portal API: Mediated desktop access (files, camera, screen)

# Check sandbox permissions
flatpak info --show-permissions org.mozilla.firefox
flatpak override org.mozilla.firefox --socket=wayland

# Reset permissions
flatpak override --reset org.mozilla.firefox

# View permissions in GUI
flatpak run org.mozilla.firefox --command=flatpak-permissions
```

### 9.3 Firejail Usage

```bash
# Install Firejail
sudo dnf5 install firejail firejail-profiles

# Run an application in a sandbox
firejail firefox
firejail --net=none firefox  # No network access
firejail --private firefox    # No home directory access
firejail --seccomp firefox    # Seccomp filter

# Create custom profile
# /etc/firejail/myapp.local
capabilities none
netfilter /etc/firejail/nolocal.net
seccomp
private-dev
private-tmp

# Run with custom profile
firejail --profile=myapp.local /usr/bin/myapp

# List sandboxed processes
firejail --list
```

### 9.4 Podman Containers

```bash
# Run container sandbox
podman run --rm -it --security-opt=seccomp=default.json \
  fedora:latest echo "Hello from container"

# For desktop application containers
podman run --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /run/user/1000/wayland-0:/run/user/1000/wayland-0 \
  fedora-lxde lxterminal
```

### 9.5 KDE Plasma Application Isolation

```bash
# KDE can run apps in sandboxed environments:
# System Settings → Applications → Application Style → Window Rules

# Or via kstart:
kstart5 --windowclass sandboxed
```

---

## 10. Browser Security

### 10.1 Firefox Hardening

```bash
# Install from Flatpak for sandboxing
flatpak install flathub org.mozilla.firefox

# Firefox security configuration (about:config):
# These settings can be managed via policies.json
# /etc/firefox/policies/policies.json
{
  "policies": {
    "DisableTelemetry": true,
    "EnableTrackingProtection": {
      "Value": true,
      "Locked": true
    },
    "DNSOverHTTPS": {
      "Enabled": true,
      "Locked": true,
      "ProviderURL": "https://mozilla.cloudflare-dns.com/dns-query"
    },
    "SanitizeOnShutdown": {
      "Cache": true,
      "Cookies": false,
      "History": true,
      "FormData": true,
      "Sessions": true
    }
  }
}
```

### 10.2 Recommended Browser Extensions

| Extension | Purpose |
|-----------|---------|
| **uBlock Origin** | Ad blocking, tracker blocking, anti-malware |
| **HTTPS Everywhere** | Force HTTPS connections |
| **Privacy Badger** | Automatic tracker blocking |
| **NoScript** | JavaScript whitelist (advanced) |
| **Bitwarden** | Open-source password manager |
| **Multi-Account Containers** | Firefox Container isolation |

### 10.3 Chromium Security

```bash
# Install Chromium
sudo dnf5 install chromium

# Run with security flags
chromium \
  --enable-strict-mixed-content-checking \
  --enable-features=NetworkService,NetworkServiceInProcess \
  --disable-features=BookmarkWhenSyncEnabled \
  --disable-component-update
```

### 10.4 DNS Privacy

```bash
# DNS-over-HTTPS (DoH) via systemd-resolved
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1 1.0.0.1
DNSOverTLS=yes
DNSSEC=allow-downgrade

# Apply
sudo systemctl restart systemd-resolved

# Verify
resolvectl query example.com
resolvectl statistics
```

### 10.5 Browser Isolation

For high-security browsing:

```bash
# Run browser in isolated container
firejail --net=none firefox  # No network (offline only)
firejail --private firefox    # No home access
# Or use separate browser for sensitive tasks
```

---

## 11. Hardening Guide (Advanced)

### 11.1 Kernel Hardening

```bash
# /etc/sysctl.d/99-security.conf
# Kernel hardening parameters

# Restrict kernel pointer exposure
kernel.kptr_restrict=2

# Restrict dmesg to root
kernel.dmesg_restrict=1

# Disable kexec (no kernel replacement without reboot)
kernel.kexec_load_disabled=1

# Restrict BPF (if not using containers)
kernel.unprivileged_bpf_disabled=1
net.core.bpf_jit_harden=2

# ASLR tuning
kernel.randomize_va_space=2

# Disable user namespaces (breaks containers)
# user.max_user_namespaces=0

# TCP hardening
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_rfc1337=1
net.ipv4.conf.all.rp_filter=1
net.ipv4.conf.all.accept_source_route=0
net.ipv6.conf.all.accept_source_route=0
net.ipv4.conf.all.accept_redirects=0
net.ipv6.conf.all.accept_redirects=0
net.ipv4.conf.all.secure_redirects=0

# Apply
sudo sysctl --system
```

### 11.2 Disable Unused Services

```bash
# List active services
systemctl list-units --type=service --state=running

# Disable unnecessary services
sudo systemctl disable --now bluetooth.service    # If not using Bluetooth
sudo systemctl disable --now cups.service         # If not printing
sudo systemctl disable --now sshd.service         # If not using SSH
sudo systemctl disable --now postfix.service      # If not running mail server
sudo systemctl disable --now avahi-daemon.service # If not using mDNS

# Mask services (links to /dev/null, prevents activation)
sudo systemctl mask cups.service
```

### 11.3 SUID/SGID Hardening

```bash
# Find all SUID binaries
sudo find / -perm -4000 -type f -ls

# Remove SUID from unnecessary binaries
sudo chmod u-s /usr/bin/chsh
sudo chmod u-s /usr/bin/chfn
sudo chmod u-s /usr/bin/passwd     # May need for multi-user
sudo chmod u-s /usr/bin/newgrp
sudo chmod u-s /usr/bin/gpasswd
sudo chmod u-s /usr/bin/pkexec     # Required for polkit
sudo chmod u-s /usr/bin/su
sudo chmod u-s /usr/bin/sudo
sudo chmod u-s /usr/bin/mount
sudo chmod u-s /usr/bin/umount

# More aggressive (test first):
# sudo chmod u-s /usr/bin/ping
# sudo chmod u-s /usr/libexec/polkit-agent-helper-1

# Alternatively, use a whitelist approach:
# Remove SUID from all files, then restore for known-required ones
```

### 11.4 PAM Hardening

```bash
# Enforce strong passwords
# /etc/security/pwquality.conf
minlen = 12
minclass = 4
maxrepeat = 3
badwords = synthex linux password

# Account lockout after failed attempts
# /etc/pam.d/system-auth
# Add to auth section:
auth        required      pam_faillock.so preauth audit silent deny=5 unlock_time=900

# Add to account section:
account     required      pam_faillock.so

# Require current password for sudo
# /etc/pam.d/sudo defaults:
auth       sufficient   pam_unix.so try_first_pass likeauth nullok
```

### 11.5 USB Device Control

```bash
# Install USBGuard
sudo dnf5 install usbguard

# Generate initial policy
sudo usbguard generate-policy > /etc/usbguard/rules.conf

# Start service
sudo systemctl enable --now usbguard

# Manage USB devices
sudo usbguard list-devices
sudo usbguard allow-device <id>
sudo usbguard block-device <id>
sudo usbguard reject-device <id>

# USBGuard GUI
sudo dnf5 install usbguard-notifier
```

### 11.6 Disable Thunderbolt DMA

```bash
# Check Thunderbolt security level
# /sys/bus/thunderbolt/security

# Set to secure connect (requires authentication)
# In UEFI: Set Thunderbolt security to "Secure Connect"
# Or via boltctl:
sudo dnf5 install bolt
boltctl list
boltctl enroll <device-uid>
```

### 11.7 System Call Filtering

```bash
# systemd service hardening (per-service seccomp filters)
# Example: /etc/systemd/system/custom.service.d/hardening.conf
[Service]
# System call filtering
SystemCallArchitectures=native
SystemCallFilter=@system-service @pkey
SystemCallErrorNumber=EPERM

# Filesystem restrictions
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Network restrictions
PrivateNetwork=yes                   # No network (if not needed)
RestrictAddressFamilies=AF_UNIX     # Only UNIX sockets

# Process restrictions
NoNewPrivileges=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
RestrictNamespaces=yes
MemoryDenyWriteExecute=yes

# User/group restrictions
DynamicUser=yes
```

### 11.8 Kernel Module Hardening

```bash
# Block unnecessary kernel modules
# /etc/modprobe.d/blacklist.conf
blacklist btusb          # Bluetooth
blacklist bluetooth
blacklist uvcvideo       # Webcam (if not needed)
blacklist snd-usb-audio  # USB audio devices

# Apply
sudo dracut --force
```

---

## 12. Security Audit How-To

### 12.1 Lynis Security Audit

```bash
# Install Lynis
sudo dnf5 install lynis

# Run full audit
sudo lynis audit system

# Output categories (with scores):
# - [0-60]  Poor
# - [60-80] Average  
# - [80-90] Good
# - [90-100] Excellent

# View specific findings
sudo lynis audit system --quick

# Generate HTML report
sudo lynis audit system --report-file /tmp/lynis-report.html

# Only specific tests
sudo lynis audit system --tests "AUTH-9308 AUTH-9328"
```

### 12.2 OpenSCAP Compliance

```bash
# Install OpenSCAP
sudo dnf5 install openscap-scanner scap-security-guide

# Scan against standard profile
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_standard \
  --results-arf /tmp/oscap-results.xml \
  --report /tmp/oscap-report.html \
  /usr/share/xml/scap/ssg/content/ssg-synthex-ds.xml

# View HTML report
xdg-open /tmp/oscap-report.html

# Remediate findings
sudo oscap xccdf eval --remediate \
  --profile xccdf_org.ssgproject.content_profile_standard
```

### 12.3 ClamAV Malware Scan

```bash
# Install ClamAV
sudo dnf5 install clamav clamav-update

# Update virus definitions
sudo freshclam

# Quick scan of user home
clamscan -r --bell -i /home/$USER

# Full system scan (takes a while)
sudo clamscan -r --bell -i --exclude-dir=/sys --exclude-dir=/proc --exclude-dir=/dev /

# Check for rootkits
sudo dnf5 install rkhunter
sudo rkhunter --check --skip-keypress
```

### 12.4 File Integrity Monitoring

```bash
# Install and configure AIDE
sudo dnf5 install aide

# Initialize database
sudo aide --init
sudo cp /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Run check
sudo aide --check

# Update database after system changes
sudo aide --update
sudo cp /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Automate via cron
sudo tee /etc/cron.d/aide-check <<EOF
0 5 * * * root /usr/sbin/aide --check | mail -s "AIDE Report" admin@example.com
EOF
```

### 12.5 Network Audit

```bash
# Open ports
sudo ss -tlnp
sudo ss -ulnp

# Network connections
sudo ss -tup

# Active listening processes
sudo lsof -i -P -n

# Nmap self-scan
sudo dnf5 install nmap
sudo nmap -sS -O localhost
sudo nmap -sS -p- localhost  # All 65535 ports

# Check for ARP spoofing
sudo arp -a
ip neigh show
```

### 12.6 Audit Log Review

```bash
# Authentication failures
sudo journalctl -u sshd -n 50 --no-pager | grep "Failed password"

# SELinux denials
sudo ausearch -m avc -ts recent

# Package changes (what was installed when)
sudo dnf5 history

# Failed sudo attempts
sudo journalctl -t sudo -n 20

# Service failures
sudo journalctl -p 3 -b  # Priority 3+ errors in boot

# USB device history
journalctl -k -n 100 | grep -i usb

# Successful logins
sudo last
sudo lastb  # Failed logins
```

---

## 13. Incident Response

### 13.1 Incident Classification

| Severity | Definition | Response Time |
|----------|-----------|--------------|
| **Low** | Unauthorized but non-destructive | 24 hours |
| **Medium** | Minor data exposure, non-critical system impact | 4 hours |
| **High** | Data breach, system compromise | 1 hour |
| **Critical** | Full system compromise, lateral movement | Immediate |

### 13.2 Immediate Response Steps

```bash
# 1. DISCONNECT FROM NETWORK
sudo systemctl stop NetworkManager
sudo ip link set dev eth0 down

# 2. PRESERVE EVIDENCE
# Create forensic memory image
sudo dnf5 install volatility3
sudo liime-helper  # (or fmem + volatility)

# Capture running processes
ps auxf > /tmp/ps-$(date +%Y%m%d-%H%M).txt

# Capture network connections
ss -tupna > /tmp/net-$(date +%Y%m%d-%H%M).txt

# Capture loaded kernel modules
lsmod > /tmp/modules-$(date +%Y%m%d-%H%M).txt

# Capture active network connections
tcpdump -i any -w /tmp/packet-capture.pcap

# 3. CHECK FOR COMPROMISE
# Check last logins
sudo last -F
sudo lastlog

# Check for unexpected users
sudo cat /etc/passwd | grep -E '/bin/(bash|sh|zsh)'
sudo cat /etc/sudoers

# Check for new SUID files
sudo find / -perm -4000 -type f -newer /boot/vmlinuz-linux -ls

# Check for suspicious processes
ps auxf | grep -E 'nc|ncat|socat|netcat|perl|python.*-c'

# Check cron jobs
sudo cat /etc/crontab
sudo ls -la /etc/cron.d/
for user in $(cut -f1 -d: /etc/passwd); do sudo crontab -u $user -l; done

# Check SSH authorized keys
cat ~/.ssh/authorized_keys
for user in $(ls /home/); do cat /home/$user/.ssh/authorized_keys 2>/dev/null; done

# Check systemd timers for persistence
systemctl list-timers --all
sudo ls -la /etc/systemd/system/*.service
```

### 13.3 Containment

```bash
# Isolate compromised user
sudo usermod -L <username>             # Lock account
sudo pkill -u <username>               # Kill all processes

# Remove SSH keys
sudo rm -f /home/<user>/.ssh/authorized_keys

# Block IP addresses
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" \
  source address="<IP_ADDRESS>" drop'
sudo firewall-cmd --reload

# Capture system for offline analysis
sudo dd if=/dev/nvme0n1 of=/mnt/forensic/disk.img bs=4M status=progress

# Change all passwords
sudo passwd <user>
# Also change: SSH keys, API tokens, database passwords
```

### 13.4 Recovery

```bash
# Clean installation is safest after compromise
# But if you need to recover:

# 1. Verify integrity of installed packages
sudo rpm -Va > /tmp/rpm-verify.txt
# Look for: S.5...T. (size, MD5, time mismatches)

# 2. Reinstall all packages
sudo dnf5 reinstall '*'

# 3. Check for rootkits
sudo dnf5 install chkrootkit rkhunter
sudo chkrootkit
sudo rkhunter --check

# 4. Rotate all secrets
# - Change passwords
# - Regenerate SSH keys: sudo rm /etc/ssh/*_key && dpkg-reconfigure openssh-server
# - Rotate API tokens
```

### 13.5 Post-Incident

1. **Document** the incident timeline
2. **Identify** root cause
3. **Patch** vulnerabilities
4. **Update** security policies
5. **Notify** affected parties (if data breach)
6. **Review** and improve monitoring

---

## 14. Reporting Vulnerabilities

### 14.1 Responsible Disclosure

Synthex takes security seriously. If you discover a security vulnerability:

**Email: security@getsynthex.org**
**PGP Key:** https://getsynthex.org/security-pgp.asc

### 14.2 What to Include

```
Subject: [Security] Brief description of vulnerability

Body:
- Type of vulnerability (RCE, LPE, XSS, etc.)
- Affected component and version
- Steps to reproduce
- Impact assessment
- Suggested fix (if available)
- Your contact information (optional for anonymous reports)
```

### 14.3 Disclosure Policy

| Phase | Timeline | Description |
|-------|----------|-------------|
| **Report received** | Within 48 hours | Acknowledgment of receipt |
| **Vulnerability assessment** | Within 5 business days | Confirm and classify severity |
| **Patch development** | Varies by severity | Fix developed in private |
| **Coordinated release** | 90 days max | Patch released with advisory |
| **Public disclosure** | After patch release | Full details published |

### 14.4 Bug Bounty

Currently, Synthex does not operate a paid bug bounty program. However, security researchers who report valid vulnerabilities will be:

- Acknowledged in release notes
- Listed on the Synthex Security Hall of Fame
- Considered for maintainer roles if interested

### 14.5 Security Mailing List

Subscribe to security advisories:

```
https://lists.getsynthex.org/mailman/listinfo/synthex-security-announce
```

---

## Appendix A: Security Cheatsheet

```bash
# Quick security checklist

# 1. Update system
sudo dnf5 update

# 2. Check SELinux
getenforce  # Should be "Enforcing"

# 3. Check firewall
sudo firewall-cmd --state
sudo firewall-cmd --list-all

# 4. Secure SSH (if enabled)
# /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes

# 5. Set up automatic updates
# Already configured: dnf5-automatic.timer

# 6. Enable audit logging
sudo systemctl enable --now auditd

# 7. Check for unused services
systemctl list-units --type=service --state=running

# 8. Check for exposed ports
sudo ss -tlnp

# 9. Run security scan
sudo lynis audit system

# 10. Back up your data and LUKS headers
```

## Appendix B: Security Tools Reference

| Tool | Purpose | Install |
|------|---------|---------|
| `lynis` | System security audit | `sudo dnf5 install lynis` |
| `rkhunter` | Rootkit detection | `sudo dnf5 install rkhunter` |
| `chkrootkit` | Rootkit detection | `sudo dnf5 install chkrootkit` |
| `clamav` | Malware scanner | `sudo dnf5 install clamav` |
| `aide` | File integrity monitoring | `sudo dnf5 install aide` |
| `usbguard` | USB device control | `sudo dnf5 install usbguard` |
| `firejail` | Application sandboxing | `sudo dnf5 install firejail` |
| `openscap` | Compliance scanning | `sudo dnf5 install openscap-scanner` |
| `nmap` | Network scanning | `sudo dnf5 install nmap` |
| `tcpdump` | Packet capture | `sudo dnf5 install tcpdump` |
| `wireshark` | Packet analysis (GUI) | `sudo dnf5 install wireshark` |
| `volatility` | Memory forensics | `sudo dnf5 install volatility3` |

## Appendix C: SELinux Boolean Quick Reference

```bash
# Useful SELinux booleans for desktop users
getsebool -a | grep -E '^(user|selinuxuser|httpd|samba|nfs)_' | grep on
sudo setsebool -P selinuxuser_execheap on           # Allow executing heap (some apps)
sudo setsebool -P selinuxuser_execmod on            # Allow execmod (some libraries)
sudo setsebool -P selinuxuser_execstack on          # Allow execstack (some apps)
sudo setsebool -P selinuxuser_ping on               # Allow ping
sudo setsebool -P selinuxuser_use_ssh_chroot on     # Allow SSH chroot
```
