Name:           synthnet
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS synthnet

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz

BuildRequires:  rust-toolchain
BuildRequires:  cargo

%description
SynthOS synthnet Part of the SynthOS system suite.

%build
cargo build --release

%install
install -Dm755 target/release/synthnet %{buildroot}%{_bindir}/synthnet

%files
%{_bindir}/synthnet

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthnet package
