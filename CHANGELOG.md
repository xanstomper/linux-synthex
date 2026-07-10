# SynthOS Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/) · Versioning: Calendar (`YYYY.MM`)

---

## [2026.10] — "Ignition" — 2026-10-01

### 🎉 Inaugural Release

The first official SynthOS release. Everything below was built for this version.

### Added

#### Core System
- **synthex-kernel 6.12** — BORE CPU scheduler, FUTEX2, HDR color patches, ZRAM-by-default, full-disk-encryption-ready
- **synthex-system-daemon** — master D-Bus hub coordinating all SynthOS services
- **synthex-hwdaemon** — hardware detection daemon (GPU, WiFi, Bluetooth, controllers)
- **synthex-desktopd** — desktop session coordinator (profile switching, environment vars)
- **synthex-firstboot** — one-shot systemd service + graphical OOBE launcher
- **SynthGuard (synthguard)** — IDS/security monitoring daemon (Fedora-based)
- **SynthNet (synthnet)** — network configuration frontend
- **SynthVault (synthvault)** — secrets/credential manager

#### Desktop Profiles (7)
- **Classic** — Familiar Windows-like layout (taskbar, start menu, file manager)
- **Gaming** — Big Picture mode, Steam overlay, Gamescope, MangoHUD pre-configured
- **Focus** — Minimal, keyboard-driven, distraction-free (tiling-friendly)
- **Pro** — Developer cockpit: Rust, Python, Docker, VS Code, Flatpak
- **Studio** — Creative suite: Kdenlive, Krita, Blender, OBS, GIMP
- **AI Hub** — Ollama, Whisper, synth-ai shell, local LLM workspace
- **Lite** — Lightweight for older/low-RAM hardware (<4 GB RAM)

#### UI & Theming
- **SDDM login theme** — Dark navy (#080B1A) with amber gold (#FFB300) accents, glassmorphism card, session picker (Wayland/X11/Plasma/Hyprland/GNOME), keyboard layout dropdown, animated clock
- **Plymouth boot splash** — Spinning amber sun logo, animated progress bar, LUKS password prompt support
- **GRUB theme** — Dark navy background, amber selection highlight, SynthOS wordmark, automatic 1080p/4K detection
- **KDE Plasma look-and-feel** — Per-profile desktop packages (wallpaper, color scheme, layout, widgets)
- **Bibata-Modern-Classic cursors** — Bundled + Amber variant
- **SynthOS icon theme** — Extended Papirus with amber/navy overrides
- **Noto Sans** — Default system font (UI + terminal)
- **JetBrains Mono** — Default monospace/code font

#### Installer (Calamares-based)
- 7-slide animated installer slideshow (branding)
- Custom `synthexprofile` Calamares module — profile picker + app bundle selection
- Custom `synthexpostinstall` module — hardware detection, GPU driver setup, theme application, service wiring
- Post-install scripts: hardware-detect, GPU configuration (AMD/Intel/NVIDIA), GRUB setup, Plymouth setup, Flatpak setup
- Calamares branding: SynthOS logo, product name, release notes URL, support URLs
- LUKS2 full-disk encryption support (automated + manual)
- Btrfs subvolume layout: `@` (root), `@home`, `@snapshots`, `@var`
- 4 kickstart files: plasma, gaming, hyprland, minimal

#### Applications (selected via OOBE)
- **Browsers**: Firefox, Brave, Chromium, Vivaldi, Microsoft Edge
- **Messaging**: Discord, Signal, Telegram, WhatsApp, Slack, Zoom, Element
- **Office**: LibreOffice, OnlyOffice, WPS Office
- **Development**: VS Code, JetBrains Toolbox, Neovim, Zed, Cursor
- **Gaming**: Steam, Heroic, Lutris, Bottles, ProtonUp-Qt, MangoHUD, Gamescope
- **Multimedia**: Kdenlive, DaVinci Resolve, Krita, Blender, OBS, VLC, Spotify
- **AI**: Ollama, AnythingLLM, Jan.ai, GPT4All
- **Utilities**: AppImageLauncher, Flatseal, Warehouse

#### OOBE (First-Run Wizard)
- Welcome screen with profile selection (7 profiles with icons, descriptions, feature lists)
- Theme/color picker (Dark Amber, Dark Navy, Midnight Purple, Ocean Blue, Forest, Graphite)
- App bundle picker (Gaming, Development, Creative, Productivity, AI, Emulation)
- Individual app picker with search + categories
- Progress screen: Flatpak install with real-time output
- Completion screen: desktop tour link, quick-tips

#### Build System
- `Makefile` with 50+ targets: `iso-plasma`, `iso-gaming`, `packages`, `install-themes`, `validate`, `dev-container`, etc.
- `build-iso.sh` — full ISO build pipeline (livemedia-creator, isohybrid, SHA256/MD5, GPG signing)
- `build-synthex-kernel.sh` — kernel RPM builder (BORE patches, FUTEX2, HDR, dracut integration)
- `Dockerfile.rpmbuild` + `docker-compose.rpmbuild.yml` — containerized build environment
- 136 RPM spec files across all SynthOS components

#### Documentation
- `README.md` — comprehensive project overview, quick-start, structure, profiles, gaming stack
- `docs/RELEASE-NOTES-2026.10.md` — detailed "Ignition" release notes
- `docs/INSTALLER-ARCHITECTURE.md` — Calamares module architecture
- `docs/architecture/` — boot chain, AI hub, branding overview

### Changed
- N/A (inaugural release)

### Fixed
- N/A (inaugural release)

### Known Issues
- NVIDIA proprietary driver installation requires an active internet connection at install time (open-source `nouveau` is used for the live session)
- Hyprland edition: some GTK3 apps show incorrect color scheme until a re-login
- Gaming profile: MangoHUD config editor requires manual toggle on AMD Navi21+ until `lact` 0.7 is packaged
- `synthex-oobe` QML file picker requires Qt 6.5+ (pre-installed; not an issue on SynthOS itself)

### Security Notes
- SELinux enforcing by default
- SynthGuard IDS monitors `/etc`, `/usr/bin`, network connections
- DNS-over-HTTPS enabled by default (NextDNS profile; configurable)
- LUKS2 with Argon2id KDF for encrypted installs
- Firewall enabled (firewalld, `public` zone)
- SSH disabled by default; enabled via Control Center → Sharing

---

## [Unreleased]

### Planned for 2027.04 — "Nova"
- Atomic/immutable base image (OSTree or bootc)
- AI-powered hardware configuration assistant
- SynthOS App Center v2 with Flathub Reviews integration
- Per-game Gamescope preset profiles (auto-applied by game ID)
- ARM64 (aarch64) edition for Raspberry Pi 5 and Snapdragon X
- SynthOS Mobile (postmarketOS-derived) proof of concept

