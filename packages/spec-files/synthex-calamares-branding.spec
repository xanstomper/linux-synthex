%global _name synthex-calamares-branding
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS Calamares installer branding and slideshow

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       calamares

%description
SynthOS Calamares branding package. Provides the installer visual
identity — branding descriptor with product info and sidebar colors,
and a QML slideshow shown during installation highlighting Synthex features.

%prep
%setup -c -T -n %{_name}-%{_version}

%build
# Nothing to build — config files only

%install
install -d -m 0755 %{buildroot}%{_datadir}/calamares/branding/synthex
install -m 0644 %{_sourcedir}/branding.desc %{buildroot}%{_datadir}/calamares/branding/synthex/branding.desc
install -m 0644 %{_sourcedir}/show.qml %{buildroot}%{_datadir}/calamares/branding/synthex/show.qml
install -m 0644 %{_sourcedir}/synthex-logo.png %{buildroot}%{_datadir}/calamares/branding/synthex/synthex-logo.png
install -m 0644 %{_sourcedir}/synthex-icon.png %{buildroot}%{_datadir}/calamares/branding/synthex/synthex-icon.png
install -m 0644 %{_sourcedir}/synthex-welcome.png %{buildroot}%{_datadir}/calamares/branding/synthex/synthex-welcome.png

%files
%{_datadir}/calamares/branding/synthex/branding.desc
%{_datadir}/calamares/branding/synthex/show.qml
%{_datadir}/calamares/branding/synthex/synthex-logo.png
%{_datadir}/calamares/branding/synthex/synthex-icon.png
%{_datadir}/calamares/branding/synthex/synthex-welcome.png

%changelog
* Mon Jul 06 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-calamares-branding package with QML slideshow and assets
