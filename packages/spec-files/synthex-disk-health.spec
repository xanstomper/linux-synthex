Name:           synthex-disk-health
Version:        0.1.0
Release:        1%{?dist}
Summary:        Disk health

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
S.M.A.R.T. disk health checker.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-disk-health %{buildroot}%{_bindir}/synthex-disk-health

%files
%{_bindir}/synthex-disk-health

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-disk-health package
