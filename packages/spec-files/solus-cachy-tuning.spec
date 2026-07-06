%define _name solus-cachy-tuning
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux CachyOS-compatibility performance tuning — kernel, sysctl, ZRAM, I/O

License:        GPL-2.0-or-later
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils
Source0:        apply-cachy-tuning.sh
Source1:        tuned-profiles/solus-gaming/tuned.conf
Source2:        tuned-profiles/solus-balanced/tuned.conf
Source3:        tuned-profiles/solus-powersave/tuned.conf
Source4:        ananicy-rules/solus-rules.conf

# ─── Performance tuning tools ─────────────────────────────────────────
Requires:       tuned
Requires:       tuned-utils
Requires:       tuned-profiles-compat

# ─── ZRAM configuration (CachyOS default) ─────────────────────────────
Requires:       zram-generator
Requires:       zstd

# ─── I/O scheduler tuning ─────────────────────────────────────────────
Requires:       iotop
Requires:       iotop-c

# ─── CPU frequency tools ──────────────────────────────────────────────
Requires:       cpupower
Requires:       cpupower-gui

# ─── Network tuning ───────────────────────────────────────────────────
Requires:       ethtool
Requires:       irqbalance

# ─── Performance monitoring ───────────────────────────────────────────
Requires:       perf
Requires:       sysstat
Requires:       turbostat

# ─── CachyOS-style fish shell ─────────────────────────────────────────
Requires:       fish
Requires:       fish-shell-completions

# ─── CachyOS repository tools ─────────────────────────────────────────
Requires:       cachyos-hello
Requires:       cachyos-packageinstaller

# ─── Ananicy (process priority daemon, CachyOS uses this) ─────────────
Requires:       ananicy-cpp
Requires:       ananicy-rules

%description
Solus Linux CachyOS-compatibility performance tuning. Ports CachyOS's
performance optimizations to Solus:

  - tuned: dynamic performance profiles (throughput/latency/powersave)
  - ZRAM: memory compression with zstd (CachyOS default)
  - ananicy-cpp: process priority daemon for smoother desktop
  - cpupower + cpupower-gui: CPU frequency management
  - BFQ/mq-deadline I/O scheduler tuning
  - Network stack tuning (TCP BBR, buffer sizes)
  - irqbalance: interrupt distribution across cores
  - fish shell: CachyOS's default shell with completions
  - CachyOS Hello app: performance overview
  - sysctl presets: vm.swappiness, vfs_cache_pressure, watermark tuning

These match CachyOS's kernel/scheduler/memory/IO/network optimizations.

%prep
%setup -c -T
cp %{SOURCE0} .
cp %{SOURCE1} solus-gaming-tuned.conf
cp %{SOURCE2} solus-balanced-tuned.conf
cp %{SOURCE3} solus-powersave-tuned.conf
cp %{SOURCE4} solus-rules.conf

%build
# Nothing to build — configs and scripts only

%install
install -d -m 0755 %{buildroot}%{_prefix}/libexec/solus
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysctl.d
install -d -m 0755 %{buildroot}%{_sysconfdir}/tuned/solus-gaming
install -d -m 0755 %{buildroot}%{_sysconfdir}/tuned/solus-balanced
install -d -m 0755 %{buildroot}%{_sysconfdir}/tuned/solus-powersave
install -d -m 0755 %{buildroot}%{_sysconfdir}/ananicy.d/solus-rules

# Tuning script
install -m 0755 apply-cachy-tuning.sh %{buildroot}%{_prefix}/libexec/solus/apply-cachy-tuning.sh

# Tuned profiles
install -m 0644 solus-gaming-tuned.conf    %{buildroot}%{_sysconfdir}/tuned/solus-gaming/tuned.conf
install -m 0644 solus-balanced-tuned.conf  %{buildroot}%{_sysconfdir}/tuned/solus-balanced/tuned.conf
install -m 0644 solus-powersave-tuned.conf %{buildroot}%{_sysconfdir}/tuned/solus-powersave/tuned.conf

# Ananicy rules
install -m 0644 solus-rules.conf %{buildroot}%{_sysconfdir}/ananicy.d/solus-rules/solus-rules.conf

# Sysctl tuning
cat > %{buildroot}%{_sysconfdir}/sysctl.d/99-solus-cachy.conf << 'EOF'
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 15
vm.watermark_scale_factor = 125
vm.min_free_kbytes = 65536
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 4096
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
kernel.sched_latency_ns = 4000000
kernel.sched_min_granularity_ns = 500000
kernel.sched_wakeup_granularity_ns = 500000
EOF

%files
%{_sysconfdir}/sysctl.d/99-solus-cachy.conf
%{_sysconfdir}/tuned/solus-gaming/tuned.conf
%{_sysconfdir}/tuned/solus-balanced/tuned.conf
%{_sysconfdir}/tuned/solus-powersave/tuned.conf
%{_sysconfdir}/ananicy.d/solus-rules/*
%{_prefix}/libexec/solus/apply-cachy-tuning.sh

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-cachy-tuning package
- Tuned profiles (gaming/balanced/powersave), ananicy rules, sysctl tuning
