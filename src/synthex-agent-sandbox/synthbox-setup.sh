#!/usr/bin/env bash
# synthex-synthbox-sandbox setup script
# Creates required cgroup directories, device allow lists, and
# bwrap bind-mount base trees used by the agent sandbox daemon.
set -euo pipefail

SANDBOX_RUNTIME=/var/lib/synthex/agent-sandbox
LOG=/var/log/synthex/synthbox-setup.log
mkdir -p "$(dirname "$LOG")"
exec >> "$LOG" 2>&1

echo "$(date -Iseconds) [synthbox-setup] starting"

# ── 1. State directories ──────────────────────────────────────────────────────
mkdir -p \
    "$SANDBOX_RUNTIME/overlays" \
    "$SANDBOX_RUNTIME/workspaces" \
    "$SANDBOX_RUNTIME/sockets"   \
    /run/synthex/agent-sandbox   \
    /var/log/synthex/agent-sandbox

chmod 0750 "$SANDBOX_RUNTIME" /run/synthex/agent-sandbox

# ── 2. cgroup v2 sandbox sub-hierarchy ───────────────────────────────────────
CGROUP_SYNTHEX=/sys/fs/cgroup/synthex-agents
if [ -d /sys/fs/cgroup ] && ! [ -d "$CGROUP_SYNTHEX" ]; then
    mkdir -p "$CGROUP_SYNTHEX"
    # Allow the daemon user (synthex-agent) to manage this sub-tree
    chown synthex-agent:synthex-agent "$CGROUP_SYNTHEX" 2>/dev/null || true
fi

# ── 3. Seccomp BPF policy cache directory ────────────────────────────────────
mkdir -p /var/cache/synthex/seccomp-bpf
chmod 0750 /var/cache/synthex/seccomp-bpf

# ── 4. Verify bubblewrap is present ──────────────────────────────────────────
if ! command -v bwrap &>/dev/null; then
    echo "$(date -Iseconds) [synthbox-setup] WARNING: bwrap not found; sandboxes will use namespace-only isolation"
fi

echo "$(date -Iseconds) [synthbox-setup] complete"
