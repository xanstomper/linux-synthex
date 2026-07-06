# Solus Linux RPM Spec — cosmic-panel
# COSMIC desktop panel (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicpanel_version 24.04.0

Name: cosmic-panel
Version: %{cosmicpanel_version}
Release: 1%{?dist}
Summary: COSMIC panel — desktop bar/panel with launcher, workspaces, system tray
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-panel
Source0: https://github.com/pop-os/cosmic-panel/archive/refs/tags/v%{cosmicpanel_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp, cosmic-bg

%description
COSMIC panel provides the main desktop panel/bar for the COSMIC desktop
environment. Features include:

- Application launcher integration
- Workspace switcher
- System tray with notifications
- Clock and calendar
- Quick settings menu (network, audio, brightness, power)
- Multi-monitor support
- Auto-hide and panel positioning

%prep
%autosetup -n cosmic-panel-v%{cosmicpanel_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-panel %{buildroot}%{_bindir}/cosmic-panel

%files
%{_bindir}/cosmic-panel

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmicpanel_version}-1
- Initial Solus package — COSMIC desktop panel
