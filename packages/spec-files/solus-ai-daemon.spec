# Solus Linux RPM Spec — solus-ai-daemon
# Rust-based AI daemon for Ollama management, D-Bus AI API, and voice commands
# Origin: https://github.com/xanstomper/solus-linux

%global daemon_version 0.1.0

Name: solus-ai-daemon
Version: %{daemon_version}
Release: 1%{?dist}
Summary: Solus AI daemon — local LLM integration via Ollama, D-Bus API, voice commands
License: MIT OR Apache-2.0
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

Requires: ollama >= 0.5.0
Requires: systemd
Suggests: whisper-cpp

%description
Solus AI Daemon is a Rust-based local AI integration daemon for Solus Linux.
It manages Ollama as a managed subprocess and provides a D-Bus API for
system-wide AI access.

Features:
- Ollama subprocess management (start/stop/health check)
- D-Bus API (org.solus.AI): Chat, Query, Troubleshoot, Transcribe, VoiceCommand
- Whisper voice command integration (speech-to-text)
- Hardware-aware system advisory (integrates with solus-system-daemon)
- CLI interface: solus-ai chat, status, start, stop, models, pull, advise
- Fallback rule-based advice when LLM is unavailable

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-ai-daemon %{buildroot}%{_libexecdir}/solus/solus-ai-daemon

# Systemd service
mkdir -p %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/solus-ai-daemon.service << 'EOS'
[Unit]
Description=Solus AI Daemon — Rust-powered Ollama manager + D-Bus AI API
Documentation=https://github.com/xanstomper/solus-linux
After=network.target network-online.target
Wants=network-online.target
ConditionFileNotEmpty=|/usr/bin/ollama

[Service]
Type=simple
ExecStart=%{_libexecdir}/solus/solus-ai-daemon daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
TimeoutStopSec=15
User=root
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=read-only

[Install]
WantedBy=multi-user.target
EOS

# Symlink for CLI access
mkdir -p %{buildroot}%{_bindir}
ln -sf %{_libexecdir}/solus/solus-ai-daemon %{buildroot}%{_bindir}/solus-ai

%post
%systemd_post solus-ai-daemon.service

%preun
%systemd_preun solus-ai-daemon.service

%postun
%systemd_postun_with_restart solus-ai-daemon.service

%files
%{_libexecdir}/solus/solus-ai-daemon
%{_bindir}/solus-ai
%{_unitdir}/solus-ai-daemon.service
%doc README.md

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus AI daemon
- Ollama subprocess management
- D-Bus API (Chat, Query, Troubleshoot, Transcribe, VoiceCommand)
- Whisper voice command integration
- Hardware-aware system advisory
- CLI interface (chat, status, start, stop, models, pull, advise)
