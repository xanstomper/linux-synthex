%define synthex_kernel_version 6.14
Name: synthex-kernel
Version: 6.14.6
Release: 1.synthex%{?dist}
Summary: SynthOS kernel with BORE scheduler
License: GPLv2
URL: https://getsynthex.io
Source0: https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.tar.xz
Source1: configs/synthex-x86_64-defconfig
BuildRequires: gcc, make, bc, bison, flex, cpio, openssl-devel
BuildRequires: elfutils-libelf-devel, dwarves, perl
BuildRequires: rust-toolchain >= 1.80.0, clang-devel, lld-devel
Requires: coreutils, bash, dracut, grub2-tools

%description
Synthex kernel with BORE (Burst-Oriented Response Enhancer) scheduler.
Optimized for desktop responsiveness, gaming (PROTON_GE, fsync, futex2),
Wayland graphics, and power efficiency. Includes defconfig tuned for
desktop workloads with ZRAM, BTRFS, and modern GPU driver support.

%prep
%setup -q -n synthex-repo-6.14.6
%autosetup -n linux-%{version} -p1

# Apply BORE scheduler patch (Burst-Oriented Response Enhancer)
# bore-scheduler v6.14 — patches kernel/sched/ for burst-oriented response
Source2: sched_bore_v6.14.patch
%autopatch -p1

%build
# Use Synthex defconfig
cp %{SOURCE1} .config
make %{?_smp_mflags} olddefconfig
make %{?_smp_mflags} all
make %{?_smp_mflags} modules

%install
%make_install
install -Dm644 .config %{buildroot}/boot/config-%{name}-%{version}

# Create symlink
ln -sf %{name}-%{version} %{buildroot}/boot/vmlinuz-%{name}

%post
/usr/sbin/dracut --force --kver %{version} 2>/dev/null || :
/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || :

%preun
if [ "$1" = "0" ]; then
    rm -f /boot/initramfs-%{version}.img 2>/dev/null || :
    /usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || :
fi

%files
/boot/vmlinuz-%{name}-%{version}
/boot/vmlinuz-%{name}
/boot/config-%{name}-%{version}
/lib/modules/%{version}/

%changelog
* Sun Jul 06 2026 Synthex Team <kernel@synthex-linux.org> - 6.14.6-1.synthex
- Synthex-tuned defconfig with BORE scheduler
- ZRAM + BTRFS + modern GPU support
- Desktop and gaming optimizations
- Tickless kernel (NO_HZ_FULL) for low latency
