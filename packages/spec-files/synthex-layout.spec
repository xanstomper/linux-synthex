Name:           synthex-layout
Version:        0.1.0
Release:        1%{?dist}
Summary:        Layout manager

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz
%description
Keyboard layout manager.

%prep
%setup -q -n synthex-repo-0.1.0
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-layout %{buildroot}%{_bindir}/synthex-layout

%files
%{_bindir}/synthex-layout

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-layout package
