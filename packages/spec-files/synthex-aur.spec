Name:           synthex-aur
Version:        0.1.0
Release:        1%{?dist}
Summary:        AUR helper

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz
%description
AUR package access bridge.

%prep
%setup -q -n synthex-repo-0.1.0
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-aur %{buildroot}%{_bindir}/synthex-aur

%files
%{_bindir}/synthex-aur

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-aur package
