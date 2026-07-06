# Solus Linux RPM Spec — solus-update-manager
# Rust-based update manager with snapshot support
# Origin: https://github.com/xanstomper/solus-linux

%global um_version 0.1.0

Name: solus-update-manager
Version: %{um_version}
Release: 1%{?dist}
Summary: Solus Linux update manager — checks, downloads, and applies system updates
License: GPL-3.0-or-later
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.75.0

Requires: dnf5, snapper, btrfs-progs

%description
Solus Update Manager is a Rust-based utility for managing system updates.
It wraps DNF5 with snapshot management (BTRFS/snapper), parallel downloads,
and update scheduling.

Features:
- Check for available updates (all or security-only)
- Download + apply updates with pre-update BTRFS snapshots
- Update history viewer
- Manual snapshot creation
- Update statistics
- Automatic refresh scheduling via systemd timer

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-update-manager %{buildroot}%{_bindir}/solus-update-manager

# Systemd timer for automatic update checks
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/solus-update-checker.service << 'EOS'
[Unit]
Description=Solus Update Checker
Documentation=man:solus-update-manager(1)

[Service]
Type=oneshot
ExecStart=%{_bindir}/solus-update-manager check
Nice=19
IOSchedulingClass=idle
EOS

cat > %{buildroot}%{_unitdir}/solus-update-checker.timer << 'EOS'
[Unit]
Description=Solus Update Check Timer (every 6 hours)

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true
RandomizedDelaySec=30m

[Install]
WantedBy=timers.target
EOS

# Config
mkdir -p %{buildroot}%{_sysconfdir}/solus
cat > %{buildroot}%{_sysconfdir}/solus/update-manager.toml << 'EOS'
auto_check = true
check_interval = 6
snapshots = true
max_parallel_downloads = 5
categories = ["security", "bugfix", "enhancement", "gaming"]
EOS

%files
%{_bindir}/solus-update-manager
%{_unitdir}/solus-update-checker.service
%{_unitdir}/solus-update-checker.timer
%config(noreplace) %{_sysconfdir}/solus/update-manager.toml
%doc README.md

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus Rust update manager
- Update checking with security filter
- DNF5 wrapper with BTRFS snapshot support
- Systemd timer for automatic checks
- Configurable update categories
