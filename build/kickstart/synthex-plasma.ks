# Synthex - KDE Plasma Edition
# Kickstart file for building reproducible Synthex ISO images
# Based on Fedora rawhide with Synthex repositories and kernel
#
# Usage: livecd-creator --config synthex-plasma.ks --releasever=rawhide

# =============================================================================
# COMMAND SECTION
# =============================================================================

# Install method: use upstream repos + Synthex repos
url --url="https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/x86_64/os/"
repo --name="synthex"     --baseurl="https://packages.getsynthex.org/shannon/x86_64/"
repo --name="synthex-updates" --baseurl="https://packages.getsynthex.org/unstable/x86_64/"
repo --name="synthex-nonfree" --baseurl="https://packages.getsynthex.org/contrib/x86_64/"
repo --name="fedora-rawhide" --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=rawhide&arch=x86_64"
repo --name="rpmfusion-free" --baseurl="https://mirrors.rpmfusion.org/free/fedora/development/rawhide/x86_64/"
repo --name="rpmfusion-nonfree" --baseurl="https://mirrors.rpmfusion.org/nonfree/fedora/development/rawhide/x86_64/"
repo --name="updates"   --baseurl="https://kojipkgs.fedoraproject.org/repos/rawhide-updates/latest/x86_64/"

# Target platform
platform x86_64

# Keyboard and language
keyboard us --xlayouts='us'
lang en_US.UTF-8

# Timezone
timezone America/New_York --isUtc

# Root password (CHANGE AFTER INSTALL)
rootpw --iscrypted locked

# SELinux
selinux --enforcing

# Bootloader
bootloader --location=mbr --driveorder=vda --append="rhgb quiet splash"

# Firewall and services
firewall --enabled --service=ssh,mdns,samba-client

# X Window System
xconfig --startxonboot

# Network
network --bootproto=dhcp --device=link --hostname=synthex-plasma --activate

# =============================================================================
# PACKAGE SECTION
# =============================================================================

zerombr
clearpart --all --initlabel
autopart --type=btrfs --encrypted=false

%packages --instLangs=en_US.UTF-8 --excludeWeakdeps --nocore

# Core system
synthex-core
synthex-base

# Plymouth
plymouth
plymouth-theme-synthex
plymouth-plugin-script

# ---- Core System ----
@fedora-kde-desktop
@standard
@kde-desktop
@kde-apps
@kde-office
@kde-multimedia
@kde-graphics
@kde-networking
kde-settings-plasma
plasma-workspace
plasma-desktop
plasma-systemsettings
plasma-nm
plasma-pa
sddm
sddm-breeze
sddm-kcm
dolphin
dolphin-plugins
konsole
kwrite
kate
okular
gwenview
spectacle
ark
kcalc
khelpcenter
kinfocenter
ksystemlog
filelight
kdf
kwakd
kde-connect
kdeplasma-addons
plasma-applet-redshift-control
plasma-applet-thermal-monitor
plasma-applets-workspace
plasma-browser-integration
plasma-discover
plasma-discover-notifier
plasma-disks
plasma-firewall
plasma-nm
plasma-systemsettings
plasma-user-manager
powerdevil
print-manager
kde-gtk-config
breeze
breeze-gtk
breeze-icon-theme
breeze-cursor-theme
oxygen-sounds
kde-print-manager
kdeaccessibility

# ---- Synthex Kernel ----
synthex-kernel
synthex-kernel-modules
synthex-kernel-headers
synthex-kernel-devel
synthex-firmware
synthex-ucode

# ---- Synthex Branding ----
synthex-branding
synthex-artwork
synthex-backgrounds
synthex-grub-theme
synthex-sddm-theme
synthex-plasma-theme
synthex-icon-theme
synthex-cursor-theme
synthex-fonts
synthex-wallpapers
synthex-sounds
synthex-gtk-theme
synthex-qt-theme
synthex-splash

# ---- Synthex Platform Meta-Packages ----
# Safety: DNF5 protect plugin, udev rules, perf sysctl, ZRAM, rescue USB, boot health
synthex-safety
# Essentials: Flatpak + Flathub + Flatseal + Warehouse + VPN + scanning + disk health + fwupd
synthex-essentials
# Creator: OBS plugins + color management (colord/DisplayCAL) + Wacom tablet + audio production
synthex-creator-platform
# Gaming platform: Steam + Proton-GE + Wine + DXVK + VKD3D + GameMode + Gamescope + MangoHUD + launchers + VR + streaming + handheld + Decky + Distrobox
synthex-gaming-platform
synthex-grub2

# ---- BTRFS & Storage ----
btrfs-progs
btrfs-assistant
snapper
snapper-rollback
snapper-gui
snapper-plasma
grub2-btrfs
compcache
zram-generator
util-linux
e2fsprogs
xfsprogs
dosfstools
ntfs-3g
exfat-utils
f2fs-tools
udftools
lvm2
cryptsetup
cryptsetup-luks
keyutils
device-mapper-multipath
mdadm
nbd
nvme-cli
sg3_utils
hdparm
smartmontools

# ---- Development Tools ----
# Focused set matching CachyOS/Nobara scope — not a polyglot dev distro.
# Heavy toolchains (gfortran/llvm/valgrind/systemtap) install via OOBE developer bundle.
@development-tools
gcc
gcc-c++
make
cmake
meson
ninja-build
autoconf
automake
libtool
pkgconf
patch
git
git-lfs
bzip2
xz
zstd
unzip
zip
tar
tmux
htop
btop
iotop
strace
lsof
gdb
binutils
elfutils
perf

# ---- Programming Languages ----
# Core languages only. Rare langs (Haskell/Scala/Kotlin/Erlang/OCaml/Prolog/Dart/R/Julia)
# are NOT shipped on the ISO — install via the developer bundle if needed.
python3
python3-pip
python3-devel
nodejs
npm
rust
cargo
go

# ---- Containers & Virtualization ----
# Podman + Distrobox for container dev (Bazzite-style). No K8s/helm/terraform/pulumi.
podman
podman-compose
buildah
skopeo
distrobox
qemu
qemu-kvm
libvirt
virt-manager

# ---- AI (lightweight, not heavy ML frameworks) ----
# Our synthex-ai-hub + AI assistant are lightweight Python tools that call local Ollama.
# Heavy frameworks (tensorflow/torch/CUDA/cuDNN/tensorrt) are NOT on the ISO — they're
# several GB and not needed for the desktop/gaming use case. Install via developer bundle.
ollama
synthex-ai-hub

# ---- Gaming ----
steam
steam-devices
lutris
heroic-games-launcher
wine
wine-core
wine-devel
winetricks
proton
proton-ge
gamescope
mangohud
mangohud-gnome
gamemode
game-devices-udev
vkd3d
vkd3d-devel
dxvk
dxvk-bin
vkbasalt
umuv
wine-staging
bottles
itch-setup
minecraft-launcher
prismlauncher
ryujinx
yuzu
rpcs3
pcsx2
ppsspp
dolphin-emu
duckstation
retroarch
retroarch-assets
retroarch-core-info
retroarch-database
retroarch-shaders
mame
scummvm
dosbox
dosbox-staging
fs-uae
openra
0ad
warzone2100
wesnoth
supertuxkart
speed-dreams
flightgear
openttd
endless-sky
naev
hedgewars
teeworlds
xonotic
ioquake3
openarena
urbanterror
assaultcube
red-eclipse
multimc
prismlauncher
umm
legendary
rare
gogdownloader

# ---- Content Creation ----
kdenlive
kdenlive-effects
kdenlive-tools
krita
gimp
gimp-resynthesizer
inkscape
blender
blender-addons
darktable
rawtherapee
digikam
digikam-libs
showfoto
shotwell
shotwell-plugins
ocenaudio
audacity
ardour
lmms
hydrogen
musescore
qtractor
sox
ffmpeg
ffmpeg-devel
ffmpeg-libs
libavcodec
libavformat
libavutil
libswscale
libavfilter
libpostproc
libavdevice
obs-studio
obs-studio-plugins
obs-vkcapture
obs-gstreamer
vlc
vlc-core
mpv
mpv-libs
handbrake
handbrake-gui
handbrake-cli
mkvtoolnix
mkvtoolnix-gui
mediainfo
exiftool
imagemagick
graphicsmagick
rawtherapee
darktable
photivo
scribus
pinta
mypaint
karbon
calligra
calligra-sheets
calligra-plan
calligra-stage
calligra-flow
libreoffice
libreoffice-kde
libreoffice-l10n-en
texlive
texlive-latex
texlive-xetex
texlive-luatex
texstudio
texmaker
lyx
pandoc
pandoc-plot

# ---- Communication ----
discord
telegram-desktop
signal-desktop
element
fractal
pidgin
hexchat
irssi
weechat
thunderbird
thunderbird-l10n-en
geary
evolution
evolution-ews
evolution-mapi
kdepim
kmail
korganizer
kaddressbook
kontact
akregator
kget
ktorrent
transmission
transmission-gtk
qbittorrent
deluge
deluge-web
aria2
curl
wget
mosh
openssh
openssh-server
tailsocks
tor
tor-geoip
torbrowser-launcher
proxychains
privoxy

# ---- Internet & Browsers ----
firefox
firefox-l10n-en
chromium
google-chrome-stable
google-chrome-beta
brave-browser
brave-browser-l10n
vivaldi
vivaldi-ffmpeg-codecs
vivaldi-widevine
opera
opera-libffmpeg
falkon
qutebrowser
nyxt
epiphany
konqueror

# ---- Utilities ----
kate
kwrite
konsole
yakuake
guake
tilix
terminator
keepassxc
bitwarden
nextcloud-client
owncloud-client
syncthing
syncthingtray
rsync
rclone
rclone-browser
duplicity
borgbackup
borgmatic
restic
vorta
timeshift
backintime
deja-dup
grub-customizer
gparted
partitionmanager
krdc
krfb
remmina
remmina-plugins-rdp
remmina-plugins-vnc
remmina-plugins-spice
remmina-plugins-www
filezilla
gftp
wireshark
wireshark-cli
tcpdump
nmap
ncat
netcat
socat
sshfs
curlftpfs
samba
samba-client
cifs-utils
nfs-utils
nfs4-acl-tools
autofs
p7zip
p7zip-plugins
unrar
unace
arj
lzip
lzop
plzip
pbzip2
pigz
pxz
cpio

# ---- Fonts ----
@fonts
google-noto-sans-fonts
google-noto-serif-fonts
google-noto-mono-fonts
google-noto-emoji-fonts
google-noto-cjk-fonts
jetbrains-mono-fonts
liberation-fonts
dejavu-sans-fonts
dejavu-serif-fonts
dejavu-sans-mono-fonts
inter-fonts

# ---- Hardware Support ----
@hardware-support
synthex-driver-manager
synthex-prime
synthex-nvidia
synthex-amdgpu
synthex-intel
fprintd
libfprint
thinks
fwupd
fwupd-efi
tpm2-tools
tpm2-abrmd
tpm2-tss
bolt
wireless-regdb
wireless-tools
iw
iwd
wpa_supplicant
hostapd
bluez
bluez-utils
bluedevil
pulseaudio-modules-bt
pipewire-pulseaudio
pulseaudio-utils
pavucontrol
pamixer
sof-firmware
alsa-firmware
alsa-ucm
alsa-sof-firmware

# ---- Cleanup exclusions ----
-xfce*
-gnome*
-@mate*
-@cinnamon*
-@lxde*
-@lxqt*
-@budgie*
-@enlightenment*
-@sway*
-*sugar*
-*abrt*
-*sendmail*
-*postfix*
-*geoclue*
-*cheese*
-*gnome-software*
-*gnome-games*
-*gnome-contacts*
-*gnome-maps*
-*gnome-weather*
-*gnome-clocks*
-*gnome-calendar*
-*gnome-characters*
-*gnome-logs*
-*gnome-system-monitor*
-*gnome-terminal*
-*gnome-tour*
-*totem*
-*rhythmbox*
-*fedora-welcome*
-*initial-setup*
-*-debuginfo*
-*-devel-docs*
-*-doc*
-*langpacks-*

%end

# =============================================================================
# POST-INSTALL SECTION
# =============================================================================

%post --interpreter=/bin/bash --log=/root/kickstart-post.log

# -------------------------------------------------------------------------
# System Configuration
# -------------------------------------------------------------------------

set -euo pipefail

echo "=== Synthex Post-Install Script ==="

# Create Synthex directory structure
mkdir -p /etc/synthex
cat > /etc/synthex/os-release << 'EOSYNTHEX'
NAME="Synthex"
ID="synthex"
PRETTY_NAME="Synthex Plasma Edition"
VERSION="1.0"
HOME_URL="https://getsynthex.org"
SUPPORT_URL="https://discuss.getsynthex.org"
BUG_REPORT_URL="https://dev.getsynthex.org"
PRIVACY_POLICY_URL="https://getsynthex.org/privacy"
LOGO="synthex"
ANSI_COLOR="0;36"
EOSYNTHEX

# Configure DNF for Synthex repos
cat > /etc/yum.repos.d/synthex.repo << 'EOREPO'
[synthex]
name=Synthex Packages
baseurl=https://packages.getsynthex.org/shannon/x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://getsynthex.org/synthex.gpg
priority=5

[synthex-updates]
name=Synthex Updates
baseurl=https://packages.getsynthex.org/unstable/x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://getsynthex.org/synthex.gpg
priority=10

[synthex-nonfree]
name=Synthex Non-Free
baseurl=https://packages.getsynthex.org/contrib/x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://getsynthex.org/synthex.gpg
priority=15

[synthex-source]
name=Synthex Source
baseurl=https://packages.getsynthex.org/shannon/sources/
enabled=0
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://getsynthex.org/synthex.gpg
EOREPO

# Import Synthex GPG key
curl -fsSL https://getsynthex.org/synthex.gpg -o /etc/pki/rpm-gpg/synthex.gpg
rpm --import /etc/pki/rpm-gpg/synthex.gpg

# -------------------------------------------------------------------------
# BTRFS Configuration
# -------------------------------------------------------------------------

# Configure BTRFS with compression and snapshots
cat > /etc/defines/btrfs-config << 'EOBTRFS'
# Synthex BTRFS Configuration
COMPRESSION_ALGORITHM=zstd
COMPRESSION_LEVEL=3
SUBVOLUME_ROOT=@
SUBVOLUME_HOME=@home
SUBVOLUME_VAR=@var
SUBVOLUME_TMP=@tmp
SUBVOLUME_SNAP=@snapshots
SUBVOLUME_LOG=@log
SUBVOLUME_CACHE=@cache
AUTO_DEFRAG=yes
SSD_OPTIMIZATION=yes
SPACE_CACHE=v2
EOBTRFS

# Configure automatic snapshots
cat > /etc/snapper/configs/root << 'EOSNAPPER'
SUBVOLUME="/"
FSTYPE="btrfs"
QGROUP="1/0"
SPACE_LIMIT="0.5"
FREE_LIMIT="0.2"
ALLOW_USERS=""
ALLOW_GROUPS="wheel"
SYNC_ACL="no"
BACKGROUND_COMPARISON="yes"
NUMBER_CLEANUP="yes"
NUMBER_MIN_AGE="1800"
NUMBER_LIMIT="50"
NUMBER_LIMIT_IMPORTANT="10"
TIMELINE_CREATE="yes"
TIMELINE_CLEANUP="yes"
TIMELINE_MIN_AGE="1800"
TIMELINE_LIMIT_HOURLY="10"
TIMELINE_LIMIT_DAILY="10"
TIMELINE_LIMIT_WEEKLY="0"
TIMELINE_LIMIT_MONTHLY="0"
TIMELINE_LIMIT_YEARLY="0"
EOSNAPPER

# -------------------------------------------------------------------------
# SELinux Configuration
# -------------------------------------------------------------------------

# Set enforcing mode
sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
mkdir -p /selinux
touch /selinux/enforce

# -------------------------------------------------------------------------
# Services Configuration
# -------------------------------------------------------------------------

# Enable essential services
systemctl enable sddm.service
systemctl enable NetworkManager.service

# ─── Live ISO configuration ───────────────────────────────────────────
# The kickstart produces a LIVE ISO. Configure SDDM autologin for liveuser
# so booting the USB lands directly on the desktop (not a login screen).
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/autologin.conf << 'EOAUTOLOGIN'
[Autologin]
User=liveuser
Session=plasma.desktop
Relogin=true
EOAUTOLOGIN

# Allow liveuser to run the installer without a password (polkit rule)
mkdir -p /etc/polkit-1/rules.d
cat > /etc/polkit-1/rules.d/49-synthex-live-installer.rules << 'EOPOLKIT'
polkit.addRule(function(action, subject) {
    if (action.id == "org.kde.kcontrol.kcmcalamares" ||
        action.id == "com.github.calamares.installer" ||
        action.id == "org.freedesktop.policykit.exec") {
        if (subject.isInGroup("wheel")) {
            return polkit.Result.YES;
        }
    }
});
EOPOLKIT

# Place the installer shortcut on the live desktop
mkdir -p /home/liveuser/Desktop
cp /usr/share/applications/synthex-installer.desktop /home/liveuser/Desktop/ 2>/dev/null || true
chmod +x /home/liveuser/Desktop/synthex-installer.desktop 2>/dev/null || true
chown -R 1000:1000 /home/liveuser/Desktop 2>/dev/null || true

# Passwordless sudo for liveuser on the live ISO (account is locked, autologin)
mkdir -p /etc/sudoers.d
echo "liveuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/10-liveuser
chmod 440 /etc/sudoers.d/10-liveuser
systemctl enable bluetooth.service
systemctl enable cups.service
systemctl enable avahi-daemon.service
systemctl enable sshd.service
systemctl enable fwupd.service
systemctl enable snapper-timeline.timer
systemctl enable snapper-cleanup.timer
systemctl enable btrfs-scrub@-.timer
systemctl enable systemd-bootchart.service
systemctl enable docker.service
systemctl enable containerd.service
systemctl enable podman.socket
systemctl enable cronie.service

# Enable Synthex platform services (safety, slim, boot profiling, OOBE, control center)
systemctl enable synthex-safety.service 2>/dev/null || true
systemctl enable synthex-slim.service 2>/dev/null || true
systemctl enable synthex-boot-profile.service 2>/dev/null || true
systemctl enable synthex-oobe.service 2>/dev/null || true
systemctl enable synthex-control-center.service 2>/dev/null || true
systemctl enable synthex-auto-tune.service 2>/dev/null || true
systemctl enable synthex-auto-tune.path 2>/dev/null || true
systemctl enable synthex-gaming-mode.service 2>/dev/null || true
systemctl enable synthex-workspace.service 2>/dev/null || true
systemctl enable synthex-desktopd.service 2>/dev/null || true
systemctl enable synthex-hwdaemon.service 2>/dev/null || true
systemctl enable synthex-gpu-setupd.service 2>/dev/null || true
systemctl enable synthex-stored.service 2>/dev/null || true

# Disable unnecessary services
systemctl disable kdump.service 2>/dev/null || true
systemctl disable irqbalance.service 2>/dev/null || true

# Configure zram
cat > /etc/systemd/zram-generator.conf << 'EOZRAM'
[zram0]
zram-fraction = 0.5
compression-algorithm = zstd
EOZRAM

# -------------------------------------------------------------------------
# User Configuration
# -------------------------------------------------------------------------

# Create default skel configuration
cat > /etc/skel/.bashrc << 'EOBASHRC'
# Synthex Bash Configuration
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# Aliases
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias cls='clear'
alias sudo='sudo '
alias update='sudo dnf update --refresh'
alias upgrade='sudo dnf upgrade'
alias install='sudo dnf install'
alias remove='sudo dnf remove'
alias search='dnf search'
alias grep='grep --color=auto'
alias diff='diff --color=auto'
alias ip='ip --color=auto'

# Prompt
PS1='\[\e[0;36m\][\u@\h \W]\$\[\e[0m\] '

# History
HISTSIZE=10000
HISTFILESIZE=20000
HISTCONTROL=ignoredups:erasedups
HISTTIMEFORMAT="%F %T "

# Completion
if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
fi

# Environment
export EDITOR=nano
export VISUAL=nano
export BROWSER=firefox
EOBASHRC

cat > /etc/skel/.config/kdeglobals << 'EOKDEGLOBALS'
[General]
ColorScheme=BreezeLight
Name=Breeze
font=Noto Sans,10,-1,5,50,0,0,0,0,0
fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0
toolBarFont=Noto Sans,10,-1,5,50,0,0,0,0,0
menuFont=Noto Sans,10,-1,5,50,0,0,0,0,0
smallestReadableFont=Noto Sans,8,-1,5,50,0,0,0,0,0

[Icons]
Theme=breeze

[KDE]
AnimationDurationFactor=1
AnimationDurationFactor=1
widgetStyle=Breeze
LookAndFeelPackage=org.synthex.desktop

[KShortcuts]
Scheduler=Ctrl+Alt+S

[WM]
activeFont=Noto Sans,10,-1,5,50,0,0,0,0,0
EOKDEGLOBALS

# Configure Plasma defaults
mkdir -p /etc/skel/.config
cat > /etc/skel/.config/plasma-org.kde.plasma.desktop-appletsrc << 'EOPLASMA'
[ActionPlugins][0]
LeftButton;NoModifier=org.kde.paste

[Containments][1]
activityId=1222d3b6-2f61-4efa-8f35-d3f13a9b91b7
formfactor=0
immutability=1
lastScreen=0
location=4
plugin=org.kde.panel
screen=0

[Containments][2]
activityId=1222d3b6-2f61-4efa-8f35-d3f13a9b91b7
formfactor=2
immutability=1
lastScreen=0
location=0
plugin=org.kde.plasma.folder
screen=0
wallpaperplugin=org.kde.image

[Containments][2][Wallpaper][org.kde.image][General]
Image=file:///usr/share/wallpapers/synthex-default.jpg
FillMode=2

[Containments][3]
activityId=1222d3b6-2f61-4efa-8f35-d3f13a9b91b7
formfactor=0
immutability=1
lastScreen=0
location=3
plugin=org.kde.plasma.icontasks
screen=0
EOPLASMA

# -------------------------------------------------------------------------
# Theming
# -------------------------------------------------------------------------

# Apply Synthex branding
mkdir -p /etc/skel/.local/share/plasma/look-and-feel
cat > /etc/skel/.local/share/plasma/look-and-feel/org.synthex.desktop/metadata.desktop << 'EOTHEME'
[Desktop Entry]
Type=X-KDE-LookAndFeel
Name=Synthex Plasma
Comment=Synthex Plasma Theme
X-KDE-PluginInfo-Author=Synthex Project
X-KDE-PluginInfo-Email=support@getsynthex.org
X-KDE-PluginInfo-Name=org.synthex.desktop
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-License=GPLv2
X-KDE-PluginInfo-EnabledByDefault=true
EOTHEME

# Copy Synthex branding assets
mkdir -p /usr/share/synthex
mkdir -p /usr/share/wallpapers
mkdir -p /usr/share/plasma/plasmoids
mkdir -p /usr/share/icons/hicolor/256x256/apps

# Set default wallpaper symlink
ln -sf /usr/share/wallpapers/synthex-default.jpg /usr/share/wallpapers/default.jpg

# -------------------------------------------------------------------------
# Desktop Shortcuts
# -------------------------------------------------------------------------

mkdir -p /etc/skel/Desktop
cat > /etc/skel/Desktop/README.desktop << 'EOREADME'
[Desktop Entry]
Type=Link
Name=Welcome to Synthex
Comment=Getting started with Synthex
Icon=help-about
URL=https://getsynthex.org/welcome
EOREADME

cat > /etc/skel/Desktop/synthex-store.desktop << 'EOSTORE'
[Desktop Entry]
Type=Application
Name=Synthex Software Center
Comment=Browse and install applications
Icon=system-software-install
Exec=plasma-discover
Terminal=false
Categories=System;PackageManager;
EOSTORE

# -------------------------------------------------------------------------
# Developer Environment
# -------------------------------------------------------------------------

# Set up Python virtual environment infrastructure
mkdir -p /etc/skel/.venv
cat > /etc/skel/.venv/pyproject.toml << 'EOPYPROJ'
[tool.poetry]
name = "synthex-default"
version = "1.0.0"
description = "Synthex Python Environment"
authors = ["Synthex Project"]

[tool.poetry.dependencies]
python = "^3.12"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOPYPROJ

# Configure Docker defaults
mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EODOCKER'
{
  "storage-driver": "overlay2",
  "storage-opts": ["overlay2.override_kernel_check=true"],
  "log-driver": "json-file",
  "log-opts": {"max-size": "10m", "max-file": "3"},
  "registry-mirrors": [],
  "experimental": true,
  "features": {"buildkit": true}
}
EODOCKER

# -------------------------------------------------------------------------
# Gaming Optimization
# -------------------------------------------------------------------------

# GameMode configuration
cat > /etc/gamemode.ini << 'EOGAMEMODE'
[general]
renice=10
softrealtime=auto
desiredgov=performance
igpu_desiredgov=performance
inigpu_desiredgov=performance
desiredgov=performance

[filter]
whitelist=steam*,lutris*,heroic*,wine*,Zomboid*,Dota*,CSGO*,hl2*,portal*

[gpu]
apply_gpu_optimisations=accept-responsibility
gpu_device=0
amd_performance_level=high

[cpu]
apply_cpu_optimisations=yes
park_cores=no
pin_cores=yes

[supervisor]
supervisord=yes
EOGAMEMODE

# MangoHud configuration
mkdir -p /etc/skel/.config/MangoHud
cat > /etc/skel/.config/MangoHud/MangoHud.conf << 'EOMANGOHUD'
legacy_layout=false
fps
frametime
cpu_stats
gpu_stats
cpu_temp
gpu_temp
ram
vram
cpu_mhz
gpu_mhz
resolution
time
toggle_hud=Shift_R+F12
upload_log=F2
EOMANGOHUD

# Wine configuration
cat > /etc/wine/wine.conf << 'EOWINE'
[Version]
; Use Win10 for maximum compatibility
; Change to Win7 for older games
Windows=win10

[Desktop]
; Run in virtual desktop for better window management
; Set to 0 for fullscreen
VirtualDesktop=0

[Hardware]
; Enable GPU acceleration
Direct3D=opengl
DirectDrawRenderer=opengl
Multisampling=enabled
StrictDrawOrder=enabled
UseGLSL=enabled
VideoMemorySize=4096
EOWINE

# -------------------------------------------------------------------------
# Firstboot Configuration
# -------------------------------------------------------------------------

mkdir -p /etc/synthex/firstboot.d
cat > /etc/synthex/firstboot.d/10-welcome.sh << 'EOWELCOME'
#!/usr/bin/env bash
# Synthex First Boot - Welcome
if [ ! -f "$HOME/.config/synthex-welcome-done" ]; then
    firefox "https://getsynthex.org/welcome" &
    touch "$HOME/.config/synthex-welcome-done"
fi
EOWELCOME

cat > /etc/synthex/firstboot.d/20-initial-setup.sh << 'EOINITIAL'
#!/usr/bin/env bash
# Synthex First Boot - Initial Configuration
set -euo pipefail

# Detect hardware and apply optimizations
/usr/libexec/synthex/hardware-detect.sh

# Apply user-specific theming
/usr/libexec/synthex/apply-theme.sh

# Configure display
if command -v xrandr &>/dev/null; then
    # Auto-detect monitors
    xrandr --auto 2>/dev/null || true
fi
EOINITIAL

chmod +x /etc/synthex/firstboot.d/*.sh

# Create firstboot systemd service
cat > /etc/systemd/system/synthex-firstboot.service << 'EOFBUNIT'
[Unit]
Description=Synthex First Boot Configuration
ConditionPathExists=!/var/lib/synthex-firstboot-done
After=network.target graphical.target

[Service]
Type=oneshot
ExecStart=/usr/libexec/synthex/firstboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOFBUNIT

# Create firstboot script
mkdir -p /usr/libexec/synthex
cat > /usr/libexec/synthex/firstboot.sh << 'EOFBSCR'
#!/usr/bin/env bash
set -euo pipefail

# Run all firstboot scripts
for script in /etc/synthex/firstboot.d/*.sh; do
    if [ -x "$script" ]; then
        echo "Running: $script"
        su -l "$(logname 2>/dev/null || echo 'liveuser')" -c "$script" 2>/dev/null || true
    fi
done

# Mark firstboot as complete
touch /var/lib/synthex-firstboot-done
EOFBSCR
chmod +x /usr/libexec/synthex/firstboot.sh
chmod +x /usr/libexec/synthex/hardware-detect.sh 2>/dev/null || true

systemctl enable synthex-firstboot.service

# -------------------------------------------------------------------------
# Cleanup
# -------------------------------------------------------------------------

# Reset machine-id (regenerated on first boot)
rm -f /etc/machine-id
touch /etc/machine-id

# Clean package cache
dnf clean all

# Remove SSH host keys (regenerated on first boot)
rm -f /etc/ssh/ssh_host_*

# Zero out free space for better compression
dd if=/dev/zero of=/zero.fill bs=1M 2>/dev/null || true
rm -f /zero.fill

# Install Synthex killer-feature scripts
mkdir -p /usr/libexec/synthex
cp /synthex/scripts/synthex-auto-tune.sh /usr/libexec/synthex/synthex-auto-tune 2>/dev/null || true
cp /synthex/scripts/synthex-gaming-mode.sh /usr/libexec/synthex/synthex-gaming-mode 2>/dev/null || true
cp /synthex/scripts/synthex-migrate-from-windows.sh /usr/libexec/synthex/synthex-migrate-from-windows 2>/dev/null || true
cp /synthex/scripts/synthex-recovery-grub.sh /usr/libexec/synthex/synthex-recovery-grub 2>/dev/null || true
chmod +x /usr/libexec/synthex/synthex-* 2>/dev/null || true

echo "=== Synthex Post-Install Complete ==="

%end

# =============================================================================
# ADDITIONAL CONFIGURATION
# =============================================================================

# Add firstboot config
%addon com_redhat_kdump --disable --reserve-mb=0

%addon org_synthex_linux_firstboot --enable

# Default runlevel
%addon org_fedora_anaconda_users
root --lock
user --name=liveuser --groups=wheel,users,docker,libvirt,kvm,audio,video,storage,adm --password=liveuser --iscrypted --lock
%end

# Live user for ISO
services --disabled=initial-setup,initial-setup-graphical,anaconda-firstboot

# =============================================================================
# END OF KICKSTART

