# SynthOS RPM Spec — ripgrep (rg)
# Faster than grep, written in Rust, recursive by default
# Origin: https://github.com/BurntSushi/ripgrep

%global rg_version 14.1.0

Name: ripgrep
Version: %{rg_version}
Release: 1%{?dist}
Summary: Ultra-fast grep replacement written in Rust
License: MIT OR Unlicense
URL: https://github.com/BurntSushi/ripgrep
Source0: https://github.com/BurntSushi/ripgrep/archive/refs/tags/%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.75.0
BuildRequires: pkgconfig

Requires: rust-toolchain-compiler

%description
ripgrep (rg) is a line-oriented search tool that recursively searches
your current directory for a regex pattern. By default it respects
.gitignore rules and automatically skips hidden files and binary files.

Key features:
- Recursive by default — no need to pipe to find/xargs
- Automatically respects .gitignore
- Searches for patterns in file contents (not filenames)
- Colorized output by default
- UTF-8 and binary file support
- SIMD-accelerated regex engine

This is part of the Synthex Rust utility suite — modern replacements
for classic Unix tools, compiled from Rust for safety and speed.

%prep
%setup -q -n ripgrep-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/rg %{buildroot}%{_bindir}/rg
install -D -m 0644 doc/rg.1 %{buildroot}%{_mandir}/man1/rg.1
ln -sf rg %{buildroot}%{_bindir}/ripgrep

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/rg --generate complete-bash > %{buildroot}%{_datadir}/bash-completion/completions/rg
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/rg --generate complete-zsh > %{buildroot}%{_datadir}/zsh/site-functions/_rg
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/rg --generate complete-fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/rg.fish

%files
%{_bindir}/rg
%{_bindir}/ripgrep
%{_mandir}/man1/rg.1*
%{_datadir}/bash-completion/completions/rg
%{_datadir}/zsh/site-functions/_rg
%{_datadir}/fish/vendor_completions.d/rg.fish
%doc README.md LICENSE-MIT

%changelog
* Sun Jul 06 2026 Synthex Rust Team <rust@synthex-project.org> - 14.1.0-1
- Initial Synthex package of ripgrep 14.1.0
- grep replacement — recursive, .gitignore-aware, SIMD regex
- Shell completions: bash, zsh, fish
