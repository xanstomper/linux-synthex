# Solus Linux - GNOME Edition
# Kickstart file for building reproducible Solus GNOME ISO images
#
# Usage: livecd-creator --config solus-gnome.ks --releasever=rawhide

# =============================================================================
# COMMAND SECTION
# =============================================================================

url --url="https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/x86_64/os/"
repo --name="solus"         --baseurl="https://packages.getsol.us/shannon/x86_64/"
repo --name="solus-updates" --baseurl="https://packages.getsol.us/unstable/x86_64/"
repo --name="solus-nonfree" --baseurl="https://packages.getsol.us/contrib/x86_64/"
repo --name="fedora-rawhide" --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=rawhide&arch=x86_64"
repo --name="rpmfusion-free" --baseurl="https://mirrors.rpmfusion.org/free/fedora/development/rawhide/x86_64/"
repo --name="rpmfusion-nonfree" --baseurl="https://mirrors.rpmfusion.org/nonfree/fedora/development/rawhide/x86_64/"

platform x86_64
keyboard us --xlayouts='us'
lang en_US.UTF-8
timezone America/New_York --isUtc
rootpw --iscrypted locked
selinux --enforcing
bootloader --location=mbr --driveorder=vda --append="rhgb quiet splash"
firewall --enabled --service=ssh
xconfig --startxonboot
network --bootproto=dhcp --device=link --hostname=solus-gnome --activate

services --disabled=initial-setup,initial-setup-graphical

# =============================================================================
# PACKAGE SECTION
# =============================================================================

%packages --instLangs=en_US.UTF-8 --excludeWeakdeps --nocore

# ---- GNOME Desktop ----
@gnome-desktop
@gnome-apps
@gnome-software
@base
@base-x
@fonts
@hardware-support
@standard

gnome-shell
gnome-shell-extension-appindicator
gnome-shell-extension-blur-my-shell
gnome-shell-extension-dash-to-dock
gnome-shell-extension-gsconnect
gnome-shell-extension-user-theme
gnome-shell-extension-caffeine
gnome-shell-extension-vitals
gnome-shell-extension-just-perfection
gnome-shell-extension-tiling-assistant
gnome-shell-extension-forge
gnome-shell-extension-pop-shell
gnome-shell-extension-arcmenu
gnome-shell-extension-burn-my-windows
gnome-tweaks
gnome-extensions-app
gnome-software
gnome-characters
gnome-clocks
gnome-calendar
gnome-contacts
gnome-logs
gnome-maps
gnome-weather
gnome-connections
gnome-console
gnome-text-editor
gnome-calculator
gnome-screenshot
gnome-disk-utility
gnome-system-monitor
gnome-usage
gnome-firmware
gnome-bluetooth
evince
eog
loupe
totem
rhythmbox
nautilus
nautilus-extensions
nautilus-python
nautilus-sendto
gvfs
gvfs-goa
gvfs-google
gvfs-gphoto2
gvfs-mtp
gvfs-smb
gvfs-afc
gdm
gdm-settings
mutter
mutter-common
adwaita-gtk2-theme
adwaita-icon-theme
adwaita-cursor-theme
cantarell-fonts
gtk3
gtk4
libadwaita
libadwaita-demos

# ---- Solus Kernel ----
solus-kernel
solus-kernel-modules
solus-kernel-headers
solus-kernel-devel
solus-firmware
solus-ucode

# ---- Solus Branding ----
solus-branding
solus-artwork
solus-backgrounds
solus-fonts
solus-wallpapers
solus-gtk-theme
solus-gnome-theme

# ---- Solus Platform Meta-Packages ----
solus-safety
solus-essentials
solus-creator-platform
solus-gaming-platform
solus-icon-theme
solus-cursor-theme
solus-sounds
solus-grub-theme
solus-gdm-theme
solus-splash
solus-grub2

# ---- BTRFS & Storage ----
btrfs-progs
btrfs-assistant
snapper
snapper-rollback
snapper-gui
grub2-btrfs
compcache
zram-generator
util-linux
e2fsprogs
cryptsetup
cryptsetup-luks
lvm2
nvme-cli
smartmontools

# ---- Development ----
@development-tools
@c-development
gcc
gcc-c++
make
cmake
meson
ninja-build
git
git-lfs
python3
python3-devel
python3-pip
nodejs
npm
rust
cargo
go
java-21-openjdk
java-21-openjdk-devel

# ---- Containers ----
docker-ce
docker-ce-cli
docker-compose
containerd
podman
podman-compose
buildah
kubectl
helm
ansible

# ---- AI & ML ----
python3-tensorflow
python3-torch
python3-transformers
python3-diffusers
python3-datasets
python3-accelerate
python3-langchain
python3-llama-cpp-python
python3-whisper
python3-openai
python3-ollama
python3-chromadb
python3-faiss
python3-onnxruntime
solus-cuda-toolkit

# ---- Gaming ----
steam
steam-devices
lutris
heroic-games-launcher
wine
wine-core
winetricks
proton
gamescope
mangohud
gamemode
vkd3d
dxvk
retroarch

# ---- Content Creation ----
gimp
inkscape
blender
kdenlive
audacity
ffmpeg
obs-studio
vlc
mpv
libreoffice
libreoffice-gnome

# ---- Communication ----
discord
telegram-desktop
signal-desktop
element
geary
evolution
evolution-ews
firefox
chromium
brave-browser

# ---- GNOME-specific apps ----
pods
fragments
amberol
decibels
eyedropper
font-manager
gradio
impression
jellyfish
keypunch
mousai
newsflash
obfuscate
planify
polari
resources
sound-recorder
tagger
textpieces
video-trimmer
warp
wike

# ---- Utilities ----
keepassxc
nextcloud-client
syncthing
rsync
rclone
borgbackup
restic
timeshift
gparted
wireshark
tcpdump
nmap
openssh
openssh-server
p7zip
unrar
htop
btop
fastfetch

# ---- Cleanup exclusions ----
-*plasma*
-*kde*
-*xfce*
-*mate*
-*cinnamon*
-*budgie*
-*enlightenment*
-*lxde*
-*lxqt*
-*sway*
-*hyprland*
-*sugar*
-*abrt*
-*sendmail*
-*postfix*
-*cheese*
-*initial-setup*
-*fedora-welcome*
-*-debuginfo*
-*-devel-docs*

%end

# =============================================================================
# POST-INSTALL SECTION
# =============================================================================

%post --interpreter=/bin/bash --log=/root/kickstart-post.log

set -euo pipefail

echo "=== Solus GNOME Edition Post-Install ==="

# OS release
mkdir -p /etc/solus
cat > /etc/solus/os-release << 'EOSOLUS'
NAME="Solus Linux"
ID="solus"
PRETTY_NAME="Solus Linux GNOME Edition"
VERSION="1.0"
HOME_URL="https://getsol.us"
SUPPORT_URL="https://discuss.getsol.us"
BUG_REPORT_URL="https://dev.getsol.us"
LOGO="solus"
ANSI_COLOR="0;36"
EOSOLUS

# Solus repos
cat > /etc/yum.repos.d/solus.repo << 'EOREPO'
[solus]
name=Solus Linux Packages
baseurl=https://packages.getsol.us/shannon/x86_64/
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://getsol.us/solus.gpg
priority=5

[solus-updates]
name=Solus Linux Updates
baseurl=https://packages.getsol.us/unstable/x86_64/
enabled=1
gpgcheck=1
gpgkey=https://getsol.us/solus.gpg
priority=10

[solus-nonfree]
name=Solus Linux Non-Free
baseurl=https://packages.getsol.us/contrib/x86_64/
enabled=1
gpgcheck=1
gpgkey=https://getsol.us/solus.gpg
priority=15
EOREPO

curl -fsSL https://getsol.us/solus.gpg -o /etc/pki/rpm-gpg/solus.gpg
rpm --import /etc/pki/rpm-gpg/solus.gpg

# BTRFS config
cat > /etc/defines/btrfs-config << 'EOBTRFS'
COMPRESSION_ALGORITHM=zstd
COMPRESSION_LEVEL=3
SUBVOLUME_ROOT=@
SUBVOLUME_HOME=@home
SUBVOLUME_VAR=@var
SUBVOLUME_TMP=@tmp
SUBVOLUME_SNAP=@snapshots
AUTO_DEFRAG=yes
SSD_OPTIMIZATION=yes
EOBTRFS

sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# GNOME default settings via dconf
mkdir -p /etc/dconf/db/local.d
cat > /etc/dconf/db/local.d/00-solus-defaults << 'EODCONF'
[org/gnome/desktop/interface]
color-scheme='default'
cursor-theme='Adwaita'
font-antialiasing='rgba'
font-hinting='full'
font-name='Cantarell 11'
document-font-name='Cantarell 11'
monospace-font-name='JetBrains Mono 11'
gtk-theme='solus-gnome'
icon-theme='Adwaita'
show-battery-percentage=true
clock-show-weekday=true
clock-show-seconds=false

[org/gnome/desktop/wm/preferences]
button-layout='appmenu:minimize,maximize,close'
theme='solus-gnome'
titlebar-font='Cantarell Bold 11'

[org/gnome/desktop/peripherals/touchpad]
tap-to-click=true
two-finger-scrolling-enabled=true
natural-scroll=true
disable-while-typing=true

[org/gnome/shell]
favorite-apps=['firefox.desktop', 'org.gnome.Nautilus.desktop', 'org.gnome.TextEditor.desktop', 'org.gnome.Console.desktop', 'discord.desktop', 'steam.desktop', 'org.gnome.Software.desktop']
enabled-extensions=['appindicatorsupport@rgcjonas.gmail.com', 'blur-my-shell@aunetx', 'dash-to-dock@micayx.github.io', 'user-theme@gnome-shell-extensions.gcampax.github.com', 'caffeine@patapon.info', 'Vitals@CoreCoding.com', 'just-perfection-desktop@just-perfection', 'tiling-assistant@leleat', 'forge@jmmaranan.com']

[org/gnome/shell/extensions/dash-to-dock]
dock-position='BOTTOM'
autohide=false
dash-max-icon-size=32
show-apps-at-top=true
height-fraction=0.9
intellihide=true

[org/gnome/shell/extensions/blur-my-shell]
blur-brightness=0.6
blur-sigma=30
hue-length=90
colorize=true

[org/gnome/shell/extensions/just-perfection]
animation=true
app-menu-icon=false
clock-menu=true
search=true
theme=true
world-clock=true
weather=true
startup-status=0
window-demands-attention-focus=true

[org/gnome/desktop/session]
idle-delay=uint32 300

[org/gnome/desktop/screensaver]
lock-delay=uint32 60
lock-enabled=true

[org/gnome/desktop/background]
picture-uri='file:///usr/share/wallpapers/solus-default.jpg'
picture-uri-dark='file:///usr/share/wallpapers/solus-default-dark.jpg'
picture-options='zoom'
primary-color='#1a1a2e'
secondary-color='#16213e'

[org/gnome/desktop/sound]
theme-name='freedesktop'
event-sounds=true

[org/gnome/nautilus/preferences]
default-folder-viewer='list-view'
search-filter-time-type='last_modified'
search-view='list-view'
show-create-link=true
show-delete-permanently=true
show-image-thumbnails=true
thumbnail-limit=100

[org/gtk/settings/file-chooser]
sort-directories-first=true
location-mode='path-bar'
show-hidden=false

[org/gnome/desktop/peripherals/keyboard]
numlock-state=true

[org/gnome/system/location]
enabled=false

[org/gnome/desktop/privacy]
remove-old-temp-files=true
remove-old-trash-files=true
old-files-age=30
recent-files-max-age=30

[org/gnome/software]
download-updates=true
download-updates-notify=true
check-timestamp=0
EODCONF

cat > /etc/dconf/db/local.d/locks/solus-locks << 'EDLOCK'
/org/gnome/desktop/interface/color-scheme
/org/gnome/desktop/background/picture-uri
/org/gnome/desktop/screensaver/lock-enabled
/org/gnome/shell/enabled-extensions
EDLOCK

# Apply dconf
dconf update

# Shell config
cat > /etc/skel/.bashrc << 'EOBASHRC'
# Solus GNOME Bash Configuration
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi
alias ll='ls -lah'
alias la='ls -A'
alias cls='clear'
alias update='sudo dnf update --refresh'
alias grep='grep --color=auto'
export EDITOR=nano
export VISUAL=nano
export BROWSER=firefox
EOBASHRC

# Services
systemctl enable gdm.service
systemctl enable NetworkManager.service
systemctl enable bluetooth.service
systemctl enable sshd.service
systemctl enable cups.service
systemctl enable avahi-daemon.service
systemctl enable docker.service
systemctl enable containerd.service
systemctl enable podman.socket

# Gaming optimization
cat > /etc/gamemode.ini << 'EOGAME'
[general]
renice=10
softrealtime=auto
desiredgov=performance
[gpu]
apply_gpu_optimisations=accept-responsibility
amd_performance_level=high
[cpu]
apply_cpu_optimisations=yes
EOGAME

# Firstboot
mkdir -p /etc/solus/firstboot.d
cat > /usr/libexec/solus/firstboot.sh << 'EOFB'
#!/usr/bin/env bash
set -euo pipefail
for script in /etc/solus/firstboot.d/*.sh; do
    [ -x "$script" ] && "$script"
done
touch /var/lib/solus-firstboot-done
EOFB
chmod +x /usr/libexec/solus/firstboot.sh

cat > /etc/systemd/system/solus-firstboot.service << 'EOFBSVC'
[Unit]
Description=Solus First Boot Configuration
ConditionPathExists=!/var/lib/solus-firstboot-done
After=network.target graphical.target
[Service]
Type=oneshot
ExecStart=/usr/libexec/solus/firstboot.sh
RemainAfterExit=yes
[Install]
WantedBy=multi-user.target
EOFBSVC
systemctl enable solus-firstboot.service

rm -f /etc/machine-id
touch /etc/machine-id
dnf clean all
rm -f /etc/ssh/ssh_host_*
dd if=/dev/zero of=/zero.fill bs=1M 2>/dev/null || true
rm -f /zero.fill

echo "=== Solus GNOME Post-Install Complete ==="

%end

%addon com_redhat_kdump --disable --reserve-mb=0

%addon org_fedora_anaconda_users
root --lock
user --name=liveuser --groups=wheel,adm,systemd-journal,docker,libvirt,kvm,audio,video,storage --password=liveuser --iscrypted --lock
%end

# =============================================================================
# END OF KICKSTART
# =============================================================================
