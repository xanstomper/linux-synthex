# SynthOS RPM Spec — cosmic-randr
# COSMIC display configuration (Rust)
# Origin: Pop!_OS (System76)

%global cosmicrandr_version 24.04.0

Name: cosmic-randr
Version: %{cosmicrandr_version}
Release: 1%{?dist}
Summary: COSMIC display configuration — xrandr replacement in Rust
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-randr
Source0: https://github.com/pop-os/cosmic-randr/archive/refs/tags/v%{cosmicrandr_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC randr provides display configuration management for the COSMIC
desktop. Written in Rust, it replaces xrandr with a Wayland-native display
configuration tool supporting:

- Multi-monitor layout configuration
- Resolution and refresh rate settings
- Scale and fractional scaling
- Display rotation and orientation
- EDID-based monitor identification
- Per-monitor color profiles

Includes both a CLI tool (cosmic-randr) and a library for other COSMIC
components to query and set display configurations.

%prep
%autosetup -n cosmic-randr-v%{cosmicrandr_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-randr %{buildroot}%{_bindir}/cosmic-randr

%files
%{_bindir}/cosmic-randr

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicrandr_version}-1
- Initial Synthex package — COSMIC display configuration
