Name:           synthex-tour
Version:        0.1.0
Release:        1%{?dist}
Summary:        Desktop tour

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Interactive desktop tour for new users.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-tour %{buildroot}%{_bindir}/synthex-tour

%files
%{_bindir}/synthex-tour

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-tour package
