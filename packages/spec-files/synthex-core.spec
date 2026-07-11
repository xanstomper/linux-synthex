# synthex-core — Core SynthOS system package
Name:           synthex-core
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS core system components and configuration
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch

Requires:       synthex-base
Requires:       synthex-release
Requires:       synthex-branding
Requires:       synthex-essentials
Requires:       synthex-kernel
Requires:       synthex-grub-theme
Requires:       synthex-system-daemon
Requires:       synthex-desktopd
Requires:       synthex-service-manager
Requires:       synthex-hwdaemon
Requires:       synthex-firstboot
Requires:       synthex-oobe
Requires:       synthex-cachy-tuning
Requires:       synthex-firmware
Requires:       systemd
Requires:       NetworkManager
Requires:       polkit
Requires:       sudo
Requires:       bash
Requires:       coreutils
Requires:       util-linux
Requires:       dbus
Requires:       pciutils
Requires:       usbutils

%description
SynthOS core meta-package. Pulling in synthex-core guarantees a complete,
bootable SynthOS base system with:
  - Synthex kernel and firmware
  - Core system daemons (desktopd, hwdaemon, service-manager, system-daemon)
  - First-boot and OOBE framework
  - SynthOS branding and release identification
  - Performance tuning (CachyOS scheduler defaults)
  - Hardware detection subsystem

This package is always installed and provides the minimum required components
for any SynthOS edition.

%prep
# Nothing to unpack — meta-package

%build
# Nothing to build

%install
# Core system drop-ins
install -d %{buildroot}/etc/synthex
install -d %{buildroot}/usr/share/synthex

# Core identity file
cat > %{buildroot}/etc/synthex/core.conf << 'EOF'
# SynthOS Core Configuration
SYNTHEX_EDITION=standard
SYNTHEX_VERSION=2026.10
SYNTHEX_CODENAME=Ignition
SYNTHEX_VARIANT=s1
SYNTHEX_RELEASE_DATE=2026-10-01
EOF

install -d %{buildroot}/usr/lib/os-release.d
cat > %{buildroot}/usr/lib/os-release.d/synthex-core << 'EOF'
SYNTHEX_CORE_VERSION=2026.10
SYNTHEX_CORE_CODENAME=Ignition
EOF

%files
%dir /etc/synthex
%config(noreplace) /etc/synthex/core.conf
%dir /usr/share/synthex
/usr/lib/os-release.d/synthex-core

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial 2026.10 "Ignition" release of synthex-core
