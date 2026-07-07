// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-kernel-manager - Kernel management for SynthOS

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::Serialize;
use serde_json;
use std::process::Command;

fn is_root() -> bool {
    Command::new("id").arg("-u").output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim() == "0").unwrap_or(false)
}

fn sudo_run(cmd: &str, args: &[&str]) -> bool {
    let out = if is_root() { Command::new(cmd).args(args).status() }
    else { Command::new("sudo").arg(cmd).args(args).status() };
    out.map(|s| s.success()).unwrap_or(false)
}

fn run(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd).args(args).output()
        .map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default()
}

fn create_snapshot(label: &str) {
    if run("which", &["snapper"]).contains("snapper") {
        sudo_run("snapper", &["-c", "root", "create", "-d", label]);
    } else if run("which", &["btrfs"]).contains("btrfs") {
        let _ = std::fs::create_dir_all("/.snapshots");
        let ts = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
        sudo_run("btrfs", &["subvolume", "snapshot", "-r", "/",
            &format!("/.snapshots/synthex-kernel-{}", ts)]);
    }
}

#[derive(Debug, Serialize)]
struct KernelEntry {
    version: String,
    running: bool,
}

#[derive(Debug, Serialize)]
struct KernelInfo {
    version: String,
    running: bool,
    arch: String,
    scheduler: String,
    modules: usize,
}

#[derive(Parser)]
#[command(name="synthex-kernel", version="0.2.0", about="SynthOS kernel manager")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
    #[arg(long, global = true)]
    json: bool,
}

#[derive(Subcommand)]
enum Commands {
    List,
    Info { version: String },
    Install { version: String },
    Remove { version: String },
    Switch,
    Default { index: usize },
    Cleanup,
    Current,
}

fn list_kernels(json: bool) {
    let running = run("uname", &["-r"]).trim().to_string();
    let mut kernels: Vec<String> = std::fs::read_dir("/boot")
        .map(|e| e.flatten().filter(|f| f.file_name().to_string_lossy().starts_with("vmlinuz"))
            .map(|f| f.file_name().to_string_lossy().replace("vmlinuz-", "")).collect())
        .unwrap_or_default();
    kernels.sort(); kernels.reverse();
    if json {
        let entries: Vec<KernelEntry> = kernels.iter().map(|k| KernelEntry {
            version: k.clone(), running: k == &running,
        }).collect();
        println!("{}", serde_json::to_string_pretty(&entries).unwrap_or_default());
        return;
    }
    println!("");
    println!("  Installed Kernels");
    for k in &kernels {
        if k == &running { println!("    * {k}  (running)"); }
        else { println!("      {k}"); }
    }
    println!();
}

fn kernel_info(ver: &str, json: bool) {
    let v = if ver.is_empty() { run("uname", &["-r"]).trim().to_string() } else { ver.to_string() };
    let running = run("uname", &["-r"]).trim().to_string();
    let sched = std::fs::read_to_string("/sys/block/sda/queue/scheduler").unwrap_or_default();
    let moddir = format!("/lib/modules/{v}");
    let modcount = std::fs::read_dir(&moddir).map(|e| e.flatten().count()).unwrap_or(0);
    let info = KernelInfo {
        version: v.clone(), running: v == running,
        arch: run("uname", &["-m"]).trim().to_string(),
        scheduler: sched.trim().to_string(), modules: modcount,
    };
    if json {
        println!("{}", serde_json::to_string_pretty(&info).unwrap_or_default());
    } else {
        println!("");
        println!("  Kernel: {v}");
        println!("    Running:  {}", if info.running { "yes" } else { "no" });
        println!("    Arch:     {}", info.arch);
        println!("    Modules:  {modcount}");
        println!("    Sched:    {}", info.scheduler);
        println!();
    }
}

fn install_kernel(version: &str) {
    println!("");
    println!("  Installing kernel: {version}");
    println!("  Snapshot before install...");
    create_snapshot(&format!("pre-kernel-{}", version));
    let pkgs: Vec<String> = match version {
        "zen" => vec!["kernel-zen", "kernel-zen-core", "kernel-zen-modules"]
            .into_iter().map(String::from).collect(),
        "latest" | "stable" => vec!["kernel", "kernel-core", "kernel-modules"]
            .into_iter().map(String::from).collect(),
        v => vec![format!("kernel-{v}")],
    };
    let mut args = vec!["install".to_string(), "-y".to_string()];
    for p in &pkgs { args.push(p.clone()); }
    let arg_refs: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
    sudo_run("dnf", &arg_refs);
    println!("  Rebuilding initramfs...");
    sudo_run("dracut", &["--force", "--regenerate-all"]);
    println!("  Rebuilding GRUB...");
    sudo_run("grub2-mkconfig", &["-o", "/boot/grub2/grub.cfg"]);
    println!("  Kernel installed. Reboot to use.");
    println!();
}

fn remove_kernel(version: &str) {
    let running = run("uname", &["-r"]).trim().to_string();
    if version == running { println!("  Cannot remove running kernel"); return; }
    println!("  Removing kernel {version}...");
    sudo_run("dnf", &["remove", "-y",
        &format!("kernel-{version}"),
        &format!("kernel-core-{version}"),
        &format!("kernel-modules-{version}")]);
    sudo_run("grub2-mkconfig", &["-o", "/boot/grub2/grub.cfg"]);
    println!("  Removed.");
}

fn show_current(json: bool) {
    let v = run("uname", &["-r"]).trim().to_string();
    let arch = run("uname", &["-m"]).trim().to_string();
    let sched = std::fs::read_to_string("/sys/block/sda/queue/scheduler").unwrap_or_default();
    let hostname = run("uname", &["-n"]).trim().to_string();
    if json {
        let mut map = serde_json::Map::new();
        map.insert("version".into(), serde_json::Value::String(v));
        map.insert("arch".into(), serde_json::Value::String(arch));
        map.insert("hostname".into(), serde_json::Value::String(hostname));
        map.insert("scheduler".into(), serde_json::Value::String(sched.trim().to_string()));
        println!("{}", serde_json::to_string_pretty(&map).unwrap_or_default());
    } else {
        println!("");
        println!("  Current Kernel");
        println!("    Version:  {v}");
        println!("    Arch:     {arch}");
        println!("    Host:     {hostname}");
        println!("    Sched:    {}", sched.trim());
        println!();
    }
}

fn switch_kernel() {
    println!("");
    println!("  Kernel Switching");
    println!("  Reboot and select from GRUB menu, or:");
    println!("    sudo grub2-set-default <index>");
    println!("    sudo grub2-reboot <index>  (once)");
    println!();
}

fn cleanup_kernels() {
    println!("");
    println!("  Cleaning old kernels...");
    let running = run("uname", &["-r"]).trim().to_string();
    let mut kernels: Vec<String> = std::fs::read_dir("/boot")
        .map(|e| e.flatten().filter(|f| f.file_name().to_string_lossy().starts_with("vmlinuz"))
            .map(|f| f.file_name().to_string_lossy().replace("vmlinuz-", "")).collect())
        .unwrap_or_default();
    kernels.sort(); kernels.reverse();
    let mut keep = 0;
    for k in &kernels {
        if k == &running { continue; }
        keep += 1;
        if keep > 1 {
            println!("    Removing: {k}");
            sudo_run("dnf", &["remove", "-y",
                &format!("kernel-{k}"), &format!("kernel-core-{k}"), &format!("kernel-modules-{k}")]);
        }
    }
    sudo_run("grub2-mkconfig", &["-o", "/boot/grub2/grub.cfg"]);
    println!("  Done.");
    println!();
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let json = cli.json;
    match cli.cmd {
        Commands::List => list_kernels(json),
        Commands::Info { version } => kernel_info(&version, json),
        Commands::Install { version } => install_kernel(&version),
        Commands::Remove { version } => remove_kernel(&version),
        Commands::Switch => switch_kernel(),
        Commands::Default { index } => {
            println!("Setting default to GRUB #{index}");
            sudo_run("grub2-set-default", &[&index.to_string()]);
            println!("Done. Reboot.");
        }
        Commands::Cleanup => cleanup_kernels(),
        Commands::Current => show_current(json),
    }
    Ok(())
}

