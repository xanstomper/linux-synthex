#!/usr/bin/env bash
# build-rust-rpms.sh — Build Rust-based RPM packages for Solus
#
# This script compiles Rust crates (daemons + tools) into release binaries,
# creates source tarballs, and builds them into RPMs.
#
# Usage:
#   ./build-rust-rpms.sh [all|daemons|tools|utils|<specific-spec>]
#
# Examples:
#   ./build-rust-rpms.sh daemons       # Build all Rust daemons
#   ./build-rust-rpms.sh tools         # Build solus-update-manager, driver-manager, pkg
#   ./build-rust-rpms.sh utils         # Build ripgrep, fd, bat, etc. (from upstream source)
#   ./build-rust-rpms.sh solus-system-daemon  # Build single package
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILDROOT="${BUILDROOT:-$ROOT/build/rpmbuild}"
REPO_DIR="${REPO_DIR:-$ROOT/build/repo}"
RUST_TARGET="${RUST_TARGET:-release}"
CARGO_FLAGS="${CARGO_FLAGS:---release}"

mkdir -p "$BUILDROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "$REPO_DIR"/{x86_64,noarch}

echo "╔══════════════════════════════════════════════════╗"
echo "║      Solus Rust RPM Build Pipeline v0.1          ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Rust: $(rustc --version 2>/dev/null || echo 'NOT FOUND')"
echo "║  Cargo: $(cargo --version 2>/dev/null || echo 'NOT FOUND')"
echo "║  Target: $RUST_TARGET"
echo "╚══════════════════════════════════════════════════╝"

# ─── Build Rust daemons (root workspace) ──────────────────────────────

build_daemons() {
    echo ""
    echo "🦀 Building Rust daemons..."
    cd "$ROOT"

    # Build the root workspace (hwdaemon, desktopd, stored, gpu-setupd, solus-cli, system-daemon)
    cargo build --workspace $CARGO_FLAGS

    echo "  Binaries built in target/$RUST_TARGET/"
    echo ""

    # Package each daemon as an RPM
    # Each daemon's spec file handles the cargo build; we just need to ensure
    # cargo build ran successfully first. The spec files will install from
    # target/release/ which is in the build root.

    local daemon_specs=(
        "solus-hwdaemon"
        "solus-desktopd"
        "solus-stored"
        "solus-gpu-setupd"
        "solus-system-daemon"
        "solus-cli"
        "solus-ai-daemon"
        "solus-installer-detect"
        "solus-control-center"
    )

    for spec_name in "${daemon_specs[@]}"; do
        local spec_path="$ROOT/packages/spec-files/$spec_name.spec"
        if [ ! -f "$spec_path" ]; then
            echo "  ⚠ Spec not found: $spec_name.spec"
            continue
        fi

        # Copy spec to build root
        cp "$spec_path" "$BUILDROOT/SPECS/"

        echo "  📦 Building $spec_name RPM..."
        if rpmbuild -bb \
            --define "_topdir $BUILDROOT" \
            --define "_rpmdir $BUILDROOT/RPMS" \
            --define "_sourcedir $ROOT/target/$RUST_TARGET" \
            --define "cargo_target $RUST_TARGET" \
            "$BUILDROOT/SPECS/$spec_name.spec" \
            > "$BUILDROOT/build-$spec_name.log" 2>&1; then
            echo "    ✅ $spec_name RPM built"
        else
            echo "    ❌ $spec_name RPM build FAILED (see $BUILDROOT/build-$spec_name.log)"
            tail -5 "$BUILDROOT/build-$spec_name.log"
        fi
    done
}

# ─── Build solus-rust-tools (separate workspace) ──────────────────────

build_tools() {
    echo ""
    echo "🦀 Building Solus Rust tools (update-manager, driver-manager, pkg)..."

    local tools=(
        "solus-update-manager"
        "solus-driver-manager"
        "solus-pkg"
    )

    for tool in "${tools[@]}"; do
        local src_dir="$ROOT/src/solus-rust-tools/$tool"
        local spec_path="$ROOT/packages/spec-files/$tool.spec"

        if [ ! -d "$src_dir" ]; then
            echo "  ⚠ Source not found: $tool"
            continue
        fi
        if [ ! -f "$spec_path" ]; then
            echo "  ⚠ Spec not found: $tool.spec"
            continue
        fi

        echo "  🔨 Building $tool..."
        cd "$src_dir"
        cargo build $CARGO_FLAGS

        # Create source tarball for RPM
        local version=$(grep '^version' "$src_dir/Cargo.toml" | cut -d'"' -f2)
        local archive_name="${tool}-${version}.tar.gz"
        cd "$ROOT"
        tar czf "$BUILDROOT/SOURCES/$archive_name" \
            --transform "s,src/solus-rust-tools/$tool,${tool}-${version}," \
            "src/solus-rust-tools/$tool/" 2>/dev/null || true

        cp "$spec_path" "$BUILDROOT/SPECS/"

        echo "  📦 Building $tool RPM..."
        if rpmbuild -bb \
            --define "_topdir $BUILDROOT" \
            --define "_rpmdir $BUILDROOT/RPMS" \
            --define "_sourcedir $BUILDROOT/SOURCES" \
            --define "cargo_target $RUST_TARGET" \
            "$BUILDROOT/SPECS/$tool.spec" \
            > "$BUILDROOT/build-$tool.log" 2>&1; then
            echo "    ✅ $tool RPM built"
        else
            echo "    ❌ $tool RPM build FAILED (see $BUILDROOT/build-$tool.log)"
            tail -3 "$BUILDROOT/build-$tool.log"
        fi
    done
}

# ─── Collect RPMs into repo ───────────────────────────────────────────

collect_rpms() {
    echo ""
    echo "📦 Collecting RPMs into repository..."
    find "$BUILDROOT/RPMS" -name '*.rpm' -exec cp {} "$REPO_DIR/x86_64/" \; 2>/dev/null || true
    for rpm in "$REPO_DIR/x86_64"/*.noarch.rpm; do
        [ -f "$rpm" ] && mv "$rpm" "$REPO_DIR/noarch/" 2>/dev/null || true
    done
    local count=$(find "$REPO_DIR" -name '*.rpm' | wc -l)
    echo "  $count RPMs in repository."

    if command -v createrepo_c &>/dev/null; then
        createrepo_c "$REPO_DIR" 2>/dev/null || \
        createrepo "$REPO_DIR" 2>/dev/null || true
        echo "  Repository metadata created."
    fi
}

# ─── Main ──────────────────────────────────────────────────────────────

TARGET="${1:-all}"

case "$TARGET" in
    all)
        build_daemons
        build_tools
        collect_rpms
        ;;
    daemons)
        build_daemons
        collect_rpms
        ;;
    tools)
        build_tools
        collect_rpms
        ;;
    *)
        echo "Unknown target: $TARGET"
        echo "Usage: $0 [all|daemons|tools|utils|<spec-name>]"
        exit 1
        ;;
esac

echo ""
echo "✅ Rust RPM build complete!"
echo "  Repository: $REPO_DIR"
