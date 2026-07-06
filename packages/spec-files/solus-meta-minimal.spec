%define _name solus-meta-minimal
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux minimal install meta-package

License:        MIT
URL:            https://solus.org

BuildArch:      noarch
BuildRequires:  coreutils

Requires:       solus-release >= %{_version}

# Core system
Requires:       kernel-core
Requires:       systemd
Requires:       systemd-udev
Requires:       dnf
Requires:       sudo
Requires:       passwd
Requires:       shadow-utils
Requires:       glibc
Requires:       glibc-common
Requires:       bash
Requires:       coreutils
Requires:       util-linux
Requires:       findutils
Requires:       gawk
Requires:       sed
Requires:       grep
Requires:       file
Requires:       diffutils
Requires:       which
Requires:       tar
Requires:       gzip
Requires:       bzip2
Requires:       xz
Requires:       cpio
Requires:       less
# nano removed — use vim or kate from the standard meta; minimal keeps vi
Requires:       vim-minimal
Requires:       openssh-clients
Requires:       openssh-server

# Network
Requires:       iproute
Requires:       iputils
Requires:       NetworkManager
Requires:       dhcp-client
Requires:       wget
Requires:       curl
Requires:       ca-certificates

# Firmware
Requires:       linux-firmware

# Time
Requires:       tzdata
Requires:       chrony

# Logging
Requires:       rsyslog

%description
Solus Linux minimal install meta-package. Provides the core operating system
components for a minimal, server-oriented installation. Includes the kernel,
systemd, package manager, networking tools, and essential system utilities
without any graphical environment.

Approximate install size: 1.2 GB

%prep
%setup -c -T

%build
# Nothing to build — this is a dependency meta-package

%install
# Create metadata file
install -d -m 0755 %{buildroot}%{_datadir}/solus-meta
cat > %{buildroot}%{_datadir}/solus-meta/minimal << 'EOF'
Solus Linux Minimal Install
Version: %{_version}
Type: minimal
Description: Core operating system components (server/CLI)
Install size: ~1.2 GB
Packages: kernel, systemd, dnf, networking, coreutils
EOF

%files
%defattr(-,root,root,-)
%{_datadir}/solus-meta/minimal

%changelog
* Sat Jul 04 2026 Solus Release Team <release@solus.org> - 1:2026.1-1
- Initial minimal install meta-package
- Core system: kernel, systemd, glibc, bash
- Package management: dnf, rpm
- Network: NetworkManager, iproute, curl, wget
- Utilities: coreutils, util-linux, findutils, tar, gzip
