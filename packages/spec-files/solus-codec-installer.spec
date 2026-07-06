%define _name solus-codec-installer
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux one-click multimedia codec installer

License:        GPL-2.0-or-later
URL:            https://getsol.us
Source0:        solus-codec-installer
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       bash
Requires:       solus-codec-pack

%description
solus-codec-installer is a Nobara-style one-click codec installer that
installs the full multimedia codec pack and verifies that H.264, H.265,
AV1, GStreamer, VAAPI, DVD, and VLC support are all active.

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_bindir}
install -m 0755 solus-codec-installer %{buildroot}%{_bindir}/solus-codec-installer

%files
%{_bindir}/solus-codec-installer

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-codec-installer package
- One-click codec setup with verification
