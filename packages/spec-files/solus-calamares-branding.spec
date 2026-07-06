%define _name solus-calamares-branding
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux Calamares installer branding and slideshow

License:        GPL-2.0-or-later
URL:            https://getsol.us
BuildArch:      noarch
BuildRequires:  coreutils

Source0:        branding.desc
Source1:        show.qml
Source2:        solus-logo.svg

Requires:       calamares

%description
Solus Linux Calamares branding package. Provides the installer visual
identity — branding descriptor with product info and sidebar colors,
and a QML slideshow shown during installation highlighting Solus features.

%prep
%setup -c -T
cp %{SOURCE0} .
cp %{SOURCE1} .
cp %{SOURCE2} .

%build
# Nothing to build — config files only

%install
install -d -m 0755 %{buildroot}%{_datadir}/calamares/branding/solus
install -m 0644 branding.desc %{buildroot}%{_datadir}/calamares/branding/solus/branding.desc
install -m 0644 show.qml %{buildroot}%{_datadir}/calamares/branding/solus/show.qml
install -m 0644 solus-logo.svg %{buildroot}%{_datadir}/calamares/branding/solus/solus-logo.png

%files
%{_datadir}/calamares/branding/solus/branding.desc
%{_datadir}/calamares/branding/solus/show.qml
%{_datadir}/calamares/branding/solus/solus-logo.png

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-calamares-branding package
- Branding descriptor + QML slideshow for Calamares installer
