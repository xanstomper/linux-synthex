Name:           synthex-aether
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS AETHER — OS-level AI consciousness daemon
License:        MIT OR Apache-2.0
Source0:        synthex-repo-%{version}.tar.gz
URL:            https://getsynthex.io
BuildRequires:  rust, cargo, systemd-rpm-macros
Requires:       systemd

%description
AETHER CORE — the permanent AI-cognition substrate for SynthOS.

aetherd is a long-running OS daemon that provides a unified memory graph
(episodic / semantic / procedural / working / reflection), a knowledge graph
of projects/files/tasks/agents, a zero-trust capability broker, a
provider-agnostic agent runtime, and a set of cognitive engines (attention,
curiosity, memory consolidation). It is the "brain" that agent daemons are
scoped, spawned, and torn down against — memory and identity persist in the
daemon, not in the agents.

Exposes a newline-JSON-over-TCP API on 127.0.0.1:8787 and an in-process
DaemonApi trait. Ships hardened (ProtectSystem=strict, dedicated unprivileged
user, capability-dropped).

%build
# AETHER CORE is an independent Cargo workspace (aether/core). Build it in-tree
# from the source checkout (the Makefile sets _sourcedir to the repo root).
cd aether/core
cargo build --release

%install
install -d %{buildroot}/usr/lib/synthex
install -Dm755 target/release/aetherd \
    %{buildroot}/usr/lib/synthex/aetherd

install -Dm644 systemd/synthex-aether.service \
    %{buildroot}%{_unitdir}/synthex-aether.service

install -Dm644 systemd/synthex-aether.sysusers \
    %{buildroot}%{_sysusersdir}/synthex-aether.conf

%files
%attr(0755,root,root) /usr/lib/synthex/aetherd
%{_unitdir}/synthex-aether.service
%{_sysusersdir}/synthex-aether.conf

%post
%systemd_post synthex-aether.service

%preun
%systemd_preun synthex-aether.service

%postun
%systemd_postun_with_restart synthex-aether.service

%changelog
* Thu Jul 11 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-aether package: AETHER CORE consciousness daemon (aetherd)
- Memory graph (SQLite), capability broker, agent runtime, cognitive engines
- Hardened systemd unit (ProtectSystem=strict, dedicated synthex-aether user)
- JSON-line TCP API on 127.0.0.1:8787
