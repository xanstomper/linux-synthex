# SynthOS 2026.10 — Packager's Guide

> **TL;DR for CI/build systems:** clone → `make rust` → `make ks-validate` → `make iso EDITION=plasma`

---

## What you're packaging

| Component | Path | Purpose |
|-----------|------|---------|
| **ISO images** (×5) | `build/out/SynthOS-*.iso` | Bootable live+install media |
| **RPM packages** (×139) | `packages/spec-files/*.spec` | All SynthOS components |
| **Source tarballs** (×3) | `~/rpmbuild/SOURCES/*.tar.gz` | installer / branding / desktop |
| **Rust binaries** (×32) | `target/release/synthex-*` | System daemons & UI apps |

---

## Critical paths

```
linux-synthex/
├── build/kickstart/           5 Anaconda KS files (pass ksvalidator)
├── branding/grub/themes/      GRUB2 dark-amber theme (PNG + PF2 fonts)
├── branding/plymouth/         Boot splash (Rust spinner, amber logo)
├── desktop/sddm/              SDDM login theme (QML + QML Components)
├── installer/
│   ├── config/settings.conf   Calamares 23-module exec sequence
│   └── modules/synthex*/      9 custom Python modules (2,000+ lines)
├── packages/spec-files/       139 RPM specs
├── src/                       Rust/Python/QML source tree
└── .github/workflows/         7-job CI (rust/ks/spec/py/theme/iso/release)
```

---

## ISO editions

| Edition | KS file | DE | Approx size |
|---------|---------|-----|------------|
| `plasma`    | `synthex-plasma.ks`    | KDE Plasma 6    | ~3.2 GB |
| `hyprland`  | `synthex-hyprland.ks`  | Hyprland WM     | ~2.8 GB |
| `gnome`     | `synthex-gnome.ks`     | GNOME 47        | ~3.0 GB |
| `gaming`    | `synthex-gaming.ks`    | KDE + gaming    | ~3.8 GB |
| `minimal`   | `synthex-minimal.ks`   | CLI only        | ~900 MB |

---

## Validated checks (53/53 pass)

```
BOOTCHAIN        5 kickstarts  •  GRUB theme  •  Plymouth  •  SDDM
INSTALLER        9 Calamares modules  •  branding  •  settings.conf
DESKTOP UI       Welcome • OOBE • Control Center • Gaming Center
                 Software Center • App Manager
RUST             32 binaries built release
PACKAGES         139 RPM specs  •  59 systemd units
DOCS             README • CHANGELOG • RELEASE-NOTES • build-guide
```

---

## Quick build commands

```bash
# Validate kickstarts only (no build dependencies needed)
make ks-validate

# Build Rust workspace (requires cargo)
make rust

# Build single ISO (requires lorax + livemedia-creator)
make iso EDITION=plasma VERSION=2026.10

# Build all 5 editions in parallel (~6h, ~100 GB disk)
make iso-all VERSION=2026.10

# Full release bundle
make release VERSION=2026.10
```

---

## Repository layout

```
linux-synthex/
├── Cargo.toml            Rust workspace (27 crates)
├── Makefile              Top-level build targets
├── README.md
├── CHANGELOG.md
├── .github/workflows/build.yml   CI/CD (7 jobs)
├── src/                  Source tree
│   ├── synthex-agent/    Python AI daemon + Codex IDE + Hermes tray
│   ├── synthex-system-daemon/  Rust core (D-Bus, profile, services)
│   ├── synthex-desktopd/ Rust desktop orchestrator
│   ├── synthex-hwdaemon/ Rust hardware monitor (SMART, thermals)
│   ├── synthex-welcome/  First-run wizard (QML + Rust launcher)
│   ├── synthex-oobe/     Installer OOBE profile picker
│   ├── synthex-control-center/  Main settings hub (QML)
│   ├── synthex-gaming-center/   Gaming hub (QML)
│   ├── synthex-software-center/ Software manager (QML)
│   ├── synthex-app-manager/     App catalogue (QML)
│   └── ... (18 more crates)
├── installer/
│   ├── config/           Calamares settings + module configs
│   ├── modules/          9 custom Python modules
│   └── scripts/          Post-install shell scripts
├── branding/
│   ├── calamares/        Slideshow QML + strings + logo
│   ├── grub/themes/synthex/   GRUB2 theme
│   ├── plymouth/theme/   Boot splash
│   └── desktop-profiles/ KDE look-and-feel per profile
├── desktop/
│   ├── sddm/synthex-sddm-theme/  Login manager theme
│   ├── plasma/           KDE Plasma config
│   └── profiles/         9 desktop profile JSON definitions
├── packages/
│   ├── spec-files/       139 RPM spec files
│   └── services-systemd/ 20 additional service units
├── build/
│   ├── kickstart/        5 Anaconda kickstart files
│   └── scripts/          ISO build pipeline scripts
└── docs/
    ├── RELEASE-NOTES-2026.10.md
    ├── INSTALL-ARCHITECTURE.md
    ├── build-guide.md
    └── PACKAGER-README.md    ← YOU ARE HERE
```

---

## Dependency graph (install order)

```
synthex-kernel-headers
  └─ synthex-kernel
       └─ synthex-firmware
            └─ synthex-core          ← base system config
                 ├─ synthex-branding ← GRUB + Plymouth + SDDM themes
                 ├─ synthex-desktop  ← KDE Plasma profile + defaults
                 ├─ synthex-installer← Calamares + 9 custom modules
                 ├─ synthex-gaming   ← gaming-specific stack
                 ├─ synthex-cursors  ← Bibata-Modern-Amber cursor set
                 └─ synthex-sounds   ← notification sound theme
```

---

## GPG / signing

Production ISOs are signed with key `0x5B3F…4A2C` (team@synthex-os.org).
Verify:
```bash
gpg --import docs/synthex-signing-key.asc
gpg --verify SynthOS-2026.10-plasma-x86_64.iso.asc
```

---

## CDN / mirrors

| Region | URL |
|--------|-----|
| Primary (EU) | `https://cdn.synthex-os.org/releases/` |
| Mirror (US)  | `https://mirror-us.synthex-os.org/releases/` |
| Mirror (AP)  | `https://mirror-ap.synthex-os.org/releases/` |
| GitHub CDN   | `https://github.com/synthex-os/linux-synthex/releases/` |

---

## Known packaging gotchas

1. **GRUB font** — `font-regular.pf2` is pre-built (shipped binary).
   If you need to rebuild it: `grub2-mkfont -s 14 -o font-regular.pf2 NotoSans-Regular.ttf`

2. **Plymouth theme** — must be in `/usr/share/plymouth/themes/synthex/` and
   registered with `plymouth-set-default-theme synthex` in post-install.

3. **SDDM** — place theme in `/usr/share/sddm/themes/synthex-sddm-theme/` then
   set `Current=synthex-sddm-theme` in `/etc/sddm.conf.d/synthex.conf`.

4. **Calamares branding** — `branding.desc` path must match the `branding` key
   in `settings.conf` exactly: `synthex`.

5. **Rust binaries** — built with `cargo build --release`, NOT `--debug`.
   Strip symbols for production: `strip target/release/synthex-*`

---

*SynthOS Team — team@synthex-os.org — https://synthex-os.org*
