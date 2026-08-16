Name:           synthex-meshnet
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS LAN mesh daemon — mDNS discovery, encrypted relay, clipboard sync

License:        GPL-3.0-or-later
URL:            https://getsynthex.io

BuildRequires:  rust
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros

Source0:        synthex-repo-2026.10.tar.gz
%description
synthex-meshnet discovers other SynthOS machines on the local network via mDNS
and relays short messages (clipboard sync, drop-zone hand-off) over a TCP channel.
Payloads are best-effort age-encrypted on the wire. A unique, package-level LAN
collaboration feature not found in other distributions.

%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-meshnet target/release/synthex-meshnet
%install
install -Dm755 target/release/synthex-meshnet %{buildroot}%{_bindir}/synthex-meshnet
install -Dm644 systemd/synthex-meshnet.service %{buildroot}%{_unitdir}/synthex-meshnet.service

%files
%{_bindir}/synthex-meshnet
%{_unitdir}/synthex-meshnet.service

%post
%systemd_post synthex-meshnet.service

%preun
%systemd_preun synthex-meshnet.service

%postun
%systemd_postun_with_restart synthex-meshnet.service

%changelog
* Fri Jul 10 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-meshnet package
- mDNS LAN discovery of SynthOS peers
- Encrypted TCP relay for clipboard sync and drop-zone hand-off
