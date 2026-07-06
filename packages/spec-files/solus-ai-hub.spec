# 
# spec file for package solus-ai-hub
#
# Copyright (c) 2026 Solus Project
#

%global __requires_exclude_from ^%{python3_sitelib}/solus_ai_hub/

%define python3_sitelib %(python3 -c "import sysconfig; print(sysconfig.get_path('purelib'))" 2>/dev/null || echo "/usr/lib/python3.12/site-packages")

Name:           solus-ai-hub
Version:        1.0.0
Release:        1
Summary:        Solus AI Hub — Central GUI for AI model management and chat

License:        GPL-3.0-or-later
URL:            https://github.com/solus-project/solus-ai-hub
Source0:        %{name}-%{version}.tar.xz

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
Solus AI Hub is the central graphical application for managing the Solus AI
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
%setup -q

%build
%meson
%meson_build

%install
%meson_install

# Install model library
install -D -m 0644 data/modellibrary.json \
    %{buildroot}%{_datadir}/solus-ai-hub/modellibrary.json

# Install model manager script
install -D -m 0755 scripts/model-sources.sh \
    %{buildroot}%{_bindir}/solus-ai-model

# Install systemd user service
install -D -m 0644 data/solus-ai-hub.service \
    %{buildroot}%{_userunitdir}/solus-ai-hub.service

# GSettings schema compilation (post-install)
%post
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :
%systemd_user_post solus-ai-hub.service

%postun
/usr/bin/glib-compile-schemas %{_datadir}/glib-2.0/schemas &>/dev/null || :
%systemd_user_postun_with_restart solus-ai-hub.service

%files
%defattr(-,root,root)
%{_bindir}/solus-ai-hub
%{_bindir}/solus-ai-model
%{python3_sitelib}/solus_ai_hub/
%{_datadir}/solus-ai-hub/
%{_datadir}/applications/org.solus.AIHub.desktop
%{_datadir}/icons/hicolor/scalable/apps/solus-ai-hub.svg
%{_datadir}/metainfo/org.solus.AIHub.metainfo.xml
%{_datadir}/glib-2.0/schemas/org.solus.AIHub.gschema.xml
%{_datadir}/dbus-1/services/org.solus.AIHub.service
%{_userunitdir}/solus-ai-hub.service
%{_mandir}/man1/solus-ai-hub.1*

%changelog
* Sat Jul 04 2026 Solus Project <packaging@solus-project.org> - 1.0.0-1
- Initial Solus AI Hub package
- Model management with Ollama integration
- GPU acceleration support (ROCm, CUDA, oneAPI)
- Built-in chat interface
- systemd service integration
