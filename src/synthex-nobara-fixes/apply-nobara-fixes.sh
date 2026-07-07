#!/usr/bin/env bash
# apply-nobara-fixes.sh — Apply Nobara-style system fixes
# Runs post-install to fix common gaming/multimedia pain points
set -euo pipefail

echo "🔧 Applying Nobara-style fixes..."

# ─── SELinux adjustments for gaming ───────────────────────────────────
if command -v setsebool &>/dev/null; then
    echo "  Adjusting SELinux booleans for gaming..."
    setsebool -P allow_execstack on 2>/dev/null || true
    setsebool -P allow_execmod on 2>/dev/null || true
    setsebool -P wine_mmap_zero_ignore on 2>/dev/null || true
    setsebool -P use_nfs_home_dirs on 2>/dev/null || true
fi

# ─── PipeWire audio fixes ─────────────────────────────────────────────
echo "  Configuring PipeWire for low-latency audio..."
mkdir -p /etc/pipewire
cat > /etc/pipewire/pipewire.conf.d/99-synthex-lowlatency.conf << 'EOF'
context.properties = {
    default.clock.quantum = 32
    default.clock.min-quantum = 16
    default.clock.max-quantum = 1024
    default.clock.rate = 48000
}
EOF

# ─── Steam permission fixes ───────────────────────────────────────────
echo "  Fixing Steam permissions..."
if [ -d /home ]; then
    for home in /home/*; do
        [ -d "$home/.steam" ] && chmod 755 "$home/.steam" 2>/dev/null || true
        [ -d "$home/.local/share/Steam" ] && chmod 755 "$home/.local/share/Steam" 2>/dev/null || true
    done
fi

# ─── Gaming compatibility tweaks ──────────────────────────────────────
echo "  Applying gaming compatibility tweaks..."
# Enable transparent hugepages for games
echo always > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
# Set vm.max_map_count for games (Star Citizen, etc.)
echo "vm.max_map_count = 16777216" > /etc/sysctl.d/99-synthex-gaming.conf
# Set fs.file-max
echo "fs.file-max = 2097152" >> /etc/sysctl.d/99-synthex-gaming.conf

# ─── OBS encoding defaults ────────────────────────────────────────────
echo "  Setting OBS encoding defaults..."
mkdir -p /etc/skel/.config/obs-studio
cat > /etc/skel/.config/obs-studio/basic/profiles/Defaults/basic.ini << 'OBSEOF'
[General]
Name=Default

[SimpleOutput]
FilePath=/home
RecFormat2=mp4
VBitrate=6000
ABitrate=160
UseAdvanced=false
UseReplayBuffer=true
RecEncoder=x264

[AdvOut]
ApplyServiceSettings=true
RescaleRes=1920x1080
TrackIndex=1
Encoder=x264
OBSEOF

# ─── udev rules for gaming controllers ────────────────────────────────
echo "  Installing gaming controller udev rules..."
mkdir -p /etc/udev/rules.d
cat > /etc/udev/rules.d/70-synthex-gaming.rules << 'UDEVEOF'
# Steam controller
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0660", GROUP="input"
# Xbox One controller
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="045e", MODE="0660"
# DualSense (PS5)
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660"
# DualShock 4
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="09cc", MODE="0660"
# Switch Pro controller
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2009", MODE="0660"
UDEVEOF

# ─── Wine prefix defaults ─────────────────────────────────────────────
echo "  Configuring Wine prefix defaults..."
mkdir -p /etc/skel/.wine
cat > /etc/skel/.wine/system.reg << 'WINEEOF'
[WINE\\\\Environment]
"WINEPREFIX"="~/.wine"

[Software\\Wine\\DllOverrides]
"winemenubuilder.exe"=""
WINEEOF

echo "✅ Nobara-style fixes applied"
