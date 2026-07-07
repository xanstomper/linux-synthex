# SynthOS RPM Spec — xdg-desktop-portal-cosmic
# COSMIC portal backend for xdg-desktop-portal (Rust)
# Origin: Pop!_OS (System76)

%global cosmicportal_version 24.04.0

Name: xdg-desktop-portal-cosmic
Version: %{cosmicportal_version}
Release: 1%{?dist}
Summary: COSMIC portal backend for xdg-desktop-portal (Rust)
License: GPL-3.0-only
URL: https://github.com/pop-os/xdg-desktop-portal-cosmic
Source0: https://github.com/pop-os/xdg-desktop-portal-cosmic/archive/refs/tags/v%{cosmicportal_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo, meson, ninja-build
BuildRequires: wayland-devel, glib2-devel
Requires: xdg-desktop-portal, cosmic-comp

%description
xdg-desktop-portal-cosmic provides the COSMIC backend for the
xdg-desktop-portal D-Bus service. It enables Flatpak, Snap, and
other sandboxed applications to access system resources through
COSMIC-native dialogs including:

- File chooser (Open/Save dialog)
- Screen capture and recording
- Screenshot
- Wallpaper selection
- Color picker
- Print dialog
- Network locations
- Camera access
- Location services
- Notification settings

Written in Rust with COSMIC's Iced toolkit, it provides a consistent,
GPU-accelerated portal experience matching the COSMIC desktop aesthetic.

%prep
%autosetup -n xdg-desktop-portal-cosmic-v%{cosmicportal_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/xdg-desktop-portal-cosmic %{buildroot}%{_libexecdir}/xdg-desktop-portal-cosmic

# Portal backend configuration
mkdir -p %{buildroot}%{_datadir}/xdg-desktop-portal/portals
cat > %{buildroot}%{_datadir}/xdg-desktop-portal/portals/cosmic.portal << EOF
[portal]
DBusName=org.freedesktop.impl.portal.desktop.cosmic
EOF

%files
%{_libexecdir}/xdg-desktop-portal-cosmic
%{_datadir}/xdg-desktop-portal/portals/cosmic.portal

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicportal_version}-1
- Initial Synthex package — COSMIC portal backend
