# SynthOS

A next-generation Fedora-based Linux distribution designed to be the definitive Linux desktop operating system. Combines the best of Fedora, Arch, Mint, Nobara, CachyOS, and Bazzite.

## Quick Start

### Build the ISO (on Fedora 41+)
```bash
sudo dnf install lorax livemedia-creator pykickstart
sudo bash scripts/build-synthex.sh docker-build
sudo bash scripts/build-synthex.sh build-iso
```

### Or build with Docker (any Linux host)
```bash
sudo bash scripts/build-synthex.sh docker-build
sudo bash scripts/build-synthex.sh build-rootfs
sudo bash scripts/build-synthex.sh build-iso
```

### Run integration tests
```bash
python3 tests/integration-tests.py   # 70 tests — validates code, configs, services, builds
make check    # validation targets for systemd, JSON, Python, desktop files
make rust-check  # cargo check — verify Rust workspace compiles cleanly
```

## Features

### System
- **KDE Plasma** desktop with Mint-inspired theme
- **Synthex Mint** layout — bottom panel, window list, classic menu
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
- **SELinux** enforcing with custom Synthex policy
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

### Synthex Native Rust Tools
| Command | Description |
|---------|-------------|
| `synthex-integration-engine` | Upstream monitoring — tracks Arch, Nobara, Bazzite, CachyOS, KDE, Mesa, Kernel, Proton-GE |
| `synthex-snapshot` | Btrfs snapshot manager — create, list, rollback, verify, clean |
| `synthex-update-manager` | System update manager with BTRFS snapshots |
| `synthex-driver-manager` | GPU detection and driver auto-install |
| `synthex-pkg` (alias `spkg`) | Package manager with Synthex repo awareness |
| `synthex-ai-daemon` | AI assistant — Ollama integration, hardware advice |
| `synthex-system-daemon` | Performance auto-tuner — CPU governor, TDP, GPU power |
| `synthex-hwdaemon` | Hardware detection daemon — D-Bus service |
| `synthex-desktopd` | Desktop layout/theme engine |
| `synthex-gpu-setupd` | GPU driver auto-installer — AMD, Intel, NVIDIA |
| `synthex-stored` | Software center backend — DNF5, Flatpak |
| `synthex-installer-detect` | Hardware detection for Calamares installer |
| `synthex-cli` | Unified system tool — info, doctor, mode, update, health |

### Synthex Tools
| Command | Description |
|---------|-------------|
| `synthex` | Unified command center (19 commands) |
| `synthex-layout` | Switch desktop layouts |
| `synthex-gaming-mode` | Gaming mode (Big Picture + performance) |
| `synthex-gpu-switch` | NVIDIA Optimus GPU switching |
| `synthex-proton` | Proton version manager |
| `synthex-firewall` | Firewall profile switcher |
| `synthex-update` | Update manager with snapshots (Rust) |
|| `synthex-driver-manager` | GPU driver auto-install (Rust) |
|| `synthex-pkg` | Package manager with repo awareness (Rust) |
||| `synthex-system-daemon` | Performance auto-tuner for VRR, HDR, CPU, TDP (Rust) |
||| `synthex-ai-daemon` | Local AI assistant via Ollama, whisper voice commands (Rust) |
||| `synthex-installer-detect` | HW auto-detection for Calamares installs (Rust) |
||| `synthex-blueprint` | Export/import system identity (.zbp) |

### COSMIC Desktop (Pop!_OS Rust Port)
| Component | Package | Role |
|---|---|---|
| | `cosmic-comp` | Wayland compositor — tiling/stacking, GPU-accelerated |
| | `cosmic-bg` | Wallpaper and background daemon |
| | `cosmic-panel` | Desktop panel with app launcher, workspaces, system tray |
| | `cosmic-app-library` | Searchable application launcher |
| | `cosmic-randr` | Display configuration (xrandr replacement) |
| | `cosmic-osd` | Volume, brightness, media on-screen display |
| | `cosmic-notifications` | Desktop notification daemon |
| | `cosmic-epoch` | PAM-based greeter/login manager |
| | `cosmic-settings` | Full graphical settings (12+ categories) |
| | `cosmic-term` | GPU-accelerated terminal with split panes |
| | `cosmic-files` | Dual-pane file manager |
| | `cosmic-text-editor` | Modern text editor with syntax highlighting |
| | `cosmic-workspaces` | Virtual desktop workspace overview |
| | `cosmic-applets` | Desktop applets (monitor, clock, network) |
| | `cosmic-screenshot` | Screenshot + recording + annotations |
| | `xdg-desktop-portal-cosmic` | Portal backend for Flatpak/Snap |

### Rust CLI Utilities (Ported from Fedora, Arch)
| Tool | Replaces | Spec |
|---|---|---|
| `ripgrep (rg)` | grep | `rust-utils-ripgrep.spec` |
| `fd-find (fd)` | find | `rust-utils-fd.spec` |
| `bat` | cat | `rust-utils-bat.spec` |
| `eza` | ls | `rust-utils-eza.spec` |
| `dust` | du | `rust-utils-dust.spec` |
| `bottom (btm)` | htop | `rust-utils-bottom.spec` |
| `sd` | sed | `rust-utils-sd.spec` |
| `starship` | shell prompt | `rust-utils-starship.spec` |
| `zellij` | tmux | `rust-utils-zellij.spec` |
| `git-delta` | diff | `rust-utils-delta.spec` |
| `procs` | ps | `rust-utils-procs.spec` |
| `hyperfine` | time (benchmark) | `rust-utils-hyperfine.spec` |
| `dog` | dig (DNS) | `rust-utils-dog.spec` |
| `dua-cli` | ncdu | `rust-utils-dua-cli.spec` |
| `gping` | ping | `rust-utils-gping.spec` |
| `bandwhich` | nethogs | `rust-utils-bandwhich.spec` |
| `just` | make | `rust-utils-just.spec` |
| `helix` | vim/nano (editor) | `rust-utils-helix.spec` |
| `nushell (nu)` | bash | `rust-utils-nushell.spec` |
| `zoxide` | cd | `rust-utils-zoxide.spec` |
| `atuin` | history | `rust-utils-atuin.spec` |
| `tealdeer` | man (tldr) | `rust-utils-tealdeer.spec` |
| `ouch` | tar/gzip/zip | `rust-utils-ouch.spec` |

`synthex-ai-hub`
| `synthex-webapp` | Turn websites into native apps |

### System Services (all Rust)
| Service | Language | Description |
|---------|----------|-------------|
| `synthex-system-daemon` | Rust | Performance auto-tuner — CPU, TDP, GPU, gaming, VRR, HDR |
| `synthex-integration-engine` | Rust | Upstream monitoring — tracks Arch, Nobara, Bazzite, CachyOS, KDE, Mesa |
| `synthex-snapshot-manager` | Rust | Btrfs snapshot creation, rollback, verification, cleanup |
| `synthex-hwdaemon` | Rust | Hardware detection daemon — CPU, GPU, RAM, disks, network |
| `synthex-gpu-setupd` | Rust | GPU driver auto-installer — AMD, Intel, NVIDIA, Secure Boot |
| `synthex-desktopd` | Rust | Desktop layout/theme/mode engine — Mint, Windows, Gaming, macOS |
| `synthex-stored` | Rust | Software center backend — DNF, Flatpak, AppImage, AUR |
| `synthex-ai-daemon` | Rust | Local AI assistant — Ollama integration, whisper, diagnostics |
| `synthex-installer-detect` | Rust | Hardware detection for Calamares installer |
| `synthex-cli` | Rust | Unified CLI — info, doctor, mode, update, snapshot, health |
| `synthex-recovery` | Rust | Recovery framework — boot, driver, package, network repair |
| `synthex-service-manager` | Rust | Systemd service management — list, start, stop, enable, disable |
| `synthex-kernel-manager` | Rust | Kernel management — list, install, remove, switch, cleanup |
| `synthex-compat-db` | Rust | Hardware compatibility database — scan, check, report |

### GUI Applications
| Application | Framework | Description |
|-------------|-----------|-------------|
| `synthex-control-center` | QML/C++ | Unified control center — 13 pages (Dashboard, System, Performance, Gaming, Developer, Themes, Security, Updates, Drivers, RGB, Snapshots, Kernel, Controllers) |
| `synthex-software-center` | QML | Mint-inspired software manager with category browsing |
| `synthex-oobe` | QML | First-run wizard — profile selection, theme, bundles |
| `synthex-gaming-center` | QML | Gaming hub — Steam, Proton, MangoHUD, Gamescope |
| `synthex-studio` | QML/C++ | Theme studio with preset designer |
| `synthex-welcome` | Python | Welcome application with links and tutorials |
| `synthex-agent` | Python | AI-powered desktop agent |

## Project Structure

```
linux-synthex/
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
│   ├── synthex-rust-tools/   # Rust workspace (update-manager, driver-manager, pkg)
│   ├── synthex-*/            # C/C++/Python/QML system tools
│   └── ...
├── systemd/          # systemd service units
└── tests/            # Integration tests and validation
```

## Included from other distros

| Distro | Features integrated into Synthex |
|--------|-------------------------------|
| **Mint** | Welcome screen, update manager, bottom panel layout, green Mint-Y theme |
| **Nobara** | Gaming kernel patches, Proton management, GPU switching, NVIDIA drivers |
| **CachyOS** | BORE scheduler, x86-64-v3, performance profiles, memory tuning |
| **Bazzite** | Gaming mode (Steam Big Picture), controller support, game streaming (Sunshine) |
| **Fedora** | Base system, package management (DNF5), SELinux, BTRFS |
| **Arch** | Rolling-style updates with snapshots, customization freedom |
