%global _miss_dep_check 1

Name:           synthex-base
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS base system meta-package
BuildArch:      noarch

License:        MIT
URL:            https://getsynthex.io

# Filesystem foundations
Requires:       filesystem
Requires:       btrfs-progs
Requires:       snapper
Requires:       grub2
Requires:       dracut
# Boot / init
Requires:       systemd
Requires:       systemd-udev
# Network
Requires:       NetworkManager
Requires:       NetworkManager-wifi
Requires:       firewalld
# Audio
Requires:       pipewire
Requires:       pipewire-pulseaudio
Requires:       wireplumber
# Graphics
Requires:       mesa
Requires:       mesa-vulkan-drivers
Requires:       mesa-dri-drivers
# Essential utilities
Requires:       git
Requires:       curl
Requires:       wget
Requires:       flatpak
Requires:       bash
Requires:       coreutils
Requires:       util-linux
Requires:       shadow-utils
Requires:       sudo
Requires:       polkit
Requires:       dbus
Requires:       less
Requires:       gzip
Requires:       tar
Requires:       xz
Requires:       zstd

%description
SynthOS base meta-package.  Pulling in synthex-base guarantees the minimum
set of packages required for a bootable, networked SynthOS system:

  - Filesystem layout and Btrfs tooling (btrfs-progs, snapper)
  - Boot chain (grub2, dracut, systemd)
  - Networking (NetworkManager, firewalld)
  - Audio subsystem (PipeWire + WirePlumber)
  - Mesa / Vulkan GPU stack
  - Core POSIX utilities

This is a meta-package (noarch, no build artefacts).

%prep
# meta-package — nothing to unpack

%build
# meta-package — nothing to build

%install
install -d %{buildroot}/etc/synthex
install -d %{buildroot}/var/lib/synthex
install -d %{buildroot}/usr/share/synthex

cat > %{buildroot}/etc/synthex/synthex-release << 'EOF'
SYNTHEX_VERSION=2026.10
SYNTHEX_CODENAME=Ignition
SYNTHEX_BUILD_DATE=2026-10-01
EOF

%files
%dir /etc/synthex
%dir /var/lib/synthex
%dir /usr/share/synthex
%config(noreplace) /etc/synthex/synthex-release

%post
mkdir -p /var/lib/synthex || :
systemctl enable NetworkManager firewalld 2>/dev/null || :

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Fix Release tag macro escaping (%%{?dist} → %{?dist})
- Add complete Requires list, %prep/%build/%install sections
- Install /etc/synthex/synthex-release config file
