%define _name synthex-release
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS repository configuration and GPG keys

License:        MIT
URL:            https://synthex.org
Source0:        synthex.repo
Source1:        RPM-GPG-KEY-synthex

BuildArch:      noarch
BuildRequires:  coreutils

Requires:       dnf
Requires:       dnf-plugins-core
Requires:       gnupg2
Requires(pre):  /usr/bin/curl
Requires(pre):  /usr/bin/rpm

%description
This package installs the DNF/YUM repository configuration files and GPG
signing keys for SynthOS. It enables the Synthex package repositories
and configures repository priorities for proper dependency resolution.

Repository streams included:
  - synthex-rawhide:  Rolling development (always current)
  - synthex-stable:   Tagged point releases
  - synthex-updates:  Security and bugfix updates for stable releases
  - synthex-testing:  Pre-release validation queue (opt-in)
  - synthex-backports: Backported packages for older releases (opt-in)
  - synthex-source:   Source RPMs

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
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/yum.repos.d/synthex.repo

# Install GPG key
install -d -m 0755 %{buildroot}%{_sysconfdir}/pki/rpm-gpg
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-synthex

# Create release identification file
install -d -m 0755 %{buildroot}%{_sysconfdir}/synthex-release
echo "SynthOS %{_version}" > %{buildroot}%{_sysconfdir}/synthex-release/name
echo "%{_version}" > %{buildroot}%{_sysconfdir}/synthex-release/version
echo "%(date +%Y%m%d)" > %{buildroot}%{_sysconfdir}/synthex-release/buildid

%post
# Import GPG key into RPM database
rpm --import %{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-synthex 2>/dev/null || :

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
%config(noreplace) %{_sysconfdir}/yum.repos.d/synthex.repo
%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-synthex
%dir %{_sysconfdir}/synthex-release
%{_sysconfdir}/synthex-release/name
%{_sysconfdir}/synthex-release/version
%{_sysconfdir}/synthex-release/buildid

%changelog
* Sat Jul 04 2026 Synthex Release Team <release@synthex.org> - 1:2026.1-1
- Initial SynthOS release configuration
- Repository definitions for all streams (rawhide, stable, updates, testing, backports)
- GPG signing key import
- Release identification metadata
