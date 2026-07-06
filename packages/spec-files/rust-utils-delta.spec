# Solus Linux RPM Spec — git-delta
# Syntax-highlighting pager for git, diff, and grep output (Rust)
# Origin: Fedora, Arch Linux
%global delta_version 0.18.2

Name: git-delta
Version: %{delta_version}
Release: 1%{?dist}
Summary: Syntax-highlighting pager for git and diff output
License: MIT
URL: https://dandavison.github.io/delta
Source0: https://crates.io/api/v1/crates/git-delta/%{delta_version}/download#git-delta-%{delta_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

Requires: git
Recommends: bat

%description
A syntax-highlighting pager for git, diff, and grep output.
Delta is written in Rust and provides a modern replacement for
git's built-in diff viewer with side-by-side layout, syntax
highlighting, line numbers, and rich color output.

Features:
- Side-by-side diff view
- Syntax highlighting (via syntect)
- Line numbers and modification markers
- Word-level diff highlighting
- Git blame style annotations
- Configurable themes
- Catppuccin, Monokai, Dracula, and more built-in themes

%prep
%setup -q -n git-delta-%{delta_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/delta %{buildroot}%{_bindir}/delta

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
install -m 0644 etc/man/delta.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

%files
%{_bindir}/delta
%{_mandir}/man1/delta.1*

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.18.2-1
- Initial Solus package
- Rust-based git diff pager
