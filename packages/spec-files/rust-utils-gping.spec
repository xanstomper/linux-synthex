# SynthOS RPM Spec — gping
# Ping with graph — graphical ping tool written in Rust
# Origin: Fedora, Arch Linux
%global gping_version 1.18.0

Name: gping
Version: %{gping_version}
Release: 1%{?dist}
Summary: Ping with a graph — real-time latency visualization
License: MIT
URL: https://github.com/orf/gping
Source0: https://crates.io/api/v1/crates/gping/%{gping_version}/download#gping-%{gping_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
Ping with a graph — written in Rust. gping displays latency to hosts
as a real-time graph, making it easy to visualize network performance
over time. Supports multiple hosts simultaneously.

Features:
- Real-time latency graph
- Multiple host support (compare latency)
- Color-coded host lines
- Custom time window
- JSON output for scripting
- IPv4 and IPv6
- DNS resolution

%prep
%setup -q -n gping-%{gping_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/gping %{buildroot}%{_bindir}/gping

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/gping --help 2>/dev/null | head -1 || true

%files
%{_bindir}/gping

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - 1.18.0-1
- Initial Synthex package
- Graphical ping tool in Rust
