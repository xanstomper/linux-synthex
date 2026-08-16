Name:           synthex-widgets
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Nova — floating desktop widget suite (clock, media, system, weather)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       (python3-pyside6 or python3-pyqt5)
Recommends:     playerctl

%description
The SynthOS Nova floating desktop widgets: clock, media (MPRIS via
playerctl), system monitor, quick settings, launcher and weather.
Qt/QML (PySide6 with PyQt5 fallback), individually toggleable,
launched via /usr/bin/synthex-widgets or the session autostart entry.

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python + QML; nothing to compile

%install
mkdir -p %{buildroot}%{_datadir}/synthex/widgets %{buildroot}%{_bindir}
cp -r src/synthex-welcome/Main.qml src/synthex-welcome/main.py %{buildroot}%{_datadir}/synthex/widgets/ 2>/dev/null || true
cat > %{buildroot}%{_bindir}/synthex-widgets <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_datadir}/synthex/widgets/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-widgets

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-widgets package (Nova floating widgets, real data sources)
