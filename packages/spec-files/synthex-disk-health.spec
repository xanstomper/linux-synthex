Name:           synthex-disk-health
Version:        0.1.0
Release:        1%{?dist}
Summary:        Disk health
License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz

%description
S.M.A.R.T. disk health checker (Python).

%prep
%setup -q -n synthex-repo-0.1.0

%build
true

%install
install -d %{buildroot}%{_libexecdir}/synthex/synthex-disk-health
install -d %{buildroot}%{_bindir}
cp -r src/synthex-disk-health/. %{buildroot}%{_libexecdir}/synthex/synthex-disk-health/
cat > %{buildroot}%{_bindir}/synthex-disk-health <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_libexecdir}/synthex/synthex-disk-health/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-disk-health

%files
%{_bindir}/synthex-disk-health
%{_libexecdir}/synthex/synthex-disk-health/

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-disk-health package