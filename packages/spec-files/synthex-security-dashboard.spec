Name:           synthex-security-dashboard
Version:        1.0.0
Release:        1
Summary:        Synthex security dashboard (stub)
License:        MIT
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

%description
Security dashboard stub. Provides a launcher, gatherer service, polkit policy,
DBus service, SELinux policy stub, and config.

%prep
%setup -q -n synthex-repo-%{version}

%build
true

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_libexecdir}/synthex %{buildroot}%{_unitdir} %{buildroot}%{_datadir}/polkit-1/actions %{buildroot}%{_datadir}/dbus-1/system-services %{buildroot}%{_datadir}/dbus-1/system.d %{buildroot}%{_datadir}/selinux/packages %{buildroot}%{_sysconfdir}/synthex/security-dashboard %{buildroot}%{_datadir}/synthex/security-dashboard

cat > %{buildroot}%{_bindir}/synthex-security-dashboard <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_datadir}/synthex/security-dashboard/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-security-dashboard

cat > %{buildroot}%{_libexecdir}/synthex/security-gatherer <<'SH'
#!/usr/bin/env bash
echo "synthex-security-gatherer stub"
SH
chmod 0755 %{buildroot}%{_libexecdir}/synthex/security-gatherer

cat > %{buildroot}%{_unitdir}/synthex-security-gatherer.service <<'EOF'
[Unit]
Description=Synthex security gatherer
[Service]
Type=oneshot
ExecStart=/usr/libexec/synthex/security-gatherer
[Install]
WantedBy=multi-user.target
EOF

cat > %{buildroot}%{_unitdir}/synthex-security-gatherer.timer <<'EOF'
[Unit]
Description=Synthex security gatherer hourly
[Timer]
OnCalendar=hourly
[Install]
WantedBy=timers.target
EOF

cat > %{buildroot}%{_datadir}/polkit-1/actions/org.synthex.security-dashboard.policy <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<policyconfig><action id="org.synthex.SecurityDashboard"><description>Security gather</description><message>auth</message><defaults><allow_active>auth_admin_keep</allow_active></defaults></action></policyconfig>
EOF

cat > %{buildroot}%{_datadir}/dbus-1/system-services/org.synthex.SecurityGatherer1.service <<'EOF'
[D-BUS Service]
Name=org.synthex.SecurityGatherer1
Exec=/usr/libexec/synthex/security-gatherer
User=root
EOF

cat > %{buildroot}%{_datadir}/dbus-1/system.d/org.synthex.SecurityGatherer1.conf <<'EOF'
<busconfig><user>root</user></busconfig>
EOF

cat > %{buildroot}%{_datadir}/selinux/packages/synthex-security-dashboard.te <<'EOF'
module synthex-security-dashboard 1.0;
EOF

echo "interval=3600" > %{buildroot}%{_sysconfdir}/synthex/security-dashboard/dashboard.conf

cp -r src/synthex-security-dashboard/. %{buildroot}%{_datadir}/synthex/security-dashboard/ 2>/dev/null || true

%post
systemctl daemon-reload 2>/dev/null || true

%postun
systemctl daemon-reload 2>/dev/null || true

%files
%{_bindir}/synthex-security-dashboard
%{_libexecdir}/synthex/security-gatherer
%{_unitdir}/synthex-security-gatherer.service
%{_unitdir}/synthex-security-gatherer.timer
%{_datadir}/polkit-1/actions/org.synthex.security-dashboard.policy
%{_datadir}/dbus-1/system-services/org.synthex.SecurityGatherer1.service
%{_datadir}/dbus-1/system.d/org.synthex.SecurityGatherer1.conf
%{_datadir}/selinux/packages/synthex-security-dashboard.te
%config(noreplace) %{_sysconfdir}/synthex/security-dashboard/dashboard.conf
%{_datadir}/synthex/security-dashboard/

%changelog
* Sat Jul 04 2026 Synthex Security Team <security@synthex-project.com> - 1.0.0-1
- Initial release (stub)