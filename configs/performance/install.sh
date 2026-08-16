#!/usr/bin/env bash
# Bake Synthex performance defaults into an image root (or "/" to apply live).
# Idempotent and reversible. Usage: ./install.sh [installroot]
set -e
D="${1:-/}"
[ -d "$D/etc" ] || { echo "no such install root: $D"; exit 1; }

mkdir -p "$D/etc/sysctl.d" "$D/usr/lib/synthex" \
         "$D/usr/lib/systemd/system" "$D/usr/bin"

cp sysctl.d/00-synthex-vm.conf      "$D/etc/sysctl.d/"
cp sysctl.d/00-synthex-network.conf "$D/etc/sysctl.d/"
cp gamemode.ini                     "$D/etc/gamemode.ini"
cp zram-setup                       "$D/usr/lib/synthex/"
cp zram.service                     "$D/usr/lib/systemd/system/synthex-zram.service"
install -m 0755 synthex-gov         "$D/usr/bin/synthex-gov"
install -m 0755 synthex-game-session "$D/usr/bin/synthex-game-session"

if command -v systemctl >/dev/null 2>&1; then
    systemctl --root "$D" enable synthex-zram.service 2>/dev/null || true
fi
echo "Synthex performance files installed to $D"
