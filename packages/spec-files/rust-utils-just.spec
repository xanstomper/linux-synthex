# Solus Linux RPM Spec — just
# Command runner (make alternative) written in Rust
# Origin: Fedora, Arch Linux
%global just_version 1.39.0

Name: just
Version: %{just_version}
Release: 1%{?dist}
Summary: A command runner for project-specific tasks — like make, but simpler
License: CC0-1.0
URL: https://github.com/casey/just
Source0: https://crates.io/api/v1/crates/just/%{just_version}/download#just-%{just_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
just is a command runner written in Rust that provides a clean,
minimal syntax for running project-specific commands. It's like
make, but without the complexity of build system semantics.

just is a handy way to save and run project-specific commands.
Commands (called recipes) are stored in a file called justfile
with syntax that's much cleaner than Makefile.

Features:
- Clean, simple syntax (not Makefile-compatible)
- Cross-platform (Linux, macOS, Windows)
- Dependencies between recipes
- Conditional recipes
- Recipes with arguments
- Support for multiple justfiles
- Environment variable passthrough
- Shell-agnostic

%prep
%setup -q -n just-%{just_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/just %{buildroot}%{_bindir}/just

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
install -m 0644 man/just.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/just --completions bash > %{buildroot}%{_datadir}/bash-completion/completions/just 2>/dev/null || true
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
./target/release/just --completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_just 2>/dev/null || true
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
./target/release/just --completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/just.fish 2>/dev/null || true

%files
%{_bindir}/just
%{_mandir}/man1/just.1*
%{_datadir}/bash-completion/completions/just
%{_datadir}/zsh/site-functions/_just
%{_datadir}/fish/vendor_completions.d/just.fish

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 1.39.0-1
- Initial Solus package
- Command runner in Rust (make alternative)
