# SynthOS Linux — Gaming Edition Kickstart
# SPDX-License-Identifier: GPL-3.0-or-later
# https://getsynthex.org

url --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-42&arch=x86_64"
repo --name="updates" --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f42&arch=x86_64"
repo --name="synthex" --baseurl="https://packages.getsynthex.org/stable/x86_64/" --gpgcheck=0
repo --name="synthex-updates" --baseurl="https://packages.getsynthex.org/updates/x86_64/" --gpgcheck=0
repo --name="rpmfusion-free" --mirrorlist="https://mirrors.rpmfusion.org/mirrorlist?repo=free-fedora-42&arch=x86_64" --gpgcheck=0
repo --name="rpmfusion-nonfree" --mirrorlist="https://mirrors.rpmfusion.org/mirrorlist?repo=nonfree-fedora-42&arch=x86_64" --gpgcheck=0

lang en_US.UTF-8
keyboard us
timezone America/New_York --utc
authselect --useshadow --passalgo=sha512
selinux --permissive
firewall --enabled --service=mdns,ssh
services --enabled=NetworkManager,sshd,chronyd,auditd,fstrim.timer,sddm,synthex-firstboot,synthex-system-daemon,synthex-gaming-mode
services --disabled=lvm2-monitor,mdmonitor
bootloader --location=mbr --append="rhgb quiet splash mitigations=auto rd.driver.blacklist=nouveau modprobe.blacklist=nouveau processor.max_cstate=5 idle=nomwait"
network --bootproto=dhcp --device=link --activate
rootpw --lock
firstboot --reconfig
xconfig --startxonboot

xconfig --startxonboot

# ── LIVE IMAGE ───────────────────────────────────────────────────────────────
# Livecd-creator builds a squashfs live root (overlayfs) mounted read-write on
# boot: the ISO is FULLY USABLE as a desktop before any installation. Contents
# are ephemeral; "Install Synthex" on the desktop (Calamares) writes to disk.
liveimg --name="Synthex-Gaming" --nombr

# Live session non-root user (also created by live-setup.sh at first boot).
# Auto-login + passwordless sudo wired in %post below.
user --name=liveuser --groups=wheel,audio,video,input,storage --password=liveuser

%packages
@core
@hardware-support
@fonts
@multimedia
@networkmanager-submodules

# KDE Plasma desktop (base for gaming)
@kde-desktop
plasma-desktop
plasma-workspace
plasma-nm
plasma-pa
plasma-systemmonitor
dolphin
konsole
spectacle
sddm
sddm-kcm
breeze-icon-theme
breeze-gtk

# Gaming core stack
gamemode
gamescope
mangohud
vkbasalt

# Wine / Proton
wine
wine-gecko
wine-mono
winetricks
protontricks

# Steam & launchers (Flatpak refs added in %post)
steam
lutris

# Controller / input
joystick
jstest-gtk
oversteer
antimicrox

# GPU drivers
mesa-dri-drivers
mesa-vulkan-drivers
mesa-vdpau
libvdpau-va-gl
vulkan-loader
vulkan-tools
vulkan-validation-layers
libva
libva-utils
vdpauinfo
glxinfo

# Media
ffmpeg
gstreamer1-plugins-good
gstreamer1-plugins-bad-free
gstreamer1-vaapi
gstreamer1-plugin-openh264
pipewire
pipewire-pulseaudio
wireplumber
pavucontrol

# Game streaming / recording
obs-studio
gstreamer1-plugins-ugly
ffmpeg

# Development / modding
cmake
make
gcc
gcc-c++
python3
python3-libs

# Fonts
google-noto-sans-fonts
google-noto-emoji-fonts
fontawesome-fonts

# System essentials
grub2-efi-x64
grub2-pc
grub2-common
shim-unsigned-x64
efibootmgr
glibc-langpack-en
bash
bash-completion
btrfs-progs
util-linux
coreutils
NetworkManager
NetworkManager-wifi
NetworkManager-bluetooth
wpa_supplicant
bluez
xorg-x11-server-Xwayland
flatpak
xdg-desktop-portal
xdg-desktop-portal-kde

# Calamares installer
calamares

# SynthOS gaming packages
synthex-core
synthex-kernel
plymouth
synthex-branding
synthex-grub-theme
synthex-plymouth-theme
synthex-cursors
synthex-sounds
synthex-wallpapers
synthex-system-daemon
synthex-control-center
synthex-gaming-center
synthex-app-manager
synthex-update-manager
synthex-performance-benchmark
synthex-cachu-tuning
synthex-nvidia-installer
synthex-codec-installer

# Performance monitoring
lm_sensors
nvme-cli
hdparm
htop
btop
iotop
inxi
pciutils
usbutils
dmidecode
wget
curl
git
vim-minimal
nano
rsync
%end

%post
#!/bin/bash
set -e

cat > /etc/yum.repos.d/synthex.repo << 'REPOEOF'
[synthex]
name=SynthOS Linux - Stable
baseurl=https://packages.getsynthex.org/stable/x86_64/
enabled=1
gpgcheck=0
priority=10

[synthex-updates]
name=SynthOS Linux - Updates
baseurl=https://packages.getsynthex.org/updates/x86_64/
enabled=1
gpgcheck=0
priority=10
REPOEOF

# Install gaming-focused Flatpaks
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flatpak-repo.flatpakrepo 2>/dev/null || true

# Kernel gaming tweaks
cat > /etc/sysctl.d/99-synthex-gaming.conf << 'SYSCTLEOF'
# SynthOS Gaming Tweaks
vm.swappiness=10
vm.compressibility_hint=0
kernel.sched_autogroup_enabled=1
kernel.perf_event_paranoid=1
net.ipv4.tcp_fastopen=3
net.core.netdev_max_backlog=16384
fs.file-max=524288
SYSCTLEOF

# MangoHud global config
mkdir -p /etc/MangoHud
cat > /etc/MangoHud/MangoHud.conf << 'MHEOF'
# SynthOS MangoHud Default Config
legacy_layout=false
position=top-left
gpu_stats
cpu_stats
fps
frametime
ram
cpu_temp
gpu_temp
wine
MHEOF

# GameMode config
cat > /etc/gamemode.ini << 'GMEOF'
[general]
renice=10
ioprio=0

[gpu]
apply_gpu_optimisations=accept-responsibility
gpu_device=0

[cpu]
park_cores=no
pin_cores=yes

[custom]
start=synthex-gaming-mode-start
end=synthex-gaming-mode-end
GMEOF

cat > /etc/default/grub << 'GRUBEOF'
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=0
GRUB_DISTRIBUTOR="SynthOS Gaming"
GRUB_CMDLINE_LINUX_DEFAULT="rhgb quiet splash mitigations=auto rd.driver.blacklist=nouveau modprobe.blacklist=nouveau processor.max_cstate=5 idle=nomwait"
GRUB_CMDLINE_LINUX="rd.luks=0 net.ifnames=0"
GRUB_DISABLE_RECOVERY="false"
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUB_GFXPAYLOAD_LINUX="keep"
GRUBEOF

mkdir -p /etc/synthex
cat > /etc/synthex/synthex-release << 'RELEOF'
NAME="SynthOS Linux"
VERSION="2026.10"
CODENAME="Ignition"
EDITION="Gaming"
ID="synthex"
ID_LIKE="fedora"
PRETTY_NAME="SynthOS Linux 2026.10 (Gaming)"
HOME_URL="https://getsynthex.org"
RELEOF

if [ -d /usr/share/plymouth/themes/synthex ]; then
    plymouth-set-default-theme synthex --rebuild-initrd 2>/dev/null || true
fi

systemctl enable NetworkManager sddm chronyd auditd fstrim.timer
systemctl disable lvm2-monitor mdmonitor 2>/dev/null || true
[ -f /usr/lib/systemd/system/synthex-firstboot.service ] && systemctl enable synthex-firstboot.service || true

echo "SynthOS Gaming Edition post-install complete."

# ── Enable live session setup (live-only via ConditionPathExists) ──
mkdir -p /run/synthex-live
systemctl enable synthex-live-setup.service 2>/dev/null || true
%end
