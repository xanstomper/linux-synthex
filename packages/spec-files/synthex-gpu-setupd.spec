Name:           synthex-gpu-setupd
Version:        0.1.0
Release:        1%{?dist}
Summary:        GPU setup daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
GPU configuration and monitoring.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-gpu-setupd %{buildroot}%{_bindir}/synthex-gpu-setupd
install -Dm644 systemd/synthex-gpu-setupd.service %{buildroot}%{_unitdir}/synthex-gpu-setupd.service 2>/dev/null || :

%files
%{_bindir}/synthex-gpu-setupd
%{_unitdir}/synthex-gpu-setupd.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-gpu-setupd package
