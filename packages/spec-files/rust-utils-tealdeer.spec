# SynthOS RPM Spec — tealdeer
# TLDR client written in Rust
# Origin: Fedora, Arch Linux

%global tealdeer_version 1.7.0

Name: tealdeer
Version: %{tealdeer_version}
Release: 1%{?dist}
Summary: TLDR client — fast, offline man page summaries (Rust)
License: MIT OR Apache-2.0
URL: https://dbrgn.github.io/tealdeer
Source0: https://github.com/dbrgn/tealdeer/archive/refs/tags/v%{tealdeer_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A very fast implementation of tldr in Rust. TLD pages are simplified,
community-driven man pages that show the most common commands for a tool.
Tealdeer provides offline, instant access to these pages.

Features:
- Instant startup (sub-millisecond)
- Offline page cache
- Autocomplete commands
- Colorized output
- Custom themes
- Language support (pages available in multiple languages)
- Fish shell completion
- Auto-update page cache

%prep
%setup -q -n synthex-repo-1.7.0
%autosetup -n tealdeer-v%{tealdeer_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/tldr %{buildroot}%{_bindir}/tldr

%files
%{_bindir}/tldr

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{tealdeer_version}-1
- Initial Synthex package — tealdeer (tldr client)
- Ported from Fedora packaging
