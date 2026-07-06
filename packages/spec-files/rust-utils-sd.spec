# Solus Linux RPM Spec — sd (sed replacement)
# An intuitive find & replace CLI, written in Rust
# Origin: https://github.com/chmln/sd

%global sd_version 1.0.0

Name: sd
Version: %{sd_version}
Release: 1%{?dist}
Summary: An intuitive find & replace CLI, replacement for sed
License: MIT
URL: https://github.com/chmln/sd
Source0: https://github.com/chmln/sd/archive/refs/tags/v%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.65.0

Requires: rust-toolchain-compiler

%description
sd is an intuitive find and replace CLI tool, designed as a
modern alternative to sed for common string replacement tasks.

Key features:
- Simple syntax: sd 'before' 'after' file.txt
  (no cryptic flags like sed -i 's/foo/bar/g')
- Regex and literal string modes
- In-place file editing
- Works with stdin/stdout for piping
- Sane defaults — no surprises
- UTF-8 aware by default
- Faster than sed for most common patterns

Part of the Solus Rust utility suite — replaces sed for most use cases.

%prep
%setup -q -n sd-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/sd %{buildroot}%{_bindir}/sd

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/sd -c bash > %{buildroot}%{_datadir}/bash-completion/completions/sd
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/sd -c zsh > %{buildroot}%{_datadir}/zsh/site-functions/_sd

%files
%{_bindir}/sd
%{_datadir}/bash-completion/completions/sd
%{_datadir}/zsh/site-functions/_sd
%doc README.md LICENSE

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 1.0.0-1
- Initial Solus package of sd 1.0.0
- sed replacement — intuitive find & replace syntax
- Shell completions: bash, zsh
