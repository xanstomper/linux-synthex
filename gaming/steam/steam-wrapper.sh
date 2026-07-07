#!/usr/bin/env bash
# ============================================================
# SynthOS — Steam Launcher Wrapper
# /usr/bin/steam-wrapper
#
# Wraps Steam (or a Steam game) with Gamescope and/or
# Gamemode, applies per-game environment variables, and
# provides HDR/FSR support.
#
# Part of synthex-steam-optimizer package.
# ============================================================

set -euo pipefail

# --- Default configuration ---
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/synthex-gaming-center"
GAME_PROFILES="${CONFIG_DIR}/games"
DEFAULT_CONFIG="${CONFIG_DIR}/steam-wrapper.conf"

# ============================================================
# CONFIGURATION LOADING
# ============================================================

load_config() {
    # Load system-wide defaults
    [[ -f "/etc/default/steam-wrapper" ]] && source "/etc/default/steam-wrapper"
    
    # Load user config
    [[ -f "$DEFAULT_CONFIG" ]] && source "$DEFAULT_CONFIG"
    
    # Apply defaults for unset variables
    : "${GAMESCOPE_ENABLED:=auto}"
    : "${GAMEMODE_ENABLED:=1}"
    : "${HDR_ENABLED:=auto}"
    : "${FSR_ENABLED:=auto}"
    : "${FSR_STRENGTH:=2}"
    : "${SCALING_MODE:=auto}"
    : "${FPS_LIMIT:=0}"
    : "${ADAPTIVE_SYNC:=auto}"
    : "${RES_WIDTH:=0}"
    : "${RES_HEIGHT:=0}"
    : "${REFRESH_RATE:=0}"
    : "${GAME_ID:=}"
}

# ============================================================
# GAME PROFILE LOOKUP
# ============================================================

load_game_profile() {
    local app_id="$1"
    local profile_file="${GAME_PROFILES}/${app_id}.conf"
    
    [[ -f "$profile_file" ]] || return 0
    
    source "$profile_file"
    log "Loaded profile for game: ${GAME_NAME:-$app_id}"
}

# ============================================================
# ENVIRONMENT VARIABLE SETUP
# ============================================================

setup_env() {
    # ==========================================================
    # General Wine/Proton environment
    # ==========================================================
    export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-}"
    export WINEDEBUG="${WINEDEBUG:-fixme-all}"
    
    # Enable fsync (fast synchronization)
    export WINEFSYNC="${WINEFSYNC:-1}"
    
    # Enable futex2 if kernel supports it
    if [[ -f "/proc/sys/kernel/futex2" ]] || grep -q "futex2" /proc/config.gz 2>/dev/null; then
        export WINEFSYNC_FUTEX2="${WINEFSYNC_FUTEX2:-1}"
    fi
    
    # ==========================================================
    # DXVK environment
    # ==========================================================
    export DXVK_ENABLE_STATE_CACHE="${DXVK_ENABLE_STATE_CACHE:-1}"
    export DXVK_STATE_CACHE_PATH="${DXVK_STATE_CACHE_PATH:-$HOME/.cache/dxvk-state-cache}"
    export DXVK_ASYNC="${DXVK_ASYNC:-0}"   # Async compile disabled by default (can cause glitches)
    export DXVK_HUD="${DXVK_HUD:-0}"
    
    # ==========================================================
    # VKD3D-Proton environment
    # ==========================================================
    export VKD3D_CONFIG="${VKD3D_CONFIG:-}"
    export VKD3D_DEBUG="${VKD3D_DEBUG:-none}"
    
    # ==========================================================
    # Mesa/RADV environment
    # ==========================================================
    export MESA_SHADER_CACHE_DIR="${MESA_SHADER_CACHE_DIR:-$HOME/.cache/mesa_shader_cache_db}"
    export MESA_SHADER_CACHE_SIZE="${MESA_SHADER_CACHE_SIZE:-4096}"
    export RADV_PERFTEST="${RADV_PERFTEST:-sam}"
    
    # ==========================================================
    # NVIDIA environment
    # ==========================================================
    if lsmod | grep -q "^nvidia " 2>/dev/null; then
        export __GL_SHADER_DISK_CACHE="${__GL_SHADER_DISK_CACHE:-1}"
        export __GL_SHADER_DISK_CACHE_PATH="${__GL_SHADER_DISK_CACHE_PATH:-$HOME/.cache/nvidia-shader-cache}"
        export __GL_SHADER_DISK_CACHE_SIZE="${__GL_SHADER_DISK_CACHE_SIZE:-4294967296}"
        export __GL_THREADED_OPTIMIZATIONS="${__GL_THREADED_OPTIMIZATIONS:-1}"
        export __GL_MaxFramesAllowed="${__GL_MaxFramesAllowed:-1}"
    fi
    
    # ==========================================================
    # MangoHUD environment
    # ==========================================================
    export MANGOHUD="${MANGOHUD:-0}"
    export MANGOHUD_CONFIG="${MANGOHUD_CONFIG:-}"
    export MANGOHUD_DLSYM="${MANGOHUD_DLSYM:-1}"
    
    # ==========================================================
    # Gamescope-related environment
    # ==========================================================
    export GAMESCOPE_WAYLAND="${GAMESCOPE_WAYLAND:-1}"
    export GAMESCOPE_FSR_DEBUG="${GAMESCOPE_FSR_DEBUG:-0}"
    
    # ==========================================================
    # SDL/Input environment
    # ==========================================================
    export SDL_JOYSTICK_HIDAPI="${SDL_JOYSTICK_HIDAPI:-1}"
    export SDL_GAMECONTROLLERCONFIG="${SDL_GAMECONTROLLERCONFIG:-}"
    export SDL_MOUSE_RELATIVE_SCALING="${SDL_MOUSE_RELATIVE_SCALING:-0}"
    
    # ==========================================================
    # General performance environment
    # ==========================================================
    export OMP_NUM_THREADS="${OMP_NUM_THREADS:-$(nproc)}"
    export PULSE_LATENCY_MSEC="${PULSE_LATENCY_MSEC:-60}"
    export PIPEWIRE_LATENCY="${PIPEWIRE_LATENCY:-256/48000}"
    
    # ==========================================================
    # Per-game overrides from profile
    # ==========================================================
    if [[ -n "${GAME_ENV:-}" ]]; then
        # GAME_ENV is a semicolon-delimited list of KEY=VALUE pairs
        local IFS=';'
        for pair in $GAME_ENV; do
            export "$pair" 2>/dev/null || true
        done
    fi
}

# ============================================================
# GAMESCOPE LAUNCH
# ============================================================

build_gamescope_cmd() {
    local width="${RES_WIDTH:-0}"
    local height="${RES_HEIGHT:-0}"
    local refresh="${REFRESH_RATE:-0}"
    
    # Auto-detect display resolution if not specified
    if [[ "$width" -eq 0 ]] || [[ "$height" -eq 0 ]]; then
        if command -v wlr-randr &>/dev/null; then
            # Wayland
            local mode
            mode=$(wlr-randr 2>/dev/null | grep -A1 "current mode" | head -1 | awk '{print $3}' || true)
            if [[ -n "$mode" ]]; then
                width="${mode%%x*}"
                height="${mode#*x}"
                height="${height%% *}"
            fi
        elif [[ -n "$DISPLAY" ]] && command -v xrandr &>/dev/null; then
            # X11
            local mode
            mode=$(xrandr 2>/dev/null | grep '*' | head -1 | awk '{print $1}' || true)
            if [[ -n "$mode" ]]; then
                width="${mode%%x*}"
                height="${mode#*x}"
            fi
        fi
    fi
    
    # Fall back to common resolution
    [[ "$width" -eq 0 ]] && width=1920
    [[ "$height" -eq 0 ]] && height=1080
    [[ "$refresh" -eq 0 ]] && refresh=60
    
    local cmd="gamescope"
    cmd+=" -W ${width} -H ${height}"
    cmd+=" -r ${refresh}"
    
    # Gamescope flags
    [[ "$FSR_ENABLED" == "1" ]] || [[ "$FSR_ENABLED" == "auto" ]] && cmd+=" -F fsr --fsr-filter-strength ${FSR_STRENGTH}"
    [[ "$HDR_ENABLED" == "1" ]] && cmd+=" --hdr-enabled"
    [[ "$ADAPTIVE_SYNC" == "1" ]] && cmd+=" --adaptive-sync"
    [[ "$FPS_LIMIT" -gt 0 ]] && cmd+=" --fps-limit ${FPS_LIMIT}"
    
    # Expose Wayland to the game (enables native Wayland support in some games)
    cmd+=" --expose-wayland"
    
    # NIS (NVIDIA Image Scaling) as alternative to FSR
    if [[ "${SCALING_MODE}" == "nis" ]]; then
        cmd+=" -F nis"
    fi
    
    echo "$cmd"
}

# ============================================================
# LAUNCH LOGIC
# ============================================================

launch_steam() {
    local use_gamescope=0
    local use_gamemode=0
    local game_appid=""
    local extra_args=()
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --gamescope)  use_gamescope=1 ;;
            --gamemode)   use_gamemode=1 ;;
            --hdr)        HDR_ENABLED=1 ;;
            --fsr)        FSR_ENABLED=1 ;;
            --no-hdr)     HDR_ENABLED=0 ;;
            --no-fsr)     FSR_ENABLED=0 ;;
            --fps=*)      FPS_LIMIT="${1#*=}" ;;
            --res=*)      RES_WIDTH="${1#*=}"; RES_HEIGHT="${2#*=}"; shift ;;
            --game=*)     game_appid="${1#*=}" ;;
            --appid=*)    game_appid="${1#*=}" ;;
            *)
                extra_args+=("$1")
                ;;
        esac
        shift
    done
    
    # Load game profile if appid provided
    if [[ -n "$game_appid" ]]; then
        load_game_profile "$game_appid"
    fi
    
    # Auto-detect gamescope if enabled=auto
    if [[ "$use_gamescope" -eq 0 ]] && [[ "$GAMESCOPE_ENABLED" == "auto" ]]; then
        # Auto-enable gamescope if running under Wayland
        if [[ -n "$WAYLAND_DISPLAY" ]]; then
            use_gamescope=1
        fi
    elif [[ "$GAMESCOPE_ENABLED" == "1" ]]; then
        use_gamescope=1
    fi
    
    # Auto-detect gamemode
    if [[ "$use_gamemode" -eq 0 ]] && [[ "$GAMEMODE_ENABLED" == "1" ]]; then
        use_gamemode=1
    fi
    
    # Setup environment
    setup_env
    
    # Build the launch command
    local launch_cmd=""
    
    if [[ "$use_gamemode" -eq 1 ]] && command -v gamemoderun &>/dev/null; then
        launch_cmd+="gamemoderun "
    fi
    
    if [[ "$use_gamescope" -eq 1 ]] && command -v gamescope &>/dev/null; then
        local gs_cmd
        gs_cmd=$(build_gamescope_cmd)
        launch_cmd+="${gs_cmd} -- "
    fi
    
    # If we're running a specific game via steam:// URL
    if [[ -n "$game_appid" ]]; then
        launch_cmd+="steam -silent -nofriendsui -no-browser steam://rungameid/${game_appid}"
    else
        launch_cmd+="steam ${extra_args[*]}"
    fi
    
    log "Launching: ${launch_cmd}"
    eval "exec ${launch_cmd}"
}

# ============================================================
# COMMAND LINE PARSING
# ============================================================

usage() {
    cat << EOF
Synthex Steam Wrapper — Launch Steam (or games) with optimized settings

USAGE:
  steam-wrapper [options] [-- steam-args...]
  steam-wrapper --game=<appid> [options]

OPTIONS:
  --gamescope       Force launch inside Gamescope
  --gamemode        Enable Feral Gamemode
  --hdr             Enable HDR output (via Gamescope)
  --no-hdr          Disable HDR output
  --fsr             Enable FSR upscaling (via Gamescope)
  --no-fsr          Disable FSR upscaling
  --fps=N           Limit frame rate to N fps
  --res=WxH         Set resolution (e.g., 1920x1080)
  --game=APPID      Launch specific Steam game by AppID
  --appid=APPID     Same as --game
  -h, --help        Show this help

CONFIGURATION:
  System-wide:  /etc/default/steam-wrapper
  User config:  ~/.config/synthex-gaming-center/steam-wrapper.conf
  Game configs: ~/.config/synthex-gaming-center/games/<appid>.conf

EXAMPLES:
  steam-wrapper                                           # Launch Steam
  steam-wrapper --gamescope --gamemode                    # Steam in Gamescope + Gamemode
  steam-wrapper --game=730                                # Launch CS2 with auto-settings
  steam-wrapper --gamescope --hdr --fsr --game=1551360    # Forza Horizon 5 with HDR + FSR
EOF
}

main() {
    load_config
    
    case "${1:-}" in
        -h|--help|help)
            usage
            exit 0
            ;;
        *)
            launch_steam "$@"
            ;;
    esac
}

main "$@"
