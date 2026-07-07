Name:           synthex-handheld
Version:        0.1.0
Release:        1%{?dist}
Summary:        Handheld mode

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
Handheld gaming mode for ROG Ally, Steam Deck, Legion Go.

%install
install -Dm755 src/synthex-handheld %{buildroot}%{_bindir}/synthex-handheld

%files
%{_bindir}/synthex-handheld

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-handheld package
