# SynthOS RPM Spec — dust (du replacement)
# More intuitive than du, written in Rust
# Origin: https://github.com/bootandy/dust

%global dust_version 1.1.1

Name: dust
Version: %{dust_version}
Release: 1%{?dist}
Summary: A more intuitive version of du, written in Rust
License: Apache-2.0
URL: https://github.com/bootandy/dust
Source0: https://github.com/bootandy/dust/archive/refs/tags/v%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.65.0

Requires: rust-toolchain-compiler

%description
dust (du + rust = dust) is a more intuitive version of du.
It displays disk usage in a visually appealing way, ordering
directories by size and showing bars for quick comparison.

Key features:
- Visual bar chart showing relative directory sizes
- Automatically sorts by size (largest first)
- Shows only what fits on screen by default
- Can drill down into subdirectories
- Coloured output by file type
- Understands SI and binary units
- Detects terminal width for responsive display

Part of the Synthex Rust utility suite — replaces du -sh *.

%prep
%setup -q -n dust-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/dust %{buildroot}%{_bindir}/dust
ln -sf dust %{buildroot}%{_bindir}/du-dust

%files
%{_bindir}/dust
%{_bindir}/du-dust
%doc README.md LICENSE

%changelog
* Sun Jul 06 2026 Synthex Rust Team <rust@synthex-project.org> - 1.1.1-1
- Initial Synthex package of dust 1.1.1
- du replacement — visual bar charts, sorted by size
