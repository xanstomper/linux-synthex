# Solus Linux RPM Spec — dua-cli
# Disk usage analyzer (du replacement) written in Rust
# Origin: Fedora, Arch Linux
%global dua_version 2.30.0

Name: dua-cli
Version: %{dua_version}
Release: 1%{?dist}
Summary: Disk usage analyzer with interactive TUI — modern du replacement
License: MIT
URL: https://github.com/Byron/dua-cli
Source0: https://crates.io/api/v1/crates/dua-cli/%{dua_version}/download#dua-cli-%{dua_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
dua (Disk Usage Analyzer) is a tool to conveniently learn about the
disk usage of directories, written in Rust. It provides an interactive
terminal UI for browsing disk usage with sort, filter, delete, and
export capabilities.

Features:
- Interactive TUI with arrow-key navigation
- Sort by size, name, or count
- Delete files directly from the interface
- Export to CSV, JSON, or terminal table
- Multi-threaded scanning for speed
- Color-coded size display
- Real-time scanning progress

%prep
%setup -q -n dua-cli-%{dua_version}

%build
cargo build --release %{?_smp_mflags}
# Build a smaller binary without TUI for scripting
cargo build --release --no-default-features -p dua-cli --bin dua 2>/dev/null || true

%install
install -D -m 0755 target/release/dua %{buildroot}%{_bindir}/dua

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
install -m 0644 docs/dua.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/dua --help 2>/dev/null | head -1 || true

%files
%{_bindir}/dua
%{_mandir}/man1/dua.1*

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 2.30.0-1
- Initial Solus package
- Disk usage analyzer in Rust
