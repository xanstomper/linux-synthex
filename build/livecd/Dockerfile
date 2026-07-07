# Synthex Linux Build Environment
# =================================
# Multi-stage Docker image for building Synthex packages and ISOs.
#
# Build:     docker build -t synthex-builder .
# Run:       docker run --rm -it --privileged -v $(pwd):/synthex synthex-builder
#
# The --privileged flag is needed for systemd-nspawn and loop devices
# used by lorax/livemedia-creator during ISO generation.

FROM fedora:41 AS builder

LABEL maintainer="Synthex Linux Project"
LABEL description="Synthex Linux Build Environment"
LABEL version="2026.10"

# Install build dependencies
RUN dnf install -y --setopt=install_weak_deps=False --skip-unavailable \
    lorax livemedia-creator pykickstart xorriso \
    livecd-tools squashfs-tools genisoimage isomd5sum \
    syslinux \
    rpm-build rpmdevtools mock createrepo_c \
    dnf-utils rpm-sign gnupg2 \
    git make cmake gcc gcc-c++ \
    qt6-qtbase-devel qt6-qtdeclarative-devel \
    qt6-qttools-devel qt6-qtwebsockets-devel \
    python3 python3-devel python3-pip \
    extra-cmake-modules kf6-ki18n-devel \
    kf6-kcoreaddons-devel kf6-kconfig-devel \
    kf6-kdbusaddons-devel \
    python3-pytest \
    grub2 grub2-tools grub2-pc grub2-efi grub2-efi-x64 \
    && dnf clean all

# Working directory
WORKDIR /synthex

# Set up environment
ENV SYNTHEX_ROOT=/synthex \
    PATH=/synthex/scripts:/usr/local/bin:$PATH

# Create necessary directories
RUN mkdir -p /build/rpms /build/iso /build/cache

# Entry point
CMD ["make", "-C", "/synthex", "help"]

# ─── Runner Stage ────────────────────────────────────────────────────
FROM builder AS runner

# Copy the build scripts
COPY . /synthex/

# Set up mock for RPM building
RUN usermod -a -G mock root 2>/dev/null || true

RUN echo "Build environment ready" && \
    echo "Synthex Linux Build Container v2026.10" && \
    echo "" && \
    echo "Commands:" && \
    echo "  make check     — Validate all code" && \
    echo "  make iso       — Build bootable ISO" && \
    echo "  make packages  — Build RPM packages"
