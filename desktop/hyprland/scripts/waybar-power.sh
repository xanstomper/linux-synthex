#!/usr/bin/env bash
# Waybar Power Profile Status Module
set -euo pipefail

PROF="balanced"
if [ -f /var/lib/synthex/power-profile ]; then
    PROF=$(cat /var/lib/synthex/power-profile)
elif command -v powerprofilesctl >/dev/null 2>&1; then
    PROF=$(powerprofilesctl get 2>/dev/null || echo "balanced")
fi

case "$PROF" in
    performance)
        TEXT="⚡ Perf"
        CLASS="performance"
        TOOLTIP="Power Profile: Performance\n• CPU Governor: Performance\n• EPP: performance\n• PCIe ASPM: High Speed"
        ;;
    power-saver|powersave)
        TEXT="🔋 Save"
        CLASS="powersave"
        TOOLTIP="Power Profile: Power Saver\n• CPU Governor: Powersave\n• EPP: power\n• PCIe ASPM: Powersave"
        ;;
    *)
        TEXT="⚖️ Bal"
        CLASS="balanced"
        TOOLTIP="Power Profile: Balanced\n• CPU Governor: Schedutil\n• EPP: balance_performance\n• PCIe ASPM: Auto"
        ;;
esac

echo "{\"text\": \"$TEXT\", \"tooltip\": \"$TOOLTIP\", \"class\": \"$CLASS\"}"
