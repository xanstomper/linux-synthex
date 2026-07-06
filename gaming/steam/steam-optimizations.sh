#!/usr/bin/env bash
# ============================================================
# Solus Linux — Steam System Optimizations
# /usr/share/solus-gaming/steam-optimizations.sh
#
# Applies system-level tuning when Steam is running.
# Called by systemd service or steam-wrapper.sh.
# Part of solus-steam-optimizer package.
# ============================================================

set -euo pipefail

# --- Configuration ---
OPTIMIZATIONS_FILE="/etc/default/steam-optimizations"
STATE_DIR="/var/lib/solus-steam-optimizer"
PIDFILE="${STATE_DIR}/steam.pid"

# --- Source user config if present ---
[[ -f "$OPTIMIZATIONS_FILE" ]] && source "$OPTIMIZATIONS_FILE"

# --- Defaults (overridable in config) ---
: "${CPU_GOVERNOR:=performance}"
: "${INOTIFY_MAX_USER_WATCHES:=524288}"
: "${VM_MAX_MAP_COUNT:=16777216}"
: "${SCHED_PRIORITY:=1}"
: "${ENABLE_SCHEDTOOL:=1}"
: "${ENABLE_PRELOAD:=1}"
: "${ENABLE_TCP_TUNING:=1}"
: "${ENABLE_WATCHDOG:=0}"
: "${ENABLE_SPLIT_LOCK:=0}"
: "${ENABLE_CSTATE:=1}"
: "${CSTATE_LIMIT:=1}"

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

log()    { echo "[$(date +'%H:%M:%S')] $*"; }
warn()   { echo "[WARN] $*" >&2; }
ensure_state_dir() { mkdir -p "$STATE_DIR"; }

save_originals() {
    local tag="${1:-default}"
    local file="$2"
    local value="$3"
    ensure_state_dir
    echo "$value" > "${STATE_DIR}/orig_${tag}_$(echo "$file" | tr '/' '_')"
}

restore_originals() {
    for f in "${STATE_DIR}/orig_"*; do
        [[ -f "$f" ]] || continue
        local file="${f#*orig_}"
        file="${file#*_}"
        file="/${file//_//}"
        local value
        value=$(cat "$f")
        echo "$value" > "$file" 2>/dev/null || true
        rm -f "$f"
    done
}

# ============================================================
# CPU GOVERNOR
# ============================================================

set_cpu_governor() {
    local governor="$1"
    log "Setting CPU governor to: ${governor}"
    
    for cpu_gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        [[ -f "$cpu_gov" ]] || continue
        local current
        current=$(cat "$cpu_gov" 2>/dev/null || echo "")
        if [[ -n "$current" ]]; then
            save_originals "governor" "$cpu_gov" "$current"
            echo "$governor" > "$cpu_gov" 2>/dev/null || warn "Failed to set governor for $cpu_gov"
        fi
    done
}

# ============================================================
# SCHEDULER / PRIORITY
# ============================================================

set_sched_priority() {
    log "Setting Steam to SCHED_BATCH / low priority class..."
    
    local steam_pid
    steam_pid=$(pidof steam 2>/dev/null || true)
    if [[ -n "$steam_pid" ]]; then
        # Move Steam process to low-priority batch scheduling
        # (keeps Steam responsive without interfering with game processes)
        schedtool -B -p 0 "$steam_pid" 2>/dev/null || true
    fi
    
    # Set game process scheduling via gamemode integration
    # (gamemoded handles renice and IO priority for child processes)
    if pidof gamemoded >/dev/null 2>&1; then
        log "Gamemode daemon is running — will handle game process scheduling."
    fi
}

# ============================================================
# KERNEL PARAMETERS
# ============================================================

bump_inotify_watches() {
    local limit="$1"
    local current
    current=$(cat /proc/sys/fs/inotify/max_user_watches 2>/dev/null || echo "0")
    
    if [[ "$current" -lt "$limit" ]]; then
        log "Increasing inotify max_user_watches: ${current} → ${limit}"
        save_originals "inotify" "/proc/sys/fs/inotify/max_user_watches" "$current"
        echo "$limit" > /proc/sys/fs/inotify/max_user_watches 2>/dev/null
    fi
}

bump_max_map_count() {
    local limit="$1"
    local current
    current=$(cat /proc/sys/vm/max_map_count 2>/dev/null || echo "0")
    
    if [[ "$current" -lt "$limit" ]]; then
        log "Increasing vm.max_map_count: ${current} → ${limit}"
        save_originals "max_map" "/proc/sys/vm/max_map_count" "$current"
        echo "$limit" > /proc/sys/vm/max_map_count 2>/dev/null
    fi
}

# ============================================================
# TCP / NETWORK TUNING (for Steam downloads)
# ============================================================

tune_network() {
    log "Tuning network for Steam downloads..."
    
    # Use BBR congestion control if available
    local tcp_avail
    tcp_avail=$(cat /proc/sys/net/ipv4/tcp_available_congestion_control 2>/dev/null || echo "")
    if echo "$tcp_avail" | grep -q "bbr"; then
        local current_cc
        current_cc=$(cat /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null || echo "")
        if [[ "$current_cc" != "bbr" ]]; then
            save_originals "tcp_cc" "/proc/sys/net/ipv4/tcp_congestion_control" "$current_cc"
            echo "bbr" > /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null
            log "  TCP congestion control: bbr"
        fi
    fi
    
    # Use fq (fair queue) qdisc for BBR
    local current_qdisc
    current_qdisc=$(cat /proc/sys/net/core/default_qdisc 2>/dev/null || echo "")
    if [[ "$current_qdisc" != "fq" ]]; then
        save_originals "qdisc" "/proc/sys/net/core/default_qdisc" "$current_qdisc"
        echo "fq" > /proc/sys/net/core/default_qdisc 2>/dev/null
        log "  Default qdisc: fq"
    fi
    
    # Increase TCP buffer sizes for faster downloads
    local tcp_rmem=("4096" "131072" "6291456")
    local current_rmem
    current_rmem=$(cat /proc/sys/net/ipv4/tcp_rmem 2>/dev/null || echo "")
    if [[ "$current_rmem" != "${tcp_rmem[*]}" ]]; then
        save_originals "tcp_rmem" "/proc/sys/net/ipv4/tcp_rmem" "$current_rmem"
        echo "${tcp_rmem[*]}" > /proc/sys/net/ipv4/tcp_rmem 2>/dev/null
        log "  TCP read buffers: ${tcp_rmem[*]}"
    fi
    
    local tcp_wmem=("4096" "65536" "6291456")
    local current_wmem
    current_wmem=$(cat /proc/sys/net/ipv4/tcp_wmem 2>/dev/null || echo "")
    if [[ "$current_wmem" != "${tcp_wmem[*]}" ]]; then
        save_originals "tcp_wmem" "/proc/sys/net/ipv4/tcp_wmem" "$current_wmem"
        echo "${tcp_wmem[*]}" > /proc/sys/net/ipv4/tcp_wmem 2>/dev/null
        log "  TCP write buffers: ${tcp_wmem[*]}"
    fi
}

# ============================================================
# C-STATE LIMITING
# ============================================================

limit_cstates() {
    local limit="$1"
    log "Limiting CPU C-states to C${limit}..."
    
    # Write to intel_idle.max_cstate if available
    local current_intel
    current_intel=$(cat /sys/module/intel_idle/parameters/max_cstate 2>/dev/null || echo "")
    if [[ -n "$current_intel" ]]; then
        save_originals "intel_cstate" "/sys/module/intel_idle/parameters/max_cstate" "$current_intel"
        echo "$limit" > /sys/module/intel_idle/parameters/max_cstate 2>/dev/null || true
    fi
    
    # Write to processor.max_cstate
    local current_proc
    current_proc=$(cat /sys/module/processor/parameters/max_cstate 2>/dev/null || echo "")
    if [[ -n "$current_proc" ]]; then
        save_originals "proc_cstate" "/sys/module/processor/parameters/max_cstate" "$current_proc"
        echo "$limit" > /sys/module/processor/parameters/max_cstate 2>/dev/null || true
    fi
    
    # Disable specific C-states via sysfs
    for cstate_dir in /sys/devices/system/cpu/cpu*/cpuidle/state*/disable; do
        [[ -f "$cstate_dir" ]] || continue
        local state_path="${cstate_dir%/disable}"
        local state_name
        state_name=$(cat "${state_path}/name" 2>/dev/null || echo "")
        if [[ "$state_name" =~ ^C[2-9] ]]; then
            echo "1" > "$cstate_dir" 2>/dev/null || true
        fi
    done
}

# ============================================================
# PRELOAD DAEMON
# ============================================================

ensure_preload() {
    if command -v preload &>/dev/null; then
        if ! pidof preload &>/dev/null; then
            log "Starting preload daemon..."
            systemctl start preload 2>/dev/null || \
                service preload start 2>/dev/null || true
        fi
        log "Preload daemon running — Steam and game binaries will be cached."
    fi
}

# ============================================================
# LATENCY OPTIMIZATIONS
# ============================================================

tune_latency() {
    log "Applying latency optimizations..."
    
    # Disable NMI watchdog (frees CPU time)
    if [[ "$ENABLE_WATCHDOG" -eq 0 ]]; then
        local current_nmi
        current_nmi=$(cat /proc/sys/kernel/nmi_watchdog 2>/dev/null || echo "1")
        if [[ "$current_nmi" != "0" ]]; then
            save_originals "nmi" "/proc/sys/kernel/nmi_watchdog" "$current_nmi"
            echo "0" > /proc/sys/kernel/nmi_watchdog 2>/dev/null || true
            log "  NMI watchdog disabled"
        fi
    fi
    
    # Disable split-lock mitigation (can improve throughput in some games)
    if [[ "$ENABLE_SPLIT_LOCK" -eq 0 ]]; then
        local current_split
        current_split=$(cat /proc/sys/kernel/split_lock_mitigate 2>/dev/null || echo "1")
        if [[ "$current_split" != "0" ]]; then
            save_originals "splitlock" "/proc/sys/kernel/split_lock_mitigate" "$current_split"
            echo "0" > /proc/sys/kernel/split_lock_mitigate 2>/dev/null || true
            log "  Split-lock mitigation disabled"
        fi
    fi
    
    # Set timer slack (lower = more precise but more wakeups)
    # Only affects the Steam process itself
    local steam_pid
    steam_pid=$(pidof steam 2>/dev/null || true)
    if [[ -n "$steam_pid" ]]; then
        # Reduce timer slack to 50ns for Steam process
        echo "50" > "/proc/${steam_pid}/timerslack_ns" 2>/dev/null || true
    fi
}

# ============================================================
# SHADER CACHE BOOTSTRAP
# ============================================================

setup_shader_cache() {
    log "Setting up shader cache directories..."
    
    # Ensure common shader cache dirs exist
    mkdir -p "$HOME/.cache/mesa_shader_cache_db" 2>/dev/null || true
    mkdir -p "$HOME/.cache/nvidia-shader-cache" 2>/dev/null || true
    mkdir -p "$HOME/.cache/dxvk-state-cache" 2>/dev/null || true
    
    # Set environment for Steam (will be used by launched games)
    export MESA_SHADER_CACHE_DIR="$HOME/.cache/mesa_shader_cache_db"
    export MESA_SHADER_CACHE_SIZE=4096
    export __GL_SHADER_DISK_CACHE_PATH="$HOME/.cache/nvidia-shader-cache"
    export __GL_SHADER_DISK_CACHE_SIZE=4294967296
    export DXVK_STATE_CACHE_PATH="$HOME/.cache/dxvk-state-cache"
    export DXVK_ENABLE_STATE_CACHE=1
    
    log "Shader cache directories ready."
}

# ============================================================
# APPLY / REVERT
# ============================================================

apply_optimizations() {
    log "Applying Steam optimizations..."
    
    set_cpu_governor "$CPU_GOVERNOR"
    bump_inotify_watches "$INOTIFY_MAX_USER_WATCHES"
    bump_max_map_count "$VM_MAX_MAP_COUNT"
    tune_network
    tune_latency
    setup_shader_cache
    
    [[ "$ENABLE_CSTATE" -eq 1 ]] && limit_cstates "$CSTATE_LIMIT"
    [[ "$ENABLE_PRELOAD" -eq 1 ]] && ensure_preload
    [[ "$ENABLE_SCHEDTOOL" -eq 1 ]] && set_sched_priority
    
    log "Optimizations applied."
}

revert_optimizations() {
    log "Reverting Steam optimizations..."
    restore_originals
    log "Optimizations reverted."
}

# ============================================================
# WATCH FOR STEAM PROCESS
# ============================================================

watch_steam() {
    log "Watching for Steam process..."
    apply_optimizations
    
    # Wait for Steam to exit
    while pidof steam >/dev/null 2>&1; do
        sleep 30
    done
    
    log "Steam has exited."
    revert_optimizations
}

# ============================================================
# MAIN
# ============================================================

usage() {
    cat << EOF
Solus Steam Optimizations — System tuning for Steam gaming

USAGE:
  steam-optimizations.sh [command]

COMMANDS:
  apply      Apply optimizations immediately
  revert     Revert all optimizations
  watch      Apply optimizations and watch for Steam process
             (automatically reverts when Steam exits)
  help       Show this help

EOF
}

main() {
    local cmd="${1:-apply}"
    
    # Check if running as root for sysctl parameters
    if [[ $EUID -ne 0 ]]; then
        warn "Some optimizations require root (CPU governor, sysctl)."
        warn "Run with sudo for full effect."
    fi
    
    case "$cmd" in
        apply)   apply_optimizations ;;
        revert)  revert_optimizations ;;
        watch)   watch_steam ;;
        help|--help|-h) usage ;;
        *)       warn "Unknown command: $cmd"; usage; exit 1 ;;
    esac
}

main "$@"
