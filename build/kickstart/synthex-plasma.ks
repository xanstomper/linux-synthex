# SynthOS Linux — Plasma Edition Kickstart
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
services --enabled=NetworkManager,sshd,chronyd,auditd,fstrim.timer,sddm,synthex-firstboot,synthex-system-daemon,synthex-safety.service,synthex-slim.service,synthex-boot-profile.service,synthex-oobe.service,synthex-control-center.service
services --disabled=lvm2-monitor,mdmonitor
bootloader --location=mbr --append="rhgb quiet splash rd.driver.blacklist=nouveau modprobe.blacklist=nouveau mitigations=auto"
network --bootproto=dhcp --device=link --activate
rootpw --lock
firstboot --reconfig
xconfig --startxonboot

# ── LIVE IMAGE ───────────────────────────────────────────────────────────────
# Livecd-creator builds a squashfs live root (overlayfs) mounted read-write on
# boot: the ISO is FULLY USABLE as a desktop before any installation. Contents
# are ephemeral; "Install Synthex" on the desktop (Calamares) writes to disk.
liveimg --name="Synthex-Plasma" --nombr

# Live session non-root user (also created by live-setup.sh at first boot).
# Auto-login + passwordless sudo wired in %post below.
user --name=liveuser --groups=wheel,audio,video,input,storage --password=liveuser

%packages
@core
@hardware-support
@fonts
@multimedia
@networkmanager-submodules

# KDE Plasma desktop
@kde-desktop
@kde-apps
@kde-media
@kde-office
plasma-desktop
plasma-workspace
plasma-nm
plasma-pa
plasma-discover
plasma-systemmonitor
plasma-firewall
plasma-disks
kscreen
kinfocenter
ksystemstats
kactivitymanagerd
kwallet5
kwalletmanager5
dolphin
konsole
kate
gwenview
okular
spectacle
ark
kcalc
kdeconnect
filelight
partitionmanager
elisa
kmail
kdepim-apps-libs
sddm
sddm-kcm
sddm-breeze
breeze-icon-theme
breeze-gtk

# Fonts
google-noto-sans-fonts
google-noto-emoji-fonts
google-noto-cjk-fonts
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
findutils
systemd
dbus
polkit
sudo
passwd
shadow-utils
NetworkManager
NetworkManager-wifi
NetworkManager-bluetooth
wpa_supplicant
iw
bluez
bluez-tools
pipewire
pipewire-pulseaudio
wireplumber
gstreamer1
gstreamer1-plugins-base
gstreamer1-plugins-good
gstreamer1-plugins-bad-free
gstreamer1-vaapi
ffmpeg-free
mesa-dri-drivers
mesa-vulkan-drivers
libva
libva-utils
vulkan-loader
vulkan-tools
wayland-protocols-devel
xorg-x11-server-Xwayland

# Flatpak support
flatpak
xdg-desktop-portal
xdg-desktop-portal-kde
xdg-user-dirs
xdg-utils

# Printing
cups
cups-pdf
system-config-printer

# Python runtime (for Calamares + SynthOS tools)
python3
python3-libs
python3-pip

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

# Additional utilities
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
bzip2
zip
unzip
gzip
file
which
lsof
strace
usbutils
pciutils
dmidecode
inxi
smartmontools
hdparm
lm_sensors
nvme-cli
%end

%post
#!/bin/bash
set -e

# ── Install SynthOS GPG key ──────────────────────────────────────────────────
mkdir -p /etc/pki/rpm-gpg/
cat > /etc/pki/rpm-gpg/RPM-GPG-KEY-synthex << 'GPGEOF'
# SynthOS Linux Signing Key — team@synthex-os.org
# Key will be available at: https://packages.getsynthex.org/RPM-GPG-KEY-synthex
GPGEOF

# ── Configure SynthOS repos ──────────────────────────────────────────────────
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

[synthex-nonfree]
name=SynthOS Linux - Non-Free
baseurl=https://packages.getsynthex.org/nonfree/x86_64/
enabled=0
gpgcheck=0
REPOEOF

# ── Enable Flatpak remotes ───────────────────────────────────────────────────
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flatpak-repo.flatpakrepo 2>/dev/null || true

# ── GRUB configuration ───────────────────────────────────────────────────────
cat > /etc/default/grub << 'GRUBEOF'
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=0
GRUB_HIDDEN_TIMEOUT=0
GRUB_DISTRIBUTOR="SynthOS Linux"
GRUB_CMDLINE_LINUX_DEFAULT="rhgb quiet splash mitigations=auto rd.driver.blacklist=nouveau modprobe.blacklist=nouveau"
GRUB_CMDLINE_LINUX="rd.luks=0 net.ifnames=0"
GRUB_DISABLE_RECOVERY="false"
GRUB_DISABLE_SUBMENU="false"
GRUB_DISABLE_OS_PROBER="false"
GRUB_GFXPAYLOAD_LINUX="keep"
GRUB_COLOR_NORMAL="white/black"
GRUB_COLOR_HIGHLIGHT="black/white"
GRUB_TERMINAL_OUTPUT="gfxterm"
GRUBEOF

# ── Plymouth theme ───────────────────────────────────────────────────────────
if [ -d /usr/share/plymouth/themes/synthex ]; then
    plymouth-set-default-theme synthex --rebuild-initrd 2>/dev/null || true
fi

# ── SDDM configuration ───────────────────────────────────────────────────────
mkdir -p /etc/sddm.conf.d/
cat > /etc/sddm.conf.d/synthex.conf << 'SDDMEOF'
[Theme]
Current=synthex-sddm-theme
CursorTheme=Bibata-Modern-Amber

[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_DISABLE_WINDOWDECORATION=1
InputMethod=

[Autologin]
Relogin=false

[X11]
ServerPath=/usr/bin/X
ServerArguments=-nolisten tcp -background none
SDDMEOF

# ── First-boot service ───────────────────────────────────────────────────────
if [ -f /usr/lib/systemd/system/synthex-firstboot.service ]; then
    systemctl enable synthex-firstboot.service
fi

# Enable SynthOS platform services
for s in synthex-safety.service synthex-slim.service synthex-boot-profile.service \
         synthex-oobe.service synthex-control-center.service; do
    if [ -f /usr/lib/systemd/system/$s ]; then
        systemctl enable $s 2>/dev/null || true
    fi
done

# Live USB session: SDDM auto-login for liveuser only (never on installed system)
mkdir -p /etc/sddm.conf.d/
cat > /etc/sddm.conf.d/autologin.conf << 'AUTOEOF'
[Autologin]
User=liveuser
Session=plasma
AUTOEOF

# Installer launcher on the live user's desktop
if id liveuser >/dev/null 2>&1; then
    LIVEDesk="/home/liveuser/Desktop"
    mkdir -p "$LIVEDesk"
    if [ -f /usr/share/applications/synthex-installer.desktop ]; then
        cp /usr/share/applications/synthex-installer.desktop "$LIVEDesk/" 2>/dev/null || true
        chmod +x "$LIVEDesk/synthex-installer.desktop" 2>/dev/null || true
    fi
fi

# Polkit rule: live session runs installer without root prompt
mkdir -p /etc/polkit-1/rules.d/
cat > /etc/polkit-1/rules.d/49-synthex-live-installer.rules << 'POLKEOF'
// SynthOS — allow liveuser to run the installer on the live USB only.
polkit.addRule(function(action, subject) {
    if (action.id === "org.freedesktop.policykit.exec" &&
        subject.user === "liveuser") {
        return polkit.Result.YES;
    }
});
POLKEOF

# Passwordless sudo for live session (live USB convenience)
mkdir -p /etc/sudoers.d/
echo "liveuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/00-synthex-liveuser
chmod 440 /etc/sudoers.d/00-synthex-liveuser

# ── Locale & keyboard ────────────────────────────────────────────────────────
localectl set-locale LANG=en_US.UTF-8 2>/dev/null || true
localectl set-x11-keymap us 2>/dev/null || true

# ── Enable critical services ─────────────────────────────────────────────────
systemctl enable NetworkManager
systemctl enable sddm
systemctl enable chronyd
systemctl enable fstrim.timer
systemctl enable auditd

# ── Disable unnecessary services ─────────────────────────────────────────────
systemctl disable lvm2-monitor 2>/dev/null || true
systemctl disable mdmonitor 2>/dev/null || true

# ── Configure DNF ────────────────────────────────────────────────────────────
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

# ── SynthOS version marker ───────────────────────────────────────────────────
mkdir -p /etc/synthex
cat > /etc/synthex/synthex-release << 'RELEOF'
NAME="SynthOS Linux"
VERSION="2026.10"
CODENAME="Ignition"
EDITION="Plasma"
ID="synthex"
ID_LIKE="fedora"
VERSION_ID="42"
PRETTY_NAME="SynthOS Linux 2026.10 (Plasma)"
HOME_URL="https://getsynthex.org"
SUPPORT_URL="https://discuss.getsynthex.org"
BUG_REPORT_URL="https://github.com/synthex-linux/issues"
BUILD_DATE="@BUILD_DATE@"
RELEOF

# ── Post-install hook ─────────────────────────────────────────────────────────
if [ -f /usr/share/synthex/scripts/post-install.sh ]; then
    bash /usr/share/synthex/scripts/post-install.sh --edition=plasma --livecd 2>/dev/null || true
fi

# ── Privacy policy (no-telemetry guarantee) ─────────────────────────────
cat > /etc/synthex/privacy.conf << 'PRIVEOF'
# SynthOS global privacy policy — NO telemetry, ever.
weather_fetch = false
integration_engine = false
telemetry = false
PRIVEOF
chmod 644 /etc/synthex/privacy.conf

echo "SynthOS Plasma Edition post-install complete."

# ── Enable live session setup (runs live-only via ConditionPathExists) ─────
# The squashfs live root mounts /run/synthex-live so autologin + installer
# launcher fire on the live USB/ISO. Skipped automatically on installed systems.
mkdir -p /run/synthex-live
systemctl enable synthex-live-setup.service 2>/dev/null || true
%end
