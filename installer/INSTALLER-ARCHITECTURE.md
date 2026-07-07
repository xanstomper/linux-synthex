# SynthOS Calamares Installer — Complete Architecture

## Overview

SynthOS uses [Calamares](https://calamares.io/) as its system installer with **5 custom modules**
and **6 post-install scripts** that wire together 32 Rust crates, 29 systemd units, and 60+ apps.

## Installation Flow

```
                    CALAMARES INSTALLER FLOW
┌─────────────────────────────────────────────────────────────────┐
│  SHOW PHASE (User sees these pages)                              │
│                                                                   │
│  ┌──────────┐   ┌────────────────┐   ┌──────────┐              │
│  │  WELCOME │──▶│ APP PICKER*    │──▶│ SUMMARY  │              │
│  │   page   │   │  QML page      │   │  page    │              │
│  └──────────┘   └────────────────┘   └──────────┘              │
│                       │                                          │
│                       ▼                                          │
│              User selects:                                       │
│               • Theme (5 options)                                │
│               • Apps (60+ apps in 8 categories)                  │
│                       │                                          │
│                       ▼                                          │
│         Writes to Calamares global storage:                      │
│         synthexTheme, synthexApps                                │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  EXEC PHASE (Installation runs)                                  │
│                                                                   │
│  1. PARTITION      → BTRFS with subvolumes (@, @home, @var...)   │
│  2. MOUNT           → Mount filesystem at /mnt                    │
│  3. UNPACKFS        → Unpack squashfs rootfs                     │
│  4. MACHINEID       → Generate machine-id                        │
│  5. FSTAB           → Generate fstab entries                     │
│  6. LOCALE          → Configure locale                           │
│  7. KEYBOARD        → Configure keyboard layout                  │
│  8. DRACUT          → Generate initramfs                         │
│  9. BOOTLOADER      → Install GRUB                               │
│  10. GRUBCFG        → Configure GRUB                             │
│  11. NETWORKCFG     → Configure NetworkManager                   │
│  12. PACKAGES       → Install base + profile packages (dnf)      │
│      └─ synthex-core group (32+ packages)                        │
│      └─ Profile group (plasma/gaming/ai/etc.)                    │
│      └─ All additional_packages (daemons, CLI tools, fonts)      │
│  13. SERVICES-SYSTEMD → Enable systemd services                  │
│  14. USERS          → Create user account                        │
│  15. DISPLAYMANAGER → Configure SDDM                             │
│  16. REMOVEUSER     → Remove live user                           │
│  17. SHELLPROCESS   → Run 6 post-install scripts                 │
│      └─ post-install.sh (DNF config, GPU, services, GRUB)       │
│      └─ hardware-detect.sh (CPU, GPU, RAM, disks)               │
│      └─ apply-theme.sh (SDDM, Plasma, GRUB theme)              │
│      └─ user-defaults.sh (bashrc, GTK, fonts, env)             │
│      └─ enable-repo.sh (Synthex repo + GPG key)                │
│      └─ dracut + grub2-mkconfig                                 │
│  18. FINISHED       → Reboot                                    │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST-INSTALL (Python module: synthexpostinstall)                │
│                                                                   │
│  1. Write install manifest → /var/lib/synthex/install-profile.json│
│  2. Install package groups via dnf group install                 │
│  3. Setup Flatpak + Flathub                                      │
│  4. Install 60+ user-selected apps (flatpak/dnf fallback)       │
│  5. Setup Synthex binaries in /usr/bin                           │
│  6. Install systemd unit files                                    │
│  7. Apply desktop profile (KDE Plasma layout)                    │
│  8. Apply theme (color scheme, SDDM, GRUB)                      │
│  9. Enable all Synthex services                                  │
│  10. Write first-boot marker                                     │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FIRST BOOT (OOBE Wizard)                                        │
│                                                                   │
│  1. synthex-firstboot.service runs                               │
│  2. Installs deferred apps from OOBE                             │
│  3. Launches synthex-oobe (QML wizard):                          │
│     Welcome → Profile → BundlePicker → AppPicker → Theme → Done  │
│  4. User can install more apps post-install                      │
│  5. Marks first boot complete                                    │
└─────────────────────────────────────────────────────────────────┘
```

## 60+ Apps in the Picker

| Category       | Apps                                                           |
|----------------|----------------------------------------------------------------|
| 🌐 Browsers    | Firefox, Brave, Chrome, Tor, Edge, Vivaldi, Opera              |
| 💬 Messaging   | Discord, Telegram, Signal, WhatsApp, Slack, Element, Zoom,    |
|                | Thunderbird, Mailspring                                        |
| 🎮 Gaming      | Steam, Lutris, Heroic, Gamescope, MangoHUD, GameMode,        |
|                | ProtonUp-Qt, RetroArch                                        |
| 🎬 Multimedia  | VLC, MPV, OBS Studio, Kdenlive, Spotify, Audacity             |
| 🖌️ Creative   | Blender, GIMP, Krita, Inkscape, LibreOffice, OnlyOffice,      |
|                | Obsidian                                                      |
| 💻 Dev         | VS Code, Docker, Podman, Distrobox, GitKraken, Neovim,       |
|                | JetBrains IDEs                                                |
| 🤖 AI & Agents | Ollama, Hermes, OpenCode, Codex, Synthex Agent, Open WebUI   |
| 🛠 Utilities   | Syncthing, qBittorrent, GParted, Btop++, Fastfetch, tmux,    |
|                | Neofetch, Wireshark, VeraCrypt, Cryptsetup, Mullvad VPN      |

## 9 Package Groups

| Group             | Contents                                                        |
|-------------------|-----------------------------------------------------------------|
| synthex-core      | All 32 Rust daemons/CLIs, fonts, mesa, pipewire                |
| synthex-plasma    | KDE Plasma, SDDM, dolphin, konsole, discover                   |
| synthex-gaming    | Steam, Lutris, gamescope, mangohud, gamemode, wine             |
| synthex-codecs    | ffmpeg, gstreamer plugins, libdvdcss                            |
| synthex-developer | git, make, cmake, gcc, python3, nodejs, golang, rust           |
| synthex-handheld  | Handheld mode, maliit-keyboard, dolphin-emu                    |
| synthex-nvidia    | NVIDIA proprietary driver installer                            |
| synthex-ai        | AI daemon, AI hub, AI platform                                 |
| synthex-creator   | Blender, krita, gimp, inkscape, kdenlive, audacity, OBS        |

## 32 Rust Crates

### Core Daemons (7)
synthex-system-daemon, synthex-hwdaemon, synthex-desktopd, synthex-gpu-setupd,
synthex-stored, synthex-ai-daemon, synthex-snapshot-manager

### CLI Tools (2)
synthex-cli (unified CLI), synthbox (sandbox runner)

### Security (4)
synthguard (integrity monitor), synthshield (snapshot manager),
synthvault (encrypted secrets), synthidentity (user identity)

### System Management (14)
synthupdate (auto-updater), synthnet (network manager),
synthex-app-installer (60+ app installer), synthex-compat-db (HW compat DB),
synthex-codec-installer-rs, synthex-handheld-rs, synthex-kernel-manager-rs,
synthex-perf-tuning-rs, synthex-proton-manager-rs, synthex-recovery-rs,
synthex-service-manager-rs, synthex-system-report-rs,
synthex-terminal-workspace, synthex-wine-manager

### Integration (2)
installer-detect (Calamares HW detection), integration-engine (upstream monitor)

### Rust Tool Suite (3)
synthex-pkg (DNF wrapper), synthex-update-manager, synthex-driver-manager

## 29 Systemd Units

### Services (22)
synthex-system-daemon, synthex-desktopd, synthex-hwdaemon, synthex-gpu-setupd,
synthex-stored, synthex-ai-daemon, synthex-ai-hub, synthex-agent,
synthex-integration-engine, synthex-compat-db, synthex-marketplace,
synthex-control-center, synthex-firstboot, synthex-oobe, synthex-hermes,
synthex-blueprint, synthex-gaming-mode, synthex-kernel-manager,
synthex-power-profiles, synthex-recovery, synthex-service-manager,
synthex-webappd, synthex-studiocd, synthex-ananicy, synthex-auto-tune

### Timers (3)
synthex-blueprint.timer, synthex-snapshot-manager.timer, synthex-auto-tune.timer

### Targets (1)
synthex.target

## Key Files

| File | Purpose |
|------|---------|
| `installer/config/calamares-settings.conf` | Main Calamares settings (YAML) |
| `installer/modules/synthexprofile/main.py` | View module bridge (QtPy) |
| `installer/modules/synthexprofile/synthex-app-picker.qml` | App picker UI (QML, 60+ apps) |
| `installer/modules/synthexpostinstall/synthexpostinstall.py` | Post-install job (wires everything) |
| `installer/modules/packages/packages.conf` | Package installation config |
| `installer/modules/shellprocess/shellprocess.conf` | Post-install shell scripts |
| `installer/scripts/post-install/*.sh` | 6 post-install scripts |
| `installer/scripts/synthex-installer-hook` | HW detection hook for live boot |
| `branding/calamares/*` | Branding + slideshow |
| `packages/groups/synthex-comps.xml` | 9 package groups (comps XML) |
| `packages/spec-files/` | 126 RPM spec files |
| `systemd/` | 29 systemd unit files |
| `Cargo.toml` | Workspace with 32 Rust crates |
| `src/synthex-app-installer/src/main.rs` | CLI app installer (Rust, 60+ apps) |
