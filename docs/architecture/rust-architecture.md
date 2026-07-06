# Solus Rust Architecture

## Overview

Solus adopts Rust as a primary systems language alongside C and C++. Rust
provides memory safety guarantees, modern tooling, and growing kernel ecosystem
support. This document outlines how Rust fits into the Solus stack.

## Rust Components

### Layer 1: Kernel (Rust-for-Linux)

Since Linux 6.14, Rust is upstream in the kernel. Solus enables this with:

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

These are available via the `solus-rust-tools` package group.

### Layer 3: Solus Native Rust Tools

System management tools written in Rust for Solus:

| Tool | Purpose | Source |
|------|---------|--------|
| `solus-update-manager` | DNF5 wrapper with BTRFS snapshots | `src/solus-rust-tools/solus-update-manager/` |
| `solus-driver-manager` | GPU detection and driver install | `src/solus-rust-tools/solus-driver-manager/` |
| `solus-pkg` (`spkg`) | Package manager with Solus repo awareness | `src/solus-rust-tools/solus-pkg/` |

| `solus-system-daemon` | Performance auto-tuner (VRR, HDR, CPU, TDP, form factor) | `src/system-daemon/` |
| `solus-cli` | Unified `solus` CLI (info, hardware, gpu, status) | `src/solus-cli/` |

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
- **Native Tools:** `packages/spec-files/solus-update-manager.spec`, `solus-driver-manager.spec`, `solus-pkg.spec`
- **System Daemon:** `packages/spec-files/solus-system-daemon.spec`
- **AI Daemon:** `packages/spec-files/solus-ai-daemon.spec`
| **Tool** | **Type** | **Spec** |
|----------|----------|----------|
| solus-ai-daemon | AI assistant (Rust) | `solus-ai-daemon.spec` |
| solus-installer-detect | HW auto-detector (Rust) | `solus-installer-detect.spec` |

### Layer 5: CI/CD

- `.github/workflows/rust-build.yml` — cargo fmt, clippy, build, test, audit
- `.github/workflows/validate-specs.yml` — rpmlint on all spec files

## Version Policy

- **Toolchain:** Track upstream stable (currently 1.80.0), updated per Fedora release cycle
- **Utilities:** Latest stable from upstream GitHub releases
- **Solus Tools:** Pinned to releases tagged in the solus-linux repo

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
├── solus-update-manager
├── solus-driver-manager
└── solus-pkg
```

## Future Rust Candidates

- **solus-hwdaemon** — hardware detection daemon (currently C)
- **solus-desktopd** — desktop layout/theme engine (currently C++)
- **solus-gpu-setupd** — GPU driver auto-installer (currently C)
- **solus-stored** — software center backend (currently C++)
- **solus-agent** — desktop AI agent daemon
- **kernel Rust GPU drivers** — as they mature upstream
- **Calamares installer modules** — auto-detect GPU/filesystem/laptop profile
- **VRR/HDR auto-detection** — display capability polling daemon
