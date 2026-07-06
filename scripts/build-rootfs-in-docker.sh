#!/usr/bin/env bash
# Rootfs builder — runs INSIDE the Docker container
# Creates a bootable Solus root filesystem tarball
set -euo pipefail
ROOTFS="/tmp/solus-rootfs"
OUTPUT="/output/solus-rootfs-$(date +%Y%m%d).tar.gz"

echo "📦 Creating Solus rootfs at ${ROOTFS}..."

# Clean and create
rm -rf "$ROOTFS"
mkdir -p "$ROOTFS"

# Install base system
echo "  Installing base system..."
dnf install --installroot="$ROOTFS" --releasever=41 --setopt=tsflags=nodocs \
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
dnf install --installroot="$ROOTFS" --releasever=41 --setopt=tsflags=nodocs \
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
    dnf install --installroot="$ROOTFS" --releasever=41 --use-host-config -y \
        https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-41.noarch.rpm \
        https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-41.noarch.rpm \
        2>/dev/null || true
done

# Install gaming / NVIDIA / codecs
echo "  Installing gaming stack and drivers..."
dnf install --installroot="$ROOTFS" --releasever=41 --setopt=tsflags=nodocs \
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
    docker-ce docker-ce-cli containerd.io \
    podman buildah skopeo \
    rust cargo golang nodejs java-21-openjdk \
    2>&1 | tail -5

# Solus platform meta-packages (safety/essentials/creator/gaming)
echo "  Installing Solus platform meta-packages..."
dnf install --installroot="$ROOTFS" --releasever=41 --setopt=tsflags=nodocs \
    --setopt=install_weak_deps=False --skip-unavailable --use-host-config -y \
    solus-safety solus-essentials solus-creator-platform solus-gaming-platform \
    2>/dev/null || true

# Enable Solus platform services in the rootfs
echo "  Enabling Solus platform services..."
for svc in solus-safety solus-slim solus-boot-profile solus-oobe solus-control-center \
           solus-workspace solus-desktopd solus-hwdaemon solus-gpu-setupd solus-stored; do
    chroot "$ROOTFS" systemctl enable "$svc.service" 2>/dev/null || true
done

# Development + creator tools
echo "  Installing development and creator tools..."
dnf install --installroot="$ROOTFS" --releasever=41 --setopt=tsflags=nodocs \
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
    echo "root:solus" | chpasswd
    
    # Create user
    useradd -m -G wheel,audio,video,storage solus
    echo "solus:solus" | chpasswd
    
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
    echo "solus" > /etc/hostname
    
    # ─── Apply Solus KDE Plasma Configuration ───
    mkdir -p /home/solus/.config /root/.config
    
    # Set Plasma color scheme to SolusMint
    cat > /home/solus/.config/kdeglobals << 'KDE'
[General]
ColorScheme=SolusMint
font=Noto Sans,10,-1,5,50,0,0,0,0,0
fixed=JetBrains Mono,10,-1,5,50,0,0,0,0,0

[Icons]
Theme=Mint-Y

[KDE]
ColorScheme=SolusMint
KDE

    # Set KWin compositor settings
    cat > /home/solus/.config/kwinrc << 'KWIN'
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
theme=solus-mint
KWIN

    # Default applications (XDG MIME)
    mkdir -p /home/solus/.config
    cat > /home/solus/.config/mimeapps.list << 'MIME'
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
    mkdir -p /home/solus/.config
    cat > /home/solus/.config/plasma-org.kde.plasma.desktop-appletsrc << 'PLASMA'
[Containments][1][General]
wallpaper=org.kde.image
lastSelectedImage=/usr/share/wallpapers/solus/solus-dark-4k.svg
image=/usr/share/wallpapers/solus/solus-dark-4k.svg

[Containments][2][General]
wallpaper=org.kde.image
lastSelectedImage=/usr/share/wallpapers/solus/solus-dark-4k.svg
PLASMA

    # Configure SDDM theme
    mkdir -p /etc/sddm.conf.d
    cat > /etc/sddm.conf.d/solus.conf << 'SDDM'
[Theme]
Current=solus-sddm-theme
CursorTheme=Bibata-Modern-Classic
Font=Noto Sans,10

[General]
Numlock=on

[Autologin]
User=solus
Session=plasma.desktop
Relogin=false
SDDM

    # Set Plymouth theme
    if [ -f /usr/sbin/plymouth-set-default-theme ]; then
        plymouth-set-default-theme solus 2>/dev/null || true
    fi

    # Own configs by user
    chown -R solus:solus /home/solus/.config 2>/dev/null || true

    # Copy configs to skel for new users
    cp -r /home/solus/.config /etc/skel/ 2>/dev/null || true
    
    # Set kernel cmdline defaults
    if [ -f /etc/default/grub ]; then
        sed -i 's/GRUB_CMDLINE_LINUX=""/GRUB_CMDLINE_LINUX="quiet splash rd.luks=1 selinux=1 enforcing=1 audit=1"/' /etc/default/grub 2>/dev/null || true
        sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet"/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/' /etc/default/grub 2>/dev/null || true
        echo 'GRUB_THEME="/boot/grub2/themes/solus/theme.txt"' >> /etc/default/grub 2>/dev/null || true
    fi
CHROOT

# Copy Solus branding and configs
echo "  Applying Solus branding and features..."
if [ -d "/solus/branding" ]; then
    # Wallpapers
    mkdir -p "$ROOTFS/usr/share/wallpapers/solus"
    cp -r /solus/branding/wallpaper/* "$ROOTFS/usr/share/wallpapers/solus/" 2>/dev/null || true
    
    # GRUB theme
    if [ -d "/solus/branding/grub" ]; then
        mkdir -p "$ROOTFS/boot/grub2/themes/solus"
        cp -r /solus/branding/grub/* "$ROOTFS/boot/grub2/themes/solus/" 2>/dev/null || true
    fi
    
    # Plymouth theme
    if [ -d "/solus/branding/plymouth" ]; then
        mkdir -p "$ROOTFS/usr/share/plymouth/themes/solus"
        cp -r /solus/branding/plymouth/* "$ROOTFS/usr/share/plymouth/themes/solus/" 2>/dev/null || true
    fi
    
    # SDDM theme
    if [ -d "/solus/desktop/sddm" ]; then
        mkdir -p "$ROOTFS/etc/sddm.conf.d"
        cp /solus/desktop/sddm/sddm.conf "$ROOTFS/etc/sddm.conf.d/" 2>/dev/null || true
    fi
    
    # Font config
    if [ -f "/solus/desktop/fonts/local.conf" ]; then
        mkdir -p "$ROOTFS/etc/fonts"
        cp /solus/desktop/fonts/local.conf "$ROOTFS/etc/fonts/" 2>/dev/null || true
    fi
    
    # Bluetooth config
    if [ -f "/solus/desktop/bluetooth/main.conf" ]; then
        mkdir -p "$ROOTFS/etc/bluetooth"
        cp /solus/desktop/bluetooth/main.conf "$ROOTFS/etc/bluetooth/" 2>/dev/null || true
    fi
    
    # Mint-style layout
    if [ -f "/solus/layouts/mint.json" ]; then
        mkdir -p "$ROOTFS/usr/share/solus/layouts"
        cp /solus/layouts/*.json "$ROOTFS/usr/share/solus/layouts/" 2>/dev/null || true
    fi
fi

if [ -d "/solus/desktop/applications" ]; then
    mkdir -p "$ROOTFS/usr/share/applications"
    cp /solus/desktop/applications/*.desktop "$ROOTFS/usr/share/applications/" 2>/dev/null || true
fi

# Copy Solus system services
echo "  Installing Solus services..."
mkdir -p "$ROOTFS/etc/systemd/system/"
for svc in /solus/systemd/*.service; do
    if [ -f "$svc" ]; then
        cp "$svc" "$ROOTFS/etc/systemd/system/"
    fi
done

# Enable Solus services
chroot "$ROOTFS" /bin/bash << 'CHROOT2'
    for svc in solus-desktopd solus-hwdaemon solus-gpu-setupd solus-stored \
               solus-workspace solus-firstboot solus-recovery; do
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
