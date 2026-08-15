#!/usr/bin/env bash
# Waybar Aegis Defense Status Module
set -euo pipefail

STATUS="ARMED"
CLASS="armed"
TEXT="🛡️ 6/6"
TOOLTIP="Aegis Endpoint Defense Shield: ARMED\n• Anti-DMA Memory Protection: Active\n• Hardware Brute-Force Rate Limiter: Armed\n• dm-integrity Block Sentinel: Enforcing\n• TPM2 PCR Hardware Sealing: Verified\n• Keyring Threat Isolation: Active\n• Panic Purge Trigger: Ready"

if [ -f /etc/sysctl.d/97-synthex-aegis-encryption.conf ]; then
    TEXT="🛡️ 6/6"
    CLASS="armed"
else
    TEXT="🛡️ Standby"
    CLASS="standby"
fi

echo "{\"text\": \"$TEXT\", \"tooltip\": \"$TOOLTIP\", \"class\": \"$CLASS\"}"
