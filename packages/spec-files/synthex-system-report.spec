Name:           synthex-system-report
Version:        0.1.0
Release:        1%{?dist}
Summary:        System report

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Comprehensive system diagnostics.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-system-report %{buildroot}%{_bindir}/synthex-system-report

%files
%{_bindir}/synthex-system-report

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-system-report package
