#!/usr/bin/env bash
# install-calamares-branding.sh — Deploy Synthex branding to Calamares
# Copies branding assets to the correct locations for the live ISO and installed system
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

BRANDING_SRC="$PROJECT_DIR/branding/calamares"
BRANDING_DST="/usr/share/calamares/branding/synthex"

LOG="/var/log/synthex-branding-install.log"
echo "=== Installing Calamares branding $(date) ===" | tee "$LOG"

# Create branding directory
mkdir -p "$BRANDING_DST"

# Install branding descriptor
if [ -f "$BRANDING_SRC/branding.desc" ]; then
    install -m 0644 "$BRANDING_SRC/branding.desc" "$BRANDING_DST/branding.desc"
    echo "  Installed branding.desc" | tee -a "$LOG"
fi

# Install slideshow
if [ -f "$BRANDING_SRC/show.qml" ]; then
    install -m 0644 "$BRANDING_SRC/show.qml" "$BRANDING_DST/show.qml"
    echo "  Installed show.qml" | tee -a "$LOG"
fi

# Install images
for img in synthex-logo.png synthex-icon.png synthex-welcome.png; do
    if [ -f "$BRANDING_SRC/$img" ]; then
        install -m 0644 "$BRANDING_SRC/$img" "$BRANDING_DST/$img"
        echo "  Installed $img" | tee -a "$LOG"
    fi
done

# Install Calamares settings
CALAMARES_CONF="/etc/calamares"
mkdir -p "$CALAMARES_CONF"

if [ -f "$PROJECT_DIR/installer/config/calamares-settings.conf" ]; then
    install -m 0644 "$PROJECT_DIR/installer/config/calamares-settings.conf" \
        "$CALAMARES_CONF/settings.conf"
    echo "  Installed settings.conf" | tee -a "$LOG"
fi

# Install module configs
for module_dir in "$PROJECT_DIR/installer/modules"/*/; do
    module_name=$(basename "$module_dir")
    mkdir -p "$CALAMARES_CONF/modules/$module_name"
    for conf in "$module_dir"*.conf; do
        [ -f "$conf" ] && install -m 0644 "$conf" "$CALAMARES_CONF/modules/$module_name/"
    done
done

# Install custom modules (Python/QML)
MODULES_DST="/usr/lib/calamares/modules"
mkdir -p "$MODULES_DST"

for module_dir in "$PROJECT_DIR/installer/modules/synthexprofile" \
                  "$PROJECT_DIR/installer/modules/synthexpostinstall"; do
    module_name=$(basename "$module_dir")
    mkdir -p "$MODULES_DST/$module_name"
    cp -r "$module_dir"/* "$MODULES_DST/$module_name/" 2>/dev/null || true
    echo "  Installed module: $module_name" | tee -a "$LOG"
done

# Install post-install scripts to /usr/libexec/synthex
LIBEXEC="/usr/libexec/synthex"
mkdir -p "$LIBEXEC"

for script in "$PROJECT_DIR/installer/scripts/post-install"/*.sh; do
    [ -f "$script" ] && install -m 0755 "$script" "$LIBEXEC/"
done

# Install installer hook
if [ -f "$PROJECT_DIR/installer/scripts/synthex-installer-hook" ]; then
    install -m 0755 "$PROJECT_DIR/installer/scripts/synthex-installer-hook" \
        "$LIBEXEC/installer-hook.sh"
fi

# Install Flatpak config
mkdir -p /etc/flatpak
if [ -f "$PROJECT_DIR/configs/flatpak/flathub.flatpakrepo" ]; then
    install -m 0644 "$PROJECT_DIR/configs/flatpak/flathub.flatpakrepo" /etc/flatpak/
fi

# Install firewalld zone
if [ -f "$PROJECT_DIR/configs/firewalld/synthex.xml" ]; then
    mkdir -p /etc/firewalld/zones
    install -m 0644 "$PROJECT_DIR/configs/firewalld/synthex.xml" /etc/firewalld/zones/
fi

# Install snapper config
if [ -f "$PROJECT_DIR/configs/snapper/snapper-root.conf" ]; then
    mkdir -p /etc/snapper/configs
    install -m 0644 "$PROJECT_DIR/configs/snapper/snapper-root.conf" /etc/snapper/configs/root
fi

# Install GRUB defaults
if [ -f "$PROJECT_DIR/configs/grub/grub-default" ]; then
    install -m 0644 "$PROJECT_DIR/configs/grub/grub-default" /etc/default/grub
fi

# Install SDDM config
if [ -f "$PROJECT_DIR/configs/sddm/sddm-synthex.conf" ]; then
    mkdir -p /etc/sddm.conf.d
    install -m 0644 "$PROJECT_DIR/configs/sddm/sddm-synthex.conf" /etc/sddm.conf.d/synthex.conf
fi

# Install journald config
if [ -f "$PROJECT_DIR/configs/journald/journald-synthex.conf" ]; then
    mkdir -p /etc/systemd/journald.conf.d
    install -m 0644 "$PROJECT_DIR/configs/journald/journald-synthex.conf" \
        /etc/systemd/journald.conf.d/synthex.conf
fi

# Install DNF config
if [ -f "$PROJECT_DIR/configs/dnf/synthex-dnf.conf" ]; then
    mkdir -p /etc/dnf
    install -m 0644 "$PROJECT_DIR/configs/dnf/synthex-dnf.conf" /etc/dnf/dnf.conf
fi

# Install security hardening configs
mkdir -p /usr/share/synthex/security/hardening
for f in sysctl.conf auditd.rules limits.conf; do
    if [ -f "$PROJECT_DIR/security/hardening/$f" ]; then
        install -m 0644 "$PROJECT_DIR/security/hardening/$f" \
            /usr/share/synthex/security/hardening/$f
    fi
done

# Install modprobe security blacklist
if [ -f "$PROJECT_DIR/configs/modprobe/synthex-security.conf" ]; then
    install -m 0644 "$PROJECT_DIR/configs/modprobe/synthex-security.conf" \
        /etc/modprobe.d/synthex-security.conf
fi

# Install systemd service units
for service in "$PROJECT_DIR/systemd"/*.service \
               "$PROJECT_DIR/systemd"/*.timer \
               "$PROJECT_DIR/systemd"/*.target \
               "$PROJECT_DIR/systemd"/*.path; do
    [ -f "$service" ] && install -m 0644 "$service" /usr/lib/systemd/system/
done
echo "  Installed $(ls "$PROJECT_DIR/systemd"/*.service "$PROJECT_DIR/systemd"/*.timer 2>/dev/null | wc -l) service units" | tee -a "$LOG"

# Install udev rules
for rules in "$PROJECT_DIR/udev"/*.rules; do
    [ -f "$rules" ] && install -m 0644 "$rules" /etc/udev/rules.d/
done

# Install desktop entries
for desktop in "$PROJECT_DIR/desktop/applications"/*.desktop; do
    [ -f "$desktop" ] && install -m 0644 "$desktop" /usr/share/applications/
done

# Mark branding as installed
touch /var/lib/synthex/.branding-installed

echo "=== Calamares branding installation complete ===" | tee -a "$LOG"
exit 0
