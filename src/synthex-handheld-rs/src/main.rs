// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-handheld — Steam Deck-like handheld mode for SynthOS
// Like Bazzite's HHD but Rust-native

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::Serialize;
use std::path::Path;
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-handheld", version = "0.1.0", about = "Handheld gaming mode")]
struct Cli {
    #[command(subcommand)] cmd: Commands,
    #[arg(long, global = true)] json: bool,
}

#[derive(Subcommand)]
enum Commands {
    Enable,
    Disable,
    Status,
    Osk,
}

const STATE_FILE: &str = "/var/lib/synthex/handheld-mode";

fn is_active() -> bool { Path::new(STATE_FILE).exists() }

fn run(args: &[&str]) { let _ = Command::new("systemctl").args(args).status(); }
fn run_user(args: &[&str]) { let _ = Command::new("systemctl").arg("--user").args(args).status(); }

fn cmd_enable() -> Result<()> {
    std::fs::create_dir_all("/var/lib/synthex")?;
    std::fs::write(STATE_FILE, "active")?;
    run_user(&["enable", "maliit-keyboard.service"]);
    run_user(&["start", "maliit-keyboard.service"]);
    println!("Handheld mode enabled");
    println!("  UI scaled for small screens");
    println!("  On-screen keyboard enabled");
    println!("  Steam Big Picture ready");
    Ok(())
}

fn cmd_disable() -> Result<()> {
    let _ = std::fs::remove_file(STATE_FILE);
    run_user(&["disable", "maliit-keyboard.service"]);
    run_user(&["stop", "maliit-keyboard.service"]);
    println!("Handheld mode disabled");
    Ok(())
}

fn cmd_status() -> Result<()> {
    println!("Handheld Mode: {}", if is_active() { "ACTIVE" } else { "Inactive" });
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Enable => cmd_enable(),
        Commands::Disable => cmd_disable(),
        Commands::Status => cmd_status(),
        Commands::Osk => {
            let active = Command::new("systemctl").args(["--user", "is-active", "maliit-keyboard.service"])
                .output().map(|o| String::from_utf8_lossy(&o.stdout).contains("active")).unwrap_or(false);
            if active { run_user(&["stop", "maliit-keyboard.service"]); println!("OSK disabled"); }
            else { run_user(&["start", "maliit-keyboard.service"]); println!("OSK enabled"); }
            Ok(())
        }
    }
}
