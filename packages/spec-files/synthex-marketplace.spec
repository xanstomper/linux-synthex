Name:           synthex-marketplace
Version:        0.1.0
Release:        1%{?dist}
Summary:        Marketplace

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Synthex package marketplace browser.

%install
install -Dm755 src/synthex-marketplace %{buildroot}%{_bindir}/synthex-marketplace

%files
%{_bindir}/synthex-marketplace

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-marketplace package
