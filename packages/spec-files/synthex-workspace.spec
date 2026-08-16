Name:           synthex-workspace
Version:        0.1.0
Release:        1%{?dist}
Summary:        Workspace manager
License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz

%description
Switch between Gaming/Balanced/Battery/Developer modes (Python).

%prep
%setup -q -n synthex-repo-0.1.0

%build
true

%install
install -d %{buildroot}%{_libexecdir}/synthex/synthex-workspace
install -d %{buildroot}%{_bindir}
cp -r src/synthex-workspace/. %{buildroot}%{_libexecdir}/synthex/synthex-workspace/
cat > %{buildroot}%{_bindir}/synthex-workspace <<'LAUNCH'
#!/usr/bin/env bash
exec bash %{_libexecdir}/synthex/synthex-workspace/synthex-workspace.sh "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-workspace

%files
%{_bindir}/synthex-workspace
%{_libexecdir}/synthex/synthex-workspace/

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-workspace package