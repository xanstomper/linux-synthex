#!/usr/bin/env bash
# ============================================================================
# SynthOS — Copr Repository Setup Script
# ============================================================================
# Configures Fedora Copr build service for SynthOS packages.
# Creates projects for each repository stream and architecture.
# ============================================================================
set -euo pipefail

# Configuration
COPR_OWNER="${COPR_OWNER:-@synthex}"
COPR_API_TOKEN="${COPR_API_TOKEN:?Must set COPR_API_TOKEN}"
COPR_API_URL="https://copr.fedorainfracloud.org/api_3"

REPOSITORIES=(
    "rawhide"
    "stable"
    "updates"
    "testing"
    "backports"
)

ARCHITECTURES=(
    "x86_64-v3"
    "x86_64-v4"
    "aarch64"
)

CHROOTS=(
    "fedora-rawhide-x86_64"
    "fedora-40-x86_64"
    "fedora-39-x86_64"
    "epel-9-x86_64"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --------------------------------------------------------------------------
# Prerequisite checks
# --------------------------------------------------------------------------
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v curl &>/dev/null; then
        log_error "curl is required but not installed."
        exit 1
    fi

    if ! command -v jq &>/dev/null; then
        log_error "jq is required but not installed."
        exit 1
    fi

    if ! command -v copr &>/dev/null; then
        log_warn "copr CLI not found. Installing..."
        if command -v dnf &>/dev/null; then
            dnf install -y copr-cli
        elif command -v pip3 &>/dev/null; then
            pip3 install copr-cli
        else
            log_error "Cannot install copr-cli. Install manually: dnf install copr-cli"
            exit 1
        fi
    fi

    # Verify API token
    if [[ ! -f ~/.config/copr ]]; then
        log_info "Configuring Copr API token..."
        mkdir -p ~/.config
        cat > ~/.config/copr << EOF
[copr-cli]
login = ${COPR_OWNER}
username = ${COPR_OWNER#@}
token = ${COPR_API_TOKEN}
copr_url = ${COPR_API_URL}
EOF
        chmod 600 ~/.config/copr
    fi

    log_info "All prerequisites met."
}

# --------------------------------------------------------------------------
# Create or update a Copr project
# --------------------------------------------------------------------------
create_project() {
    local repo="$1"
    local project_name="synthex-${repo}"
    local description="$2"

    log_info "Creating/updating Copr project: ${project_name}"

    # Check if project exists
    if copr list "${COPR_OWNER}" 2>/dev/null | grep -q "${project_name}"; then
        log_warn "Project ${project_name} already exists. Updating..."
        copr modify \
            --description "${description}" \
            --disable_createrepo 0 \
            --delete_after_days 0 \
            --chroots "$(IFS=, ; echo "${CHROOTS[*]}")" \
            --develproject "${COPR_OWNER}/synthex-rawhide" \
            --appstream 1 \
            "${COPR_OWNER}/${project_name}" || true
    else
        log_info "Creating project: ${project_name}"
        copr create \
            --description "${description}" \
            --disable_createrepo 0 \
            --delete_after_days 0 \
            --chroots "$(IFS=, ; echo "${CHROOTS[*]}")" \
            --develproject "${COPR_OWNER}/synthex-rawhide" \
            --appstream 1 \
            --enable_net 1 \
            --packages_namespace "synthex" \
            --homepage "https://synthex.org" \
            --contact "packaging@synthex.org" \
            "${COPR_OWNER}/${project_name}"
    fi

    log_info "Project ${project_name} configured successfully."
}

# --------------------------------------------------------------------------
# Configure build permissions
# --------------------------------------------------------------------------
configure_project_permissions() {
    local repo="$1"
    local project_name="synthex-${repo}"

    log_info "Configuring permissions for ${project_name}..."

    # Set default builder: only allow Synthex team members
    curl -s -X PUT \
        -H "Content-Type: application/json" \
        -H "Authorization: token ${COPR_API_TOKEN}" \
        -d '{
            "builder_builders": "synthex-team",
            "permissions": {
                "builder": ["@synthex-team"],
                "admin": ["@synthex-admin"]
            }
        }' \
        "${COPR_API_URL}/project/${COPR_OWNER}/${project_name}/permissions" \
        > /dev/null

    log_info "Permissions configured for ${project_name}."
}

# --------------------------------------------------------------------------
# Set up webhook integration with GitHub
# --------------------------------------------------------------------------
setup_webhooks() {
    local repo="$1"
    local project_name="synthex-${repo}"

    log_info "Setting up GitHub webhook for ${project_name}..."

    # Register the Copr webhook URL in GitHub (requires GitHub token)
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        curl -s -X POST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -H "Accept: application/vnd.github.v3+json" \
            -d "{
                \"name\": \"web\",
                \"active\": true,
                \"events\": [\"push\", \"pull_request\"],
                \"config\": {
                    \"url\": \"${COPR_API_URL}/webhooks/github/${COPR_OWNER}/${project_name}\",
                    \"content_type\": \"json\",
                    \"secret\": \"${COPR_WEBHOOK_SECRET:-}\"
                }
            }" \
            "https://api.github.com/repos/synthex-linux/packages/hooks" \
            > /dev/null || log_warn "Failed to create webhook (may already exist)"
    else
        log_warn "GITHUB_TOKEN not set. Skipping webhook setup."
    fi

    log_info "Webhook configured for ${project_name}."
}

# --------------------------------------------------------------------------
# Main setup routine
# --------------------------------------------------------------------------
main() {
    echo "============================================"
    echo "  SynthOS — Copr Repository Setup"
    echo "============================================"
    echo ""

    check_prerequisites

    # Process each repository stream
    for repo in "${REPOSITORIES[@]}"; do
        echo ""
        echo "--- Processing: ${repo} ---"

        case "${repo}" in
            rawhide)
                desc="SynthOS rolling development stream (rawhide)"
                ;;
            stable)
                desc="SynthOS stable releases"
                ;;
            updates)
                desc="SynthOS security and bugfix updates"
                ;;
            testing)
                desc="SynthOS pre-release testing repository"
                ;;
            backports)
                desc="SynthOS backported packages for older releases"
                ;;
        esac

        create_project "${repo}" "${desc}"
        configure_project_permissions "${repo}"
        setup_webhooks "${repo}"

        log_info "Repository ${repo} setup complete."
    done

    echo ""
    echo "============================================"
    echo "  Copr Repository Setup Complete!"
    echo "============================================"
    echo ""
    echo "Created projects:"
    for repo in "${REPOSITORIES[@]}"; do
        echo "  - ${COPR_OWNER}/synthex-${repo}"
    done
    echo ""
    echo "Chroots configured:"
    for chroot in "${CHROOTS[@]}"; do
        echo "  - ${chroot}"
    done
    echo ""

    # Print usage instructions
    cat << 'USAGE'

To build a package in Copr:
  copr build @synthex/synthex-rawhide path/to/package.src.rpm

To enable the Copr repo on a system:
  dnf copr enable @synthex/synthex-rawhide

To build directly from a Git repository:
  copr buildscm --clone-url https://github.com/synthex-linux/packages \
    --commit main --subdir packages/package-name \
    --spec package-name.spec \
    @synthex/synthex-rawhide

USAGE
}

main "$@"
