#!/usr/bin/env bash
set -euo pipefail

# SynthOS Repository Setup Script
# Configures DNF repositories, imports GPG keys, and sets up
# repository priority for SynthOS package management.

REPO_BASE="${REPO_BASE:-https://repo.synthex.org}"
GPG_KEY_URL="${GPG_KEY_URL:-${REPO_BASE}/synthex-release-key.asc}"
DNF_REPO_DIR="/etc/yum.repos.d"
RPM_GPG_DIR="/etc/pki/rpm-gpg"

log_info()  { echo -e "\033[1;32m[INFO]\033[0m $*"; }
log_warn()  { echo -e "\033[1;33m[WARN]\033[0m $*"; }
log_error() { echo -e "\033[1;31m[ERROR]\033[0m $*"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root."
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing dependencies..."
    if command -v dnf &>/dev/null; then
        dnf install -y dnf-plugins-core gnupg2 curl ca-certificates
    elif command -v yum &>/dev/null; then
        yum install -y yum-utils gnupg2 curl ca-certificates
    else
        log_error "No supported package manager found (dnf/yum)."
        exit 1
    fi
    log_info "Dependencies installed."
}

import_gpg_key() {
    log_info "Importing SynthOS GPG signing key..."

    mkdir -p "${RPM_GPG_DIR}"
    local key_path="${RPM_GPG_DIR}/RPM-GPG-KEY-synthex"

    if curl -fsSL "${GPG_KEY_URL}" -o "${key_path}"; then
        rpm --import "${key_path}"
        log_info "GPG key imported from ${GPG_KEY_URL}"
    else
        log_warn "Could not download GPG key from ${GPG_KEY_URL}"
        log_warn "Using bundled key if available..."
        if [[ -f "/usr/share/synthex/RPM-GPG-KEY-synthex" ]]; then
            rpm --import "/usr/share/synthex/RPM-GPG-KEY-synthex"
            log_info "Bundled GPG key imported."
        else
            log_error "No GPG key available. Repository GPG check may fail."
        fi
    fi
}

install_repo_file() {
    log_info "Installing repository configuration..."

    local repo_file="${DNF_REPO_DIR}/synthex.repo"

    cat > "${repo_file}" << 'REPO'
[synthex-rawhide]
name=SynthOS Rolling (rawhide) - $basearch
baseurl=https://repo.synthex.org/rawhide/$basearch
metalink=https://mirrors.synthex.org/metalink?repo=rawhide&arch=$basearch
enabled=1
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=1
type=rpmmd
autorefresh=yes
keepcache=0

[synthex-stable]
name=SynthOS Stable - $basearch
baseurl=https://repo.synthex.org/stable/$releasever/$basearch
metalink=https://mirrors.synthex.org/metalink?repo=stable-$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=5
type=rpmmd
autorefresh=yes

[synthex-updates]
name=SynthOS Updates - $basearch
baseurl=https://repo.synthex.org/updates/$releasever/$basearch
metalink=https://mirrors.synthex.org/metalink?repo=updates-$releasever&arch=$basearch
enabled=1
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=5
type=rpmmd
autorefresh=yes

[synthex-testing]
name=SynthOS Testing - $basearch
baseurl=https://repo.synthex.org/testing/$releasever/$basearch
metalink=https://mirrors.synthex.org/metalink?repo=testing-$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=10
type=rpmmd
autorefresh=yes

[synthex-backports]
name=SynthOS Backports - $basearch
baseurl=https://repo.synthex.org/backports/$releasever/$basearch
metalink=https://mirrors.synthex.org/metalink?repo=backports-$releasever&arch=$basearch
enabled=0
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=15
type=rpmmd
autorefresh=yes

[synthex-source]
name=SynthOS Source - SRPMS
baseurl=https://repo.synthex.org/rawhide/SRPMS
enabled=1
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
repo_gpgcheck=1
priority=99
type=rpm-md
autorefresh=yes
REPO

    chmod 644 "${repo_file}"
    log_info "Repository file installed: ${repo_file}"
}

configure_dnf() {
    log_info "Configuring DNF defaults for Synthex..."

    local dnf_conf="/etc/dnf/dnf.conf"

    # Set Synthex-appropriate defaults
    if grep -q "^max_parallel_downloads" "${dnf_conf}" 2>/dev/null; then
        sed -i 's/^max_parallel_downloads=.*/max_parallel_downloads=10/' "${dnf_conf}"
    else
        echo "max_parallel_downloads=10" >> "${dnf_conf}"
    fi

    if grep -q "^fastestmirror" "${dnf_conf}" 2>/dev/null; then
        sed -i 's/^fastestmirror=.*/fastestmirror=True/' "${dnf_conf}"
    else
        echo "fastestmirror=True" >> "${dnf_conf}"
    fi

    if grep -q "^deltarpm" "${dnf_conf}" 2>/dev/null; then
        sed -i 's/^deltarpm=.*/deltarpm=True/' "${dnf_conf}"
    else
        echo "deltarpm=True" >> "${dnf_conf}"
    fi

    log_info "DNF configured."
}

verify_repository() {
    log_info "Verifying repository configuration..."

    if command -v dnf &>/dev/null; then
        dnf repolist 2>&1 | grep -i synthex || {
            log_warn "Synthex repositories not visible in repolist."
            log_warn "Check: dnf repolist"
        }

        # Test repository access
        if dnf --disablerepo='*' --enablerepo=synthex-rawhide makecache 2>&1; then
            log_info "Repository reachable and metadata cached."
        else
            log_warn "Repository not reachable. Check network/firewall."
        fi
    fi
}

main() {
    echo "============================================"
    echo "  SynthOS Repository Setup"
    echo "============================================"
    echo ""

    check_root
    install_dependencies
    import_gpg_key
    install_repo_file
    configure_dnf
    verify_repository

    echo ""
    echo "============================================"
    echo "  Setup Complete!"
    echo "============================================"
    echo ""
    echo "Synthex repositories are now configured on this system."
    echo ""
    echo "Quick start:"
    echo "  dnf install synthex-meta-standard    # Install standard desktop"
    echo "  dnf search synthex                   # List available packages"
    echo "  dnf update                         # Update all packages"
    echo ""
}

main "$@"
