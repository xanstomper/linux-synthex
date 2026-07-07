Name:           synthex-input-remapper
Version:        0.1.0
Release:        1%{?dist}
Summary:        Input remapper

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Controller input remapping.

%install
install -Dm755 src/synthex-input-remapper %{buildroot}%{_bindir}/synthex-input-remapper

%files
%{_bindir}/synthex-input-remapper

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-input-remapper package
