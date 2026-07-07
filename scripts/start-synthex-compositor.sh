#!/usr/bin/env bash
# /usr/libexec/synthex/start-synthex-compositor.sh
# SDDM Wayland compositor launcher — starts KDE Plasma Wayland session
# This is referenced by sddm.conf [Wayland] CompositorCommand
set -euo pipefail

# Source environment
if [ -f /etc/profile ]; then
    . /etc/profile
fi

# Start KDE Plasma Wayland session
if [ -x /usr/libexec/plasma-dbus-run-session-if-needed ]; then
    exec /usr/libexec/plasma-dbus-run-session-if-needed /usr/bin/startplasma-wayland
elif [ -x /usr/bin/startplasma-wayland ]; then
    exec /usr/bin/startplasma-wayland
else
    # Fallback to X11 Plasma session
    exec /usr/bin/startplasma-x11
fi
