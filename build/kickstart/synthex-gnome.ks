# SynthOS Linux — GNOME Edition Kickstart
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
selinux --enforcing
firewall --enabled --service=mdns,ssh
services --enabled=NetworkManager,sshd,chronyd,auditd,fstrim.timer,gdm,synthex-firstboot,synthex-system-daemon
services --disabled=lvm2-monitor,mdmonitor
bootloader --location=mbr --append="rhgb quiet splash mitigations=auto"
network --bootproto=dhcp --device=link --activate
rootpw --lock
firstboot --reconfig
xconfig --startxonboot

xconfig --startxonboot

# ── LIVE IMAGE ───────────────────────────────────────────────────────────────
# Livecd-creator builds a squashfs live root (overlayfs) mounted read-write on
# boot: the ISO is FULLY USABLE as a desktop before any installation. Contents
# are ephemeral; "Install Synthex" on the desktop (Calamares) writes to disk.
liveimg --name="Synthex-Gnome" --nombr

# Live session non-root user (also created by live-setup.sh at first boot).
# Auto-login + passwordless sudo wired in %post below.
user --name=liveuser --groups=wheel,audio,video,input,storage --password=liveuser

%packages
@core
@hardware-support
@fonts
@multimedia
@networkmanager-submodules

# GNOME desktop
@gnome-desktop
gnome-shell
gnome-session
gnome-control-center
gnome-tweaks
gnome-extensions-app
gnome-software
gnome-calculator
gnome-calendar
gnome-characters
gnome-clocks
gnome-color-manager
gnome-disk-utility
gnome-logs
gnome-maps
gnome-photos
gnome-screenshot
gnome-system-monitor
gnome-terminal
gnome-text-editor
gnome-weather
nautilus
eog
evince
totem
rhythmbox
gedit
baobab
gdm
gnome-shell-extension-appindicator
gnome-shell-extension-dash-to-dock
gnome-shell-extension-blur-my-shell
gnome-shell-extension-user-theme
adwaita-icon-theme
adwaita-gtk2-theme

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
pipewire
pipewire-pulseaudio
wireplumber
gstreamer1-plugins-good
gstreamer1-plugins-bad-free
gstreamer1-vaapi
ffmpeg-free
mesa-dri-drivers
mesa-vulkan-drivers
wayland-protocols-devel
xorg-x11-server-Xwayland
flatpak
xdg-desktop-portal
xdg-desktop-portal-gnome
xdg-user-dirs
cups
python3
python3-libs

# Calamares installer
calamares

# SynthOS packages
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
synthex-app-manager
synthex-update-manager

# SynthOS platform bundles (meta-groups from synthex-comps.xml)
@synthex-safety
@synthex-essentials
@synthex-creator-platform
synthex-widgets
synthex-blueprint
synthex-boot
@synthex-gaming-platform

# Utilities
htop
neofetch
fastfetch
wget
curl
git
vim-minimal
nano
rsync
tar
xz
smartmontools
lm_sensors
inxi
pciutils
usbutils
%end

%post
#!/bin/bash
set -e

# Configure SynthOS repos
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

flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flatpak-repo.flatpakrepo 2>/dev/null || true

cat > /etc/default/grub << 'GRUBEOF'
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=0
GRUB_DISTRIBUTOR="SynthOS Linux"
GRUB_CMDLINE_LINUX_DEFAULT="rhgb quiet splash mitigations=auto"
GRUB_CMDLINE_LINUX="rd.luks=0 net.ifnames=0"
GRUB_DISABLE_RECOVERY="false"
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUB_GFXPAYLOAD_LINUX="keep"
GRUBEOF

if [ -d /usr/share/plymouth/themes/synthex ]; then
    plymouth-set-default-theme synthex --rebuild-initrd 2>/dev/null || true
fi

mkdir -p /etc/synthex
cat > /etc/synthex/synthex-release << 'RELEOF'
NAME="SynthOS Linux"
VERSION="2026.10"
CODENAME="Ignition"
EDITION="GNOME"
ID="synthex"
ID_LIKE="fedora"
PRETTY_NAME="SynthOS Linux 2026.10 (GNOME)"
HOME_URL="https://getsynthex.org"
RELEOF

systemctl enable NetworkManager gdm chronyd auditd fstrim.timer
systemctl disable lvm2-monitor mdmonitor 2>/dev/null || true
[ -f /usr/lib/systemd/system/synthex-firstboot.service ] && systemctl enable synthex-firstboot.service || true

cat > /etc/dnf/dnf.conf << 'DNFEOF'
[main]
gpgcheck=1
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
fastestmirror=True
deltarpm=True
max_parallel_downloads=10
defaultyes=True
DNFEOF

echo "SynthOS GNOME Edition post-install complete."

# ── Enable live session installation (live-only via ConditionPathExists) ──
mkdir -p /run/synthex-live
systemctl enable synthex-live-setup.service 2>/dev/null || true
%end
