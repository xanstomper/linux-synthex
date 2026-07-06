# Solus Linux Gaming Platform
# RPM Spec: solus-gaming-platform (meta-package)
#
# Meta-package that pulls in all gaming platform components.
# This package itself contains no files — it only declares dependencies.

%global gaming_version 1.0.0
%global gaming_release 1

Name:       solus-gaming-platform
Version:    %{gaming_version}
Release:    %{gaming_release}
Summary:    Solus Linux Gaming Platform — meta-package for all gaming components

Group:      Applications/System
License:    MIT
URL:        https://getsolus.com/gaming
Source0:    %{name}-%{version}.tar.xz

BuildArch:  noarch
Requires:   solus-gpu-drivers >= %{version}
Requires:   solus-gaming-control-center >= %{version}
Requires:   solus-gaming-tools >= %{version}
Requires:   solus-steam-optimizer >= %{version}

# Core gaming dependencies
Requires:   steam
Requires:   lutris
Requires:   heroic-games-launcher

# Graphics stack
Requires:   mesa-dri-drivers
Requires:   mesa-vulkan-drivers
Requires:   mesa-libGL
Requires:   mesa-libEGL
Requires:   mesa-va-drivers
Requires:   mesa-vdpau-drivers
Requires:   vulkan-loader
Requires:   vulkan-tools
Requires:   vulkan-validation-layers

# Wine / Proton
Requires:   wine-core
Requires:   wine-proton
Requires:   wine-wayland
Requires:   dxvk
Requires:   vkd3d-proton

# Gaming tools
Requires:   gamemode
Requires:   gamemode-devel
Requires:   gamescope
Requires:   mangohud
Requires:   goverlay
Requires:   vkbasalt
Requires:   preload

# Shader cache
Requires:   dxvk-state-cache-manager

# Controller support
Requires:   joycond
Requires:   ds4drv
Requires:   steam-devices
Requires:   xpadneo
Requires:   antimicrox
Requires:   sc-controller
Requires:   input-remapper

# Network optimization
Requires:   bbswitch

# Benchmarking
Requires:   gputest
Requires:   unigine-heaven
Requires:   unigine-valley
Requires:   unigine-superposition

# Minecraft + emulation launchers
Requires:   prism-launcher
Requires:   retroarch
Requires:   dolphin-emu
Requires:   rpcs3
Requires:   pcsx2
Requires:   ppsspp
Requires:   mame

# Game streaming (Bazzite-style)
Requires:   sunshine
Requires:   moonlight

# VR support
Requires:   monado
Requires:   alvr
Requires:   steamvr

# NVIDIA overclocking / monitoring (Nobara)
Requires:   greenwithenvy

# Decky Loader (Steam Deck plugin loader, Bazzite)
Requires:   decky-loader

# Handheld daemon (TDP/gyro/RGB for ROG Ally/Legion Go, Bazzite)
Requires:   handheld-daemon

# Low-latency audio (rtkit + proaudio PipeWire profile)
Requires:   rtkit
Requires:   realtime-setup

# Distrobox (Bazzite container dev)
Requires:   distrobox

%description
Solus Gaming Platform is a complete, integrated gaming environment for
Solus Linux. This meta-package installs everything needed for a
high-performance gaming experience:

- Automatic GPU driver detection and installation (AMD, NVIDIA, Intel)
- Optimized graphics stack (Mesa, Vulkan, DXVK, VKD3D-Proton)
- Proton GE with custom Wine patches
- Gamescope micro-compositor for sandboxed, low-latency gaming
- MangoHUD and GOverlay for performance monitoring
- Gamemode for automatic system tuning
- Steam with performance-enhancing scripts
- Lutris and Heroic Games Launcher
- Gaming Control Center GUI for all settings
- Full controller support (Xbox, PlayStation, Nintendo Switch)
- HDR and VRR support (Wayland)

Install this package, reboot, and start playing.

%prep
%setup -q

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Thu Jul 04 2026 Solus Gaming Team <gaming@getsolus.com> - 1.0.0-1
- Initial Solus Gaming Platform meta-package
- Include all core gaming components
