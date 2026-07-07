%define _name synthex-log-viewer
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS system log viewer — journalctl wrapper with filtering

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-log-viewer
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       systemd

%description
synthex-log-viewer provides a filtered view of system logs via journalctl.
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
install -m 0755 synthex-log-viewer %{buildroot}%{_bindir}/synthex-log-viewer

%files
%{_bindir}/synthex-log-viewer

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-log-viewer package
- Commands: boot, kernel, errors, warnings, service, follow, search, boots
