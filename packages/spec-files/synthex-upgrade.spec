Name:           synthex-upgrade
Version:        0.1.0
Release:        1%{?dist}
Summary:        Upgrader

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Major version upgrade tool.

%install
install -Dm755 src/synthex-upgrade %{buildroot}%{_bindir}/synthex-upgrade

%files
%{_bindir}/synthex-upgrade

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-upgrade package
