Name:           synthex-codec-installer
Version:        0.1.0
Release:        1%{?dist}
Summary:        Codec installer

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
One-command multimedia codec installation.

%install
install -Dm755 src/synthex-codec-installer %{buildroot}%{_bindir}/synthex-codec-installer

%files
%{_bindir}/synthex-codec-installer

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-codec-installer package
