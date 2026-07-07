#!/usr/bin/env bash
# synthex-post-install.sh — Master post-install configuration script
# Installed to /usr/libexec/synthex/post-install.sh
# Called by Calamares shellprocess module after installation.
# This wires up ALL Synthex packages, daemons, and services.
set -euo pipefail

SYNTHEX_STATE="/var/lib/synthex"
LOG="/var/log/synthex-post-install.log"
mkdir -p "$SYNTHEX_STATE"

echo "=== Synthex Post-Install $(date) ===" | tee "$LOG"

# Load install profile
PROFILE="focus"
THEME="graphite"
GPU="unknown"
if [ -f "$SYNTHEX_STATE/install-profile.json" ]; then
    PROFILE=$(jq -r '.profile // "focus"' "$SYNTHEX_STATE/install-profile.json")
    THEME=$(jq -r '.theme // "graphite"' "$SYNTHEX_STATE/install-profile.json")
    GPU=$(jq -r '.gpu.vendor // "unknown"' "$SYNTHEX_STATE/install-profile.json")
    echo "Profile: $PROFILE, Theme: $THEME, GPU: $GPU" | tee -a "$LOG"
else
    echo "No install profile found, using defaults" | tee -a "$LOG"
fi

# ── 1. Configure DNF ─────────────────────────────────────────────────
echo "Configuring DNF..." | tee -a "$LOG"
mkdir -p /etc/dnf
cat > /etc/dnf/dnf.conf << 'DNFEOF'
[main]
gpgcheck=True
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
max_parallel_downloads=10
fastestmirror=True
deltarpm=True
DNFEOF

# ── 2. Enable Synthex repository ─────────────────────────────────────
echo "Enabling Synthex repository..." | tee -a "$LOG"
mkdir -p /etc/yum.repos.d
if [ -f /etc/synthex/synthex.repo ]; then
    cp /etc/synthex/synthex.repo /etc/yum.repos.d/synthex.repo 2>/dev/null || true
fi

# ── 3. Install Flatpak and Flathub ───────────────────────────────────
echo "Setting up Flatpak..." | tee -a "$LOG"
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true

# ── 4. Configure PipeWire audio ──────────────────────────────────────
echo "Configuring PipeWire..." | tee -a "$LOG"
systemctl --user enable pipewire pipewire-pulse wireplumber 2>/dev/null || true

# ── 5. GPU-specific configuration ────────────────────────────────────
echo "Configuring GPU ($GPU)..." | tee -a "$LOG"
mkdir -p /etc/dracut.conf.d
case "$GPU" in
    nvidia)
        echo 'add_drivers+=" nvidia nvidia_modeset nvidia_uvm nvidia_drm "' > /etc/dracut.conf.d/nvidia.conf
        # Enable NVIDIA persistence daemon
        systemctl enable nvidia-persistenced 2>/dev/null || true
        ;;
    amd)
        echo 'add_drivers+=" amdgpu "' > /etc/dracut.conf.d/amdgpu.conf
        ;;
esac

# ── 6. Set default kernel parameters ─────────────────────────────────
echo "Setting kernel parameters..." | tee -a "$LOG"
if [ -f /etc/default/grub ]; then
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=".*"/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash mitigations=auto"/' /etc/default/grub
fi

# ── 6b. Create required system groups ────────────────────────────────
echo "Creating system groups..." | tee -a "$LOG"
for grp in games libvirt docker; do
    getent group "$grp" >/dev/null 2>&1 || groupadd "$grp" 2>/dev/null || true
done

# Add user to groups
for grp in wheel audio video input storage games libvirt kvm docker; do
    usermod -aG "$grp" "$username" 2>/dev/null || true
done

# ── 6c. Install WiFi setup script ────────────────────────────────────
echo "Installing WiFi setup..." | tee -a "$LOG"
if [ -f /synthex/desktop/network/wifi-setup.sh ]; then
    install -m 0755 /synthex/desktop/network/wifi-setup.sh /usr/libexec/synthex/wifi-setup.sh 2>/dev/null || true
fi

# ── 6d. Install compositor launcher ──────────────────────────────────
echo "Installing compositor launcher..." | tee -a "$LOG"
if [ -f /synthex/scripts/start-synthex-compositor.sh ]; then
    install -m 0755 /synthex/scripts/start-synthex-compositor.sh /usr/libexec/synthex/start-synthex-compositor.sh 2>/dev/null || true
fi

# ── 6e. Install firstboot script ─────────────────────────────────────
echo "Installing firstboot script..." | tee -a "$LOG"
if [ -f /synthex/systemd/synthex-firstboot-impl.sh ]; then
    install -m 0755 /synthex/systemd/synthex-firstboot-impl.sh /usr/libexec/synthex/firstboot.sh 2>/dev/null || true
fi

# ── 7. Enable system services ────────────────────────────────────────
echo "Enabling system services..." | tee -a "$LOG"
for svc in NetworkManager bluetooth sddm cups firewalld fwupd; do
    systemctl enable "$svc" 2>/dev/null || true
done

# ── 8. Enable Synthex services ───────────────────────────────────────
echo "Enabling Synthex services..." | tee -a "$LOG"
for svc in \
    synthex-system-daemon.service \
    synthex-desktopd.service \
    synthex-hwdaemon.service \
    synthex-gpu-setupd.service \
    synthex-stored.service \
    synthex-ai-daemon.service \
    synthex-snapshot-manager.timer \
    synthex-blueprint.timer \
    synthex-oobe.service \
    synthex.target; do
    systemctl enable "$svc" 2>/dev/null || true
done

# ── 9. Set graphical target ──────────────────────────────────────────
systemctl set-default graphical.target 2>/dev/null || true

# ── 10. Create user directories ──────────────────────────────────────
echo "Creating user directories..." | tee -a "$LOG"
for dir in Desktop Documents Downloads Music Pictures Videos .config .local; do
    mkdir -p "/etc/skel/$dir" 2>/dev/null || true
done

# ── 11. Configure tuned performance profiles ──────────────────────────
if command -v tuned-adm &>/dev/null; then
    case "$PROFILE" in
        gaming)  tuned-adm profile gaming 2>/dev/null || true ;;
        pro)     tuned-adm profile latency-performance 2>/dev/null || true ;;
        lite)    tuned-adm profile powersave 2>/dev/null || true ;;
        studio)  tuned-adm profile audio-production 2>/dev/null || true ;;
        *)       tuned-adm profile balanced 2>/dev/null || true ;;
    esac
fi

# ── 11. Deploy security hardening ──────────────────────────────────────
echo "Deploying security hardening..." | tee -a "$LOG"
if [ -x /usr/libexec/synthex/security-deploy.sh ]; then
    /usr/libexec/synthex/security-deploy.sh 2>&1 | tail -5 | tee -a "$LOG"
elif [ -f /usr/share/synthex/security-deploy.sh ]; then
    bash /usr/share/synthex/security-deploy.sh 2>&1 | tail -5 | tee -a "$LOG"
else
    echo "  security-deploy.sh not found, skipping" | tee -a "$LOG"
fi

# ── 12. Update initramfs ─────────────────────────────────────────────
echo "Updating initramfs..." | tee -a "$LOG"
dracut --force --regenerate-all 2>/dev/null || true

# ── 13. Update GRUB ──────────────────────────────────────────────────
echo "Updating GRUB..." | tee -a "$LOG"
grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || true

# ── 14. Set permissions ──────────────────────────────────────────────
chmod 755 /usr/libexec/synthex/*.sh 2>/dev/null || true
chmod 755 /usr/bin/synthex* 2>/dev/null || true

echo "=== Post-install complete $(date) ===" | tee -a "$LOG"
exit 0
