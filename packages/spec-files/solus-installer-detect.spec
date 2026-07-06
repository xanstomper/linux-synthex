# Solus Linux RPM Spec — solus-installer-detect
# Rust-based hardware auto-detection for Calamares installer
# Origin: https://github.com/xanstomper/solus-linux

%global detect_version 0.1.0

Name: solus-installer-detect
Version: %{detect_version}
Release: 1%{?dist}
Summary: Solus hardware detector — GPU, form factor, disk auto-detection for Calamares
License: MIT OR Apache-2.0
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
Requires: jq

%description
Solus Installer Detect is a Rust binary that auto-detects system hardware
and generates JSON configuration recommendations for the Calamares installer.

It detects:
- GPU vendor and model (NVIDIA, AMD, Intel) with VRAM and driver recommendations
- Form factor (laptop, desktop, tablet, server, VM) via DMI chassis type
- Disk type and size (NVMe, SSD, HDD) with rotational detection
- Firmware type (UEFI vs legacy BIOS) and Secure Boot status
- RAM size and CPU cores/threads

Generation of recommendations:
- Desktop edition (Plasma, GNOME, Hyprland)
- Filesystem (BTRFS with compression, ext4, XFS) based on disk type
- Swap (partition, ZRAM, file) based on RAM size
- GPU driver (nvidia-open, nvidia-proprietary, amdgpu, xe)
- Kernel (kernel-zen, kernel-core) with tuned boot parameters
- Calamares configuration overlays for automatic installation

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-installer-detect %{buildroot}%{_bindir}/solus-installer-detect

# Calamares integration hook
install -D -m 0755 %{SOURCE1} %{buildroot}%{_bindir}/solus-installer-hook

# Calamares config overlays directory
mkdir -p %{buildroot}%{_sysconfdir}/calamares
mkdir -p %{buildroot}%{_sysconfdir}/solus-installer

%post
echo "solus-installer-detect installed — Calamares will auto-detect hardware on next ISO build"

%files
%{_bindir}/solus-installer-detect
%{_bindir}/solus-installer-hook
%dir %{_sysconfdir}/calamares/
%dir %{_sysconfdir}/solus-installer/
%doc README.md

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus installer hardware detector
- GPU, form factor, disk, firmware detection
- Edition, filesystem, swap, driver, kernel recommendations
- Calamares configuration overlays
