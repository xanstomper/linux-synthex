Name:           synthex-ucode
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS CPU microcode meta-package (Intel + AMD)
License:        Proprietary
URL:            https://synthex-os.org
BuildArch:      noarch

Requires:       (microcode_ctl if x86_64)
Recommends:     iucode-tool

%ifarch x86_64
Requires:       linux-firmware-whence
Recommends:     amd-ucode-firmware
Recommends:     microcode_ctl
%endif

%description
SynthOS CPU microcode meta-package. Automatically installs appropriate
microcode updates for both Intel and AMD processors.
Early microcode loading is configured via dracut for maximum security.

%prep
# meta-package

%install
# dracut conf to force early microcode loading
install -d %{buildroot}/etc/dracut.conf.d
cat > %{buildroot}/etc/dracut.conf.d/99-synthex-ucode.conf << 'EOF'
# SynthOS: Always include CPU microcode in initramfs for early loading
early_microcode="yes"
add_drivers+=" microcode "
EOF

%files
%license LICENSE
%config(noreplace) /etc/dracut.conf.d/99-synthex-ucode.conf

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial 2026.10 "Ignition" microcode meta-package
