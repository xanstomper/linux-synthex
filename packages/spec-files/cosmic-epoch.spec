# SynthOS RPM Spec — cosmic-epoch
# COSMIC greeter/login manager (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicepoch_version 24.04.0

Name: cosmic-epoch
Version: %{cosmicepoch_version}
Release: 1%{?dist}
Summary: COSMIC epoch — Rust-based login/greeter for the COSMIC desktop
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-epoch
Source0: https://github.com/pop-os/cosmic-epoch/archive/refs/tags/v%{cosmicepoch_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel, pam-devel
Requires: cosmic-comp, cosmic-bg

%description
COSMIC epoch is the login manager (greeter) for the COSMIC desktop
environment. Written entirely in Rust, it provides:

- User authentication via PAM
- Session selection (COSMIC, Plasma, GNOME, etc.)
- Background/theme customization
- Virtual keyboard support (touchscreen devices)
- Accessibility options (high contrast, large fonts)
- System-level power operations (shutdown, reboot, suspend)
- Auto-login configuration

Runs as a Wayland session with GPU acceleration for smooth animations.

%prep
%setup -q -n synthex-repo-24.04.0
%autosetup -n cosmic-epoch-v%{cosmicepoch_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-epoch %{buildroot}%{_bindir}/cosmic-epoch

# Greeter PAM configuration
mkdir -p %{buildroot}/etc/pam.d
cat > %{buildroot}/etc/pam.d/cosmic-epoch << 'EOF'
# PAM configuration for COSMIC epoch greeter
auth        required    pam_shells.so
auth        required    pam_unix.so
account     required    pam_unix.so
password    required    pam_unix.so
session     required    pam_unix.so
EOF

%files
%{_bindir}/cosmic-epoch
/etc/pam.d/cosmic-epoch

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicepoch_version}-1
- Initial Synthex package — COSMIC epoch greeter
