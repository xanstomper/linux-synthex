Name:           synthex-workspace
Version:        0.1.0
Release:        1%{?dist}
Summary:        Workspace manager

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Switch between Gaming/Balanced/Battery/Developer modes.

%install
install -Dm755 src/synthex-workspace %{buildroot}%{_bindir}/synthex-workspace

%files
%{_bindir}/synthex-workspace

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-workspace package
