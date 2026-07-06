# Solus Linux

A next-generation Fedora-based Linux distribution designed to be the definitive Linux desktop operating system. Combines the best of Fedora, Arch, Mint, Nobara, CachyOS, and Bazzite.

## Quick Start

### Build the ISO (on Fedora 41+)
```bash
sudo dnf install lorax livemedia-creator pykickstart
sudo bash scripts/build-solus.sh docker-build
sudo bash scripts/build-solus.sh build-iso
```

### Or build with Docker (any Linux host)
```bash
sudo bash scripts/build-solus.sh docker-build
sudo bash scripts/build-solus.sh build-rootfs
sudo bash scripts/build-solus.sh build-iso
```

### Run integration tests
```bash
make test     # 64+ tests — verifies code, configs, services, desktop files
make check    # validation targets for systemd, JSON, Python, desktop files
```

## Features

### System
- **KDE Plasma** desktop with Mint-inspired theme
- **Solus Mint** layout — bottom panel, window list, classic menu
- **BTRFS** filesystem with automatic snapper snapshots
- **SELinux** enforcing by default
- **Firewalld** with profiles (gaming, secure, dev, home)
- **Wayland**-first graphics — KWin compositor with OpenGL
- **PipeWire** audio

### Gaming
- **Steam** pre-installed with Proton support
- **Proton GE** — latest community Proton builds
- **GE-Proton Manager** — per-game Proton version management
- **Gaming Mode** — Steam Big Picture auto-launch, CPU/GPU optimization
- **GPU Switcher** — NVIDIA Optimus hybrid graphics support
- **MangoHUD, Gamescope, Gamemode, vkBasalt** 
- **Lutris, Heroic Games Launcher, Prism Launcher**
- **WINE + Winetricks** — full Windows compatibility
- **OBS Studio** with streaming support

### Performance
- **BORE Scheduler** — burst-oriented response enhancer
- **EEVDF** — Earliest Eligible Virtual Deadline scheduler
- **FSYNC/Futex2** — Wine/Proton game sync primitives
- **x86-64-v3** optimized by default
- **Performance profiles** — gaming, balanced, powersave
- **ZRAM** compressed swap

### Security
- **SELinux** enforcing with custom Solus policy
- **Firewalld** with nftables backend
- **Secure Boot** support (shim + GRUB)
- **LUKS2** full disk encryption
- **TPM2** measured boot
- **Kernel lockdown** mode
- **Hardened** sysctl, auditd, limits

### Applications
- **Firefox** (default browser)
- **LibreOffice** (Writer, Calc, Impress)
- **Thunderbird** (email)
- **GIMP, Krita, Inkscape** (graphics)
- **Kdenlive** (video editing)
- **Elisa** (music player)
- **Haruna** (video player)
- **Dolphin, Konsole, Kate, Gwenview, Spectacle**

### Development
- **VS Code** pre-installed
- **Git, Rust, Go, Node.js, Java 21**
- **Docker, Podman, Buildah, Skopeo** — containers
- **QEMU/KVM + Virt-Manager** — virtualization
- **SystemTap, GDB, Valgrind, strace** — debugging

### Solus Tools
| Command | Description |
|---------|-------------|
| `solus` | Unified command center (19 commands) |
| `solus-layout` | Switch desktop layouts |
| `solus-gaming-mode` | Gaming mode (Big Picture + performance) |
| `solus-gpu-switch` | NVIDIA Optimus GPU switching |
| `solus-proton` | Proton version manager |
| `solus-firewall` | Firewall profile switcher |
| `solus-update` | Update manager with snapshots |
| `solus-blueprint` | Export/import system identity (.zbp) |
| `solus-ai-hub` | Local AI model management via Ollama |
| `solus-webapp` | Turn websites into native apps |

### System Services
| Service | Description |
|---------|-------------|
| `solus-desktopd` | Desktop layout/theme/mode engine |
| `solus-hwdaemon` | Hardware detection daemon |
| `solus-gpu-setupd` | GPU driver auto-installer |
| `solus-stored` | Software center backend |
| `solus-workspace` | System mode switcher |
| `solus-recovery` | Boot failure recovery |

## Project Structure

```
linux-solus/
├── branding/         # Logos, themes, wallpapers, icons
├── build/            # ISO build scripts, kickstart files
├── ci/               # GitHub Actions workflows
├── desktop/          # KDE configs, KCM modules, launchers
├── installer/        # Calamares config and modules
├── kernel/           # Kernel config (BORE + EEVDF + FSYNC)
├── layouts/          # Desktop layout presets
├── modes/            # Performance mode scripts
├── packages/         # RPM spec files, repo configs
├── scripts/          # Docker build scripts
├── security/         # SELinux policy, hardening configs
├── src/              # All source code (daemons, tools, GUIs)
└── systemd/          # systemd service units
```

## Included from other distros

| Distro | Features integrated into Solus |
|--------|-------------------------------|
| **Mint** | Welcome screen, update manager, bottom panel layout, green Mint-Y theme |
| **Nobara** | Gaming kernel patches, Proton management, GPU switching, NVIDIA drivers |
| **CachyOS** | BORE scheduler, x86-64-v3, performance profiles, memory tuning |
| **Bazzite** | Gaming mode (Steam Big Picture), controller support, game streaming (Sunshine) |
| **Fedora** | Base system, package management (DNF5), SELinux, BTRFS |
| **Arch** | Rolling-style updates with snapshots, customization freedom |
