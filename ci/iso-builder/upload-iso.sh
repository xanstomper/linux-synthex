#!/usr/bin/env bash
# ============================================================================
# Solus Linux — ISO Upload & Mirror Sync Script
# ============================================================================
# Uploads built ISO images to the primary repository server and triggers
# mirror synchronization across the CDN and regional mirrors.
# ============================================================================
set -euo pipefail

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./builder-config.sh
source "${SCRIPT_DIR}/builder-config.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()  { echo -e "${CYAN}[STEP]${NC} $*"; }

# --------------------------------------------------------------------------
# Prerequisites
# --------------------------------------------------------------------------
check_prerequisites() {
    log_info "Checking prerequisites..."

    local required_commands=(
        "rsync"
        "gpg"
        "sha256sum"
        "sha512sum"
        "curl"
        "jq"
    )

    local missing=0
    for cmd in "${required_commands[@]}"; do
        if ! command -v "${cmd}" &>/dev/null; then
            log_error "Required command not found: ${cmd}"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_error "${missing} prerequisite(s) missing. Install them and retry."
        exit 1
    fi

    # Check SSH key
    if [[ ! -f "${MIRROR_SSH_KEY}" ]]; then
        log_warn "Mirror SSH key not found at ${MIRROR_SSH_KEY}"
        log_warn "Falling back to password authentication (if available)"
    fi

    log_info "All prerequisites met."
}

# --------------------------------------------------------------------------
# Source validation
# --------------------------------------------------------------------------
validate_artifacts() {
    log_step "Validating build artifacts..."

    if [[ ! -d "${OUTPUT_DIR}" ]]; then
        log_error "Output directory does not exist: ${OUTPUT_DIR}"
        exit 1
    fi

    local iso_path="${OUTPUT_DIR}/${ISO_FILENAME}"
    if [[ ! -f "${iso_path}" ]]; then
        log_error "ISO file not found: ${iso_path}"
        log_error "Run the ISO builder first."
        exit 1
    fi

    # Check for associated files
    local required_extensions=(
        "${ISO_FILENAME}.sha256"
        "${ISO_FILENAME}.sha512"
        "${ISO_FILENAME}.b2"
    )

    local missing=0
    for ext in "${required_extensions[@]}"; do
        if [[ ! -f "${OUTPUT_DIR}/${ext}" ]]; then
            log_warn "Checksum file missing: ${ext} — will regenerate"
            missing=$((missing + 1))
        fi
    done

    if [[ $missing -gt 0 ]]; then
        log_step "Regenerating checksums..."
        cd "${OUTPUT_DIR}"
        sha256sum "${ISO_FILENAME}" > "${ISO_FILENAME}.sha256"
        sha512sum "${ISO_FILENAME}" > "${ISO_FILENAME}.sha512"
        b2sum "${ISO_FILENAME}" > "${ISO_FILENAME}.b2"
    fi

    # Check signature
    local sig_file="${OUTPUT_DIR}/${ISO_FILENAME}.asc"
    if [[ ! -f "${sig_file}" ]]; then
        log_warn "GPG signature not found. Signing now..."
        sign_artifact "${iso_path}"
    fi

    # File size
    local iso_size
    iso_size=$(stat --format=%s "${iso_path}")
    log_info "ISO size: $(numfmt --to=iec "${iso_size}")"

    log_info "Artifacts validated successfully."
}

# --------------------------------------------------------------------------
# Signing
# --------------------------------------------------------------------------
sign_artifact() {
    local artifact="$1"

    log_step "Signing artifact: $(basename "${artifact}")"

    case "${SIGNING_KEY_STORAGE}" in
        hsm)
            # Sign using HSM (YubiHSM2 / Nitrokey)
            gpg --homedir /etc/solus/gpg \
                --default-key "${SIGNING_KEY}" \
                --detach-sign --armor \
                --digest-algo SHA512 \
                "${artifact}"
            ;;
        file)
            # Sign using key file (CI environment)
            local key_file="${SIGNING_KEY_FILE:-/etc/solus/signing-key.asc}"
            if [[ ! -f "${key_file}" ]]; then
                log_error "Signing key file not found: ${key_file}"
                return 1
            fi
            gpg --batch --yes \
                --import "${key_file}" 2>/dev/null
            gpg --batch --yes \
                --default-key "${SIGNING_KEY}" \
                --detach-sign --armor \
                --digest-algo SHA512 \
                "${artifact}"
            ;;
        agent)
            # Sign using gpg-agent (interactive)
            gpg --default-key "${SIGNING_KEY}" \
                --detach-sign --armor \
                --digest-algo SHA512 \
                "${artifact}"
            ;;
        *)
            log_error "Unknown signing key storage: ${SIGNING_KEY_STORAGE}"
            return 1
            ;;
    esac

    log_info "Signed: $(basename "${artifact}").asc"
}

# --------------------------------------------------------------------------
# Checksum generation
# --------------------------------------------------------------------------
generate_checksum_files() {
    log_step "Generating combined checksum files..."

    cd "${OUTPUT_DIR}"

    # Generate combined checksum file
    {
        echo "=========================================="
        echo " Solus Linux ${RELEASE_VERSION} - ${ISO_VARIANT}"
        echo " Architecture: ${ARCHITECTURE}"
        echo " Generated: $(date -u)"
        echo "=========================================="
        echo ""
        echo "--- SHA256 ---"
        cat "${ISO_FILENAME}.sha256"
        echo ""
        echo "--- SHA512 ---"
        cat "${ISO_FILENAME}.sha512"
        echo ""
        echo "--- BLAKE2b ---"
        cat "${ISO_FILENAME}.b2"
        echo ""
        echo "=========================================="
    } > "CHECKSUMS"

    # Sign checksums
    gpg --default-key "${SIGNING_KEY}" \
        --detach-sign --armor \
        --digest-algo SHA512 \
        "CHECKSUMS"

    log_info "Checksum files generated."
}

# --------------------------------------------------------------------------
# Torrent generation
# --------------------------------------------------------------------------
generate_torrent() {
    log_step "Generating BitTorrent metafile..."

    if ! command -v transmission-create &>/dev/null; then
        log_warn "transmission-create not found. Installing..."
        if command -v dnf &>/dev/null; then
            dnf install -y transmission-cli
        else
            log_warn "Cannot install transmission-cli. Skipping torrent generation."
            return 0
        fi
    fi

    local iso_path="${OUTPUT_DIR}/${ISO_FILENAME}"
    local torrent_path="${OUTPUT_DIR}/${ISO_PATTERN}.torrent"

    # Build tracker arguments
    local tracker_args=()
    for tracker in "${TRACKERS[@]}"; do
        tracker_args+=("--tracker" "${tracker}")
    done

    transmission-create \
        "${tracker_args[@]}" \
        --comment "Solus Linux ${RELEASE_VERSION} (${ISO_VARIANT}, ${ARCHITECTURE})" \
        --outfile "${torrent_path}" \
        "${iso_path}"

    # Sign torrent
    gpg --default-key "${SIGNING_KEY}" \
        --detach-sign --armor \
        "${torrent_path}"

    log_info "Torrent generated: $(basename "${torrent_path}")"
}

# --------------------------------------------------------------------------
# Upload to mirror origin
# --------------------------------------------------------------------------
upload_to_mirror() {
    log_step "Uploading artifacts to mirror origin..."

    local rsync_opts=(
        "-avz"
        "--progress"
        "--partial"
        "--timeout=600"
    )

    if [[ -f "${MIRROR_SSH_KEY}" ]]; then
        rsync_opts+=("-e" "ssh -i ${MIRROR_SSH_KEY} -o StrictHostKeyChecking=no")
    fi

    # Upload all files from the output directory
    rsync "${rsync_opts[@]}" \
        "${OUTPUT_DIR}/" \
        "deploy@${MIRROR_ORIGIN}:${MIRROR_PATH}"

    log_info "Upload complete."
}

# --------------------------------------------------------------------------
# CDN cache purge
# --------------------------------------------------------------------------
purge_cdn_cache() {
    log_step "Purging CDN cache..."

    if [[ -z "${CDN_API_KEY:-}" ]]; then
        log_warn "CDN_API_KEY not set. Skipping CDN cache purge."
        return 0
    fi

    if [[ -z "${CDN_ZONE_ID:-}" ]]; then
        log_warn "CDN_ZONE_ID not set. Skipping CDN cache purge."
        return 0
    fi

    local cdn_urls=(
        "https://cdn.solus.org/releases/${RELEASE_VERSION}/"
        "https://cdn.solus.org/releases/latest/"
    )

    for url in "${cdn_urls[@]}"; do
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${CDN_API_KEY}" \
            -d "$(jq -n --arg url "${url}" '{urls: [$url]}')" \
            "https://api.bunny.net/pullzone/${CDN_ZONE_ID}/purge" \
            && log_info "CDN cache purged for: ${url}" \
            || log_warn "CDN purge failed for: ${url}"
    done
}

# --------------------------------------------------------------------------
# Mirror sync trigger
# --------------------------------------------------------------------------
trigger_mirror_sync() {
    log_step "Triggering regional mirror sync..."

    if [[ -z "${MIRROR_API_KEY:-}" ]]; then
        log_warn "MIRROR_API_KEY not set. Skipping mirror sync trigger."
        return 0
    fi

    curl -s -X POST \
        -H "Authorization: Bearer ${MIRROR_API_KEY}" \
        "https://admin.solus.org/api/mirrors/sync" \
        && log_info "Mirror sync triggered successfully." \
        || log_warn "Mirror sync trigger failed."
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
main() {
    echo "============================================"
    echo "  Solus Linux — ISO Upload & Mirror Sync"
    echo "============================================"
    echo ""
    echo "Version:     ${RELEASE_VERSION}"
    echo "Variant:     ${ISO_VARIANT}"
    echo "Arch:        ${ARCHITECTURE}"
    echo "ISO:         ${ISO_FILENAME}"
    echo "Output:      ${OUTPUT_DIR}"
    echo "Mirror:      ${MIRROR_ORIGIN}:${MIRROR_PATH}"
    echo ""

    check_prerequisites
    validate_artifacts
    generate_checksum_files
    generate_torrent
    upload_to_mirror
    purge_cdn_cache
    trigger_mirror_sync

    echo ""
    echo "============================================"
    echo "  Upload Complete!"
    echo "============================================"
    echo ""
    echo "ISO URL:  https://cdn.solus.org/releases/${RELEASE_VERSION}/${ISO_FILENAME}"
    echo "Torrent:  https://cdn.solus.org/releases/${RELEASE_VERSION}/${ISO_PATTERN}.torrent"
    echo ""

    # Generate a quick verification snippet
    cat << VERIFY
To verify the download:
  wget https://cdn.solus.org/releases/${RELEASE_VERSION}/${ISO_FILENAME}
  wget https://cdn.solus.org/releases/${RELEASE_VERSION}/${ISO_FILENAME}.asc
  gpg --verify ${ISO_FILENAME}.asc ${ISO_FILENAME}
  sha256sum -c ${ISO_FILENAME}.sha256
VERIFY
}

main "$@"
