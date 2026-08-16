Name:           synthvault
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthVault — SynthOS secure storage manager (LUKS2 + TPM2)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros
Requires:       cryptsetup
Requires:       tpm2-tools
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd

%description
SynthVault manages SynthOS secure storage: LUKS2 volumes, TPM2 sealing and
the lockdown action exposed via synthex-synthvault.service.


%prep
%setup -q -n synthex-repo-2026.10

%build
cargo build --release

%install
install -Dm755 target/release/synthvault %{buildroot}%{_bindir}/synthvault
install -Dm644 systemd/synthex-synthvault.service %{buildroot}%{_unitdir}/synthex-synthvault.service

%files
%{_bindir}/synthvault
%{_unitdir}/synthex-synthvault.service

%post
%systemd_post synthex-synthvault.service

%preun
%systemd_preun synthex-synthvault.service

%postun
%systemd_postun_with_restart synthex-synthvault.service

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthvault package (LUKS2 + TPM2 secure storage)
