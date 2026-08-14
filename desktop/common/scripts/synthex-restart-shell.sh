#!/usr/bin/env bash
# Restart the desktop shell layer (Plasma: kwin_wayland; Hyprland: waybar/mako)
set -euo pipefail
if pgrep -x plasmashell >/dev/null; then
    kquitapp6 plasmashell 2>/dev/null || killall -TERM plasmashell 2>/dev/null || true
    sleep 1; setsid -f kstart plasmashell 2>/dev/null || setsid -f plasmashell
elif pgrep -x Hyprland >/dev/null; then
    /usr/share/synthex/hyprland/scripts/restart-shell.sh
fi
