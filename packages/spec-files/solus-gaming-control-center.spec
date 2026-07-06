# Solus Linux Gaming Platform
# RPM Spec: solus-gaming-control-center
#
# GUI application for managing gaming settings, profiles, and hardware.

%global gaming_version 1.0.0
%global gaming_release 1

%define _misspelld_blocklist_blocklist 1

Name:       solus-gaming-control-center
Version:    %{gaming_version}
Release:    %{gaming_release}
Summary:    Solus Gaming Control Center — GUI for gaming optimization

Group:      Applications/System
License:    MIT
URL:        https://getsolus.com/gaming
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
Requires:   solus-gpu-drivers >= %{version}
Requires:   solus-steam-optimizer >= %{version}
Requires:   hwdata
Requires:   pciutils
Requires:   lm_sensors

Recommends: goverlay
Recommends: vkbasalt
Recommends: joycond
Recommends: steam-devices

%description
Solus Gaming Control Center is a native GUI application for managing
every aspect of gaming on Solus Linux.

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
install -m 755 daemon/target/release/solus-gaming-daemon \
    %{buildroot}%{_libexecdir}/solus-gaming-daemon

# Install GTK4 frontend
cd control-center
DESTDIR=%{buildroot} meson install -C build
cd ..

# Install systemd user service
install -d %{buildroot}%{_unitdir}/user
install -m 644 data/solus-gaming-daemon.service \
    %{buildroot}%{_unitdir}/user/solus-gaming-daemon.service

# Install D-Bus service file
install -d %{buildroot}%{_datadir}/dbus-1/services
install -m 644 data/com.solus.GamingDaemon.service \
    %{buildroot}%{_datadir}/dbus-1/services/com.solus.GamingDaemon.service

# Install polkit policy
install -d %{buildroot}%{_datadir}/polkit-1/actions
install -m 644 data/com.solus.gaming.policy \
    %{buildroot}%{_datadir}/polkit-1/actions/com.solus.gaming.policy

# Install icons
install -d %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
install -m 644 data/icons/solus-gaming-center.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

# Install appstream metadata
install -d %{buildroot}%{_datadir}/metainfo
install -m 644 data/com.solus.GamingCenter.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/

%post
# Enable and start daemon for current user
if [ $1 -eq 1 ]; then
    systemctl --global enable solus-gaming-daemon.service 2>/dev/null || :
fi

%postun
if [ $1 -eq 0 ]; then
    systemctl --global disable solus-gaming-daemon.service 2>/dev/null || :
fi

%files
%license LICENSE
%doc README.md

%dir %{_sysconfdir}/solus-gaming-center
%config(noreplace) %{_sysconfdir}/solus-gaming-center/*

%{_bindir}/solus-gaming-center
%{_libexecdir}/solus-gaming-daemon
%{_libexecdir}/solus-gaming-polkit-helper

%{_unitdir}/user/solus-gaming-daemon.service

%{_datadir}/dbus-1/services/com.solus.GamingDaemon.service
%{_datadir}/polkit-1/actions/com.solus.gaming.policy
%{_datadir}/icons/hicolor/scalable/apps/solus-gaming-center.svg
%{_datadir}/applications/solus-gaming-center.desktop
%{_datadir}/metainfo/com.solus.GamingCenter.metainfo.xml

%changelog
* Thu Jul 04 2026 Solus Gaming Team <gaming@getsolus.com> - 1.0.0-1
- Initial Gaming Control Center
- Dashboard with system monitoring
- Game library and per-game profiles
- GPU driver management
- Performance profile switching
- MangoHUD configurator
