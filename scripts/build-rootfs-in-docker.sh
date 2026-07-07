#!/usr/bin/env bash
# Rootfs builder — runs INSIDE the Docker container
# Creates a bootable Synthex root filesystem tarball
set -euo pipefail
ROOTFS="/tmp/synthex-rootfs"
OUTPUT="/output/synthex-rootfs-$(date +%Y%m%d).tar.gz"

echo "📦 Creating Synthex rootfs at ${ROOTFS}..."

# Clean and create
rm -rf "$ROOTFS"
mkdir -p "$ROOTFS"

# Install base system
echo "  Installing base system..."
dnf install --installroot="$ROOTFS" --releasever=42 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    systemd bash coreutils dnf util-linux \
    passwd shadow-utils sudo \
    glibc-langpack-en \
    kernel kernel-core kernel-modules \
    btrfs-progs snapper \
    firewalld selinux-policy-targeted \
    NetworkManager \
    pipewire pipewire-pulseaudio wireplumber \
    flatpak fwupd \
    firefox \
    libreoffice-writer libreoffice-calc libreoffice-impress \
    gimp \
    git \
    elisa \
    kdenlive \
    PackageKit-Qt6 \
    thunderbird \
    haruna \
    transmission \
    filelight \
    ksystemlog \
    gstreamer1-plugins-good gstreamer1-plugins-bad-free gstreamer1-plugins-ugly-free \
    kmahjongg kmines kpat \
    khelpcenter \
    krfb krdc \
    ktorrent \
    2>&1 | tail -5

# Install KDE Plasma
echo "  Installing KDE Plasma (this may take a while)..."
dnf install --installroot="$ROOTFS" --releasever=42 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    plasma-desktop sddm kwin \
    dolphin konsole kate gwenview spectacle \
    plasma-nm plasma-pa powerdevil \
    ffmpegthumbs \
    2>&1 | tail -5
# Add RPM Fusion repos (for NVIDIA, Steam, codecs)
echo "  Adding RPM Fusion repositories..."
for repo in free nonfree; do
    rpm -q rpmfusion-${repo}-release 2>/dev/null || \
    dnf install --installroot="$ROOTFS" --releasever=42 --use-host-config -y \
        https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-42.noarch.rpm \
        https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-42.noarch.rpm \
        2>/dev/null || true
done

# Install gaming / NVIDIA / codecs
echo "  Installing gaming stack and drivers..."
dnf install --installroot="$ROOTFS" --releasever=42 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    steam \
    mangohud gamescope gamemode \
    obs-studio \
    akmod-nvidia \
    ffmpeg-libs \
    glibc-all-langpacks \
    linux-firmware \
    kernel-modules-extra \
    intel-media-driver \
    freetype-freeworld \
    lutris \
    wine wine-core wine-wow wine-twain \
    winetricks \
    steam-devices \
    sunshine \
    privoxy \
    input-remapper \
    im-chooser \
    qemu qemu-kvm libvirt virt-manager \
    podman buildah skopeo \
    rust cargo golang nodejs java-21-openjdk \
    2>&1 | tail -5

# Synthex platform meta-packages (safety/essentials/creator/gaming)
echo "  Installing Synthex platform meta-packages..."
dnf install --installroot="$ROOTFS" --releasever=42 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    synthex-safety synthex-essentials synthex-creator-platform synthex-gaming-platform \
    2>/dev/null || true

# Enable Synthex platform services in the rootfs
echo "  Enabling Synthex platform services..."
for svc in synthex-safety synthex-slim synthex-boot-profile synthex-oobe synthex-control-center \
           synthex-workspace synthex-desktopd synthex-hwdaemon synthex-gpu-setupd synthex-stored; do
    chroot "$ROOTFS" systemctl enable "$svc.service" 2>/dev/null || true
done

# Development + creator tools
echo "  Installing development and creator tools..."
dnf install --installroot="$ROOTFS" --releasever=42 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    cmake ninja-build gdb valgrind strace ltrace \
    htop btop neofetch fastfetch \
    fish zsh tmux \
    vim nano emacs \
    krita inkscape blender \
    discord 2>/dev/null || true
    proton-ge-custom 2>/dev/null || true
    heroic-games-launcher 2>/dev/null || true
    2>&1 | tail -5

# Download Proton GE manually
echo "  Downloading Proton GE..."
cd "$ROOTFS/tmp"
PROTON_GE_URL=$(curl -s https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest | grep "browser_download_url" | grep ".tar.gz" | cut -d'"' -f4 | head -1)
if [ -n "$PROTON_GE_URL" ]; then
    curl -L -o proton-ge.tar.gz "$PROTON_GE_URL" 2>/dev/null || true
    mkdir -p "$ROOTFS/usr/share/steam/compatibilitytools.d"
    tar -xzf proton-ge.tar.gz -C "$ROOTFS/usr/share/steam/compatibilitytools.d/" 2>/dev/null || true
    rm -f proton-ge.tar.gz
    echo "  Proton GE downloaded"
fi

# Install extra Flatpak runtimes
echo "  Installing extra Flatpak runtimes..."
if command -v flatpak &>/dev/null; then
    flatpak --system install -y flathub org.freedesktop.Platform//22.08 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform//24.08 2>/dev/null || true
    flatpak --system install -y flathub org.kde.Platform//6.8 2>/dev/null || true
    flatpak --system install -y flathub org.gnome.Platform//47 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform.GL32.default//24.08 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform.VAAPI.Intel 2>/dev/null || true
    flatpak --system install -y flathub net.lutris.Lutris 2>/dev/null || true
    flatpak --system install -y flathub com.heroicgameslauncher.hgl 2>/dev/null || true
    flatpak --system install -y flathub org.prismlauncher.PrismLauncher 2>/dev/null || true
fi

# Pre-install Flatpak runtime
echo "  Installing Flatpak runtime..."
if command -v flatpak &>/dev/null; then
    flatpak --system remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform//24.08 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform.GL.default//24.08 2>/dev/null || true
    flatpak --system install -y flathub org.freedesktop.Platform.GL32.default//24.08 2>/dev/null || true
fi


# Configure the system
echo "  Configuring system..."
chroot "$ROOTFS" /bin/bash << 'CHROOT'
    # Set root password
    echo "root:synthex" | chpasswd
    
    # Create required groups
    for grp in games libvirt docker kvm; do
        getent group "$grp" >/dev/null 2>&1 || groupadd "$grp" 2>/dev/null || true
    done

    # Create user
    useradd -m -G wheel,audio,video,storage,games,input,libvirt,kvm synthex
    echo "synthex:synthex" | chpasswd
    
    # Enable services
    systemctl enable sddm
    systemctl enable NetworkManager
    systemctl enable firewalld
    systemctl enable fwupd
    systemctl enable bluetooth
    
    # Configure BTRFS snapshots
    snapper -c root create-config / 2>/dev/null || true
    
    # Set locale
    echo "LANG=en_US.UTF-8" > /etc/locale.conf
    
    # Hostname
    echo "synthex" > /etc/hostname
    
    # ─── Apply Synthex KDE Plasma Configuration ───
    mkdir -p /home/synthex/.config /root/.config
    
    # Set Plasma color scheme to SynthexMint
    cat > /home/synthex/.config/kdeglobals << 'KDE'
[General]
ColorScheme=SynthexMint
font=Noto Sans,10,-1,5,50,0,0,0,0,0
fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0

[Icons]
Theme=Mint-Y

[KDE]
ColorScheme=SynthexMint
KDE

    # Set KWin compositor settings
    cat > /home/synthex/.config/kwinrc << 'KWIN'
[Compositing]
Backend=OpenGL
Enabled=true
LatencyPolicy=1
MaxFPS=60
RefreshRate=60

[Desktops]
Number=4
Rows=2

[org.kde.kdecoration2]
library=org.kde.kwin.aurorae
theme=synthex-mint
KWIN

    # Default applications (XDG MIME)
    mkdir -p /home/synthex/.config
    cat > /home/synthex/.config/mimeapps.list << 'MIME'
[Default Applications]
text/html=firefox.desktop
x-scheme-handler/http=firefox.desktop
x-scheme-handler/https=firefox.desktop
inode/directory=dolphin.desktop
application/x-terminal=konsole.desktop
text/plain=kate.desktop
image/jpeg=gwenview.desktop
image/png=gwenview.desktop
audio/mpeg=elisa.desktop
video/mp4=kdenlive.desktop
application/pdf=okular.desktop
application/zip=ark.desktop
MIME

    # Apply wallpaper
    mkdir -p /home/synthex/.config
    cat > /home/synthex/.config/plasma-org.kde.plasma.desktop-appletsrc << 'PLASMA'
[Containments][1][General]
wallpaper=org.kde.image
lastSelectedImage=/usr/share/wallpapers/synthex/synthex-dark-4k.svg
image=/usr/share/wallpapers/synthex/synthex-dark-4k.svg

[Containments][2][General]
wallpaper=org.kde.image
lastSelectedImage=/usr/share/wallpapers/synthex/synthex-dark-4k.svg
PLASMA

    # Configure SDDM theme
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/synthex.conf << 'SDDM'
[Theme]
Current=synthex-sddm-theme
CursorTheme=Bibata-Modern-Classic
Font=Noto Sans,10

[General]
Numlock=on

[Autologin]
User=synthex
Session=plasma.desktop
Relogin=false
SDDM

    # Set Plymouth theme
    if [ -f /usr/sbin/plymouth-set-default-theme ]; then
        plymouth-set-default-theme synthex 2>/dev/null || true
    fi

    # Own configs by user
    chown -R synthex:synthex /home/synthex/.config 2>/dev/null || true

    # Copy configs to skel for new users
    cp -r /home/synthex/.config /etc/skel/ 2>/dev/null || true
    
    # Set kernel cmdline defaults
    if [ -f /etc/default/grub ]; then
        sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="quiet splash rd.luks=1 selinux=1 enforcing=1 audit=1"/' /etc/default/grub 2>/dev/null || true
        sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet"/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/' /etc/default/grub 2>/dev/null || true
        echo 'GRUB_THEME="/boot/grub2/themes/synthex/theme.txt"' >> /etc/default/grub 2>/dev/null || true
    fi
CHROOT

# Copy Synthex branding and configs
echo "  Applying Synthex branding and features..."
if [ -d "/synthex/branding" ]; then
    # Wallpapers
    mkdir -p "$ROOTFS/usr/share/wallpapers/synthex"
    cp -r /synthex/branding/wallpaper/* "$ROOTFS/usr/share/wallpapers/synthex/" 2>/dev/null || true
    
    # GRUB theme
    if [ -d "/synthex/branding/grub" ]; then
        mkdir -p "$ROOTFS/boot/grub2/themes/synthex"
        cp -r /synthex/branding/grub/* "$ROOTFS/boot/grub2/themes/synthex/" 2>/dev/null || true
    fi
    
    # Plymouth theme
    if [ -d "/synthex/branding/plymouth" ]; then
        mkdir -p "$ROOTFS/usr/share/plymouth/themes/synthex"
        cp -r /synthex/branding/plymouth/* "$ROOTFS/usr/share/plymouth/themes/synthex/" 2>/dev/null || true
    fi
    
    # SDDM theme
    if [ -d "/synthex/desktop/sddm" ]; then
        mkdir -p "$ROOTFS/etc/sddm.conf.d"
        cp /synthex/desktop/sddm/sddm.conf "$ROOTFS/etc/sddm.conf.d/" 2>/dev/null || true
    fi
    
    # Font config
    if [ -f "/synthex/desktop/fonts/local.conf" ]; then
        mkdir -p "$ROOTFS/etc/fonts"
        cp /synthex/desktop/fonts/local.conf "$ROOTFS/etc/fonts/" 2>/dev/null || true
    fi
    
    # Bluetooth config
    if [ -f "/synthex/desktop/bluetooth/main.conf" ]; then
        mkdir -p "$ROOTFS/etc/bluetooth"
        cp /synthex/desktop/bluetooth/main.conf "$ROOTFS/etc/bluetooth/" 2>/dev/null || true
    fi
    
    # Mint-style layout
    if [ -f "/synthex/layouts/mint.json" ]; then
        mkdir -p "$ROOTFS/usr/share/synthex/layouts"
        cp /synthex/layouts/*.json "$ROOTFS/usr/share/synthex/layouts/" 2>/dev/null || true
    fi
fi

if [ -d "/synthex/desktop/applications" ]; then
    mkdir -p "$ROOTFS/usr/share/applications"
    cp /synthex/desktop/applications/*.desktop "$ROOTFS/usr/share/applications/" 2>/dev/null || true
fi

# Copy Synthex system services
echo "  Installing Synthex services..."
mkdir -p "$ROOTFS/etc/systemd/system/"
for svc in /synthex/systemd/*.service; do
    if [ -f "$svc" ]; then
        cp "$svc" "$ROOTFS/etc/systemd/system/"
    fi
done

# Enable Synthex services
chroot "$ROOTFS" /bin/bash << 'CHROOT2'
    for svc in synthex-desktopd synthex-hwdaemon synthex-gpu-setupd synthex-stored \
               synthex-workspace synthex-firstboot synthex-recovery; do
        systemctl enable "$svc" 2>/dev/null || true
    done
CHROOT2

# Cleanup
echo "  Cleaning..."
chroot "$ROOTFS" dnf clean all 2>/dev/null || true
rm -rf "$ROOTFS/var/log/*" "$ROOTFS/tmp/*" "$ROOTFS/var/tmp/*"

# Create tarball
echo "  Creating tarball..."
tar -czf "$OUTPUT" -C "$ROOTFS" .

# Report
SIZE=$(du -h "$OUTPUT" | cut -f1)
echo "✅ Rootfs built: $OUTPUT"
echo "   Size: $SIZE"
echo "   To extract: tar -xzf $OUTPUT -C /mnt/root"
echo "   To boot: mount /dev/sdX /mnt/root && grub2-install ..."
