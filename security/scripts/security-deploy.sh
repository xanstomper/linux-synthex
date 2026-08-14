#!/usr/bin/env bash
# SynthOS security-deploy — apply the selected hardening profile (real ops)
# Usage: security-deploy.sh [balanced|gaming|powersave]
set -euo pipefail
PROFILE="${1:-balanced}"
BASE=/usr/share/synthex/security/hardening
[ -f "$BASE/sysctl-$PROFILE.conf" ] && SRC="$BASE/sysctl-$PROFILE.conf" || SRC="$BASE/sysctl.conf"
echo "[synthex-security] applying sysctl profile: $SRC"
sysctl -p "$SRC"
echo "[synthex-security] installing auditd rules"
install -Dm0640 "$BASE/auditd.rules" /etc/audit/rules.d/99-synthex.rules
augenrules --load 2>/dev/null || systemctl reload auditd 2>/dev/null || true
echo "[synthex-security] installing limits"
install -Dm0644 "$BASE/limits.conf" /etc/security/limits.d/99-synthex.conf
echo "[synthex-security] enabling AppArmor profiles (if present)"
if [ -d /etc/apparmor.d ] && command -v apparmor_parser >/dev/null; then
    for p in /etc/apparmor.d/usr.bin.synthex-*; do
        [ -f "$p" ] && apparmor_parser -r -W "$p" || true
    done
fi
echo "[synthex-security] done."
