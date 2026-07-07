# SynthOS RPM Spec — cosmic-bg
# COSMIC background/wallpaper daemon (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicbg_version 24.04.0

Name: cosmic-bg
Version: %{cosmicbg_version}
Release: 1%{?dist}
Summary: COSMIC background daemon — wallpaper and background management
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-bg
Source0: https://github.com/pop-os/cosmic-bg/archive/refs/tags/v%{cosmicbg_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel, mesa-libEGL-devel, mesa-libgbm-devel
Requires: cosmic-comp

%description
COSMIC background daemon manages wallpapers and backgrounds for the COSMIC
desktop. Written in Rust with Iced, it provides:

- Static and animated wallpaper support
- Multiple monitors with independent backgrounds
- Color scheme extraction from wallpaper
- Slideshow support

%prep
%autosetup -n cosmic-bg-v%{cosmicbg_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-bg %{buildroot}%{_bindir}/cosmic-bg

%files
%{_bindir}/cosmic-bg

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicbg_version}-1
- Initial Synthex package — COSMIC background daemon
