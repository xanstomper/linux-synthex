#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Cachy Tuning — apply CachyOS-inspired performance tweaks

import sys, os, subprocess, logging
logging.basicConfig(level=logging.INFO, format="[cachy-tuning] %(levelname)s %(message)s")
log = logging.getLogger("cachy-tuning")

SYSCTL_TWEAKS = {
    # Memory management
    "vm.swappiness":                  "10",
    "vm.vfs_cache_pressure":          "50",
    "vm.dirty_ratio":                 "6",
    "vm.dirty_background_ratio":      "3",
    "vm.dirty_expire_centisecs":      "500",
    "vm.dirty_writeback_centisecs":   "100",
    "vm.overcommit_memory":           "1",
    "vm.watermark_boost_factor":      "0",
    "vm.watermark_scale_factor":      "125",

    # Network
    "net.core.netdev_max_backlog":    "16384",
    "net.core.somaxconn":             "8192",
    "net.core.rmem_default":          "1048576",
    "net.core.wmem_default":          "1048576",
    "net.core.rmem_max":              "16777216",
    "net.core.wmem_max":              "16777216",
    "net.ipv4.tcp_fastopen":          "3",
    "net.ipv4.tcp_congestion_control":"bbr",
    "net.ipv4.tcp_slow_start_after_idle": "0",

    # Security (minimal impact)
    "kernel.kptr_restrict":           "2",
    "kernel.dmesg_restrict":          "1",

    # CPU
    "kernel.sched_latency_ns":        "3000000",
    "kernel.sched_min_granularity_ns":"300000",
    "kernel.sched_wakeup_granularity_ns": "500000",
    "kernel.nmi_watchdog":            "0",
    "kernel.watchdog":                "0",
    "kernel.timer_migration":         "0",
}

UDEV_RULES = """# SynthOS performance udev rules
# I/O scheduler — BFQ for HDD/SSD, none for NVMe
ACTION=="add|change", KERNEL=="sd[a-z]|hd[a-z]", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="bfq"
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="bfq"
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
# CPU readahead
ACTION=="add|change", KERNEL=="sd[a-z]|nvme[0-9]n[0-9]", ATTR{bdi/read_ahead_kb}="2048"
"""

def apply_sysctl():
    log.info("Applying sysctl tweaks")
    conf_path = "/etc/sysctl.d/99-synthex-cachy.conf"
    with open(conf_path, "w") as f:
        f.write("# SynthOS CachyOS-inspired performance sysctl\n")
        for k, v in SYSCTL_TWEAKS.items():
            f.write(f"{k} = {v}\n")
    subprocess.run(["sysctl","--system"], capture_output=True, timeout=30)
    log.info(f"Sysctl written: {conf_path}")

def apply_udev():
    log.info("Applying I/O scheduler udev rules")
    rules_path = "/etc/udev/rules.d/60-synthex-io-scheduler.rules"
    with open(rules_path, "w") as f:
        f.write(UDEV_RULES)
    subprocess.run(["udevadm","control","--reload-rules"], capture_output=True, timeout=10)
    subprocess.run(["udevadm","trigger"], capture_output=True, timeout=10)
    log.info(f"Udev rules written: {rules_path}")

def set_cpu_governor(governor="schedutil"):
    log.info(f"Setting CPU governor: {governor}")
    for cpu in os.listdir("/sys/devices/system/cpu"):
        gov_path = f"/sys/devices/system/cpu/{cpu}/cpufreq/scaling_governor"
        if os.path.exists(gov_path):
            try:
                with open(gov_path, "w") as f:
                    f.write(governor)
            except PermissionError:
                log.debug("Cannot set governor for %s: permission denied", gov_path)

def set_irq_affinity():
    """Enable IRQ balancing for multi-core."""
    subprocess.run(["systemctl","enable","--now","irqbalance.service"],
                   capture_output=True, timeout=15)
    log.info("IRQ balance enabled")

def apply_transparent_hugepages(mode="madvise"):
    thp = "/sys/kernel/mm/transparent_hugepage/enabled"
    if os.path.exists(thp):
        try:
            with open(thp, "w") as f:
                f.write(mode)
            log.info(f"THP set to: {mode}")
        except PermissionError:
            log.warning("Cannot write THP setting (need root)")

def main():
    if os.geteuid() != 0:
        print("Error: cachy-tuning must run as root", file=sys.stderr)
        sys.exit(1)

    log.info("Applying SynthOS performance tuning")
    apply_sysctl()
    apply_udev()
    set_cpu_governor()
    set_irq_affinity()
    apply_transparent_hugepages()
    log.info("Performance tuning complete")

if __name__ == "__main__":
    main()
