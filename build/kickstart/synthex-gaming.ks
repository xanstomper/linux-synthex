# =============================================================================
# SynthOS Gaming Edition Kickstart
# Builds a KDE Plasma ISO pre-loaded with the full gaming stack
# =============================================================================

# Language & locale
lang en_US.UTF-8
keyboard --vckeymap=us --xlayouts=us
timezone America/New_York --utc

# Network
network --bootproto=dhcp --device=link --activate
network --hostname=synthos-gaming

# Root & live user
rootpw --iscrypted --lock *
user --name=liveuser --groups=wheel,users,audio,video,storage,games \
     --password=liveuser --iscrypted --lock

# Boot & storage
bootloader --location=mbr --driveorder=sda
zerombr
clearpart --all --initlabel
autopart --type=btrfs

# Services
services --enabled=NetworkManager,sddm,bluetooth,fstrim.timer,gamemode,synthex-firstboot
services --disabled=initial-setup,firewalld

# SELinux (permissive in gaming edition for max compatibility)
selinux --permissive

# Firewall — open only Steam + Sunshine ports
firewall --enabled --port=27036:tcp,27037:tcp,47984:tcp,47989:tcp,47990:tcp,48010:tcp

# Display manager
displaymanager --enable=sddm

# =============================================================================
# Repositories
# =============================================================================

repo --name=fedora        --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-rawhide&arch=x86_64
repo --name=updates       --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-rawhide&arch=x86_64
repo --name=synthex       --baseurl=https://packages.synthex-os.org/unstable/x86_64/ --gpgcheck=0
repo --name=synthex-nonfree --baseurl=https://packages.synthex-os.org/nonfree/x86_64/ --gpgcheck=0
repo --name=rpmfusion-free --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=free-rawhide&arch=x86_64
repo --name=rpmfusion-nonfree --mirrorlist=https://mirrors.rpmfusion.org/mirrorlist?repo=nonfree-rawhide&arch=x86_64
repo --name=copr-synthex  --baseurl=https://copr-be.cloud.fedorainfrastructure.org/results/synthex-linux/packages/rawhide-x86_64/

# =============================================================================
# Packages
# =============================================================================

%packages

# Core system
synthex-core
synthex-base

# Plymouth
plymouth
plymouth-theme-synthex
plymouth-plugin-script
# Base system
@core
@standard
@hardware-support

# KDE Plasma desktop
@kde-desktop
@kde-apps
plasma-workspace
plasma-desktop
plasma-nm
plasma-pa
plasma-systemmonitor
kscreen
kpipewire
spectacle
kdeconnect
kdialog
filelight

# SynthOS base
synthex-desktop-gaming
synthex-branding
synthex-system-daemon
synthex-hwdaemon
synthex-kernel
synthex-oobe
synthex-firstboot
synthex-control-center
synthex-software-center
synthex-update-manager
synthex-gaming-mode
synthex-gpu-setupd
synthex-gaming-center

# Themes
sddm-theme-synthex
plymouth-theme-synthex
synthex-grub-theme
synthex-cursors
synthex-firmware

# Full gaming stack
%include synthex-gaming-packages.ksinc

# Development tools (lite — for modding/scripting)
git
python3
python3-pip
nodejs
gcc
make

# Terminal & shell
konsole
zsh
bash-completion
tmux
htop
btop
neofetch
fastfetch

# File management
dolphin
ark
p7zip
unrar

# Additional utilities
flatpak
discover
xdg-desktop-portal
xdg-desktop-portal-kde
spectacle
ksnip

# Fonts
google-noto-fonts-common
google-noto-sans-fonts
google-noto-emoji-fonts
jetbrains-mono-fonts

# Plymouth
plymouth
plymouth-plugin-script
plymouth-scripts

# Dracut
dracut
dracut-config-rescue

# Excluded (not needed in gaming edition)
-gnome-shell
-gnome-session
-gdm
-evolution
-rhythmbox
-totem
-cheese
-libreoffice*

%end

# =============================================================================
# Pre-install
# =============================================================================

%pre
#!/bin/bash
# Detect GPU vendor early for driver pre-staging
GPU_VENDOR="unknown"
if lspci 2>/dev/null | grep -qi "NVIDIA"; then
    GPU_VENDOR="nvidia"
elif lspci 2>/dev/null | grep -qi "AMD\|ATI"; then
    GPU_VENDOR="amd"
elif lspci 2>/dev/null | grep -qi "Intel"; then
    GPU_VENDOR="intel"
fi
echo "GPU_VENDOR=$GPU_VENDOR" > /tmp/synthex-hwdetect.env
echo "EDITION=gaming" >> /tmp/synthex-hwdetect.env
%end

# =============================================================================
# Post-install
# =============================================================================

%post --nochroot
#!/bin/bash
echo "=== SynthOS Gaming Edition Post-Install (nochroot) ==="

# Copy hardware detection result into chroot
[ -f /tmp/synthex-hwdetect.env ] && \
    cp /tmp/synthex-hwdetect.env /mnt/sysimage/var/lib/synthex/hwdetect.env

%end

%post
#!/bin/bash
set -euo pipefail
LOG=/var/log/synthex-gaming-post.log
exec > >(tee -a "$LOG") 2>&1

echo "=== SynthOS Gaming Edition Post-Install (chroot) ==="
mkdir -p /var/lib/synthex

# ── Write gaming install profile ──────────────────────────────────────────────
cat > /var/lib/synthex/install-profile.json << 'PROFILE'
{
  "edition":  "gaming",
  "profile":  "gaming",
  "version":  "2026.10",
  "variant":  "v3",
  "features": ["gaming", "steam", "proton", "mangohud", "gamescope", "bore-kernel"]
}
PROFILE

# ── Gaming-specific kernel parameters ─────────────────────────────────────────
if [ -f /etc/default/grub ]; then
    sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash mitigations=off threadirqs preempt=full"/' \
        /etc/default/grub
fi

# ── Enable gaming services ────────────────────────────────────────────────────
systemctl enable gamemode.service   &>/dev/null || true
systemctl enable irqbalance.service &>/dev/null || true
systemctl enable bluetooth.service  &>/dev/null || true

# ── Disable mitigations (user choice — warning in OOBE) ───────────────────────
# Already set in GRUB above; also set in sysctl
cat > /etc/sysctl.d/99-synthex-gaming.conf << 'SYSCTL'
# SynthOS Gaming Tweaks
vm.swappiness = 1
kernel.nmi_watchdog = 0
net.core.netdev_max_backlog = 16384
kernel.sched_autogroup_enabled = 1
SYSCTL

# ── Udev rules for controllers ────────────────────────────────────────────────
cat > /etc/udev/rules.d/70-synthex-gaming-devices.rules << 'UDEV'
# Steam controllers
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", MODE="0660", TAG+="uaccess"
# PS5 DualSense
SUBSYSTEM=="hidraw", KERNEL=="hidraw*", ATTRS{idVendor}=="054c", ATTRS{idProduct}=="0ce6", MODE="0660", TAG+="uaccess"
# Xbox controllers
SUBSYSTEM=="input", ATTRS{idVendor}=="045e", MODE="0660", TAG+="uaccess"
# Nintendo Switch Pro
SUBSYSTEM=="hid", ATTRS{idVendor}=="057e", ATTRS{idProduct}=="2009", MODE="0660", TAG+="uaccess"
UDEV

# ── Gamescope session for Big Picture mode ────────────────────────────────────
cat > /usr/share/wayland-sessions/gamescope-steam.desktop << 'GSDTP'
[Desktop Entry]
Name=Gaming Mode (Gamescope + Steam)
Comment=Full-screen Steam Big Picture via Gamescope
Exec=/usr/bin/gamescope -e -f -W 1920 -H 1080 -- steam -gamepadui
Type=Application
GSDTP

# ── Plymouth gaming theme (same as standard, gaming variant) ──────────────────
if command -v plymouth-set-default-theme &>/dev/null; then
    plymouth-set-default-theme synthex &>/dev/null || true
fi

# ── SDDM gaming config ────────────────────────────────────────────────────────
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/synthex-gaming.conf << 'SDDMCFG'
[Theme]
Current=synthex

[Autologin]
Session=gamescope-steam.desktop
Relogin=false

[General]
DisplayServer=wayland
GreeterEnvironment=QT_WAYLAND_SHELL_INTEGRATION=layer-shell
SDDMCFG

# ── Machine-ID reset (regenerated on first boot) ──────────────────────────────
rm -f /etc/machine-id && touch /etc/machine-id
rm -f /etc/ssh/ssh_host_*

# ── Final cleanup ─────────────────────────────────────────────────────────────
dnf clean all &>/dev/null || true

echo "=== SynthOS Gaming Edition Post-Install Complete ==="
%end

# =============================================================================
# END OF GAMING KICKSTART
# =============================================================================
