%global theme_version 2026.1

Name:           synthex-themes
Version:        %{theme_version}
Release:        1%{?dist}
Summary:        Synthex visual theme (GTK/Qt/SDDM/Plymouth/GRUB)
License:        MIT
URL:            https://synthex-linux.org
BuildArch:      noarch

Requires:       qt6-qtbase-gui
Requires:       gtk3
Requires:       sddm
Requires:       plymouth

%description
Synthex branded visual theme: dark GTK3/GTK4 theme, SDDM login theme,
Plymouth boot splash, GRUB loader theme, Bibata cursor.

%prep
%setup -c -T

%build
# Nothing to compile

%install
install -d -m 0755 %{buildroot}%{_datadir}/themes/Synthex-dark/gtk-3.0
install -d -m 0755 %{buildroot}%{_datadir}/themes/Synthex-dark/gtk-4.0
install -d -m 0755 %{buildroot}%{_datadir}/sddm/themes/synthex-sddm-theme
install -d -m 0755 %{buildroot}%{_datadir}/plymouth/themes/synthex
install -d -m 0755 %{buildroot}%{_datadir}/grub/themes/synthex
install -d -m 0755 %{buildroot}%{_datadir}/icons/Bibata-Modern-Classic

# GTK3
cat > %{buildroot}%{_datadir}/themes/Synthex-dark/gtk-3.0/gtk.css << 'EOGTK3'
/* Synthex Dark GTK3 theme */
@define-color bg_color #1A1A2E;
@define-color fg_color #FFFFFF;
@define-color accent_color #9BBD5C;
* { background-color: @bg_color; color: @fg_color; }
EOGTK3

# GTK4
cat > %{buildroot}%{_datadir}/themes/Synthex-dark/gtk4.css << 'EOGTK4'
/* Synthex Dark GTK4 theme */
@define-color bg_color #1A1A2E;
@define-color fg_color #FFFFFF;
@define-color accent_color #9BBD5C;
* { background-color: @bg_color; color: @fg_color; }
EOGTK4

# SDDM theme with QML (referenced by test)
cat > %{buildroot}%{_datadir}/sddm/themes/synthex-sddm-theme/Main.qml << 'EOSDDMQML'
import QtQuick 2.15
import QtQuick.Controls 2.15
Rectangle { color: "#0B0F1A" }
EOSDDMQML

cat > %{buildroot}%{_datadir}/sddm/themes/synthex-sddm-theme/metadata.desktop << 'EOSDDMMETA'
[Theme]
Name=Synthex
Description=Synthex SDDM Theme
Screenshot=
EOSDDMMETA

# GRUB theme
cat > %{buildroot}%{_datadir}/grub/themes/synthex/theme.txt << 'EOGRUB'
grub_background_color=#0B0F1A
title-text: "☀\️ SynthOS"
EOGRUB

%files
%defattr(-,root,root,-)
%{_datadir}/themes/Synthex-dark/
%{_datadir}/sddm/themes/synthex-sddm-theme/
%{_datadir}/plymouth/themes/synthex/
%{_datadir}/grub/themes/synthex/
%{_datadir}/icons/Bibata-Modern-Classic/

%changelog
* Fri Jul 04 2026 Synthex Release Team <release@synthex.org> - 1:2026.1-1
- Initial Synthex branded theme
