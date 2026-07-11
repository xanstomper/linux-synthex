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

---

## 🧠 Brain OS — AI-Native Runtime Layer (2026.10 New)

SynthOS 2026.10 "Ignition" introduces **Brain OS** — a suite of tightly integrated AI
daemons and secure execution primitives that make SynthOS the first Linux distribution
with a genuine AI-native runtime as part of its core system layer.

### synthex-brain — AI Consciousness Daemon
The central AI orchestration daemon. Manages long-running inference sessions, routes
requests from all other AI daemons, and exposes a D-Bus API
(`org.synthex.Brain`) for query, streaming completions, and model lifecycle
management. Connects to local Ollama, remote OpenAI-compatible endpoints, or both.
Model switching is zero-downtime; hot-swappable from the Control Center.

### synthex-agent-sandbox — Secure AI Execution Environment
Sandboxed execution environment for AI-generated code and autonomous agent tasks.
Uses Linux namespaces, seccomp-BPF filters, AppArmor profiles, and a custom
capability whitelist (`ImplicitPolicyTarget`) to isolate agent processes from the
host system. Compatible with the OpenAI tool-calling API surface.

### synthex-workspace-ai — Multi-Workspace AI Coordinator
Bridges the AI layer with KDE Plasma workspaces. Tracks per-workspace context,
automatically switches AI personas (coding assistant, research mode, creative mode)
based on the active workspace profile, and manages KWin integration for
AI-triggered window arrangements.

### synthex-hermes — AI Agent Daemon
The outbound agent runner. Executes multi-step autonomous tasks delegated by
`synthex-brain` — web search, file operations, API calls — inside the
`synthex-agent-sandbox`. Exposes a D-Bus service (`org.synthex.Hermes`) and a
REST gateway on `localhost:7430`.

### synthex-neural-ipc — Ultra-Fast IPC Bus
Zero-copy, lock-free shared-memory message bus (`/dev/shm/synthex-neural-bus`)
for sub-microsecond latency communication between all Brain OS components.
64 KiB × 256 slots ring buffer; D-Bus façade available for sandboxed consumers.
Benchmark: >2 M msg/s on a modern desktop CPU.

---

## 🔒 Security Additions (2026.10)

### Paranoid Mode (`synthex-paranoid`)
Extreme-hardening toggle for high-security sessions:
- Disables all USB ports except pre-approved serial numbers via `/sys/bus/usb/`
- Full network packet logging to encrypted rotating logs (`/var/log/synthex/paranoid/`)
- File integrity monitoring of critical system paths with SHA-256 baseline
- Screenshot auditing — periodic screenshots saved for the session record
- USB and network policy enforced with `iptables` + `usbguard`
- Encrypted audit trail at `/var/log/synthex/paranoid/paranoid.log`
- CLI: `synthex-paranoid [enable|disable|status|log|add-usb|add-ip]`
- Desktop notification integration via `notify-send --urgency=critical`
- Automatic threat response (lock screen, kill suspicious PIDs)

### Encrypted Vault (`synthex-vault`)
Auto-mounting LUKS2 encrypted container:
- Creates `~/.synthex-vault.img` (configurable size, default 512 MiB)
- LUKS2 with Argon2id KDF, AES-256-XTS cipher, 512-bit key
- PAM hook: auto-mounts on login via `/etc/pam.d/common-session`
- DBus watch on `org.freedesktop.ScreenSaver`: auto-unmounts on screen lock
- `~/Vault/` symlink to mount point for seamless access
- Idle auto-close after 600 s of no filesystem activity
- CLI: `synthex-vault [create SIZE|open|close|status|install-pam]`

---

## 🎮 Gaming Additions (2026.10)

### Game Optimizer (`synthex-game-optimizer`)
Per-game automatic performance tuning daemon:
- Monitors running processes every 2 s against a database of 60+ game profiles
- On game launch: sets CPU governor to `performance`, enables GameMode, suspends
  background services (baloo_file, tracker-miner-fs-3, synthex-update-manager),
  applies GPU performance mode (NVIDIA/AMD auto-detected), sets network QoS via `tc`
- On game exit: restores all settings automatically
- Profile database: `gaming/game-profiles.json` — 60+ titles with per-game env vars,
  Steam App IDs, and optimisation notes
- CLI: `synthex-game-optimizer [start|stop|status|list-games|add-game]`

### Game Profiles (`gaming/game-profiles.json`)
Machine-readable profile database covering 60+ titles including CS2, Dota 2,
Cyberpunk 2077, Elden Ring, Baldur's Gate 3, Path of Exile 2, Apex Legends,
Satisfactory, Factorio, Minecraft, Valheim, and more — each with Steam App ID,
recommended env vars (DXVK_ASYNC, __GL_THREADED_OPTIMIZATIONS, mesa_glthread, etc.),
network QoS priority, and human-readable optimisation notes.

---

## 🎯 Focus Mode (`synthex-focus`)
Distraction-free work environment with integrated binaural beats:
- **Binaural beat generator** — pure Python, zero external deps:
  - Focus: 40 Hz gamma (200 Hz / 240 Hz stereo)
  - Relax: 10 Hz alpha (200 Hz / 210 Hz stereo)
  - Sleep: 4 Hz theta (200 Hz / 204 Hz stereo)
  - Writes WAV via `wave` + `struct`, plays via paplay/aplay/ffplay
- **Do Not Disturb** — KDE Plasma inhibit API, GNOME banners off, dunst/mako SIGSTOP
- **App suspension** — SIGSTOP configurable distracting apps on focus start, SIGCONT on end
- **Pomodoro timer** — 25-min focus / 5-min break, `notify-send` countdown alerts, bell sound
- **DBus service** — `org.synthex.FocusMode`: Start/Stop/GetStatus/TakeBreak
- **Session log** — `~/.local/share/synthex/focus-history.json`
- CLI: `synthex-focus [start MINS|stop|status|break] [--mode focus|relax|sleep] [--no-binaural]`

---

## 🔮 Predictive Launcher (`synthex-predict`)
ML-based app pre-launching for instant application start:
- Records every app launch: timestamp, day of week, hour, currently open apps
- Trains a Markov chain model on usage history (pure Python, no ML frameworks)
- State: (day_of_week, time_period, open_apps_set) → transition probabilities
- Predictions with probability > threshold (default 0.6) are pre-forked with SIGSTOP
- When user actually launches the predicted app: SIGCONT → instant start
- Pre-forked apps auto-killed after 30 minutes if unused
- **DBus**: `org.synthex.Predictive` — GetPredictions, RecordLaunch, SetThreshold, GetStats
- **Accuracy tracking** — logs prediction hit rate to history
- CLI: `synthex-predict [start|stop|status|predict|stats|clear-history]`
