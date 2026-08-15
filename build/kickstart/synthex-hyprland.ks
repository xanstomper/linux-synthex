# SynthOS Linux — Hyprland Edition Kickstart
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
services --enabled=NetworkManager,sshd,chronyd,auditd,fstrim.timer,synthex-firstboot,synthex-system-daemon
services --disabled=lvm2-monitor,mdmonitor
bootloader --location=mbr --append="rhgb quiet splash mitigations=auto"
network --bootproto=dhcp --device=link --activate
rootpw --lock
firstboot --reconfig

# ── LIVE IMAGE ─────────────────────────────────────────
# Live squashfs root: usable before installing.
liveimg --name="Synthex-Hyprland" --nombr

# Live session non-root user (created by live-setup.sh).
user --name=liveuser --groups=wheel,audio,video,input,storage --password=liveuser

%packages
@core
@hardware-support
@fonts
@multimedia
@networkmanager-submodules

# Hyprland Wayland compositor
hyprland
hyprpaper
hyprlock
hypridle
xdg-desktop-portal-hyprland

# Status bar
waybar

# App launcher
wofi
rofi-wayland

# Notifications
dunst
libnotify

# Terminal
foot
kitty

# File manager
thunar
thunar-volman
thunar-archive-plugin
gvfs
gvfs-mtp

# File viewer / image
imv
mpv

# Screen capture
grim
slurp
wl-clipboard

# Display manager
greetd
greetd-tuigreet

# Audio
pipewire
pipewire-pulseaudio
pipewire-jack-audio-connection-kit
wireplumber
pavucontrol
pamixer

# Network
NetworkManager
NetworkManager-wifi
NetworkManager-tui
network-manager-applet
wpa_supplicant
iwd

# Bluetooth
bluez
blueman

# Fonts
google-noto-sans-fonts
google-noto-emoji-fonts
ttf-fira-code
fira-code-fonts
fontawesome-fonts

# GTK theming
gtk3
gtk4
adwaita-gtk2-theme
lxappearance

# System tools
polkit
polkit-gnome
udisks2
upower
xdg-user-dirs
xdg-utils
flatpak
xdg-desktop-portal
brightnessctl
playerctl
mako

# Core system
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
xorg-x11-server-Xwayland
mesa-dri-drivers
mesa-vulkan-drivers
libva
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
smartmontools
pciutils
usbutils

# SynthOS Nova shell & terminal stack (real packages)
fish
starship
zoxide
eza
bat
ripgrep
wlsunset
swayidle
wl-clipboard
cliphist
%end

%post
#!/bin/bash
set -e

# ── SynthOS Nova shell & terminal configs → /etc/skel (new users) ─────
SRCTOP=/usr/share/synthex
install_shell_configs() {
    local DSTROOT=$1
    mkdir -p "$DSTROOT/.config/kitty" \
             "$DSTROOT/.config/fish/conf.d" \
             "$DSTROOT/.config/starship" \
             "$DSTROOT/.config/fastfetch" \
             "$DSTROOT/.config/wofi" \
             "$DSTROOT/.config/mako"
    [ -f $SRCTOP/terminal/kitty/kitty.conf ] && cp $SRCTOP/terminal/kitty/kitty.conf "$DSTROOT/.config/kitty/"
    [ -f $SRCTOP/terminal/kitty/nova.conf ] && cp $SRCTOP/terminal/kitty/nova.conf "$DSTROOT/.config/kitty/"
    [ -f $SRCTOP/terminal/fish/30-synthex.fish ] && cp $SRCTOP/terminal/fish/30-synthex.fish "$DSTROOT/.config/fish/conf.d/"
    [ -f $SRCTOP/terminal/starship/starship.toml ] && cp $SRCTOP/terminal/starship/starship.toml "$DSTROOT/.config/starship/"
    [ -f $SRCTOP/terminal/fastfetch/config.jsonc ] && cp $SRCTOP/terminal/fastfetch/config.jsonc "$DSTROOT/.config/fastfetch/"
    [ -f $SRCTOP/hyprland/wofi-style.css ] && cp $SRCTOP/hyprland/wofi-style.css "$DSTROOT/.config/wofi/style.css"
    [ -f $SRCTOP/hyprland/wofi-config ] && cp $SRCTOP/hyprland/wofi-config "$DSTROOT/.config/wofi/config"
    [ -f $SRCTOP/hyprland/mako.conf ] && cp $SRCTOP/hyprland/mako.conf "$DSTROOT/.config/mako/config"
}
# Copy for new users; also apply for the live session user if present
install_shell_configs /etc/skel
id liveuser >/dev/null 2>&1 && install_shell_configs /home/liveuser || true

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

# greetd config for Hyprland auto-start
mkdir -p /etc/greetd
cat > /etc/greetd/config.toml << 'GREETEOF'
[terminal]
vt = 1

[default_session]
command = "tuigreet --time --greeting 'Welcome to SynthOS' --cmd Hyprland"
user = "greeter"
GREETEOF

# Hyprland default config skeleton (users can override)
mkdir -p /etc/skel/.config/hypr
cat > /etc/skel/.config/hypr/hyprland.conf << 'HYPREOF'
# SynthOS Hyprland Default Config
monitor=,preferred,auto,1

exec-once = waybar
exec-once = hyprpaper
exec-once = dunst
exec-once = synthex-system-daemon

$terminal = foot
$menu = wofi --show drun

input {
    kb_layout = us
    follow_mouse = 1
    touchpad { natural_scroll = true }
}

general {
    gaps_in = 5
    gaps_out = 10
    border_size = 2
    col.active_border = rgba(FFB300ff) rgba(FF8C00ff) 45deg
    col.inactive_border = rgba(1a1a2eff)
    layout = dwindle
}

decoration {
    rounding = 10
    blur { enabled = true; size = 6; passes = 2 }
    drop_shadow = true
    shadow_range = 8
    col.shadow = rgba(00000088)
}

animations {
    enabled = true
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = windowsOut, 1, 7, default, popin 80%
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default
}

dwindle { pseudotile = true; preserve_split = true }

$mainMod = SUPER
bind = $mainMod, Return, exec, $terminal
bind = $mainMod, D, exec, $menu
bind = $mainMod, Q, killactive,
bind = $mainMod SHIFT, E, exit,
bind = $mainMod, F, fullscreen,
bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4
bind = $mainMod, 5, workspace, 5
bindm = $mainMod, mouse:272, movewindow
bindm = $mainMod, mouse:273, resizewindow
HYPREOF

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
EDITION="Hyprland"
ID="synthex"
ID_LIKE="fedora"
PRETTY_NAME="SynthOS Linux 2026.10 (Hyprland)"
HOME_URL="https://getsynthex.org"
RELEOF

systemctl enable NetworkManager greetd chronyd auditd fstrim.timer
systemctl disable lvm2-monitor mdmonitor 2>/dev/null || true
[ -f /usr/lib/systemd/system/synthex-firstboot.service ] && systemctl enable synthex-firstboot.service || true

useradd -r -d /var/lib/greeter -M greeter 2>/dev/null || true

echo "SynthOS Hyprland Edition post-install complete."

# ── Enable live session setup (live-only via ConditionPathExists) ──
mkdir -p /etc/synthex && touch /etc/synthex/live-mode
systemctl enable synthex-live-setup.service 2>/dev/null || true
%end
