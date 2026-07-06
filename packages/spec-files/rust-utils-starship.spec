# Solus Linux RPM Spec — starship
# Cross-shell prompt customization (Rust)
# Origin: Fedora, crates.io
%global starship_version 1.22.1

Name: starship
Version: %{starship_version}
Release: 1%{?dist}
Summary: Cross-shell prompt — minimal, blazing-fast, infinitely customizable
License: ISC
URL: https://starship.rs
Source0: https://crates.io/api/v1/crates/starship/%{starship_version}/download#starship-%{starship_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

Requires: fontconfig
Recommends: (nerd-fonts-fira-code or nerd-fonts-meslo or fira-code-fonts)

%description
The minimal, blazing-fast, and infinitely customizable prompt for any shell!
Starship is written in Rust and provides a single, minimal prompt that works
in bash, zsh, fish, ion, tcsh, elvish, nu, and PowerShell.

Features:
- Git status indicator
- Package version (cargo, node, python, go, ruby, rust, etc.)
- Command duration
- Directory truncation
- Battery level
- Time display
- Custom commands
- Nerd Font icons

%prep
%setup -q -n starship-%{starship_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/starship %{buildroot}%{_bindir}/starship

# Shell init completions
mkdir -p %{buildroot}%{_datadir}/starship
./target/release/starship completions bash > %{buildroot}%{_datadir}/starship/starship.bash 2>/dev/null || true
./target/release/starship completions zsh > %{buildroot}%{_datadir}/starship/starship.zsh 2>/dev/null || true
./target/release/starship completions fish > %{buildroot}%{_datadir}/starship/starship.fish 2>/dev/null || true

%files
%{_bindir}/starship
%{_datadir}/starship/*

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 1.22.1-1
- Initial Solus package
- Rust-based cross-shell prompt
