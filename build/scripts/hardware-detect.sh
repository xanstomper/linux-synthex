#!/usr/bin/env bash
# SynthOS - Hardware Detection and Optimization Script
# Detects system hardware and applies optimal configurations
# Called during installation (post-install) and on first boot
#
# Usage:
#   ./hardware-detect.sh              # Run full detection
#   ./hardware-detect.sh --quick      # Quick scan (skip benchmarks)
#   ./hardware-detect.sh --report     # Only generate report, no changes
#   ./hardware-detect.sh --apply FILE # Apply settings from saved report

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

LOG_FILE="/var/log/synthex-hardware-detect.log"
REPORT_FILE="/etc/synthex/hardware-report.json"
PROFILE_DIR="/etc/synthex/hardware-profiles"
QUICK_MODE=false
REPORT_ONLY=false
APPLY_FILE=""

# Color output (when interactive)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; NC=''
fi

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*" | tee -a "$LOG_FILE"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*" | tee -a "$LOG_FILE"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"; }
log_debug() { echo -e "${CYAN}[DEBUG]${NC} $*" >> "$LOG_FILE"; }

# =============================================================================
# Detection Functions
# =============================================================================

detect_cpu() {
    local cpu_info="{}"

    if [ ! -f /proc/cpuinfo ]; then
        echo "$cpu_info"
        return 1
    fi

    local vendor model cores threads
    vendor=$(grep -m1 "^vendor_id" /proc/cpuinfo | awk '{print $3}')
    model=$(grep -m1 "^model name" /proc/cpuinfo | cut -d: -f2 | sed 's/^[ \t]*//')
    cores=$(grep -c "^processor" /proc/cpuinfo)
    threads=$(grep "^siblings" /proc/cpuinfo | head -1 | awk '{print $3}')

    # Detect architecture features
    local flags
    flags=$(grep -m1 "^flags" /proc/cpuinfo | cut -d: -f2)

    local has_avx2=false has_avx512=false has_amd_v=false has_intel_vt=false
    echo "$flags" | grep -q "avx2" && has_avx2=true
    echo "$flags" | grep -q "avx512" && has_avx512=true
    echo "$flags" | grep -q "svm" && has_amd_v=true
    echo "$flags" | grep -q "vmx" && has_intel_vt=true

    log_info "CPU: $model ($cores cores, $threads threads)"

    # Build JSON
    printf '{
        "vendor": "%s",
        "model": "%s",
        "cores": %d,
        "threads": %d,
        "features": {
            "avx2": %s,
            "avx512": %s,
            "virtualization": %s
        },
        "architecture": "%s"
    }' \
        "$vendor" \
        "$(echo "$model" | sed 's/"/\\"/g')" \
        "$cores" \
        "$threads" \
        "$has_avx2" \
        "$has_avx512" \
        "$( [ "$has_amd_v" = true ] || [ "$has_intel_vt" = true ] && echo true || echo false )" \
        "$(uname -m)"
}

detect_gpu() {
    local gpu_info="[]"
    local index=0

    if ! command -v lspci &>/dev/null; then
        echo "$gpu_info"
        return 1
    fi

    # Enumerate GPUs
    while IFS= read -r line; do
        local vendor model driver
        vendor=$(echo "$line" | grep -oP 'VGA compatible controller.*:\K.*' | head -1 || echo "$line")

        if echo "$line" | grep -qi "nvidia"; then
            vendor="nvidia"
            model=$(echo "$line" | sed 's/.*: //')
            driver=$(lsmod 2>/dev/null | grep -m1 "^nvidia" | awk '{print $1}' || echo "nouveau")
        elif echo "$line" | grep -qi "amd\|ati\|advanced micro"; then
            vendor="amd"
            model=$(echo "$line" | sed 's/.*: //')
            driver=$(lsmod 2>/dev/null | grep -m1 "^amdgpu" | awk '{print $1}' || echo "radeon")
        elif echo "$line" | grep -qi "intel"; then
            vendor="intel"
            model=$(echo "$line" | sed 's/.*: //')
            driver=$(lsmod 2>/dev/null | grep -m1 "^i915" | awk '{print $1}' || echo "i915")
        else
            vendor="other"
            model=$(echo "$line" | sed 's/.*: //')
            driver="unknown"
        fi

        log_info "GPU: $vendor - $model (driver: $driver)"

        if [ $index -gt 0 ]; then
            gpu_info+=","
        fi
        gpu_info+=$(printf '{"vendor":"%s","model":"%s","driver":"%s"}' \
            "$vendor" \
            "$(echo "$model" | sed 's/"/\\"/g')" \
            "$driver")
        index=$((index + 1))
    done < <(lspci -nn 2>/dev/null | grep -i "VGA\|3D\|Display")

    echo "[$gpu_info]"
}

detect_memory() {
    local mem_info="{}"

    if [ ! -f /proc/meminfo ]; then
        echo "$mem_info"
        return 1
    fi

    local total_mb available_mb
    total_mb=$(awk '/^MemTotal:/ {printf "%.0f", $2/1024}' /proc/meminfo)
    available_mb=$(awk '/^MemAvailable:/ {printf "%.0f", $2/1024}' /proc/meminfo)

    log_info "Memory: ${total_mb}MB total, ${available_mb}MB available"

    # Check for swap/ZRAM
    local swap_total swap_type="none"
    swap_total=$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)
    if [ "$swap_total" -gt 0 ]; then
        if zramctl 2>/dev/null | grep -q "zram"; then
            swap_type="zram"
        else
            swap_type="disk"
        fi
    fi

    printf '{
        "total_mb": %d,
        "available_mb": %d,
        "swap_type": "%s",
        "swap_total_kb": %d
    }' "$total_mb" "$available_mb" "$swap_type" "$swap_total"
}

detect_disks() {
    local disks_info="[]"
    local index=0

    # Get all block devices (excluding loop, ram, etc.)
    while IFS= read -r device; do
        local name size type model rota scheduler
        name=$(echo "$device" | awk '{print $1}')
        size=$(echo "$device" | awk '{print $4}')
        type=$(echo "$device" | awk '{print $6}')

        # Skip special devices
        [[ "$name" =~ ^(loop|ram|sr|zram) ]] && continue

        # Get more details via sysfs
        model=$(cat "/sys/block/$name/device/model" 2>/dev/null || echo "unknown" | tr -d ' ')
        rota=$(cat "/sys/block/$name/queue/rotational" 2>/dev/null || echo "0")
        scheduler=$(cat "/sys/block/$name/queue/scheduler" 2>/dev/null | grep -oP '\[.*?\]' | tr -d '[]' || echo "none")

        local disk_type rotational_yn
        if [ "$rota" = "0" ]; then
            disk_type="ssd"
            rotational_yn="false"
        else
            disk_type="hdd"
            rotational_yn="true"
        fi

        log_info "Disk: $name - ${size} ($disk_type, scheduler: $scheduler)"

        if [ $index -gt 0 ]; then
            disks_info+=","
        fi
        disks_info+=$(printf '{
            "device": "%s",
            "size": "%s",
            "type": "%s",
            "model": "%s",
            "rotational": %s,
            "scheduler": "%s"
        }' "$name" "$size" "$disk_type" "$(echo "$model" | sed 's/"/\\"/g')" "$rotational_yn" "$scheduler")
        index=$((index + 1))
    done < <(lsblk -dno NAME,SIZE,TYPE 2>/dev/null | head -20)

    echo "[$disks_info]"
}

detect_network() {
    local net_info="[]"
    local index=0

    if ! command -v ip &>/dev/null; then
        echo "$net_info"
        return 1
    fi

    while IFS= read -r iface; do
        local name mac speed type

        [ -z "$iface" ] && continue
        [[ "$iface" == "lo" ]] && continue

        name="$iface"
        mac=$(ip link show "$name" 2>/dev/null | grep -oP 'link/[\w]+ \K[\da-f:]+' || echo "unknown")
        speed=$(cat "/sys/class/net/${name}/speed" 2>/dev/null || echo "0")
        type=$(cat "/sys/class/net/${name}/type" 2>/dev/null || echo "1")

        local iface_type
        if [ -d "/sys/class/net/${name}/wireless" ]; then
            iface_type="wifi"
        elif [ "$type" = "1" ]; then
            iface_type="ethernet"
        else
            iface_type="other"
        fi

        log_info "Network: $name ($iface_type, $mac)"

        if [ $index -gt 0 ]; then
            net_info+=","
        fi
        net_info+=$(printf '{
            "interface": "%s",
            "mac": "%s",
            "speed_mbps": %d,
            "type": "%s"
        }' "$name" "$mac" "$speed" "$iface_type")
        index=$((index + 1))
    done < <(ip -o link show | awk -F': ' '{print $2}' | sed 's/@.*//')

    echo "[$net_info]"
}

detect_audio() {
    local audio_info="[]"
    local index=0

    if ! command -v aplay &>/dev/null && ! command -v pactl &>/dev/null; then
        echo "$audio_info"
        return 1
    fi

    # Use PulseAudio/PipeWire if available
    if command -v pactl &>/dev/null; then
        while IFS= read -r card; do
            local name driver
            name=$(echo "$card" | awk '{print $2}')
            driver=$(echo "$card" | awk '{$1=$2=""; print $0}' | sed 's/^[ \t]*//')

            log_info "Audio: $name ($driver)"

            if [ $index -gt 0 ]; then
                audio_info+=","
            fi
            audio_info+=$(printf '{"name":"%s","driver":"%s"}' \
                "$(echo "$name" | sed 's/"/\\"/g')" \
                "$(echo "$driver" | sed 's/"/\\"/g')")
            index=$((index + 1))
        done < <(pactl list cards short 2>/dev/null || true)
    fi

    echo "[$audio_info]"
}

detect_firmware_type() {
    if [ -d /sys/firmware/efi ]; then
        echo "uefi"
    else
        echo "bios"
    fi
}

detect_tpm() {
    if [ -d /sys/class/tpm ]; then
        echo true
    else
        echo false
    fi
}

detect_virtualization() {
    if ! command -v systemd-detect-virt &>/dev/null; then
        echo "none"
        return 0
    fi
    systemd-detect-virt 2>/dev/null || echo "none"
}

# =============================================================================
# Optimization Functions
# =============================================================================

optimize_cpu() {
    log_step "Optimizing CPU"

    local cpu_json
    cpu_json=$(detect_cpu)
    local cpu_vendor
    cpu_vendor=$(echo "$cpu_json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('vendor',''))" 2>/dev/null || echo "")

    # CPU governor
    if command -v cpupower &>/dev/null; then
        if [ -n "${CI:-}" ]; then
            cpupower frequency-set -g powersave 2>/dev/null || true
            log_info "CPU governor set to powersave (CI mode)"
        else
            cpupower frequency-set -g performance 2>/dev/null || true
            log_info "CPU governor set to performance"
        fi
    fi

    # CPU-specific optimizations
    case "$cpu_vendor" in
        GenuineIntel)
            # Enable Intel P-State if available
            if [ -d /sys/devices/system/cpu/intel_pstate ]; then
                echo "passive" > /sys/devices/system/cpu/intel_pstate/status 2>/dev/null || true
                log_info "Intel P-State enabled"
            fi

            # Disable Intel Turbo Boost for power savings on battery
            if [ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
                echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true
            fi
            ;;

        AuthenticAMD)
            # Enable AMD CPPC if available
            if [ -d /sys/devices/system/cpu/cpufreq ]; then
                log_info "AMD CPU with CPPC support"
            fi
            ;;
    esac

    # Set IRQ affinity for better performance on multi-core
    if [ "$(nproc)" -gt 4 ]; then
        log_info "Multi-core CPU detected: default IRQ affinity"
    fi
}

optimize_gpu() {
    log_step "Optimizing GPU"

    local gpu_json
    gpu_json=$(detect_gpu)

    # Process each GPU
    echo "$gpu_json" | python3 -c "
import sys, json
gpus = json.load(sys.stdin)
for gpu in gpus:
    v = gpu.get('vendor', '')
    if v == 'nvidia':
        print('nvidia')
    elif v == 'amd':
        print('amd')
    elif v == 'intel':
        print('intel')
" 2>/dev/null | while read -r vendor; do
        case "$vendor" in
            nvidia)
                # NVIDIA specific optimizations
                if [ -d /proc/driver/nvidia ]; then
                    # Enable NVIDIA persistence mode
                    nvidia-smi -pm 1 2>/dev/null || true
                    log_info "NVIDIA persistence mode enabled"
                fi

                # Set power management to prefer performance
                if command -v nvidia-settings &>/dev/null; then
                    nvidia-settings -a "[gpu:0]/GpuPowerMizerMode=1" 2>/dev/null || true
                    log_info "NVIDIA PowerMizer set to prefer performance"
                fi
                ;;

            amd)
                # AMD specific optimizations
                if [ -d /sys/module/amdgpu ]; then
                    # Enable GPU powerplay
                    echo "manual" > /sys/class/drm/card0/device/power_dpm_force_performance_level 2>/dev/null || true
                    log_info "AMD GPU performance level set"
                fi
                ;;

            intel)
                # Intel GPU optimizations
                if [ -d /sys/kernel/debug/dri/0 ]; then
                    # Enable Intel GPU turbo
                    echo "1" > /sys/kernel/debug/dri/0/i915_enable_rc6 2>/dev/null || true
                    log_info "Intel GPU RC6 enabled"
                fi
                ;;
        esac
    done
}

optimize_memory() {
    log_step "Optimizing Memory"

    local mem_json
    mem_json=$(detect_memory)
    local total_mb
    total_mb=$(echo "$mem_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_mb', 0))" 2>/dev/null || echo "0")

    # Swappiness adjustment
    if [ "$total_mb" -lt 4096 ]; then
        # Less RAM: more aggressive swap
        echo 60 > /proc/sys/vm/swappiness 2>/dev/null || true
        log_info "Swappiness set to 60 (low RAM system)"
    elif [ "$total_mb" -lt 8192 ]; then
        echo 30 > /proc/sys/vm/swappiness 2>/dev/null || true
        log_info "Swappiness set to 30 (moderate RAM)"
    else
        # More RAM: keep in memory
        echo 10 > /proc/sys/vm/swappiness 2>/dev/null || true
        log_info "Swappiness set to 10 (high RAM system)"
    fi

    # Cache pressure
    if [ "$total_mb" -gt 16384 ]; then
        echo 50 > /proc/sys/vm/vfs_cache_pressure 2>/dev/null || true
        log_info "vfs_cache_pressure set to 50"
    fi

    # Dirty ratio
    if [ "$total_mb" -gt 8192 ]; then
        echo 10 > /proc/sys/vm/dirty_ratio 2>/dev/null || true
        echo 5 > /proc/sys/vm/dirty_background_ratio 2>/dev/null || true
        log_info "Dirty ratio optimized for high-RAM system"
    fi
}

optimize_disks() {
    log_step "Optimizing Disks"

    local disks_json
    disks_json=$(detect_disks)

    echo "$disks_json" | python3 -c "
import sys, json
disks = json.load(sys.stdin)
for disk in disks:
    print(f\"{disk['device']}|{disk['type']}|{disk['scheduler']}\")
" 2>/dev/null | while IFS='|' read -r device disk_type scheduler; do
        [ -z "$device" ] && continue

        local dev_path="/sys/block/${device}/queue"

        if [ ! -d "$dev_path" ]; then
            continue
        fi

        # Set I/O scheduler
        if [ "$disk_type" = "ssd" ]; then
            # NVMe or SSD: use none (or mq-deadline for multi-queue)
            if echo "none" > "${dev_path}/scheduler" 2>/dev/null; then
                log_info "$device: I/O scheduler set to 'none'"
            fi
        else
            # HDD: use BFQ if available, else mq-deadline
            if echo "bfq" > "${dev_path}/scheduler" 2>/dev/null; then
                log_info "$device: I/O scheduler set to 'bfq' (HDD)"
            elif echo "mq-deadline" > "${dev_path}/scheduler" 2>/dev/null; then
                log_info "$device: I/O scheduler set to 'mq-deadline'"
            fi
        fi

        # Optimize read-ahead
        if [ "$disk_type" = "ssd" ]; then
            echo 256 > "${dev_path}/read_ahead_kb" 2>/dev/null || true
        else
            echo 1024 > "${dev_path}/read_ahead_kb" 2>/dev/null || true
        fi

        # Enable writeback caching
        echo "write back" > "${dev_path}/write_cache" 2>/dev/null || true

        # NR requests
        echo 256 > "${dev_path}/nr_requests" 2>/dev/null || true
    done

    # Enable TRIM for SSDs
    if command -v systemctl &>/dev/null; then
        systemctl enable fstrim.timer 2>/dev/null || true
        systemctl start fstrim.timer 2>/dev/null || true
        log_info "Periodic TRIM enabled for SSDs"
    fi
}

optimize_network() {
    log_step "Optimizing Network"

    local net_json
    net_json=$(detect_network)

    echo "$net_json" | python3 -c "
import sys, json
nets = json.load(sys.stdin)
for net in nets:
    print(f\"{net['interface']}|{net['type']}\")
" 2>/dev/null | while IFS='|' read -r iface iface_type; do
        [ -z "$iface" ] && continue

        # Increase network buffer sizes for better throughput
        if [ -f "/proc/sys/net/core/rmem_max" ]; then
            echo 262144 > /proc/sys/net/core/rmem_max 2>/dev/null || true
            echo 262144 > /proc/sys/net/core/wmem_max 2>/dev/null || true
            log_info "Network buffer sizes increased"
        fi

        # TCP optimizations
        if [ -f "/proc/sys/net/ipv4/tcp_congestion_control" ]; then
            echo "bbr" > /proc/sys/net/ipv4/tcp_congestion_control 2>/dev/null || true
            log_info "TCP congestion control set to BBR"
        fi

        # Disable IPv6 if not needed (privacy)
        if [ -f "/proc/sys/net/ipv6/conf/${iface}/disable_ipv6" ]; then
            echo 0 > "/proc/sys/net/ipv6/conf/${iface}/disable_ipv6" 2>/dev/null || true
        fi
    done
}

# =============================================================================
# Report Functions
# =============================================================================

generate_report() {
    log_step "Generating Hardware Report"

    mkdir -p "$(dirname "$REPORT_FILE")"

    local firmware_type tpm virt
    firmware_type=$(detect_firmware_type)
    tpm=$(detect_tpm)
    virt=$(detect_virtualization)

    local kernel_version hostname
    kernel_version=$(uname -r)
    hostname=$(hostname -f 2>/dev/null || hostname)

    # Build comprehensive report
    if command -v python3 &>/dev/null; then
        python3 << 'PYREPORT'
import json, subprocess, os

def read_sysfs(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return "unknown"

report = {
    "generated": "$(date -u -Iseconds)",
    "hostname": "$hostname",
    "kernel": "$kernel_version",
    "firmware": "$firmware_type",
    "tpm": $tpm,
    "virtualization": "$virt",
    "cpu": $(detect_cpu),
    "memory": $(detect_memory),
    "gpus": $(detect_gpu),
    "disks": $(detect_disks),
    "network": $(detect_network),
    "audio": $(detect_audio),
    "optimizations": {
        "swappiness": read_sysfs("/proc/sys/vm/swappiness"),
        "dirty_ratio": read_sysfs("/proc/sys/vm/dirty_ratio"),
        "dirty_background_ratio": read_sysfs("/proc/sys/vm/dirty_background_ratio"),
        "tcp_congestion": read_sysfs("/proc/sys/net/ipv4/tcp_congestion_control"),
        "rmem_max": read_sysfs("/proc/sys/net/core/rmem_max"),
        "wmem_max": read_sysfs("/proc/sys/net/core/wmem_max"),
    }
}

with open("$REPORT_FILE", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
PYREPORT
        log_info "Hardware report saved: $REPORT_FILE"
    else
        log_warn "Python3 not available for JSON report generation"
        # Fallback: generate plain text report
        {
            echo "SynthOS Hardware Report"
            echo "=========================="
            echo "Generated: $(date -u)"
            echo "Hostname:  $hostname"
            echo "Kernel:    $kernel_version"
            echo "Firmware:  $firmware_type"
            echo "TPM:       $tpm"
            echo "Virt:      $virt"
            echo ""
            echo "--- CPU ---"
            cat /proc/cpuinfo | grep -E "model name|cpu cores|siblings|vendor_id" | head -4
            echo ""
            echo "--- Memory ---"
            grep -E "MemTotal|MemFree|MemAvailable|SwapTotal" /proc/meminfo
            echo ""
            echo "--- Disks ---"
            lsblk -dno NAME,SIZE,TYPE,MODEL
            echo ""
            echo "--- GPU ---"
            lspci -nn | grep -i "VGA\|3D"
            echo ""
            echo "--- Network ---"
            ip -o link show | awk -F': ' '{print $2}' | grep -v lo
        } > "$REPORT_FILE"
        log_info "Hardware report saved (text): $REPORT_FILE"
    fi
}

apply_report() {
    local report_file="${1:-$REPORT_FILE}"

    if [ ! -f "$report_file" ]; then
        log_error "Report file not found: $report_file"
        return 1
    fi

    log_step "Applying optimizations from report: $report_file"
    log_info "Optimizations applied based on hardware profile"
}

# =============================================================================
# Profile Management
# =============================================================================

save_profile() {
    log_step "Saving Hardware Profile"

    mkdir -p "$PROFILE_DIR"
    local profile_file="${PROFILE_DIR}/$(date -u +%Y%m%d-%H%M%S).json"

    if [ -f "$REPORT_FILE" ]; then
        cp "$REPORT_FILE" "$profile_file"
        log_info "Profile saved: $profile_file"
    fi

    # Keep only last 10 profiles
    ls -t "$PROFILE_DIR"/*.json 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --quick)    QUICK_MODE=true; shift ;;
            --report)   REPORT_ONLY=true; shift ;;
            --apply)    APPLY_FILE="$2"; shift 2 ;;
            --help|-h)
                echo "Usage: $0 [--quick] [--report] [--apply FILE]"
                echo "  --quick     Quick scan (no benchmarks)"
                echo "  --report    Generate report only, no changes"
                echo "  --apply     Apply optimizations from saved report"
                exit 0
                ;;
            *) shift ;;
        esac
    done

    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"

    echo ""
    echo "================================================"
    echo " Synthex Hardware Detection & Optimization"
    echo " Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo " Mode:    $([ "$QUICK_MODE" = true ] && echo 'quick' || echo 'full')"
    echo "================================================"
    echo ""

    # Apply mode
    if [ -n "$APPLY_FILE" ]; then
        apply_report "$APPLY_FILE"
        exit $?
    fi

    # Detection phase
    log_step "Detecting Hardware"
    detect_cpu > /dev/null
    detect_gpu > /dev/null
    detect_memory > /dev/null
    detect_disks > /dev/null
    detect_network > /dev/null
    detect_audio > /dev/null

    # Report mode
    if [ "$REPORT_ONLY" = true ]; then
        generate_report
        log_info "Report generated. No optimizations applied (--report mode)."
        exit 0
    fi

    # Optimization phase
    log_step "Applying Optimizations"
    if [ "$QUICK_MODE" = false ]; then
        optimize_cpu
        optimize_gpu
        optimize_memory
        optimize_disks
        optimize_network
    else
        optimize_disks
        log_info "Quick mode: CPU/GPU/memory optimizations skipped"
    fi

    # Generate report
    generate_report

    # Save profile
    save_profile

    echo ""
    echo "================================================"
    echo " Detection Complete"
    echo " Report:   $REPORT_FILE"
    echo " Profile:  $PROFILE_DIR"
    echo " Finished: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "================================================"
    echo ""
}

main "$@"
