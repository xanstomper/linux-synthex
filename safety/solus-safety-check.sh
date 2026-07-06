#!/usr/bin/env bash
#===============================================================================
# solus-safety-check — post-boot health check; clears the boot-failure counter
# Writes /var/lib/solus/safety-report.json. Run via solus-safety.service after
# the system reaches multi-user.target (i.e. boot succeeded).
#===============================================================================
set -euo pipefail

STATE_DIR="/var/lib/solus"
COUNTER="$STATE_DIR/boot-counter"
MARKER="$STATE_DIR/.boot-counted"
REPORT="$STATE_DIR/safety-report.json"

log() { echo "[solus-safety] $*"; }

mkdir -p "$STATE_DIR" 2>/dev/null || true

# Boot succeeded — clear the failure counter set by the recovery/initramfs hook.
boot_cleared=false
if [[ -f "$COUNTER" ]]; then
    echo 0 > "$COUNTER" 2>/dev/null || true
    rm -f "$MARKER" 2>/dev/null || true
    boot_cleared=true
    log "boot-failure counter cleared"
fi

ts="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Failed systemd units
failed_json="$(systemctl --failed --no-legend --plain list-units 2>/dev/null \
    | awk '{print $1}' | sed 's/.*/"&"/' | paste -sd, -)"
[[ -z "$failed_json" ]] && failed_json="[]"
failed_json="[$failed_json]"

# Dependency consistency (dnf5 check verifies the rpmdb is solvable)
dep="unknown"
if command -v dnf5 &>/dev/null; then
    dnf5 -q check &>/dev/null && dep="ok" || dep="broken"
elif command -v dnf &>/dev/null; then
    dnf -q check &>/dev/null && dep="ok" || dep="broken"
fi

# Kernel + matching initramfs presence
kver="$(ls -1 /boot/vmlinuz-* 2>/dev/null | sort -V | tail -1 || true)"
initramfs_ok=false
if [[ -n "$kver" ]]; then
    kver="${kver#/boot/vmlinuz-}"
    [[ -f "/boot/initramfs-${kver}.img" ]] && initramfs_ok=true
else
    kver="none"
fi

# BTRFS device error counters (sum of all error counters on root)
btrfs_err=0
if findmnt -n -o FSTYPE / 2>/dev/null | grep -q btrfs; then
    btrfs_err="$(btrfs device stats / 2>/dev/null | awk -F'[^0-9]+' '{s+=$NF} END{print s+0}')"
fi

# Root filesystem usage
disk_pct="$(df -P / 2>/dev/null | awk 'NR==2{gsub(/%/,""); print $5+0}')"
disk_pct="${disk_pct:-0}"

# Human-readable issues
issues=()
[[ "$failed_json" != "[]" ]] && issues+=("failed systemd units present")
[[ "$dep" == "broken" ]] && issues+=("package dependency check failed")
[[ "$initramfs_ok" == false ]] && issues+=("initramfs missing for current kernel")
[[ "$btrfs_err" -gt 0 ]] && issues+=("btrfs device errors: $btrfs_err")
[[ "$disk_pct" -ge 95 ]] && issues+=("root filesystem >=95% full")

if [[ ${#issues[@]} -eq 0 ]]; then
    issues_json="[]"
else
    issues_json="$(printf '%s\n' "${issues[@]}" | sed 's/.*/"&"/' | paste -sd, -)"
    issues_json="[$issues_json]"
fi

if [[ "$failed_json" == "[]" && "$dep" == "ok" && "$initramfs_ok" == true \
      && "$btrfs_err" -eq 0 && "$disk_pct" -lt 95 ]]; then
    status="healthy"
else
    status="degraded"
fi

cat > "$REPORT" <<EOF
{
  "timestamp": "$ts",
  "status": "$status",
  "boot_counter_cleared": $boot_cleared,
  "failed_units": $failed_json,
  "dependencies": "$dep",
  "kernel": "$kver",
  "initramfs_present": $initramfs_ok,
  "btrfs_device_errors": $btrfs_err,
  "root_disk_used_pct": $disk_pct,
  "issues": $issues_json
}
EOF

log "health report written to $REPORT (status=$status)"
exit 0
