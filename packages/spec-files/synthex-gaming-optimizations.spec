%define _name synthex-gaming-optimizations
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS gaming optimizations — realtime priorities, sysctl, env vars

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
BuildArch:      noarch
BuildRequires:  coreutils

Source0:        limits.conf
Source1:        sysctl-gaming.conf
Source2:        environment-gaming.conf

Requires:       systemd
Requires:       gamemode

%description
SynthOS gaming optimization configurations. Provides:
  - Realtime priorities for audio/video/gaming groups (limits.conf)
  - Gaming-tuned sysctl values (swappiness, TCP BBR, scheduler latency)
  - Gaming environment variables (Proton, DXVK, VKD3D, RADV, NVIDIA, SDL)

These match and exceed CachyOS + Nobara gaming optimizations.

%prep
%setup -c -T

%build
# Nothing to build — config files only

%install
# Realtime priorities
install -d -m 0755 %{buildroot}%{_sysconfdir}/security/limits.d
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/security/limits.d/99-synthex-gaming.conf

# Gaming sysctl
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysctl.d
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/sysctl.d/99-synthex-gaming-optimize.conf

# Gaming environment
install -d -m 0755 %{buildroot}%{_sysconfdir}/environment.d
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/environment.d/synthex-gaming.conf

%files
%{_sysconfdir}/security/limits.d/99-synthex-gaming.conf
%{_sysconfdir}/sysctl.d/99-synthex-gaming-optimize.conf
%{_sysconfdir}/environment.d/synthex-gaming.conf

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-gaming-optimizations package
- Realtime priorities, gaming sysctl, Proton/DXVK/VKD3D environment
