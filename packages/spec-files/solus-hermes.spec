%global _name solus-hermes
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Hermes — Desktop AI Agent Platform

License:        MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils

Requires:       python3
Requires:       qt6-qtdeclarative
Recommends:     python3-pyqt6
Recommends:     ollama

%description
Solus Hermes — a native desktop AI agent for Solus Linux.
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
echo "Solus Hermes AI Agent" > build.log

%install
mkdir -p %{buildroot}%{_bindir}
install -m 0755 %{SOURCE0} %{buildroot}%{_bindir}/solus-hermes

# Desktop files
mkdir -p %{buildroot}%{_datadir}/applications
install -m 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/solus-hermes.desktop

# Autostart tray
mkdir -p %{buildroot}%{_sysconfdir}/xdg/autostart
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/xdg/autostart/solus-hermes-tray.desktop

# Application data
mkdir -p %{buildroot}%{_datadir}/solus/hermes
cp -r %{SOURCE3}/* %{buildroot}%{_datadir}/solus/hermes/

# Icon
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 0644 %{SOURCE4} %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/solus-hermes.svg

%files
%{_bindir}/solus-hermes
%{_datadir}/applications/solus-hermes.desktop
%{_sysconfdir}/xdg/autostart/solus-hermes-tray.desktop
%{_datadir}/solus/hermes/
%{_datadir}/icons/hicolor/scalable/apps/solus-hermes.svg

%changelog
* Tue Jul 2026 Solus Project
- Initial Hermes AI agent package
