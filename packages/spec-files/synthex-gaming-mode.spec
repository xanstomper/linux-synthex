Name:           synthex-gaming-mode
Version:        0.1.0
Release:        1%{?dist}
Summary:        Gaming mode

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Gamescope gaming session with performance optimizations.

%install
install -Dm755 src/synthex-gaming-mode %{buildroot}%{_bindir}/synthex-gaming-mode

%files
%{_bindir}/synthex-gaming-mode

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-gaming-mode package
