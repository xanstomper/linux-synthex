#!/usr/bin/env bash
# ============================================================================
# SynthOS — ISO Builder Configuration
# ============================================================================
# Central configuration for the ISO build process. Sources kickstart files,
# repository configuration, and build parameters.
# ============================================================================
set -euo pipefail

# --------------------------------------------------------------------------
# Build Parameters
# --------------------------------------------------------------------------
# Release version (e.g., 2026.1, nightly-20260704)
RELEASE_VERSION="${RELEASE_VERSION:-nightly-$(date +%Y%m%d)}"

# ISO variant to build: minimal, standard, full, netinstall
ISO_VARIANT="${ISO_VARIANT:-standard}"

# Target architecture: x86_64-v3, x86_64-v4, aarch64
ARCHITECTURE="${ARCHITECTURE:-x86_64-v3}"

# Build type: release, nightly, testing
BUILD_TYPE="${BUILD_TYPE:-nightly}"

# Output directory for built ISOs
OUTPUT_DIR="${OUTPUT_DIR:-/var/tmp/synthex-iso}"

# Cache directory for package downloads
CACHE_DIR="${CACHE_DIR:-/var/cache/livecd}"

# Temporary build directory
WORK_DIR="${WORK_DIR:-/var/tmp/synthex-build}"

# Log directory
LOG_DIR="${LOG_DIR:-/var/log/synthex-iso-builder}"

# --------------------------------------------------------------------------
# Repository Configuration
# --------------------------------------------------------------------------
# Base URL for Synthex package repositories
REPO_BASE="${REPO_BASE:-https://repo.synthex.org}"

# Additional repositories for build-time dependencies
BUILD_REPOS=(
    "${REPO_BASE}/rawhide/${ARCHITECTURE}"
)

# Optional: local repository for pre-cached packages
LOCAL_REPO="${LOCAL_REPO:-}"

# --------------------------------------------------------------------------
# Container / Build Environment
# --------------------------------------------------------------------------
# Container image for the ISO builder
BUILDER_IMAGE="${BUILDER_IMAGE:-ghcr.io/synthex-linux/iso-builder:latest}"

# Container runtime (podman or docker)
CONTAINER_RUNTIME="${CONTAINER_RUNTIME:-podman}"

# Privileged mode required (mount, loop devices)
CONTAINER_PRIVILEGED=true

# --------------------------------------------------------------------------
# Compression and Format
# --------------------------------------------------------------------------
# SquashFS compression: xz, zstd, gzip, lzo
SQUASHFS_COMPRESSION="${SQUASHFS_COMPRESSION:-xz}"

# ISO filesystem: iso9660, udf
ISO_FILESYSTEM="${ISO_FILESYSTEM:-iso9660}"

# Bootloader: grub, isolinux, both
BOOTLOADER="${BOOTLOADER:-grub}"

# --------------------------------------------------------------------------
# ISO Naming
# --------------------------------------------------------------------------
# ISO filename pattern
ISO_PATTERN="synthex-linux-${RELEASE_VERSION}-${ISO_VARIANT}-${ARCHITECTURE}"

# Full ISO filename
ISO_FILENAME="${ISO_PATTERN}.iso"

# --------------------------------------------------------------------------
# Signing Configuration
# --------------------------------------------------------------------------
# GPG key to use for signing (ID or email)
SIGNING_KEY="${SIGNING_KEY:-Synthex ISO <iso@synthex.org>}"

# Signing key storage (hsm, file, agent)
SIGNING_KEY_STORAGE="${SIGNING_KEY_STORAGE:-agent}"

# HSM slot (if using YubiHSM2 / Nitrokey)
SIGNING_HSM_SLOT="${SIGNING_HSM_SLOT:-0}"

# --------------------------------------------------------------------------
# Torrent Configuration
# --------------------------------------------------------------------------
# BitTorrent trackers
TRACKERS=(
    "udp://tracker.synthex.org:6969/announce"
    "udp://tracker.opentrackr.org:1337/announce"
    "https://tracker.synthex.org:443/announce"
)

# Webseed URLs (for direct download fallback)
WEBSEED_URL="${WEBSEED_URL:-https://cdn.synthex.org/releases/${RELEASE_VERSION}/}"

# --------------------------------------------------------------------------
# Mirror Sync
# --------------------------------------------------------------------------
# Primary repository server
MIRROR_ORIGIN="${MIRROR_ORIGIN:-repo.synthex.org}"

# Rsync target path on mirror
MIRROR_PATH="${MIRROR_PATH:-/repo/synthex/releases/${RELEASE_VERSION}/}"

# SSH key for mirror deployment
MIRROR_SSH_KEY="${MIRROR_SSH_KEY:-/etc/synthex/deploy-key}"

# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
validate_config() {
    local errors=0

    if [[ -z "${RELEASE_VERSION}" ]]; then
        echo "ERROR: RELEASE_VERSION is not set"
        errors=$((errors + 1))
    fi

    case "${ISO_VARIANT}" in
        minimal|standard|full|netinstall) ;;
        *)
            echo "ERROR: Invalid ISO_VARIANT: ${ISO_VARIANT}"
            echo "  Valid options: minimal, standard, full, netinstall"
            errors=$((errors + 1))
            ;;
    esac

    case "${ARCHITECTURE}" in
        x86_64-v3|x86_64-v4|aarch64) ;;
        *)
            echo "ERROR: Invalid ARCHITECTURE: ${ARCHITECTURE}"
            echo "  Valid options: x86_64-v3, x86_64-v4, aarch64"
            errors=$((errors + 1))
            ;;
    esac

    case "${BUILD_TYPE}" in
        release|nightly|testing) ;;
        *)
            echo "ERROR: Invalid BUILD_TYPE: ${BUILD_TYPE}"
            errors=$((errors + 1))
            ;;
    esac

    if [[ ! -d "${WORK_DIR}" ]]; then
        mkdir -p "${WORK_DIR}"
    fi

    if [[ ! -d "${OUTPUT_DIR}" ]]; then
        mkdir -p "${OUTPUT_DIR}"
    fi

    if [[ ! -d "${LOG_DIR}" ]]; then
        mkdir -p "${LOG_DIR}"
    fi

    if [[ $errors -gt 0 ]]; then
        echo "ERROR: ${errors} configuration error(s) found. Aborting."
        exit 1
    fi

    echo "Configuration validated successfully."
}

# --------------------------------------------------------------------------
# Environment Setup
# --------------------------------------------------------------------------
export RELEASE_VERSION
export ISO_VARIANT
export ARCHITECTURE
export BUILD_TYPE
export OUTPUT_DIR
export CACHE_DIR
export WORK_DIR
export LOG_DIR
export REPO_BASE
export SQUASHFS_COMPRESSION
export ISO_FILENAME
export ISO_PATTERN
export SIGNING_KEY

# Run validation if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    validate_config

    echo ""
    echo "============================================"
    echo "  Synthex ISO Builder Configuration"
    echo "============================================"
    echo ""
    echo "Release Version:    ${RELEASE_VERSION}"
    echo "ISO Variant:        ${ISO_VARIANT}"
    echo "Architecture:       ${ARCHITECTURE}"
    echo "Build Type:         ${BUILD_TYPE}"
    echo "Output Directory:   ${OUTPUT_DIR}"
    echo "ISO Filename:       ${ISO_FILENAME}"
    echo ""
    echo "SquashFS Compress:  ${SQUASHFS_COMPRESSION}"
    echo "Bootloader:         ${BOOTLOADER}"
    echo "Signing Key:        ${SIGNING_KEY}"
    echo ""
    echo "Configuration file is valid."
    echo "============================================"
fi
