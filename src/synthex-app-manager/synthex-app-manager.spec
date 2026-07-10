Name:           synthex-app-manager
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS App Manager — GTK4 application installer
License:        GPL-3.0-or-later
URL:            https://synthex-os.org
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3
Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       flatpak
Requires:       pkexec

%description
GTK4/libadwaita application manager for SynthOS Linux.
Browse and install Flatpak, DNF, and AppImage applications
by category. Supports batch install of app bundles.

%install
mkdir -p %{buildroot}/usr/lib/synthex/
mkdir -p %{buildroot}/usr/share/applications/

install -m755 synthex-app-manager          %{buildroot}/usr/lib/synthex/synthex-app-manager
install -m644 synthex-app-manager.desktop  %{buildroot}/usr/share/applications/

%files
/usr/lib/synthex/synthex-app-manager
/usr/share/applications/synthex-app-manager.desktop
