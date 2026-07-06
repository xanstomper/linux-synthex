#!/usr/bin/env bash
# /usr/libexec/solus/live-setup.sh — Live environment setup
# Creates liveuser, configures autologin, sets up Calamares
set -euo pipefail

echo "💿 Setting up Solus live environment..."

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
Session=plasma
EOF

# Enable Calamares desktop icon
echo "  Configuring Calamares..."
mkdir -p /home/liveuser/Desktop
cat > /home/liveuser/Desktop/install-solus.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Install Solus Linux
Name[de]=Solus Linux installieren
Comment=Launch the Solus installer
Comment[de]=Solus Installer starten
Exec=sudo calamares
Icon=calamares
Terminal=false
Categories=System;
StartupNotify=true
EOF
chown liveuser:liveuser /home/liveuser/Desktop/install-solus.desktop
chmod +x /home/liveuser/Desktop/install-solus.desktop

# Create Calamares desktop entry in applications menu
cp /home/liveuser/Desktop/install-solus.desktop /usr/share/applications/ 2>/dev/null || true

# Disable persistent services that don't make sense in live
systemctl disable snapper-timeline.timer 2>/dev/null || true
systemctl disable snapper-cleanup.timer 2>/dev/null || true
systemctl disable dnf-automatic.timer 2>/dev/null || true

# Mount shared folders if running in VM
if [ -d /run/media ]; then
    echo "  Live environment ready."
fi

# Set hostname
hostnamectl set-hostname "solus-live" 2>/dev/null || true

# Enable network
systemctl enable NetworkManager 2>/dev/null || true

echo "✅ Live environment setup complete"
