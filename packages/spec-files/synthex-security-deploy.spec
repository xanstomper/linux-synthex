%define _name synthex-security-deploy

Name:           %{_name}
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS security deployment — hardening profiles, polkit, AppArmor, SELinux policy

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       audit
Requires:       systemd
Requires(post): systemd
Recommends:     apparmor-parser
Recommends:     policycoreutils

%description
Deploys the SynthOS security stack:
- Kernel hardening sysctl profiles (balanced / gaming / powersave)
- auditd rules (CIS-benchmark derived)
- Resource limits
- Polkit admin rules for SynthOS control daemons
- AppArmor profiles for synthex-agent and synthex-webappd
- Reference SELinux policy module (synthex-policy)
- security-deploy.sh — applies the selected profile (real sysctl/audit/AA ops)

%prep
%setup -q -n synthex-repo-%{version}

%build
# Scripts + configs; nothing to compile

%install
# Deploy script
install -Dm0755 security/scripts/security-deploy.sh \
    %{buildroot}/usr/libexec/synthex/security-deploy.sh

# Hardening profiles
mkdir -p %{buildroot}/usr/share/synthex/security/hardening
install -m 0644 security/hardening/sysctl.conf \
    security/hardening/sysctl-balanced.conf \
    security/hardening/sysctl-gaming.conf \
    security/hardening/sysctl-powersave.conf \
    security/hardening/auditd.rules \
    security/hardening/limits.conf \
    security/hardening/zram-synthex.conf \
    security/hardening/99-synthex-performance.conf \
    %{buildroot}/usr/share/synthex/security/hardening/

# Polkit rules for SynthOS admin actions
install -Dm0644 security/polkit/50-synthex-admin.rules \
    %{buildroot}%{_datadir}/polkit-1/rules.d/50-synthex-admin.rules

# AppArmor profiles (enforced at install when AppArmor is active)
install -d %{buildroot}%{_sysconfdir}/apparmor.d
install -m 0644 security/synthex-apparmor-profiles/usr.bin.synthex-agent \
    security/synthex-apparmor-profiles/usr.bin.synthex-webappd \
    %{buildroot}%{_sysconfdir}/apparmor.d/

# SELinux reference policy module
mkdir -p %{buildroot}/usr/share/synthex/security/selinux-policy
install -m 0644 security/selinux-policy/synthex-policy.te \
    security/selinux-policy/synthex-policy.if \
    security/selinux-policy/synthex-policy.fc \
    security/selinux-policy/Makefile \
    %{buildroot}/usr/share/synthex/security/selinux-policy/

%files
/usr/libexec/synthex/security-deploy.sh
%dir /usr/share/synthex/security
/usr/share/synthex/security/hardening/
/usr/share/synthex/security/selinux-policy/
%{_datadir}/polkit-1/rules.d/50-synthex-admin.rules
%config(noreplace) %{_sysconfdir}/apparmor.d/usr.bin.synthex-agent
%config(noreplace) %{_sysconfdir}/apparmor.d/usr.bin.synthex-webappd

%post
# Load AppArmor profiles when AppArmor is active
if command -v apparmor_parser >/dev/null 2>&1 && [ -d /sys/kernel/security/apparmor ]; then
    apparmor_parser -r -W %{_sysconfdir}/apparmor.d/usr.bin.synthex-agent 2>/dev/null || :
    apparmor_parser -r -W %{_sysconfdir}/apparmor.d/usr.bin.synthex-webappd 2>/dev/null || :
fi

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Rewrite for repo tarball; ship hardening profiles + deploy script
- Wire polkit admin rules, AppArmor profiles (agent, webappd), SELinux policy
