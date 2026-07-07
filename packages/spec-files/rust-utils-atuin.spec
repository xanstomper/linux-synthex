# SynthOS RPM Spec — atuin
# Shell history with sync (Rust)
# Origin: Fedora, Arch Linux

%global atuin_version 18.4.0

Name: atuin
Version: %{atuin_version}
Release: 1%{?dist}
Summary: Magical shell history — syncs, searches, and deduplicates shell history
License: MIT
URL: https://atuin.sh
Source0: https://github.com/atuinsh/atuin/archive/refs/tags/v%{atuin_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
Magical shell history. Atuin replaces your existing shell history with an
SQLite-backed database that supports search, sync, and deduplication.

Features:
- Encrypted sync across devices (server or self-hosted)
- Full-text search (Ctrl+R replacement)
- Backup and restore history
- Statistics: most used commands, directories, etc.
- Multi-session support
- Context: shows working directory, exit code, duration, hostname
- Tags and metadata on commands
- Shell integration for bash, zsh, fish
- Import from bash, zsh, fish history
- Cross-platform

%prep
%autosetup -n atuin-v%{atuin_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/atuin %{buildroot}%{_bindir}/atuin

%files
%{_bindir}/atuin

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{atuin_version}-1
- Initial Synthex package — atuin
- Ported from Fedora and Arch Linux packaging
