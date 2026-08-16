Name:           synthex-snapshot-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Snapshot manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Btrfs snapshot management daemon.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt binaries
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-snapshot target/release/synthex-snapshot
cp target/release/synthex-snapshot target/release/synthex-snapshot-manager
%install
install -Dm755 target/release/synthex-snapshot-manager %{buildroot}%{_bindir}/synthex-snapshot-manager
install -Dm644 systemd/synthex-snapshot-manager.service %{buildroot}%{_unitdir}/synthex-snapshot-manager.service 2>/dev/null || :

%files
%{_bindir}/synthex-snapshot-manager
%{_unitdir}/synthex-snapshot-manager.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-snapshot-manager package
