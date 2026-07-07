# synthex-creator-platform.spec — content creation, color management, tablet
# support, and audio production. Covers the Nobara "creator/streaming" layer.

%global creator_version 1.0.0

Name:           synthex-creator-platform
Version:        %{creator_version}
Release:        1%{?dist}
Summary:        Content creation, color management, and tablet support for Synthex

Group:          Applications/Multimedia
License:        MIT
URL:            https://synthex-linux.org/creator
BuildArch:      noarch

# Streaming / recording (Nobara patches OBS; we ship vanilla + plugins)
Requires:       obs-studio
Requires:       obs-studio-plugin-browser-source
Requires:       obs-studio-plugin-vkcapture
Requires:       gpu-screen-recorder
Requires:       wl-screenrec
Requires:       replay-sorcery

# Video editing
Requires:       kdenlive
Requires:       shotcut
Requires:       blender
Requires:       handbrake

# Graphics
Requires:       gimp
Requires:       gimp-plugins
Requires:       inkscape
Requires:       krita
Requires:       darktable
Requires:       rawtherapee

# Audio production
Requires:       audacity
Requires:       easyeffects
Requires:       pavucontrol
Requires:       helvum
Requires:       carla
Requires:       lsp-plugins
Requires:       zam-plugins
Requires:       calf-plugins

# Color management (creator-critical, missing from most distros)
Requires:       colord
Requires:       colord-gtk
Requires:       displaycal
Requires:       argyllcms

# Tablet / pen support (Wacom + generic)
Requires:       libwacom
Requires:       wacomtablet
Requires:       kcm_wacomtablet

%description
Synthex Creator Platform — streaming, content creation, color management,
and tablet/pen support. Brings the Nobara creator/streaming layer plus
proper color management (colord + DisplayCAL) and Wacom tablet support
that most gaming distros miss.

- OBS Studio with browser source + Vulkan capture plugins
- GPU screen recorder + Wayland screen recorder + replay buffer
- Kdenlive, Blender, GIMP, Inkscape, Krita, Darktable, RawTherapee
- Full audio production stack (EasyEffects, Carla, LSP/ZAM/Calf plugins)
- Color management (colord + DisplayCAL + ArgyllCMS)
- Wacom tablet support (libwacom + KDE Wacom KCM)

%prep
%setup -c -T

%build

%install

%files

%changelog
* Sat Jul 05 2026 Synthex Team <creator@synthex-linux.org> - 1.0.0-1
- OBS + browser source + Vulkan capture plugins
- GPU/Wayland screen recording + replay buffer
- Full video/graphics/audio creation suite
- Color management (colord, DisplayCAL, ArgyllCMS)
- Wacom tablet support
