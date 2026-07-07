Name:           synthex-timeshift
Version:        0.1.0
Release:        1%{?dist}
Summary:        Snapshot browser

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Btrfs snapshot browser and manager.

%install
install -Dm755 src/synthex-timeshift %{buildroot}%{_bindir}/synthex-timeshift

%files
%{_bindir}/synthex-timeshift

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-timeshift package
