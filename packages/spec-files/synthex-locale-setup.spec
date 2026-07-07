%define _name synthex-locale-setup
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS locale, timezone, and keyboard configuration tool

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-locale-setup
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       glibc-common
Requires:       systemd

%description
synthex-locale-setup provides commands to configure system locale, timezone,
and keyboard layout. Supports listing available locales and timezones,
and shows current status.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 synthex-locale-setup %{buildroot}%{_bindir}/synthex-locale-setup

%files
%{_bindir}/synthex-locale-setup

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-locale-setup package
- Commands: locale, timezone, keyboard, list-locales, list-timezones, status
