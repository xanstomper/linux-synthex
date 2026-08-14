Name:           synthex-recovery-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        System recovery framework

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
One-click recovery for boot, drivers, packages, network, audio. Btrfs snapshots.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-recovery %{buildroot}%{_bindir}/synthex-recovery
install -Dm644 systemd/synthex-recovery.service %{buildroot}%{_unitdir}/synthex-recovery.service 2>/dev/null || :

%files
%{_bindir}/synthex-recovery
%{_unitdir}/synthex-recovery.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-recovery-rs package
