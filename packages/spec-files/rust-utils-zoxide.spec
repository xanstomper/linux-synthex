# SynthOS RPM Spec — zoxide
# Smarter cd command in Rust
# Origin: Fedora, Arch Linux

%global zoxide_version 0.9.7

Name: zoxide
Version: %{zoxide_version}
Release: 1%{?dist}
Summary: Smarter cd command — remembers your directories and jumps to them
License: MIT
URL: https://github.com/ajeetdsouza/zoxide
Source0: https://github.com/ajeetdsouza/zoxide/archive/refs/tags/v%{zoxide_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A smarter cd command for your terminal. Zoxide learns which directories you
use most frequently and lets you jump to them with minimal keystrokes.
Written in Rust for maximum performance.

Features:
- Fuzzy matching: jump to directories by typing part of their name
- Interactive selection: pick from a list of matching directories
- Learning: automatically learns your most-used directories
- Shell integration: works with bash, zsh, fish, nu, elvish, powershell
- Instant: Rust-powered with tiny memory footprint
- Tab-completion: use tab to cycle through matches
- Cross-platform: Linux, macOS, Windows

%prep
%setup -q -n synthex-repo-0.9.7
%autosetup -n zoxide-v%{zoxide_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/zoxide %{buildroot}%{_bindir}/zoxide

%files
%{_bindir}/zoxide

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{zoxide_version}-1
- Initial Synthex package — zoxide
- Ported from Fedora packaging
