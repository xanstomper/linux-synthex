Name:           synthex-app-manager
Version:        1.0.0
Release:        1
Summary:        SynthOS app manager (Python)
License:        MIT
URL:            https://getsynthex.org
Requires:       python3

Source0:        synthex-repo-%{version}.tar.gz

%description
SynthOS application manager (Python GUI + launcher).

%prep
%setup -q -n synthex-repo-%{version}

%build
true

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_libexecdir}/synthex/app-manager %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_bindir}/synthex-app-manager <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_libexecdir}/synthex/app-manager/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-app-manager
cp -r src/synthex-app-manager/. %{buildroot}%{_libexecdir}/synthex/app-manager/ 2>/dev/null || true
cp src/synthex-app-manager/synthex-app-manager.desktop %{buildroot}%{_datadir}/applications/ 2>/dev/null || true

%files
%{_bindir}/synthex-app-manager
%{_libexecdir}/synthex/app-manager/
%{_datadir}/applications/synthex-app-manager.desktop

%changelog
* Sun Aug 16 2026 SynthOS Team <build@synthex.org> - 1.0.0-1
- Rewire as Python app-manager
