%define _name solus-gaming-optimizations
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux gaming optimizations — realtime priorities, sysctl, env vars

License:        GPL-2.0-or-later
URL:            https://getsol.us
BuildArch:      noarch
BuildRequires:  coreutils

Source0:        limits.conf
Source1:        sysctl-gaming.conf
Source2:        environment-gaming.conf

Requires:       systemd
Requires:       gamemode

%description
Solus Linux gaming optimization configurations. Provides:
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
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/security/limits.d/99-solus-gaming.conf

# Gaming sysctl
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysctl.d
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/sysctl.d/99-solus-gaming-optimize.conf

# Gaming environment
install -d -m 0755 %{buildroot}%{_sysconfdir}/environment.d
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/environment.d/solus-gaming.conf

%files
%{_sysconfdir}/security/limits.d/99-solus-gaming.conf
%{_sysconfdir}/sysctl.d/99-solus-gaming-optimize.conf
%{_sysconfdir}/environment.d/solus-gaming.conf

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-gaming-optimizations package
- Realtime priorities, gaming sysctl, Proton/DXVK/VKD3D environment
