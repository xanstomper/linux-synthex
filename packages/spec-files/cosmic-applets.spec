# Solus Linux RPM Spec — cosmic-applets
# COSMIC applets (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicapplets_version 24.04.0

Name: cosmic-applets
Version: %{cosmicapplets_version}
Release: 1%{?dist}
Summary: COSMIC applets — desktop widget/applet system
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-applets
Source0: https://github.com/pop-os/cosmic-applets/archive/refs/tags/v%{cosmicapplets_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC applets provides the widget/applet system for the COSMIC desktop
panel and desktop. Includes:

- System Monitor: CPU, RAM, network, disk usage
- Clock: time, date, calendar, world clocks
- Audio: volume slider, output device switching
- Network: Wi-Fi scan, connection management
- Bluetooth: device list and management
- Power: battery status, power profile switching
- Weather: current conditions, forecast
- Quick Settings: toggles for common actions
- Notifications: recent notification history
- User Menu: account switching, lock, logout

%prep
%autosetup -n cosmic-applets-v%{cosmicapplets_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-applets %{buildroot}%{_bindir}/cosmic-applets

%files
%{_bindir}/cosmic-applets

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmicapplets_version}-1
- Initial Solus package — COSMIC applets
