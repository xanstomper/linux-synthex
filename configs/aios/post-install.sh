#!/usr/bin/env bash
# %post snippet: wire the SynthOS differentiators into the installed image.
# Paste this into the kickstart %post (or run inside the buildroot).
set -uo pipefail
PREFIX="${1:-/}"

# 1) AI console + first-boot defaults
/usr/share/synthex/aios/install.sh "$PREFIX" 2>/dev/null || true
systemctl --root "$PREFIX" enable \
    synthex-defaults.service \
    synthex-zram.service \
    2>/dev/null || true

# 2) Predictive launch on by default (the "OS knows you" feature)
systemctl --root "$PREFIX" enable \
    synthex-predictive.service \
    synthex-predictive-launch.service 2>/dev/null || true

# 3) Snapshot/rollback before updates — unbreakable-updates story
#    (btrfs + snapper; enables timeline snapshots)
if [ -x "$PREFIX/sbin/snapper" ] || command -v snapper >/dev/null; then
    systemctl --root "$PREFIX" enable \
        snapper-timeline.timer \
        btrfs-scrub@-.timer \
        fstrim.timer 2>/dev/null || true
    snapper -c root create --description "synthos-default" 2>/dev/null || true
fi

# 4) Performance/gaming defaults (the files in configs/performance)
for p in 00-synthex-vm.conf 00-synthex-network.conf; do
    if [ -f "$PREFIX/etc/sysctl.d/$p" ]; then
        printf '  sysctl.d/%s applied on boot\n' "$p"
    fi
done

echo "SynthOS %post: differentiators enabled (best-effort)"
exit 0