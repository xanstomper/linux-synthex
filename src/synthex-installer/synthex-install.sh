#!/bin/bash
# Synthex Calamares Installer — Profile-based package install
# Handles post-install package installation based on user profile selection
# Called by Calamares packages module and post-install module

set -euo pipefail

PROFILE="${1:-minimal}"
LOG_FILE="/var/log/synthex-install.log"
SNAPSHOT_DESC="fresh-synthex-${PROFILE}-install"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

install_profile_base() {
    log "📦 Installing base system packages..."
    
    # Core system
    dnf install -y \
        btrfs-progs snapper \
        firewalld selinux-policy-targeted \
        flatpak fwupd \
        pipewire pipewire-pulseaudio wireplumber \
        NetworkManager network-manager-applet \
        rsync git curl wget \
        dnf5 dnf5-plugins 2>&1 | tail -1
    
    # Desktop
    dnf install -y \
        plasma-desktop sddm wayland kwin \
        dolphin konsole kate gwenview spectacle \
        kcalc kwrite qt6-qdbusviewer \
        plasma-nm plasma-pa \
        kscreen powerdevil \
        ffmpegthumbs kio-gphoto2 kio-extras 2>&1 | tail -1
}

install_profile_gaming() {
    log "🎮 Installing gaming profile..."
    
    dnf groupinstall -y --nogpgcheck synthex-gaming 2>/dev/null || {
        dnf install -y \
            steam-devices lutris mangohud gamescope \
            gamemode wine-core 2>&1 | tail -1
    }
    
    # Enable gamemode
    systemctl enable gamemoded 2>/dev/null || true
}

install_profile_developer() {
    log "💻 Installing developer profile..."
    
    dnf groupinstall -y --nogpgcheck synthex-dev 2>/dev/null || {
        dnf install -y \
            git gcc gcc-c++ make cmake \
            python3 python3-devel python3-pip \
            rust cargo golang nodejs \
            java-21-openjdk java-21-openjdk-devel \
            podman podman-compose toolbox distrobox \
            @development-tools 2>&1 | tail -1
    }
}

install_profile_creator() {
    log "🎨 Installing creator profile..."
    
    dnf install -y \
        blender krita gimp inkscape obs-studio \
        audacity handbrake 2>&1 | tail -1
}

configure_system() {
    log "⚙ Configuring system..."
    
    # Enable services
    systemctl enable sddm
    systemctl enable firewalld
    systemctl enable NetworkManager
    systemctl enable fwupd
    systemctl enable bluetooth
    
    # Enable snapshots
    snapper -c root create-config /
    snapper create --description "$SNAPSHOT_DESC"
    
    # Configure Flatpak
    flatpak remote-add --if-not-exists flathub \
        https://flathub.org/repo/flathub.flatpakrepo
    
    # Configure DNF
    cat > /etc/dnf/dnf.conf << 'DNF'
[main]
gpgcheck=True
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
fastestmirror=True
max_parallel_downloads=10
deltarpm=True
DNF
    
    # Create Synthex directories
    mkdir -p /etc/synthex /usr/share/synthex/{layouts,modes,themes}
    
    # Set default locale
    localectl set-locale LANG=en_US.UTF-8
}

configure_bootloader() {
    log "🔧 Configuring bootloader..."
    
    # Detect UEFI
    if [ -d /sys/firmware/efi ]; then
        log "UEFI detected — configuring GRUB"
        
        # Install GRUB
        if [ -d /boot/efi ]; then
            grub2-install --target=x86_64-efi --efi-directory=/boot/efi \
                --bootloader-id="Synthex" 2>&1 | tail -1
        else
            grub2-install --target=x86_64-efi --efi-directory=/boot \
                --bootloader-id="Synthex" 2>&1 | tail -1
        fi
        
        # Generate GRUB config with Synthex entries
        /usr/bin/grub-generator.sh 2>/dev/null || \
            grub2-mkconfig -o /boot/grub2/grub.cfg
    else
        log "Legacy BIOS detected — configuring GRUB"
        grub2-install "${ROOT_DISK}" 2>/dev/null || true
        grub2-mkconfig -o /boot/grub2/grub.cfg
    fi
}

post_install_cleanup() {
    log "🧹 Cleaning up..."
    
    # Remove temporary files
    rm -rf /tmp/*.rpm /tmp/ks-script*
    
    # Clean package cache
    dnf clean all
    
    # Reset machine ID (will be generated on first boot)
    rm -f /etc/machine-id
    touch /etc/machine-id
    
    log "✅ Installation complete!"
}

main() {
    log "═══════════════════════════════════"
    log "  Synthex Installer"
    log "  Profile: $PROFILE"
    log "═══════════════════════════════════"
    
    install_profile_base
    
    case "$PROFILE" in
        gaming|game)
            install_profile_gaming
            ;;
        developer|dev)
            install_profile_developer
            ;;
        creator)
            install_profile_creator
            ;;
        full)
            install_profile_gaming
            install_profile_developer
            install_profile_creator
            ;;
        minimal|*)
            # Just base packages
            ;;
    esac
    
    configure_system
    configure_bootloader
    post_install_cleanup
    
    log ""
    log "✅ Synthex ($PROFILE profile) installed!"
    log "   Reboot to start your new system"
}

main "$@"
