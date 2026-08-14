Name:           synthupdate
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS synthupdate

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  rust-toolchain
BuildRequires:  cargo

%description
SynthOS synthupdate Part of the SynthOS system suite.

%build
cargo build --release

%install
install -Dm755 target/release/synthupdate %{buildroot}%{_bindir}/synthupdate

%files
%{_bindir}/synthupdate

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthupdate package
