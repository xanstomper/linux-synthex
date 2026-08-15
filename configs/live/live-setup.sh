#!/usr/bin/env bash
# /usr/libexec/synthex/live-setup.sh — Live environment setup
# Creates liveuser, configures autologin, sets up Calamares
set -euo pipefail

echo "💿 Setting up Synthex live environment..."

# Create live user
echo "  Creating liveuser..."
useradd -m -G wheel,audio,video,input,storage -s /bin/bash liveuser 2>/dev/null || true
echo "liveuser" | passwd --stdin liveuser 2>/dev/null || true

# Passwordless sudo for liveuser
echo "liveuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/10-liveuser
chmod 440 /etc/sudoers.d/10-liveuser

# Autologin for live session
echo "  Configuring autologin..."
mkdir -p /etc/sddm.conf.d
cat > /etc/sddm.conf.d/autologin.conf << 'EOF'
[Autologin]
User=liveuser
Session=plasma.desktop
EOF

# Enable Calamares desktop icon
echo "  Configuring Calamares..."
mkdir -p /home/liveuser/Desktop
cat > /home/liveuser/Desktop/install-synthex.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Install SynthOS
Name[de]=SynthOS installieren
Comment=Launch the Synthex installer
Comment[de]=Synthex Installer starten
Exec=sudo calamares
Icon=calamares
Terminal=false
Categories=System;
StartupNotify=true
EOF
chown liveuser:liveuser /home/liveuser/Desktop/install-synthex.desktop
chmod +x /home/liveuser/Desktop/install-synthex.desktop

# Create Calamares desktop entry in applications menu
cp /home/liveuser/Desktop/install-synthex.desktop /usr/share/applications/ 2>/dev/null || true

# Disable persistent services that don't make sense in live
systemctl disable snapper-timeline.timer 2>/dev/null || true
systemctl disable snapper-cleanup.timer 2>/dev/null || true
systemctl disable dnf-automatic.timer 2>/dev/null || true
systemctl disable synthex-firstboot 2>/dev/null || true
systemctl disable synthex-oobe 2>/dev/null || true
systemctl disable synthex-system-daemon 2>/dev/null || true
systemctl disable synthex-hwdaemon 2>/dev/null || true
systemctl disable synthex-desktopd 2>/dev/null || true
systemctl disable synthex-gpu-setupd 2>/dev/null || true
systemctl disable synthex-stored 2>/dev/null || true

# Run hardware detection hook for Calamares pre-seeding
echo "  Running hardware detection..." 
if [ -x /usr/libexec/synthex/installer-hook.sh ]; then
    /usr/libexec/synthex/installer-hook.sh 2>/dev/null || true
elif [ -f /synthex/installer/scripts/synthex-installer-hook ]; then
    bash /synthex/installer/scripts/synthex-installer-hook 2>/dev/null || true
fi

# Mount shared folders if running in VM
if [ -d /run/media ]; then
    echo "  Live environment ready."
fi

# Set hostname
hostnamectl set-hostname "synthex-live" 2>/dev/null || true

# Enable network
systemctl enable NetworkManager 2>/dev/null || true

echo "✅ Live environment setup complete"
