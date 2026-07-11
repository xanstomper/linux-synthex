# SynthOS RPM Spec — helix
# Modal text editor in Rust
# Origin: Fedora, Arch Linux

%global helix_version 25.1.0

Name: helix
Version: %{helix_version}
Release: 1%{?dist}
Summary: Modal text editor — Rust-powered editor with tree-sitter + LSP support
License: MPL-2.0
URL: https://helix-editor.com
Source0: https://github.com/helix-editor/helix/releases/download/%{helix_version}/helix-%{helix_version}-x86_64-linux.tar.xz

BuildRequires: tar, xz
Requires: nodejs
Recommends: rust-toolchain, lldb

%description
A post-modern modal text editor written in Rust. Helix combines the best of
Vim-style modal editing with built-in Language Server Protocol (LSP) support,
tree-sitter syntax highlighting, and a built-in debugger.

Key features:
- Modal editing (Vim-like) with multiple selection
- Built-in LSP client for 100+ languages
- Tree-sitter syntax highlighting and parsing
- Built-in debugger (DAP) support
- Fuzzy file finder and search
- Auto-completion and signature help
- Code actions and diagnostics
- Multi-cursor and multi-selection editing
- Cross-platform (Linux, macOS, Windows)

%prep
%setup -q -n helix-%{helix_version}-x86_64-linux

%build
# Nothing to compile — noarch data/script package

%install
install -D -m 0755 helix %{buildroot}%{_bindir}/hx
install -D -m 0755 helix-term %{buildroot}%{_bindir}/helix-term 2>/dev/null || true

# Runtime files
mkdir -p %{buildroot}%{_datadir}/helix/runtime
cp -r runtime/* %{buildroot}%{_datadir}/helix/runtime/

%files
%{_bindir}/hx
%{_bindir}/helix-term
%{_datadir}/helix/runtime/

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{helix_version}-1
- Initial Synthex package — helix editor
- Pre-built binary from upstream (full Rust build with tree-sitter + LSP)
- Ported from Fedora packaging
