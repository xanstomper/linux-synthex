#!/usr/bin/env bash
#===============================================================================
# Solus AI — Model Sources Manager
# Download, verify, and manage local LLM models for Solus Linux
#
# Usage:
#   ./model-sources.sh install <model-id> [quant]
#   ./model-sources.sh remove <model-id> [quant]
#   ./model-sources.sh list
#   ./model-sources.sh search <query>
#   ./model-sources.sh prune [days]
#   ./model-sources.sh status
#   ./model-sources.sh update-index
#
# Examples:
#   ./model-sources.sh install llama3.1:8b Q4_K_M
#   ./model-sources.sh remove qwen2.5:7b
#   ./model-sources.sh list
#   ./model-sources.sh prune 30
#===============================================================================

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

SOLUS_AI_HOME="${SOLUS_AI_HOME:-$HOME/.solus/ai}"
MODELS_DIR="${SOLUS_AI_MODELS_DIR:-$SOLUS_AI_HOME/models}"
CACHE_DIR="${SOLUS_AI_CACHE_DIR:-$SOLUS_AI_HOME/cache}"
CONFIG_DIR="${SOLUS_AI_CONFIG_DIR:-$HOME/.config/solus-ai-hub}"
LIBRARY_JSON="${CONFIG_DIR}/modellibrary.json"
LOG_FILE="${SOLUS_AI_HOME}/logs/model-manager.log"
DB_FILE="${CONFIG_DIR}/aihub.db"

# Default fallback URLs (when library is not available)
OLLAMA_API="${OLLAMA_API:-http://127.0.0.1:11434}"
HUGGINGFACE_MIRROR="${HUGGINGFACE_MIRROR:-https://huggingface.co}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ──────────────────────────────────────────────────────────────────────────────
# Utility Functions
# ──────────────────────────────────────────────────────────────────────────────

log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
    echo -e "${msg}" | tee -a "${LOG_FILE}" >&2
}

info()    { log "INFO"    "${CYAN}${*}${NC}"; }
success() { log "SUCCESS" "${GREEN}${*}${NC}"; }
warning() { log "WARN"    "${YELLOW}${*}${NC}"; }
error()   { log "ERROR"   "${RED}${*}${NC}"; }

ensure_dirs() {
    mkdir -p "${MODELS_DIR}" "${CACHE_DIR}" "${CONFIG_DIR}" "$(dirname "${LOG_FILE}")"
}

check_deps() {
    local missing=()
    for dep in curl jq sha256sum ollama; do
        if ! command -v "${dep}" &>/dev/null; then
            missing+=("${dep}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "Missing dependencies: ${missing[*]}"
        echo "Install with: sudo dnf install curl jq ollama" >&2
        return 1
    fi
}

human_size() {
    numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"
}

check_disk_space() {
    local needed="$1"
    local available
    available=$(df -B1 "${MODELS_DIR}" | awk 'NR==2 {print $4}')
    if [[ "${available}" -lt "${needed}" ]]; then
        error "Insufficient disk space. Need $(human_size "$needed"), have $(human_size "$available")"
        return 1
    fi
    return 0
}

# ──────────────────────────────────────────────────────────────────────────────
# Model Library Functions
# ──────────────────────────────────────────────────────────────────────────────

# Load metadata from the bundled modellibrary.json
load_library() {
    if [[ -f "${LIBRARY_JSON}" ]]; then
        cat "${LIBRARY_JSON}"
    elif [[ -f "/usr/share/solus-ai-hub/modellibrary.json" ]]; then
        cat "/usr/share/solus-ai-hub/modellibrary.json"
    else
        warning "Model library not found at ${LIBRARY_JSON}"
        echo "{}"
    fi
}

get_model_info() {
    local model_id="$1"
    load_library | jq -r --arg id "${model_id}" '.models[] | select(.id == $id) // empty'
}

list_available_models() {
    load_library | jq -r '.models[] | "\(.id) | \(.name) | \(.category) | \(.popularity)"' 2>/dev/null \
        || echo "No library available"
}

search_models() {
    local query="$1"
    load_library | jq -r --arg q "${query}" \
        '.models[] | select(.name | test($q; "i") or .id | test($q; "i") or .description | test($q; "i")) |
        "\(.id) | \(.name) | \(.category) | ★\(.popularity)"' 2>/dev/null \
        || echo "No results"
}

# ──────────────────────────────────────────────────────────────────────────────
# Installation via Ollama (Primary Method)
# ──────────────────────────────────────────────────────────────────────────────

install_via_ollama() {
    local model_id="$1"
    local quant="${2:-}"

    # Check if Ollama is running
    if ! curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        warning "Ollama is not running. Attempting to start..."
        if command -v systemctl &>/dev/null; then
            systemctl --user start ollama 2>/dev/null || sudo systemctl start ollama 2>/dev/null || true
        fi
        sleep 2
        if ! curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
            error "Cannot connect to Ollama. Please start it first: ollama serve"
            return 1
        fi
    fi

    # Determine full tag
    local tag="${model_id}"
    if [[ -n "${quant}" ]]; then
        # Map quantization to Ollama tag variant
        case "${quant}" in
            Q4_K_M) tag="${model_id}:q4_k_m" ;;
            Q5_K_M) tag="${model_id}:q5_k_m" ;;
            Q8_0)   tag="${model_id}:q8_0"   ;;
            F16)    tag="${model_id}:f16"    ;;
            *)      tag="${model_id}:${quant,,}" ;;
        esac
    fi

    info "Installing model via Ollama: ${tag}"
    info "This will download the model weights. This may take several minutes depending on model size."

    # Check disk space before pulling
    local model_size
    model_size=$(get_model_info "${model_id}" | jq -r --arg q "${quant:-Q4_K_M}" '.file_size[$q] // "0"')
    if [[ "${model_size}" -gt 0 ]]; then
        # Add overhead for download + conversion
        local total_needed=$(( model_size + 5000000000 ))  # 5GB overhead
        check_disk_space "${total_needed}" || return 1
    fi

    # Pull model
    if ollama pull "${tag}"; then
        success "Model installed: ${tag}"

        # Set keep-alive for responsiveness
        ollama run "${tag}" "" --keep-alive 5m 2>/dev/null || true

        # Register in local database
        if command -v sqlite3 &>/dev/null && [[ -f "${DB_FILE}" ]]; then
            sqlite3 "${DB_FILE}" \
                "INSERT OR REPLACE INTO installed_models (model_id, quant, ollama_name, status, downloaded_at)
                 VALUES ('${model_id}', '${quant:-Q4_K_M}', '${tag}', 'ready', datetime('now'));" 2>/dev/null || true
        fi

        return 0
    else
        error "Failed to install model: ${tag}"
        return 1
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# Installation via Hugging Face (Alternative Method)
# ──────────────────────────────────────────────────────────────────────────────

install_via_huggingface() {
    local repo_id="$1"
    local filename="$2"
    local output_name="${3:-$(basename "${filename}" .gguf)}"

    local output_path="${MODELS_DIR}/${output_name}.gguf"

    info "Downloading from HuggingFace: ${repo_id}/${filename}"
    info "Output: ${output_path}"

    # Create temp download path
    local tmp_path="${CACHE_DIR}/${output_name}.part"

    # Get file size for disk check
    local file_size
    file_size=$(curl -sI "https://huggingface.co/${repo_id}/resolve/main/${filename}" \
        | grep -i content-length | awk '{print $2}' | tr -d '\r' || echo "0")

    if [[ "${file_size}" -gt 0 ]]; then
        check_disk_space "${file_size}" || return 1
    fi

    # Download with resume support
    info "Downloading with resume support..."
    if curl -L -C - --progress-bar \
        "https://huggingface.co/${repo_id}/resolve/main/${filename}" \
        -o "${tmp_path}"; then

        # Verify download
        if [[ -f "${tmp_path}" ]]; then
            mv "${tmp_path}" "${output_path}"
            success "Model downloaded: ${output_path} ($(human_size "$(stat -c%s "${output_path}")"))"

            # Generate Ollama Modelfile for this GGUF
            local modelfile="${MODELS_DIR}/${output_name}.Modelfile"
            cat > "${modelfile}" << MODELFILES
FROM ${output_path}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "</s>"
TEMPLATE """
{{- if .System }}
System: {{ .System }}
{{- end }}

User: {{ .Prompt }}

Assistant: {{ .Response }}"""
MODELFILES

            info "Created Modelfile at ${modelfile}"
            info "To create Ollama model: ollama create ${output_name} -f ${modelfile}"

            return 0
        fi
    fi

    error "Download failed"
    rm -f "${tmp_path}"
    return 1
}

# ──────────────────────────────────────────────────────────────────────────────
# Model Management Functions
# ──────────────────────────────────────────────────────────────────────────────

list_installed() {
    echo -e "${BLUE}Installed Models:${NC}"
    echo "─────────────────────────────────────────────────"

    # List via Ollama
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        echo -e "${CYAN}Ollama registered models:${NC}"
        curl -sf "${OLLAMA_API}/api/tags" | jq -r '
            .models[] | "  \(.name) (\(.size // "unknown")) [\(.details.parameter_size // "?") | \(.details.quantization_level // "?")]"
        ' 2>/dev/null || echo "  (none)"
    else
        echo -e "${YELLOW}  Ollama not running. Start with: ollama serve${NC}"
    fi

    echo ""
    # List local GGUF files
    local gguf_count
    gguf_count=$(find "${MODELS_DIR}" -name "*.gguf" 2>/dev/null | wc -l)
    if [[ "${gguf_count}" -gt 0 ]]; then
        echo -e "${CYAN}Local GGUF files:${NC}"
        find "${MODELS_DIR}" -name "*.gguf" -exec sh -c '
            echo "  $(basename "{}") ($(numfmt --to=iec --suffix=B "$(stat -c%s "{}")" 2>/dev/null || echo "?"))"
        ' \;
    else
        echo "  (no local GGUF files)"
    fi

    # Summary
    local total_size
    total_size=$(find "${MODELS_DIR}" -type f \( -name "*.gguf" -o -name "*.bin" \) -printf "%s\n" 2>/dev/null | awk '{s+=$1} END {print s}' || echo "0")
    echo ""
    echo -e "${GREEN}Total model storage: $(human_size "${total_size}")${NC}"
}

remove_model() {
    local model_id="$1"
    local quant="${2:-}"

    local tag="${model_id}"
    if [[ -n "${quant}" ]]; then
        case "${quant}" in
            Q4_K_M) tag="${model_id}:q4_k_m" ;;
            Q5_K_M) tag="${model_id}:q5_k_m" ;;
            Q8_0)   tag="${model_id}:q8_0"   ;;
            F16)    tag="${model_id}:f16"    ;;
            *)      tag="${model_id}:${quant,,}" ;;
        esac
    fi

    info "Removing model: ${tag}"

    # Remove via Ollama
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        if ollama rm "${tag}" 2>/dev/null; then
            success "Removed from Ollama: ${tag}"
        else
            warning "Model ${tag} not found in Ollama"
        fi
    fi

    # Remove from local database
    if command -v sqlite3 &>/dev/null && [[ -f "${DB_FILE}" ]]; then
        sqlite3 "${DB_FILE}" \
            "DELETE FROM installed_models WHERE model_id='${model_id}' AND quant='${quant:-Q4_K_M}';" 2>/dev/null || true
    fi

    # Remove local GGUF if it matches
    local gguf_path="${MODELS_DIR}/${model_id/:/_}.gguf"
    if [[ -f "${gguf_path}" ]]; then
        rm -f "${gguf_path}"
        success "Removed local GGUF: ${gguf_path}"
    fi

    # Remove Modelfile
    local modelfile="${MODELS_DIR}/${model_id/:/_}.Modelfile"
    if [[ -f "${modelfile}" ]]; then
        rm -f "${modelfile}"
    fi

    success "Model removed: ${tag}"
}

# ──────────────────────────────────────────────────────────────────────────────
# Pruning (Cleanup) Functions
# ──────────────────────────────────────────────────────────────────────────────

prune_models() {
    local days="${1:-30}"
    info "Pruning models not loaded in ${days} days..."

    local freed=0
    local count=0

    # Check Ollama for stale models
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        local stale
        stale=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' || true)

        for model in ${stale}; do
            # Skip if we have a DB timestamp showing recent use
            if command -v sqlite3 &>/dev/null && [[ -f "${DB_FILE}" ]]; then
                local last_loaded
                last_loaded=$(sqlite3 "${DB_FILE}" \
                    "SELECT last_loaded_at FROM installed_models WHERE ollama_name='${model}' 
                     AND last_loaded_at > datetime('now', '-${days} days');" 2>/dev/null || true)
                if [[ -n "${last_loaded}" ]]; then
                    continue
                fi
            fi

            # Ask before removing (non-interactive: skip)
            if [[ -t 0 ]]; then
                read -r -p "Remove stale model ${model}? [y/N] " reply
                if [[ "${reply}" =~ ^[Yy]$ ]]; then
                    local size
                    size=$(ollama show "${model}" 2>/dev/null | grep "size" | awk '{print $2}' || echo "0")
                    ollama rm "${model}" 2>/dev/null || true
                    freed=$(( freed + size ))
                    count=$(( count + 1 ))
                    success "Pruned: ${model}"
                fi
            fi
        done
    fi

    # Clean cache blobs (partial downloads older than 7 days)
    local cache_count=0
    local cache_freed=0
    while IFS= read -r -d '' file; do
        local age
        age=$(( ( $(date +%s) - $(stat -c%Y "${file}") ) / 86400 ))
        if [[ "${age}" -gt 7 ]]; then
            local size
            size=$(stat -c%s "${file}")
            rm -f "${file}"
            cache_freed=$(( cache_freed + size ))
            cache_count=$(( cache_count + 1 ))
        fi
    done < <(find "${CACHE_DIR}" -name "*.part" -o -name "*.tmp" -print0 2>/dev/null)

    success "Pruned ${count} stale models, ${cache_count} cache files"
    info "Freed approximately $(human_size $((freed + cache_freed)))"
}

# ──────────────────────────────────────────────────────────────────────────────
# Status / Diagnostics
# ──────────────────────────────────────────────────────────────────────────────

show_status() {
    echo -e "${BLUE}Solus AI Model Manager — Status${NC}"
    echo "═══════════════════════════════════════════════"

    # Storage
    local model_size model_count
    model_size=$(find "${MODELS_DIR}" -type f \( -name "*.gguf" -o -name "*.bin" \) -printf "%s\n" 2>/dev/null | awk '{s+=$1} END {print s}' || echo "0")
    model_count=$(ollama list 2>/dev/null | wc -l || echo "0")
    model_count=$(( model_count - 1 ))  # Subtract header
    [[ "${model_count}" -lt 0 ]] && model_count=0

    echo -e "${CYAN}Models Directory:${NC}     ${MODELS_DIR}"
    echo -e "${CYAN}Installed Models:${NC}    ${model_count}"
    echo -e "${CYAN}Model Storage:${NC}       $(human_size "${model_size}")"
    echo ""

    # Cache
    local cache_size
    cache_size=$(find "${CACHE_DIR}" -type f -printf "%s\n" 2>/dev/null | awk '{s+=$1} END {print s}' || echo "0")
    echo -e "${CYAN}Cache Directory:${NC}     ${CACHE_DIR}"
    echo -e "${CYAN}Cache Size:${NC}          $(human_size "${cache_size}")"
    echo ""

    # Disk space
    local disk_free disk_total
    disk_free=$(df -h "${MODELS_DIR}" 2>/dev/null | awk 'NR==2 {print $4}' || echo "?")
    disk_total=$(df -h "${MODELS_DIR}" 2>/dev/null | awk 'NR==2 {print $2}' || echo "?")
    echo -e "${CYAN}Disk Free:${NC}           ${disk_free} / ${disk_total}"
    echo ""

    # Ollama status
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        echo -e "${GREEN}● Ollama:${NC} Running on ${OLLAMA_API}"
    else
        echo -e "${RED}● Ollama:${NC} Not running"
    fi

    # GPU status
    if command -v rocm-smi &>/dev/null; then
        echo -e "${GREEN}● AMD GPU:${NC} Detected (ROCm available)"
    elif command -v nvidia-smi &>/dev/null; then
        echo -e "${GREEN}● NVIDIA GPU:${NC} Detected (CUDA available)"
    elif ls /dev/dri/renderD128 &>/dev/null && command -v clinfo &>/dev/null; then
        echo -e "${GREEN}● Intel GPU:${NC} Detected (oneAPI/Level Zero available)"
    else
        echo -e "${YELLOW}● GPU:${NC} Not detected — running CPU inference"
    fi
}

# ──────────────────────────────────────────────────────────────────────────────
# Update Model Index
# ──────────────────────────────────────────────────────────────────────────────

update_index() {
    info "Updating model index from Ollama registry..."
    if curl -sf "${OLLAMA_API}/api/tags" >/dev/null 2>&1; then
        local installed
        installed=$(curl -sf "${OLLAMA_API}/api/tags" | jq -r '.models[].name' 2>/dev/null || true)
        info "Connected to Ollama. Installed models:"
        echo "${installed}" | while IFS= read -r m; do
            [[ -n "${m}" ]] && echo "  - ${m}"
        done
    else
        warning "Cannot connect to Ollama. Start it with 'ollama serve' first."
    fi

    # Check for updates
    info "Checking for model updates..."
    if command -v sqlite3 &>/dev/null && [[ -f "${DB_FILE}" ]]; then
        local outdated
        outdated=$(sqlite3 "${DB_FILE}" \
            "SELECT model_id FROM installed_models WHERE updated_at < datetime('now', '-30 days');" 2>/dev/null || true)
        if [[ -n "${outdated}" ]]; then
            echo -e "${YELLOW}Models possibly outdated (last updated >30 days ago):${NC}"
            echo "${outdated}" | while IFS= read -r m; do
                [[ -n "${m}" ]] && echo "  - ${m}"
            done
            echo "Reinstall with: ollama pull <model>"
        fi
    fi

    success "Index update complete"
}

# ──────────────────────────────────────────────────────────────────────────────
# Batch Install from Quick Install List
# ──────────────────────────────────────────────────────────────────────────────

quick_install() {
    local category="${1:-recommended}"

    info "Quick installing '${category}' models..."
    local models
    models=$(load_library | jq -r ".quick_install.\"${category}\"[]" 2>/dev/null || true)

    if [[ -z "${models}" ]]; then
        error "Unknown quick install category: ${category}"
        echo "Available categories: recommended, lightweight, code, large"
        return 1
    fi

    echo "${models}" | while IFS= read -r tag; do
        [[ -z "${tag}" ]] && continue
        # Parse tag back to model_id and quant
        local model_id="${tag%:*}"
        local quant="${tag#*:}"
        quant="${quant%-q4}"
        quant="${quant%-q5}"
        quant="${quant%-q8}"
        quant="${quant^^}_K_M"

        if [[ "${tag}" == *"-q4"* ]]; then
            quant="Q4_K_M"
        elif [[ "${tag}" == *"-q5"* ]]; then
            quant="Q5_K_M"
        elif [[ "${tag}" == *"-q8"* ]]; then
            quant="Q8_0"
        fi

        install_via_ollama "${model_id}" "${quant}" || warning "Failed to install ${tag}, continuing..."
    done

    success "Quick install complete for '${category}' models"
}

# ──────────────────────────────────────────────────────────────────────────────
# Main Command Dispatch
# ──────────────────────────────────────────────────────────────────────────────

usage() {
    cat << USAGE
Solus AI Model Manager — Download, manage, and prune local LLMs

Usage:
  $(basename "$0") install <model-id> [quant]    Install a model (via Ollama)
  $(basename "$0") install-gguf <repo> <file>    Install a GGUF model (via HF)
  $(basename "$0") remove  <model-id> [quant]    Remove a model
  $(basename "$0") list                          List installed models
  $(basename "$0") search <query>                Search available models
  $(basename "$0") quick [category]              Quick install preset models
  $(basename "$0") prune [days]                  Prune stale models (default: 30d)
  $(basename "$0") status                        Show system and model status
  $(basename "$0") update-index                  Refresh model registry index

Quick Install Categories:
  recommended    Llama 3.1 8B, Qwen 2.5 7B, DeepSeek R1 7B, Phi-4 14B
  lightweight    Phi-3.5 3.8B, Qwen 2.5 1.5B, Gemma 2 2B
  code           Qwen 2.5 Coder 7B, DeepSeek Coder 6.7B, StarCoder 2 7B
  large          Llama 3.1 70B, Mixtral 8x7B, Qwen 2.5 32B

Environment Variables:
  SOLUS_AI_HOME       Base directory (~/.solus/ai)
  SOLUS_AI_MODELS_DIR Model storage directory
  OLLAMA_API          Ollama API endpoint (http://127.0.0.1:11434)

Examples:
  $(basename "$0") install llama3.1:8b Q4_K_M
  $(basename "$0") install-gguf TheBloke/Llama-2-7B-GGUF llama-2-7b.Q4_K_M.gguf
  $(basename "$0") quick recommended
  $(basename "$0") prune 14
USAGE
}

main() {
    check_deps
    ensure_dirs

    local cmd="${1:-help}"
    shift 2>/dev/null || true

    case "${cmd}" in
        install)
            local model_id="${1:-}"
            local quant="${2:-Q4_K_M}"
            if [[ -z "${model_id}" ]]; then
                error "Usage: $(basename "$0") install <model-id> [quant]"
                return 1
            fi
            install_via_ollama "${model_id}" "${quant}"
            ;;
        install-gguf|hf)
            local repo="${1:-}"
            local file="${2:-}"
            local name="${3:-}"
            if [[ -z "${repo}" || -z "${file}" ]]; then
                error "Usage: $(basename "$0") install-gguf <repo> <file> [name]"
                return 1
            fi
            install_via_huggingface "${repo}" "${file}" "${name}"
            ;;
        remove|rm)
            local model_id="${1:-}"
            local quant="${2:-}"
            if [[ -z "${model_id}" ]]; then
                error "Usage: $(basename "$0") remove <model-id> [quant]"
                return 1
            fi
            remove_model "${model_id}" "${quant}"
            ;;
        list|ls)
            list_installed
            ;;
        search)
            local query="${1:-}"
            if [[ -z "${query}" ]]; then
                error "Usage: $(basename "$0") search <query>"
                return 1
            fi
            search_models "${query}"
            ;;
        quick)
            quick_install "${1:-recommended}"
            ;;
        prune)
            prune_models "${1:-30}"
            ;;
        status|info)
            show_status
            ;;
        update-index|update)
            update_index
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: ${cmd}"
            usage
            return 1
            ;;
    esac
}

main "$@"
