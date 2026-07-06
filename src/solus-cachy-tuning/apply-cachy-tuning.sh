#!/usr/bin/env bash
# apply-cachy-tuning.sh — Apply CachyOS-style performance tuning
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Run as root"; exit 1; }

echo "⚡ Applying CachyOS-style performance tuning..."

# ─── Sysctl tuning (CachyOS defaults) ─────────────────────────────────
cat > /etc/sysctl.d/99-solus-cachy.conf << 'EOF'
# ─── Memory ───────────────────────────────────────────────────────────
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.watermark_scale_factor = 100
vm.watermark_boost_factor = 0
vm.min_free_kbytes = 65536
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
vm.page_lock_unfairness = 1
vm.compact_unevictable_allowed = 0

# ─── Kernel scheduler ─────────────────────────────────────────────────
kernel.sched_latency_ns = 6000000
kernel.sched_min_granularity_ns = 750000
kernel.sched_wakeup_granularity_ns = 1000000
kernel.sched_migration_cost_ns = 500000
kernel.sched_cfs_bandwidth_slice_us = 3000

# ─── Network (CachyOS TCP tuning) ─────────────────────────────────────
net.core.somaxconn = 4096
net.core.netdev_max_backlog = 16384
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_notsent_lowat = 131072
net.core.default_qdisc = fq

# ─── I/O ──────────────────────────────────────────────────────────────
fs.aio-max-nr = 1048576
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 1024

# ─── Security (relaxed for performance, still safe) ───────────────────
kernel.kptr_restrict = 1
kernel.dmesg_restrict = 1
EOF

sysctl --system 2>/dev/null || true

# ─── I/O scheduler (BFQ for HDD, mq-deadline for SSD, none for NVMe) ──
for dev in /sys/block/sd*/queue/scheduler /sys/block/nvme*/queue/scheduler; do
    [ -f "$dev" ] || continue
    disk=$(echo "$dev" | cut -d/ -f4)
    if echo "$disk" | grep -q nvme; then
        echo none > "$dev" 2>/dev/null || true
    elif lsblk -d -o ROTA "/dev/$disk" 2>/dev/null | grep -q "^1$"; then
        echo bfq > "$dev" 2>/dev/null || true
    else
        echo mq-deadline > "$dev" 2>/dev/null || true
    fi
done

# ─── CPU governor (schedutil for modern CPUs) ─────────────────────────
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    [ -f "$cpu" ] && echo schedutil > "$cpu" 2>/dev/null || true
done

# ─── THP (transparent hugepages) ──────────────────────────────────────
echo madvise > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true
echo always > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true

# ─── ZRAM (CachyOS default: zstd, 50% of RAM) ─────────────────────────
cat > /etc/systemd/zram-generator.conf << 'EOF'
[zram0]
zram-fraction = 0.5
max-zram-size = 16384
compression-algorithm = zstd
EOF

systemctl restart systemd-zram-setup@zram0.service 2>/dev/null || true

echo "✅ CachyOS-style tuning applied"
