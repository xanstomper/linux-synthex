Name:           synthex-sentinel
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS AETHER SENTINEL — zero-trust security intelligence layer
License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo, systemd-rpm-macros
Requires:       systemd, synthex-aether

Source0:        synthex-repo-2026.10.tar.gz
%description
AETHER SENTINEL — the zero-trust autonomous security intelligence layer for
SynthOS AETHER CORE.

sentinel turns telemetry (process, filesystem, network, agent, auth, package)
into scored, correlated threats using a provider-agnostic detection + scoring
pipeline: a signature lane, a behavioral lane, and an AI-anomaly lane fuse
into a single risk score per actor. It runs as a hardened system service
alongside the AETHER consciousness daemon and grades agent activity in
real time.


%prep
%setup -q -n synthex-repo-2026.10

%build
# use prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/aether/sentinel/target/release/aether-sentinel target/release/aether-sentinel
%install
install -d %{buildroot}/usr/lib/synthex
install -Dm755 target/release/aether-sentinel \
    %{buildroot}/usr/lib/synthex/aether-sentinel

install -Dm644 systemd/synthex-sentinel.service \
    %{buildroot}%{_unitdir}/synthex-sentinel.service

install -Dm644 systemd/synthex-sentinel.sysusers \
    %{buildroot}%{_sysusersdir}/synthex-sentinel.conf

%files
%attr(0755,root,root) /usr/lib/synthex/aether-sentinel
%{_unitdir}/synthex-sentinel.service
%{_sysusersdir}/synthex-sentinel.conf

%post
%systemd_post synthex-sentinel.service

%preun
%systemd_preun synthex-sentinel.service

%postun
%systemd_postun_with_restart synthex-sentinel.service

%changelog
* Thu Jul 11 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-sentinel package: zero-trust security intelligence daemon
- Signature + behavioral detection lanes, multi-lane threat scoring/correlation
- Hardened systemd unit (ProtectSystem=strict, dedicated synthex-sentinel user)
- Requires and grades activity of the AETHER consciousness daemon
