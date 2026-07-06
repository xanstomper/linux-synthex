%define _name solus-service-manager
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux systemd service manager — start/stop/enable/disable/status

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-service-manager
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       systemd

%description
solus-service-manager provides a command-line interface to manage systemd
services. Commands include list (running/failed/enabled/disabled/all),
start, stop, restart, enable, disable, mask, unmask, and status.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-service-manager %{buildroot}%{_bindir}/solus-service-manager

%files
%{_bindir}/solus-service-manager

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-service-manager package
- Commands: list, start, stop, restart, enable, disable, status, failed
