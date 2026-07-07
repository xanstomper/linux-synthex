Name:           synthex-control-center
Version:        1.0.0
Release:        1%%{?dist}
Summary:        Synthex control center GUI

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  cmake, qt6-qtdeclarative-devel, qt6-qtquickcontrols2-devel
Requires:       qt6-qtdeclarative, qt6-qtquickcontrols2

%%description
Unified control panel for SynthOS.

%%prep
%%setup -q
%%build
cmake -B build
cmake --build build
%%install
install -Dm755 build/synthex-control-center %%{buildroot}%%{_bindir}/synthex-control-center
%%files
%%{_bindir}/synthex-control-center
%%changelog
* Mon Jul 06 2026 - Initial
