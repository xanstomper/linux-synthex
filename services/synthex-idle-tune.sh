#!/usr/bin/env bash
# Synthex Idle Tune — reduce footprint after boot.
# Stops file indexers if unwanted, drops caches once, disables THP defrag.
set -euo pipefail

LOG="/var/log/synthex-idle.log"
mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

[[ $EUID -eq 0 ]] || { log "must run as root"; exit 1; }

log "═══ Synthex Idle Tune ═══"

# Stop file indexers (tracker/baloo) for the active user sessions
for user in $(loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'); do
    uid=$(id -u "$user" 2>/dev/null || continue)
    for svc in tracker-miner-fs-3.service tracker-miner-rss-3.service baloo-file.service; do
        systemctl --user -M "${user}@.host" stop "$svc" 2>/dev/null || \
        XDG_RUNTIME_DIR=/run/user/$uid systemctl --user -M "${user}@" stop "$svc" 2>/dev/null || true
    done
done
log "file indexers stopped for user sessions"

# Disable transparent hugepages defrag (reduces latency spikes)
if [ -w /sys/kernel/mm/transparent_hugepage/khugepaged_defrag ]; then
    echo 0 > /sys/kernel/mm/transparent_hugepage/khugepaged_defrag 2>/dev/null || true
    log "THP khugepaged defrag disabled"
fi
if [ -w /sys/kernel/mm/transparent_hugepage/defrag ]; then
    echo madvise > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true
    log "THP defrag set to madvise"
fi

# One-time cache drop after boot settles (frees page cache, keeps dentries/inodes)
echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
log "page cache dropped (one-time)"

# Swappiness already set by 99-synthex-performance.conf; reaffirm
sysctl -w vm.swappiness=10 2>/dev/null || true

log "done"
