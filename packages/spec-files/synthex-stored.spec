Name:           synthex-stored
Version:        0.1.0
Release:        1%{?dist}
Summary:        State daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
System state persistence daemon.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-stored %{buildroot}%{_bindir}/synthex-stored
install -Dm644 systemd/synthex-stored.service %{buildroot}%{_unitdir}/synthex-stored.service 2>/dev/null || :

%files
%{_bindir}/synthex-stored
%{_unitdir}/synthex-stored.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-stored package
