Name:           sddm-theme-synthex
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS SDDM login theme — dark navy with amber gold accents
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch
Requires:       sddm
Requires:       qt6-qtdeclarative
Requires:       google-noto-sans-fonts

%description
SynthOS SDDM login screen theme.
Features dark navy/midnight blue design with amber gold (#FFB300) accents,
glassmorphism login card, session selector (Wayland/X11/Plasma/Hyprland/GNOME),
keyboard layout picker, clock/date display, and power controls.

%install
install -d %{buildroot}%{_datadir}/sddm/themes/synthex
install -d %{buildroot}%{_datadir}/sddm/themes/synthex/components
cp -r desktop/sddm/synthex-sddm-theme/. \
    %{buildroot}%{_datadir}/sddm/themes/synthex/

%post
# Set synthex as default SDDM theme if /etc/sddm.conf exists
if [ -f /etc/sddm.conf ]; then
    if grep -q "^\[Theme\]" /etc/sddm.conf; then
        sed -i '/^\[Theme\]/,/^\[/{s/^Current=.*/Current=synthex/}' /etc/sddm.conf
    else
        echo -e "\n[Theme]\nCurrent=synthex" >> /etc/sddm.conf
    fi
fi

%files
%{_datadir}/sddm/themes/synthex/

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: dark navy, amber gold, glassmorphism card
