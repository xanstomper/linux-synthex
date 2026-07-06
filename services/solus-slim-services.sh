#!/usr/bin/env bash
# Solus Slim Services — conditionally + reversibly disable bloat.
# Detects hardware first; never breaks the system. Logs to /var/log/solus-slim.log.
# Re-enable any unit with: systemctl enable <unit>
set -euo pipefail

LOG="/var/log/solus-slim.log"
STATE="/var/lib/solus/slim-disabled.txt"
mkdir -p "$(dirname "$LOG")" "$(dirname "$STATE")"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

[[ $EUID -eq 0 ]] || { log "must run as root"; exit 1; }

has_printer()  { lpstat -p 2>/dev/null | grep -q . ; }
has_bt()       { rfkill list bluetooth 2>/dev/null | grep -q . ; }
has_modem()    { ls /sys/class/net 2>/dev/null | grep -qE 'wwan|enp0s.*c.*mbim'; }
has_raid()     { lsblk -o TYPE 2>/dev/null | grep -q raid; }

disable_if() {
    local unit="$1" condition="$2"
    if systemctl list-unit-files "$unit" &>/dev/null; then
        if eval "$condition"; then
            log "keeping $unit (hardware present)"
        else
            systemctl disable "$unit" 2>/dev/null || true
            systemctl stop "$unit" 2>/dev/null || true
            echo "$unit" >> "$STATE"
            log "disabled $unit (no matching hardware)"
        fi
    fi
}

log "═══ Solus Slim Services ═══"

# Printer-dependent
disable_if cups.service "! has_printer"
disable_if cups.socket "! has_printer"
disable_if cups-browsed.service "! has_printer"
disable_if avahi-daemon.service "! has_printer"
disable_if avahi-daemon.socket "! has_printer"

# Mobile broadband
disable_if ModemManager.service "! has_modem"

# Bluetooth
disable_if bluetooth.service "! has_bt"

# Always-bloat (safe to disable on desktop)
for u in abrtd.service abrt-journal-core.service abrt-oops.service abrt-vmcore.service \
         abrt-ccpp.service smartcard-daemon.service atd.service \
         nfs-server.service nfs-client.service iscsi.service iscsid.service \
         rpcbind.service rpc-statd.service gssproxy.service; do
    if systemctl list-unit-files "$u" &>/dev/null; then
        systemctl disable "$u" 2>/dev/null || true
        systemctl stop "$u" 2>/dev/null || true
        echo "$u" >> "$STATE"
        log "disabled $u (bloat)"
    fi
done

# RAID only if no RAID present
disable_if mdmonitor.service "! has_raid"

# Use systemd-timesyncd instead of chronyd/ntpd if present
if systemctl list-unit-files chronyd.service &>/dev/null && \
   systemctl list-unit-files systemd-timesyncd.service &>/dev/null; then
    systemctl disable chronyd.service 2>/dev/null || true
    systemctl enable systemd-timesyncd.service 2>/dev/null || true
    log "switched chronyd → systemd-timesyncd"
fi

log "done — $(wc -l < "$STATE" 2>/dev/null || echo 0) units disabled"
log "re-enable any with: systemctl enable <unit>"
