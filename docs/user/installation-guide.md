# Solus Installation Guide

> **Audience:** New users installing Solus Linux for the first time  
> **Last updated:** July 2026  
> **Solus version:** 4.6 "Fortitude"

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Downloading the ISO](#2-downloading-the-iso)
3. [Verification](#3-verification)
4. [Creating Bootable Media](#4-creating-bootable-media)
5. [Step-by-Step Installation (Calamares)](#5-step-by-step-installation-calamares)
6. [Automatic Partitioning](#6-automatic-partitioning)
7. [Custom Partitioning Guide](#7-custom-partitioning-guide)
8. [Encryption Setup](#8-encryption-setup)
9. [Dual-Boot with Windows](#9-dual-boot-with-windows)
10. [Dual-Boot with Other Linux](#10-dual-boot-with-other-linux)
11. [Secure Boot Setup](#11-secure-boot-setup)
12. [First Boot Walkthrough](#12-first-boot-walkthrough)
13. [Post-Installation Steps](#13-post-installation-steps)
14. [Troubleshooting Common Issues](#14-troubleshooting-common-issues)
15. [Driver Installation](#15-driver-installation)
16. [Language/Locale Setup](#16-languagelocale-setup)

---

## 1. System Requirements

### Minimum Requirements
| Component | Requirement |
|-----------|-------------|
| **CPU** | 64-bit (x86_64) dual-core, 2 GHz+ |
| **RAM** | 4 GB |
| **Storage** | 20 GB (SSD recommended) |
| **Graphics** | Any GPU with KMS support (AMD/Intel/NVIDIA) |
| **Display** | 1024×768 resolution |
| **USB port** | For bootable installation media |
| **Internet** | Recommended for updates and driver installation |

### Recommended Requirements
| Component | Recommendation |
|-----------|---------------|
| **CPU** | Quad-core 3 GHz+ or better |
| **RAM** | 8 GB (16 GB for heavy multitasking) |
| **Storage** | 128 GB SSD or NVMe |
| **Graphics** | AMD Radeon RX 5000+ / Intel Arc / NVIDIA RTX 2000+ |
| **Display** | 1920×1080 or higher |
| **Internet** | Broadband connection for updates |

### Supported Architectures
| Architecture | Status | Notes |
|-------------|--------|-------|
| **x86_64 (amd64)** | ✅ Primary | Full support, all editions |
| **aarch64** | ✅ Supported | ARM 64-bit (Raspberry Pi 4/5, Apple M1+) |
| **i686** | ❌ Discontinued | Dropped after Solus 4.4 |

### Supported Installation Media
- USB flash drive (8 GB+ recommended)
- DVD-R/DVD+R (if optical drive available)
- Virtual Machine (VirtualBox, VMware, QEMU/KVM)
- Network boot (PXE, for advanced setups)

---

## 2. Downloading the ISO

### Official Download

Download the latest Solus ISO from the official website:

```
https://getsol.us/download/
```

### ISO Variants

| Edition | Desktop | Best For |
|---------|---------|----------|
| **Solus Plasma** | KDE Plasma 6 | General desktop, gaming, customization |
| **Solus GNOME** | GNOME 46+ | Modern workflow, simplicity |
| **Solus Budgie** | Budgie | Traditional desktop, lightweight |
| **Solus MATE** | MATE | Older hardware, familiar layout |
| **Solus Minimal** | CLI only | Servers, containers, custom setups |

> **Recommendation:** First-time users should download **Solus Plasma** for the most feature-rich experience.

### Direct Download Links
```
https://downloads.getsol.us/iso/Solus-4.6-Plasma.iso
https://downloads.getsol.us/iso/Solus-4.6-GNOME.iso
https://downloads.getsol.us/iso/Solus-4.6-Budgie.iso
https://downloads.getsol.us/iso/Solus-4.6-MATE.iso
```

### BitTorrent
For faster download and to reduce server load, use the torrent files:
```
https://downloads.getsol.us/iso/Solus-4.6-Plasma.iso.torrent
```

---

## 3. Verification

### 3.1 SHA256 Checksum

Always verify the ISO integrity after downloading:

```bash
# Download the checksum file
wget https://downloads.getsol.us/iso/Solus-4.6-Plasma.iso.sha256

# Verify the checksum
sha256sum -c Solus-4.6-Plasma.iso.sha256

# Expected output:
# Solus-4.6-Plasma.iso: OK

# Manual check
sha256sum Solus-4.6-Plasma.iso
# Compare output with the checksum file
```

### 3.2 GPG Signature Verification

For cryptographic verification, use GPG:

```bash
# Download signature file
wget https://downloads.getsol.us/iso/Solus-4.6-Plasma.iso.sig

# Import the Solus signing key
gpg --keyserver keyserver.ubuntu.com --recv-keys 8C2C215F9E3D4F8E

# Or download the key directly
wget https://getsol.us/solus-keyring.gpg
gpg --import solus-keyring.gpg

# Verify the signature
gpg --verify Solus-4.6-Plasma.iso.sig Solus-4.6-Plasma.iso

# Expected output:
# gpg: Good signature from "Solus Project <security@getsol.us>"
# Primary key fingerprint: 4B1E B3B0 1E3E 4C6E A815  8C2C 215F 9E3D 4F8E
```

### 3.3 Windows Verification (PowerShell)

```powershell
# SHA256 in PowerShell
Get-FileHash .\Solus-4.6-Plasma.iso -Algorithm SHA256

# GPG verification (using gpg4win)
gpg --verify Solus-4.6-Plasma.iso.sig Solus-4.6-Plasma.iso
```

---

## 4. Creating Bootable Media

### 4.1 Using `dd` (Linux/macOS)

```bash
# Identify your USB device (BE CAREFUL - this will ERASE the target)
lsblk
# → Find your USB device, e.g., /dev/sdb

# Write the ISO to USB
sudo dd if=Solus-4.6-Plasma.iso of=/dev/sdb bs=4M status=progress oflag=sync

# The command uses:
# - if=:  Input file (the ISO)
# - of=:  Output device (the USB - NOT a partition like /dev/sdb1)
# - bs=:  Block size (4M for faster writes)
# - status=progress: Show progress
# - oflag=sync: Ensure data is written before completion
```

### 4.2 Using Rufus (Windows)

1. Download [Rufus](https://rufus.ie/) (portable version recommended)
2. Insert your USB flash drive
3. Launch Rufus (no installation needed)
4. Configure:
   - **Device:** Select your USB drive
   - **Boot selection:** Select the Solus ISO file
   - **Partition scheme:** GPT (recommended for UEFI)
   - **Target system:** UEFI (non-CSM)
   - **File system:** FAT32 (default)
   - **Cluster size:** 4096 bytes (default)
5. Click **START**
6. If asked about "ISOHybrid" or "DD mode", choose **Write in DD mode** for best compatibility
7. Wait for completion

### 4.3 Using Balena Etcher (Cross-Platform)

1. Download [Balena Etcher](https://www.balena.io/etcher/)
2. Launch Etcher
3. Click **Flash from file** → Select `Solus-4.6-Plasma.iso`
4. Click **Select target** → Choose your USB drive
5. Click **Flash!**
6. Enter password if prompted
7. Wait for validation (Etcher auto-verifies)

### 4.4 Using Ventoy (Cross-Platform)

[Ventoy](https://www.ventoy.net/) allows multiple ISOs on one USB without reformatting:

```bash
# Install Ventoy
wget https://github.com/ventoy/Ventoy/releases/download/v1.0.97/ventoy-1.0.97-linux.tar.gz
tar -xzf ventoy-1.0.97-linux.tar.gz
cd ventoy-1.0.97

# Install to USB (replace /dev/sdb with your USB)
sudo bash Ventoy2Disk.sh -i /dev/sdb

# Simply copy ISO to USB
cp Solus-4.6-Plasma.iso /media/USB/
```

**Windows:**
1. Download and run `Ventoy2Disk.exe`
2. Select your USB drive
3. Click **Install**
4. Copy the ISO file(s) to the USB (no extraction needed)

### 4.5 Making USB Bootable (macOS)

```bash
# Identify USB
diskutil list
# → Find your USB, e.g., /dev/disk2

# Unmount (don't eject)
diskutil unmountDisk /dev/disk2

# Write ISO
sudo dd if=Solus-4.6-Plasma.iso of=/dev/rdisk2 bs=4M status=progress

# Eject when done
sudo diskutil eject /dev/disk2
```

---

## 5. Step-by-Step Installation (Calamares)

Solus uses the **Calamares** system installer, a modern, user-friendly graphical installer.

### 5.1 Booting from the Install Media

1. Insert the bootable USB into your computer
2. Restart and enter the **boot menu**:
   - **Dell/Lenovo:** F12
   - **HP:** F9
   - **ASUS:** F8 or Esc
   - **Acer:** F12
   - **Apple Mac:** Hold Option/Alt
   - **Custom builds:** F11 or Del
3. Select your USB drive from the boot menu
4. You'll see the Solus GRUB boot menu:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              Solus Linux 4.6 "Fortitude"            │
│                                                     │
│  ┌─────────────────────────────────────────────────┐│
│  │ > Start Solus                                   ││
│  │   Start Solus (Safe Graphics)                   ││
│  │   Test this media & start Solus                 ││
│  │   Boot from local drive                         ││
│  │                                                 ││
│  │   ─────────────────────────────────────────      ││
│  │                                                 ││
│  │   Memory Test (memtest86+)                      ││
│  │   Hardware Detection                            ││
│  └─────────────────────────────────────────────────┘│
│                                                     │
│  Use ↑↓ to select, Enter to boot, 'e' to edit       │
└─────────────────────────────────────────────────────┘
```

5. Select **Start Solus** (or **Safe Graphics** if you have NVIDIA hardware)

### 5.2 Live Desktop

After booting, you'll see the Solus live desktop:

```
┌────────────────────────────────────────────────────────────────┐
│  ☰  Solus Installer  │  Terminal  │  Firefox  │  12:45  🔋🔊 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│          ┌──────────────────────────────────────┐              │
│          │                                      │              │
│          │      Welcome to Solus Linux!         │              │
│          │                                      │              │
│          │   You are running the live system.   │              │
│          │   To install Solus permanently,      │              │
│          │   click the "Install Solus" icon     │              │
│          │   on the desktop.                    │              │
│          │                                      │              │
│          │   [ Install Solus ]                  │              │
│          │                                      │              │
│          └──────────────────────────────────────┘              │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ☰ Menu │ 📁 Files │ 🌐 Browser │ ⚙ Settings │ 🔌  │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

Double-click **Install Solus** to begin.

### 5.3 Welcome Screen

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Solus Installer                       │  │
│  │                                                          │  │
│  │   Welcome to the Solus installation wizard!              │  │
│  │                                                          │  │
│  │   This program will guide you through setting up         │  │
│  │   Solus Linux on your computer.                          │  │
│  │                                                          │  │
│  │   [✓] Install third-party software for graphics and      │  │
│  │       Wi-Fi hardware                                     │  │
│  │                                                          │  │
│  │   ──────────────────────────────────────────────         │  │
│  │                                                          │  │
│  │   Language: [ English ▼ ]                                │  │
│  │                                                          │  │
│  │           [ Cancel ]    [ Next → ]                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Select your language
- Check the box for third-party software if desired (recommended)
- Click **Next**

### 5.4 Location / Time Zone

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Location                             │  │
│  │                                                          │  │
│  │            ┌──────────────────────────┐                  │  │
│  │            │    World Map (clickable)  │                 │  │
│  │            │                          │                  │  │
│  │            │      ● (your location)   │                  │  │
│  │            └──────────────────────────┘                  │  │
│  │                                                          │  │
│  │   Region: [ Americas    ▼ ]   Zone: [ New_York    ▼ ]   │  │
│  │                                                          │  │
│  │   [✓] System uses UTC clock                              │  │
│  │                                                          │  │
│  │           [ Back ]                    [ Next → ]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Click your location on the map, or select Region/Zone from dropdowns
- Keep "System uses UTC clock" checked (recommended for dual-boot)
- Click **Next**

### 5.5 Keyboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Keyboard                              │  │
│  │                                                          │  │
│  │   Layout: [ English (US)         ▼ ]                     │  │
│  │   Variant: [ English (US - default) ▼ ]                  │  │
│  │                                                          │  │
│  │   ┌─────────────────────────────────────────────┐       │  │
│  │   │   ~ │ 1 │ 2 │ 3 │ 4 │ 5 │ 6 │ 7 │ 8 │ 9... │       │  │
│  │   │ Tab │ q │ w │ e │ r │ t │ y │ u │ i │ o... │       │  │
│  │   │ Caps │ a │ s │ d │ f │ g │ h │ j │ k │ l...│       │  │
│  │   └─────────────────────────────────────────────┘       │  │
│  │                                                          │  │
│  │   Type here to test your keyboard: ______________        │  │
│  │                                                          │  │
│  │           [ Back ]                    [ Next → ]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Select your keyboard layout
- Type in the test box to verify keys map correctly
- Click **Next**

### 5.6 Partitioning (See Sections 6 & 7 for details)

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Partitioning                          │  │
│  │                                                          │  │
│  │   ┌──────────────────────────────────────────────────┐  │  │
│  │   │ Device           Size   Used   Type               │  │  │
│  │   │ ─────────────────────────────────────────────    │  │  │
│  │   │ /dev/nvme0n1                                     │  │  │
│  │   │   ├─ nvme0n1p1   512M   ESP    EFI System        │  │  │
│  │   │   ├─ nvme0n1p2    16G   ?      Windows           │  │  │
│  │   │   └─ nvme0n1p3    50G   ?      Free Space        │  │  │
│  │   │ /dev/sda                                          │  │  │
│  │   │   └─ sda1        1.8T   ?      Linux LUKS        │  │  │
│  │   └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │   ○ Erase disk (automatic)                               │  │
│  │   ○ Replace a partition                                 │  │
│  │   ● Manual partitioning                                 │  │
│  │                                                          │  │
│  │           [ Back ]                    [ Next → ]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Choose your partitioning method:**
- **Erase disk:** Automatic for single-OS installations (see Section 6)
- **Replace a partition:** Choose an existing partition to overwrite
- **Manual:** Full control (advanced - see Section 7)

### 5.7 User Creation

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   User Details                          │  │
│  │                                                          │  │
│  │   What is your name?                                     │  │
│  │   [ John Smith                          ]                │  │
│  │                                                          │  │
│  │   What name do you want to use to log in?                 │  │
│  │   [ jsmith                              ]                │  │
│  │                                                          │  │
│  │   What is the name of this computer?                     │  │
│  │   [ solus-pc                            ]                │  │
│  │                                                          │  │
│  │   Choose a password (strongly recommended):               │  │
│  │   [ ********                            ]                 │  │
│  │   Confirm password:                                      │  │
│  │   [ ********                            ]                 │  │
│  │                                                          │  │
│  │   Password strength: ●●●●●●●○○○                          │  │
│  │                                                          │  │
│  │   [✓] Require password to log in                         │  │
│  │   [ ] Encrypt home folder                                │  │
│  │                                                          │  │
│  │           [ Back ]                    [ Next → ]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Enter your full name
- Choose a username (lowercase, no spaces)
- Set a hostname for your computer
- Choose a **strong password** (minimum 8 chars, mix of types)
- Decide if password is required for login

### 5.8 Summary / Confirm

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Ready to Install                       │  │
│  │                                                          │  │
│  │   ┌────────────────────────────────────────────────────┐ │  │
│  │   │  Installation Summary                              │ │  │
│  │   │                                                    │ │  │
│  │   │  Location:     Americas/New_York                   │ │  │
│  │   │  Keyboard:     English (US)                        │ │  │
│  │   │  Partitions:   Manual partitioning                  │ │  │
│  │   │  ─────────────────────────────────────────────    │ │  │
│  │   │  /dev/nvme0n1p1 → /boot/efi (EFI System) 512M    │ │  │
│  │   │  /dev/nvme0n1p4 → /boot (ext4)             1G    │ │  │
│  │   │  /dev/nvme0n1p5 → /    (btrfs) LUKS       50G   │ │  │
│  │   │  /dev/vda1      → swap (swap)              8G    │ │  │
│  │   │                                                    │ │  │
│  │   │  User:         John Smith (jsmith)                 │ │  │
│  │   │  Hostname:     solus-pc                            │ │  │
│  │   └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │   ⚠ Once you click Install, the partition layout        │  │
│  │     will be written to disk. This cannot be undone.      │  │
│  │                                                          │  │
│  │           [ Cancel ]              [ Install ]           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Review your settings carefully
- Click **Install** to begin

### 5.9 Installation Progress

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Installing Solus                       │  │
│  │                                                          │  │
│  │   ┌──────────────────────────────────────────────────┐  │  │
│  │   │  ███████████████████████████████████░░░░░░░░░░░  │  │  │
│  │   │              68% complete                         │  │  │
│  │   └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │   Installing packages...                                 │  │
│  │   ✓ Preparing partition                                  │  │
│  │   ✓ Creating filesystem                                  │  │
│  │   ✓ Mounted partitions                                   │  │
│  │   ✓ Installing base system                               │  │
│  │   ● Installing desktop environment                       │  │
│  │   ○ Configuring system                                   │  │
│  │   ○ Installing bootloader                                │  │
│  │   ○ Finishing setup                                      │  │
│  │                                                          │  │
│  │   ─────────────────────────────────────                  │  │
│  │                                                          │  │
│  │   [x] Install QEMU guest agent (for VMs)                 │  │
│  │                                                          │  │
│  │   [ Pause ]                                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Installation takes **5–15 minutes** depending on hardware and internet speed
- You can pause if needed

### 5.10 Completion

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   All Done!                              │  │
│  │                                                          │  │
│  │   Installation complete!                                 │  │
│  │                                                          │  │
│  │   You may now restart your computer.                     │  │
│  │                                                          │  │
│  │   Don't forget to remove the installation medium         │  │
│  │   when the system restarts.                              │  │
│  │                                                          │  │
│  │   [✓] Restart now                                        │  │
│  │                                                          │  │
│  │           [ Restart ]          [ Done ]                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

- Click **Restart Now**
- Remove the USB drive when prompted
- The system will boot into your new Solus installation

---

## 6. Automatic Partitioning

### 6.1 How Automatic Partitioning Works

When you select **Erase disk** in the partitioning step, Calamares automatically creates:

```
┌────────────────────────────────────────────────────────────────┐
│                   Automatic Layout (SSD)                       │
│                                                                │
│   ┌──────────────┬──────────────┬──────────────────────────┐   │
│   │  ESP (FAT32)  │  /boot       │  BTRFS (LUKS optional)  │   │
│   │  512 MiB      │  ext4        │  Rest of disk            │   │
│   │  /boot/efi    │  1024 MiB    │  /                       │   │
│   │               │              │                          │   │
│   │  Bootloader   │  Staging     │  • @ (root)              │   │
│   │  & kernels    │  & extra     │  • @home                 │   │
│   │               │  kernels     │  • @snapshots            │   │
│   │               │              │  • @var                  │   │
│   └──────────────┴──────────────┴──────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Automatic Partitioning Options

| Option | Description | When to use |
|--------|-------------|-------------|
| **Erase disk** | Complete disk overwrite | First installation, repurposing disk |
| **Replace partition** | Overwrite existing partition | Dual-boot with unused partition |
| **Install alongside** | Shrink existing partition | Dual-boot (if available in Calamares) |

### 6.3 Encryption in Automatic Mode

If you check "Encrypt system" in automatic mode:

1. LUKS2 container is created on the BTRFS partition
2. You're prompted for an encryption passphrase
3. The system will prompt for the passphrase at boot
4. Optionally: TPM2 auto-unlock can be configured post-install

---

## 7. Custom Partitioning Guide

### 7.1 Partition Layout Examples

#### Minimal Desktop (20–40 GB)
```
Size       Type        Mount      Filesystem
──────────────────────────────────────────────
512 MiB    EFI System  /boot/efi  FAT32
1 GiB      Linux boot  /boot      ext4
Rest       Linux root  /          BTRFS
```

#### Standard Desktop (40–120 GB)
```
Size       Type        Mount      Filesystem
──────────────────────────────────────────────
512 MiB    EFI System  /boot/efi  FAT32
1 GiB      Linux boot  /boot      ext4
Rest       Linux root  /          BTRFS (LUKS optional)
```

#### Power User / Developer (120 GB+)
```
Size       Type        Mount      Filesystem
──────────────────────────────────────────────
512 MiB    EFI System  /boot/efi  FAT32
1 GiB      Linux boot  /boot      ext4
40-80 GiB  Linux root  /          BTRFS (with LUKS)
Rest       Linux home  /home      BTRFS (or XFS/ext4)
8-32 GiB   Linux swap  [swap]     swap
```

#### Dual-Boot (shared with Windows)
```
Size       Type        Mount      Filesystem
──────────────────────────────────────────────
512 MiB    EFI System  /boot/efi  FAT32 (shared with Windows)
16-80 GiB  Windows     C:\        NTFS (existing)
512 MiB    Linux boot  /boot      ext4
60-100 GiB Linux root  /          BTRFS
8-32 GiB   Linux swap  [swap]     swap
```

### 7.2 Manual Partitioning Steps

1. In Calamares, select **Manual partitioning**
2. If needed, create a new partition table:
   - **GPT** for UEFI systems (recommended for all modern systems)
   - **MBR** for legacy BIOS (only if you must)
3. Create partitions in order:

```bash
# Example: For a 256 GB NVMe drive

# Partition 1: EFI System Partition (ESP)
New partition table → GPT
Add partition:
  Size: 512 MiB
  Type: EFI System Partition
  Filesystem: FAT32
  Mount: /boot/efi

# Partition 2: Boot
Add partition:
  Size: 1024 MiB
  Type: Linux extended boot
  Filesystem: ext4
  Mount: /boot

# Partition 3: Root (BTRFS)
Add partition:
  Size: 100 GiB
  Type: Linux filesystem
  Filesystem: BTRFS
  Mount: /
  Encrypt: ✓ (recommended)

# Partition 4: Home (optional)
Add partition:
  Size: remaining space
  Type: Linux filesystem
  Filesystem: BTRFS
  Mount: /home

# Partition 5: Swap (optional - ZRAM is used by default)
Add partition:
  Size: 8 GiB (or RAM size for hibernation)
  Type: Linux swap
  Filesystem: swap
```

### 7.3 BTRFS Subvolume Creation (Post-Install)

After installation, create the recommended subvolume layout:

```bash
# If you used a single BTRFS partition for /
sudo mount /dev/nvme0n1p3 /mnt
cd /mnt

# Create subvolumes
sudo btrfs subvolume create @
sudo btrfs subvolume create @home
sudo btrfs subvolume create @var
sudo btrfs subvolume create @snapshots
sudo btrfs subvolume create @cache
sudo btrfs subvolume create @log

# Set up for snapper
sudo btrfs subvolume create /.snapshots
```

---

## 8. Encryption Setup

### 8.1 LUKS2 Encryption During Installation

1. In the partitioning step, select **Manual partitioning**
2. For the root partition (or any data partition), check **Encrypt**
3. Set a strong passphrase:

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Encryption Passphrase                   │  │
│  │                                                          │  │
│  │   You have selected to encrypt partition:                │  │
│  │   /dev/nvme0n1p3 (Root)                                 │  │
│  │                                                          │  │
│  │   Enter a strong passphrase:                             │  │
│  │   [ ****************************       ]                 │  │
│  │                                                          │  │
│  │   Confirm passphrase:                                    │  │
│  │   [ ****************************       ]                 │  │
│  │                                                          │  │
│  │   ⚠ This passphrase will be required EVERY boot!        │  │
│  │     Store it safely.                                     │  │
│  │                                                          │  │
│  │   Passphrase strength: ●●●●●●●●●○                       │  │
│  │                                                          │  │
│  │           [ Cancel ]          [ Set Passphrase ]         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 8.2 Post-Install LUKS Setup

If you didn't encrypt during installation, you can encrypt after:

> ⚠ **Warning:** Encrypting after installation requires significant disk operations. Backup first!

```bash
# Backup critical data
sudo snapper -c root create -d "before-encryption"

# Boot from live USB, then:
sudo cryptsetup reencrypt --encrypt --type luks2 /dev/nvme0n1p3 \
  --cipher aes-xts-plain64 --key-size 512 \
  --pbkdf argon2id --pbkdf-memory 256000

# This re-encrypts in-place (online reencryption)
```

### 8.3 TPM2 Auto-Unlock (Optional)

For unattended boot with encryption:

```bash
# Enroll TPM2 to automatically unlock LUKS
sudo systemd-cryptenroll --tpm2-device=auto \
  --tpm2-pcrs=0+7 \
  /dev/nvme0n1p3

# Update crypttab for TPM unlock
# /etc/crypttab
luks-<UUID> UUID=<UUID> /dev/null tpm2-device=auto,discard

# Update initramfs
sudo dracut --force
```

### 8.4 FIDO2/Token Unlock

```bash
# Using FIDO2 hardware token (YubiKey, SoloKey, etc.)
sudo systemd-cryptenroll --fido2-device=auto \
  --fido2-with-client-pin=yes \
  --fido2-with-user-verification=no \
  /dev/nvme0n1p3
```

### 8.5 Recovery Key

Always create a recovery key:

```bash
# Generate a recovery key
sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3

# View recovery key (write this down and store securely!)
sudo systemd-cryptenroll --recovery-key /dev/nvme0n1p3 --show
```

---

## 9. Dual-Boot with Windows

### 9.1 Pre-Installation (Windows Side)

1. **Disable Fast Startup** in Windows:
   - Control Panel → Power Options → Choose what power buttons do
   - Click "Change settings that are currently unavailable"
   - Uncheck "Turn on fast startup (recommended)"
   - Save changes
   - *Fast Startup can prevent Linux from accessing NTFS partitions*

2. **Disable Secure Boot** (temporarily, can re-enable later):
   - Reboot → Enter UEFI/BIOS
   - Find Secure Boot setting → Disable
   - Save and exit

3. **Shrink Windows Partition**:
   ```
   Disks Management:
   1. Win+X → Disk Management
   2. Right-click C: → Shrink Volume
   3. Enter amount to shrink (at least 60 GB = 61440 MB)
   4. Click Shrink
   ```

4. **Disable bitlocker** (if enabled):
   - Control Panel → BitLocker Drive Encryption → Suspend Protection

### 9.2 Installation

1. Boot from Solus USB
2. In Calamares partitioning:
   - Keep the Windows partitions intact
   - Use the **unallocated space** for Solus
   - The existing EFI partition can be shared
3. Continue with normal installation

### 9.3 GRUB Configuration for Windows Dual-Boot

Solus GRUB should auto-detect Windows. If not:

```bash
# After installation, run:
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
# This should find "Windows Boot Manager"
```

### 9.4 Time Sync Fix

Windows uses local time; Linux uses UTC. Fix the time conflict:

```bash
# Make Linux use local time (matching Windows)
sudo timedatectl set-local-rtc 1

# Verify
timedatectl | grep "RTC in local TZ"
# → RTC in local TZ: yes
```

### 9.5 Accessing Windows Files

```bash
# Install NTFS support
sudo dnf5 install ntfs-3g

# Mount Windows partition
sudo mount /dev/nvme0n1p2 /mnt/windows -t ntfs-3g
# (replace /dev/nvme0n1p2 with your Windows partition)

# Or use KDE Dolphin → Click Windows drive in sidebar
```

---

## 10. Dual-Boot with Other Linux

### 10.1 Pre-Installation

```bash
# From your current Linux, identify partitions
lsblk -f
# Note which partitions belong to which distro

# Create unallocated space (if needed)
# Use GParted or your distro's partition manager
sudo gparted
```

### 10.2 Sharing Home Partition (Advanced)

You can share a `/home` partition across distros:

> ⚠ Only share `/home` if both distros use the same UID/GID for your user

```bash
# Ensure UID/GID matches
id jsmith
# → uid=1000(jsmith) gid=1000(jsmith)

# On both distros, user ID must be 1000
```

### 10.3 GRUB Management

Solus will install its own GRUB as the primary bootloader. Other distros will be detected automatically.

```bash
# If another distro's GRUB takes over:
# 1. Boot into Solus
# 2. Regenerate GRUB config
sudo grub2-mkconfig -o /boot/grub2/grub.cfg

# 3. Reinstall to ESP
sudo grub2-install --target=x86_64-efi --efi-directory=/boot/efi
```

### 10.4 BTRFS Across Distros

If both distros use BTRFS:

```bash
# Mount the shared BTRFS volume
sudo mount /dev/nvme0n1p3 /mnt

# You'll see subvolumes from both distros
ls /mnt
# @solus-root
# @solus-home
# @ubuntu-root
# @ubuntu-home
# @snapshots
```

---

## 11. Secure Boot Setup

### 11.1 Understanding Secure Boot on Solus

Solus supports Secure Boot through:
1. **Shim** - First-stage bootloader signed by Microsoft
2. **GRUB** - Signed with Machine Owner Key (MOK)
3. **Kernel** - Signed with MOK

### 11.2 Enrolling MOK During Installation

If Secure Boot is enabled during installation:

1. Calamares will detect Secure Boot and generate a MOK key
2. You'll be prompted to set a MOK enrollment password:

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Secure Boot / MOK Enrollment                │  │
│  │                                                          │  │
│  │   Secure Boot is enabled. Solus uses Shim + MOK          │  │
│  │   for compatibility.                                     │  │
│  │                                                          │  │
│  │   A Machine Owner Key (MOK) will be generated.          │  │
│  │   You will need to enroll it after reboot.               │  │
│  │                                                          │  │
│  │   Set a MOK enrollment password:                         │  │
│  │   [ ****************                                    ] │  │
│  │   Confirm:                                               │  │
│  │   [ ****************                                    ] │  │
│  │                                                          │  │
│  │   ⚠ You will need this password AFTER reboot to          │  │
│  │     complete enrollment.                                 │  │
│  │                                                          │  │
│  │           [ Skip ]          [ Set Password ]             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

3. After reboot, MokManager will prompt for enrollment:

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Forbidden: Shim UEFI Key Management                           │
│                                                                 │
│   Select an option:                                             │
│                                                                 │
│   [Enroll key from disk]                                        │
│   [Enroll key from MOK]                                         │
│   [Continue boot]                                               │
│                                                                 │
│   → Select "Enroll key from MOK"                                │
│                                                                 │
│   Enter password you set during installation                    │
│                                                                 │
│   [Yes] - Enroll the key(s)                                     │
│   [No]  - Continue without enrolling                            │
└────────────────────────────────────────────────────────────────┘
```

### 11.3 Post-Install Secure Boot Management

```bash
# Check Secure Boot status
mokutil --sb-state
# → SecureBoot enabled

# List enrolled MOK keys
mokutil --list-enrolled

# Enroll a new key
sudo mokutil --import new-key.der
# → Set password, reboot, use MokManager

# Remove a key
sudo mokutil --delete
# → Interactive, removes selected key

# Reset MOK list (if boot issues)
sudo mokutil --reset
```

### 11.4 Signing Custom Kernels

```bash
# Sign a custom kernel for Secure Boot
sudo pesign -n /etc/pki/pesign -c "Solus Kernel Signing Key" \
  -i /boot/vmlinuz-linux -o /boot/vmlinuz-linux.signed -s

# Or using sbsign
sudo sbsign --key /path/to/MOK.key --cert /path/to/MOK.pem \
  --output /boot/vmlinuz-linux /boot/vmlinuz-linux
```

---

## 12. First Boot Walkthrough

### 12.1 GRUB Menu

After installation, your system boots to GRUB:

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              Solus Linux 4.6 "Fortitude"            │
│                                                     │
│  > Solus Linux (default)                            │
│    Advanced options for Solus Linux                 │
│    Windows Boot Manager (if dual-boot)              │
│    System settings                                  │
│    Firmware setup                                   │
│                                                     │
│                                                     │
│  Use ↑↓ to select, Enter to boot                    │
│                                                     │
│  Press 'e' to edit kernel command line              │
│  Press 'c' for GRUB console                         │
└─────────────────────────────────────────────────────┘
```

Press Enter or wait for auto-boot.

### 12.2 First Boot Sequence

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        Solus Linux                             │
│                                                                 │
│   ████████████████████████████████████████████████░░░░  85%    │
│                                                                 │
│   Starting user manager...                                      │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 12.3 SDDM Login Screen

```
┌────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     ┌─────────────────┐                         │
│                     │   ●  ○  ○       │                         │
│                     │                 │                         │
│                     │    jsmith        │                         │
│                     │                 │                         │
│                     │  [ ********   ] │                         │
│                     │                 │                         │
│                     │   [ Log In ]    │                         │
│                     │                 │                         │
│                     │  Session:       │                         │
│                     │  Plasma (Wayl..│  ▼                      │
│                     │                 │                         │
│                     │  ○ Plasma (Wayland)                       │
│                     │  ○ Plasma (X11)                           │
│                     └─────────────────┘                         │
│                                                                 │
│   Solus Linux 4.6 "Fortitude"                                   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

- Select your user
- Enter password
- Choose **Plasma (Wayland)** (default)
- Click **Log In**

### 12.4 Welcome Wizard

On first login, the Solus Welcome Wizard appears:

```
┌────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               Welcome to Solus Linux!                    │  │
│  │                                                          │  │
│  │   ┌──────────────────────────────────────────────────┐  │  │
│  │   │     🎉 Thank you for choosing Solus!              │  │  │
│  │   │                                                  │  │  │
│  │   │   Let's get your system set up.                   │  │  │
│  │   │                                                  │  │  │
│  │   │   [1] Connect to the internet                    │  │  │
│  │   │   [2] Set up online accounts                     │  │  │
│  │   │   [3] Personalize your desktop                   │  │  │
│  │   │   [4] Install drivers                            │  │  │
│  │   │   [5] Install recommended apps                   │  │  │
│  │   │                                                  │  │  │
│  │   └──────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │   [ Skip All ]                     [ Get Started → ]    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 12.5 Plasma Desktop First Look

```
┌────────────────────────────────────────────────────────────────┐
│  ☰ App Menu │ 📁 Dolphin │ 🌐 Firefox │ ⚙ Settings │  12:45  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│          ┌──────────────────────────────────────┐              │
│          │                                      │              │
│          │         ☀  Good afternoon            │              │
│          │                                      │              │
│          │    Welcome to your new desktop!      │              │
│          │                                      │              │
│          │   • Press ☰ for applications        │              │
│          │   • Right-click desktop to customize │              │
│          │   • Click here to add widgets        │              │
│          │                                      │              │
│          │              [ Got it! ]             │              │
│          │                                      │              │
│          └──────────────────────────────────────┘              │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  ☰ │ 🌐 │ 📁 │ 📧 │ 📦 │ 🎮 │ 🔧 │ 🖨 │ 📷 │ 🔊  │    │
│  └────────────────────────────────────────────────────────┘    │
│  Task Manager                       System Tray                 │
└────────────────────────────────────────────────────────────────┘
```

---

## 13. Post-Installation Steps

### 13.1 Initial System Update

```bash
# Update all packages
sudo dnf5 update

# Check for firmware updates
sudo fwupdmgr refresh
sudo fwupdmgr get-updates
sudo fwupdmgr update
```

### 13.2 Install Essential Software

```bash
# Codecs for multimedia
sudo dnf5 install ffmpegthumbs ffmpeg

# Fonts
sudo dnf5 install google-noto-fonts-common \
  noto-fonts-emoji \
  liberation-fonts \
  jetbrains-mono-fonts

# Archive tools
sudo dnf5 install ark unrar p7zip

# Development basics
sudo dnf5 install git curl wget

# Printing
sudo dnf5 install cups system-config-printer

# Bluetooth
sudo dnf5 install bluez bluez-utils
```

### 13.3 Enable Services

```bash
# Enable firewall
sudo systemctl enable --now firewalld

# Enable printing
sudo systemctl enable --now cups

# Enable Bluetooth
sudo systemctl enable --now bluetooth

# Enable SSH (optional)
sudo systemctl enable --now sshd
```

### 13.4 Configure Software Repositories

```bash
# Enable additional repos
sudo dnf5 config-manager --set-enabled solus-nonfree
sudo dnf5 config-manager --set-enabled solus-backports

# Add Flathub for Flatpak apps
flatpak remote-add --if-not-exists flathub \
  https://flathub.org/repo/flathub.flatpakrepo
```

### 13.5 Create Snapshots

```bash
# Install snapper
sudo dnf5 install snapper snapper-zypp-plugin

# Configure root snapshots
sudo snapper -c root create-config /

# Create initial snapshot
sudo snapper -c root create -d "fresh-install"

# Verify
sudo snapper -c root list
```

### 13.6 Setup Automatic Snapshots

```bash
# Snapper configuration at /etc/snapper/configs/root
# Recommended settings:
sudo tee /etc/snapper/configs/root <<EOF
ALLOW_GROUPS="wheel"
TIMELINE_CREATE="yes"
TIMELINE_CLEANUP="yes"
TIMELINE_MIN_AGE="1800"
TIMELINE_LIMIT_HOURLY="5"
TIMELINE_LIMIT_DAILY="7"
TIMELINE_LIMIT_WEEKLY="0"
TIMELINE_LIMIT_MONTHLY="0"
TIMELINE_LIMIT_YEARLY="0"
NUMBER_LIMIT="10"
NUMBER_LIMIT_IMPORTANT="10"
EOF
```

---

## 14. Troubleshooting Common Issues

### 14.1 Installation Issues

#### "No root device found" / Boot Failure
```
Symptom: System boots to initramfs shell or kernel panic
Solution:
  - Check if disk encryption was set up correctly
  - At GRUB, press 'e' and verify root=UUID matches your partition
  - Boot from live USB and rebuild initramfs:
    sudo mount /dev/nvme0n1p5 /mnt
    sudo chroot /mnt
    sudo dracut --force
    exit
```

#### GRUB Installation Failed
```
Symptom: Installer reports bootloader installation failed
Solution:
  1. Check if ESP partition is FAT32 and flagged as EFI System
  2. Manually install GRUB from live USB:
    sudo mount /dev/nvme0n1p1 /boot/efi
    sudo mount /dev/nvme0n1p4 /boot
    sudo mount /dev/nvme0n1p5 /mnt
    sudo grub2-install --target=x86_64-efi \
      --efi-directory=/boot/efi --bootloader-id=Solus
    sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

#### Black Screen / No Display
```
Symptom: Screen goes black after booting installer
Solution:
  1. Use "Safe Graphics" option from GRUB
  2. Add nomodeset to kernel parameters (press 'e' at GRUB):
    linux /vmlinuz-linux ... nomodeset
  3. For NVIDIA GPUs, add:
    linux /vmlinuz-linux ... nouveau.modeset=0
```

#### "Out of Memory" During Installation
```
Symptom: Installer crashes with OOM
Solution:
  1. Close other applications (Firefox, etc.)
  2. Add swap before installing (even if temporary):
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
  3. Use the "Minimal" ISO variant
```

#### USB Boot Hangs at GRUB
```
Symptom: USB stick shows GRUB menu but hangs on "Start Solus"
Solution:
  1. Re-write USB with DD mode (not ISO mode)
  2. Try a different USB port (USB 2.0 often more compatible)
  3. Verify ISO checksum (corrupted download)
  4. Try Ventoy instead of direct write
```

### 14.2 Hardware Issues

#### NVIDIA GPU Not Working
See [Section 15.3 - NVIDIA Driver Installation](#153-nvidia-driver)

#### Wi-Fi Not Detected
```bash
# Check Wi-Fi hardware
lspci -k | grep -i network
rfkill list

# Install firmware (if needed)
sudo dnf5 install linux-firmware

# For Broadcom chipsets:
sudo dnf5 install broadcom-wl

# Restart NetworkManager
sudo systemctl restart NetworkManager
```

#### Touchpad Not Working
```bash
# Check touchpad detection
xinput list (X11)
libinput list-devices

# Install synaptics (if needed)
sudo dnf5 install xorg-x11-drv-synaptics

# KDE settings: System Settings → Input Devices → Touchpad
```

#### Sound Not Working
```bash
# Check ALSA detection
aplay -l

# Restart PipeWire
systemctl --user restart pipewire pipewire-pulse wireplumber

# Check if muted
pactl set-sink-mute @DEFAULT_SINK@ 0
pactl set-sink-volume @DEFAULT_SINK@ 100%

# Install additional codecs
sudo dnf5 install sof-firmware # For Intel SOF DSP
```

### 14.3 Boot Issues

#### Kernel Panic
```
Symptom: "Kernel panic - not syncing: VFS: Unable to mount root fs"
Solution:
  1. Boot from live USB
  2. Chroot into system
  3. Rebuild initramfs:
    sudo chroot /mnt dracut --force
  4. Check /etc/fstab for correct UUIDs
  5. Regenerate GRUB config:
    sudo chroot /mnt grub2-mkconfig -o /boot/grub2/grub.cfg
```

#### Emergency Mode
```bash
# If boot drops to emergency mode:
journalctl -xb -p 3  # Show errors
systemctl default    # Try to continue booting

# Common causes:
# 1. Bad /etc/fstab entry → comment out or fix
# 2. Filesystem corruption → fsck
# 3. Failed systemd service → systemctl disable
```

#### Filesystem Corruption
```bash
# Boot from live USB
# Identify your root partition
lsblk -f

# Check and repair BTRFS
sudo btrfs check /dev/nvme0n1p5
sudo btrfs scrub start /mnt

# For ext4
sudo fsck.ext4 -f /dev/nvme0n1p4
```

---

## 15. Driver Installation

### 15.1 Graphics Drivers

#### AMD (Open Source - Included)

AMD GPUs work out of the box with the open-source `amdgpu` kernel driver and Mesa.

```bash
# Check your GPU
lspci -k | grep -A2 VGA

# Install Vulkan support
sudo dnf5 install vulkan-loader vulkan-tools

# For AMD ROCm (compute/ML)
sudo dnf5 install rocm-hip rocm-smi
```

#### Intel (Open Source - Included)

```bash
# Install Intel compute runtime
sudo dnf5 install intel-compute-runtime

# For media encoding/decoding
sudo dnf5 install intel-media-driver
```

#### NVIDIA (Proprietary Driver)

```bash
# Step 1: Check your GPU model
lspci -k | grep -i nvidia

# Step 2: Install NVIDIA driver
sudo dnf5 install nvidia-driver nvidia-driver-cuda

# Step 3: Enable NVIDIA DRM modesetting
sudo tee /etc/modprobe.d/nvidia.conf <<EOF
options nvidia-drm modeset=1
options nvidia NVreg_UsePageAttributeTable=1
EOF

# Step 4: Regenerate initramfs
sudo dracut --force

# Step 5: Verify installation
nvidia-smi

# For Wayland support (NVIDIA):
# Ensure nvidia-drm.modeset=1 is set
# Install nvidia-vaapi-driver for video acceleration
```

### 15.2 Wi-Fi / Bluetooth Drivers

```bash
# Broadcom Wi-Fi
sudo dnf5 install broadcom-wl kernel-devel
sudo dkms install broadcom-sta

# Realtek Wi-Fi (RTW88/RTW89)
sudo dnf5 install rtw88-firmware

# Intel Wi-Fi (works out of box)
sudo dnf5 install iwlwifi-firmware

# Qualcomm Atheros
sudo dnf5 install ath10k-firmware ath11k-firmware
```

### 15.3 Printer Drivers

```bash
# CUPS + common printer drivers
sudo dnf5 install cups cups-filters \
  gutenprint hplip \
  system-config-printer

# Brother printers
# Download from https://support.brother.com

# Enable and start CUPS
sudo systemctl enable --now cups
```

### 15.4 Audio Drivers

```bash
# ALSA firmware (for modern Intel/AMD audio)
sudo dnf5 install sof-firmware alsa-firmware

# PipeWire codecs
sudo dnf5 install pipewire-codec-aptx pipewire-codec-ldac
```

### 15.5 Firmware Updates

```bash
# LVFS (Linux Vendor Firmware Service)
sudo dnf5 install fwupd fwupd-efi

# Check for updates
sudo fwupdmgr refresh
sudo fwupdmgr get-updates
sudo fwupdmgr update

# Check if your hardware is supported
fwupdmgr get-devices
```

---

## 16. Language/Locale Setup

### 16.1 During Installation

Select your language in the first step of the Calamares installer. This sets:
- System language
- Locale formats (date, time, currency)
- Default keyboard layout
- Regional settings

### 16.2 Post-Installation Language Change

```bash
# Check current locale
locale
# LANG=en_US.UTF-8

# List available locales
locale -a

# Generate additional locale
sudo locale-gen de_DE.UTF-8

# Set system locale
sudo localectl set-locale LANG=de_DE.UTF-8

# Apply to current session (log out and back in for full effect)
```

### 16.3 Input Methods

For CJK (Chinese, Japanese, Korean) input:

```bash
# Install IBus
sudo dnf5 install ibus ibus-qt \
  ibus-hangul   # Korean
  ibus-libpinyin # Chinese
  ibus-mozc      # Japanese (Mozc)
  ibus-unikey    # Vietnamese

# IBus setup
ibus-setup

# Add input sources in KDE:
# System Settings → Input Devices → Virtual Keyboard → IBus
```

### 16.4 Keyboard Layout Switching

```bash
# Via KDE System Settings:
# System Settings → Input Devices → Keyboard → Layouts

# Via command line (X11)
setxkbmap -layout us,de -option 'grp:alt_shift_toggle'

# Via console (Wayland)
localectl set-x11-keymap us,de '' '' grp:alt_shift_toggle
```

### 16.5 Date/Time/Locale Formats

```bash
# KDE settings
# System Settings → Regional Settings

# Command line
# Language
localectl set-locale LANG=en_US.UTF-8

# Keymap
localectl set-keymap us
localectl set-x11-keymap us

# Time format
# → Set via KDE: Regional Settings → Time → Format
```

### 16.6 Spell Check Dictionaries

```bash
# Install dictionaries
sudo dnf5 install aspell-{en,de,es,fr,it,pt,ru}

# Hunspell (used by many apps)
sudo dnf5 install hunspell-{en,de,es,fr,it,pt,ru}

# Sonnet (KDE spell checking)
sudo dnf5 install sonnet
```

---

## Appendix A: Installation Checklist

```
☐ Verify system meets minimum requirements
☐ Download Solus ISO
☐ Verify ISO checksum (sha256)
☐ Verify ISO GPG signature
☐ Create bootable USB
☐ Backup important data (for dual-boot)
☐ Disable Windows Fast Startup (for dual-boot)
☐ Disable Secure Boot temporarily (optional)
☐ Boot from USB media
☐ Select language/keyboard/timezone
☐ Choose partitioning method (automatic/manual)
☐ Set up encryption (recommended)
☐ Create user account
☐ Confirm installation settings
☐ Wait for installation to complete
☐ Reboot and remove USB
☐ Complete first-boot wizard
☐ Run system update (sudo dnf5 update)
☐ Install additional drivers (if needed)
☐ Create initial system snapshot
☐ Install essential software
```

## Appendix B: Keyboard Shortcuts (Live Environment)

| Shortcut | Function |
|----------|----------|
| `Super` | App launcher |
| `Super + D` | Show desktop |
| `Alt + Tab` | Switch windows |
| `Super + L` | Lock screen |
| `Ctrl + Alt + T` | Open terminal |
| `Super + E` | File manager (Dolphin) |
| `Print Screen` | Screenshot |
| `Super + V` | Clipboard manager |
| `Super + arrows` | Window tiling |
| `Super + Shift + arrows` | Move window to desktop |

## Appendix C: Emergency Recovery Commands

```bash
# Regenerate GRUB config
sudo grub2-mkconfig -o /boot/grub2/grub.cfg

# Regenerate initramfs
sudo dracut --force

# Reset root password (from live USB)
sudo chroot /mnt passwd

# Repair BTRFS
sudo btrfs check --repair /dev/nvme0n1p5

# Rollback system (snapper)
sudo snapper -c root undochange <pre>..<post>
```
