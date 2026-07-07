# Synthex Rust Architecture

## Overview

Synthex adopts Rust as a primary systems language alongside C and C++. Rust
provides memory safety guarantees, modern tooling, and growing kernel ecosystem
support. This document outlines how Rust fits into the Synthex stack.

## Rust Components

### Layer 1: Kernel (Rust-for-Linux)

Since Linux 6.14, Rust is upstream in the kernel. Synthex enables this with:

- `CONFIG_RUST=y` in kernel config
- `rustc >= 1.80.0` as a build dependency
- Rust kernel driver support (PHY abstractions)
- Future: Rust GPU drivers (Asahi-style), NVMe, filesystem drivers

**Kernel config:** `kernel/config-x86_64` (Rust section at line 864)

### Layer 2: Rust Utility Suite (User-Facing)

Modern replacements for classic Unix tools, all written in Rust:

| Tool | Replaces | Spec File |
|------|----------|-----------|
| `ripgrep` (rg) | `grep` | `packages/spec-files/rust-utils-ripgrep.spec` |
| `fd-find` (fd) | `find` | `packages/spec-files/rust-utils-fd.spec` |
| `bat` | `cat` | `packages/spec-files/rust-utils-bat.spec` |
| `eza` | `ls` | `packages/spec-files/rust-utils-eza.spec` |
| `dust` | `du` | `packages/spec-files/rust-utils-dust.spec` |
| `bottom` (btm) | `htop` | `packages/spec-files/rust-utils-bottom.spec` |
| `sd` | `sed` | `packages/spec-files/rust-utils-sd.spec` |

These are available via the `synthex-rust-tools` package group.

### Layer 3: Synthex Native Rust Tools

System management tools written in Rust for Synthex:

| Tool | Purpose | Source |
|------|---------|--------|
| `synthex-update-manager` | DNF5 wrapper with BTRFS snapshots | `src/synthex-rust-tools/synthex-update-manager/` |
| `synthex-driver-manager` | GPU detection and driver install | `src/synthex-rust-tools/synthex-driver-manager/` |
| `synthex-pkg` (`spkg`) | Package manager with Synthex repo awareness | `src/synthex-rust-tools/synthex-pkg/` |

| `synthex-system-daemon` | Performance auto-tuner (VRR, HDR, CPU, TDP, form factor) | `src/system-daemon/` |
| `synthex-cli` | Unified `synthex` CLI (info, hardware, gpu, status) | `src/synthex-cli/` |

### Layer 4: RPM Specs

| **Toolchain:** `packages/spec-files/rust-toolchain.spec` — rustc + cargo + std + src
| **Rust Utilities:** `packages/spec-files/rust-utils-*.spec` (17 specs)
| | Tool | Replaces | Spec |
| |------|----------|------|
| | ripgrep (rg) | grep | `rust-utils-ripgrep.spec` |
| | fd-find (fd) | find | `rust-utils-fd-find.spec` |
| | bat | cat | `rust-utils-bat.spec` |
| | eza | ls | `rust-utils-eza.spec` |
| | dust | du | `rust-utils-dust.spec` |
| | bottom (btm) | htop | `rust-utils-bottom.spec` |
| | sd | sed | `rust-utils-sd.spec` |
| | starship | prompt | `rust-utils-starship.spec` |
| | zellij | tmux | `rust-utils-zellij.spec` |
| | git-delta | diff | `rust-utils-delta.spec` |
| | procs | ps | `rust-utils-procs.spec` |
| | hyperfine | benchmark | `rust-utils-hyperfine.spec` |
| | dog | dig | `rust-utils-dog.spec` |
| | bandwhich | nethogs | `rust-utils-bandwhich.spec` |
| | dua-cli | du (interactive) | `rust-utils-dua-cli.spec` |
| | gping | ping (graphical) | `rust-utils-gping.spec` |
| | just | make | `rust-utils-just.spec` |
| | helix | modal text editor | `rust-utils-helix.spec` |
| | nushell (nu) | modern shell | `rust-utils-nushell.spec` |
| | zoxide | smarter cd | `rust-utils-zoxide.spec` |
| | atuin | shell history sync | `rust-utils-atuin.spec` |
| | tealdeer | tldr client | `rust-utils-tealdeer.spec` |
| | ouch | compression CLI | `rust-utils-ouch.spec` |
- **Native Tools:** `packages/spec-files/synthex-update-manager.spec`, `synthex-driver-manager.spec`, `synthex-pkg.spec`
- **System Daemon:** `packages/spec-files/synthex-system-daemon.spec`
- **AI Daemon:** `packages/spec-files/synthex-ai-daemon.spec`
| **Tool** | **Type** | **Spec** |
|----------|----------|----------|
| synthex-ai-daemon | AI assistant (Rust) | `synthex-ai-daemon.spec` |
| synthex-installer-detect | HW auto-detector (Rust) | `synthex-installer-detect.spec` |

### Layer 5: COSMIC Desktop (Pop!_OS Rust Port)

Port of System76's COSMIC desktop environment — a full Rust-based Wayland desktop using the Iced GUI toolkit.

| **Component** | **Package** | **Purpose** | **Spec** |
|---|---|---|---|
| cosmic-comp | Wayland compositor | GPU-accelerated compositor with tiling/stacking | `cosmic-comp.spec` |
| cosmic-bg | Background daemon | Wallpaper and background management | `cosmic-bg.spec` |
| cosmic-panel | Desktop panel | Bar with launcher, workspaces, system tray | `cosmic-panel.spec` |
| cosmic-app-library | App launcher | Searchable application grid | `cosmic-app-library.spec` |
| cosmic-randr | Display config | xrandr replacement in Rust | `cosmic-randr.spec` |
| cosmic-osd | On-screen display | Volume, brightness, media OSD | `cosmic-osd.spec` |
| cosmic-notifications | Notification daemon | Desktop notifications (XDG spec) | `cosmic-notifications.spec` |
| cosmic-epoch | Login greeter | PAM-based Wayland greeter | `cosmic-epoch.spec` |
| cosmic-settings | Settings app | Full graphical settings with 12+ categories | `cosmic-settings.spec` |
| cosmic-term | Terminal emulator | GPU-accelerated terminal with split panes, tabs | `cosmic-term.spec` |
| cosmic-files | File manager | Dual-pane file browser with preview, search | `cosmic-files.spec` |
| cosmic-text-editor | Text editor | Modern GUI editor with syntax highlighting | `cosmic-text-editor.spec` |
| cosmic-workspaces | Workspace manager | Virtual desktop overview with exposé | `cosmic-workspaces.spec` |
| xdg-desktop-portal-cosmic | Portal backend | Flatpak/Snap file chooser, screen share, print | `xdg-desktop-portal-cosmic.spec` |
| cosmic-applets | Desktop applets | System monitor, clock, network, power, weather | `cosmic-applets.spec` |
| cosmic-screenshot | Screenshot tool | Screenshot + screen recording with annotations | `cosmic-screenshot.spec` |

### Layer 6: CI/CD

- `.github/workflows/rust-build.yml` — cargo fmt, clippy, build, test, audit
- `.github/workflows/validate-specs.yml` — rpmlint on all spec files

## Version Policy

- **Toolchain:** Track upstream stable (currently 1.80.0), updated per Fedora release cycle
- **Utilities:** Latest stable from upstream GitHub releases
- **Synthex Tools:** Pinned to releases tagged in the synthex-linux repo

## Dependency Graph

```
rust-toolchain (rustc + cargo + std)
├── ripgrep (rg)
├── fd-find (fd)
├── bat
├── eza
├── dust
├── bottom (btm)
├── sd
├── synthex-update-manager
├── synthex-driver-manager
└── synthex-pkg
```

## Future Rust Candidates

- **synthex-hwdaemon** — hardware detection daemon (currently C)
- **synthex-desktopd** — desktop layout/theme engine (currently C++)
- **synthex-gpu-setupd** — GPU driver auto-installer (currently C)
- **synthex-stored** — software center backend (currently C++)
- **synthex-agent** — desktop AI agent daemon
- **kernel Rust GPU drivers** — as they mature upstream
- **Calamares installer modules** — auto-detect GPU/filesystem/laptop profile
- **VRR/HDR auto-detection** — display capability polling daemon
