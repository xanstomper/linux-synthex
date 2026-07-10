# SynthOS Build Guide

## Quick Start

```bash
# Clone and enter project
git clone https://github.com/synthex-os/linux-synthex
cd linux-synthex

# 1. Build all Rust binaries
cargo build --release

# 2. Build a specific ISO edition
VERSION=2026.10 EDITION=plasma bash build/scripts/build-iso.sh

# 3. Build all editions
make iso-all VERSION=2026.10
```

## Prerequisites

### Build Host Requirements
- Fedora 40+ or RHEL 9+ (recommended); other RPM-based distros work
- 16 GB RAM minimum (32 GB recommended for parallel ISO builds)
- 100 GB free disk space
- Rust 1.78+ (`rustup install stable`)
- Python 3.11+

### Required Packages
```bash
sudo dnf install -y \
    lorax livemedia-creator \
    pykickstart ksvalidator \
    xorriso isomd5sum \
    grub2-tools grub2-efi-x64 \
    shim-x64 \
    squashfs-tools \
    calamares calamares-libs \
    python3-pyaml python3-jsonschema \
    rpm-build rpmdevtools \
    inkscape grub2-tools
```

## Build Stages

### Stage 1: Rust Workspace
```bash
cargo build --release --workspace
# Produces 32 binaries in target/release/
```

### Stage 2: RPM Packages
```bash
# Set up RPMbuild tree
rpmdev-setuptree

# Create source tarballs
tar czf ~/rpmbuild/SOURCES/synthex-installer-2026.10.tar.gz installer/
tar czf ~/rpmbuild/SOURCES/synthex-branding-2026.10.tar.gz  branding/
tar czf ~/rpmbuild/SOURCES/synthex-desktop-2026.10.tar.gz   desktop/

# Build all packages (noarch + binary)
for spec in packages/spec-files/*.spec; do
    rpmbuild -ba "$spec" \
        --define "_sourcedir $(pwd)" \
        --define "_rpmdir build/rpms" \
        --define "_srcrpmdir build/srpms" || true
done
```

### Stage 3: Repo Setup
```bash
# Create local DNF repo from built RPMs
mkdir -p build/repo
find build/rpms -name "*.rpm" -exec cp {} build/repo/ \;
createrepo_c build/repo/
```

### Stage 4: ISO Build
```bash
# Validate kickstart files first
bash build/scripts/prepare-kickstart.sh all --validate-only

# Build Plasma edition ISO
VERSION=2026.10 EDITION=plasma bash build/scripts/build-iso.sh

# Build all editions (requires ~50 GB + 6h on modern hardware)
make iso-all VERSION=2026.10
```

### Stage 5: Signing (optional)
```bash
# Sign the ISO with GPG
gpg --detach-sign --armor build/out/SynthOS-2026.10-plasma-x86_64.iso
sha256sum build/out/SynthOS-2026.10-*.iso > build/out/SHA256SUMS
gpg --clearsign build/out/SHA256SUMS
```

## Edition Matrix

| Edition | Desktop | Approx. Size | Kernel args |
|---------|---------|-------------|-------------|
| plasma | KDE Plasma 6 | ~3.2 GB | quiet splash |
| hyprland | Hyprland WM | ~2.8 GB | nvidia_drm.modeset=1 |
| gnome | GNOME 47 | ~3.0 GB | quiet splash |
| gaming | KDE + gaming stack | ~3.8 GB | amd_pstate=active mitigations=off |
| minimal | CLI only | ~900 MB | quiet |

## Repo Structure

```
linux-synthex/
├── Cargo.toml                    # Rust workspace root
├── Makefile                      # Top-level build targets
├── src/                          # All source code
│   ├── synthex-agent/            # Python AI assistant daemon
│   ├── synthex-system-daemon/    # Rust core system daemon
│   ├── desktopd/                 # Rust desktop orchestrator
│   ├── hwdaemon/                 # Rust hardware monitor
│   └── ...                       # 25+ other crates/packages
├── installer/
│   ├── config/settings.conf      # Calamares master sequence
│   ├── modules/synthex*/         # 9 custom installer modules
│   └── scripts/post-install/     # Shell scripts run after install
├── packages/spec-files/          # 139 RPM spec files
├── build/
│   ├── kickstart/                # 5 Anaconda KS files
│   └── scripts/                  # ISO build pipeline scripts
├── branding/
│   ├── calamares/                # Installer slideshow + strings
│   ├── grub/themes/synthex/      # GRUB bootloader theme
│   └── plymouth/theme/           # Boot splash theme
└── desktop/
    ├── plasma/                   # KDE Plasma configuration
    ├── sddm/                     # SDDM login manager theme
    └── profiles/                 # Desktop profile JSONs
```

## Troubleshooting

### `livemedia-creator` fails with "no space left"
```bash
# Increase tmpfs or point WORK_DIR to a real partition
export WORK_DIR=/var/tmp/synthex-build
```

### GRUB theme fonts missing at ISO build time
```bash
grub2-mkfont -s 14 -o branding/grub/themes/synthex/font-regular.pf2 \
    /usr/share/fonts/google-noto/NotoSans-Regular.ttf
```

### Kickstart validation errors
```bash
ksvalidator build/kickstart/synthex-plasma.ks
# Or use the prepare script:
bash build/scripts/prepare-kickstart.sh all --validate-only
```

## CI/CD

The project ships a `build.yml` GitHub Actions workflow that:
1. Builds the Rust workspace on every push
2. Validates all kickstart files
3. Runs `--validate-iso` checks on ISOs (size, SHA, GPG)
4. Publishes release ISOs to CDN on tagged releases
