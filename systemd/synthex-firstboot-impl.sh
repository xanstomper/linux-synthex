#!/usr/bin/env bash
# /usr/libexec/synthex/firstboot.sh — Synthex first boot initialization
# Runs once on initial system startup to complete setup
# Called by synthex-firstboot.service
set -euo pipefail

SYNTHEX_STATE="/var/lib/synthex"
LOG="/var/log/synthex-firstboot.log"
mkdir -p "$SYNTHEX_STATE"

echo "=== Synthex First Boot $(date) ===" | tee "$LOG"

# Only run once
if [ -f "$SYNTHEX_STATE/firstboot-complete" ]; then
    echo "First boot already completed" | tee -a "$LOG"
    exit 0
fi

# 1. Create required system groups
echo "Creating system groups..." | tee -a "$LOG"
for grp in games libvirt docker; do
    getent group "$grp" >/dev/null 2>&1 || groupadd "$grp" 2>/dev/null || true
done
# Add liveuser to groups
for grp in wheel audio video input storage games libvirt kvm docker; do
    usermod -aG "$grp" "$(logname 2>/dev/null || echo 'synthex')" 2>/dev/null || true
done

# 2. Load install profile
if [ -f "$SYNTHEX_STATE/install-profile.json" ]; then
    PROFILE=$(jq -r '.profile // "classic"' "$SYNTHEX_STATE/install-profile.json")
    echo "Profile: $PROFILE" | tee -a "$LOG"
fi

# 3. Install deferred apps from OOBE
if [ -f "$SYNTHEX_STATE/oobe-apps.json" ]; then
    echo "Installing deferred apps..." | tee -a "$LOG"
    APPS=$(jq -r '.[]' "$SYNTHEX_STATE/oobe-apps.json" 2>/dev/null || true)
    for app in $APPS; do
        case "$app" in
            firefox)       dnf install -y firefox 2>>"$LOG" || true ;;
            brave)         dnf install -y brave-browser 2>>"$LOG" || flatpak install -y flathub com.brave.Browser 2>>"$LOG" || true ;;
            discord)       flatpak install -y flathub com.discordapp.Discord 2>>"$LOG" || dnf install -y discord 2>>"$LOG" || true ;;
            steam)         dnf install -y steam 2>>"$LOG" || flatpak install -y flathub com.valvesoftware.Steam 2>>"$LOG" || true ;;
            vscode)        flatpak install -y flathub com.visualstudio.code 2>>"$LOG" || true ;;
            obs)           flatpak install -y flathub com.obsproject.Studio 2>>"$LOG" || dnf install -y obs-studio 2>>"$LOG" || true ;;
            vlc)           dnf install -y vlc 2>>"$LOG" || flatpak install -y flathub org.videolan.VLC 2>>"$LOG" || true ;;
            *)             flatpak install -y flathub "$app" 2>>"$LOG" || dnf install -y "$app" 2>>"$LOG" || true ;;
        esac
    done
    echo "Apps installed" | tee -a "$LOG"
fi

# 4. Run auto-tuning
if [ -x /usr/libexec/synthex/synthex-auto-tune ]; then
    echo "Running auto-tuning..." | tee -a "$LOG"
    /usr/libexec/synthex/synthex-auto-tune 2>&1 | tail -5 | tee -a "$LOG"
fi

# 5. WiFi auto-connect
if [ -x /usr/libexec/synthex/wifi-setup.sh ]; then
    echo "Running WiFi setup..." | tee -a "$LOG"
    /usr/libexec/synthex/wifi-setup.sh 2>&1 | tail -3 | tee -a "$LOG"
fi

# 6. Run OOBE wizard
if command -v synthex-oobe &>/dev/null; then
    echo "Launching OOBE wizard..." | tee -a "$LOG"
    synthex-oobe 2>/dev/null || true
fi

# 7. Mark as complete
touch "$SYNTHEX_STATE/firstboot-complete"
echo "=== First boot complete $(date) ===" | tee -a "$LOG"
exit 0