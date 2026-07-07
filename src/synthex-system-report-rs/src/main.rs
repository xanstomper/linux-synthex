// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-system-report - Comprehensive system diagnostics in Rust

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::Serialize;
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-report", version = "0.1.0")]
struct Cli {
    #[command(subcommand)] cmd: ReportCommand,
    #[arg(long, global = true)] json: bool,
}

#[derive(Subcommand)]
enum ReportCommand { Generate, Save }

#[derive(Serialize)]
struct SystemReport {
    hostname: String, kernel: String, os: String,
    cpu: String, cpu_count: usize, ram_gb: String,
    gpu: String, disk: String, uptime: String,
    desktop: String, session: String,
    packages: String, flatpaks: String,
    firewall: String, selinux: String,
    services_failed: usize, zram: String,
}

fn run(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd).args(args).output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn run_sh(cmd: &str) -> String {
    Command::new("sh").args(["-c", cmd]).output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
        .unwrap_or_default()
}

fn collect() -> SystemReport {
    let mem = std::fs::read_to_string("/proc/meminfo").unwrap_or_default();
    let ram_mb = mem.lines().find(|l| l.starts_with("MemTotal"))
        .and_then(|l| l.split_whitespace().nth(1))
        .and_then(|k| k.parse::<f64>().ok())
        .map(|kb| format!("{:.1} GB", kb / 1048576.0)).unwrap_or_default();
    let cpu_count = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(0);
    SystemReport {
        hostname: run("hostname", &[]),
        kernel: run("uname", &["-r"]),
        os: run_sh("cat /etc/os-release 2>/dev/null | head -3"),
        cpu: run_sh("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2"),
        cpu_count,
        ram_gb: ram_mb,
        gpu: run_sh("lspci | grep -E 'VGA|3D' | head -1 | cut -d: -f3-"),
        disk: run_sh("df -h / | tail -1 | tr -s ' ' | cut -d' ' -f2,3,4,5"),
        uptime: run("uptime", &["-p"]),
        desktop: run_sh("echo ${XDG_CURRENT_DESKTOP:-unknown}"),
        session: run_sh("echo ${XDG_SESSION_TYPE:-unknown}"),
        packages: run_sh("rpm -qa 2>/dev/null | wc -l"),
        flatpaks: run_sh("flatpak list --app 2>/dev/null | wc -l"),
        firewall: run("firewall-cmd", &["--state"]),
        selinux: run("getenforce", &[]),
        services_failed: run_sh("systemctl --failed --no-legend 2>/dev/null | wc -l").parse().unwrap_or(0),
        zram: run_sh("zramctl --noheadings 2>/dev/null | head -1 | tr -s ' ' | cut -d' ' -f2,3,4"),
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let report = collect();
    match cli.cmd {
        ReportCommand::Save => {
            let path = format!("synthex-report-{}.json", chrono::Local::now().format("%Y%m%d"));
            std::fs::write(&path, serde_json::to_string_pretty(&report)?)?;
            println!("Report saved: {path}");
        }
        ReportCommand::Generate => {
            if cli.json { println!("{}", serde_json::to_string_pretty(&report)?); }
            else {
                println!("  System Report");
                println!("  Host:    {}", report.hostname);
                println!("  Kernel:  {}", report.kernel);
                println!("  CPU:     {} ({} cores)", report.cpu.trim(), report.cpu_count);
                println!("  GPU:     {}", report.gpu.trim());
                println!("  RAM:     {}", report.ram_gb);
                println!("  Disk:    {}", report.disk);
                println!("  Desktop: {} ({})", report.desktop, report.session);
                println!("  Pkgs:    {} / {} flatpak", report.packages, report.flatpaks);
                println!("  Firewall: {}  SELinux: {}", report.firewall, report.selinux);
            }
        }
    }
    Ok(())
}
