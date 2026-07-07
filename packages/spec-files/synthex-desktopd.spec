Name:           synthex-desktopd
Version:        0.1.0
Release:        1%{?dist}
Summary:        Desktop daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Desktop environment integration service.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-desktopd %{buildroot}%{_bindir}/synthex-desktopd
install -Dm644 systemd/synthex-desktopd.service %{buildroot}%{_unitdir}/synthex-desktopd.service 2>/dev/null || :

%files
%{_bindir}/synthex-desktopd
%{_unitdir}/synthex-desktopd.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-desktopd package
