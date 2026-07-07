# SynthOS Gaming Platform
# RPM Spec: synthex-gaming-control-center
#
# GUI application for managing gaming settings, profiles, and hardware.

%global gaming_version 1.0.0
%global gaming_release 1

%define _misspelld_blocklist_blocklist 1

Name:       synthex-gaming-control-center
Version:    %{gaming_version}
Release:    %{gaming_release}
Summary:    Synthex Gaming Control Center — GUI for gaming optimization

Group:      Applications/System
License:    MIT
URL:        https://getsynthex.com/gaming
Source0:    %{name}-%{version}.tar.xz

# Build dependencies
BuildRequires:  rust >= 1.75
BuildRequires:  cargo
BuildRequires:  meson >= 1.3
BuildRequires:  ninja-build
BuildRequires:  gtk4-devel >= 4.12
BuildRequires:  libadwaita-devel >= 1.4
BuildRequires:  glib2-devel
BuildRequires:  libappindicator-gtk3-devel
BuildRequires:  blueprint-compiler
BuildRequires:  gettext
BuildRequires:  systemd

# Runtime dependencies
Requires:   gtk4 >= 4.12
Requires:   libadwaita >= 1.4
Requires:   libnotify
Requires:   polkit
Requires:   polkit-gtk
Requires:   systemd
Requires:   dbus
Requires:   gamemode
Requires:   mangohud
Requires:   gamescope
Requires:   synthex-gpu-drivers >= %{version}
Requires:   synthex-steam-optimizer >= %{version}
Requires:   hwdata
Requires:   pciutils
Requires:   lm_sensors

Recommends: goverlay
Recommends: vkbasalt
Recommends: joycond
Recommends: steam-devices

%description
Synthex Gaming Control Center is a native GUI application for managing
every aspect of gaming on SynthOS.

Features:
- Dashboard with real-time system monitoring (CPU/GPU temps, clocks, FPS)
- Performance profile switcher (Power Saver, Balanced, Performance, Turbo)
- Game library integration (Steam, Lutris, Heroic)
- Per-game optimization profiles with fine-grained settings
- GPU driver detection, installation, and switching (NVIDIA ↔ Nouveau)
- MangoHUD visual configurator
- Shader cache management
- HDR and VRR toggles
- Controller test pad
- Benchmark runner with frame-time capture
- System tray quick profile switching

%prep
%setup -q -n %{name}-%{version}

%build
# Build Rust backend
cd daemon
cargo build --release %{?_smp_mflags}
cd ..

# Build GTK4 frontend
cd control-center
meson setup build --buildtype=release
meson compile -C build
cd ..

%install
# Install Rust daemon
install -d %{buildroot}%{_libexecdir}
install -m 755 daemon/target/release/synthex-gaming-daemon \
    %{buildroot}%{_libexecdir}/synthex-gaming-daemon

# Install GTK4 frontend
cd control-center
DESTDIR=%{buildroot} meson install -C build
cd ..

# Install systemd user service
install -d %{buildroot}%{_unitdir}/user
install -m 644 data/synthex-gaming-daemon.service \
    %{buildroot}%{_unitdir}/user/synthex-gaming-daemon.service

# Install D-Bus service file
install -d %{buildroot}%{_datadir}/dbus-1/services
install -m 644 data/com.synthex.GamingDaemon.service \
    %{buildroot}%{_datadir}/dbus-1/services/com.synthex.GamingDaemon.service

# Install polkit policy
install -d %{buildroot}%{_datadir}/polkit-1/actions
install -m 644 data/com.synthex.gaming.policy \
    %{buildroot}%{_datadir}/polkit-1/actions/com.synthex.gaming.policy

# Install icons
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 644 data/icons/synthex-gaming-center.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

# Install appstream metadata
install -d %{buildroot}%{_datadir}/metainfo
install -m 644 data/com.synthex.GamingCenter.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/

%post
# Enable and start daemon for current user
if [ $1 -eq 1 ]; then
    systemctl --global enable synthex-gaming-daemon.service 2>/dev/null || :
fi

%postun
if [ $1 -eq 0 ]; then
    systemctl --global disable synthex-gaming-daemon.service 2>/dev/null || :
fi

%files
%license LICENSE
%doc README.md

%dir %{_sysconfdir}/synthex-gaming-center
%config(noreplace) %{_sysconfdir}/synthex-gaming-center/*

%{_bindir}/synthex-gaming-center
%{_libexecdir}/synthex-gaming-daemon
%{_libexecdir}/synthex-gaming-polkit-helper

%{_unitdir}/user/synthex-gaming-daemon.service

%{_datadir}/dbus-1/services/com.synthex.GamingDaemon.service
%{_datadir}/polkit-1/actions/com.synthex.gaming.policy
%{_datadir}/icons/hicolor/scalable/apps/synthex-gaming-center.svg
%{_datadir}/applications/synthex-gaming-center.desktop
%{_datadir}/metainfo/com.synthex.GamingCenter.metainfo.xml

%changelog
* Thu Jul 04 2026 Synthex Gaming Team <gaming@getsynthex.com> - 1.0.0-1
- Initial Gaming Control Center
- Dashboard with system monitoring
- Game library and per-game profiles
- GPU driver management
- Performance profile switching
- MangoHUD configurator
