Name:           synthex-proton-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Proton manager

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz
%description
Manage Proton-GE/Wine versions per game.

%prep
%setup -q -n synthex-repo-0.1.0
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-proton-manager %{buildroot}%{_bindir}/synthex-proton-manager

%files
%{_bindir}/synthex-proton-manager

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-proton-manager package
