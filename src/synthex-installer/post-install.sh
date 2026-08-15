#!/usr/bin/env bash
# post-install.sh — Calamares post-install hook
# Runs inside the chroot target after packages are installed
set -euo pipefail

echo "🔧 Synthex post-install configuration..."

# Generate machine ID
echo "  Generating machine-id..."
systemd-machine-id-setup 2>/dev/null || true

# Set timezone if not already set
if [ ! -f /etc/localtime ]; then
    ln -sf /usr/share/zoneinfo/UTC /etc/localtime 2>/dev/null || true
fi

# Enable Synthex repositories
echo "  Enabling Synthex repositories..."
mkdir -p /etc/yum.repos.d

# Configure DNF for Synthex
mkdir -p /etc/dnf/dnf.conf.d
cat > /etc/dnf/dnf.conf 2>/dev/null << 'EOF' || true
[main]
gpgcheck=1
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
max_parallel_downloads=10
fastestmirror=True
EOF

# Set default target to graphical
echo "  Setting default boot target..."
systemctl set-default graphical.target 2>/dev/null || true

# Enable essential services
echo "  Enabling services..."
for svc in NetworkManager bluetooth sddm cups avahi-daemon sshd fwupd firewalld \
           snapper-timeline.timer snapper-cleanup.timer btrfs-scrub@-.timer \
           synthex-safety synthex-slim synthex-desktopd synthex-hwdaemon \
           synthex-gpu-setupd synthex-stored synthex-workspace synthex-oobe \
           synthex-control-center synthex-firstboot; do
    systemctl enable "$svc" 2>/dev/null || true
done

# Remove live-only packages
echo "  Removing live-session packages..."
dnf remove -y liveuser-config synthex-live-installer calamares-live 2>/dev/null || true

# Clean up live user
userdel -r liveuser 2>/dev/null || true
rm -f /etc/sudoers.d/10-liveuser 2>/dev/null || true
rm -f /etc/sddm.conf.d/autologin.conf 2>/dev/null || true

# Remove the live-mode marker so live-setup never runs on an installed system
rm -f /etc/synthex/live-mode 2>/dev/null || true

# Rebuild initramfs
echo "  Rebuilding initramfs..."
dracut --force --regenerate-all 2>/dev/null || true

# Update GRUB
echo "  Updating GRUB..."
grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || \
    grub2-mkconfig -o /boot/efi/EFI/synthex/grub.cfg 2>/dev/null || true

# Create Btrfs snapshot config for root
if command -v snapper &>/dev/null; then
    echo "  Configuring Snapper..."
    snapper -c root create-config / 2>/dev/null || true
fi

echo "✅ Post-install complete"
