# SynthOS RPM Spec — zellij
# Terminal multiplexer (tmux replacement) written in Rust
# Origin: Fedora, Arch Linux
%global zellij_version 0.41.1

Name: zellij
Version: %{zellij_version}
Release: 1%{?dist}
Summary: Terminal multiplexer with a workspace-oriented layout engine
License: MIT
URL: https://zellij.dev
Source0: https://crates.io/api/v1/crates/zellij/%{zellij_version}/download#zellij-%{zellij_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

Requires: (tmux or screen)

%description
A terminal workspace with batteries included — written in Rust.
Zellij is a terminal multiplexer similar to tmux/screen, but with a
cleaner UX, split panels, floating panes, session management, and
built-in plugin system. Works out of the box with no configuration.

Features:
- Intuitive default keybindings
- Split panes and tabs
- Floating and stacked panes
- Session restore
- Plugin system (node, WASM)
- True color support
- Mouse mode
- Layout system via YAML/JSON/KDL

%prep
%setup -q -n zellij-%{zellij_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/zellij %{buildroot}%{_bindir}/zellij

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
./target/release/zellij setup --generate-completion bash > %{buildroot}%{_datadir}/bash-completion/completions/zellij 2>/dev/null || true
./target/release/zellij setup --generate-completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_zellij 2>/dev/null || true
install -m 0644 docs/man/man1/zellij.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

%files
%{_bindir}/zellij
%{_mandir}/man1/zellij.1*
%{_datadir}/bash-completion/completions/zellij
%{_datadir}/zsh/site-functions/_zellij

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - 0.41.1-1
- Initial Synthex package
- Rust-based terminal multiplexer
