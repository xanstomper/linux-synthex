// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-terminal-workspace — tmux-powered terminal workspaces
// Rust rewrite of synthex-term Python script for better performance

use anyhow::Result;
use clap::{Parser, Subcommand};
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-term", version = "0.1.0", about = "Terminal workspace manager")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Open a workspace (dev, monitor, general, gaming)
    Workspace { name: String },
    /// List active tmux sessions
    Sessions,
    /// Attach to a tmux session
    Attach { name: String },
}

const WORKSPACES: &[(&str, &str, &[&[&str]])] = &[
    ("dev", "Development", &[
        &["nvim .", "cargo watch -x check", "git status"],
        &["btop", "htop -t"],
        &["make -j$(nproc) 2>&1 | tail -30", "echo 'Build ready'"],
    ]),
    ("monitor", "System Monitor", &[
        &["btop", "htop -t", "journalctl -f -n 50", "df -h; free -h"],
        &["ping 1.1.1.1"],
    ]),
    ("general", "General", &[
        &["echo 'Welcome to Synthex Terminal'", "btop"],
    ]),
    ("gaming", "Gaming", &[
        &["mangohud", "gamemoderun steam", "nvtop"],
    ]),
];

fn open_workspace(name: &str) -> Result<()> {
    let ws = WORKSPACES.iter().find(|w| w.0 == name)
        .ok_or_else(|| anyhow::anyhow!("Unknown workspace: {}. Available: dev, monitor, general, gaming", name))?;

    let session_name = format!("synthex-{}", name);
    println!("Opening workspace: {} ({})", ws.1, session_name);

    // Check if tmux is available
    if Command::new("which").arg("tmux").status().map(|s| !s.success()).unwrap_or(true) {
        println!("tmux not found. Please install: sudo dnf install tmux");
        return Ok(());
    }

    // Check if session exists
    let has_session = Command::new("tmux")
        .args(["has-session", "-t", &session_name])
        .status()
        .map(|s| s.success())
        .unwrap_or(false);

    if has_session {
        println!("Attaching to existing session...");
        Command::new("tmux")
            .args(["attach-session", "-t", &session_name])
            .status()?;
        return Ok(());
    }

    // Create new session
    println!("Creating new workspace...");
    // We delegate to the Python script for complex tmux setup
    Command::new("synthex-term.py")
        .args(["workspace", name])
        .status()?;

    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::Workspace { name } => open_workspace(&name)?,
        Commands::Sessions => {
            Command::new("tmux").arg("list-sessions").status()?;
        }
        Commands::Attach { name } => {
            Command::new("tmux").args(["attach-session", "-t", &name]).status()?;
        }
    }
    Ok(())
}
