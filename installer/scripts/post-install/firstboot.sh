#!/usr/bin/env bash
# synthex-firstboot.sh — First boot initialization
# Runs once on initial system startup to complete setup
set -euo pipefail

SYNTHEX_STATE="/var/lib/synthex"
LOG="/var/log/synthex-firstboot.log"

echo "=== Synthex First Boot $(date) ===" | tee "$LOG"

# Only run once
if [ -f "$SYNTHEX_STATE/firstboot-complete" ]; then
    echo "First boot already completed" | tee -a "$LOG"
    exit 0
fi

mkdir -p "$SYNTHEX_STATE"

# 1. Load install profile
if [ -f "$SYNTHEX_STATE/install-profile.json" ]; then
    PROFILE=$(jq -r '.profile' "$SYNTHEX_STATE/install-profile.json")
    echo "Profile: $PROFILE" | tee -a "$LOG"
fi

# 2. Install deferred apps from OOBE
if [ -f "$SYNTHEX_STATE/oobe-apps.json" ]; then
    echo "Installing deferred apps..." | tee -a "$LOG"
    APPS=$(jq -r '.[]' "$SYNTHEX_STATE/oobe-apps.json")
    for app in $APPS; do
        echo "  Installing $app..." | tee -a "$LOG"
        dnf install -y "$app" 2>>"$LOG" || echo "  Failed: $app" | tee -a "$LOG"
    done
    echo "Apps installed" | tee -a "$LOG"
fi

# 3. Run OOBE wizard
if command -v synthex-oobe &>/dev/null; then
    echo "Launching OOBE wizard..." | tee -a "$LOG"
    synthex-oobe
fi

# 4. Mark as complete
touch "$SYNTHEX_STATE/firstboot-complete"
echo "=== First boot complete $(date) ===" | tee -a "$LOG"
exit 0
