Name:           synthex-codec-installer-rs
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS codec installer CLI — RPM Fusion media codec stack

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildRequires:  rust >= 1.75
BuildRequires:  cargo

%description
SynthOS codec installer CLI — RPM Fusion media codec stack. Part of the SynthOS Rust tools suite (replaces the earlier
Python prototypes with a single fast static binary).


%prep
%setup -q -n synthex-repo-2026.10

%build
cargo build --release

%install
install -Dm755 target/release/synthex-codec-installer-rs %{buildroot}%{_bindir}/synthex-codec-installer-rs

%files
%{_bindir}/synthex-codec-installer-rs

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-codec-installer-rs package
