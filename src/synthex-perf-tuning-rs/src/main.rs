// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-perf-tuning — CachyOS-style performance auto-tuning in Rust
// CPU governor, I/O scheduler, zram, sysctl, THP

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-perf", version = "0.1.0")]
struct Cli {
    #[command(subcommand)] cmd: PerfCommand,
}

#[derive(clap::Subcommand)]
enum PerfCommand {
    /// Apply CachyOS-style performance tuning
    Apply,
    /// Reset to system defaults
    Reset,
    /// Show current tuning status
    Status,
}

fn write_file(path: &str, content: &str) -> bool {
    Command::new("sudo").args(["sh", "-c", &format!("echo '{}' > {}", content.replace("'", "'\"'"), path)])
        .status().map(|s| s.success()).unwrap_or(false)
}

fn apply_tuning() -> Result<()> {
    println!("Applying CachyOS-style performance tuning...");
    // CPU governor
    for cpu in 0..64 {
        let p = format!("/sys/devices/system/cpu/cpu{}/cpufreq/scaling_governor", cpu);
        let _ = Command::new("sudo").args(["sh", "-c", &format!("echo schedutil > {}", p)]).status();
    }
    // I/O scheduler: none for NVMe, mq-deadline for SSD
    let _ = Command::new("sudo").args(["sh", "-c", "echo mq-deadline > /sys/block/sda/queue/scheduler"]).status();
    // Set swappiness
    let _ = Command::new("sudo").args(["sysctl", "-w", "vm.swappiness=10"]).status();
    let _ = Command::new("sudo").args(["sysctl", "-w", "vm.vfs_cache_pressure=50"]).status();
    let _ = Command::new("sudo").args(["sysctl", "-w", "kernel.sched_latency_ns=6000000"]).status();
    let _ = Command::new("sudo").args(["sysctl", "-w", "kernel.sched_min_granularity_ns=750000"]).status();
    // Network tuning
    let _ = Command::new("sudo").args(["sysctl", "-w", "net.core.default_qdisc=fq"]).status();
    let _ = Command::new("sudo").args(["sysctl", "-w", "net.ipv4.tcp_congestion_control=bbr"]).status();
    // THP
    let _ = Command::new("sudo").args(["sh", "-c", "echo always > /sys/kernel/mm/transparent_hugepage/enabled"]).status();
    // ZRAM config
    let _ = Command::new("sudo").args(["sh", "-c",
        "echo '[zram0]\nzram-fraction = 0.5\ncompression-algorithm = zstd' > /etc/systemd/zram-generator.conf"]).status();
    println!("Performance tuning applied");
    Ok(())
}

fn show_status() -> Result<()> {
    println!("");
    println!("  Performance Tuning Status");
    let gov = std::fs::read_to_string("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor").unwrap_or_default();
    println!("  CPU Governor: {}", gov.trim());
    let sched = std::fs::read_to_string("/sys/block/sda/queue/scheduler").unwrap_or_default();
    println!("  I/O Scheduler: {}", sched.trim());
    let swap = std::fs::read_to_string("/proc/sys/vm/swappiness").unwrap_or_default();
    println!("  Swappiness: {}", swap.trim());
    let cc = std::fs::read_to_string("/proc/sys/net/ipv4/tcp_congestion_control").unwrap_or_default();
    println!("  TCP CC: {}", cc.trim());
    println!();
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        PerfCommand::Apply => apply_tuning(),
        PerfCommand::Reset => {
            let _ = Command::new("sudo").args(["sysctl", "-w", "vm.swappiness=60"]).status();
            println!("Reset to defaults");
            Ok(())
        }
        PerfCommand::Status => show_status(),
    }
}
