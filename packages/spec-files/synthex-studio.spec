Name:           synthex-studio
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Studio — creative workstation launcher and profile manager

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3

%description
SynthOS Studio opens a specialized creative environment: audio, video and
graphics tool profiles with per-profile presets (presets/). Launches the real
creative applications (Kdenlive, Krita, Blender, OBS) with tuned settings.

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python + QML; nothing to compile

%install
install -Dm755 synthex-studio %{buildroot}%{_libexecdir}/synthex/synthex-studio
install -Dm644 presets/*.json %{buildroot}%{_datadir}/synthex/studio/presets/
mkdir -p %{buildroot}%{_datadir}/synthex/studio/ui
cp -r ui/* %{buildroot}%{_datadir}/synthex/studio/ui/
cp main.py %{buildroot}%{_datadir}/synthex/studio/main.py

%files
%{_libexecdir}/synthex/synthex-studio
%{_datadir}/synthex/studio/

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-studio package
