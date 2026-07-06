#!/usr/bin/env bash
# Solus WiFi Auto-Connect Setup
# Detects and configures WiFi on first boot
# Runs as part of solus-firstboot.service

set -euo pipefail

log() { echo "[wifi] $*"; }

detect_wifi() {
    # Check for WiFi hardware
    if ! iw dev 2>/dev/null | grep -q "Interface"; then
        log "No WiFi interface detected"
        return 1
    fi
    
    # Get interface name
    IFACE=$(iw dev 2>/dev/null | grep "Interface" | awk '{print $2}')
    if [ -z "$IFACE" ]; then
        log "Could not determine WiFi interface"
        return 1
    fi
    
    log "WiFi interface: $IFACE"
    
    # Check if interface is soft-blocked
    if rfkill list wifi 2>/dev/null | grep -q "Soft blocked: yes"; then
        log "Unblocking WiFi..."
        rfkill unblock wifi
    fi
    
    # Bring interface up
    ip link set "$IFACE" up 2>/dev/null || true
    
    # Scan for networks
    log "Scanning for networks..."
    iw dev "$IFACE" scan 2>/dev/null | grep "SSID:" | sort -u | head -10 || true
    
    return 0
}

auto_connect() {
    # Try to connect to known networks via NetworkManager
    if command -v nmcli &>/dev/null; then
        # Check if already connected
        if nmcli -t -f GENERAL.STATE con show 2>/dev/null | grep -q "activated"; then
            log "Already connected to a network"
            nmcli con show --active 2>/dev/null | head -5
            return 0
        fi
        
        # Try to auto-connect using saved profiles
        log "Attempting auto-connect..."
        nmcli device wifi rescan 2>/dev/null || true
        sleep 2
        
        # List available networks
        nmcli -f SSID,SIGNAL,SECURITY device wifi list 2>/dev/null | head -10 || true
    fi
}

main() {
    log "Solus WiFi Setup"
    
    detect_wifi || true
    auto_connect || true
    
    log "WiFi setup complete"
}

main "$@"
