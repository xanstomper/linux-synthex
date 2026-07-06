# Solus Linux RPM Spec — solus-driver-manager
# Rust-based GPU/driver detection and installation
# Origin: https://github.com/xanstomper/solus-linux

%global dm_version 0.1.0

Name: solus-driver-manager
Version: %{dm_version}
Release: 1%{?dist}
Summary: Solus Linux GPU/driver manager — auto-detect and install graphics drivers
License: GPL-3.0-or-later
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.75.0

Requires: dnf5, pciutils, lspci
Recommends: supergfxctl, akmod-nvidia, rocm-opencl

%description
Solus Driver Manager is a Rust-based utility for detecting GPU hardware
and installing the appropriate graphics drivers. It supports NVIDIA,
AMD, Intel, and Mesa drivers with automatic detection and Optimus
switching.

Features:
- GPU hardware detection (PCI vendor/model)
- Driver installation: NVIDIA, AMD, Intel, Mesa
- Automatic driver recommendation based on detected hardware
- NVIDIA Optimus mode switching (integrated, nvidia, hybrid, compute)
- Installed driver listing and status
- Driver update checking
- Driver removal

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-driver-manager %{buildroot}%{_bindir}/solus-driver-manager

%files
%{_bindir}/solus-driver-manager
%doc README.md

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus Rust driver manager
- GPU detection via lspci
- NVIDIA/AMD/Intel/Mesa driver installation
- NVIDIA Optimus mode switching
- Driver update checking
