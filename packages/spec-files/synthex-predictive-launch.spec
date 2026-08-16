Name:           synthex-predictive-launch
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Predictive Launcher — Markov-chain app pre-launching

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3

%description
Learns which applications follow each other in your session (Markov
transitions over application launch history) and pre-warms the predicted
next app to cut perceived launch latency. Fully local — no telemetry.

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python; nothing to compile

%install
install -Dm755 src/synthex-predictive-launch/predictor.py %{buildroot}%{_libexecdir}/synthex/predictive-launch.py

%files
%{_libexecdir}/synthex/predictive-launch.py

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-predictive-launch package (local-only Markov predictor)
