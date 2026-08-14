Name:           synthex-widgets
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Nova — floating desktop widget suite (clock, media, system, weather)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz
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
%setup -q

%build
# Python + QML; nothing to compile

%install
mkdir -p %{buildroot}%{_datadir}/synthex/widgets
cp *.qml main.py %{buildroot}%{_datadir}/synthex/widgets/
cat > %{buildroot}%{_bindir}/synthex-widgets <<'LAUNCH'
#!/usr/bin/env bash
exec python3 /usr/share/synthex/widgets/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-widgets

%files
%{_bindir}/synthex-widgets
%{_datadir}/synthex/widgets/

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-widgets package (Nova floating widgets, real data sources)
