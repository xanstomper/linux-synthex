Name:           synthex-proton-manager-rs
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Proton manager — install/switch Proton-GE builds per game

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthOS Proton manager — install/switch Proton-GE builds per game. Part of the SynthOS Rust tools suite (replaces the earlier
Python prototypes with a single fast static binary).

%build
cargo build --release

%install
install -Dm755 target/release/synthex-proton-manager-rs %{buildroot}%{_bindir}/synthex-proton-manager-rs

%files
%{_bindir}/synthex-proton-manager-rs

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-proton-manager-rs package
