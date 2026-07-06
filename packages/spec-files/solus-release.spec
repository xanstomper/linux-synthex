%define _name solus-release
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux repository configuration and GPG keys

License:        MIT
URL:            https://solus.org
Source0:        solus.repo
Source1:        RPM-GPG-KEY-solus

BuildArch:      noarch
BuildRequires:  coreutils

Requires:       dnf
Requires:       dnf-plugins-core
Requires:       gnupg2
Requires(pre):  /usr/bin/curl
Requires(pre):  /usr/bin/rpm

%description
This package installs the DNF/YUM repository configuration files and GPG
signing keys for Solus Linux. It enables the Solus package repositories
and configures repository priorities for proper dependency resolution.

Repository streams included:
  - solus-rawhide:  Rolling development (always current)
  - solus-stable:   Tagged point releases
  - solus-updates:  Security and bugfix updates for stable releases
  - solus-testing:  Pre-release validation queue (opt-in)
  - solus-backports: Backported packages for older releases (opt-in)
  - solus-source:   Source RPMs

%prep
%setup -c -T
install -m 0644 %{SOURCE0} .
install -m 0644 %{SOURCE1} .

%build
# Nothing to build — this is a configuration-only package

%install
# Remove default build install dir
rm -rf %{buildroot}

# Install repository configuration
install -d -m 0755 %{buildroot}%{_sysconfdir}/yum.repos.d
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/solus.repo

# Install GPG key
install -d -m 0755 %{buildroot}%{_sysconfdir}/pki/rpm-gpg
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-solus

# Create release identification file
install -d -m 0755 %{buildroot}%{_sysconfdir}/solus-release
echo "Solus Linux %{_version}" > %{buildroot}%{_sysconfdir}/solus-release/name
echo "%{_version}" > %{buildroot}%{_sysconfdir}/solus-release/version
echo "%(date +%Y%m%d)" > %{buildroot}%{_sysconfdir}/solus-release/buildid

%post
# Import GPG key into RPM database
rpm --import %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-solus 2>/dev/null || :

%preun
if [ "$1" = 0 ]; then
    # Remove GPG key from RPM database on package removal
    rpm -e --allmatches gpg-pubkey-* 2>/dev/null || :
fi

%postun
if [ "$1" = 0 ]; then
    # Clean up repository cache
    dnf clean all --quiet 2>/dev/null || :
fi

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/yum.repos.d/solus.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-solus
%dir %{_sysconfdir}/solus-release
%{_sysconfdir}/solus-release/name
%{_sysconfdir}/solus-release/version
%{_sysconfdir}/solus-release/buildid

%changelog
* Sat Jul 04 2026 Solus Release Team <release@solus.org> - 1:2026.1-1
- Initial Solus Linux release configuration
- Repository definitions for all streams (rawhide, stable, updates, testing, backports)
- GPG signing key import
- Release identification metadata
