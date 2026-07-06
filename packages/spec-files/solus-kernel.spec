%define _name solus-kernel
%define _version 6.12.8
%define _release 1.solus%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux custom kernel with BORE scheduler + gaming optimizations

License:        GPL-2.0-only
URL:            https://getsol.us
BuildArch:      x86_64

Source0:        solus-x86_64-defconfig
Patch0:         solus-0001-bore-scheduler.patch
Patch1:         solus-0002-gaming-latency.patch
Patch2:         solus-0003-tickless-gaming.patch
Patch3:         solus-0004-vm-gaming-tuning.patch

Requires:       kernel-core = %{version}-%{release}
Requires:       kernel-modules = %{version}-%{release}

%description
The Solus Linux custom kernel. Based on the upstream Linux kernel with:
  - BORE (Burst-Oriented Response Enhancer) scheduler from CachyOS
  - Gaming latency reduction (tuned sched_latency/min_granularity)
  - Tickless (NO_HZ_FULL) for gaming cores
  - VM gaming tuning (swappiness=10, watermark_scale_factor=125)
  - ZRAM support, Btrfs, all GPU drivers, gaming input devices
  - TCP BBR, schedutil CPU governor, transparent hugepages

%prep
# Kernel source would be downloaded by build-solus-kernel.sh
# This spec packages the kernel config + patches for distribution

%build
# Kernel is built by scripts/build-solus-kernel.sh
# This spec provides the config and patches

%install
install -d -m 0755 %{buildroot}%{_datadir}/solus-kernel
install -m 0644 %{SOURCE0} %{buildroot}%{_datadir}/solus-kernel/solus-x86_64-defconfig
install -d -m 0755 %{buildroot}%{_datadir}/solus-kernel/patches
install -m 0644 %{PATCH0} %{buildroot}%{_datadir}/solus-kernel/patches/
install -m 0644 %{PATCH1} %{buildroot}%{_datadir}/solus-kernel/patches/
install -m 0644 %{PATCH2} %{buildroot}%{_datadir}/solus-kernel/patches/
install -m 0644 %{PATCH3} %{buildroot}%{_datadir}/solus-kernel/patches/

%files
%{_datadir}/solus-kernel/solus-x86_64-defconfig
%{_datadir}/solus-kernel/patches/*.patch

%changelog
* Sat Jul 05 2026 Solus Team <kernel@getsol.us> - 6.12.8-1.solus
- Solus kernel 6.12.8 with BORE scheduler
- Gaming latency, tickless, VM tuning patches
