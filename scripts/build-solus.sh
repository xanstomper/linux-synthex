#!/usr/bin/env bash
# Solus Linux Build System — produces a bootable Solus rootfs
# Works on any Linux host with Docker installed.
#
# Usage:
#   # Build the builder container (once)
#   bash build-solus.sh docker-build
#
#   # Build a bootable rootfs tarball
#   bash build-solus.sh build-rootfs
#
#   # Build ISO (requires privileged Docker)
#   bash build-solus.sh build-iso
#
#   # Run integration tests
#   bash build-solus.sh test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${PROJECT_DIR}/build/out"
CONTAINER_NAME="solus-builder"
IMAGE_NAME="solus-builder:latest"

mkdir -p "$OUTPUT_DIR"

case "${1:-help}" in
    docker-build)
        echo "🐳 Building Solus builder container..."
        docker build -t "$IMAGE_NAME" -f "${PROJECT_DIR}/build/livecd/Dockerfile" "$PROJECT_DIR"
        echo "✅ Builder container ready"
        echo "   Run: bash build-solus.sh build-rootfs"
        ;;
    
    build-rootfs)
        echo "📦 Building Solus rootfs..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG \
            -v "${PROJECT_DIR}:/solus:ro" \
            -v "${OUTPUT_DIR}:/output" \
            "$IMAGE_NAME" \
            bash /solus/scripts/build-rootfs-in-docker.sh
        echo "✅ Rootfs built: ${OUTPUT_DIR}/"
        ls -lh "${OUTPUT_DIR}/" 2>/dev/null || true
        ;;
    
    build-iso)
        echo "💿 Building Solus ISO..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG --privileged \
            -v "${PROJECT_DIR}:/solus:ro" \
            -v "${OUTPUT_DIR}:/output" \
            "$IMAGE_NAME" \
            bash /solus/scripts/build-iso-in-docker.sh
        echo "✅ ISO built: ${OUTPUT_DIR}/"
        ls -lh "${OUTPUT_DIR}/"*.iso 2>/dev/null || true
        ;;
    
    test)
        echo "🧪 Running Solus integration tests..."
        TTY_FLAG=""
        [ -t 0 ] && TTY_FLAG="-it"
        docker run --rm $TTY_FLAG \
            -v "${PROJECT_DIR}:/solus:ro" \
            "$IMAGE_NAME" \
            bash -c "cd /solus && python3 tests/run-tests.py"
        ;;
    
    shell)
        echo "🔧 Starting shell in builder container..."
        docker run --rm -it \
            -v "${PROJECT_DIR}:/solus" \
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
        echo "Solus Linux Build System"
        echo ""
        echo "Usage: bash build-solus.sh <command>"
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
        echo "  1. bash build-solus.sh docker-build"
        echo "  2. bash build-solus.sh build-rootfs"
        echo "  3. bash build-solus.sh build-iso"
        echo ""
        echo "Output goes to: ${OUTPUT_DIR}/"
        ;;
esac
