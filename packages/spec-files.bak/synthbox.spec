Name:           synthbox
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthBox — Sandboxed Application Runner

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz

BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthBox — Sandboxed Application Runner Part of the SynthOS system suite.

%build
cargo build --release

%install
install -Dm755 target/release/synthbox %{buildroot}%{_bindir}/synthbox

%files
%{_bindir}/synthbox

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthbox package
