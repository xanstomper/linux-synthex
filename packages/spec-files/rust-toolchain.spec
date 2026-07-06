# Solus Linux Rust Toolchain RPM Spec
# Package: rust-toolchain
# Provides: rustc, cargo, rust-std, rust-src, rust-docs, cargo-doc
# Origin: Fedora/RHEL upstream with Solus tuning
#
# Solus ships a full Rust toolchain for kernel module development,
# system utility rewrites, and user-facing application development.
# This spec tracks upstream Fedora's rust-packaging closely.
#
# Build variants:
#   --with lto    : LTO-optimized rustc (default on supported arches)
#   --without lto : Non-LTO build for compatibility

%global rust_arch x86_64-unknown-linux-gnu
%global rust_triple x86_64-unknown-linux-gnu
%global rust_version 1.80.0

Name: rust-toolchain
Version: %{rust_version}
Release: 1%{?dist}
Summary: Rust programming language toolchain — rustc, cargo, rust-src

License: (Apache-2.0 OR MIT) AND (Apache-2.0 WITH LLVM-exception OR Apache-2.0 OR MIT)
URL: https://www.rust-lang.org

# Upstream Rust source tarball
Source0: https://static.rust-lang.org/dist/rustc-%{version}-src.tar.xz
Source1: https://static.rust-lang.org/dist/rustc-%{version}-src.tar.xz.asc

# GPG key for verification (Rust release signing key)
Source2: https://keybase.io/rust/pgp_keys.asc

# Solus cargo config (default registry, mirrors, settings)
Source3: cargo-config.toml

# Pre-built Rust bootstrap compiler for bootstrapping
# Uses the previous stable release as the bootstrap compiler
Source10: https://static.rust-lang.org/dist/rust-%{version}-%{rust_arch}.tar.xz
Source11: https://static.rust-lang.org/dist/rust-std-%{version}-%{rust_arch}.tar.xz

BuildRequires: make, gcc, gcc-c++, patch, git-core
BuildRequires: curl, cmake, ninja-build, pkgconfig
BuildRequires: zlib-devel, libffi-devel, openssl-devel
BuildRequires: python3, perl, gettext, texinfo
BuildRequires: procps-ng, which, time, xz, bzip2
BuildRequires: llvm-devel >= 17, clang-devel >= 17, lld-devel >= 17

# LLVM is required for codegen backends
Requires: llvm-libs >= 17
Requires: zlib, openssl, libcurl

%description
Rust is a systems programming language focused on three goals:
safety, speed, and concurrency. It maintains memory safety without
requiring a garbage collector.

This package provides:
- rustc — the Rust compiler
- cargo — the Rust package manager and build system
- rust-std — standard library for x86_64
- rust-src — Rust source code for IDE integration
- rust-docs — HTML documentation
- cargo-doc — Cargo documentation

Solus uses Rust for:
- Kernel module development (Rust-for-Linux)
- System utility rewrites (ripgrep, fd, bat, eza, etc.)
- Solus system daemons (update-manager, driver-manager, pkg)
- Desktop application development

%package compiler
Summary: Rust compiler (rustc) and package manager (cargo)
Requires: %{name}-std = %{version}-%{release}
Requires: llvm-libs >= 17
Provides: rustc = %{version}
Provides: cargo = %{version}
Obsoletes: rustc < %{version}
Obsoletes: cargo < %{version}

%description compiler
The Rust compiler (rustc) and Cargo package manager.
Includes the borrow checker, type system, and LLVM codegen backend.

%package std
Summary: Rust standard library for x86_64
Requires: %{name}-compiler = %{version}-%{release}
Provides: rust-std = %{version}

%description std
The Rust standard library (libstd, libcore, liballoc, libproc_macro)
compiled for x86_64-unknown-linux-gnu with optimizations.

%package src
Summary: Rust source code for code navigation and IDE support
Requires: %{name}-compiler = %{version}-%{release}
Provides: rust-src = %{version}

%description src
Complete Rust source tree installed to /usr/lib/rustlib/src/rust/.
Required by rust-analyzer, IDEs (VS Code, JetBrains), and tools
that need to browse or cross-reference standard library source.

%package docs
Summary: Rust documentation (The Book, Reference, std docs)
Requires: %{name}-compiler = %{version}-%{release}
Provides: rust-docs = %{version}

%description docs
HTML documentation including:
- The Rust Programming Language (The Book)
- The Rust Reference
- The Rustonomicon
- Standard library API documentation
- Cargo documentation
- Edition Guide

%package cargo-doc
Summary: Cargo documentation
Requires: %{name}-compiler = %{version}-%{release}
Provides: cargo-doc = %{version}

%description cargo-doc
HTML documentation for the Cargo package manager,
including the Cargo Book and API reference.

%prep
%setup -q -n rustc-%{version}-src

# Verify GPG signature if possible
%{?gpgverify: %gpgverify --data='%{SOURCE0}' --sig='%{SOURCE1}' --key='%{SOURCE2}'}

# Apply any Solus-specific patches (none yet)
# %patch0 -p1

%build
# Configure Rust build
./configure \
    --prefix=%{_prefix} \
    --libdir=%{_libdir} \
    --sysconfdir=%{_sysconfdir} \
    --local-rust-root=/opt/rust-bootstrap \
    --release-channel=stable \
    --enable-extended \
    --tools=rustc,cargo,rust-std,rust-src,rust-docs,rustfmt,clippy \
    --enable-llvm-static-stdcpp \
    --set target.x86_64-unknown-linux-gnu.cc=/usr/bin/gcc \
    --set target.x86_64-unknown-linux-gnu.cxx=/usr/bin/g++ \
    --set target.x86_64-unknown-linux-gnu.linker=/usr/bin/gcc \
    --set target.x86_64-unknown-linux-gnu.ar=/usr/bin/ar \
    --enable-profiler \
    --enable-optimize-llvm \
    --release

%if %{with lto}
    # Enable ThinLTO for optimized rustc
    echo "rust.lto = 'thin'" >> config.toml
    echo "rust.codegen-units = 1" >> config.toml
%endif

# Build (parallel — this takes a while)
%{python3} x.py build 2>&1 | tail -20

# Install cargo config
mkdir -p %{buildroot}%{_sysconfdir}/cargo
install -m 644 %{SOURCE3} %{buildroot}%{_sysconfdir}/cargo/config.toml

%install
DESTDIR=%{buildroot} %{python3} x.py install 2>&1 | tail -10

# Create symlinks for expected binary names
mkdir -p %{buildroot}%{_bindir}
ln -sf rustc %{buildroot}%{_bindir}/rustc
ln -sf cargo %{buildroot}%{_bindir}/cargo
ln -sf rustfmt %{buildroot}%{_bindir}/rustfmt
ln -sf clippy-driver %{buildroot}%{_bindir}/clippy-driver

# Install rust-src to standard location
mkdir -p %{buildroot}%{_datadir}/rustlib/src
cp -a src %{buildroot}%{_datadir}/rustlib/src/rust/

# Remove unnecessary build artifacts
find %{buildroot} -name '*.a' -type f -delete
find %{buildroot} -name '*.o' -type f -delete

%files compiler
%{_bindir}/rustc
%{_bindir}/cargo
%{_bindir}/rustfmt
%{_bindir}/clippy-driver
%{_bindir}/cargo-clippy
%{_bindir}/rust-analyzer
%{_libdir}/rustlib/%{rust_triple}/codegen-backends/
%{_libdir}/rustlib/%{rust_triple}/lib/*.so
%dir %{_libdir}/rustlib/
%{_libdir}/rustlib/components
%{_libdir}/rustlib/install.log
%{_libdir}/rustlib/manifest-*
%{_libdir}/rustlib/rustc-src/
%{_sysconfdir}/cargo/config.toml
%doc README.md LICENSE

%files std
%{_libdir}/rustlib/%{rust_triple}/lib/*.rlib
%{_libdir}/rustlib/%{rust_triple}/lib/*.rmeta

%files src
%{_datadir}/rustlib/src/

%files docs
%dir %{_datadir}/doc/rust/
%{_datadir}/doc/rust/*

%files cargo-doc
%dir %{_datadir}/doc/cargo/
%{_datadir}/doc/cargo/*

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 1.80.0-1
- Initial Solus Rust toolchain package (v1.80.0 stable)
- Extended tool profile: rustc, cargo, rust-std, rust-src, docs
- ThinLTO enabled for optimised compiler performance
- LLVM 17 codegen backend bundled
- System cargo config at /etc/cargo/config.toml
- rust-analyzer included for IDE support
- Required for Rust-for-Linux kernel module development
