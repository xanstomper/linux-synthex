Name:           synthex-service-manager-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        Service manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
systemd service management with JSON output and health scoring.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-service %{buildroot}%{_bindir}/synthex-service

%files
%{_bindir}/synthex-service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-service-manager-rs package
