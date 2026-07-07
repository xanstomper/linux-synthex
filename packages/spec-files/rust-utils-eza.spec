# SynthOS RPM Spec — eza (modern ls replacement)
# A modern, maintained fork of exa, written in Rust
# Origin: https://github.com/eza-community/eza

%global eza_version 0.20.4

Name: eza
Version: %{eza_version}
Release: 1%{?dist}
Summary: A modern, maintained replacement for ls, written in Rust
License: MIT
URL: https://github.com/eza-community/eza
Source0: https://github.com/eza-community/eza/archive/refs/tags/v%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.76.0
BuildRequires: pkgconfig
BuildRequires: zlib-devel, libgit2-devel

Requires: rust-toolchain-compiler

%description
eza is a modern replacement for ls, the command line file lister.
It uses colours to distinguish file types and metadata, supports
symlinks, extended attributes, and Git integration.

Key features:
- Colour-coded output by file type, metadata, and security context
- Grid view, long view, and icon view
- Git status indicators (staged, modified, new, deleted)
- Extended attributes and SELinux context display
- Tree view with --tree (replaces tree command)
- File icons with --icons
- Colour themes (gruvbox, solarized, etc.)
- Faster than ls for large directories

Part of the Synthex Rust utility suite — replaces ls, tree, and ll.

%prep
%setup -q -n eza-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/eza %{buildroot}%{_bindir}/eza
install -D -m 0644 man/eza.1 %{buildroot}%{_mandir}/man1/eza.1
install -D -m 0644 man/eza_colors.5 %{buildroot}%{_mandir}/man5/eza_colors.5
ln -sf eza %{buildroot}%{_bindir}/l

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/eza --completions bash > %{buildroot}%{_datadir}/bash-completion/completions/eza
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/eza --completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_eza
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/eza --completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/eza.fish

%files
%{_bindir}/eza
%{_bindir}/l
%{_mandir}/man1/eza.1*
%{_mandir}/man5/eza_colors.5*
%{_datadir}/bash-completion/completions/eza
%{_datadir}/zsh/site-functions/_eza
%{_datadir}/fish/vendor_completions.d/eza.fish
%doc README.md LICENSE

%changelog
* Sun Jul 06 2026 Synthex Rust Team <rust@synthex-project.org> - 0.20.4-1
- Initial Synthex package of eza 0.20.4
- ls replacement — colourised, Git-aware, tree view, icons
- Shell completions: bash, zsh, fish
- Provides 'l' alias for quick listings
