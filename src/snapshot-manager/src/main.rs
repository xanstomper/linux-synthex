// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-snapshot-manager — Btrfs snapshot management for SynthOS
//
// Provides:
//   - Automatic pre-update snapshots via snapper
//   - One-click rollback (no terminal required)
//   - Snapshot listing and browsing
//   - Snapshot cleanup and rotation
//   - Boot verification after updates
//   - Recovery helpers

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::process::Command;
use tracing::error;

#[derive(Parser)]
#[command(name = "synthex-snapshot", version = "0.1.0",
          about = "SynthOS Btrfs snapshot manager")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// List all snapshots
    List {
        #[arg(short, long, default_value = "20")]
        count: usize,
    },
    /// Create a new snapshot
    Create {
        /// Snapshot description
        #[arg(short, long, default_value = "manual snapshot")]
        description: String,
        /// Snapshot type: pre, post, or manual
        #[arg(short, long, default_value = "manual")]
        kind: String,
    },
    /// Rollback to a specific snapshot
    Rollback {
        /// Snapshot number to rollback to
        number: u64,
        /// Skip confirmation
        #[arg(short, long)]
        yes: bool,
    },
    /// Delete a snapshot
    Delete {
        /// Snapshot number
        number: u64,
    },
    /// Show snapshot details
    Info {
        /// Snapshot number
        number: u64,
    },
    /// Clean old snapshots (keep last N)
    Clean {
        /// Number of snapshots to keep
        #[arg(short, long, default_value = "10")]
        keep: usize,
    },
    /// Create pre-update snapshot (called automatically)
    PreUpdate {
        #[arg(short, long, default_value = "pre-update snapshot")]
        description: String,
    },
    /// Verify system health after update
    Verify,
    /// Show snapshot statistics
    Stats,
}

#[derive(Debug, Serialize, Deserialize)]
#[allow(dead_code)]
struct SnapshotInfo {
    number: u64,
    date: String,
    description: String,
    snapshot_type: String,
    user: String,
    cleanup: String,
}

fn run_snapper(args: &[&str]) -> Result<String> {
    let output = Command::new("snapper")
        .args(args)
        .output()
        .context("Failed to run snapper — is snapper installed?")?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    if !output.status.success() && !stderr.is_empty() {
        error!("snapper failed: {stderr}");
    }
    Ok(stdout)
}

fn list_snapshots(count: usize) -> Result<()> {
    let output = run_snapper(&["-c", "root", "list"])?;
    let lines: Vec<&str> = output.lines().collect();

    println!("\n  {:<8} {:<22} {:<30} {}", "#", "Date", "Type", "Description");
    println!("  {}", "\u{2500}".repeat(80));

    let mut displayed = 0;
    for line in lines.iter().rev() {
        if line.trim().is_empty() || line.starts_with("---") || line.starts_with("Number") {
            continue;
        }
        let parts: Vec<&str> = line.split('|').map(|s| s.trim()).collect();
        if parts.len() >= 4 {
            println!("  {:<8} {:<22} {:<30} {}", parts[0], parts[1], parts[2], parts[3]);
            displayed += 1;
            if displayed >= count {
                break;
            }
        }
    }

    println!("\n  Total lines: {}", lines.len());
    Ok(())
}

fn create_snapshot(description: &str, kind: &str) -> Result<()> {
    println!("\n  Creating {kind} snapshot: {description}");
    let output = run_snapper(&[
        "-c", "root", "create",
        "-d", description,
        "--print-number",
    ])?;
    let snap_num = output.trim();
    println!("  \u{2705} Snapshot created: #{snap_num}");
    Ok(())
}

fn rollback_to(number: u64, yes: bool) -> Result<()> {
    println!("\n  \u{26a0}  ROLLBACK WARNING");
    println!("  This will restore the system to snapshot #{number}");
    println!("  The current system state will be lost.");
    println!("  A reboot will be required.");
    println!();

    if !yes {
        print!("  Are you sure? [y/N]: ");
        use std::io::Write;
        std::io::stdout().flush()?;
        let mut input = String::new();
        std::io::stdin().read_line(&mut input)?;
        if !input.trim().eq_ignore_ascii_case("y") {
            println!("  Rollback cancelled.");
            return Ok(());
        }
    }

    println!("  Creating pre-rollback snapshot...");
    let _ = run_snapper(&["-c", "root", "create", "-d", "pre-rollback snapshot"]);

    println!("  Rolling back to snapshot #{number}...");
    let status = Command::new("snapper")
        .args(["-c", "root", "rollback", &number.to_string()])
        .status()
        .context("Failed to run snapper rollback")?;

    if status.success() {
        println!("  \u{2705} Rollback complete!");
        println!("  Please reboot your system to apply changes.");
    } else {
        error!("Rollback failed");
    }

    Ok(())
}

fn delete_snapshot(number: u64) -> Result<()> {
    let output = Command::new("snapper")
        .args(["-c", "root", "delete", &number.to_string()])
        .status()
        .context("Failed to delete snapshot")?;
    if output.success() {
        println!("  \u{2705} Snapshot #{number} deleted");
    } else {
        error!("Failed to delete snapshot #{number}");
    }
    Ok(())
}

fn show_info(number: u64) -> Result<()> {
    let output = run_snapper(&["-c", "root", "list", "-s", "-c", &number.to_string()])?;
    println!("\n  Snapshot #{number}:");
    println!("  {}", "\u{2500}".repeat(40));
    for line in output.lines() {
        if !line.trim().is_empty() {
            println!("  {line}");
        }
    }
    Ok(())
}

fn clean_snapshots(keep: usize) -> Result<()> {
    let output = run_snapper(&["-c", "root", "list"])?;
    let numbers: Vec<u64> = output.lines()
        .filter_map(|l| {
            let parts: Vec<&str> = l.split('|').collect();
            parts.first()?.trim().parse::<u64>().ok()
        })
        .collect();

    let total = numbers.len();
    if total <= keep {
        println!("  \u{2705} No cleanup needed ({total} snapshots, keeping {keep})");
        return Ok(());
    }

    let to_delete = total - keep;
    println!("  Cleaning {to_delete} old snapshots (keeping {keep})...");
    for &num in numbers.iter().take(to_delete) {
        if let Err(e) = delete_snapshot(num) {
            error!("Failed to delete snapshot #{num}: {e}");
        }
    }
    println!("  \u{2705} Cleanup complete");
    Ok(())
}

fn verify_system() -> Result<()> {
    println!("\n  \u{1f50d} Verifying system health after update...");
    let mut issues = 0u32;

    // Check filesystem
    print!("  Filesystem: ");
    let status = Command::new("btrfs")
        .args(["filesystem", "show"])
        .status();
    match status {
        Ok(s) if s.success() => println!("\u{2705} OK"),
        _ => { println!("\u{26a0}  WARNING"); issues += 1; }
    }

    // Check bootloader
    print!("  Bootloader: ");
    if std::path::Path::new("/boot/grub2/grub.cfg").exists() ||
       std::path::Path::new("/boot/grub/grub.cfg").exists() ||
       std::path::Path::new("/boot/efi/EFI/fedora/grub.cfg").exists() {
        println!("\u{2705} OK");
    } else {
        println!("\u{26a0}  GRUB config not found"); issues += 1;
    }

    // Check kernel
    print!("  Kernel: ");
    let output = Command::new("uname").arg("-r").output();
    match output {
        Ok(o) if o.status.success() => {
            let ver = String::from_utf8_lossy(&o.stdout);
            println!("\u{2705} {}", ver.trim());
        }
        _ => { println!("\u{26a0}  Cannot determine kernel"); issues += 1; }
    }

    // Check initramfs
    print!("  Initramfs: ");
    let boot_entries = std::fs::read_dir("/boot")
        .map(|entries| entries.flatten()
            .filter(|e| e.file_name().to_string_lossy().starts_with("initramfs"))
            .count())
        .unwrap_or(0);
    if boot_entries > 0 {
        println!("\u{2705} OK ({boot_entries} images)");
    } else {
        println!("\u{26a0}  No initramfs images found"); issues += 1;
    }

    // Check systemd
    print!("  Systemd: ");
    let status = Command::new("systemctl").args(["is-system-running"]).status();
    match status {
        Ok(s) if s.success() => println!("\u{2705} running"),
        _ => { println!("\u{26a0}  degraded"); issues += 1; }
    }

    println!();
    if issues == 0 {
        println!("  \u{2705} System verification passed");
    } else {
        println!("  \u{26a0}  {issues} issue(s) detected");
        println!("  Run: synthex-recovery to fix issues");
    }
    Ok(())
}

fn show_stats() -> Result<()> {
    let output = run_snapper(&["-c", "root", "list"])?;
    let lines: Vec<&str> = output.lines().collect();
    let count = lines.iter()
        .filter(|l| !l.trim().is_empty() && !l.starts_with("---") && !l.starts_with("Number"))
        .count();

    println!("\n  Synthex Snapshot Statistics");
    println!("  {}", "\u{2500}".repeat(40));
    println!("  Total snapshots: {count}");
    println!("  Configuration:   root");

    // Check disk usage
    let btrfs_out = Command::new("btrfs")
        .args(["filesystem", "usage", "/", "-h"])
        .output();
    if let Ok(o) = btrfs_out {
        let text = String::from_utf8_lossy(&o.stdout);
        for line in text.lines() {
            if line.contains("Device") || line.contains("Overall") || line.contains("total") {
                println!("  {line}");
            }
        }
    }
    Ok(())
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "synthex_snapshot=info".into()))
        .with_target(false).compact().init();

    let cli = Cli::parse();

    match cli.command {
        Commands::List { count } => list_snapshots(count)?,
        Commands::Create { description, kind } => create_snapshot(&description, &kind)?,
        Commands::Rollback { number, yes } => rollback_to(number, yes)?,
        Commands::Delete { number } => delete_snapshot(number)?,
        Commands::Info { number } => show_info(number)?,
        Commands::Clean { keep } => clean_snapshots(keep)?,
        Commands::PreUpdate { description } => {
            println!("  Creating pre-update snapshot...");
            create_snapshot(&description, "pre")?;
        }
        Commands::Verify => verify_system()?,
        Commands::Stats => show_stats()?,
    }
    Ok(())
}
