# Synthex Build Guide

> **Audience:** Developers, release engineers, ISO builders  
> **Last updated:** July 2026  
> **Synthex version:** 4.6 "Fortitude"

---

## Table of Contents

1. [Setting Up Build Environment](#1-setting-up-build-environment)
2. [Building from Source](#2-building-from-source)
3. [Building the Kernel](#3-building-the-kernel)
4. [Building Packages](#4-building-packages)
5. [Building ISOs](#5-building-isos)
6. [Testing ISOs](#6-testing-isos)
7. [Custom ISO Creation](#7-custom-iso-creation)
8. [Build Automation (GitHub Actions)](#8-build-automation-github-actions)
9. [Publishing Process](#9-publishing-process)
10. [Build Troubleshooting](#10-build-troubleshooting)

---

## 1. Setting Up Build Environment

### 1.1 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 4 cores | 16+ cores |
| **RAM** | 8 GB | 32 GB |
| **Storage** | 100 GB | 500 GB+ (SSD) |
| **Network** | Broadband | Fast broadband (many sources to download) |
| **OS** | Synthex 4.6+ | Synthex 4.6+ (or compatible RPM-based distro) |

### 1.2 Install Build Dependencies

```bash
# Core build tools
sudo dnf5 group install "Development Tools"
sudo dnf5 install git git-lfs curl wget

# Build system tools
sudo dnf5 install make cmake meson ninja-build autoconf automake libtool
sudo dnf5 install ccache          # Compiler cache (speeds up rebuilds)
sudo dnf5 install mock            # Clean build chroot

# ISO building tools
sudo dnf5 install lorax          # Live image creation
sudo dnf5 install isomd5sum      # ISO checksums
sudo dnf5 install syslinux       # Bootloader for ISO

# Package management tools
sudo dnf5 install rpm-build rpmdevtools rpmlint spectool
sudo dnf5 install createrepo     # Repository metadata
sudo dnf5 install dnf5-plugins-core

# Container/virtualization for testing
sudo dnf5 install podman qemu-kvm virt-manager

# Python tooling
sudo dnf5 install python3 python3-pip python3-virtualenv
python3 -m pip install --user sphinx sphinx-rtd-theme
```

### 1.3 Set Up Directory Structure

```bash
# Create workspace
mkdir -p ~/synthex-build/{src,pkgs,iso,cache}
cd ~/synthex-build

# Clone all repositories
git clone https://github.com/synthex-project/packages.git
git clone https://github.com/synthex-project/synthex-build.git
git clone https://github.com/synthex-project/linux.git
git clone https://github.com/synthex-project/artwork.git
git clone https://github.com/synthex-project/docs.git

# Configure ccache for faster rebuilds
mkdir -p ~/.ccache
cat >> ~/.bashrc << 'EOF'
export CCACHE_DIR="$HOME/.ccache"
export CCACHE_SIZE="50G"
export USE_CCACHE=1
EOF
source ~/.bashrc
```

### 1.4 Configure Mock for Synthex

```bash
# Create Synthex mock configuration
# (see building-packages.md for detailed setup)
sudo mkdir -p /etc/mock/
cat << 'EOF' | sudo tee /etc/mock/synthex-x86_64.cfg
config_opts['root'] = 'synthex-x86_64'
config_opts['target_arch'] = 'x86_64'
config_opts['legal_host_arches'] = ['x86_64']
config_opts['chroot_setup_cmd'] = 'install @buildsys-build'
config_opts['dist'] = 'synthex'
config_opts['releasever'] = '4'
# ... add repository config
EOF

# Add your user to mock group
sudo usermod -aG mock $USER
# Log out and back in
```

### 1.5 Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export SYNTHEX_TOP="$HOME/synthex-build"
export SYNTHEX_PACKAGES="$SYNTHEX_TOP/packages"
export SYNTHEX_BUILD="$SYNTHEX_TOP/synthex-build"
export SYNTHEX_ISO="$SYNTHEX_TOP/iso"
export PATH="$HOME/.local/bin:$PATH"
```

---

## 2. Building from Source

### 2.1 Overview

Building Synthex from source involves:
1. Building all packages from RPM spec files
2. Assembling a repository
3. Creating installation ISO images

### 2.2 Building Packages

See [Building Packages Guide](building-packages.md) for detailed instructions.

```bash
# Quick start:
cd ~/synthex-build/packages

# Build a single package
make <package-name>

# Build with parallel jobs
make -j$(nproc)

# Build in mock (clean chroot)
mock -r synthex-x86_64 --rebuild ~/rpmbuild/SRPMS/package-1.0.0-1.src.rpm
```

### 2.3 Building the Package Repository

```bash
# Build all packages (takes a long time)
cd ~/synthex-build/packages
make -j$(nproc) 2>&1 | tee build.log

# After build, create repository metadata
cd ~/synthex-build/pkgs
createrepo .

# This creates repodata/ directory with metadata
ls repodata/
# → repomd.xml
# → primary.xml.gz
# → filelists.xml.gz
# → other.xml.gz
```

### 2.4 Using Local Repository

```bash
# Add local repository to DNF
sudo tee /etc/yum.repos.d/local-synthex.repo <<EOF
[local-synthex]
name=Local Synthex Build
baseurl=file:///home/$USER/synthex-build/pkgs
enabled=1
gpgcheck=0
priority=50
EOF

# Now you can install packages from your local build
sudo dnf5 install <your-package>
```

---

## 3. Building the Kernel

### 3.1 Kernel Sources

```bash
# Clone the Synthex kernel repository
cd ~/synthex-build
git clone https://github.com/synthex-project/linux.git
cd linux

# Check branches
git branch -a
# → master (current Synthex kernel)
# → synthex-6.x (version branches)

# View kernel configuration
ls config/
# → kernel-x86_64.config
# → kernel-aarch64.config
```

### 3.2 Building the Kernel

```bash
# Set up build directory
cd ~/synthex-build/linux
mkdir -p build

# Configure kernel (using Synthex config)
make O=build defconfig
cp config/kernel-x86_64.config build/.config
make O=build olddefconfig  # Apply default settings for any new options

# Build the kernel
make O=build -j$(nproc)

# Build modules
make O=build modules -j$(nproc)

# Install modules (to temporary directory)
make O=build modules_install INSTALL_MOD_PATH=/tmp/kernel-install

# Install kernel
sudo make O=build install

# Expected build time:
# - Clean build: 10-60 minutes (depending on CPU)
# - Incremental: 1-5 minutes
```

### 3.3 Custom Kernel Configuration

```bash
# Menu-based configuration
make O=build menuconfig

# Save configuration
cp build/.config config/kernel-x86_64.custom.config

# Diff against default
diff config/kernel-x86_64.config config/kernel-x86_64.custom.config | less
```

### 3.4 Kernel Packaging

```bash
# Build RPM packages from kernel
cd ~/synthex-build/linux
make O=build rpm-pkg

# RPMs are in:
ls ~/rpmbuild/RPMS/x86_64/kernel-*
# → kernel-<version>.x86_64.rpm
# → kernel-devel-<version>.x86_64.rpm
# → kernel-headers-<version>.x86_64.rpm

# Install custom kernel
sudo dnf5 install ~/rpmbuild/RPMS/x86_64/kernel-<version>.x86_64.rpm
```

### 3.5 Kernel Module Signing

```bash
# Generate signing key
openssl req -new -x509 -newkey rsa:2048 -keyout kernel.key \
  -out kernel.pem -days 3650 -subj "/CN=Synthex Kernel/"

# Configure kernel to use the key
scripts/config --file build/.config \
  --set-str CONFIG_SYSTEM_TRUSTED_KEYS "kernel.pem"
scripts/config --file build/.config \
  --set-str CONFIG_MODULE_SIG_KEY "kernel.pem"

# Build and modules will be signed automatically
make O=build -j$(nproc)
make O=build modules_install -j$(nproc)
```

### 3.6 Kernel Testing

```bash
# Test in virtual machine
sudo dnf5 install qemu-kvm virt-manager
# Create VM and boot with custom kernel

# Benchmark
sudo dnf5 install stress-ng perf
stress-ng --cpu 0 --timeout 60s
sudo perf stat -a -- sleep 10

# Check kernel messages
dmesg | tail -20

# Verify modules load
lsmod | head -20
```

---

## 4. Building Packages

See [Building Packages Guide](building-packages.md) for comprehensive instructions.

### 4.1 Quick Build Reference

```bash
# Build a package
cd ~/synthex-build/packages
make <package-name>

# Build in mock
mock -r synthex-x86_64 --rebuild <package>.src.rpm

# Build and install locally
make <package-name> && sudo dnf5 install ../RPMS/x86_64/<package>-*.rpm

# Build dependency tree
make <package-name>-dep-tree
```

### 4.2 Building Package Groups

```bash
# Build a group of packages
cd ~/synthex-build/packages

# Build all packages needed for desktop
make @desktop-plasma

# Build all packages (full distro)
make

# Build with specific architecture
make ARCH=x86_64
make ARCH=aarch64
```

### 4.3 Package Build Monitoring

```bash
# Build only failed packages
make retry-failed

# Show build status
make status

# Clean and rebuild
make clean-<package-name>
make <package-name>

# Build log
less /var/log/synthex-build/<package>.log
```

---

## 5. Building ISOs

### 5.1 ISO Build System Overview

Synthex uses **lorax** (Live OS creation tools) + custom scripts to build ISOs:

```
┌────────────────────────────────────────────────────────────────┐
│                    ISO BUILD PROCESS                            │
│                                                                │
│  1. Package Repository                                         │
│     └─ Built packages assembled into a repository              │
│                                                                │
│  2. lorax (livemedia-creator)                                  │
│     └─ Creates squashfs filesystem from repository             │
│        with kernel, initramfs, and base system                 │
│                                                                │
│  3. ISO Assembly                                               │
│     └─ Combines:                                               │
│        • squashfs.img (live filesystem)                        │
│        • Kernel + initramfs (boot/ directory)                  │
│        • EFI bootloader (GRUB)                                 │
│        • isolinux (BIOS boot)                                  │
│        • Boot config files (grub.cfg, isolinux.cfg)            │
│        • splash images                                         │
│        • Package manifest                                      │
│                                                                │
│  4. ISO Finalization                                           │
│     └─ Create hybrid ISO (works for USB + DVD)                │
│        • isohybrid                                            │
│        • implantisomd5 (checksum)                              │
│        • GPG signature                                         │
└────────────────────────────────────────────────────────────────┘
```

### 5.2 Install ISO Building Tools

```bash
sudo dnf5 install lorax lorax-lmc-nouveau lorax-lmc-virt
sudo dnf5 install genisoimage isomd5sum syslinux
sudo dnf5 install grub2 grub2-efi-x64 shim
sudo dnf5 install pykickstart   # Kickstart parsing
```

### 5.3 Kickstart Configuration

The build is controlled by a kickstart file:

```bash
# Example: synthex-plasma.ks
cat ~/synthex-build/synthex-build/config/synthex-plasma.ks

# Key sections:
# - Keyboard/language settings
# - Package selection (groups and individual packages)
# - Services to enable/disable
# - Post-install scripts
# - Default configuration files
```

### 5.4 Building the ISO

```bash
# Set up build environment
cd ~/synthex-build/synthex-build

# Build the ISO
sudo ./build-iso.sh \
  --edition plasma \
  --version 4.6 \
  --arch x86_64 \
  --repo file:///home/$USER/synthex-build/pkgs \
  --output ~/synthex-build/iso/

# The script performs:
# 1. Validates repository
# 2. Creates rootfs using lorax
# 3. Builds squashfs filesystem
# 4. Assembles ISO with GRUB
# 5. Creates hybrid ISO
# 6. Generates checksums

# Expected output:
~/synthex-build/iso/
├── Synthex-4.6-Plasma.iso
├── Synthex-4.6-Plasma.iso.sha256
├── Synthex-4.6-Plasma.iso.sig
└── Synthex-4.6-Plasma.iso.torrent
```

### 5.5 Build Options

```bash
# Available editions
./build-iso.sh --edition plasma      # KDE Plasma desktop
./build-iso.sh --edition gnome        # GNOME desktop
./build-iso.sh --edition budgie       # Budgie desktop
./build-iso.sh --edition mate         # MATE desktop
./build-iso.sh --edition minimal      # CLI only

# Other options
./build-iso.sh --arch aarch64         # ARM 64-bit
./build-iso.sh --no-compress          # Skip squashfs compression (faster)
./build-iso.sh --debug                # Verbose logging
./build-iso.sh --keep-temp            # Keep temporary files

# Custom package list
./build-iso.sh --package-list my-packages.ks
```

### 5.6 ISO Build Decomposition

```bash
# Step-by-step ISO creation (for debugging):

# 1. Create root filesystem
sudo livemedia-creator \
  --make-iso \
  --ks synthex-plasma.ks \
  --lorax-templates /usr/share/lorax/live/ \
  --no-virt \
  --resultdir /tmp/iso-build/ \
  --project "Synthex" \
  --releasever 4.6

# 2. Build squashfs
sudo mksquashfs /tmp/iso-build/rootfs/ \
  /tmp/iso-build/LiveOS/squashfs.img \
  -comp zstd -b 1M

# 3. Create bootable ISO
sudo mkisofs -o Synthex-4.6-Plasma.iso \
  -b isolinux/isolinux.bin \
  -c isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  -eltorito-alt-boot \
  -e images/efiboot.img \
  -no-emul-boot \
  -R -J -v -T \
  /tmp/iso-build/

# 4. Make hybrid (USB bootable)
sudo isohybrid Synthex-4.6-Plasma.iso

# 5. Add ISO checksum
sudo implantisomd5 Synthex-4.6-Plasma.iso
```

### 5.7 ISO Package Manifest

```bash
# Extract package list from an existing ISO
sudo mount -o loop Synthex-4.6-Plasma.iso /mnt/iso
cat /mnt/iso/Packages-*  # Package manifest
# → Contains list of all packages in the ISO
sudo umount /mnt/iso
```

---

## 6. Testing ISOs

### 6.1 Automated Testing in QEMU/KVM

```bash
#!/bin/bash
# test-iso.sh - Test Synthex ISO in VM

ISO="$1"
VM_NAME="synthex-test"
RAM=4096
CPUS=4
DISK_SIZE=20G

# Create test disk
qemu-img create -f qcow2 /tmp/$VM_NAME.qcow2 $DISK_SIZE

# Run VM
qemu-system-x86_64 \
  -name $VM_NAME \
  -m $RAM \
  -smp $CPUS \
  -boot d \
  -cdrom $ISO \
  -drive file=/tmp/$VM_NAME.qcow2,format=qcow2 \
  -vga virtio \
  -display gtk \
  -enable-kvm \
  -netdev user,id=net0 \
  -device virtio-net,netdev=net0 \
  -usb \
  -device usb-tablet
```

### 6.2 ISO Validation Tests

```bash
# 1. Verify checksum
sha256sum -c Synthex-4.6-Plasma.iso.sha256

# 2. Verify GPG signature
gpg --verify Synthex-4.6-Plasma.iso.sig Synthex-4.6-Plasma.iso

# 3. Check ISO structure
isoinfo -l -i Synthex-4.6-Plasma.iso

# 4. Verify hybrid boot
sudo isohybrid --entry-test Synthex-4.6-Plasma.iso

# 5. Test install with virt-install
sudo virt-install \
  --name synthex-test \
  --memory 4096 \
  --vcpus 4 \
  --disk size=20 \
  --cdrom Synthex-4.6-Plasma.iso \
  --os-variant generic
```

### 6.3 Automated Testing with openQA (Optional)

For comprehensive automated testing:

```bash
# openQA is an automated testing framework
# https://openqa.opensuse.org/

# Setup requires:
# - openQA server
# - Worker machines
# - Test definitions (needle matching)
```

### 6.4 Manual Testing Checklist

```
☐ Boot from ISO (UEFI and BIOS)
☐ Language/keyboard selection works
☐ Timezone detection correct
☐ Partitioning (automatic, manual, LUKS)
☐ User creation
☐ Installation completes
☐ Boot from installed system
☐ GRUB menu displays correctly
☐ Login works
☐ Desktop starts properly
☐ Network (wired + Wi-Fi)
☐ Sound output
☐ Display resolution correct
☐ Package manager works (dnf5)
☐ Software Center works
☐ Flatpak works
☐ Snapshot/rollback works
☐ Suspend/resume
☐ All hardware detected (GPU, storage, etc.)
```

---

## 7. Custom ISO Creation

### 7.1 Creating a Custom Edition

```bash
# 1. Create custom kickstart
cat > ~/synthex-build/custom.ks << 'EOF'
# Custom Synthex Edition Kickstart

lang en_US.UTF-8
keyboard us
timezone UTC

# Partitioning
autopart --type=lvm
clearpart --all --initlabel

# Repositories
repo --name=synthex --baseurl=file:///home/$USER/synthex-build/pkgs

# Package selection
%packages
@base
@desktop-plasma
@development
firefox
code
steam
kdenlive
gimp
ibreoffice
-neverball
-ksudoku
%end

# Services
services --enabled=NetworkManager,firewalld,sshd

# Post-install
%post
# Custom branding
sed -i 's/Synthex/MyDistro/g' /etc/os-release
# Add your configurations
echo "Custom setup complete"
%end
EOF

# 2. Build custom ISO
sudo ./build-iso.sh \
  --kickstart custom.ks \
  --edition custom \
  --version 1.0 \
  --output ~/synthex-build/iso/
```

### 7.2 Custom Branding

```bash
# Replace Synthex branding with your own
cd ~/synthex-build/artwork

# Edit files:
# - grub/        → Boot splash
# - sddm/        → Login screen
# - plasma/      → Desktop theme
# - wallpapers/  → Default wallpaper
# - icons/       → Distribution icon

# Rebuild artwork package
cd ~/synthex-build/packages
make synthex-artwork
```

### 7.3 Custom Package Repository

```bash
# 1. Build your packages
cd ~/synthex-build/packages
make my-custom-package

# 2. Create repository
cd ~/synthex-build/pkgs
createrepo .

# 3. Sign repository
gpg --detach-sign --armor repodata/repomd.xml

# 4. Add repository to ISO kickstart
# custom.ks:
# repo --name=custom --baseurl=https://my-repo.example.com/synthex
```

### 7.4 Pre-Configured ISO

For pre-configured installations (enterprise, education):

```bash
# Create pre-seeded configuration
mkdir -p ~/synthex-build/live-overlay/etc
mkdir -p ~/synthex-build/live-overlay/home/liveuser

# Add pre-configured settings
cp my-config.conf ~/synthex-build/live-overlay/etc/

# Build with overlay
sudo ./build-iso.sh \
  --overlay ~/synthex-build/live-overlay \
  --preset my-enterprise-config
```

### 7.5 ISO with Pre-Installed Packages

```bash
# Create ISO that includes extra packages
# by modifying the kickstart %packages section

%packages
@base
@desktop-plasma
# Add all packages you want pre-installed
docker
docker-compose
python3-pandas
python3-numpy
jupyter-notebook
code
# Exclude unnecessary packages
-akregator
-kmag
%end
```

---

## 8. Build Automation (GitHub Actions)

### 8.1 Workflow Overview

```yaml
# .github/workflows/build.yml
name: Synthex Build and Test

on:
  push:
    branches: [master, 'release/*']
  pull_request:
    branches: [master]

jobs:
  build-packages:
    runs-on: ubuntu-latest
    container:
      image: synthexproject/build:latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Install build dependencies
      run: |
        dnf5 install -y rpm-build mock git
    
    - name: Build package
      run: |
        make -j$(nproc) ${{ matrix.package }}
    
    - name: Run rpmlint
      run: |
        rpmlint *.rpm
    
    - name: Store artifacts
      uses: actions/upload-artifact@v4
      with:
        name: rpms
        path: '*.rpm'
  
  build-iso:
    needs: build-packages
    runs-on: ubuntu-latest
    container:
      image: synthexproject/iso-builder:latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build ISO
      run: |
        ./build-iso.sh \
          --edition plasma \
          --version 4.6-nightly \
          --repo file:///github/workspace/pkgs
    
    - name: Test ISO
      run: |
        # Run VM-based tests
        virt-install --cdrom Synthex-4.6-*.iso ...
    
    - name: Store ISO
      uses: actions/upload-artifact@v4
      with:
        name: iso
        path: '*.iso'
```

### 8.2 Build Container Setup

```dockerfile
# Dockerfile for build container
FROM synthex:latest

# Install build tools
RUN dnf5 install -y \
    rpm-build \
    mock \
    git \
    make \
    cmake \
    gcc \
    gcc-c++ \
    && dnf5 clean all

# Set up mock
RUN usermod -aG mock builduser

# Create build user
RUN useradd -m builduser
USER builduser
WORKDIR /home/builduser
```

### 8.3 Nightly Build Pipeline

```yaml
# .github/workflows/nightly.yml
name: Nightly Build

on:
  schedule:
    - cron: '0 2 * * *'  # Every day at 02:00 UTC

jobs:
  build:
    runs-on: [self-hosted, linux, x64]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Build all packages
      run: |
        make -j$(nproc) 2>&1 | tee build.log
    
    - name: Build ISO
      run: |
        ./build-iso.sh \
          --edition plasma \
          --version $(date +%Y%m%d)-nightly
    
    - name: Run tests
      run: |
        make test-all
    
    - name: Upload to nightly repo
      run: |
        rsync -avz pkgs/ ${{ secrets.NIGHTLY_REPO_URL }}/
```

### 8.4 CI/CD Pipeline for Packages

```yaml
# .github/workflows/package-ci.yml
name: Package CI

on:
  pull_request:
    paths:
      - 'packages/**/*.spec'

jobs:
  validate-and-build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Check changed packages
      id: changed
      run: |
        git fetch origin ${{ github.base_ref }}
        CHANGED=$(git diff --name-only origin/${{ github.base_ref }}...HEAD \
          | grep '/.*\.spec$' \
          | sed 's|packages/./||' \
          | sed 's|/.*.spec||' \
          | sort -u)
        echo "packages=$CHANGED" >> $GITHUB_OUTPUT
    
    - name: rpmlint check
      run: |
        for pkg in ${{ steps.changed.outputs.packages }}; do
          rpmlint packages/${pkg:0:1}/$pkg/$pkg.spec
        done
    
    - name: Build in mock
      run: |
        for pkg in ${{ steps.changed.outputs.packages }}; do
          mock -r synthex-x86_64 \
            --buildsrpm \
            --spec packages/${pkg:0:1}/$pkg/$pkg.spec \
            --sources packages/${pkg:0:1}/$pkg/
        done
```

### 8.5 Self-Hosted Build Server

For large-scale builds, consider setting up a dedicated build server:

```bash
# Build server requirements:
# - Fast CPU (32+ cores recommended)
# - Large RAM (64 GB+)
# - Fast storage (NVMe RAID)
# - Gigabit+ network

# Install build tools
sudo dnf5 install koji               # Fedora build system (optional)
sudo dnf5 install copr-cli           # Copr integration
sudo dnf5 install jenkins            # Alternative CI server
```

---

## 9. Publishing Process

### 9.1 Release Checklist

```
☐ All packages build successfully
☐ ISO builds without errors
☐ ISO passes smoke tests
☐ ISO installs cleanly
☐ All critical bugs fixed
☐ Release notes written
☐ Version bumped in all places
☐ GPG signatures generated
☐ Checksums generated
☐ Mirrors updated
☐ Announcement prepared
```

### 9.2 Signing the Release

```bash
# Import release signing key
gpg --import synthex-release-key.gpg

# Sign the ISO
gpg --detach-sign --armor Synthex-4.6-Plasma.iso

# Sign the checksum file
gpg --clearsign Synthex-4.6-Plasma.iso.sha256

# Verify
gpg --verify Synthex-4.6-Plasma.iso.sig Synthex-4.6-Plasma.iso
```

### 9.3 Generate Checksums

```bash
# Generate SHA256 checksums
sha256sum Synthex-4.6-Plasma.iso > Synthex-4.6-Plasma.iso.sha256

# Generate SHA1 (for compatibility)
sha1sum Synthex-4.6-Plasma.iso > Synthex-4.6-Plasma.iso.sha1

# Generate BLAKE2 (modern)
b2sum Synthex-4.6-Plasma.iso > Synthex-4.6-Plasma.iso.b2

# Verify checksums
sha256sum -c Synthex-4.6-Plasma.iso.sha256
```

### 9.4 Create Torrent

```bash
# Create BitTorrent metadata
sudo dnf5 install transmission-cli
transmission-create \
  -o Synthex-4.6-Plasma.iso.torrent \
  -t https://tracker.getsynthex.org/announce \
  -s 4194304 \
  Synthex-4.6-Plasma.iso

# Trackers:
# - https://tracker.getsynthex.org/announce
# - udp://tracker.opentrackr.org:1337
# - https://tracker.torrent.eu.org:451
```

### 9.5 Upload to Mirrors

```bash
# Upload to primary mirror
rsync -avP \
  Synthex-4.6-Plasma.iso* \
  mirror@mirror.getsynthex.org:/srv/mirrors/synthex/iso/

# Generate mirror list
cat > MIRRORS.txt <<EOF
Primary:
  https://mirrors.getsynthex.org/iso/

Community mirrors:
  https://mirror.rackspace.com/synthex/iso/
  https://mirror.aarnet.edu.au/pub/synthex/iso/
  http://mirror.math.princeton.edu/pub/synthex/iso/
EOF
```

### 9.6 Announcement

```bash
# Update website
# Edit: synthex-website/content/download.md
# Add new version to downloads page

# Update get.synthex.us redirect
# Point latest ISO link to new version

# Announce on:
# - Synthex Forums (discuss.getsynthex.org)
# - Synthex Blog
# - Reddit /r/SynthexProject
# - Twitter/X @SynthexProject
# - DistroWatch
# - Phoronix (tip them)
```

---

## 10. Build Troubleshooting

### 10.1 Common Build Failures

| Symptom | Cause | Solution |
|---------|-------|----------|
| `No space left on device` | /tmp or build directory full | Clean cache: `sudo dnf5 clean all`, `rm -rf /tmp/synthex-build*` |
| `Failed to connect to repository` | Network issue or mirror down | Check `/etc/yum.repos.d/` configs, use different mirror |
| `Missing BuildRequires` | Dependency not installed | `sudo dnf5 builddep package.spec` |
| `Conflicting requests` | Dependency conflict | Check for circular deps or version conflicts |
| `Patch failed` | Patch no longer applies | Refresh patches for new upstream version |
| `Segmentation fault in %check` | Test failing in mock chroot | Set `%bcond_with check` in spec to disable tests temporarily |
| `Filesystem is full` during ISO build | ISO build temp files grew too large | `--keep-temp false`, clean `/var/tmp/lmc/` |
| `Kernel panic` in test VM | Bad kernel config or modules | Check kernel .config, ensure necessary drivers are built-in (not modules) |

### 10.2 Debugging Build Scripts

```bash
# Enable verbose build output
make V=1 <package-name>

# Run build step by step
make <package-name>-prep     # Unpack and patch
make <package-name>-build    # Compile
make <package-name>-install  # Install to buildroot
make <package-name>-check    # Run tests

# Show build commands without executing
make -n <package-name>
```

### 10.3 Mock Debugging

```bash
# Keep chroot after failure
mock -r synthex-x86_64 --rebuild <package>.src.rpm --no-cleanup-after

# Shell into chroot
mock -r synthex-x86_64 --shell

# Inside chroot, inspect:
cd /builddir/build/
ls BUILD/     # Source directory
ls BUILDROOT/ # Install root
cat build.log # Build log
cat root.log  # Root installation log
cat state.log # State log

# Copy files out of chroot
mock -r synthex-x86_64 --copyout /builddir/build/RPMS/ .
```

### 10.4 ISO Build Debugging

```bash
# Check ISO contents
isoinfo -l -i Synthex-4.6-Plasma.iso

# Extract ISO contents
mkdir /tmp/iso-contents
sudo mount -o loop Synthex-4.6-Plasma.iso /tmp/iso-contents
ls -la /tmp/iso-contents/
# → LiveOS/          (squashfs)
# → boot/            (kernel, initrd, GRUB)
# → EFI/             (UEFI bootloader)
# → isolinux/        (BIOS bootloader)
# → Packages-*       (package manifest)
sudo umount /tmp/iso-contents

# Check squashfs
unsquashfs -l /tmp/iso-contents/LiveOS/squashfs.img | head -50
```

### 10.5 Cleaning Up

```bash
# Clean build artifacts
cd ~/synthex-build
rm -rf cache/
rm -rf packages/BUILD/
rm -rf packages/BUILDROOT/
rm -rf packages/RPMS/
rm -rf packages/SRPMS/

# Clean mock cache
mock -r synthex-x86_64 --clean

# Clean DNF cache
sudo dnf5 clean all

# Clean ISO build temp
sudo rm -rf /var/tmp/lmc/
sudo rm -rf /tmp/iso-build/

# Clean ccache (if rebuilds needed with different flags)
ccache -C
```

---

## Appendix A: Build Command Quick Reference

```bash
# Package building
make <package>              # Build a package
make -j$(nproc)             # Parallel build all packages
make clean-<package>        # Clean package artifacts
make status                 # Build status

# ISO building
./build-iso.sh --edition <e>  # Build ISO
sudo lorax ...                # Root filesystem creation

# Mock
mock -r synthex-x86_64 --rebuild <pkg>.src.rpm  # Clean rebuild
mock -r synthex-x86_64 --shell                    # Interactive chroot

# Repository
createrepo .                # Create repo metadata
sudo dnf5 builddep pkg.spec # Install build deps

# ISO tools
isoinfo -l -i <iso>         # List ISO contents
isohybrid <iso>             # Make USB-bootable
implantisomd5 <iso>         # Add embedded checksum

# Testing
virt-install ...            # VM installation test
sha256sum -c <file>.sha256  # Verify checksum
gpg --verify <file>.sig     # Verify signature
```

## Appendix B: Build Optimization

```bash
# Use tmpfs for fast builds (if you have enough RAM)
sudo mount -t tmpfs -o size=32G tmpfs /tmp
# Add to /etc/fstab:
tmpfs /tmp tmpfs defaults,noatime,mode=1777,size=32G 0 0

# Use local mirror for source downloads
# /etc/dnf/dnf.conf: fastestmirror=1

# Parallel downloads
# /etc/dnf/dnf.conf: max_parallel_downloads=10

# Pre-populate ccache with common builds
ccache -F 0     # Unlimited cache files
ccache -M 50G   # 50 GB cache size

# Use mold linker (much faster than GNU ld)
sudo dnf5 install mold
# Set as default: export LDFLAGS="-fuse-ld=mold"
```

## Appendix C: Build Outputs Reference

```
~/synthex-build/
├── packages/           # Package source repository
│   ├── packages/       # Spec files
│   ├── BUILD/          # Build directories
│   ├── RPMS/           # Binary RPMs
│   │   ├── x86_64/
│   │   └── noarch/
│   └── SRPMS/          # Source RPMs
├── pkgs/               # Combined repository
│   └── repodata/       # Repository metadata
├── iso/                # ISO output
│   ├── Synthex-4.6-*.iso
│   ├── *.sha256
│   └── *.sig
└── cache/              # Build cache (ccache, etc.)
```
