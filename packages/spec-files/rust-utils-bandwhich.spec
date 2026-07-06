# Solus Linux RPM Spec — bandwhich
# Terminal bandwidth utilization monitor written in Rust
# Origin: Fedora, Arch Linux
%global bandwhich_version 0.40.0

Name: bandwhich
Version: %{bandwhich_version}
Release: 1%{?dist}
Summary: Terminal bandwidth utilization tool — see who's using your network
License: MIT
URL: https://github.com/imsnif/bandwhich
Source0: https://crates.io/api/v1/crates/bandwhich/%{bandwhich_version}/download#bandwhich-%{bandwhich_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
Requires: libpcap

%description
A terminal bandwidth utilization tool written in Rust that displays
current network utilization by process, connection, and remote IP/hostname.

bandwhich sniffs network traffic and correlates it with running processes,
showing you exactly which applications and connections are using your
bandwidth in real-time.

Features:
- Real-time network usage per process
- Connection-level breakdown (local/remote addresses)
- Remote hostname resolution (reverse DNS)
- DNS query monitoring
- Interactive TUI with filtering
- Mouse support
- Low overhead (written in Rust)

%prep
%setup -q -n bandwhich-%{bandwhich_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/bandwhich %{buildroot}%{_bindir}/bandwhich

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/bandwhich --help 2>/dev/null | head -1 || true

%files
%{_bindir}/bandwhich

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.40.0-1
- Initial Solus package
- Network bandwidth monitor in Rust
