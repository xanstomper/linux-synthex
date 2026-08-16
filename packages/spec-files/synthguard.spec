Name:           synthguard
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthGuard — SynthOS kernel security monitor (audit, integrity, threats)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros
Requires:       audit
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
SynthGuard is the SynthOS kernel security monitor. It watches the kernel
audit subsystem, verifies file integrity against recorded baselines and
surfaces threat detections. Ships the synthguard CLI plus the
synthex-synthguard.service system unit (two ExecStart lines: the long-running
monitor and the one-shot integrity check wired via ExecStartPost).


%prep
%setup -q -n synthex-repo-2026.10

%build
cargo build --release

%install
install -Dm755 target/release/synthguard %{buildroot}%{_bindir}/synthguard
install -Dm644 systemd/synthex-synthguard.service %{buildroot}%{_unitdir}/synthex-synthguard.service

%files
%{_bindir}/synthguard
%{_unitdir}/synthex-synthguard.service

%post
%systemd_post synthex-synthguard.service

%preun
%systemd_preun synthex-synthguard.service

%postun
%systemd_postun_with_restart synthex-synthguard.service

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthguard package (kernel security monitor)
- Ships synthex-synthguard.service system unit
