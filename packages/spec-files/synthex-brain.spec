# synthex-brain.spec — SynthOS Brain OS persistent AI consciousness daemon
#
# Build:  rpmbuild -ba synthex-brain.spec
# Crate:  linux-synthex/src/synthex-brain/  (Cargo workspace member)

%global crate_name  synthex-brain
%global service     synthex-brain.service
%global dbus_conf   org.synthex.Brain.conf

Name:           synthex-brain
Version:        2026.10.0
Release:        1%{?dist}
Summary:        SynthOS Brain OS – persistent AI consciousness daemon

License:        MIT OR Apache-2.0
URL:            https://github.com/synthex-os/linux-synthex
Source0:        %{name}-%{version}.tar.gz

# ── Build dependencies ────────────────────────────────────────────────────────
BuildRequires:  rust-toolchain
BuildRequires:  cargo
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(sqlite3)
BuildRequires:  systemd-rpm-macros

# ── Runtime dependencies ──────────────────────────────────────────────────────
Requires:       systemd
Requires:       dbus
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
synthex-brain is the central AI consciousness daemon for SynthOS Brain OS.
It maintains persistent agent state, orchestrates sub-agents, exposes the
Brain IPC bus, and hosts the local inference gateway at
http://localhost:7700.  All SynthOS intelligent subsystems (gesture engine,
FPS overlay, package advisor, etc.) report metrics to and receive
recommendations from this daemon.

%prep
%autosetup -n %{name}-%{version}

%build
# Build the release binary via Cargo.  The workspace Cargo.toml is at the
# repo root; individual crate lives at src/synthex-brain/.
cargo build --release --package %{crate_name} \
    --manifest-path src/synthex-brain/Cargo.toml

%install
install -D -m 0755 target/release/%{crate_name} \
    %{buildroot}%{_libdir}/synthex/%{crate_name}

# ── systemd unit ──────────────────────────────────────────────────────────────
install -D -m 0644 /dev/stdin \
    %{buildroot}%{_unitdir}/%{service} << 'UNIT'
[Unit]
Description=SynthOS Brain OS — AI consciousness daemon
Documentation=https://github.com/synthex-os/linux-synthex/wiki/brain
After=network.target dbus.service
Wants=network.target

[Service]
Type=notify
ExecStart=%{_libdir}/synthex/synthex-brain --config /etc/synthex/brain.toml
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5s
TimeoutStartSec=30
TimeoutStopSec=20
WatchdogSec=60

# Hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
ReadWritePaths=/var/lib/synthex /run/synthex /tmp/synthex-brain

# State and runtime directories
StateDirectory=synthex
RuntimeDirectory=synthex
RuntimeDirectoryMode=0750

# Brain IPC shared memory
ReadWritePaths=/dev/shm

# Environment
Environment=SYNTHEX_LOG=info
Environment=RUST_BACKTRACE=1

[Install]
WantedBy=multi-user.target
UNIT

# ── D-Bus system policy ───────────────────────────────────────────────────────
install -D -m 0644 /dev/stdin \
    %{buildroot}%{_datadir}/dbus-1/system.d/%{dbus_conf} << 'DBUS'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE busconfig PUBLIC
  "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy user="root">
    <allow own="org.synthex.Brain"/>
  </policy>
  <policy context="default">
    <allow send_destination="org.synthex.Brain"
           send_interface="org.synthex.Brain"
           send_member="QueryAgent"/>
    <allow send_destination="org.synthex.Brain"
           send_interface="org.synthex.Brain"
           send_member="GetStatus"/>
    <allow send_destination="org.synthex.Brain"
           send_interface="org.freedesktop.DBus.Properties"/>
    <allow send_destination="org.synthex.Brain"
           send_interface="org.freedesktop.DBus.Introspectable"/>
  </policy>
</busconfig>
DBUS

# ── Default configuration ─────────────────────────────────────────────────────
install -D -m 0640 /dev/stdin \
    %{buildroot}%{_sysconfdir}/synthex/brain.toml << 'TOML'
# SynthOS Brain OS — main daemon configuration
# /etc/synthex/brain.toml

[daemon]
listen_addr   = "127.0.0.1:7700"
log_level     = "info"
state_dir     = "/var/lib/synthex/brain"
max_agents    = 32

[inference]
# Local inference gateway settings
model         = "synthex-local-7b"
context_size  = 8192
max_tokens    = 2048

[gaming]
# Thresholds for FPS overlay advisor recommendations
gpu_warn_pct  = 95
vram_warn_pct = 90
fps_warn      = 30

[ipc]
shm_name      = "synthex-brain-bus"
shm_size_mb   = 64
TOML

%files
%license LICENSE-MIT LICENSE-APACHE
%doc README.md CHANGELOG.md
%{_libdir}/synthex/%{crate_name}
%{_unitdir}/%{service}
%{_datadir}/dbus-1/system.d/%{dbus_conf}
%config(noreplace) %{_sysconfdir}/synthex/brain.toml

%post
%systemd_post %{service}
systemctl daemon-reload >/dev/null 2>&1 || true

%preun
%systemd_preun %{service}

%postun
%systemd_postun_with_restart %{service}

%changelog
* Fri Jul 11 2026 SynthOS Maintainers <packages@synthex-os.org> - 2026.10.0-1
- Initial packaging of synthex-brain 2026.10.0
- Adds persistent AI consciousness daemon with Brain IPC bus
- Exposes local inference gateway at http://localhost:7700
- Integrates gaming metrics advisor (FPS overlay, GPU throttle hints)
- D-Bus policy: org.synthex.Brain on system bus
