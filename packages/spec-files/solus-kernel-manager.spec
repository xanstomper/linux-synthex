%define _name solus-kernel-manager
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux kernel management tool — list, install, switch, remove, cleanup

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-kernel-manager
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       dnf5
Requires:       grubby

%description
solus-kernel-manager provides commands to list installed kernels, install
new kernels, switch the default boot kernel, remove old kernels, show kernel
info, and clean up old kernels (keeping current + 1 backup).

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-kernel-manager %{buildroot}%{_bindir}/solus-kernel-manager

%files
%{_bindir}/solus-kernel-manager

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-kernel-manager package
- Commands: list, install, switch, remove, info, cleanup
