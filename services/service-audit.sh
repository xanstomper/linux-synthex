#!/usr/bin/env bash
# Solus Service Audit — classify every enabled systemd unit as
# essential / desktop-optional / bloat and write a JSON report.
# Usage: solus-service-audit.sh [--apply]
set -euo pipefail

REPORT="/var/lib/solus/service-audit.json"
STATE="/var/lib/solus"

# Units that must NEVER be disabled
ESSENTIAL="systemd NetworkManager dbus polkit rtkit-daemon pipewire wireplumber \
    firewalld cronie rsyslog auditd udev udisks2 upower \
    solus-desktopd solus-hwdaemon solus-gpu-setupd solus-stored solus-workspace \
    solus-recovery solus-firstboot solus-safety solus-oobe solus-control-center"

# Units that are optional depending on hardware/use
OPTIONAL="bluetooth cups avahi-daemon avahi-dnsconfd ModemManager \
    smartcard-daemon atd crond rsyncd nfs-server nfs-client \
    iscsi iscsid mdmonitor dmraid-event \
    rpcbind rpc-statd gssproxy \
    colord power-profiles-daemon switcheroo-control \
    low-memory-monitor fwupd"

# Units that are almost always bloat on a desktop
BLOAT="abrtd abrt-journal-core abrt-oops abrt-vmcore abrt-ccpp \
    kdump kdumpette thermald (laptops only) \
    ntpd chronyd (use systemd-timesyncd) \
    postfix sendmail exim \
    qpidd ksmtuned sensord"

mkdir -p "$STATE"

classify() {
    local unit="$1"
    for e in $ESSENTIAL; do [[ "$unit" == *"$e"* ]] && echo "essential" && return; done
    for b in $BLOAT;    do [[ "$unit" == *"$b"* ]] && echo "bloat"     && return; done
    for o in $OPTIONAL; do [[ "$unit" == *"$o"* ]] && echo "optional"   && return; done
    echo "unknown"
}

# Gather enabled units
enabled=$(systemctl list-unit-files --state=enabled --type=service --no-legend 2>/dev/null | awk '{print $1}')

essential_json=""
optional_json=""
bloat_json=""
unknown_json=""

for u in $enabled; do
    cls=$(classify "$u")
    entry="\"$u\""
    case "$cls" in
        essential) essential_json="${essential_json:+$essential_json,}$entry" ;;
        optional)  optional_json="${optional_json:+$optional_json,}$entry"   ;;
        bloat)     bloat_json="${bloat_json:+$bloat_json,}$entry"           ;;
        *)         unknown_json="${unknown_json:+$unknown_json,}$entry"      ;;
    esac
done

cat > "$REPORT" <<EOF
{
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')",
  "essential": [${essential_json}],
  "optional":  [${optional_json}],
  "bloat":     [${bloat_json}],
  "unknown":   [${unknown_json}]
}
EOF

echo "Service audit written to $REPORT"
echo "  essential: $(echo "$essential_json" | tr ',' '\n' | grep -c '\"') units"
echo "  optional:  $(echo "$optional_json"  | tr ',' '\n' | grep -c '\"') units"
echo "  bloat:     $(echo "$bloat_json"     | tr ',' '\n' | grep -c '\"') units"
echo "  unknown:   $(echo "$unknown_json"   | tr ',' '\n' | grep -c '\"') units"
echo ""
echo "Review bloat + optional, then run solus-slim-services.sh to disable."
