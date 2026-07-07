Name:           synthex-firewall
Version:        0.1.0
Release:        1%{?dist}
Summary:        Firewall manager

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Firewall profile switching (gaming/secure/dev/home).

%install
install -Dm755 src/synthex-firewall %{buildroot}%{_bindir}/synthex-firewall

%files
%{_bindir}/synthex-firewall

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-firewall package
