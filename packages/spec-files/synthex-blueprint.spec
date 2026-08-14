Name:           synthex-blueprint
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Blueprint — declarative system snapshot/restore (.zbp blueprints)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd

%description
Blueprint exports the current system state (packages, services, users,
configuration) to a portable .zbp blueprint file and can restore it on
another SynthOS machine. Ships synthex-blueprint.service (on-demand export
to /var/backups/synthex/system.zbp) and a nightly timer.

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python; nothing to compile

%install
install -Dm755 synthex-blueprint %{buildroot}%{_bindir}/synthex-blueprint
mkdir -p %{buildroot}%{_datadir}/synthex/blueprint
cp blueprint.py share.py %{buildroot}%{_datadir}/synthex/blueprint/
install -Dm644 systemd/synthex-blueprint.service %{buildroot}%{_unitdir}/synthex-blueprint.service
install -Dm644 systemd/synthex-blueprint.timer %{buildroot}%{_unitdir}/synthex-blueprint.timer

%files
%{_bindir}/synthex-blueprint
%{_datadir}/synthex/blueprint/
%{_unitdir}/synthex-blueprint.service
%{_unitdir}/synthex-blueprint.timer

%post
%systemd_post synthex-blueprint.timer

%preun
%systemd_preun synthex-blueprint.timer

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-blueprint package (export/restore + nightly timer)
