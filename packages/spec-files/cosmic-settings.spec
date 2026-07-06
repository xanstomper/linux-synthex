# Solus Linux RPM Spec — cosmic-settings
# COSMIC settings application (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicsettings_version 24.04.0

Name: cosmic-settings
Version: %{cosmicsettings_version}
Release: 1%{?dist}
Summary: COSMIC settings — graphical settings manager for the COSMIC desktop
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-settings
Source0: https://github.com/pop-os/cosmic-settings/archive/refs/tags/v%{cosmicsettings_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC settings is the graphical settings application for the COSMIC
desktop environment. Written in Rust with Iced, it provides a modern
settings interface organized into categories:

- Appearance: themes, accent colors, fonts, wallpapers
- Display: resolution, scaling, refresh rate, orientation
- Keyboard: layout, shortcuts, input methods
- Mouse & Touchpad: acceleration, speed, gestures
- Sound: output/input devices, volume, profiles
- Network: Wi-Fi, Ethernet, VPN, proxy
- Bluetooth: device management
- Printer: printer configuration
- Power: battery, sleep, brightness, power profiles
- Privacy: location, camera, microphone
- Accounts: user accounts, online accounts
- System: date/time, language, region, updates
- About: device info, OS version, licenses

%prep
%autosetup -n cosmic-settings-v%{cosmicsettings_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-settings %{buildroot}%{_bindir}/cosmic-settings

%files
%{_bindir}/cosmic-settings

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmicsettings_version}-1
- Initial Solus package — COSMIC settings
