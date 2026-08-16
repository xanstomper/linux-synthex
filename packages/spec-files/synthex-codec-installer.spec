Name:           synthex-codec-installer
Version:        0.1.0
Release:        1%{?dist}
Summary:        Codec installer

License:        MIT
URL:            https://getsynthex.io
Source0:        synthex-repo-%{version}.tar.gz
Requires:       python3

%description
One-command multimedia codec installation.

%prep
%setup -q -n synthex-repo-%{version}

%build
# Python application; nothing to compile
true

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_datadir}/synthex-codec-installer
cat > %{buildroot}%{_bindir}/synthex-codec-installer <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_datadir}/synthex-codec-installer/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-codec-installer
cp -r src/synthex-codec-installer/. %{buildroot}%{_datadir}/synthex-codec-installer/ 2>/dev/null || true

%files
%{_bindir}/synthex-codec-installer
%{_datadir}/synthex-codec-installer/

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-codec-installer package
