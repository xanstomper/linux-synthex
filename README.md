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
- **Git, Rust 1.80+, Go, Node.js, Java 21**
- **Docker, Podman, Buildah, Skopeo** — containers
- **QEMU/KVM + Virt-Manager** — virtualization
- **SystemTap, GDB, Valgrind, strace** — debugging

### Rust Toolchain
- **rustc** — Rust compiler (v1.80.0+, LLVM 17 backend)
- **cargo** — Package manager and build system
- **rust-src** — Source code for IDE/rust-analyzer
- **rustfmt, clippy, rust-analyzer** — Developer tooling
- **Rust-for-Linux** — Kernel module development support

### Rust Utility Suite
| Traditional | Rust Replacement | Package | Description |
|-------------|-----------------|---------|-------------|
| `grep` | `rg` (ripgrep) | `ripgrep` | Ultra-fast recursive search, .gitignore-aware |
| `find` | `fd` | `fd-find` | Intuitive file finder with sensible defaults |
| `cat` | `bat` | `bat` | Syntax-highlighted output, git integration |
| `ls` | `eza` | `eza` | Colorised, tree view, icons, git status |
| `du` | `dust` | `dust` | Visual disk usage with bar charts |
| `htop` | `btm` (bottom) | `bottom` | Graphical terminal system monitor |
| `sed` | `sd` | `sd` | Intuitive find & replace CLI |
| prompt | `starship` | `starship` | Cross-shell prompt, minimal and fast |
| `tmux` | `zellij` | `zellij` | Terminal multiplexer with workspace layout |
| `diff` | `delta` | `git-delta` | Syntax-highlighted git diff pager |
| `ps` | `procs` | `procs` | Modern process list with tree view |
| `time` | `hyperfine` | `hyperfine` | Statistical command benchmarking |
| `dig` | `dog` | `dog` | DNS lookup client with color |
| `nethogs` | `bandwhich` | `bandwhich` | Real-time bandwidth per process |
| `du` (TUI) | `dua` | `dua-cli` | Interactive disk usage analyzer |
| `ping` | `gping` | `gping` | Latency with real-time graph |
| `make` | `just` | `just` | Command runner (simpler make) |

### Solus Native Rust Tools
| Command | Description |
|---------|-------------|
| `solus-update-manager` | System update manager with BTRFS snapshots |
| `solus-driver-manager` | GPU detection and driver auto-install |
| `solus-pkg` (alias `spkg`) | Package manager with Solus repo awareness |

### Solus Tools
| Command | Description |
|---------|-------------|
| `solus` | Unified command center (19 commands) |
| `solus-layout` | Switch desktop layouts |
| `solus-gaming-mode` | Gaming mode (Big Picture + performance) |
| `solus-gpu-switch` | NVIDIA Optimus GPU switching |
| `solus-proton` | Proton version manager |
| `solus-firewall` | Firewall profile switcher |
| `solus-update` | Update manager with snapshots (Rust) |
| `solus-driver-manager` | GPU driver auto-install (Rust) |
| `solus-pkg` | Package manager with repo awareness (Rust) |
|| `solus-system-daemon` | Performance auto-tuner for VRR, HDR, CPU, TDP (Rust) |
|| `solus-ai-daemon` | Local AI assistant via Ollama, whisper voice commands (Rust) |
|| `solus-blueprint` | Export/import system identity (.zbp) |
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
|| `solus-ai` | solus-ai-daemon CLI — chat, start, stop, models, pull, advise |

## Project Structure

```
linux-solus/
├── branding/         # Logos, themes, wallpapers, icons
├── build/            # ISO build scripts, kickstart files
├── ci/               # GitHub Actions workflows (incl Rust CI)
├── desktop/          # KDE configs, KCM modules, launchers
├── installer/        # Calamares config and modules
├── kernel/           # Kernel config (BORE + EEVDF + FSYNC + Rust)
├── layouts/          # Desktop layout presets
├── modes/            # Performance mode scripts
├── packages/         # RPM spec files, repo configs
├── scripts/          # Docker build scripts
├── security/         # SELinux policy, hardening configs
├── src/
│   ├── solus-rust-tools/   # Rust workspace (update-manager, driver-manager, pkg)
│   ├── solus-*/            # C/C++/Python/QML system tools
│   └── ...
├── systemd/          # systemd service units
└── tests/            # Integration tests and validation
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
