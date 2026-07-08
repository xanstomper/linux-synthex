#!/usr/bin/env bash
# SynthOS Build System — produces a bootable Synthex rootfs
# Works on any Linux host with Docker installed.
#
# Usage:
#   # Build the builder container (once)
#   bash build-synthex.sh docker-build
#
#   # Build a bootable rootfs tarball
#   bash build-synthex.sh build-rootfs
#
#   # Build ISO (requires privileged Docker)
#   bash build-synthex.sh build-iso
#
#   # Run integration tests
#   bash build-synthex.sh test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_DIR}/build/out"
CONTAINER_NAME="synthex-builder"
IMAGE_NAME="synthex-builder:latest"

mkdir -p "$OUTPUT_DIR"

case "${1:-help}" in
    docker-build)
        echo "🐳 Building Synthex builder container..."
        docker build -t "$IMAGE_NAME" -f "${PROJECT_DIR}/build/livecd/Dockerfile" "$PROJECT_DIR"
        echo "✅ Builder container ready"
        echo "   Run: bash build-synthex.sh build-rootfs"
        ;;
    
    build-rootfs)
        echo "📦 Building Synthex rootfs..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG \
            -v "${PROJECT_DIR}:/synthex:ro" \
            -v "${OUTPUT_DIR}:/output" \
            "$IMAGE_NAME" \
            bash /synthex/scripts/build-rootfs-in-docker.sh
        echo "✅ Rootfs built: ${OUTPUT_DIR}/"
        ls -lh "${OUTPUT_DIR}/" 2>/dev/null || true
        ;;
    
    build-iso)
        echo "💿 Building Synthex ISO..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG --privileged \
            -v "${PROJECT_DIR}:/synthex:ro" \
            -v "${OUTPUT_DIR}:/output" \
            "$IMAGE_NAME" \
            bash /synthex/scripts/build-iso-in-docker.sh
        echo "✅ ISO built: ${OUTPUT_DIR}/"
        ls -lh "${OUTPUT_DIR}/"*.iso 2>/dev/null || true
        ;;
    
    test)
        echo "🧪 Running Synthex integration tests..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG \
            -v "${PROJECT_DIR}:/synthex:ro" \
            "$IMAGE_NAME" \
            bash -c "cd /synthex && python3 tests/run-tests.py"
        ;;
    
    shell)
        echo "🔧 Starting shell in builder container..."
        docker run --rm -it \
            -v "${PROJECT_DIR}:/synthex" \
            -v "${OUTPUT_DIR}:/output" \
            "$IMAGE_NAME" \
            /bin/bash
        ;;
    
    clean)
        echo "🧹 Cleaning..."
        rm -rf "${OUTPUT_DIR:?}/"*
        echo "✅ Cleaned ${OUTPUT_DIR}/"
        ;;
    
    *)
        echo "SynthOS Build System"
        echo ""
        echo "Usage: bash build-synthex.sh <command>"
        echo ""
        echo "Commands:"
        echo "  docker-build    Build the Docker builder container"
        echo "  build-rootfs    Build bootable rootfs tarball"
        echo "  build-iso       Build bootable ISO"
        echo "  test            Run integration tests"
        echo "  shell           Open shell in builder container"
        echo "  clean           Clean build output"
        echo ""
        echo "Step-by-step:"
        echo "  1. bash build-synthex.sh docker-build"
        echo "  2. bash build-synthex.sh build-rootfs"
        echo "  3. bash build-synthex.sh build-iso"
        echo ""
        echo "Output goes to: ${OUTPUT_DIR}/"
        ;;
esac
