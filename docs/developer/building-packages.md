# Building Packages for Solus Linux

> **Audience:** Package maintainers and developers  
> **Last updated:** July 2026  
> **Package format:** RPM (via DNF5)

---

## Table of Contents

1. [RPM Packaging Basics](#1-rpm-packaging-basics)
2. [Mock Setup and Usage](#2-mock-setup-and-usage)
3. [Copr Repository Setup](#3-copr-repository-setup)
4. [Local Build and Test](#4-local-build-and-test)
5. [Spec File Reference](#5-spec-file-reference)
6. [Patch Management](#6-patch-management)
7. [Dependency Resolution](#7-dependency-resolution)
8. [Architecture-Specific Builds](#8-architecture-specific-builds)
9. [Signing Packages](#9-signing-packages)
10. [Contributing Packages Upstream](#10-contributing-packages-upstream)

---

## 1. RPM Packaging Basics

### 1.1 What is an RPM?

RPM (RPM Package Manager) is the package format used by Solus. An RPM is a compressed archive containing:
- Binary files to install
- Metadata (name, version, dependencies)
- Scripts (pre/post install/uninstall)
- GPG signatures
- File checksums and permissions

### 1.2 Package Naming Convention

```
<name>-<version>-<release>.<architecture>.rpm
```

| Component | Description | Example |
|-----------|-------------|---------|
| **name** | Package name (lowercase, no spaces) | `firefox` |
| **version** | Upstream version (X.Y.Z) | `128.0.3` |
| **release** | Package revision (starts at 1) | `1` |
| **dist tag** | Distribution identifier | `solus` |
| **architecture** | CPU architecture | `x86_64` |

**Examples:**
```
firefox-128.0.3-1.x86_64.rpm
python3-3.12.4-1.x86_64.rpm
kernel-6.8.12-1.x86_64.rpm
```

### 1.3 RPM Directory Layout

```
$HOME/rpmbuild/
├── BUILD/            # Build directory (extracted sources)
├── BUILDROOT/        # Install root (fakeroot)
├── RPMS/             # Built binary RPMs
│   ├── x86_64/
│   ├── noarch/
│   └── aarch64/
├── SOURCES/          # Source tarballs, patches, config files
├── SPECS/            # Spec files
└── SRPMS/            # Source RPMs

# Override via ~/.rpmmacros:
%_topdir  /path/to/rpmbuild
```

### 1.4 Setting Up RPM Build Tree

```bash
# Create RPM build tree
rpmdev-setuptree

# Or manually:
mkdir -p ~/rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
```

### 1.5 Essential Tools

```bash
# Install RPM packaging tools
sudo dnf5 install rpm-build rpmdevtools rpmlint

# For spec file development
sudo dnf5 install spectool          # Download sources from spec
sudo dnf5 install rpm-sign           # Package signing

# For testing
sudo dnf5 install mock               # Build in clean chroot
```

---

## 2. Mock Setup and Usage

[Mock](https://github.com/rpm-software-management/mock) creates a clean chroot environment for building packages, ensuring builds are reproducible and isolated from your main system.

### 2.1 Install Mock

```bash
sudo dnf5 install mock
sudo usermod -aG mock $USER
# Log out and back in for group changes
```

### 2.2 Solus Mock Configuration

```bash
# Check if Solus mock config exists
ls /etc/mock/ | grep solus
# If not, create one:

# Create Solus config
sudo tee /etc/mock/solus-x86_64.cfg << 'EOF'
config_opts['root'] = 'solus-x86_64'
config_opts['target_arch'] = 'x86_64'
config_opts['legal_host_arches'] = ['x86_64']

config_opts['chroot_setup_cmd'] = 'install @buildsys-build'
config_opts['dist'] = 'solus'
config_opts['releasever'] = '4'

config_opts['yum.conf'] = """
[main]
keepcache=1
debuglevel=2
reposdir=/dev/null
retries=20
obsoletes=1
gpgcheck=0

[solus]
name=Solus $releasever - x86_64
baseurl=https://mirrors.getsol.us/repo/$releasever/x86_64/
enabled=1
gpgcheck=1
gpgkey=https://getsol.us/solus-keyring.gpg

[solus-updates]
name=Solus $releasever - x86_64 - Updates
baseurl=https://mirrors.getsol.us/repo/$releasever/x86_64/updates/
enabled=1
gpgcheck=1
gpgkey=https://getsol.us/solus-keyring.gpg
"""
EOF
```

### 2.3 Building with Mock

```bash
# Build from source RPM
mock -r solus-x86_64 --rebuild /path/to/package-1.0.0-1.src.rpm

# Build from spec file (mock creates SRPM first)
mock -r solus-x86_64 --buildsrpm --spec package.spec --sources ~/rpmbuild/SOURCES/
mock -r solus-x86_64 --rebuild ~/rpmbuild/SRPMS/package-1.0.0-1.src.rpm

# Build and keep chroot for debugging
mock -r solus-x86_64 -v --rebuild package-1.0.0-1.src.rpm --resultdir=./results

# Interactive shell in chroot
mock -r solus-x86_64 --shell

# Clean chroot
mock -r solus-x86_64 --clean
```

### 2.4 Mock Configuration Options

```bash
# Common mock options:
--no-clean          # Don't clean chroot before building
--no-cleanup-after  # Keep chroot after build
--arch=x86_64       # Target architecture
--resultdir=./out   # Output directory
--verbose           # Verbose output
--enable-network    # Allow network access during build
--with=option       # Enable conditional build
--without=option    # Disable conditional build

# Debugging failed builds:
mock -r solus-x86_64 --rebuild package.src.rpm --no-cleanup-after
mock -r solus-x86_64 --shell  # Then inspect /builddir/build/
```

---

## 3. Copr Repository Setup

[Copr](https://copr.fedorainfracloud.org/) is a build system for RPM packages that provides automated builds and a repository for distribution.

### 3.1 Create a Copr Repository

```bash
# Install copr-cli
sudo dnf5 install copr-cli

# Configure authentication
# Visit https://copr.fedorainfracloud.org/api/ to get API token
copr-cli login

# Create a new project
copr-cli create solus-experimental \
    --chroot fedora-40-x86_64 \
    --description "Experimental Solus packages" \
    --instructions "sudo dnf5 copr enable @solus/solus-experimental" \
    --unlisted-group solus

# Or for Solus-native builds, specify custom chroot
copr-cli create solus-custom \
    --chroot custom-1 \
    --chroot-custom-1-name "solus-4-x86_64" \
    --chroot-custom-1-baseurl "https://mirrors.getsol.us/repo/4/x86_64/" \
    --chroot-custom-1-repos "https://mirrors.getsol.us/repo/4/x86_64/updates/"
```

### 3.2 Building with Copr

```bash
# Build from URL
copr-cli build solus-experimental https://example.com/package-1.0.0.src.rpm

# Build from local SRPM
copr-cli build solus-experimental ~/rpmbuild/SRPMS/package-1.0.0-1.src.rpm

# Build from spec (automatically downloads sources)
copr-cli buildscm solus-experimental \
    --clone-url https://github.com/user/package \
    --spec package.spec \
    --commit main

# Monitor builds
copr-cli watch-build <build-id>

# List builds
copr-cli list-builds solus-experimental
```

### 3.3 Using Copr Repository

```bash
# Enable a Copr repo
sudo dnf5 copr enable @solus/solus-experimental

# Or manually:
sudo tee /etc/yum.repos.d/copr-solus.repo <<EOF
[copr-solus-experimental]
name=Copr - Solus Experimental
baseurl=https://download.copr.fedorainfracloud.org/results/@solus/solus-experimental/fedora-\$releasever-\$basearch/
gpgcheck=1
gpgkey=https://download.copr.fedorainfracloud.org/results/@solus/solus-experimental/pubkey.gpg
enabled=1
EOF

# Install packages from Copr
sudo dnf5 install package-name
```

### 3.4 Local Mock + Copr Alternative

For users who prefer not to use Copr, a local repository can be set up:

```bash
# Create local repo
sudo dnf5 install createrepo
mkdir -p ~/local-repo/x86_64
cp ~/rpmbuild/RPMS/x86_64/*.rpm ~/local-repo/x86_64/
createrepo ~/local-repo/

# Add as DNF source
sudo tee /etc/yum.repos.d/local.repo <<EOF
[local]
name=Local Repository
baseurl=file:///home/$USER/local-repo
enabled=1
gpgcheck=0
EOF
```

---

## 4. Local Build and Test

### 4.1 Quick Build Flow

```bash
# 1. Set up sources
cd ~/rpmbuild/SPECS
spectool -g -R package.spec  # Downloads sources defined in spec

# 2. Build binary RPM
rpmbuild -ba package.spec

# 3. Check results
ls ~/rpmbuild/RPMS/x86_64/package-*.rpm
ls ~/rpmbuild/SRPMS/package-*.src.rpm

# 4. Install and test
sudo dnf5 install ~/rpmbuild/RPMS/x86_64/package-*.rpm
package --version
```

### 4.2 RPM Build Modes

| Command | Output | Use Case |
|---------|--------|----------|
| `rpmbuild -bp` | `BUILD/` | Unpack sources and apply patches |
| `rpmbuild -bc` | `BUILD/` | Build (compile) sources |
| `rpmbuild -bi` | `BUILDROOT/` | Install to buildroot |
| `rpmbuild -bb` | `RPMS/` | Build binary RPM only |
| `rpmbuild -bs` | `SRPMS/` | Build source RPM only |
| `rpmbuild -ba` | `RPMS/ + SRPMS/` | Build both binary and source RPM |
| `rpmbuild --short-circuit` | Various | Skip to specific step (for debugging) |

### 4.3 Quick Build with dnf5

```bash
# dnf5 can build packages from spec files directly
sudo dnf5 build package.spec

# This automatically resolves BuildRequires and builds
```

### 4.4 Building Solus Packages (from solus-dev)

```bash
cd ~/solus-dev/packages

# Build a single package
make <package-name>

# Build specific architecture
make <package-name> ARCH=x86_64

# Build and install
make <package-name> && sudo dnf5 install ../RPMS/x86_64/<package-name>-*.rpm

# Clean build artifacts
make clean-<package-name>

# Build a group of packages
make -j$(nproc)                    # Build all packages (parallel)
```

### 4.5 Build Log Analysis

```bash
# View build log
less ~/rpmbuild/BUILD/<package>/build.log

# Check for common issues:
# - Missing BuildRequires
# - Failed tests
# - Unrecognized options
# - File conflicts

# Check installed files
rpm -qpl <package>.rpm

# Check dependencies
rpm -qpR <package>.rpm

# Check scripts
rpm -qp --scripts <package>.rpm
```

### 4.6 Testing Installed Package

```bash
# Verify package integrity
rpm -V <package-name>

# Check file ownership
rpm -qf /path/to/file

# Verify dependencies are satisfied
sudo dnf5 repoquery --requires <package-name>

# Run upstream test suite (if packaged)
# Many packages include %check section
```

---

## 5. Spec File Reference

### 5.1 Spec File Anatomy

A spec file is divided into sections, each defining a stage of the build process:

```
%global macro     # Global macros (shared across sections)

Name:             # Package name (required)
Version:          # Upstream version (required)
Release:          # Package release number (required)
Summary:          # One-line description (required)
License:          # Software license (required)
URL:              # Upstream website
Source0:          # Source tarball (required, at least one)
Patch0:           # Distribution patches (optional)

BuildRequires:    # Build-time dependencies
Requires:         # Run-time dependencies
Provides:         # Virtual provides
Obsoletes:        # Packages this replaces
Conflicts:        # Incompatible packages

%description      # Multi-line description
%prep             # Source unpacking and patching
%build            # Compilation commands
%install          # Install to buildroot
%check            # Test suite (optional)
%files            # Files to include in package
%changelog        # Package changelog
```

### 5.2 Header Section

```rpm
# Global macros
%global maj_ver 1
%global min_ver 2
%global patch_ver 3
%global real_version %{maj_ver}.%{min_ver}.%{patch_ver}

# Basic info
Name:           example-package
Version:        %{real_version}
Release:        1%{?dist}
Summary:        An example package for demonstration

# Licensing
License:        MIT
URL:            https://example.com/%{name}
Source0:        https://example.com/%{name}/%{name}-%{version}.tar.gz
Source1:        %{name}.desktop
Source2:        %{name}.conf

# Patches
Patch0:         %{name}-fix-bug.patch

# Dependencies
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconfig(foo) >= 1.0
Requires:       bar-libs
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

# Groups/exclusive arch
ExclusiveArch:  x86_64 aarch64
BuildArch:      noarch    # For architecture-independent packages
```

### 5.3 Common Macros

```rpm
# Path macros
%{_bindir}          /usr/bin
%{_sbindir}         /usr/sbin
%{_libdir}          /usr/lib64
%{_libexecdir}      /usr/libexec
%{_datadir}         /usr/share
%{_includedir}      /usr/include
%{_sysconfdir}      /etc
%{_localstatedir}   /var
%{_sharedstatedir}  /var/lib
%{_mandir}          /usr/share/man
%{_infodir}         /usr/share/info
%{_docdir}          /usr/share/doc
%{_unitdir}         /usr/lib/systemd/system
%{_userunitdir}     /usr/lib/systemd/user
%{_udevrulesdir}    /usr/lib/udev/rules.d

# Build macros
%{buildroot}        $RPM_BUILD_ROOT
%{optflags}         Optimization flags
%{_smp_mflags}      -j<N> for parallel builds
%{_smp_build_nprocs} Number of CPUs

# Setup macros
%setup -q           # Quiet unpack
%setup -n name      # Specify directory name
%setup -c           # Create and enter directory
%setup -b 0         # Unpack source 0 only
%autosetup          # Auto-apply patches

# Conditional
%if 0%{?rhel} >= 8
%endif

%ifarch x86_64
%endif

%ifnarch noarch
%endif
```

### 5.4 Section Examples

#### %prep — Unpack and Patch

```rpm
%prep
# Simple unpack
%setup -q

# Or with custom directory
%setup -q -n %{name}-%{version}

# Apply patches
%patch0 -p1
%patch1 -p1 -b .suffix

# Or auto-apply all patches
%autosetup -p1

# Manual unpack if needed
tar -xf %{SOURCE0}
cd %{name}-%{version}
```

#### %build — Compilation

```rpm
%build
# Autotools (configure/make)
%configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --disable-static \
    --enable-shared
%make_build

# CMake
%cmake \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=%{_prefix}
%cmake_build

# Meson
%meson \
    -Dbuildtype=release \
    -Dprefix=%{_prefix}
%meson_build

# Simple make
make %{?_smp_mflags}

# Python
%pyproject_buildrequires
%pyproject_wheel
```

#### %install — Installation

```rpm
%install
# Autotools
%make_install

# CMake
%cmake_install

# Meson
%meson_install

# Manual install
install -Dm0755 %{name} %{buildroot}%{_bindir}/%{name}
install -Dm0644 %{name}.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dm0644 %{name}.service %{buildroot}%{_unitdir}/%{name}.service

# Python
%pyproject_install
```

#### %check — Testing

```rpm
%check
# Run upstream tests
make test
# Or
ctest --output-on-failure
# Or
%pytest

# Smoke test (quick verification)
%{buildroot}%{_bindir}/%{name} --version
%{buildroot}%{_bindir}/%{name} --help
```

#### %files — File Listing

```rpm
%files
%license LICENSE
%doc README.md NEWS.md
%{_bindir}/%{name}
%{_libdir}/%{name}/
%{_datadir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.*
%{_mandir}/man1/%{name}.1*
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf

# Subpackage
%package libs
Summary:    Library files for %{name}
%description libs
Runtime libraries for %{name}

%files libs
%{_libdir}/lib%{name}.so.*
```

#### %changelog

```rpm
%changelog
* Mon Jun 23 2026 Developer Name <dev@getsol.us> - 1.2.3-1
- Update to 1.2.3
- Security fixes for CVE-2024-XXXX

* Thu May 15 2026 Developer Name <dev@getsol.us> - 1.2.2-1
- Initial package for Solus
```

### 5.5 Complete Minimal Spec

```rpm
Name:       hello-world
Version:    1.0.0
Release:    1%{?dist}
Summary:    A simple hello world program

License:    MIT
URL:        https://example.com/hello-world
Source0:    https://example.com/hello-world/hello-world-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  make

%description
A simple hello world program demonstrating RPM packaging.

%prep
%setup -q

%build
%configure
%make_build

%install
%make_install

%check
%{buildroot}%{_bindir}/hello-world --version

%files
%license LICENSE
%{_bindir}/hello-world
%{_mandir}/man1/hello-world.1*

%changelog
* Mon Jun 23 2026 Developer <dev@getsol.us> - 1.0.0-1
- Initial package
```

---

## 6. Patch Management

### 6.1 Creating Patches

```bash
# From upstream tarball
tar -xzf package-1.0.0.tar.gz
cp -r package-1.0.0 package-1.0.0.orig

# Make modifications
cd package-1.0.0
# Edit files...

# Generate patch
diff -Naur package-1.0.0.orig package-1.0.0 > ../patches/fix-feature.patch
```

### 6.2 Using Quilt for Patch Management

[Quilt](https://savannah.nongnu.org/projects/quilt) manages a stack of patches:

```bash
# Initialize quilt in source tree
sudo dnf5 install quilt
cd ~/rpmbuild/BUILD/package-1.0.0/

# Create a new patch
quilt new fix-build-error.patch
quilt add src/main.c
# Edit src/main.c
quilt refresh

# Apply all patches
quilt push -a

# View applied patches
quilt series

# Reorder patches
quilt pop
quilt push
```

### 6.3 Patches in Spec Files

```rpm
# List patches in header (ordered by application)
Patch0:  fix-build.patch
Patch1:  add-feature.patch
Patch2:  fix-security.patch
Patch3:  solus-defaults.patch

# Apply in %prep
%prep
%setup -q

# Apply with -p1 (strip first directory component)
%patch0 -p1
%patch1 -p1

# Apply with -b (backup suffix)
%patch2 -p1 -b .orig

# Or auto-apply all patches
%autosetup -p1 -N   # -N = don't apply patches automatically
# Then apply selectively:
%autopatch -p1
```

### 6.4 Patch Guidelines

- **Use `-p1`** (strip directory prefix) for all patches
- **Prefix patches by type:**
  - `fix-*` — Bug fixes
  - `feature-*` — New features
  - `security-*` — Security fixes
  - `backport-*` — Backported upstream fixes
  - `solus-*` — Solus-specific changes
- **Document patches** with commit messages in the patch header
- **Upstream first** — send patches upstream whenever possible
- **Regenerate on version bumps** — patches may need updating
- **Keep patches minimal** — one logical change per patch

### 6.5 Patch Header Format

```diff
From: Developer Name <dev@getsol.us>
Date: Mon, 23 Jun 2026 12:00:00 -0400
Subject: [PATCH] Short description of the patch

Longer description explaining why this patch is needed,
what it changes, and any side effects.

Signed-off-by: Developer Name <dev@getsol.us>

---
 src/main.c | 5 +++++
 1 file changed, 5 insertions(+)

diff --git a/src/main.c b/src/main.c
index abc123..def456 100644
--- a/src/main.c
+++ b/src/main.c
@@ -10,6 +10,11 @@
+    // Added feature
+    return 0;
 }
```

---

## 7. Dependency Resolution

### 7.1 Automatic Dependency Detection

RPM automatically detects:
- **Shared library dependencies** (`libfoo.so.1()(64bit)`)
- **Python imports** (`python3.12dist(foo)`)
- **Perl modules** (`perl(Foo::Bar)`)
- **pkg-config requirements** (`pkgconfig(foo)`)

```bash
# Check automatic dependencies
rpm -qp --requires package.rpm
rpm -qp --provides package.rpm
```

### 7.2 Manual Dependencies

```rpm
# Versioned dependencies
Requires:       library >= 2.0
Requires:       library < 3.0

# Architecture-specific
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

# Virtual provides (for alternatives)
Provides:       webserver
Provides:       %{name}%{?_isa} = %{version}-%{release}

# Conflicts
Conflicts:      old-implementation < 2.0

# Obsoletes (replaces)
Obsoletes:      old-name < 1.0

# Recommends (soft dependency)
Recommends:     optional-plugin

# Supplements (reverse soft dep)
Supplements:    application
```

### 7.3 BuildRequires Best Practices

```rpm
# Prefer pkgconfig-style (auto-resolves -devel packages)
BuildRequires:  pkgconfig(gtk+-3.0) >= 3.24
BuildRequires:  pkgconfig(libpulse)
BuildRequires:  pkgconfig(x11)

# Use system library names when pkgconfig not available
BuildRequires:  zlib-devel
BuildRequires:  bzip2-devel

# Build tools
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  meson >= 1.0
BuildRequires:  python3-devel

# Version control / download during build
BuildRequires:  git
BuildRequires:  wget

# For documentation generation
BuildRequires:  doxygen
BuildRequires:  python3-sphinx
```

### 7.4 Resolving Dependencies

```bash
# Find what package provides a file
dnf5 provides '*/foo.h'
dnf5 provides 'libfoo.so.1'

# Find what package provides a pkgconfig module
dnf5 provides 'pkgconfig(foo)'

# Check what depends on a package
dnf5 repoquery --whatrequires <package-name>

# Resolve all dependencies for a package
dnf5 builddep package.spec

# Check if dependencies are installable
dnf5 repoquery --unsat <package-name>
```

### 7.5 Circular Dependencies

If you encounter circular dependencies (A requires B, B requires A):

```bash
# Temporarily bootstrap:
# 1. Build A without the feature that needs B
# 2. Build B normally
# 3. Rebuild A with full features

# Use %bootstrap conditional in spec:
%bcond_with bootstrap

%if %{with bootstrap}
BuildRequires:  ... (minimal deps)
%else
BuildRequires:  ... (full deps including B)
%endif

# Build bootstrap: rpmbuild -ba --without bootstrap package.spec
```

---

## 8. Architecture-Specific Builds

### 8.1 Supported Architectures

| Architecture | RPM Value | Status |
|-------------|-----------|--------|
| x86_64 (AMD64) | `x86_64` | Primary |
| AArch64 (ARM64) | `aarch64` | Supported |
| i686 (32-bit) | `i686` | Legacy (dropped) |

### 8.2 Architecture-Specific Spec Sections

```rpm
# Limit to specific architectures
ExclusiveArch:  x86_64 aarch64

# Skip build on some architectures
ExcludeArch:    i686

# Architecture-specific build logic
%ifarch x86_64
BuildRequires:  intel-gpu-tools
%endif

%ifarch aarch64
BuildRequires:  arm-gpu-tools
%endif

# Architecture-specific compiler flags
%ifarch x86_64
%global optflags -march=x86-64-v3 -O2
%endif

%ifarch aarch64
%global optflags -march=armv8-a+crc+crypto -O2
%endif
```

### 8.3 Multi-Arch Considerations

```rpm
# When splitting into -devel subpackage:
%package devel
Summary:    Development files for %{name}
Requires:   %{name}%{?_isa} = %{version}-%{release}

# For libraries, use %_isa to ensure architecture match
Requires:   libfoo%{?_isa} >= 1.0
```

### 8.4 Cross-Compilation

```bash
# Using mock for different architecture
mock -r solus-aarch64 --rebuild package.src.rpm

# For cross-compilation environment
sudo dnf5 install qemu-user-static qemu-user-binfmt
# Then mock can run aarch64 builds on x86_64 hardware
```

---

## 9. Signing Packages

### 9.1 Generate GPG Key

```bash
# Generate a signing key (if you don't have one)
gpg --gen-key
# Real name: Developer Name
# Email: dev@getsol.us
# Type: RSA (4096 bits)
# Expiration: 2y (recommended)

# List keys
gpg --list-keys
gpg --list-secret-keys
```

### 9.2 Configure RPM for Signing

```bash
# Configure RPM macros for signing
cat >> ~/.rpmmacros <<EOF
%_signature gpg
%_gpg_name Developer Name <dev@getsol.us>
%_gpgbin /usr/bin/gpg
%_gpg_path ~/.gnupg
EOF
```

### 9.3 Sign Packages

```bash
# Sign a single RPM
rpm --addsign package-1.0.0-1.x86_64.rpm
# Enter GPG passphrase when prompted

# Sign all RPMs in a directory
rpm --addsign ~/rpmbuild/RPMS/x86_64/*.rpm

# Sign with a specific key
rpm --addsign --define "_gpg_name 0xKEYID" package.rpm

# Sign source RPMs
rpm --addsign ~/rpmbuild/SRPMS/package-1.0.0-1.src.rpm

# Batch sign multiple files
find ~/rpmbuild/RPMS -name '*.rpm' -exec rpm --addsign {} \;
```

### 9.4 Verify Signatures

```bash
# Import the public key
rpm --import /path/to/public.key

# Verify a signed package
rpm -K package-1.0.0-1.x86_64.rpm
# → package-1.0.0-1.x86_64.rpm: digests signatures OK

# Verify with GPG
rpm -Kv package-1.0.0-1.x86_64.rpm
```

### 9.5 Automated Signing with expect

```bash
#!/usr/bin/expect -f
# sign-rpm.exp - Automated RPM signing

set passphrase [lindex $argv 0]
set rpm_file [lindex $argv 1]

spawn rpm --addsign $rpm_file
expect -exact "Enter pass phrase: "
send "$passphrase\r"
expect eof

# Usage: ./sign-rpm.exp "passphrase" package.rpm
```

---

## 10. Contributing Packages Upstream

### 10.1 Before Submitting

Checklist before contributing a package to Solus:

```
☐ Package builds successfully
☐ rpmlint reports no errors
☐ All dependencies are satisfied
☐ Package is properly licensed (FOSS-compatible)
☐ No bundled libraries without reason
☐ %check tests pass (if applicable)
☐ Spec file follows Solus conventions
☐ Files are properly split into subpackages
☐ Changelog entry is present
☐ Desktop file exists (for GUI apps)
☐ AppStream metadata exists (for GUI apps)
☐ Systemd service file exists (if daemon)
```

### 10.2 Solus-Specific Requirements

```bash
# Desktop file validation
desktop-file-validate %{name}.desktop

# AppStream metadata
appstream-util validate %{name}.appdata.xml

# Systemd service file
systemd-analyze verify %{name}.service

# Check for bundled libraries
rpm -q --filesbypkg -qp package.rpm | grep -E '\.(so|a)$' | head
```

### 10.3 Submission Process

1. **Create a fork** of the packages repository
2. **Add your package** in the correct directory (`packages/<first-letter>/<name>/`)
3. **Include all files:** spec, sources, patches
4. **Commit** with descriptive message
5. **Create PR** against solus-project/packages

See [Contributing Guide](contributing.md) for detailed PR workflow.

### 10.4 Review Expectations

What reviewers will check:

1. **Spec correctness** — follows Solus conventions
2. **Build reproducibility** — builds consistently in clean chroot
3. **Dependency completeness** — nothing missing, nothing extra
4. **License compliance** — proper licensing metadata
5. **File placement** — FHS compliance
6. **Integration** — works with Solus desktop/tools

### 10.5 Common Review Feedback

| Issue | How to Fix |
|-------|-----------|
| **Missing BuildRequires** | Install missing deps, add to spec |
| **Bundled library** | Add `Provides: bundled(libname) = version` |
| **File not in %files** | Add missing files to %files section |
| **Incorrect license tag** | Verify upstream license, use SPDX format |
| **No %check section** | Add smoke test or enable upstream tests |
| **Static library** | Remove `*.a` files, add `%{_libdir}/*.so` |
| **Hardcoded paths** | Use RPM macros instead of hardcoded paths |
| **RPATH in binaries** | Set `%define _disable_rpath 1` or fix build |

---

## Appendix A: Quick Command Reference

```bash
# Build
rpmbuild -ba package.spec                    # Full build
mock -r solus-x86_64 --rebuild package.src.rpm  # Clean build

# Query
rpm -qip package.rpm                         # Package info
rpm -qpl package.rpm                         # File list
rpm -qpR package.rpm                         # Requires
rpm -qp --provides package.rpm               # Provides

# Install/Remove
sudo rpm -ivh package.rpm                    # Install (verbose, hash)
sudo rpm -Uvh package.rpm                    # Upgrade
sudo rpm -e package-name                     # Erase

# Verify
rpm -V package-name                          # Verify installed package
rpm -K package.rpm                           # Verify signature

# Extract
rpm2cpio package.rpm | cpio -idmv           # Extract without installing
```

## Appendix B: Debugging Build Failures

```bash
# Check build log for errors
grep -i error ~/rpmbuild/BUILD/*/build.log
grep -i warning ~/rpmbuild/BUILD/*/build.log

# Check for missing files in buildroot
find ~/rpmbuild/BUILDROOT -type f | head -50

# Debug spec file parsing
rpm -E '%{_bindir}'                        # Evaluate macro
rpm --eval '%global ver 1.0; %{ver}'        # Test macro logic
rpmspec --parse package.spec                # Parse and output

# Debug build process with short-circuit
rpmbuild -bp package.spec                   # Stop after %setup
rpmbuild -bc --short-circuit package.spec   # Resume at %build
```
