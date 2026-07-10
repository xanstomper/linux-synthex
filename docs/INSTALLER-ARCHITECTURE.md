# SynthOS Installer Architecture

## Overview

SynthOS uses a customized **Calamares** installer framework enhanced with bespoke Python modules that provide hardware detection, profile selection, GPU configuration, and post-install setup beyond what stock Calamares offers.

---

## Directory Layout

```
installer/
├── config/
│   ├── settings.conf              # Calamares global settings
│   └── calamares-settings.conf    # Full module sequence & config
├── modules/
│   ├── bootloader/                # Built-in: GRUB/systemd-boot
│   ├── displaymanager/            # Built-in: SDDM/GDM setup
│   ├── dracut/                    # Built-in: initramfs generation
│   ├── finished/                  # Built-in: completion screen
│   ├── fstab/                     # Built-in: /etc/fstab generation
│   ├── grubcfg/                   # Built-in: grub.cfg customisation
│   ├── keyboard/                  # Built-in: keyboard layout
│   ├── locale/                    # Built-in: locale / timezone
│   ├── machineid/                 # Built-in: /etc/machine-id
│   ├── networkcfg/                # Built-in: NetworkManager config
│   ├── packages/                  # Built-in: DNF package installs
│   ├── partition/                 # Built-in: disk partitioning
│   ├── removeuser/                # Built-in: removes live user
│   ├── services-systemd/          # Built-in: systemd enable/disable
│   ├── shellprocess/              # Built-in: shell script runner
│   ├── unpackfs/                  # Built-in: rootfs extraction
│   ├── users/                     # Built-in: user account creation
│   ├── welcome/                   # Built-in: welcome screen
│   ├── synthexfirstuser/          # Custom: first-user wizard
│   ├── synthexgpusetup/           # Custom: GPU driver selection
│   ├── synthexhardwaredetect/     # Custom: hardware fingerprinting
│   ├── synthexnetworksetup/       # Custom: network configuration
│   ├── synthexpostinstall/        # Custom: post-install pipeline
│   ├── synthexprofile/            # Custom: desktop profile picker
│   ├── synthexsecuritysetup/      # Custom: SELinux / firewall
│   ├── synthexservices/           # Custom: systemd service manager
│   └── synthextheme/              # Custom: theme / SDDM / GRUB
└── welcome/
    └── Welcome.qml                # OOBE welcome QML application
```

---

## Installation Sequence

### Show Phase (Interactive UI Pages)
| Order | Module | Purpose |
|-------|--------|---------|
| 1 | `welcome` | Language selection, requirements check |
| 2 | `locale` | Timezone and locale picker |
| 3 | `keyboard` | Keyboard layout |
| 4 | `synthexprofile` | Desktop profile & edition picker |
| 5 | `summary` | Installation summary review |

### Exec Phase (Background Tasks)
| Order | Module | Purpose |
|-------|--------|---------|
| 1 | `partition` | Disk partitioning (Btrfs + subvolumes) |
| 2 | `mount` | Mount target filesystem |
| 3 | `unpackfs` | Extract squashfs rootfs |
| 4 | `machineid` | Generate `/etc/machine-id` |
| 5 | `fstab` | Write `/etc/fstab` |
| 6 | `locale` | Apply locale to target |
| 7 | `keyboard` | Apply keyboard to target |
| 8 | `dracut` | Regenerate initramfs |
| 9 | `bootloader` | Install GRUB / systemd-boot |
| 10 | `grubcfg` | Write GRUB config with SynthOS theme |
| 11 | `networkcfg` | Configure NetworkManager |
| 12 | `packages` | Install edition-specific packages |
| 13 | `services-systemd` | Enable/disable systemd units |
| 14 | `users` | Create live → real user account |
| 15 | `displaymanager` | Configure SDDM autologin (first boot) |
| 16 | `synthexpostinstall` | Full post-install pipeline (see below) |
| 17 | `shellprocess` | Run `post-install.sh` cleanup script |
| 18 | `removeuser` | Remove `synthex` live user |
| 19 | `finished` | Show completion, offer reboot |

---

## Custom Module Details

### `synthexhardwaredetect`
Runs before the exec phase to fingerprint:
- CPU vendor & core count → selects scheduler tuning
- GPU vendor (NVIDIA / AMD / Intel) → queues driver packages
- RAM total → warns if under 4 GB (gaming profiles need 8 GB)
- Storage type (NVMe / SSD / HDD) → tuning & swap recommendations
- Display server capability → Wayland vs X11 fallback logic

Output is stored in `GlobalStorage` and consumed by later modules.

### `synthexprofile`
Presents the profile picker QML page. Profiles map to package bundles:

| Profile | Desktop | Bundle |
|---------|---------|--------|
| `classic` | KDE Plasma | `synthex-plasma` |
| `gaming` | KDE Plasma + gaming stack | `synthex-gaming-dark` |
| `lite` | KDE Plasma (lightweight) | `synthex-desktop-lite` |
| `studio` | KDE Plasma + creative tools | `synthex-studio` |
| `pro` | KDE Plasma + dev tools | `synthex-pro` |
| `minimal` | no desktop | `synthex-minimal` |
| `gaming-neon` | Plasma gaming neon theme | `synthex-gaming-dark` |
| `ai` | AI workstation | `synthex-ai` |

### `synthexgpusetup`
Installs GPU drivers after hardware detection:
- **NVIDIA**: Akmod-NVIDIA (open kernel module for RTX 3000+, proprietary otherwise)
- **AMD**: Mesa + AMDGPU + ROCm (optional, based on VRAM)
- **Intel**: intel-media-driver (iHD)
- **VM**: Virtual GPU guest additions (VMware / VirtualBox / KVM)

### `synthexpostinstall`
The main post-install orchestrator. Runs 19 labelled steps:
1. Profile validation
2. OOBE apps JSON write
3. Flatpak remote setup (Flathub + Flathub Beta)
4. Flatpak app installation (profile-specific)
5. Hardware-specific post-install
6. SDDM autologin configuration
7. Plymouth theme installation
8. GRUB theme installation & `grub2-mkconfig`
9. GPU driver finalisation
10. Synthex first-boot service enablement
11. Synthex system daemon enablement
12. Synthex agent enablement
13. Calamares service removal
14. DNF automatic-install timer configuration
15. Security hardening (SELinux / firewall / SSH)
16. User group membership (audio, video, gamemode, etc.)
17. Theme / SDDM / wallpaper application
18. Synthex update manager configuration
19. Final cleanup & state file write

### `synthextheme`
Applies the SynthOS visual identity:
- SDDM theme: `synthex-sddm-theme`
- Plymouth theme: `synthex-plymouth` (dark amber splash)
- GRUB theme: `/usr/share/grub/themes/synthex/`
- KDE Plasma global theme: `synthex-kde-theme`
- KDE colour scheme: SynthexDark / SynthexAmber
- Cursor: Bibata-Modern-Amber
- Icon theme: Tela-circle-dark / Papirus-Dark
- Wallpaper: `/usr/share/synthex/wallpapers/synthex-default.jpg`

---

## Disk Partitioning

### Default Layout (UEFI + Btrfs)
```
/dev/sdX1   512 MiB   FAT32     /boot/efi   ESP flag
/dev/sdX2     2 GiB   ext4      /boot
/dev/sdX3  remaining  Btrfs     /
  └── @           →  /
  └── @home       →  /home
  └── @var        →  /var
  └── @tmp        →  /tmp
  └── @snapshots  →  /.snapshots
```

### Gaming Profile (additional swap)
- `zram` enabled by `zram-generator` at 50% RAM
- Optional: separate `/dev/sdX4` for game library

### Encryption
Optional LUKS2 full-disk encryption:
- Argon2id KDF, 4 iterations, 64 MiB memory
- TPM2 unlock (systemd-cryptenroll) or passphrase
- Enabled when `enableLuksAutomatedPartitioning: true` in settings

---

## First Boot (OOBE) Flow

After reboot, `synthex-firstboot.service` runs once:
1. Launches `synthex-welcome` QML app
2. User selects apps from bundle picker
3. Installs selected Flatpak apps
4. Applies hardware optimisations (CPU governor, GPU settings)
5. Enables user-selected services
6. Writes `~/.synthex-firstboot-done` sentinel
7. Service auto-disables via `RemainAfterExit=yes` + `ConditionPathExists=!`

---

## Build Integration

The installer modules are compiled into the live ISO at:
```
/usr/lib/calamares/modules/synthex*/
```
via the `synthex-installer` RPM package, built by:
```
build/scripts/build-iso.sh  →  rpmbuild  →  mkksiso
```

See `docs/build/build-guide.md` for full build instructions.
