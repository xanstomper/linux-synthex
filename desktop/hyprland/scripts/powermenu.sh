#!/usr/bin/env bash
# SynthOS Nova — power menu (wofi dmenu backend, real logind actions)
set -euo pipefail
declare -A actions=(
  ["Lock"]="loginctl lock-session"
  ["Logout"]="hyprctl dispatch exit"
  ["Suspend"]="systemctl suspend"
  ["Hibernate"]="systemctl hibernate"
  ["Reboot"]="systemctl reboot"
  ["Shutdown"]="systemctl poweroff"
)
choice=$(printf '%s\n' "Lock" "Logout" "Suspend" "Hibernate" "Reboot" "Shutdown" \
  | wofi --dmenu --prompt "Power" --cache-file /dev/null 2>/dev/null) || exit 0
[ -n "${actions[$choice]:-}" ] && exec bash -c "${actions[$choice]}"
