# Solus Linux RPM Spec — fd-find (fd)
# Faster than find, written in Rust, sensible defaults
# Origin: https://github.com/sharkdp/fd

%global fd_version 10.2.0

Name: fd-find
Version: %{fd_version}
Release: 1%{?dist}
Summary: Simple, fast, and user-friendly alternative to find
License: MIT OR Apache-2.0
URL: https://github.com/sharkdp/fd
Source0: https://github.com/sharkdp/fd/archive/refs/tags/v%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.70.0

Requires: rust-toolchain-compiler

%description
fd is a program to find entries in your filesystem. It is a
modern, fast, and user-friendly alternative to the traditional
find command.

Key features:
- Convenient syntax: fd PATTERN instead of find -iname '*PATTERN*'
- Colorized terminal output (similar to ls)
- Parallel command execution
- Smart case: case-insensitive by default, switches to case-sensitive
  if the pattern contains an uppercase character
- Ignores hidden directories and .gitignore by default
- Unicode-aware
- Regular expression and glob-based patterns

Part of the Solus Rust utility suite.

%prep
%setup -q -n fd-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/fd %{buildroot}%{_bindir}/fd
ln -sf fd %{buildroot}%{_bindir}/fdfind
install -D -m 0644 doc/fd.1 %{buildroot}%{_mandir}/man1/fd.1

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/fd --gen-completions bash > %{buildroot}%{_datadir}/bash-completion/completions/fd
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/fd --gen-completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_fd
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/fd --gen-completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/fd.fish

%files
%{_bindir}/fd
%{_bindir}/fdfind
%{_mandir}/man1/fd.1*
%{_datadir}/bash-completion/completions/fd
%{_datadir}/zsh/site-functions/_fd
%{_datadir}/fish/vendor_completions.d/fd.fish
%doc README.md LICENSE-APACHE

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 10.2.0-1
- Initial Solus package of fd-find 10.2.0
- find replacement — fast, colorized, .gitignore-aware
- Shell completions: bash, zsh, fish
