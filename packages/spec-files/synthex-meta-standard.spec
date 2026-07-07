%define _name synthex-meta-standard
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS standard desktop install meta-package

License:        MIT
URL:            https://synthex.org

BuildArch:      noarch
BuildRequires:  coreutils

# Include minimal base
Requires:       synthex-meta-minimal >= %{_version}

# Display server
Requires:       xorg-x11-server-Xorg
Requires:       xorg-x11-drv-evdev
Requires:       xorg-x11-drv-libinput
Requires:       xorg-x11-drv-fbdev
Requires:       xorg-x11-drv-vesa
Requires:       mesa-dri-drivers
Requires:       mesa-vulkan-drivers
Requires:       mesa-libGL
Requires:       libglvnd

# Desktop environment — Budgie (default)
Requires:       budgie-desktop
Requires:       budgie-desktop-view
Requires:       budgie-screensaver
Requires:       budgie-control-center
Requires:       gnome-session
Requires:       gnome-settings-daemon
Requires:       gnome-terminal
Requires:       nautilus
Requires:       gedit
Requires:       evince
Requires:       eog

# Display manager
Requires:       lightdm
Requires:       lightdm-gtk
Requires:       slick-greeter

# Audio
Requires:       pipewire
Requires:       pipewire-pulseaudio
Requires:       wireplumber
Requires:       alsa-sof-firmware
Requires:       pavucontrol

# Fonts
Requires:       dejavu-sans-fonts
Requires:       dejavu-serif-fonts
Requires:       dejavu-sans-mono-fonts
Requires:       google-noto-sans-fonts
Requires:       google-noto-emoji-fonts
Requires:       liberation-fonts
Requires:       fontconfig

# Printing
Requires:       cups
Requires:       cups-filters
Requires:       system-config-printer

# Bluetooth
Requires:       bluez
Requires:       bluez-obexd

# Power management
Requires:       upower
Requires:       power-profiles-daemon

# Polkit
Requires:       polkit
Requires:       polkit-gnome

# Network management (GUI)
Requires:       network-manager-applet

# File systems
Requires:       fuse
Requires:       fuse-libs
Requires:       exfat-utils
Requires:       ntfs-3g
Requires:       udisks2

# Codecs
Requires:       gstreamer1
Requires:       gstreamer1-plugins-base
Requires:       gstreamer1-plugins-good
Requires:       gstreamer1-plugins-bad-free
Requires:       gstreamer1-plugin-libav

# Browser
Requires:       firefox

# Utilities
Requires:       file-roller
Requires:       gnome-disk-utility
Requires:       gnome-calculator
Requires:       gnome-characters
Requires:       gnome-logs
Requires:       gnome-system-monitor
Requires:       baobab
Requires:       totem
Requires:       rhythmbox

# Input methods
Requires:       ibus
Requires:       ibus-libpinyin

# Themes
Requires:       arc-theme
Requires:       papirus-icon-theme
Requires:       adwaita-gtk3-theme

# Development libraries (runtime)
Requires:       gtk3
Requires:       gtk4
Requires:       qt6-qtbase-gui
Requires:       python3
Requires:       python3-pip

# Security
Requires:       firewalld
Requires:       fail2ban
Requires:       selinux-policy-targeted

# Flatpak ecosystem + Flathub preconfigured (users never add repos manually)
Requires:       synthex-essentials >= %{_version}

# Creator / color / tablet layer
Requires:       synthex-creator-platform >= 1.0.0

# ─── Bazzite/CachyOS/Nobara/Mint feature parity ──────────────────────
# Complete codec pack (Nobara strength — users never hunt for codecs)
Requires:       synthex-codec-pack >= 1.0.0
# Welcome app (all 4 distros have one)
Requires:       synthex-welcome >= 1.0.0
# Mint tools: USB writer, file sharing, XApps, Timeshift, update manager
Requires:       synthex-mint-extras >= 1.0.0
# Bazzite: ujust, handheld configs, Steam Gaming Mode, controller-first
Requires:       synthex-bazzite-extras >= 1.0.0
# CachyOS: tuned, ananicy, ZRAM, sysctl, fish, performance presets
Requires:       synthex-cachy-tuning >= 1.0.0
# Nobara: NVIDIA wizard, patched OBS, audio fixes, gaming compatibility
Requires:       synthex-nobara-fixes >= 1.0.0
# Desktop utility tools: screenshots, input methods, file sharing, remote desktop,
# Bluetooth GUI, night light, Syncthing, clipboard, archives, password managers,
# backup, downloads, viewers, accessibility, webcam, disk tools, firewall GUI
Requires:       synthex-desktop-tools >= 1.0.0
# System utilities: network diagnostics, global fonts, data recovery, hardware
# monitoring, spell check, privacy/Tor, VPN protocols, modem, filesystem tools
Requires:       synthex-system-utilities >= 1.0.0
# System configuration files: dracut, GRUB, SDDM, firewalld, Flatpak, Snapper,
# sudo, polkit, journald, modprobe, locale, Secure Boot, Btrfs, live image
Requires:       synthex-system-config >= 1.0.0
# Visual themes: GTK3/GTK4 dark theme + SDDM QML login screen
Requires:       synthex-themes >= 1.0.0
# Gaming optimizations: realtime priorities, gaming sysctl, Proton/DXVK env
Requires:       synthex-gaming-optimizations >= 1.0.0
# Custom kernel config + patches (BORE scheduler, gaming latency, tickless)
Requires:       synthex-kernel >= 6.12.0

%description
SynthOS standard desktop install meta-package. Provides a complete
desktop operating system with the Budgie desktop environment, essential
applications, multimedia codecs, printing support, Bluetooth, and all
core desktop functionality.

Approximate install size: 2.5 GB

Includes:
  - Budgie Desktop Environment
  - Firefox web browser
  - GNOME application suite
  - Printing and scanning support
  - Bluetooth and audio
  - Multimedia codecs
  - Development libraries

%prep
%setup -c -T

%build
# Nothing to build — this is a dependency meta-package

%install
# Create metadata file
install -d -m 0755 %{buildroot}%{_datadir}/synthex-meta
cat > %{buildroot}%{_datadir}/synthex-meta/standard << 'EOF'
SynthOS Standard Desktop Install
Version: %{_version}
Type: standard
Description: Complete desktop operating system with Budgie
Install size: ~2.5 GB
Desktop: Budgie
Browser: Firefox
Office: GNOME Documents, Evince
Multimedia: Rhythmbox, Totem, Codecs
EOF

%files
%defattr(-,root,root,-)
%{_datadir}/synthex-meta/standard

%changelog
* Sat Jul 04 2026 Synthex Release Team <release@synthex.org> - 1:2026.1-1
- Initial standard desktop meta-package
- Budgie desktop environment
- X11 display server with Mesa graphics
- Firefox browser, GNOME applications
- Printing (CUPS), Bluetooth (BlueZ), Audio (PipeWire)
- Multimedia codecs and GStreamer plugins
