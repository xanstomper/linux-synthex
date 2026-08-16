#!/usr/bin/env bash
# Bake the SynthOS AI + first-boot-differentiators layer into an image root.
# Usage: ./install.sh [installroot]   (default: /)
set -e
D="${1:-/}"  # image root (e.g. /root from livecd-creator, or "/" for live)
[ -d "$D/etc" ] || { echo "no such install root: $D"; exit 1; }

mkdir -p "$D/usr/bin" "$D/usr/sbin" "$D/usr/lib/systemd/system" "$D/etc/snapper/configs"

install -m 0755 synthex                    "$D/usr/bin/synthex"
install -m 0755 synthex-defaults           "$D/usr/sbin/synthex-defaults"
install -m 0644 synthex-defaults.service   "$D/usr/lib/systemd/system/synthex-defaults.service"

# ensure daemon units the OS ships are present to be enabled by synthex-defaults
for u in synthex-brain synthex-hermes synthex-predictive synthex-predictive-launch \
         synthex-snapshot synthex-zram; do
  : # (units come from their own RPMs; not created here)
done

# a starter snapper btrfs config for / (if btrfs)
cat > "$D/etc/snapper/configs/root" <<'SN'
SUBVOLUME="/"
FSTYPE=btrfs
TIMELINE_CREATE="yes"
NUMBER_CLEANUP="yes"
TIMELINE_LIMIT_DAILY="5"
TIMELINE_LIMIT_WEEKLY="0"
SN

echo "AI-SynthOS layer installed to $D"
echo "  usr/bin/synthex            (assistant console)"
echo "  usr/sbin/synthex-defaults  (first-boot enabler)"
echo "  usr/lib/.../synthex-defaults.service"