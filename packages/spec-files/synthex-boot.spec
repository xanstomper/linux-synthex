Name:           synthex-boot
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Boot — first-boot finalizer, GRUB generator, initramfs recovery

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       grub2-tools
Requires:       systemd

%description
SynthOS boot tooling: first-boot finalization (main.py), a GRUB menu-entry
generator (grub-generator.sh), the initramfs recovery hook
(initramfs-recovery.sh) and the synthex-bootctl control script.

%prep
%setup -q

%build
# Python + shell; nothing to compile

%install
install -Dm755 synthex-bootctl.sh %{buildroot}%{_bindir}/synthex-bootctl
install -Dm755 main.py %{buildroot}%{_libexecdir}/synthex/synthex-boot
install -Dm755 grub-generator.sh %{buildroot}%{_datadir}/synthex/boot/grub-generator.sh
install -Dm755 initramfs-recovery.sh %{buildroot}%{_datadir}/synthex/boot/initramfs-recovery.sh

%files
%{_bindir}/synthex-bootctl
%{_libexecdir}/synthex/synthex-boot
%{_datadir}/synthex/boot/

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-boot package
