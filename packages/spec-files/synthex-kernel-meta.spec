Name:           synthex-kernel-meta
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS kernel meta-package with BORE scheduler tuning
BuildArch:      noarch

License:        GPLv2
URL:            https://getsynthex.io

# Kernel itself — require the generic kernel; distro can override with kernel-zen
Requires:       kernel
Requires:       kernel-core
Requires:       kernel-modules
# CPU microcode
Requires:       linux-firmware
# Kernel tuning helpers
Requires:       tuned
Requires:       cpupower
Suggests:       kernel-zen
Suggests:       kernel-rt

%description
SynthOS kernel meta-package.  Ensures the correct kernel and firmware
packages are installed and drops tuning configuration appropriate for
the SynthOS BORE-scheduled kernel:

  - Low-latency CFS/BORE scheduler settings (sched_latency_ns = 6 ms)
  - Reduced swappiness for desktop workloads (vm.swappiness = 10)
  - Tuned VFS cache pressure (vm.vfs_cache_pressure = 50)
  - IRQ-affinity tuned profile via tuned (desktop-powersave profile)

Suggests kernel-zen for the recommended CachyOS / BORE-patched kernel and
kernel-rt for real-time audio or low-latency production workloads.

%prep
# meta-package — nothing to unpack

%build
# meta-package — nothing to build

%install
install -d %{buildroot}/etc/sysctl.d
install -d %{buildroot}/etc/synthex
install -d %{buildroot}/usr/lib/tuned/synthex-kernel

cat > %{buildroot}/etc/sysctl.d/99-synthex-kernel.conf << 'EOF'
# SynthOS Kernel Tuning (BORE scheduler + desktop)
# BORE / CFS scheduling — keep latency ≤ 6 ms
kernel.sched_latency_ns = 6000000
kernel.sched_min_granularity_ns = 600000
kernel.sched_wakeup_granularity_ns = 1000000
# Reduce swap pressure for desktop use
vm.swappiness = 10
# VFS inode/dentry cache pressure
vm.vfs_cache_pressure = 50
# Writeback latency
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

cat > %{buildroot}/usr/lib/tuned/synthex-kernel/tuned.conf << 'EOF'
[main]
summary=SynthOS BORE Kernel Desktop Profile
include=desktop

[sysctl]
kernel.sched_latency_ns=6000000
vm.swappiness=10

[scheduler]
policy=performance
EOF

%files
%dir /etc/synthex
%config(noreplace) /etc/sysctl.d/99-synthex-kernel.conf
%dir /usr/lib/tuned/synthex-kernel
/usr/lib/tuned/synthex-kernel/tuned.conf

%post
# Apply sysctl immediately
/usr/sbin/sysctl --system 2>/dev/null || :
# Switch tuned to the SynthOS kernel profile if tuned is running
if systemctl is-active --quiet tuned 2>/dev/null; then
    tuned-adm profile synthex-kernel 2>/dev/null || :
fi

%preun
if [ $1 -eq 0 ]; then
    if systemctl is-active --quiet tuned 2>/dev/null; then
        tuned-adm profile balanced 2>/dev/null || :
    fi
fi

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Fix Release tag macro escaping (%%{?dist} → %{?dist})
- Add BuildArch: noarch
- Add complete Requires/Suggests, %prep/%build/%install/%files
- Ship sysctl drop-in and tuned profile as proper config files
- Move %post sysctl write to %install-time config file
