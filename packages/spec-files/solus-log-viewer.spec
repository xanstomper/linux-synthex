%define _name solus-log-viewer
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux system log viewer — journalctl wrapper with filtering

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-log-viewer
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       systemd

%description
solus-log-viewer provides a filtered view of system logs via journalctl.
Commands include boot (current boot), kernel (dmesg), errors, warnings,
today, service (specific service), follow (live tail), search, and boots
(boot history).

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-log-viewer %{buildroot}%{_bindir}/solus-log-viewer

%files
%{_bindir}/solus-log-viewer

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-log-viewer package
- Commands: boot, kernel, errors, warnings, service, follow, search, boots
