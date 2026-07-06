# Solus Linux RPM Spec — dog
# Command-line DNS client (dig replacement) written in Rust
# Origin: Fedora, Arch Linux
%global dog_version 0.4.0

Name: dog
Version: %{dog_version}
Release: 1%{?dist}
Summary: Command-line DNS client — colorful, modern dig replacement
License: EUPL-1.2
URL: https://dns.lookup.dog
Source0: https://crates.io/api/v1/crates/dog/%{dog_version}/download#dog-%{dog_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
dog is a command-line DNS client written in Rust. It has colorful output,
supports DNS-over-TLS and DNS-over-HTTPS, and can be used as a drop-in
replacement for dig.

Features:
- Colorful output with syntax highlighting
- DNS-over-TLS and DNS-over-HTTPS
- Full support for all record types (A, AAAA, MX, TXT, etc.)
- Short and long output formats
- JSON output
- IDN support
- Minimal latency

%prep
%setup -q -n dog-%{dog_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/dog %{buildroot}%{_bindir}/dog

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
install -m 0644 man/dog.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/dog --help 2>/dev/null | head -1 || true

%files
%{_bindir}/dog
%{_mandir}/man1/dog.1*

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.4.0-1
- Initial Solus package
- DNS client in Rust (dig replacement)
