# SynthOS Kernel RPM Spec
# Package: kernel-synthex
# Optimized desktop kernel with BORE scheduler, EEVDF improvements, gaming & container support
#
# Build variants:
#   --with v3    : x86-64-v3 baseline (default)
#   --with v4    : x86-64-v4 baseline (requires AMD Zen4+/Intel SPR+)
#   --without custom: generic x86-64 baseline

%define pkgname kernel-synthex
%define kversion 6.14
%define patchlevel 2
%define rpmversion %{kversion}.%{patchlevel}
%define variant %{?_with_v3:v3}%{?_with_v4:v4}%{!?_with_v3:%{!?_with_v4:generic}}

%define basever %{kversion}.%{patchlevel}
%define target_arch x86_64
%define build_dir %{_builddir}/%{pkgname}-%{basever}
%define kernel_name %{pkgname}

# x86-64 microarchitecture level defaults
%if "%{variant}" == "v3"
%define _target_cpu x86-64-v3
%define config_flags CONFIG_GENERIC_CPU3=y CONFIG_GENERIC_CPU2=n CONFIG_GENERIC_CPU=n
%define kver_postfix -synthex-v3
%endif
%if "%{variant}" == "v4"
%define _target_cpu x86-64-v4
%define config_flags CONFIG_GENERIC_CPU4=y CONFIG_GENERIC_CPU3=n CONFIG_GENERIC_CPU2=n CONFIG_GENERIC_CPU=n
%define kver_postfix -synthex-v4
%endif
%if "%{variant}" == "generic"
%define _target_cpu x86_64
%define config_flags CONFIG_GENERIC_CPU=y CONFIG_GENERIC_CPU2=n CONFIG_GENERIC_CPU3=n
%define kver_postfix -synthex
%endif

Name: kernel-synthex
Version: %{basever}%{kver_postfix}
Release: 1%{?dist}
Summary: SynthOS custom kernel with BORE scheduler and desktop optimizations

Group: System Environment/Kernel
License: GPL-2.0-only
URL: https://github.com/torvalds/linux
Source0: https://cdn.kernel.org/pub/linux/kernel/v%{kversion}.x/linux-%{basever}.tar.xz
Source1: config-x86_64

# BORE scheduler patch (Burst-Oriented Response Enhancer)
Patch0: https://github.com/firelzrd/bore-scheduler/raw/master/patches/v6.14/sched_bore_v6.14.patch

# CachyOS optimizations (optional, applied when available)
Patch1: https://github.com/CachyOS/kernel-patches/raw/master/6.14/misc/cachyos-harder.patch

# Futex2 / PROTON_GE support patches
Patch2: https://github.com/CachyOS/kernel-patches/raw/master/6.14/misc/futex2.patch

# BTRFS performance improvements
Patch3: https://github.com/CachyOS/kernel-patches/raw/master/6.14/btrfs/btrfs-zstd-fast.patch

# CachyOS CPU optimizations (scheduler/CPU tuning — 0005-cachy)
Patch4: https://github.com/CachyOS/kernel-patches/raw/master/6.14/0005-cachy.patch

BuildRequires: bc, bison, flex, gcc, gcc-c++, make, patch, openssl-devel
BuildRequires: elfutils-libelf-devel, dwarves, python3-devel, perl
BuildRequires: rsync, kmod, xz, zstd, lz4, lzo, lzma
BuildRequires: pahole, m4, tar, gzip, bzip2
BuildRequires: audit-libs-devel, device-mapper-devel
BuildRequires: libcap-devel, libcap-ng-devel
BuildRequires: ncurses-devel, readline-devel
BuildRequires: git-core, diffutils, hostname
BuildRequires: rpm-build, redhat-rpm-config
BuildRequires: elfutils-devel, numactl-devel, libbpf-devel
BuildRequires: systemd-devel, libudev-devel, libattr-devel
# Rust-for-Linux support (memory-safe kernel drivers)
BuildRequires: rust-toolchain >= 1.80.0, clang-devel >= 17, lld-devel >= 17
BuildRequires: rust-std, cargo

Requires: coreutils, bash, dracut, grub2-tools
Requires(pre): /usr/sbin/dracut
Requires(post): /usr/sbin/dracut, /usr/sbin/grub2-mkconfig

|%description
SynthOS custom kernel with BORE (Burst-Oriented Response Enhancer) scheduler.
Optimized for desktop responsiveness, gaming (PROTON_GE, fsync, futex2),
Wayland graphics, container workloads, and power efficiency.

Includes:
- BORE scheduler for reduced latency under interactive load
- EEVDF latency improvements
- x86-64-%{variant} optimizations
- PREEMPT_FULL for low-latency scheduling
- Rust-for-Linux support (CONFIG_RUST=y) for memory-safe kernel drivers
- Comprehensive BTRFS + zstd compression support
- SELinux + AppArmor + Lockdown security
- Full AMD/Intel GPU support (i915, amdgpu, NVIDIA)
- Container support (cgroup v2, namespaces, cgroup subsystem)
- Tickless NO_HZ_FULL + high-res timers
- Schedutil CPU frequency governor with fast switching
- Paravirtualized spinlocks (KVM guest)
- Debug overhead disabled (CONFIG_DEBUG_* =n)

%package core
Summary: Core kernel image and modules for %{pkgname}
Group: System Environment/Kernel
Requires: %{name} = %{version}-%{release}
Provides: kernel-synthex-core-%{variant} = %{version}-%{release}
Obsoletes: kernel-synthex-core < %{version}-%{release}

%description core
The core kernel package containing the kernel image, System.map,
and required modules for the Synthex custom kernel.

%package devel
Summary: Development headers and scripts for %{pkgname}
Group: Development/System
Requires: %{name} = %{version}-%{release}
Provides: kernel-synthex-devel-%{variant} = %{version}-%{release}
Requires: kernel-devel-uname-r = %{version}-%{release}

%description devel
Development package for building kernel modules against the
Synthex custom kernel. Contains headers, scripts, and Makefiles.

%package modules
Summary: Extra kernel modules for %{pkgname}
Group: System Environment/Kernel
Requires: %{name} = %{version}-%{release}
Provides: kernel-synthex-modules-%{variant} = %{version}-%{release}
Obsoletes: kernel-synthex-modules < %{version}-%{release}

%description modules
Additional kernel modules for the Synthex custom kernel,
including filesystem, networking, and hardware drivers.

%package headers
Summary: Kernel headers for %{pkgname}
Group: Development/System
Requires: %{name} = %{version}-%{release}
Provides: kernel-synthex-headers-%{variant} = %{version}-%{release}

%description headers
User-visible kernel headers for the Synthex custom kernel.
Required by glibc and many system tools.

%prep
%autosetup -n linux-%{basever} -p1

# Apply BORE scheduler patch
%patch0 -p1

# Apply CachyOS hardening
%patch1 -p1 -b .cachyos-hard

# Apply futex2 for PROTON_GE
%patch2 -p1 -b .futex2

# Apply BTRFS zstd-fast
%patch3 -p1 -b .btrfs-zstd

# Apply CachyOS CPU optimizations
%patch4 -p1 -b .cachyos-cpu

# Copy Synthex kernel configuration
cp %{SOURCE1} .config

# Update config for variant-specific options
%if "%{variant}" == "v3"
    scripts/config --enable CONFIG_GENERIC_CPU3
    scripts/config --disable CONFIG_GENERIC_CPU2
    scripts/config --disable CONFIG_GENERIC_CPU
    scripts/config --enable CONFIG_ARCH_USE_BUILTIN_BSWAP
    scripts/config --enable CONFIG_ARCH_SUPPORTS_INT128
    scripts/config --set-val CONFIG_GENERIC_CPU3 y
%endif
%if "%{variant}" == "v4"
    scripts/config --enable CONFIG_GENERIC_CPU4
    scripts/config --disable CONFIG_GENERIC_CPU3
    scripts/config --disable CONFIG_GENERIC_CPU2
    scripts/config --disable CONFIG_GENERIC_CPU
    scripts/config --enable CONFIG_ARCH_USE_BUILTIN_BSWAP
    scripts/config --enable CONFIG_ARCH_SUPPORTS_INT128
    scripts/config --enable CONFIG_ARCH_SUPPORTS_AVX2
    scripts/config --enable CONFIG_ARCH_SUPPORTS_AVX512
    scripts/config --set-val CONFIG_GENERIC_CPU4 y
%endif
%if "%{variant}" == "generic"
    scripts/config --enable CONFIG_GENERIC_CPU
    scripts/config --disable CONFIG_GENERIC_CPU2
    scripts/config --disable CONFIG_GENERIC_CPU3
    scripts/config --disable CONFIG_GENERIC_CPU4
%endif

# Apply local version suffix
scripts/config --set-str CONFIG_LOCALVERSION "%{kver_postfix}"

# Fix any broken dependencies
yes '' | make oldconfig

%build
make %{?_smp_mflags} CC=gcc HOSTCC=gcc

%install
# Install kernel and modules
make INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_install
make INSTALL_PATH=$RPM_BUILD_ROOT/boot install

# Install System.map and config
cp System.map $RPM_BUILD_ROOT/boot/System.map-%{kernel_name}-%{basever}%{kver_postfix}
cp .config $RPM_BUILD_ROOT/boot/config-%{kernel_name}-%{basever}%{kver_postfix}
cp vmlinuz $RPM_BUILD_ROOT/boot/vmlinuz-%{kernel_name}-%{basever}%{kver_postfix}

# Create symlinks
ln -sf vmlinuz-%{kernel_name}-%{basever}%{kver_postfix} $RPM_BUILD_ROOT/boot/vmlinuz-%{kernel_name}
ln -sf System.map-%{kernel_name}-%{basever}%{kver_postfix} $RPM_BUILD_ROOT/boot/System.map-%{kernel_name}
ln -sf config-%{kernel_name}-%{basever}%{kver_postfix} $RPM_BUILD_ROOT/boot/config-%{kernel_name}

# Install headers
make INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install

# Install development files for module building
make INSTALL_MOD_PATH=$RPM_BUILD_ROOT modules_prepare

# Clean up unnecessary build artifacts
find $RPM_BUILD_ROOT/lib/modules/%{basever}%{kver_postfix} -name '*.ko' -exec chmod 644 {} \;
find $RPM_BUILD_ROOT/lib/modules/%{basever}%{kver_postfix} -name '*.ko' -exec strip --strip-debug {} \;

# Remove build link if it exists
rm -f $RPM_BUILD_ROOT/lib/modules/%{basever}%{kver_postfix}/build
rm -f $RPM_BUILD_ROOT/lib/modules/%{basever}%{kver_postfix}/source

%pre
# Ensure dracut is available but don't regenerate yet (kernel not installed)
echo "Synthex kernel %{basever}%{kver_postfix} pre-installation"

%post
# Regenerate initramfs for new kernel
/usr/sbin/dracut --force --kver %{basever}%{kver_postfix} 2>/dev/null || :

# Update GRUB configuration
if [ -x /usr/sbin/grub2-mkconfig ]; then
    /usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || \
    /usr/sbin/grub2-mkconfig -o /boot/efi/EFI/synthex/grub.cfg 2>/dev/null || :
elif [ -x /usr/sbin/update-grub ]; then
    /usr/sbin/update-grub 2>/dev/null || :
fi

# Add kernel to EFI if systemd-boot is used
if [ -x /usr/bin/bootctl ] && [ -d /boot/efi/EFI/systemd ]; then
    /usr/bin/kernel-install add %{basever}%{kver_postfix} $RPM_BUILD_ROOT/boot/vmlinuz-%{kernel_name}-%{basever}%{kver_postfix} 2>/dev/null || :
fi

%preun
if [ "$1" = "0" ]; then
    # Remove old initramfs
    rm -f /boot/initramfs-%{basever}%{kver_postfix}.img 2>/dev/null || :
    rm -f /boot/initrd-%{basever}%{kver_postfix}.img 2>/dev/null || :

    # Update GRUB after removal
    if [ -x /usr/sbin/grub2-mkconfig ]; then
        /usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || \
        /usr/sbin/grub2-mkconfig -o /boot/efi/EFI/synthex/grub.cfg 2>/dev/null || :
    elif [ -x /usr/sbin/update-grub ]; then
        /usr/sbin/update-grub 2>/dev/null || :
    fi
fi

%postun
if [ "$1" = "0" ]; then
    # Clean up stale kernel entries in systemd-boot
    if [ -x /usr/bin/bootctl ] && [ -d /boot/efi/EFI/systemd ]; then
        /usr/bin/kernel-install remove %{basever}%{kver_postfix} 2>/dev/null || :
    fi
fi

%files core
%defattr(-, root, root)
/boot/vmlinuz-%{kernel_name}-%{basever}%{kver_postfix}
/boot/vmlinuz-%{kernel_name}
/boot/System.map-%{kernel_name}-%{basever}%{kver_postfix}
/boot/System.map-%{kernel_name}
/boot/config-%{kernel_name}-%{basever}%{kver_postfix}
/boot/config-%{kernel_name}
/lib/modules/%{basever}%{kver_postfix}/

%files devel
%defattr(-, root, root)
/lib/modules/%{basever}%{kver_postfix}/build
/lib/modules/%{basever}%{kver_postfix}/source
%dir /usr/src/kernels/
/usr/src/kernels/%{basever}%{kver_postfix}/

%files modules
%defattr(-, root, root)
/lib/modules/%{basever}%{kver_postfix}/kernel/
/lib/modules/%{basever}%{kver_postfix}/modules.*
%exclude /lib/modules/%{basever}%{kver_postfix}/kernel/drivers/gpu/drm/nvidia
%exclude /lib/modules/%{basever}%{kver_postfix}/kernel/drivers/gpu/drm/nouveau

%files headers
%defattr(-, root, root)
/usr/include/

%changelog
* Sat Jul 05 2026 Synthex Kernel Team <kernel@synthex-project.org> - 6.14.2-2
- Fast-boot tuning: NO_HZ_FULL tickless, schedutil default governor
- Disable debug cruft (CONFIG_DEBUG_*, BTRFS asserts, PM_DEBUG, CGROUP_DEBUG)
- THP madvise-only, zswap off by default, zram primary swap
- Enable PARAVIRT_SPINLOCK + KVM_GUEST for guest workloads
- Add CachyOS cpu-optimizations patch (0005-cachy)
- Disable unused filesystems for a smaller kernel

* Sat Jul 04 2026 Synthex Kernel Team <kernel@synthex-project.org> - 6.14.2-1
- Initial Synthex kernel package
- BORE scheduler v6.14 patch applied
- CachyOS hardening patches applied
- Futex2 support for PROTON_GE
- BTRFS zstd-fast compression patch
- x86-64-v3 and v4 optimization variants
- PREEMPT_FULL low-latency configuration
- Desktop, gaming, and container optimizations
- SELinux + AppArmor + Lockdown security profiles
