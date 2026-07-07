%define _name synthex-security-deploy
%define _version 1.0.0
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Synthex security hardening deployment script

License:        MIT
URL:            https://getsynthex.org

BuildArch:      noarch

Requires:       sysctl-linux
Requires:       audit
Requires:       firewalld

%description
Deploys CIS/NIST-grade security hardening to the installed Synthex system.
Includes: sysctl kernel hardening, auditd rules, resource limits,
modprobe blacklist, firewalld configuration, and SELinux enforcement.

References:
  - CIS Linux Benchmark v3.0
  - Kernel Self-Protection Project (KSPP)
  - NIST SP 800-53

%install
mkdir -p %{buildroot}/usr/libexec/synthex
install -m 0755 %{_sourcedir}/security-deploy.sh \
    %{buildroot}/usr/libexec/synthex/security-deploy.sh

mkdir -p %{buildroot}/usr/share/synthex/security/hardening
install -m 0644 %{_sourcedir}/sysctl.conf \
    %{buildroot}/usr/share/synthex/security/hardening/sysctl.conf 2>/dev/null || true
install -m 0644 %{_sourcedir}/auditd.rules \
    %{buildroot}/usr/share/synthex/security/hardening/auditd.rules 2>/dev/null || true
install -m 0644 %{_sourcedir}/limits.conf \
    %{buildroot}/usr/share/synthex/security/hardening/limits.conf 2>/dev/null || true

%files
/usr/libexec/synthex/security-deploy.sh
%dir /usr/share/synthex/security
%dir /usr/share/synthex/security/hardening
/usr/share/synthex/security/hardening/

%post
chmod 755 /usr/libexec/synthex/security-deploy.sh 2>/dev/null || :

%changelog
* Sun Jul 06 2026 Synthex Security Team <security@getsynthex.org> - 1.0.0-1
- Initial release of security hardening deployment
- CIS Linux Benchmark v3.0 compliant
- KSPP-recommended sysctl settings
- NIST SP 800-53 audit controls
