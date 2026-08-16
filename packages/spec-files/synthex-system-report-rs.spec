Name:           synthex-system-report-rs
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS system report CLI — hardware/software diagnostic dump

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthOS system report CLI — hardware/software diagnostic dump. Part of the SynthOS Rust tools suite (replaces the earlier
Python prototypes with a single fast static binary).


%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-system-report-rs target/release/synthex-system-report-rs
%install
install -Dm755 target/release/synthex-system-report-rs %{buildroot}%{_bindir}/synthex-system-report-rs

%files
%{_bindir}/synthex-system-report-rs

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-system-report-rs package
