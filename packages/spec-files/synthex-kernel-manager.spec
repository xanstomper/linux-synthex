%define _name synthex-kernel-manager
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS kernel management tool — list, install, switch, remove, cleanup

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-kernel-manager
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       dnf5
Requires:       grubby

%description
synthex-kernel-manager provides commands to list installed kernels, install
new kernels, switch the default boot kernel, remove old kernels, show kernel
info, and clean up old kernels (keeping current + 1 backup).

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 synthex-kernel-manager %{buildroot}%{_bindir}/synthex-kernel-manager

%files
%{_bindir}/synthex-kernel-manager

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-kernel-manager package
- Commands: list, install, switch, remove, info, cleanup
