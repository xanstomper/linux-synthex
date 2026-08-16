Name:           synthex-tray
Version:        0.1.0
Release:        1%{?dist}
Summary:        System tray
License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz

%description
Synthex system tray indicator (Python).

%prep
%setup -q -n synthex-repo-0.1.0

%build
true

%install
install -d %{buildroot}%{_libexecdir}/synthex/synthex-tray
install -d %{buildroot}%{_bindir}
cp -r src/synthex-tray/. %{buildroot}%{_libexecdir}/synthex/synthex-tray/
# Launcher
cat > %{buildroot}%{_bindir}/synthex-tray <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_libexecdir}/synthex/synthex-tray/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-tray

%files
%{_bindir}/synthex-tray
%{_libexecdir}/synthex/synthex-tray/

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-tray package