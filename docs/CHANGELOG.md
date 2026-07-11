# Changelog — SynthOS Linux

All notable changes to SynthOS are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2026.10 "Ignition"] — 2026-10-01 — UNRELEASED

### Added
- **5 desktop editions**: Plasma, GNOME, Hyprland, Gaming, Minimal
- **Calamares installer** with 31 custom Python/QML modules
  - Hardware detection (GPU, CPU, RAM, storage)
  - GPU driver configuration (NVIDIA/AMD/Intel auto-detect)
  - Desktop profile picker (9 profiles)
  - App bundle picker (60+ curated apps via Flatpak)
  - BTRFS subvolume partitioning with encryption
  - Plymouth boot splash configuration
  - Full GRUB2 theme integration
  - SDDM theme and auto-login configuration
  - First-boot OOBE wizard (7-step welcome flow)
  - Locale, timezone, keyboard, user account setup
  - Network/WiFi configuration module
  - Services-systemd enable/disable module
  - Security hardening module (SELinux, SSH, firewall)
  - Unpack-fs and shellprocess modules
  - Sliding branding slideshow (7 slides, auto-advance)
- **SynthOS Control Center** — unified Qt6/QML system hub
  - Gaming Center page (MangoHud, GameMode, GPU boost)
  - App Manager page (Flatpak + DNF unified catalogue)
  - Performance Advisor page (CPU governor, TDP tuning)
  - Driver Assistant page (NVIDIA/AMD/Intel management)
  - AI Hub page (Hermes integration, Ollama management)
  - Security Dashboard page (SELinux, firewall, audit)
  - Disk Health page (SMART, BTRFS scrub, snapshots)
  - Software Center page
  - Snapshot Manager page (BTRFS timeshift-like)
  - Update Manager page (DNF + Flatpak + firmware)
  - RGB & Peripherals page (OpenRGB integration)
  - Log Viewer page (journald, structured viewer)
  - System Report page
- **Hermes AI Assistant** — native desktop AI daemon
  - D-Bus service (`org.synthex.Hermes`)
  - Ollama backend (LLaMA 3.2 default, CodeLlama optional)
  - System tray integration
  - Task-aware context (current app, file, clipboard)
  - Hermes IDE bridge (D-Bus → editor protocol)
- **Synthex Agent** — background automation daemon
  - Coordinator, runner, provider, dispatcher sub-systems
  - Native D-Bus service (`org.synthex.Agent`)
  - Performance advisor integration
  - Safety: dnf-protect.py stub, agent sandboxing
- **SynthOS SDDM theme** — dark amber login screen
  - Session selector (Plasma/Hyprland/GNOME)
  - Animated Plymouth boot splash
  - Hardware-detection-gated GPU info display
- **Plymouth theme** — animated boot splash
  - Spinner + progress bar + logo animation
  - Smooth fade-in/out transitions
  - OEM/branding aware
- **GRUB2 theme** — dark amber/navy aesthetic
  - Custom fonts (Noto Sans), background SVG
  - Boot menu with edition badges
  - Recovery and safe graphics entries
  - Amber gold `#FFB300` accent color
- **GRUB configuration script** — `grub-setup.sh`
  - Detects UEFI/BIOS, sets appropriate defaults
  - Embeds kernel parameters (quiet splash mitigations=auto)
  - BTRFS-aware (`rootflags=subvol=@`)
  - Writes `40_synthex` custom entry
- **synthex-kernel** — hardened Fedora kernel
  - BORE CPU scheduler patches
  - FUTEX2 patches
  - HDR patches (2 sets)
  - ZRAM + zstd compression by default
  - Custom Cachy-OS tuning (sched, vm, net)
  - 10Gbps network defaults
  - Kernel hardening via sysctl
- **64 RPM spec files** — complete package graph
  - synthex-core, synthex-kernel, synthex-base
  - synthex-branding, synthex-firmware, synthex-cursors
  - synthex-grub-theme, synthex-plymouth-theme
  - All desktop edition meta-packages
  - Gaming: synthex-gaming-core, synthex-gaming-packages
  - AI: synthex-ai-hub, synthex-agent, synthex-hermes
  - All 34 Rust tool specs
  - synthex-sounds, synthex-wallpapers
- **34 Rust crates** — compiled native tooling
  - synthex-system-daemon (IPC bus, hardware monitor)
  - synthex-app-manager (Flatpak/DNF bridge)
  - synthex-control-center (Qt6 QML host)
  - synthex-gaming-center (GPU/MangoHud/GameMode)
  - synthex-update-manager (DNF + Flatpak + LVFS)
  - synthex-snapshot-manager (BTRFS snapshots)
  - synthex-disk-health (SMART + BTRFS scrub)
  - synthex-log-viewer (journald + structured)
  - synthex-security-dashboard (SELinux + firewall)
  - synthex-nvidia-installer (auto NVIDIA driver)
  - synthex-performance-benchmark (GPU/CPU/memory)
  - synthex-cachu-tuning (kernel performance tuning)
  - synthex-cli (ujust-based CLI interface)
  - synthex-stored (persistent key-value store)
  - synthex-welcome (OOBE welcome wizard host)
  - synthex-identity (SynthOS branding/version)
  - synthex-theme (theme application engine)
  - synthex-software-center (app discovery)
  - synthex-service-manager (systemd service UI)
  - synthex-webapp-engine (web app hosting)
  - synthex-workspace (workspace/profile manager)
  - synthex-wine-manager (Wine/Proton manager)
  - synthex-compat-db (compatibility database)
  - synthex-tray (system tray daemon)
  - synthex-hwdaemon (hardware event daemon)
  - synthex-term (terminal emulator wrapper)
  - synthex-recovery (system recovery tools)
  - synthex-perf-tuning (performance tuning daemon)
  - synthex-codec-installer (media codec setup)
  - synthex-nobara-fixes (Nobara compatibility patches)
  - synthex-rust-tools (driver-manager, pkg, update-manager)
  - synthex-firstuser (first-user setup service)
  - synthex-sandbox (application sandboxing)
  - synthex-ujust (ujust-based task runner)
- **9 desktop profiles** — JSON-driven profile system
  - Classic (Windows-like), Gaming, Focus, Studio
  - Pro, AI Workstation, Lite, Minimal, Dolphin
- **Post-install scripts** — `post-install.sh`
  - GPU driver auto-apply
  - SDDM theme configuration
  - Flatpak app installation from profile
  - GRUB rebuild
  - Plymouth update
  - First-boot service enablement
- **Security hardening** — `synthex-securitysetup.py`
  - SELinux enforcing configuration
  - SSH hardening (ed25519, no passwords, fail2ban)
  - Firewalld zones and rules
  - AppArmor profile loading
  - sysctl hardening (kernel, net, vm namespaces)
  - Optional LUKS2 full-disk encryption at install
  - ClamAV integration
  - Automatic security updates (dnf-automatic)
  - Audit framework (auditd rules)
- **Network setup** — NetworkManager configuration module
  - DNS-over-HTTPS configuration
  - Connection save/restore
  - Bluetooth configuration
  - MDNS/Avahi integration
- **Calamares branding** — `synthex-branding`
  - 7-slide animated installer slideshow (QML)
  - Synthex logo, icon, welcome.png
  - Branding descriptor with all URLs
  - Calamares settings.conf (complete)
- **Build pipeline** — `build/scripts/`
  - `build-iso.sh` — 10-stage parallel ISO builder
  - `build-synthex-kernel.sh` — kernel RPM builder
  - `validate-iso.sh` — ISO completeness validator
  - `prepare-kickstart.sh` — kickstart pre-processor
  - `release.sh` — full release pipeline (CDN upload, SHA256, GPG tag)
  - `gen-grub-assets.sh` — GRUB PNG generator
  - `build-all.sh` — orchestrate all 8 editions
- **GitHub Actions CI/CD** — `.github/workflows/build.yml`
  - Parallel 8-edition ISO builds
  - Kickstart validation
  - RPM spec linting
  - Rust `cargo build --release`
  - Python test suite
  - ISO size/structure validation
  - Automated CDN upload on tag
- **ujust task runner** — `Justfile` (300 lines)
  - System, GPU, Gaming, Desktop, AI, Security recipes
  - Developer build recipes
  - Container management (Distrobox)
  - Health check recipe
- **Documentation** — `docs/`
  - `INSTALL-ARCHITECTURE.md` — complete installer architecture
  - `RELEASE-NOTES-2026.10.md` — comprehensive release notes
  - `build-guide.md` — developer build instructions
  - `security-guide.md` — security hardening guide
  - `getting-started.md` — user quickstart
  - `installation-guide.md` — step-by-step install
  - `developer/` — API docs, contributing guide

### Changed
- Fedora 42 base → SynthOS-hardened kernel replaces stock
- DNF configured with fastest mirrors + deltarpm + parallel downloads
- BTRFS default filesystem (replaces ext4 default)
- ZRAM enabled by default (zstd, 150% RAM)
- SELinux enforcing by default
- Gaming-specific kernel parameters pre-configured

### Security
- LUKS2 encryption supported at install time
- SELinux targeted enforcing by default  
- SSH: ed25519 only, PermitRootLogin no, fail2ban enabled
- Firewalld enabled with public zone defaults
- Kernel hardening: unprivileged user namespaces restricted
- Automatic security updates via dnf-automatic

---

## [Pre-release / Development] — 2025–2026

Initial development of SynthOS Linux project.
Architecture design, Rust crate scaffolding, build system setup.

---

*SynthOS is an independent project not affiliated with Fedora Project or Red Hat.*
*© 2026 Synthex Team <team@synthex-os.org>*
*Licensed under GPL-3.0-or-later*
