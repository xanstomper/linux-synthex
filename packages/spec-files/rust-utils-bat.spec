# Solus Linux RPM Spec — bat
# A cat(1) clone with syntax highlighting and Git integration
# Origin: https://github.com/sharkdp/bat

%global bat_version 0.24.0

Name: bat
Version: %{bat_version}
Release: 1%{?dist}
Summary: A cat(1) clone with wings — syntax highlighting and Git integration
License: MIT OR Apache-2.0
URL: https://github.com/sharkdp/bat
Source0: https://github.com/sharkdp/bat/archive/refs/tags/v%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.70.0
BuildRequires: pkgconfig
BuildRequires: zlib-devel

Requires: rust-toolchain-compiler

%description
bat is a cat(1) clone with syntax highlighting for over 200 languages
and Git integration. It displays the contents of a file with line numbers,
changes, and syntax-coloured output.

Key features:
- Syntax highlighting for 200+ languages
- Git change markers in the gutter
- Automatic paging with less
- Line numbers and column rulers
- File concatenation (like cat)
- Show non-printable characters
- Customisable themes (over 30 built-in)
- Paging, searching, and customisation

Part of the Solus Rust utility suite.

%prep
%setup -q -n bat-v%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/bat %{buildroot}%{_bindir}/bat
install -D -m 0644 assets/man/bat.1 %{buildroot}%{_mandir}/man1/bat.1
# "batcat" symlink for Debian/Fedora compat
ln -sf bat %{buildroot}%{_bindir}/batcat

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/bat --completion bash > %{buildroot}%{_datadir}/bash-completion/completions/bat
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/bat --completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_bat
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/bat --completion fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/bat.fish

%files
%{_bindir}/bat
%{_bindir}/batcat
%{_mandir}/man1/bat.1*
%{_datadir}/bash-completion/completions/bat
%{_datadir}/zsh/site-functions/_bat
%{_datadir}/fish/vendor_completions.d/bat.fish
%doc README.md LICENSE-MIT

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 0.24.0-1
- Initial Solus package of bat 0.24.0
- cat replacement — syntax highlighting, Git integration, paging
- Shell completions: bash, zsh, fish
