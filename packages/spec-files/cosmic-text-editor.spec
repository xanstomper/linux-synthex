# SynthOS RPM Spec — cosmic-text-editor
# COSMIC text editor (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicte_version 24.04.0

Name: cosmic-text-editor
Version: %{cosmicte_version}
Release: 1%{?dist}
Summary: COSMIC text editor — modern text editor for the COSMIC desktop
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-text-editor
Source0: https://github.com/pop-os/cosmic-text-editor/archive/refs/tags/v%{cosmicte_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC text editor is a modern GUI text editor for the COSMIC desktop
environment. Written in Rust with Iced, it provides:

- Syntax highlighting for 100+ languages
- Line numbers and code folding
- Multi-cursor editing
- Find and replace (with regex)
- Auto-indentation and bracket matching
- Encoding detection (UTF-8, UTF-16, ISO-8859-*)
- Large file support
- Minimap
- Vim mode (optional)
- Auto-save and session restore
- Markdown preview

%prep
%autosetup -n cosmic-text-editor-v%{cosmicte_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-text-editor %{buildroot}%{_bindir}/cosmic-text-editor

%files
%{_bindir}/cosmic-text-editor

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicte_version}-1
- Initial Synthex package — COSMIC text editor
