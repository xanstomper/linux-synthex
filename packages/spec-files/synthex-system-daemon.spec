Name:           synthex-system-daemon
Version:        0.1.0
Release:        1%{?dist}
Summary:        Performance daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Auto-tunes CPU governor, TDP, VRR, HDR, power management.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-system-daemon %{buildroot}%{_bindir}/synthex-system-daemon
install -Dm644 systemd/synthex-system-daemon.service %{buildroot}%{_unitdir}/synthex-system-daemon.service 2>/dev/null || :

%files
%{_bindir}/synthex-system-daemon
%{_unitdir}/synthex-system-daemon.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-system-daemon package
