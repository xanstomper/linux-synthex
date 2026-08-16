Name:           synthex-deadman
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Dead Man's Switch — session lockdown + webhook alert on missed check-in

License:        GPL-3.0-or-later
URL:            https://getsynthex.io

BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros

Source0:        synthex-repo-2026.10.tar.gz
%description
The SynthOS Dead Man's Switch monitors periodic check-ins from the companion
C{synthex-checkin} binary. If no check-in arrives within the configured interval +
grace period, it trips the switch: locks all user sessions (loginctl) and fires
webhook alerts to every configured endpoint. A unique, package-level security
feature for unattended or high-risk machines.

%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-deadman target/release/synthex-deadman
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-checkin target/release/synthex-checkin
%install
install -Dm755 target/release/synthex-deadman  %{buildroot}%{_bindir}/synthex-deadman
install -Dm755 target/release/synthex-checkin  %{buildroot}%{_bindir}/synthex-checkin
install -Dm644 systemd/synthex-deadman.service %{buildroot}%{_unitdir}/synthex-deadman.service
install -Dm644 systemd/synthex-checkin.service %{buildroot}%{_unitdir}/synthex-checkin.service
install -Dm644 systemd/synthex-checkin.timer   %{buildroot}%{_unitdir}/synthex-checkin.timer

%files
%{_bindir}/synthex-deadman
%{_bindir}/synthex-checkin
%{_unitdir}/synthex-deadman.service
%{_unitdir}/synthex-checkin.service
%{_unitdir}/synthex-checkin.timer

%post
%systemd_post synthex-deadman.service synthex-checkin.timer

%preun
%systemd_preun synthex-deadman.service synthex-checkin.timer

%postun
%systemd_postun_with_restart synthex-deadman.service

%changelog
* Fri Jul 10 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-deadman package
- Dead Man's Switch: missed-check-in session lockdown + webhook alerts
- synthex-checkin timer for periodic attendance proof
