%define _name synthex-nvidia-installer
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS NVIDIA driver installer wizard with auto-detection

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-nvidia-installer
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
synthex-nvidia-installer is a Nobara-style NVIDIA driver wizard that
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
install -m 0755 synthex-nvidia-installer %{buildroot}%{_bindir}/synthex-nvidia-installer

%files
%{_bindir}/synthex-nvidia-installer

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-nvidia-installer package
- Auto-detects GPU, builds akmod, handles Secure Boot
