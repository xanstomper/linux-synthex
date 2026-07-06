# Solus Linux RPM Spec — cosmic-app-library
# COSMIC app library/launcher (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmical_version 24.04.0

Name: cosmic-app-library
Version: %{cosmical_version}
Release: 1%{?dist}
Summary: COSMIC app library — application launcher and grid
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-app-library
Source0: https://github.com/pop-os/cosmic-app-library/archive/refs/tags/v%{cosmical_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC app library provides the application launcher and grid view for the
COSMIC desktop. Features:

- Searchable application grid
- Application categories and folders
- Favorites and recent apps
- Keybinding launcher (Super+Space)
- Desktop file integration

%prep
%autosetup -n cosmic-app-library-v%{cosmical_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-app-library %{buildroot}%{_bindir}/cosmic-app-library

%files
%{_bindir}/cosmic-app-library

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmical_version}-1
- Initial Solus package — COSMIC app library launcher
