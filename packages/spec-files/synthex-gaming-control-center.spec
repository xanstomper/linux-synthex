Name:           synthex-gaming-control-center
Version:        1.0.0
Release:        1
Summary:        SynthOS gaming control center (Python)
License:        MIT
URL:            https://getsynthex.org
Requires:       python3

Source0:        synthex-repo-%{version}.tar.gz

%description
SynthOS gaming/performance control center (Python GUI).

%prep
%setup -q -n synthex-repo-%{version}

%build
true

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_libexecdir}/synthex/gaming-center %{buildroot}%{_datadir}/synthex/gaming-center
cat > %{buildroot}%{_bindir}/synthex-gaming-control-center <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_libexecdir}/synthex/gaming-center/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-gaming-control-center
cp -r src/synthex-gaming-center/. %{buildroot}%{_libexecdir}/synthex/gaming-center/ 2>/dev/null || true
install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/synthex-gaming-daemon <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_libexecdir}/synthex/gaming-center/gaming-daemon.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-gaming-daemon

%files
%{_bindir}/synthex-gaming-control-center
%{_bindir}/synthex-gaming-daemon
%{_libexecdir}/synthex/gaming-center/
%{_datadir}/synthex/gaming-center/

%changelog
* Thu Jul 16 2026 SynthOS Team <build@synthex.org> - 1.0.0-1
- Rewire as Python gaming control center + daemon
