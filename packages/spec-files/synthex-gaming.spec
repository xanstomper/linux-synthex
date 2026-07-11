Name:           synthex-gaming
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS gaming stack — Nobara-level out of the box
BuildArch:      noarch

License:        MIT
URL:            https://getsynthex.io

# Core gaming runtimes
Requires:       steam
Requires:       lutris
Requires:       heroic-games-launcher
# Performance / overlay
Requires:       gamescope
Requires:       mangohud
Requires:       gamemode
# Compatibility / Wine
Requires:       protontricks
Requires:       protonup-qt
Requires:       wine
Requires:       wine-mono
Requires:       winetricks
# Vulkan / DXVK support
Requires:       vulkan-tools
Requires:       vulkan-loader
Requires:       mesa-vulkan-drivers
# Controller support
Requires:       steam-devices
Requires:       xboxdrv
# Audio for gaming
Requires:       pipewire
Requires:       pipewire-pulseaudio
# Kernel tuning helpers
Requires:       tuned
Requires:       cpupower
Suggests:       obs-studio
Suggests:       discord
Suggests:       vkbasalt
Suggests:       goverlay

%description
SynthOS gaming meta-package.  Installs a complete, Nobara-inspired gaming
stack including:

  - Steam + Lutris + Heroic Games Launcher
  - Gamescope compositor, MangoHud overlay, Gamemode scheduler
  - Proton management (ProtonUp-Qt, Protontricks)
  - Wine + Winetricks + Wine-Mono
  - Full Vulkan / DXVK toolchain
  - Controller udev rules (Steam Devices + xboxdrv)
  - Kernel sysctl tuning for low-latency gaming

Kernel sysctl tweaks are dropped into /etc/sysctl.d/ at install time and
activated immediately via sysctl --system.

%prep
# meta-package — nothing to unpack

%build
# meta-package — nothing to build

%install
install -d %{buildroot}/etc/sysctl.d
install -d %{buildroot}/etc/synthex
install -d %{buildroot}/usr/lib/systemd/user/default.target.wants

cat > %{buildroot}/etc/sysctl.d/99-synthex-gaming.conf << 'EOF'
# SynthOS Gaming Kernel Tweaks
# Low-latency CFS scheduling
kernel.sched_latency_ns = 3000000
kernel.sched_min_granularity_ns = 300000
kernel.sched_wakeup_granularity_ns = 500000
# Large memory maps for game engines (Steam, DXVK, etc.)
vm.max_map_count = 2147483642
# Reduced swap pressure for gaming sessions
vm.swappiness = 10
# Faster dirty page writeback
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
# Compaction latency
kernel.compaction_proactiveness = 0
EOF

cat > %{buildroot}/etc/synthex/gaming.conf << 'EOF'
# SynthOS Gaming Configuration
SYNTHEX_GAMING_ENABLED=1
SYNTHEX_GAMEMODE_AUTO=1
SYNTHEX_MANGOHUD_DEFAULT=0
SYNTHEX_GAMESCOPE_DEFAULT=0
EOF

%files
%dir /etc/synthex
%config(noreplace) /etc/sysctl.d/99-synthex-gaming.conf
%config(noreplace) /etc/synthex/gaming.conf

%post
# Apply sysctl tweaks immediately (ignore errors on live system)
/usr/sbin/sysctl --system 2>/dev/null || :
# Enable gamemode for all users
systemctl --global enable gamemoded 2>/dev/null || :

%preun
if [ $1 -eq 0 ]; then
    systemctl --global disable gamemoded 2>/dev/null || :
fi

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Fix Release tag macro escaping (%%{?dist} → %{?dist})
- Add BuildArch: noarch
- Add complete Requires, %prep/%build/%install/%files sections
- Ship /etc/sysctl.d/99-synthex-gaming.conf as a proper config file
- Add %preun to disable gamemoded on removal
