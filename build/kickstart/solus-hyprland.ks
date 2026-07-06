# Solus Linux - Hyprland Edition
# Kickstart file for building reproducible Solus Hyprland ISO images
#
# Usage: livecd-creator --config solus-hyprland.ks --releasever=rawhide

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
bootloader --location=mbr --driveorder=vda --append="rhgb quiet splash nvidia_drm.modeset=1"
firewall --enabled --service=ssh
xconfig --startxonboot
network --bootproto=dhcp --device=link --hostname=solus-hyprland --activate

services --disabled=initial-setup,initial-setup-graphical,NetworkManager-wait-online
services --enabled=NetworkManager,bluetooth,sshd,avahi-daemon

# =============================================================================
# PACKAGE SECTION
# =============================================================================

%packages --instLangs=en_US.UTF-8 --excludeWeakdeps --nocore

# ---- Hyprland Desktop ----
@base-x
@base
@fonts
@hardware-support
@standard

hyprland
hyprland-devel
hyprpicker
hypridle
hyprlock
hyprpaper
hyprsunset
hyprshot
hyprswitch
hyprutils
hyprgraphics
hyprland-qtutils
xdg-desktop-portal-hyprland
xdg-desktop-portal-gtk
wayland-protocols
wayland-utils
wlroots
wlroots-devel
wl-clipboard
wlopm
wlsunset
wlogout
waybar
wofi
rofi-wayland
rofi-calc
rofi-emoji
dunst
libnotify
notification-daemon
mako
swaync
swaybg
swayidle
swayshot
swappy
grim
slurp
wf-recorder
qt5-wayland
qt6-wayland
qt6-qpa-hyprland
gtk3
gtk4
gtk-layer-shell
polkit-gnome
polkit-kde
network-manager-applet
blueman
blueberry
pavucontrol
pamixer
pipewire
pipewire-pulseaudio
pipewire-alsa
pipewire-jack
wireplumber
pulseaudio-utils

# ---- Terminal & Shell ----
foot
foot-terminfo
kitty
alacritty
wezterm
zsh
zsh-autosuggestions
zsh-syntax-highlighting
oh-my-zsh
starship
fzf
ripgrep
fd-find
bat
eza
zoxide
tmux
tmuxinator
neovim
neovim-plugins
neovim-python3
emacs
emacs-evil
vscode
vscodium

# ---- File Management ----
thunar
thunar-archive-plugin
thunar-media-tags-plugin
thunar-volman
thunar-shares-plugin
tumbler
gvfs
gvfs-afc
gvfs-gphoto2
gvfs-mtp
gvfs-smb
pcmanfm
ranger
lf
nnn
yazi
trash-cli

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
solus-grub-theme
solus-sddm-theme
solus-splash
solus-grub2

# ---- Solus Platform Meta-Packages ----
solus-safety
solus-essentials
solus-creator-platform
solus-gaming-platform

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

# ---- Development Tools ----
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
python3-pytest
nodejs
npm
rust
cargo
go
java-21-openjdk
java-21-openjdk-devel

# ---- Containers & Virtualization ----
docker-ce
docker-ce-cli
docker-compose
containerd
podman
podman-compose
buildah
kubectl
helm
minikube
ansible

# ---- AI & Machine Learning ----
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
solus-cudnn

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
vkd3d-devel
dxvk
vkbasalt
retroarch
mame
dosbox
prismlauncher

# ---- Content Creation ----
gimp
inkscape
blender
kdenlive
audacity
ffmpeg
ffmpeg-devel
obs-studio
mpv
vlc
imagemagick
libreoffice

# ---- Communication ----
discord
telegram-desktop
signal-desktop
element
thunderbird
firefox
chromium
brave-browser
qutebrowser

# ---- Utilities ----
keepassxc
nextcloud-client
syncthing
rsync
rclone
borgbackup
restic
vorta
timeshift
gparted
wireshark
tcpdump
nmap
openssh
openssh-server
p7zip
unrar
unzip
zip
htop
btop
fastfetch
neofetch
cava
cmus
ncspot
spotify

# ---- Hyprland-specific: Notifications/Bars ----
waybar
dunst
mako
swaync
eww
ags
ags-devel

# ---- Cleanup exclusions ----
-*plasma*
-*kde*
-*gnome*
-*xfce*
-*mate*
-*cinnamon*
-*budgie*
-*enlightenment*
-*lxde*
-*lxqt*
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

echo "=== Solus Hyprland Edition Post-Install ==="

# Create OS release
mkdir -p /etc/solus
cat > /etc/solus/os-release << 'EOSOLUS'
NAME="Solus Linux"
ID="solus"
PRETTY_NAME="Solus Linux Hyprland Edition"
VERSION="1.0"
HOME_URL="https://getsol.us"
SUPPORT_URL="https://discuss.getsol.us"
BUG_REPORT_URL="https://dev.getsol.us"
LOGO="solus"
ANSI_COLOR="0;36"
EOSOLUS

# Solus repositories
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

# BTRFS configuration
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

# SELinux enforcing
sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# Hyprland default config
mkdir -p /etc/skel/.config/hypr
cat > /etc/skel/.config/hypr/hyprland.conf << 'EOHYPR'
# Solus Hyprland Configuration
# Auto-generated for Solus Linux Hyprland Edition

monitor=,preferred,auto,1

exec-once = hyprpaper
exec-once = waybar
exec-once = dunst
exec-once = nm-applet --indicator
exec-once = blueman-applet
exec-once = /usr/libexec/polkit-gnome-authentication-agent-1

# Input
input {
    kb_layout = us
    kb_variant =
    kb_model =
    kb_options =
    kb_rules =
    follow_mouse = 1
    sensitivity = 0
    touchpad {
        natural_scroll = yes
        tap-to-click = yes
        drag_lock = yes
    }
}

# General
general {
    gaps_in = 5
    gaps_out = 10
    border_size = 2
    col.active_border = rgba(33ccffee) rgba(00ff88ee) 45deg
    col.inactive_border = rgba(595959aa)
    cursor_inactive_timeout = 3
    layout = dwindle
    no_border_on_floating = false
    resize_on_border = true
    hover_icon_on_border = true
}

# Decoration
decoration {
    rounding = 10
    active_opacity = 1.0
    inactive_opacity = 0.9
    fullscreen_opacity = 1.0
    drop_shadow = yes
    shadow_range = 4
    shadow_render_power = 3
    col.shadow = rgba(1a1a1aee)
    blur {
        enabled = yes
        size = 8
        passes = 3
        new_optimizations = on
        ignore_opacity = on
        xray = false
    }
}

# Animations
animations {
    enabled = yes
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = windowsOut, 1, 7, default, popin 80%
    animation = border, 1, 10, default
    animation = borderAngle, 1, 8, default
    animation = fade, 1, 7, default
    animation = workspaces, 1, 6, default, slide
}

# Layouts
dwindle {
    pseudotile = yes
    preserve_split = yes
    smart_split = true
    smart_resizing = true
}

master {
    mfact = 0.55
    smart_resizing = true
    always_show_master = true
}

# Gestures
gestures {
    workspace_swipe = on
    workspace_swipe_fingers = 3
    workspace_swipe_distance = 300
    workspace_swipe_invert = true
    workspace_swipe_min_finger_to_channel = 1
    workspace_swipe_cancel_ratio = 0.5
}

# Window rules
windowrule = float, ^(nm-connection-editor|blueman-manager|pavucontrol)$
windowrule = center, ^(nm-connection-editor|blueman-manager|pavucontrol)$
windowrule = float, title:^(Picture in picture)$
windowrule = opacity 0.9 0.9 override, ^(Alacritty|Kitty|foot)$

# Keybindings
$mainMod = SUPER

bind = $mainMod, Q, exec, kitty
bind = $mainMod, W, killactive
bind = $mainMod, E, exec, thunar
bind = $mainMod, F, fullscreen
bind = $mainMod, SPACE, exec, rofi -show drun
bind = $mainMod, D, togglefloating
bind = $mainMod, R, exec, rofi -show run
bind = $mainMod, P, pseudo
bind = $mainMod, S, togglesplit
bind = $mainMod, L, exec, hyprlock
bind = $mainMod, V, exec, wl-clipboard

bind = $mainMod SHIFT, Q, exit
bind = $mainMod SHIFT, E, exec, wlogout
bind = $mainMod SHIFT, R, exec, hyprctl reload
bind = $mainMod SHIFT, C, exec, hyprpicker -a

bind = $mainMod, left, movefocus, l
bind = $mainMod, right, movefocus, r
bind = $mainMod, up, movefocus, u
bind = $mainMod, down, movefocus, d

bind = $mainMod SHIFT, left, movewindow, l
bind = $mainMod SHIFT, right, movewindow, r
bind = $mainMod SHIFT, up, movewindow, u
bind = $mainMod SHIFT, down, movewindow, d

bind = $mainMod, 1, workspace, 1
bind = $mainMod, 2, workspace, 2
bind = $mainMod, 3, workspace, 3
bind = $mainMod, 4, workspace, 4
bind = $mainMod, 5, workspace, 5
bind = $mainMod, 6, workspace, 6
bind = $mainMod, 7, workspace, 7
bind = $mainMod, 8, workspace, 8
bind = $mainMod, 9, workspace, 9
bind = $mainMod, 0, workspace, 10

bind = $mainMod SHIFT, 1, movetoworkspace, 1
bind = $mainMod SHIFT, 2, movetoworkspace, 2
bind = $mainMod SHIFT, 3, movetoworkspace, 3
bind = $mainMod SHIFT, 4, movetoworkspace, 4
bind = $mainMod SHIFT, 5, movetoworkspace, 5
bind = $mainMod SHIFT, 6, movetoworkspace, 6
bind = $mainMod SHIFT, 7, movetoworkspace, 7
bind = $mainMod SHIFT, 8, movetoworkspace, 8
bind = $mainMod SHIFT, 9, movetoworkspace, 9
bind = $mainMod SHIFT, 0, movetoworkspace, 10

bind = $mainMod CTRL, left, workspace, e-1
bind = $mainMod CTRL, right, workspace, e+1

bind = , XF86AudioRaiseVolume, exec, pamixer -i 5
bind = , XF86AudioLowerVolume, exec, pamixer -d 5
bind = , XF86AudioMute, exec, pamixer -t
bind = , XF86MonBrightnessUp, exec, brightnessctl s +5%
bind = , XF86MonBrightnessDown, exec, brightnessctl s 5%-
bind = , XF86AudioPlay, exec, playerctl play-pause
bind = , XF86AudioNext, exec, playerctl next
bind = , XF86AudioPrev, exec, playerctl previous
bind = , XF86Search, exec, rofi -show drun

# Screenshots
bind = , Print, exec, hyprshot -m output
bind = SHIFT, Print, exec, hyprshot -m region
bind = CTRL, Print, exec, hyprshot -m window

# Scroll through existing workspaces with mainMod + scroll
bind = $mainMod, mouse_down, workspace, e+1
bind = $mainMod, mouse_up, workspace, e-1

# Move/resize with mainMod + LMB/RMB
bindm = $mainMod, mouse:272, movewindow
bindm = $mainMod, mouse:273, resizewindow
EOHYPR

# Waybar config
mkdir -p /etc/skel/.config/waybar
cat > /etc/skel/.config/waybar/style.css << 'EOCSS'
* {
    border: none;
    border-radius: 0;
    font-family: "JetBrains Mono", "Noto Sans", "Symbols Nerd Font";
    font-size: 13px;
    min-height: 0;
}

window#waybar {
    background: rgba(30, 30, 46, 0.85);
    color: #cdd6f4;
    transition-property: background-color;
    transition-duration: .5s;
}

window#waybar.hidden {
    opacity: 0.2;
}

#workspaces button {
    padding: 0 5px;
    background: transparent;
    color: #585b70;
    border-bottom: 2px solid transparent;
}

#workspaces button.focused {
    color: #cba6f7;
    border-bottom: 2px solid #cba6f7;
}

#workspaces button.urgent {
    background-color: #f38ba8;
    color: #1e1e2e;
}

#clock, #battery, #cpu, #memory, #disk, #temperature, #backlight, #network, #pulseaudio, #wireplumber, #custom-media, #tray, #mode, #idle_inhibitor, #mpd, #custom-power, #custom-updates {
    padding: 0 10px;
    color: #cdd6f4;
}

#battery.charging, #battery.plugged {
    color: #a6e3a1;
}

#battery.critical:not(.charging) {
    background-color: #f38ba8;
    color: #1e1e2e;
    animation-name: blink;
    animation-duration: 0.5s;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
    animation-direction: alternate;
}

@keyframes blink {
    to {
        background-color: #1e1e2e;
        color: #f38ba8;
    }
}

#pulseaudio.muted {
    color: #585b70;
}
EOCSS

cat > /etc/skel/.config/waybar/config.jsonc << 'EOWAYBAR'
{
    "layer": "top",
    "position": "top",
    "height": 30,
    "modules-left": ["hyprland/workspaces"],
    "modules-center": ["clock"],
    "modules-right": ["custom-updates", "pulseaudio", "network", "cpu", "memory", "battery", "tray", "custom-power"],
    "hyprland/workspaces": {
        "format": "{name}",
        "active-only": false,
        "all-outputs": true
    },
    "clock": {
        "format": "{:%I:%M %p  %a %b %d}",
        "format-alt": "{:%H:%M  %A %B %d %Y}",
        "tooltip-format": "<tt>{calendar}</tt>",
        "calendar": {
            "mode": "month",
            "format": {
                "months": "<span color='#cba6f7'><b>{}</b></span>",
                "days": "<span color='#cdd6f4'>{}</span>"
            }
        }
    },
    "cpu": {
        "format": "CPU {usage}%",
        "interval": 5
    },
    "memory": {
        "format": "RAM {}%",
        "interval": 5
    },
    "network": {
        "format-wifi": "{essid} ({signalStrength}%)",
        "format-ethernet": "Connected",
        "format-disconnected": "Disconnected",
        "tooltip-format": "{ifname} via {gwaddr}",
        "interval": 30
    },
    "pulseaudio": {
        "format": "{icon} {volume}%",
        "format-muted": "🔇 Muted",
        "format-icons": {
            "default": ["🔈", "🔉", "🔊"]
        },
        "scroll-step": 5,
        "on-click": "pavucontrol"
    },
    "battery": {
        "bat": "BAT0",
        "format": "{capacity}% {icon}",
        "format-icons": ["🔋", "🔋", "🔋", "🔋", "🔋"],
        "format-charging": "⚡{capacity}%",
        "format-plugged": "🔌 {capacity}%",
        "interval": 30
    },
    "custom-power": {
        "format": "⏻",
        "on-click": "wlogout",
        "tooltip": "Shutdown / Reboot / Lock"
    },
    "custom-updates": {
        "format": "{} ",
        "exec": "dnf check-update --quiet 2>/dev/null | wc -l",
        "interval": 3600
    },
    "tray": {
        "icon-size": 16,
        "spacing": 5
    }
}
EOWAYBAR

# Hyprpaper config
mkdir -p /etc/skel/.config/hypr
cat > /etc/skel/.config/hypr/hyprpaper.conf << 'EOHYPRPAPER'
preload = /usr/share/wallpapers/solus-default.jpg
wallpaper = ,/usr/share/wallpapers/solus-default.jpg
ipc = off
EOHYPRPAPER

# Hyprlock config
cat > /etc/skel/.config/hypr/hyprlock.conf << 'EOHYPRLOCK'
background {
    path = /usr/share/wallpapers/solus-default.jpg
    blur_size = 4
    blur_passes = 3
    brightness = 0.5
}

input-field {
    monitor =
    size = 300, 50
    outline_thickness = 2
    dots_size = 0.33
    dots_spacing = 0.15
    dots_center = true
    outer_color = rgba(33ccffee)
    inner_color = rgba(1e1e2ecc)
    font_color = rgba(cdd6f4ff)
    fade_on_empty = true
    placeholder_text = <i>Password...</i>
    hide_input = false
    position = 0, -80
    halign = center
    valign = center
}

label {
    monitor =
    text = $TIME
    font_size = 56
    color = rgba(cdd6f4ff)
    position = 0, 40
    halign = center
    valign = center
}

label {
    monitor =
    text = Welcome to Solus Hyprland
    font_size = 18
    color = rgba(a6adc8ff)
    position = 0, -10
    halign = center
    valign = center
}
EOHYPRLOCK

# Wlogout config
mkdir -p /etc/skel/.config/wlogout
cat > /etc/skel/.config/wlogout/layout << 'EOWLOGOUT'
{
    "label": "lock",
    "action": "hyprlock",
    "text": "🔒",
    "keybind": "l"
}
{
    "label": "shutdown",
    "action": "systemctl poweroff",
    "text": "⏻",
    "keybind": "s"
}
{
    "label": "reboot",
    "action": "systemctl reboot",
    "text": "🔄",
    "keybind": "r"
}
{
    "label": "logout",
    "action": "hyprctl dispatch exit",
    "text": "🚪",
    "keybind": "e"
}
{
    "label": "suspend",
    "action": "systemctl suspend",
    "text": "💤",
    "keybind": "u"
}
{
    "label": "hibernate",
    "action": "systemctl hibernate",
    "text": "🔋",
    "keybind": "h"
}
EOWLOGOUT

# ZSH default
cat > /etc/skel/.zshrc << 'EOZSHRC'
# Solus Hyprland ZSH Configuration
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git docker docker-compose kubectl helm ansible command-not-found zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# Starship prompt
eval "$(starship init zsh)"

# Aliases
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias cls='clear'
alias update='sudo dnf update --refresh'
alias grep='grep --color=auto'
alias diff='diff --color=auto'

# History
HISTSIZE=10000
SAVEHIST=10000
HISTFILE="$HOME/.zsh_history"
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS
setopt HIST_REDUCE_BLANCES

# FZF
eval "$(fzf --zsh)"
export FZF_DEFAULT_COMMAND='rg --files --hidden'
export FZF_DEFAULT_OPTS='--height 40% --layout=reverse --border'

# Starship config
mkdir -p ~/.config
cat > ~/.config/starship.toml << 'EOSTARSHIP'
add_newline = false
format = "$all"

[character]
success_symbol = "[➜](green)"
error_symbol = "[➜](red)"

[hostname]
ssh_only = true
format = "[@$hostname](bold yellow)"
disabled = false
EOSTARSHIP

# Environment
export EDITOR=nvim
export VISUAL=nvim
export BROWSER=firefox
EOZSHRC

# Services
systemctl enable NetworkManager.service
systemctl enable bluetooth.service
systemctl enable sshd.service
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

echo "=== Solus Hyprland Post-Install Complete ==="

%end

%addon com_redhat_kdump --disable --reserve-mb=0

%addon org_fedora_anaconda_users
root --lock
user --name=liveuser --groups=wheel,adm,systemd-journal,docker,libvirt,kvm,audio,video,storage --password=liveuser --iscrypted --lock
%end

# =============================================================================
# END OF KICKSTART
# =============================================================================
