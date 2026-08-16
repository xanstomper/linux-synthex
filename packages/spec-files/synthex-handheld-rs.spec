Name:           synthex-handheld-rs
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS handheld integration CLI — controllers, TDP, handheld profiles

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthOS handheld integration CLI — controllers, TDP, handheld profiles. Part of the SynthOS Rust tools suite (replaces the earlier
Python prototypes with a single fast static binary).


%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-handheld-rs target/release/synthex-handheld-rs
%install
install -Dm755 target/release/synthex-handheld-rs %{buildroot}%{_bindir}/synthex-handheld-rs

%files
%{_bindir}/synthex-handheld-rs

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-handheld-rs package
