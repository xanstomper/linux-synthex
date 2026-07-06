%define _name solus-nvidia-installer
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux NVIDIA driver installer wizard with auto-detection

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-nvidia-installer
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       akmod-nvidia
Requires:       nvidia-settings
Requires:       nvidia-prime
Requires:       dkms
Requires:       kernel-devel
Requires:       mokutil

%description
solus-nvidia-installer is a Nobara-style NVIDIA driver wizard that
auto-detects NVIDIA GPUs, installs the correct driver stack, builds the
kernel module, configures Wayland modeset, blacklists nouveau, handles
Secure Boot MOK enrollment, and rebuilds the initramfs.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-nvidia-installer %{buildroot}%{_bindir}/solus-nvidia-installer

%files
%{_bindir}/solus-nvidia-installer

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-nvidia-installer package
- Auto-detects GPU, builds akmod, handles Secure Boot
