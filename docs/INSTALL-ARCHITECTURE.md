# SynthOS Installer Architecture

## Overview

SynthOS uses **Calamares** as its graphical installer, extended with 9 custom Python modules
that handle SynthOS-specific setup beyond what stock Calamares provides.

## Module Execution Sequence

```
SHOW PHASE (wizard pages)          EXEC PHASE (installation)
──────────────────────────         ───────────────────────────────────
1. welcome                         1.  partition        ← BTRFS layout
2. locale                          2.  mount
3. keyboard                        3.  unpackfs         ← squashfs → disk
4. partition                       4.  machineid
5. users                           5.  fstab
6. synthexprofile     ← CUSTOM     6.  locale / keyboard
7. summary                         7.  users
                                   8.  networkcfg
                                   9.  hwclock
                                   10. services-systemd
                                   11. dracut            ← initramfs
                                   12. packages          ← DNF post-install
                                   13. synthexhardwaredetect  ← CUSTOM
                                   14. grubcfg / bootloader
                                   15. displaymanager
                                   16. synthexfirstuser       ← CUSTOM
                                   17. synthexnetworksetup    ← CUSTOM
                                   18. synthexgpusetup        ← CUSTOM
                                   19. synthexsecuritysetup   ← CUSTOM
                                   20. synthexservices        ← CUSTOM
                                   21. synthextheme           ← CUSTOM
                                   22. synthexpostinstall     ← CUSTOM
                                   23. removeuser / umount / finished
```

## Custom Modules

| Module | Purpose |
|--------|---------|
| `synthexprofile` | User selects Desktop Profile (Plasma/GNOME/Hyprland/Gaming/Studio/etc.) |
| `synthexhardwaredetect` | Detects GPU (AMD/NVIDIA/Intel), RAM, SSD, WiFi chip |
| `synthexfirstuser` | Creates real user account with Synthex defaults |
| `synthexnetworksetup` | Configures NetworkManager, DNS-over-HTTPS, firewall |
| `synthexgpusetup` | Installs GPU driver stack (Mesa/NVIDIA/Intel/AMD ROCm) |
| `synthexsecuritysetup` | SELinux policy, SSH hardening, firewalld zones |
| `synthexservices` | Enables/disables systemd services per profile |
| `synthextheme` | Applies selected theme (SDDM, GRUB, Plymouth, KDE globals) |
| `synthexpostinstall` | Final cleanup, flatpak bootstrap, initramfs rebuild |

## Disk Layout (BTRFS default)

```
/dev/sdX
├── EFI System Partition    512 MiB   vfat    /boot/efi
├── /boot                   1 GiB     ext4    /boot
└── BTRFS pool              remaining  btrfs
    ├── @                             →  /
    ├── @home                         →  /home
    ├── @var                          →  /var
    ├── @var_log                      →  /var/log
    ├── @snapshots                    →  /.snapshots
    └── @tmp                          →  /tmp
```

## File Locations

| Path | Contents |
|------|---------|
| `/etc/calamares/settings.conf` | Module sequence (this file) |
| `/etc/calamares/modules/` | Per-module configuration files |
| `/usr/lib/calamares/modules/synthex*/` | Custom Python modules |
| `/usr/libexec/synthex/` | Post-install shell scripts |
| `/usr/share/calamares/branding/synthex/` | Slideshow, icons, strings |
| `/usr/share/synthex/profiles/` | Desktop profile JSON definitions |

## Build System

```
linux-synthex/
├── installer/           ← Calamares configs, modules, scripts
│   ├── config/          ← settings.conf + module confs
│   ├── modules/         ← 9 custom Python modules
│   └── scripts/         ← post-install shell scripts
├── branding/            ← GRUB, Plymouth, Calamares branding
├── packages/spec-files/ ← 139 RPM spec files
├── build/kickstart/     ← 5 Anaconda kickstart files
└── src/                 ← Rust (32 binaries) + Python + QML sources
```
