# 
# spec file for package synthex-ai-hub
#
# Copyright (c) 2026 Synthex Project
#

%global __requires_exclude_from ^%{_datadir}/synthex-ai-hub/

%define python3_sitelib %(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))" 2>/dev/null || echo "/usr/lib/python3.12/site-packages")

Name:           synthex-ai-hub
Version:        1.0.0
Release:        1
Summary:        Synthex AI Hub — Central GUI for AI model management and chat

License:        GPL-3.0-or-later
URL:            https://github.com/synthex-project/synthex-ai-hub
Source0:        synthex-repo-%{version}.tar.gz

# Build dependencies
BuildRequires:  meson >= 1.0.0
BuildRequires:  python3-devel
BuildRequires:  pkgconfig(pygobject-3.0)
BuildRequires:  pkgconfig(gtk4) >= 4.12
BuildRequires:  pkgconfig(libadwaita-1) >= 1.5
BuildRequires:  glib2-devel
BuildRequires:  desktop-file-utils
BuildRequires:  appstream-glib

# Runtime dependencies
Requires:       python3 >= 3.12
Requires:       python3-gobject >= 3.48
Requires:       gtk4 >= 4.12
Requires:       libadwaita >= 1.5
Requires:       python3-aiohttp >= 3.9
Requires:       python3-httpx >= 0.27
Requires:       python3-watchdog >= 4.0
Requires:       python3-dbus >= 1.3
Requires:       ollama
Requires:       jq
Requires:       numfmt (coreutils)

Recommends:     python3-pillow
Recommends:     python3-markdown

# Optional GPU acceleration
Suggests:       rocm-hip
Suggests:       rocm-smi
Suggests:       nvidia-driver
Suggests:       cuda-toolkit
Suggests:       intel-compute-runtime

%description
Synthex AI Hub is the central graphical application for managing the Synthex AI
stack. It provides a unified interface for model management, local LLM chat,
service orchestration (Ollama, Open WebUI), and system integration.

Features:
- Browse, install, and manage local LLM models
- Built-in chat interface with any loaded model
- GPU acceleration auto-detection (ROCm, CUDA, oneAPI)
- Service control for Ollama and Open WebUI
- Resource monitoring (CPU, RAM, VRAM, disk)
- AI-powered system integration (smart search, file assistant)
- Privacy-first: everything runs locally, no telemetry

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python application; nothing to compile
true

%install
install -d %{buildroot}%{_bindir} %{buildroot}%{_userunitdir} %{buildroot}%{_datadir}/synthex-ai-hub

# Launcher that runs the Python module
cat > %{buildroot}%{_bindir}/synthex-ai-hub <<'LAUNCH'
#!/usr/bin/env bash
exec python3 %{_datadir}/synthex-ai-hub/main.py "$@"
LAUNCH
chmod 0755 %{buildroot}%{_bindir}/synthex-ai-hub
install -m 0755 scripts/model-sources.sh %{buildroot}%{_bindir}/synthex-ai-model
install -m 0644 data/modellibrary.json %{buildroot}%{_datadir}/synthex-ai-hub/modellibrary.json
install -m 0644 data/synthex-ai-hub.service %{buildroot}%{_userunitdir}/synthex-ai-hub.service

# GSettings schema compilation (post-install)
%post
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :
%systemd_user_post synthex-ai-hub.service

%postun
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :
%systemd_user_postun_with_restart synthex-ai-hub.service

%files
%defattr(-,root,root)
%{_bindir}/synthex-ai-hub
%{_bindir}/synthex-ai-model
%{_datadir}/synthex-ai-hub/modellibrary.json
%{_userunitdir}/synthex-ai-hub.service

%changelog
* Sat Jul 04 2026 Synthex Project <packaging@synthex-project.org> - 1.0.0-1
- Initial Synthex AI Hub package
- Model management with Ollama integration
- GPU acceleration support (ROCm, CUDA, oneAPI)
- Built-in chat interface
- systemd service integration
