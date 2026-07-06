// SPDX-License-Identifier: MIT OR Apache-2.0
use anyhow::Result;
use clap::{Parser, Subcommand};
use std::process::Command;

fn is_root() -> bool {
    Command::new("id").arg("-u").output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim() == "0")
        .unwrap_or(false)
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

#[derive(Parser)]
#[command(name="solus-kernel", version="0.1.0", about="Solus Linux kernel manager")]
struct Cli { #[command(subcommand)] cmd: Commands }

#[derive(Subcommand)]
enum Commands {
    List,
    Info { #[arg(default_value="")] version: String },
    Install { #[arg(default_value="latest")] version: String },
    Remove { version: String },
    Switch,
    Default { index: usize },
    Cleanup,
}

fn list_kernels() {
    let running = run("uname", &["-r"]).trim().to_string();
    println!("\n  📦 Installed Kernels\n");
    let mut kernels: Vec<String> = std::fs::read_dir("/boot")
        .map(|e| e.flatten().filter(|f| f.file_name().to_string_lossy().starts_with("vmlinuz"))
            .map(|f| f.file_name().to_string_lossy().replace("vmlinuz-", "")).collect())
        .unwrap_or_default();
    kernels.sort(); kernels.reverse();
    for k in &kernels {
        if k == &running { println!("    ▶ {k}  (running)"); }
        else { println!("      {k}"); }
    }
    println!("\n  📦 Available in repos:\n");
    let out = run("dnf", &["list", "available", "kernel*", "--quiet"]);
    let mut count = 0;
    for line in out.lines().skip(1) {
        let p: Vec<&str> = line.split_whitespace().collect();
        if p.len() >= 2 && p[0].starts_with("kernel") {
            println!("    {:<40} {}", p[0], p[1]);
            count += 1;
            if count >= 15 { println!("    ... (and more)"); break; }
        }
    }
    println!();
}

fn kernel_info(ver: &str) {
    let v = if ver.is_empty() { run("uname", &["-r"]).trim().to_string() } else { ver.to_string() };
    let running = run("uname", &["-r"]).trim().to_string();
    println!("\n  📋 Kernel: {v}\n");
    println!("    Running:  {}", if v == running { "yes" } else { "no" });
    println!("    Arch:     {}", run("uname", &["-m"]).trim());
    let vmlinuz = format!("/boot/vmlinuz-{v}");
    println!("    Installed: {}", std::path::Path::new(&vmlinuz).exists());
    let moddir = format!("/lib/modules/{v}");
    let modcount = std::fs::read_dir(&moddir).map(|e| e.flatten().count()).unwrap_or(0);
    println!("    Modules:  {modcount} entries");
    let sched = std::fs::read_to_string("/sys/block/sda/queue/scheduler").unwrap_or_default();
    println!("    I/O Scheduler: {}", sched.trim());
    println!();
}

fn install_kernel(version: &str) {
    println!("\n  📦 Installing kernel: {version}\n");
    let pkgs = match version {
        "zen" => vec![String::from("kernel-zen"), String::from("kernel-zen-core"), String::from("kernel-zen-modules")],
        "latest" | "stable" => vec![String::from("kernel"), String::from("kernel-core"), String::from("kernel-modules")],
        v => vec![format!("kernel-{v}"), format!("kernel-core-{v}")],
    };
    let refs: Vec<&str> = pkgs.iter().map(|s| s.as_str()).collect();
    let mut args = vec!["install", "-y"];
    args.extend_from_slice(&refs);
    sudo_run("dnf", &args);
    println!("  📋 Rebuilding initramfs...");
    sudo_run("dracut", &["--force", "--regenerate-all"]);
    println!("  📋 Rebuilding GRUB...");
    sudo_run("grub2-mkconfig", &["-o", "/boot/grub2/grub.cfg"]);
    println!("  ✅ Kernel installed. Reboot to use.\n");
}

fn remove_kernel(version: &str) {
    let running = run("uname", &["-r"]).trim().to_string();
    if version == running { println!("  ❌ Cannot remove running kernel"); return; }
    println!("  Removing kernel {version}...");
    sudo_run("dnf", &["remove", "-y", &format!("kernel-{version}"), &format!("kernel-core-{version}"), &format!("kernel-modules-{version}")]);
    sudo_run("grub2-mkconfig", &["-o", "/boot/grub2/grub.cfg"]);
    println!("  ✅ Removed.");
}

fn switch_kernel() {
    println!("\n  🔄 Kernel Switching\n");
    println!("  Reboot and select from GRUB menu, or:");
    println!("    sudo grub2-set-default <index>");
    println!("    sudo grub2-reboot <index>  (once)\n");
}

fn cleanup_kernels() {
    println!("\n  🧹 Cleaning old kernels (keeping running + 1 backup)...\n");
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
            sudo_run("dnf", &["remove", "-y", &format!("kernel-{k}"), &format!("kernel-core-{k}"), &format!("kernel-modules-{k}")]);
        }
    }
    println!("  ✅ Done.\n");
}

fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter(
        tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_|"solus_kernel=info".into()))
        .with_target(false).compact().init();
    let cli = Cli::parse();
    match cli.cmd {
        Commands::List => list_kernels(),
        Commands::Info{version} => kernel_info(&version),
        Commands::Install{version} => install_kernel(&version),
        Commands::Remove{version} => remove_kernel(&version),
        Commands::Switch => switch_kernel(),
        Commands::Default{index} => { println!("Setting default to GRUB #{index}"); sudo_run("grub2-set-default", &[&index.to_string()]); println!("✅ Done. Reboot."); },
        Commands::Cleanup => cleanup_kernels(),
    }
    Ok(())
}
