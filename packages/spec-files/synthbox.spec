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


%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthbox target/release/synthbox
%install
install -Dm755 target/release/synthbox %{buildroot}%{_bindir}/synthbox

%files
%{_bindir}/synthbox

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthbox package
