Name:           synthex-drip-sync
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Drip-Sync — multi-distro upstream update synchronization engine

License:        MIT OR Apache-2.0
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  systemd-rpm-macros
Requires:       systemd
Requires(post): systemd
Requires(preun): systemd

%description
Drip-sync synchronizes curated upstream improvements (CachyOS scheduler
tuning, Nobara gaming fixes, Bazzite/Mint UX patches) into SynthOS via
small, reviewable, atomic changes ("drips"). Ships the CLI plus a systemd
service + timer (daily apply window).

Privacy: only runs when explicitly enabled — see /etc/synthex/privacy.conf
(integration_engine/drip-sync are opt-in, OFF by default).

%prep
%setup -q -n synthex-repo-%{version}

%build
cargo build --release -p synthex-drip-sync

%install
install -Dm755 target/release/synthex-drip-sync %{buildroot}%{_bindir}/synthex-drip-sync
install -Dm644 systemd/synthex-drip-sync.service %{buildroot}%{_unitdir}/synthex-drip-sync.service
install -Dm644 systemd/synthex-drip-sync.timer %{buildroot}%{_unitdir}/synthex-drip-sync.timer

%files
%{_bindir}/synthex-drip-sync
%{_unitdir}/synthex-drip-sync.service
%{_unitdir}/synthex-drip-sync.timer

%post
%systemd_post synthex-drip-sync.timer

%preun
%systemd_preun synthex-drip-sync.timer

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-drip-sync package (upstream drip-feed engine + daily timer)
