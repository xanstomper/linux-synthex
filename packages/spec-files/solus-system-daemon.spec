# Solus Linux RPM Spec — solus-system-daemon
# Rust-based performance auto-tuner for CPU governor, VRR, HDR, TDP
# Origin: https://github.com/xanstomper/solus-linux

%global sd_version 0.1.0

Name: solus-system-daemon
Version: %{sd_version}
Release: 1%{?dist}
Summary: Solus system performance auto-tuner — VRR, HDR, CPU governor, TDP, form factor
License: MIT OR Apache-2.0
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

Requires: systemd
Recommends: gamemode

%description
Solus System Daemon is a Rust-based performance auto-tuner that detects
hardware capabilities and configures optimal system settings.

Features:
- Form factor detection (laptop/desktop/VM)
- Display capability detection (VRR, HDR, max refresh rate)
- CPU governor auto-tuning (mode + AC/battery aware)
- TDP management (RAPL power limits for laptops)
- GPU power level auto-configuration
- KWin compositor configuration (VRR, HDR, refresh rate)
- ACPI power source monitoring (auto-switch modes)
- GameMode integration
- Background service management

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-system-daemon %{buildroot}%{_libexecdir}/solus/solus-system-daemon

# Systemd service
install -D -m 0644 %{buildroot}%{_unitdir}/solus-system-daemon.service \
    %{_builddir}/solus-system-daemon.service 2>/dev/null || true
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/solus-system-daemon.service << 'EOS'
[Unit]
Description=Solus System Performance Auto-Tuner (Rust)
Documentation=https://github.com/xanstomper/solus-linux
After=sysinit.target local-fs.target
Before=display-manager.service

[Service]
Type=simple
ExecStart=%{_libexecdir}/solus/solus-system-daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
TimeoutStopSec=10
User=root
Nice=0

[Install]
WantedBy=multi-user.target
EOS

%post
%systemd_post solus-system-daemon.service

%preun
%systemd_preun solus-system-daemon.service

%postun
%systemd_postun_with_restart solus-system-daemon.service

%files
%{_libexecdir}/solus/solus-system-daemon
%{_unitdir}/solus-system-daemon.service
%doc README.md

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus system daemon
- Form factor detection (laptop/desktop/VM)
- Display capability detection (VRR, HDR, refresh rate)
- CPU governor auto-tuning with AC/battery awareness
- TDP management via RAPL
- GPU power level auto-config
- KWin configuration for VRR/HDR
- ACPI power source monitoring
- GameMode integration
