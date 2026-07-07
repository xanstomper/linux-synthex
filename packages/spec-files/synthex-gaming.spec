Name:           synthex-gaming
Version:        2026.10
Release:        1%%{?dist}
Summary:        Synthex gaming stack

License:        MIT
URL:            https://getsynthex.io

Requires:       steam, lutris, heroic-games-launcher
Requires:       gamescope, mangohud, gamemode
Requires:       protontricks, protonup-qt, wine
Suggests:       obs-studio, discord

%%description
Synthex gaming meta-package - Nobara-level gaming.

%%files
%%dir /etc/synthex

%%post
cat > /etc/sysctl.d/99-synthex-gaming.conf << 'EOF'
kernel.sched_latency_ns = 3000000
vm.max_map_count = 2147483642
EOF
systemctl --global enable gamemoded 2>/dev/null || :
echo "Synthex Gaming Stack installed"

%%changelog
* Mon Jul 06 2026 - Initial
