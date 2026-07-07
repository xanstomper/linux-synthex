# SynthOS RPM Spec — nushell (nu)
# Modern shell written in Rust
# Origin: Fedora, Arch Linux

%global nu_version 0.103.0

Name: nushell
Version: %{nu_version}
Release: 1%{?dist}
Summary: Modern shell for the GitHub era — structured data, pipelines, and plugins
License: MIT
URL: https://www.nushell.sh
Source0: https://github.com/nushell/nushell/archive/refs/tags/%{nu_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A modern shell written in Rust. Nushell provides a structured data pipeline
that handles not just strings but structured data (tables, lists, records),
making shell scripting more powerful and less error-prone.

Key features:
- Structured data pipelines (tables, lists, records)
- Plugin system in any language
- Cross-platform (Linux, macOS, Windows)
- Built-in file system operations
- Data manipulation commands (sort, filter, group, join)
- Type system with error checking
- Interactive REPL with history and completion
- Custom commands and aliases
- Environment management
- Configurable prompt and themes

%prep
%autosetup -n nushell-%{nu_version}

%build
cargo build --release %{?_smp_mflags} -p nu

%install
install -D -m 0755 target/release/nu %{buildroot}%{_bindir}/nu

# Plugin binaries
for plugin in nu-plugin-core nu-plugin-ext; do
    [ -f "target/release/$plugin" ] && \
        install -D -m 0755 "target/release/$plugin" "%{buildroot}%{_bindir}/$plugin"
done

%files
%{_bindir}/nu
%{_bindir}/nu-plugin-core
%{_bindir}/nu-plugin-ext

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{nu_version}-1
- Initial Synthex package — nushell
- Ported from Fedora and Arch Linux packaging
