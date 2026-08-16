Name:           synthex-system-daemon
Version:        0.1.0
Release:        1%{?dist}
Summary:        Performance daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Auto-tunes CPU governor, TDP, VRR, HDR, power management.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-system-daemon target/release/synthex-system-daemon
%install
install -Dm755 target/release/synthex-system-daemon %{buildroot}%{_bindir}/synthex-system-daemon
install -Dm644 systemd/synthex-system-daemon.service %{buildroot}%{_unitdir}/synthex-system-daemon.service 2>/dev/null || :

%files
%{_bindir}/synthex-system-daemon
%{_unitdir}/synthex-system-daemon.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-system-daemon package
