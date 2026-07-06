# Solus Linux RPM Spec — procs
# Modern replacement for ps (process list) written in Rust
# Origin: Fedora, Arch Linux, FreeBSD
%global procs_version 0.14.9

Name: procs
Version: %{procs_version}
Release: 1%{?dist}
Summary: Modern replacement for ps — process information with color and tree view
License: MIT
URL: https://github.com/dalance/procs
Source0: https://crates.io/api/v1/crates/procs/%{procs_version}/download#procs-%{procs_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A modern replacement for ps written in Rust. Procs provides:
- Colorized process list
- Tree view (like pstree)
- Docker container awareness
- TCP/UDP port listing
- Systemd unit integration
- Watch mode (like htop)
- Customizable columns
- Mouse support in interactive mode
- Cross-platform (Linux, macOS, Windows)

%prep
%setup -q -n procs-%{procs_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/procs %{buildroot}%{_bindir}/procs

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
./target/release/procs --completion bash > %{buildroot}%{_datadir}/bash-completion/completions/procs 2>/dev/null || true
./target/release/procs --completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_procs 2>/dev/null || true
./target/release/procs --completion fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/procs.fish 2>/dev/null || true

%files
%{_bindir}/procs
%{_datadir}/bash-completion/completions/procs
%{_datadir}/zsh/site-functions/_procs
%{_datadir}/fish/vendor_completions.d/procs.fish

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.14.9-1
- Initial Solus package
- Modern ps replacement in Rust
