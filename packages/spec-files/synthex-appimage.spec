Name:           synthex-appimage
Version:        0.1.0
Release:        1%{?dist}
Summary:        AppImage manager

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
AppImage integration and management.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-appimage %{buildroot}%{_bindir}/synthex-appimage

%files
%{_bindir}/synthex-appimage

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-appimage package
