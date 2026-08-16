<div align="center">

# ☀️ SynthOS Linux

**Illuminate Your Desktop**

[![License: GPL-3.0+](https://img.shields.io/badge/License-GPL--3.0%2B-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2026.10-orange.svg)](docs/RELEASE-NOTES-2026.10.md)
[![Status](https://img.shields.io/badge/Status-Pre--Release-yellow.svg)]()
[![Base](https://img.shields.io/badge/Base-Fedora%20Rawhide-informational.svg)]()

A next-generation Fedora-based Linux distribution designed to be the definitive desktop experience — gaming-ready, developer-friendly, AI-integrated, and beautiful out of the box.

</div>

---

## 🌟 What is SynthOS?

SynthOS (formerly "Synthex") is a curated Linux desktop distribution built on Fedora Rawhide, delivering:

- **7 Desktop Profiles** — Gaming, Focus, Pro, Studio, AI, Classic, Lite  
- **Gorgeous theming** — Dark navy/amber SDDM login, animated Plymouth splash, custom GRUB
- **Gaming-first kernel** — BORE scheduler, low-latency patches, Proton/Steam pre-configured
- **AI-native** — Local LLM (Ollama), Whisper voice commands, `synth ai` shell assistant
- **Secure by default** — SELinux enforcing, SynthGuard IDS, LUKS2, DNS-over-HTTPS
- **Polished installer** — Calamares with 7-slide slideshow, profile picker, app selection wizard
- **First-run wizard** — OOBE with profile/theme/app selection that applies on first login

---

## 📁 Repository Structure

```
linux-synthex/
├── src/                        # All Synthex application source code
│   ├── synthex-control-center/ # System settings hub (Qt6/QML)
│   ├── synthex-oobe/           # First-run setup wizard (QML + Python)
│   ├── synthex-welcome/        # Welcome screen (Python/Qt)
│   ├── synthex-gaming-center/  # Gaming launcher (Qt6/QML)
│   ├── synthex-software-center/# App store (Qt6/QML)
│   ├── synthex-installer/      # ISO build pipeline
│   ├── synthex-agent/          # Desktop assistant daemon
│   └── ...                     # 60+ additional components
├── packages/
│   ├── spec-files/             # 161 RPM spec files
│   └── groups/                 # Comps groups XML
├── installer/
│   ├── config/                 # Calamares settings.conf + module configs
│   ├── modules/                # Custom Calamares Python modules
│   │   ├── synthexprofile/     # Profile selection module
│   │   └── synthexpostinstall/ # Post-install wiring (apps, services, theme)
│   └── scripts/post-install/   # Hardware detect, GPU setup, theme apply, GRUB
├── branding/
│   ├── calamares/              # Installer branding + 7-slide slideshow
│   ├── desktop-profiles/       # Per-profile KDE look-and-feel packages
│   ├── plymouth/               # Boot splash theme + install script
│   └── theme/                  # Design tokens, logo sources
├── desktop/
│   ├── sddm/synthex-sddm-theme/# Login screen (QML, dark navy/amber)
│   ├── grub-theme/             # GRUB2 bootloader theme
│   ├── plymouth/synthex-theme/ # Plymouth boot splash (script + SVGs)
│   └── plasma/                 # KDE Plasma workspace configs
├── configs/
│   ├── grub/40_synthex         # Custom GRUB menu entries script
│   ├── sddm/                   # SDDM configuration
│   └── dracut/                 # Dracut initramfs config
├── build/
│   ├── kickstart/              # ISO kickstart files (plasma/gnome/hyprland/gaming)
│   ├── livecd/                 # LiveCD creator configs
│   └── scripts/                # Build helper scripts
├── systemd/                    # systemd service/timer unit files
├── docs/                       # Documentation + release notes
└── Makefile                    # Build system
```

---

## 🚀 Quick Start

### Building an ISO

```bash
# Prerequisites (Fedora/RHEL host)
sudo dnf install lorax livemedia-creator pykickstart xorriso isohybrid

# Build KDE Plasma edition (default)
make iso-plasma VERSION=2026.10

# Other editions
make iso-gaming      # Gaming-optimized
make iso-hyprland    # Hyprland WM
make iso-gnome       # GNOME desktop
make iso-minimal     # Minimal CLI base

# Output: build/iso-out/synthex-plasma-2026.10-v3.iso
```

### Installing Themes (on an existing system)

```bash
# Install all SynthOS themes at once
make install-themes

# Or individually:
sudo make install-sddm-theme      # Login screen
sudo make install-grub-theme      # Bootloader
sudo make install-plymouth-theme  # Boot splash
```

### Building Packages

```bash
# Build all RPM packages (requires rpmbuild)
make packages

# Or build in Docker:
make dev-container
```

---

## 🎨 Desktop Profiles

| Profile   | Icon | Description |
|-----------|------|-------------|
| **Classic**  | 🖥  | Familiar, Windows-like layout for new Linux users |
| **Gaming**   | 🎮 | Big Picture mode, Steam, Proton, Gamescope |
| **Focus**    | ⚡  | Minimal, keyboard-driven, distraction-free |
| **Pro**      | 💻 | Developer cockpit: Rust, Python, Docker, VS Code |
| **Studio**   | 🎨 | Creative suite: Kdenlive, Krita, Blender, OBS |
| **AI Hub**   | 🤖 | Ollama, Whisper, synth-ai shell, AI workspace |
| **Lite**     | 🪶  | Lightweight, fast, for older/low-RAM hardware |

---

## 🎮 Gaming Stack

| Component | Version | Notes |
|-----------|---------|-------|
| Kernel    | synthex-kernel | BORE + FUTEX2 + HDR patches |
| Steam     | Latest  | Pre-installed (native + Flatpak) |
| Proton GE | Latest  | Valve + GloriousEggroll |
| Gamescope | 3.14+   | VRR, HDR, per-game FSR |
| MangoHUD  | 0.7.x   | GPU/CPU overlay |
| GameMode  | 1.8     | CPU/GPU boost daemon |
| DXVK      | 2.4+    | DirectX → Vulkan |
| VKD3D-Proton | 2.13+ | DX12 → Vulkan |
| Heroic    | 2.14+   | Epic/GOG/Amazon stores |
| Lutris    | 0.5.x   | Universal game launcher |

---

## 🛠 System Components

```
synthex-system-daemon   — Master system daemon (D-Bus hub)
synthex-hwdaemon        — Hardware detection & management
synthex-desktopd        — Desktop session coordinator
synthex-agent           — AI assistant daemon
synthex-firstboot       — First-boot initialization service
synthex-oobe            — First-login setup wizard
synthex-welcome         — Welcome screen app
synthex-control-center  — System settings GUI
synthex-software-center — Unified app store
synthex-update-manager  — System update GUI
synthex-gaming-mode     — Gaming mode switcher
synthex-gpu-setupd      — GPU configuration daemon
synthex-recovery        — Recovery mode helper
synthguard              — Security/IDS daemon
synthnet                — Network configuration
synthvault              — Secret/credential manager
```

---

## 🔧 Configuration

### Boot Parameters

```bash
# Added to GRUB_CMDLINE_LINUX_DEFAULT by synthex-grub-setup.sh:
quiet splash

# Gaming mode (applied by synthex-gaming-mode):
mitigations=off threadirqs

# Encrypted systems (added by Calamares):
rd.luks.uuid=<UUID>

# NVIDIA with Wayland:
nvidia-drm.modeset=1 nvidia.NVreg_PreserveVideoMemoryAllocations=1
```

### Key File Locations

| File | Purpose |
|------|---------|
| `/var/lib/synthex/install-profile.json` | Active desktop profile |
| `/var/lib/synthex/oobe-apps.json` | Apps selected in OOBE |
| `/var/lib/synthex/firstboot-complete` | First-boot completion marker |
| `/etc/synthex/synthex.conf` | Global SynthOS configuration |
| `/etc/sddm.conf.d/synthex.conf` | SDDM theme config |
| `/etc/default/grub` | GRUB boot parameters |
| `/usr/share/plymouth/themes/synthex/` | Plymouth theme |

---

## 📦 Edition ISOs

| Edition | Size | Profile | Default WM |
|---------|------|---------|------------|
| Plasma  | ~3.2 GB | Full | KDE Plasma 6.2 |
| Hyprland| ~2.8 GB | Focus/Gaming | Hyprland 0.42 |
| GNOME   | ~3.0 GB | Full | GNOME 47 |
| Gaming  | ~3.8 GB | Gaming | KDE Plasma |
| Minimal | ~900 MB | None | None (CLI) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make changes and test
4. Open a pull request

### Building a Component

```bash
# Build a specific Rust component
cargo build --release -p synthex-hwdaemon

# Run the OOBE wizard in reset mode
make run-oobe

# Validate all configs
make validate
```

---

## 📜 License

- Source code: **GPL-3.0+**
- Artwork & wallpapers: **CC-BY-SA-4.0**
- Documentation: **CC-BY-4.0**

---

## 🔗 Links

| | |
|-|-|
| 🌐 Website | https://synthex-os.org |
| 💬 Forum | https://discuss.synthex-os.org |
| 🐛 Issues | https://github.com/synthex-linux/issues |
| 🎮 Discord | https://discord.gg/synthex |
| 📧 Contact | team@synthex-os.org |

---

<div align="center">

**Built with ❤ by the SynthOS community**

*SynthOS is an independent project not affiliated with Fedora Project or Red Hat.*

</div>

---

## 📚 Documentation

Full, detailed docs live in **`docs/`** — **start at [docs/ALL-DOCS.md](docs/ALL-DOCS.md)**
(two-generation index) or, for the operations readers, **[docs/INDEX.md](docs/INDEX.md)**.

Key entry points:

| Want to… | Read |
|---|---|
| verify everything | `docs/README.md` (and run `configs/tests/verify.sh`) |
| build the repo | `docs/BUILD.md`, `docs/PACKAGING.md`, `docs/RUNBOOK.md` |
| use the assistant console | `docs/AIOS.md` |
| the Mint/Bazzite-style updater | `docs/UPDATER.md` |
| safe perf tuning | `docs/PERFORMANCE.md` |
| security posture | `docs/SECURITY.md` |
| the daemons | `docs/DAEMONS.md` |
| assemble the ISO | `docs/ISO.md`, `docs/KICKSTARTS.md` |
| contribute | `docs/CONTRIBUTING.md`, `docs/ROADMAP.md` |
| all docs (both generations) | `docs/ALL-DOCS.md` |
