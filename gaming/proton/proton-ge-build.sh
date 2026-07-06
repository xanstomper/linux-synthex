#!/usr/bin/env bash
# ============================================================
# Solus Linux — Proton GE Build Script
# /usr/share/solus-gaming/proton-ge-build.sh
#
# Builds Custom Proton (Proton GE) from source with
# optimizations for the Solus platform.
#
# Part of solus-gaming-tools package.
# ============================================================

set -euo pipefail

# --- Configuration ---
BUILD_DIR="${BUILD_DIR:-$HOME/proton-ge-build}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.steam/root/compatibilitytools.d}"
WORK_DIR="${BUILD_DIR}/work"
LOGS_DIR="${BUILD_DIR}/logs"
DIST_DIR="${BUILD_DIR}/dist"

# Git repositories
PROTON_REPO="https://github.com/ValveSoftware/Proton.git"
PROTON_WINE_REPO="https://github.com/GloriousEggroll/proton-wine.git"
DXVK_REPO="https://github.com/doitsujin/dxvk.git"
VKD3D_PROTON_REPO="https://github.com/HansKristian-Work/vkd3d-proton.git"
WINE_PROTON_REPO="https://github.com/Kise1e/wine-proton.git"

# Version tags (can be overridden)
PROTON_VERSION="${PROTON_VERSION:-9.0}"
PROTON_GE_TAG="${PROTON_GE_TAG:-GE-Proton9-25}"
DXVK_VERSION="${DXVK_VERSION:-2.5.1}"
VKD3D_VERSION="${VKD3D_VERSION:-2.14.1}"

# Build options
BUILD_THREADS="${BUILD_THREADS:-$(nproc)}"
BUILD_TYPE="${BUILD_TYPE:-release}"
ENABLE_DXVK="${ENABLE_DXVK:-1}"
ENABLE_VKD3D="${ENABLE_VKD3D:-1}"
ENABLE_WAYLAND="${ENABLE_WAYLAND:-1}"
ENABLE_MEDIA="${ENABLE_MEDIA:-1}"  # Media Foundation support

# ============================================================
# LOGGING
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()     { echo -e "${GREEN}[INFO]${NC}  $(date +'%H:%M:%S') $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $(date +'%H:%M:%S') $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $(date +'%H:%M:%S') $*"; }
section() { echo -e "\n${BLUE}═══ $* ═══${NC}\n"; }

# ============================================================
# BUILD DEPENDENCIES
# ============================================================

check_dependencies() {
    log "Checking build dependencies..."
    
    local deps=(
        # Build tools
        git cmake meson ninja-build
        autoconf automake libtool pkg-config
        bison flex gcc gcc-c++ gcc-gfortran
        
        # Wine/Proton dependencies
        glib2-devel freetype-devel fontconfig-devel
        libX11-devel libXext-devel libXrender-devel
        libXrandr-devel libXfixes-devel libXcursor-devel
        libXi-devel libXxf86vm-devel libXcomposite-devel
        libxkbcommon-devel wayland-devel
        libpcap-devel libusb-devel libgphoto2-devel
        sane-backends-devel libpng-devel libjpeg-turbo-devel
        libtiff-devel libxml2-devel libxslt-devel
        dbus-devel alsa-lib-devel pulseaudio-libs-devel
        mesa-libGL-devel mesa-libEGL-devel
        vulkan-loader-devel vulkan-tools
        ocl-icd-devel OpenCL
        
        # DXVK dependencies
        rust cargo
        
        # VKD3D-Proton dependencies
        glslang python3-pip
        
        # Compression
        xz bzip2 zstd
    )
    
    local missing=()
    for dep in "${deps[@]}"; do
        if ! rpm -q "$dep" &>/dev/null 2>&1 && ! eopkg info "$dep" &>/dev/null 2>&1; then
            if ! command -v "$dep" &>/dev/null 2>&1; then
                missing+=("$dep")
            fi
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        warn "Missing build dependencies. Installing..."
        if command -v eopkg &>/dev/null; then
            sudo eopkg install "${missing[@]}"
        elif command -v dnf &>/dev/null; then
            sudo dnf builddep -y wine 2>/dev/null || true
            sudo dnf install -y "${missing[@]}"
        else
            error "Cannot install dependencies. Missing: ${missing[*]}"
            error "Please install them manually and re-run."
            exit 1
        fi
    fi
    
    log "All build dependencies satisfied."
}

# ============================================================
# DIRECTORY SETUP
# ============================================================

setup_directories() {
    log "Setting up build directories..."
    mkdir -p "$BUILD_DIR" "$WORK_DIR" "$LOGS_DIR" "$DIST_DIR"
    
    # Ensure Steam compatibility tools directory exists
    mkdir -p "$INSTALL_DIR"
}

# ============================================================
# SOURCE CLONING
# ============================================================

clone_source() {
    local repo="$1"
    local dir="$2"
    local tag="${3:-}"
    
    if [[ -d "$dir/.git" ]]; then
        log "Updating existing clone: ${dir}"
        cd "$dir"
        git fetch --all --tags
        [[ -n "$tag" ]] && git checkout "tags/${tag}" -b "build-${tag}" 2>/dev/null || \
            git checkout "tags/${tag}" 2>/dev/null || true
        cd "$OLDPWD"
    else
        log "Cloning: ${repo} → ${dir}"
        if [[ -n "$tag" ]]; then
            git clone --depth 1 --branch "$tag" "$repo" "$dir"
        else
            git clone --depth 1 "$repo" "$dir"
        fi
    fi
}

fetch_sources() {
    section "Fetching Sources"
    
    clone_source "$PROTON_REPO" "${WORK_DIR}/proton" "$PROTON_VERSION"
    clone_source "$PROTON_WINE_REPO" "${WORK_DIR}/proton-wine" "$PROTON_GE_TAG"
    clone_source "$DXVK_REPO" "${WORK_DIR}/dxvk" "v${DXVK_VERSION}"
    clone_source "$VKD3D_PROTON_REPO" "${WORK_DIR}/vkd3d-proton" "v${VKD3D_VERSION}"
    
    log "All sources fetched."
}

# ============================================================
# BUILD COMPONENTS
# ============================================================

build_wine() {
    section "Building Wine (Proton GE Fork)"
    
    cd "${WORK_DIR}/proton-wine"
    
    local build_dir="${WORK_DIR}/proton-wine/build"
    mkdir -p "$build_dir"
    cd "$build_dir"
    
    local configure_args=(
        "--prefix=${WORK_DIR}/proton-wine/install"
        "--enable-win64"
        "--disable-win16"
        "--disable-tests"
        "--without-capi"
        "--without-oss"
        "--without-gstreamer"
        "--with-x"
        "--with-wayland"
        "--with-vulkan"
        "--with-pulse"
        "--with-dbus"
        "--without-ldap"
        "--without-cups"
    )
    
    log "Configuring Wine..."
    "${WORK_DIR}/proton-wine/configure" "${configure_args[@]}" 2>&1 | \
        tee "${LOGS_DIR}/wine-configure.log"
    
    log "Building Wine (${BUILD_THREADS} threads)..."
    make -j"$BUILD_THREADS" 2>&1 | tee "${LOGS_DIR}/wine-build.log"
    
    log "Installing Wine..."
    make install 2>&1 | tee "${LOGS_DIR}/wine-install.log"
    
    cd "$OLDPWD"
    log "Wine build complete."
}

build_dxvk() {
    [[ "$ENABLE_DXVK" -eq 0 ]] && { log "Skipping DXVK build (disabled)"; return; }
    
    section "Building DXVK"
    
    cd "${WORK_DIR}/dxvk"
    
    log "Building DXVK with cargo/meson..."
    meson setup --buildtype "$BUILD_TYPE" \
        -Denable_nvapi=true \
        -Duse_wayland=true \
        build 2>&1 | tee "${LOGS_DIR}/dxvk-meson.log"
    
    ninja -C build -j"$BUILD_THREADS" 2>&1 | tee "${LOGS_DIR}/dxvk-build.log"
    
    cd "$OLDPWD"
    log "DXVK build complete."
}

build_vkd3d_proton() {
    [[ "$ENABLE_VKD3D" -eq 0 ]] && { log "Skipping VKD3D-Proton build (disabled)"; return; }
    
    section "Building VKD3D-Proton"
    
    cd "${WORK_DIR}/vkd3d-proton"
    
    log "Configuring VKD3D-Proton..."
    meson setup --buildtype "$BUILD_TYPE" \
        -Denable_nvapi=true \
        build 2>&1 | tee "${LOGS_DIR}/vkd3d-meson.log"
    
    ninja -C build -j"$BUILD_THREADS" 2>&1 | tee "${LOGS_DIR}/vkd3d-build.log"
    
    cd "$OLDPWD"
    log "VKD3D-Proton build complete."
}

# ============================================================
# PROTON ASSEMBLY
# ============================================================

assemble_proton() {
    section "Assembling Proton GE Distribution"
    
    local proton_dir="${DIST_DIR}/Proton-${PROTON_GE_TAG}"
    rm -rf "$proton_dir"
    mkdir -p "$proton_dir"
    
    log "Copying Wine installation..."
    cp -a "${WORK_DIR}/proton-wine/install/"* "$proton_dir/"
    
    log "Copying Proton files..."
    cp -a "${WORK_DIR}/proton/"* "$proton_dir/" 2>/dev/null || true
    
    # Copy DXVK
    if [[ "$ENABLE_DXVK" -eq 1 ]] && [[ -d "${WORK_DIR}/dxvk/build" ]]; then
        log "Installing DXVK..."
        mkdir -p "$proton_dir/lib64/wine" "$proton_dir/lib/wine"
        
        # x64 DXVK DLLs
        cp -a "${WORK_DIR}/dxvk/build/dxvk_x64.dll" "$proton_dir/lib64/wine/"
        cp -a "${WORK_DIR}/dxvk/build/dxvk_x64.so" "$proton_dir/lib64/wine/"
        
        # x32 DXVK DLLs
        cp -a "${WORK_DIR}/dxvk/build/dxvk_x32.dll" "$proton_dir/lib/wine/"
        cp -a "${WORK_DIR}/dxvk/build/dxvk_x32.so" "$proton_dir/lib/wine/"
    fi
    
    # Copy VKD3D-Proton
    if [[ "$ENABLE_VKD3D" -eq 1 ]] && [[ -d "${WORK_DIR}/vkd3d-proton/build" ]]; then
        log "Installing VKD3D-Proton..."
        mkdir -p "$proton_dir/lib64/wine" "$proton_dir/lib/wine"
        
        # x64 VKD3D DLLs
        cp -a "${WORK_DIR}/vkd3d-proton/build/vkd3d-proton-x64/"* "$proton_dir/lib64/wine/"
        
        # x32 VKD3D DLLs
        cp -a "${WORK_DIR}/vkd3d-proton/build/vkd3d-proton-x86/"* "$proton_dir/lib/wine/"
    fi
    
    # Create version file
    cat > "$proton_dir/version" << VER
Proton GE ${PROTON_GE_TAG}
Built: $(date -u '+%Y-%m-%d %H:%M UTC')
Build Type: ${BUILD_TYPE}
DXVK: ${DXVK_VERSION}
VKD3D: ${VKD3D_VERSION}
Wayland: ${ENABLE_WAYLAND}
Media Foundation: ${ENABLE_MEDIA}
VER
    
    log "Proton assembled at: ${proton_dir}"
}

# ============================================================
# PACKAGING
# ============================================================

package_proton() {
    section "Packaging Proton GE"
    
    local package_name="Proton-${PROTON_GE_TAG}.tar.xz"
    local package_path="${DIST_DIR}/${package_name}"
    
    cd "${DIST_DIR}"
    
    log "Creating tarball: ${package_name}"
    tar -caf "$package_path" \
        --use-compress-program="zstd -T${BUILD_THREADS} -19" \
        "Proton-${PROTON_GE_TAG}/"
    
    local size
    size=$(du -h "$package_path" | cut -f1)
    log "Package created: ${package_path} (${size})"
    
    cd "$OLDPWD"
}

# ============================================================
# INSTALLATION
# ============================================================

install_proton() {
    section "Installing Proton GE to Steam"
    
    local src="${DIST_DIR}/Proton-${PROTON_GE_TAG}"
    local dest="${INSTALL_DIR}/Proton-${PROTON_GE_TAG}"
    
    if [[ ! -d "$src" ]]; then
        error "Proton distribution not found at ${src}. Build first."
        exit 1
    fi
    
    log "Installing to: ${dest}"
    rm -rf "$dest"
    cp -a "$src" "$dest"
    
    log "Proton GE installed to Steam compatibility tools:"
    log "  ${dest}"
    log ""
    log "Restart Steam, then select 'Proton ${PROTON_GE_TAG}' in"
    log "Steam Play settings (Settings → Compatibility)."
}

# ============================================================
# CLEANUP
# ============================================================

clean_build() {
    section "Cleaning Build"
    
    log "Removing work directory..."
    rm -rf "$WORK_DIR"
    log "Removing distribution directory..."
    rm -rf "$DIST_DIR"
    log "Clean complete."
}

clean_work() {
    section "Cleaning Work Directory (keeping dist)"
    rm -rf "$WORK_DIR"
    log "Work directory cleaned."
}

# ============================================================
# MAIN
# ============================================================

usage() {
    cat << EOF
Solus Proton GE Builder — Build custom Proton (GloriousEggroll) from source

USAGE:
  proton-ge-build.sh [command]

COMMANDS:
  all            Full build: deps → fetch → build → assemble → package
  full           Same as 'all'
  build          Build all components (assumes deps installed + sources fetched)
  deps           Check and install build dependencies
  fetch          Clone/update source repositories
  wine           Build only Wine/Proton
  dxvk           Build only DXVK
  vkd3d          Build only VKD3D-Proton
  assemble       Assemble final Proton distribution
  package        Package as compressed tarball
  install        Install to Steam compatibility tools directory
  clean          Remove all build artifacts
  clean-work     Remove only work directory (keep dist)
  help           Show this help

ENVIRONMENT VARIABLES:
  BUILD_DIR       Build root directory (default: ~/proton-ge-build)
  INSTALL_DIR     Steam compatibility tools dir (default: ~/.steam/...)
  BUILD_THREADS   Parallel build jobs (default: all cores)
  PROTON_GE_TAG   Proton GE version tag (default: GE-Proton9-25)
  DXVK_VERSION    DXVK version tag (default: 2.5.1)
  VKD3D_VERSION   VKD3D-Proton version tag (default: 2.14.1)

EXAMPLES:
  proton-ge-build.sh all                          # Full build
  proton-ge-build.sh build                        # Build only
  proton-ge-build.sh install                      # Install last build
  PROTON_GE_TAG=GE-Proton8-31 proton-ge-build.sh all  # Build specific version
EOF
}

main() {
    local cmd="${1:-help}"
    
    setup_directories
    
    case "$cmd" in
        all|full)
            check_dependencies
            fetch_sources
            build_wine
            build_dxvk
            build_vkd3d_proton
            assemble_proton
            package_proton
            section "Build Complete"
            log "Package: ${DIST_DIR}/Proton-${PROTON_GE_TAG}.tar.xz"
            log "Run 'proton-ge-build.sh install' to install to Steam."
            ;;
        deps|dependencies)
            check_dependencies
            ;;
        fetch)
            fetch_sources
            ;;
        build)
            build_wine
            build_dxvk
            build_vkd3d_proton
            assemble_proton
            ;;
        wine)
            build_wine
            ;;
        dxvk)
            build_dxvk
            ;;
        vkd3d)
            build_vkd3d_proton
            ;;
        assemble)
            assemble_proton
            ;;
        package)
            package_proton
            ;;
        install)
            install_proton
            ;;
        clean)
            clean_build
            ;;
        clean-work|clean_work)
            clean_work
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            error "Unknown command: $cmd"
            usage
            exit 1
            ;;
    esac
}

main "$@"
