%define _name synthex-service-manager
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS systemd service manager — start/stop/enable/disable/status

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-service-manager
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       systemd

%description
synthex-service-manager provides a command-line interface to manage systemd
services. Commands include list (running/failed/enabled/disabled/all),
start, stop, restart, enable, disable, mask, unmask, and status.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 synthex-service-manager %{buildroot}%{_bindir}/synthex-service-manager

%files
%{_bindir}/synthex-service-manager

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-service-manager package
- Commands: list, start, stop, restart, enable, disable, status, failed
