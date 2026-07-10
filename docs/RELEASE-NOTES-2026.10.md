# SynthOS 2026.10 — "Ignition" Release Notes

**Release Date:** October 2026  
**Codename:** Ignition  
**Version:** 2026.10  
**Branch:** Stable (LTS-Revision)

---

## What's New in 2026.10 "Ignition"

### 🌟 Highlights

- **New SDDM Login Theme** — Dark navy/amber gold login screen with glassmorphism card, 
  session selector (Wayland/X11/Plasma/Hyprland/GNOME), keyboard layout picker, and 
  power controls. Ships as `sddm-theme-synthex`.

- **Animated Plymouth Boot Splash** — Spinning amber sun logo with progress bar and 
  full disk-encryption password dialog. Now works across all GPU configurations.

- **Setup Wizard (OOBE) v2** — Redesigned Out-Of-Box Experience with 6-step wizard:
  Welcome → Profile → Theme → App Bundles → App Picker → Finish. Selections are 
  applied on first login via `synthex-firstboot.service`.

- **7-Slide Calamares Installer Slideshow** — Full SynthOS branding in the installer 
  with amber/navy color scheme covering Gaming, Dev, AI, Security, and Community slides.

- **GRUB2 Theme + Custom Boot Entries** — `/etc/grub.d/40_synthex` adds Recovery, 
  Safe-Graphics, and Previous-Kernel submenu entries with amber-highlighted menu.

---

### 🎮 Gaming

- Steam Proton GE (latest) pre-installed alongside Valve Proton
- Gamescope compositor v3.14+ with VRR/HDR support
- MangoHUD v0.7.x with Synthex default HUD config
- BORE scheduler in default kernel (`kernel-synthex`)
- GameMode daemon v1.8 pre-enabled for all users
- `synthex-gaming-mode` big-picture launcher via keyboard shortcut
- GPU auto-detection: NVIDIA (proprietary + open), AMD (amdgpu), Intel (i915/xe)
- Heroic Games Launcher + Lutris + Bottles for non-Steam stores
- Prism Launcher for Minecraft (Java + Bedrock via Geyser)

### 💻 Desktop & UI

- KDE Plasma 6.2 (Wayland-first)
- Synthex Plasma Theme: 6 color variants (Graphite, Midnight, Frost, Latte, Mint, Amber)
- KDE Global Theme: Synthex with matching SDDM/Plymouth/GRUB
- 7 Desktop Profiles: Classic, Gaming, Focus, Pro, Studio, AI, Lite
- Custom Kirigami-native Welcome app (`synthex-welcome`)
- Synthex Control Center for all system settings
- Per-profile widget layouts applied on first login

### 🤖 AI Features

- Ollama v0.4+ with Llama 3.3 8B pulled on AI-profile activation
- `synth ai` shell command: plain-English terminal assistant
- Whisper voice command integration
- SynthAI tray widget for quick queries
- Zero telemetry — all AI processing is local by default

### 🛡 Security

- SELinux enforcing by default (Fedora base policies)
- SynthGuard IDS daemon with anomaly alerting
- Firewalld + nftables pre-configured
- LUKS2 with Argon2id KDF (installer option)
- Secure Boot signed bootloader (shim + grub2)
- AppArmor profiles for browsers and media apps
- DNS-over-HTTPS via systemd-resolved (Cloudflare + Quad9)
- `synthex-security-dashboard` GUI for security posture

### ⚡ Performance

- `kernel-synthex` based on Fedora kernel + BORE + FUTEX2 + HDR patches
- ZRAM swap (8GB, zstd) enabled by default on ≥4GB RAM systems
- Auto-NUMA balancing enabled
- `irqbalance` tuned for desktop workloads  
- Transparent Huge Pages: `madvise` mode
- CPU governor: `schedutil` (switches to `performance` in Gaming Mode)
- I/O scheduler: `mq-deadline` (NVMe: `none`)
- Network: `bbr` TCP congestion control + `fq` qdisc

### 🔧 Developer Tools

- Rust 1.80+ (stable) via rustup bootstrap
- Python 3.12 with pip, pyenv, virtualenv
- Node.js 22 LTS + Bun 1.1
- Docker Engine + Podman + Buildah (rootless)
- VS Code (Flatpak) + Neovim with Synthex config
- Git 2.45+ with delta pager and custom Synthex gitconfig
- `synthex-ujust` — Synthex-flavored `ujust` task runner
- Containerized dev environments via `synthex-devbox`

### 📦 Package Management

- DNF5 as default package manager
- Flathub pre-configured (full catalog)
- SynthAUR helper for AUR packages
- AppImage support via `synthex-appimage` daemon
- Synthex Software Center (native + Flatpak + AppImage unified)

---

## Known Issues

- **Nvidia + Wayland**: Cards older than RTX 2000 may experience flickering on 
  Wayland. Workaround: use X11 session or pass `nvidia-drm.modeset=1` to kernel.
- **GRUB theme on pure-EFI systems**: may require manually running 
  `grub2-mkconfig -o /boot/efi/EFI/fedora/grub.cfg` after install.
- **OOBE on Wayland without QML runner**: if `qml6`/`qmlscene` isn't installed, 
  wizard falls back to notification-only mode. Run `sudo dnf install qt6-qtdeclarative` to fix.
- **Plymouth on NVIDIA proprietary**: must have `nvidia-drm.modeset=1` in kernel 
  cmdline for animated splash. Added by default in new installs.

---

## Installation

### Minimum Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU       | x86_64 dual-core | 4+ cores |
| RAM       | 4 GB    | 16 GB     |
| Storage   | 25 GB   | 60 GB SSD |
| GPU       | Any with KMS | Discrete GPU |
| Network   | Optional (offline install supported) | Broadband |

### Download
- **KDE Plasma Edition**: `synthex-plasma-2026.10-x86_64.iso` (≈3.2 GB)
- **Hyprland Edition**: `synthex-hyprland-2026.10-x86_64.iso` (≈2.8 GB)
- **GNOME Edition**: `synthex-gnome-2026.10-x86_64.iso` (≈3.0 GB)
- **Minimal Edition**: `synthex-minimal-2026.10-x86_64.iso` (≈900 MB)

Verify your download:
```bash
sha256sum -c synthex-plasma-2026.10-x86_64.iso.sha256
```

### Writing to USB
```bash
sudo dd if=synthex-plasma-2026.10-x86_64.iso of=/dev/sdX bs=4M status=progress
sync
```

Or use `synthex-usb-writer` (GUI) on an existing SynthOS/Linux system.

---

## Upgrade from 2026.07

```bash
sudo synth upgrade          # Recommended: Synthex upgrade manager
# or
sudo dnf system-upgrade download --releasever=2026.10
sudo dnf system-upgrade reboot
```

---

## Community & Support

| Resource | URL |
|----------|-----|
| Website  | https://synthex-os.org |
| Forum    | https://discuss.synthex-os.org |
| Bug Tracker | https://github.com/synthex-linux/issues |
| Discord  | https://discord.gg/synthex |
| Matrix   | #synthex:matrix.org |
| Release Archives | https://synthex-os.org/releases |

---

## Credits

SynthOS is built by the community. Special thanks to:
- The Fedora Project for the upstream base
- KDE Community for Plasma 6
- The gaming Linux community (GloriousEggroll, ferzol, many others)
- All contributors on GitHub

---

*© 2026 SynthOS Project — GPL-3.0+ Licensed*
