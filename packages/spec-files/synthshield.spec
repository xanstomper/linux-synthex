Name:           synthshield
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthShield — SynthOS file integrity & snapshot manager

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  rust-toolchain
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros
Requires:       btrfs-progs
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
SynthShield scans installed files for integrity drift and manages btrfs
snapshot-based rollback points. Ships the synthshield CLI and the
synthex-synthshield.service system unit.

%build
cargo build --release

%install
install -Dm755 target/release/synthshield %{buildroot}%{_bindir}/synthshield
install -Dm644 systemd/synthex-synthshield.service %{buildroot}%{_unitdir}/synthex-synthshield.service

%files
%{_bindir}/synthshield
%{_unitdir}/synthex-synthshield.service

%post
%systemd_post synthex-synthshield.service

%preun
%systemd_preun synthex-synthshield.service

%postun
%systemd_postun_with_restart synthex-synthshield.service

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthshield package (file integrity + snapshots)
