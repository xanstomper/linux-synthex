#!/usr/bin/env bash
# SynthOS Nova — restart the shell (waybar + mako) without rebooting
set -euo pipefail
pkill -x waybar  2>/dev/null || true
pkill -x mako    2>/dev/null || true
sleep 0.3
setsid -f waybar
setsid -f mako
notify-send -a SynthOS "Shell restarted" "waybar + mako reloaded" 2>/dev/null || true
