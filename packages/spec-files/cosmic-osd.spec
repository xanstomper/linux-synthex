# Solus Linux RPM Spec — cosmic-osd
# COSMIC on-screen display (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmico_version 24.04.0

Name: cosmic-osd
Version: %{cosmico_version}
Release: 1%{?dist}
Summary: COSMIC OSD — on-screen display for volume, brightness, keyboard backlight
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-osd
Source0: https://github.com/pop-os/cosmic-osd/archive/refs/tags/v%{cosmico_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC OSD provides on-screen display notifications for the COSMIC desktop.
It shows visual feedback for:

- Volume level changes
- Display brightness adjustments
- Keyboard backlight level
- Media playback controls
- Screen recording indicator
- Caps lock, num lock, and layout toggles

Written in Rust with Iced, cosmic-osd renders overlay notifications with
smooth animations and minimal resource usage.

%prep
%autosetup -n cosmic-osd-v%{cosmico_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-osd %{buildroot}%{_bindir}/cosmic-osd

%files
%{_bindir}/cosmic-osd

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmico_version}-1
- Initial Solus package — COSMIC on-screen display
