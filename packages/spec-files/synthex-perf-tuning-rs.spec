Name:           synthex-perf-tuning-rs
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS performance tuning CLI — governor, I/O scheduler, sysctl profiles

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthOS performance tuning CLI — governor, I/O scheduler, sysctl profiles. Part of the SynthOS Rust tools suite (replaces the earlier
Python prototypes with a single fast static binary).


%prep
%setup -q -n synthex-repo-2026.10

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-perf-tuning-rs target/release/synthex-perf-tuning-rs
%install
install -Dm755 target/release/synthex-perf-tuning-rs %{buildroot}%{_bindir}/synthex-perf-tuning-rs

%files
%{_bindir}/synthex-perf-tuning-rs

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-perf-tuning-rs package
