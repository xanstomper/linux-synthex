# synthex-installer — SynthOS Calamares installer configuration and modules
Name:           synthex-installer
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Calamares installer configuration and custom modules

License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch

BuildRequires:  python3
BuildRequires:  python3-setuptools

Requires:       calamares
Requires:       calamares-libs
Requires:       python3
Requires:       python3-pyaml
Requires:       python3-jsonschema
Requires:       synthex-branding
Requires:       synthex-calamares-branding
Requires:       parted
Requires:       btrfs-progs
Requires:       dosfstools
Requires:       e2fsprogs
Requires:       cryptsetup
Requires:       grub2
Requires:       grub2-efi-x64
Requires:       shim-x64

%description
Provides the complete Calamares installer configuration for SynthOS, including:
  - Main settings.conf (module sequence and branding reference)
  - All module configurations (partition, users, locale, bootloader, etc.)
  - Custom synthexprofile and synthexpostinstall Python modules
  - Post-install scripts (hardware detection, GPU setup, theme apply)
  - Desktop profile activation scripts

%prep
%setup -q

%build
# Nothing to compile — noarch data/script package

%install
# Install Calamares config
install -d %{buildroot}/etc/calamares
install -d %{buildroot}/etc/calamares/modules
install -d %{buildroot}/usr/lib/calamares/modules/synthexprofile
install -d %{buildroot}/usr/lib/calamares/modules/synthexpostinstall
install -d %{buildroot}/usr/lib/calamares/modules/synthexfirstuser
install -d %{buildroot}/usr/lib/calamares/modules/synthexgpusetup
install -d %{buildroot}/usr/lib/calamares/modules/synthexhardwaredetect
install -d %{buildroot}/usr/lib/calamares/modules/synthexnetworksetup
install -d %{buildroot}/usr/lib/calamares/modules/synthexsecuritysetup
install -d %{buildroot}/usr/lib/calamares/modules/synthexservices
install -d %{buildroot}/usr/lib/calamares/modules/synthextheme
install -d %{buildroot}/usr/libexec/synthex

# Main config
install -m 644 installer/config/calamares-settings-complete.conf \
    %{buildroot}/etc/calamares/settings.conf

# Module configs
for conf in installer/config/modules/*.conf; do
    install -m 644 "$conf" %{buildroot}/etc/calamares/modules/
done

# Custom Python modules
install -m 644 installer/modules/synthexprofile/synthexprofile.py \
    %{buildroot}/usr/lib/calamares/modules/synthexprofile/main.py
install -m 644 installer/modules/synthexprofile/module.desc \
    %{buildroot}/usr/lib/calamares/modules/synthexprofile/

install -m 644 installer/modules/synthexpostinstall/synthexpostinstall.py \
    %{buildroot}/usr/lib/calamares/modules/synthexpostinstall/main.py
install -m 644 installer/modules/synthexpostinstall/module.desc \
    %{buildroot}/usr/lib/calamares/modules/synthexpostinstall/
# All 7 remaining custom modules
for mod in synthexfirstuser synthexgpusetup synthexhardwaredetect \
           synthexnetworksetup synthexsecuritysetup synthexservices synthextheme; do
    install -m 644 installer/modules/$mod/main.py \
        %{buildroot}/usr/lib/calamares/modules/$mod/ 2>/dev/null || true
    install -m 644 installer/modules/$mod/module.desc \
        %{buildroot}/usr/lib/calamares/modules/$mod/ 2>/dev/null || true
done

# Post-install scripts
for script in installer/scripts/post-install/*.sh; do
    install -m 755 "$script" %{buildroot}/usr/libexec/synthex/
done

%files
%license LICENSE
/etc/calamares/settings.conf
/etc/calamares/modules/
/usr/lib/calamares/modules/synthexprofile/
/usr/lib/calamares/modules/synthexpostinstall/
/usr/lib/calamares/modules/synthexfirstuser/
/usr/lib/calamares/modules/synthexgpusetup/
/usr/lib/calamares/modules/synthexhardwaredetect/
/usr/lib/calamares/modules/synthexnetworksetup/
/usr/lib/calamares/modules/synthexsecuritysetup/
/usr/lib/calamares/modules/synthexservices/
/usr/lib/calamares/modules/synthextheme/
/usr/libexec/synthex/

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- 2026.10 "Ignition" installer release
