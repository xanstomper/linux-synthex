Name:           synthex-recovery-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        System recovery framework

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
One-click recovery for boot, drivers, packages, network, audio. Btrfs snapshots.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-recovery target/release/synthex-recovery
%install
install -Dm755 target/release/synthex-recovery %{buildroot}%{_bindir}/synthex-recovery
install -Dm644 systemd/synthex-recovery.service %{buildroot}%{_unitdir}/synthex-recovery.service 2>/dev/null || :

%files
%{_bindir}/synthex-recovery
%{_unitdir}/synthex-recovery.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-recovery-rs package
