%define _name solus-locale-setup
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux locale, timezone, and keyboard configuration tool

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-locale-setup
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       glibc-common
Requires:       systemd

%description
solus-locale-setup provides commands to configure system locale, timezone,
and keyboard layout. Supports listing available locales and timezones,
and shows current status.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-locale-setup %{buildroot}%{_bindir}/solus-locale-setup

%files
%{_bindir}/solus-locale-setup

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-locale-setup package
- Commands: locale, timezone, keyboard, list-locales, list-timezones, status
