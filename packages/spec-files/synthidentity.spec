Name:           synthidentity
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthIdentity — Encrypted Credential Manager

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthIdentity — Encrypted Credential Manager Part of the SynthOS system suite.

%build
cargo build --release

%install
install -Dm755 target/release/synthidentity %{buildroot}%{_bindir}/synthidentity

%files
%{_bindir}/synthidentity

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthidentity package
