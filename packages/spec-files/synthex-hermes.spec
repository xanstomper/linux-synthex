%global _name synthex-hermes
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Synthex Hermes — Desktop AI Agent Platform

License:        MIT
URL:            https://synthex.org
BuildRequires:  coreutils

Requires:       python3
Requires:       qt6-qtdeclarative
Recommends:     python3-pyqt6
Recommends:     ollama

Source0:        synthex-repo-%{_version}.tar.gz
Source1:        synthex-hermes.desktop
Source2:        synthex-hermes-tray.desktop
Source3:        hermes-data
Source4:        synthex-hermes.svg
%description
Synthex Hermes — a native desktop AI agent for SynthOS.
Features:
• System tray integration for always-available AI assistance
• Multi-model support: OpenAI, Anthropic, Ollama, OpenCode, and more
• Chat interface with markdown rendering
• System control with configurable permissions
• File system access and code assistance
• Agent system with specialist agents (coding, system, research)
• Voice input support (optional)
• Fully offline capable with local models (Ollama)

Install additional models:
  ollama pull llama3.2:3b
  ollama pull deepseek-r1:1.5b

%prep
%setup -c -T

%build
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-hermes target/release/synthex-hermes
%install
mkdir -p %{buildroot}%{_bindir}
install -m 0755 target/release/synthex-hermes %{buildroot}%{_bindir}/synthex-hermes

# Desktop files
mkdir -p %{buildroot}%{_datadir}/applications
install -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/synthex-hermes.desktop

# Autostart tray
mkdir -p %{buildroot}%{_sysconfdir}/xdg/autostart
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/xdg/autostart/synthex-hermes-tray.desktop

# Application data
mkdir -p %{buildroot}%{_datadir}/synthex/hermes
cp -r %{SOURCE3}/* %{buildroot}%{_datadir}/synthex/hermes/

# Icon
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 0644 %{SOURCE4} %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/synthex-hermes.svg

%files
%{_bindir}/synthex-hermes
%{_datadir}/applications/synthex-hermes.desktop
%{_sysconfdir}/xdg/autostart/synthex-hermes-tray.desktop
%{_datadir}/synthex/hermes/
%{_datadir}/icons/hicolor/scalable/apps/synthex-hermes.svg

%changelog
* Tue Jul 2026 Synthex Project
- Initial Hermes AI agent package
