#!/usr/bin/env bash
#===============================================================================
# Synthex Workspace Engine — System Mode Switcher
#===============================================================================
# CLI tool to switch the entire system between performance modes:
#   synthex-workspace set <mode>   — Apply a workspace mode
#   synthex-workspace status       — Show current mode
#   synthex-workspace list         — List available modes
#
# Modes:
#   gaming    — max performance, compositor off, game services
#   dev       — developer tools enabled, schedutil governor
#   creator   — creative workloads, high GPU, low latency audio
#   battery   — power saving, low GPU, throttled CPU
#   balanced  — default, ondemand governor, normal services
#
# Each mode applies:
#   - CPU governor (cpupower frequency-set)
#   - GPU power profile (via /sys/class/drm/card0/device/power_dpm_force_performance_level)
#   - Compositor state (suspend Plasma compositor for gaming)
#   - Background services (start/stop lists)
#   - Tuned-adm profile
#   - Synthex Layout (if available)
#===============================================================================

set -euo pipefail

# --- Constants ---------------------------------------------------------------
readonly SELF="synthex-workspace"
readonly CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/synthex/workspace"
readonly MODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/modes"
readonly STATE_FILE="${CONFIG_DIR}/current_mode"
readonly LAYOUT_CMD="/usr/bin/synthex-layout"
readonly TUNED_ADM="/usr/sbin/tuned-adm"

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Utility Functions -------------------------------------------------------

usage() {
    cat <<EOF
Usage: ${SELF} <command> [options]

Commands:
  set <mode>     Apply a workspace mode
  status         Show current active mode
  list           List available modes and their descriptions

Modes:
  gaming         Maximum performance, compositor disabled, game services
  dev            Developer tools, schedutil governor, Docker/Podman
  creator        Creative workloads, high GPU, low-latency audio
  battery        Power saving, low GPU, throttled CPU
  balanced       Default balanced mode (ondemand governor)

Options:
  -h, --help     Show this help message

Examples:
  ${SELF} set gaming       Switch to gaming mode
  ${SELF} status            Show current mode
  ${SELF} list              List all modes
EOF
    exit 0
}

die() {
    echo -e "${RED}Error:${NC} $*" >&2
    exit 1
}

info() {
    echo -e "${GREEN}==>${NC} $*"
}

warn() {
    echo -e "${YELLOW}Warning:${NC} $*"
}

notify_user() {
    local title="$1"
    local message="$2"
    if command -v notify-send &>/dev/null; then
        notify-send -i preferences-system "Synthex Workspace" "${title}: ${message}" 2>/dev/null || true
    fi
    echo "[${title}] ${message}"
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        die "This operation requires root privileges. Use: sudo ${SELF} ${*:-}"
    fi
}

# --- Mode Loading ------------------------------------------------------------

load_mode() {
    local mode="$1"
    local mode_script="${MODE_DIR}/${mode}.sh"

    if [[ ! -f "${mode_script}" ]]; then
        die "Mode '${mode}' not found. Run '${SELF} list' to see available modes."
    fi

    if [[ ! -x "${mode_script}" ]]; then
        chmod +x "${mode_script}"
    fi

    info "Applying '${mode}' mode..."
    # shellcheck source=/dev/null
    source "${mode_script}"

    # Save current mode
    mkdir -p "${CONFIG_DIR}"
    echo "${mode}" > "${STATE_FILE}"

    info "Mode '${mode}' applied successfully."
    notify_user "Mode Changed" "Switched to ${mode} mode"
}

# --- Commands ----------------------------------------------------------------

cmd_set() {
    local mode="$1"
    case "${mode}" in
        gaming|dev|creator|battery|balanced)
            # Mode scripts handle their own permissions
            load_mode "${mode}"
            ;;
        *)
            die "Unknown mode '${mode}'. Run '${SELF} list' for available modes."
            ;;
    esac
}

cmd_status() {
    local current="unknown"
    if [[ -f "${STATE_FILE}" ]]; then
        current="$(cat "${STATE_FILE}")"
    fi

    echo -e "${BOLD}Synthex Workspace Status${NC}"
    echo "  Current mode: ${current}"

    # CPU governor
    local governor=""
    if command -v cpupower &>/dev/null; then
        governor="$(cpupower frequency-info -g 2>/dev/null | head -1 || echo "N/A")"
    fi
    echo "  CPU governor:  ${governor:-N/A}"

    # GPU power level
    local gpu_power=""
    for gpu_dev in /sys/class/drm/card?/device/power_dpm_force_performance_level; do
        if [[ -r "${gpu_dev}" ]]; then
            gpu_power="$(cat "${gpu_dev}")"
        fi
    done
    echo "  GPU profile:   ${gpu_power:-N/A}"

    # Compositor
    local compositor=""
    if command -v qdbus &>/dev/null; then
        if qdbus org.kde.KWin /Compositor org.kde.kwin.Compositor.compositingActive &>/dev/null; then
            compositor="active"
        else
            compositor="suspended"
        fi
    fi
    echo "  Compositor:    ${compositor:-N/A}"

    # Tuned profile
    if command -v "${TUNED_ADM}" &>/dev/null; then
        echo "  Tuned profile: $("${TUNED_ADM}" active 2>/dev/null || echo "N/A")"
    fi

    # Layout
    if command -v "${LAYOUT_CMD}" &>/dev/null; then
        echo "  Layout:        $("${LAYOUT_CMD}" status 2>/dev/null || echo "N/A")"
    fi
}

cmd_list() {
    echo -e "${BOLD}Available Workspace Modes${NC}\n"

    local modes_available=()
    if [[ -d "${MODE_DIR}" ]]; then
        for f in "${MODE_DIR}"/*.sh; do
            [[ -f "${f}" ]] || continue
            local base
            base="$(basename "${f}" .sh)"
            modes_available+=("${base}")
        done
    fi

    if [[ ${#modes_available[@]} -eq 0 ]]; then
        # Fallback to built-in modes documentation
        modes_available=(gaming dev creator battery balanced)
    fi

    for mode in "${modes_available[@]}"; do
        case "${mode}" in
            gaming)   desc="Maximum performance for games. Disables compositor, sets performance governor, enables gamemode." ;;
            dev)      desc="Developer environment. Starts Docker/Podman, schedutil governor, enables dev services." ;;
            creator)  desc="Creative workloads. High GPU performance, low-latency audio, real-time priority." ;;
            battery)  desc="Power saving mode. Low CPU/GPU frequency, disables non-essential services, extends battery life." ;;
            balanced) desc="Default balanced mode. Ondemand governor, normal services, good power/performance balance." ;;
            *)        desc="Custom mode: ${mode}" ;;
        esac
        echo -e "  ${BOLD}${mode}${NC}"
        echo "      ${desc}"
        echo ""
    done
}

# --- Main --------------------------------------------------------------------

main() {
    local cmd="${1:-help}"

    case "${cmd}" in
        set)
            [[ $# -lt 2 ]] && die "Usage: ${SELF} set <mode>"
            cmd_set "$2"
            ;;
        status)
            cmd_status
            ;;
        list|--list)
            cmd_list
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            die "Unknown command '${cmd}'. See '${SELF} --help'."
            ;;
    esac
}

main "$@"
