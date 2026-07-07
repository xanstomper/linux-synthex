// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-proton-manager — Manage Proton/Wine-GE versions per game
// Like Nobara but Rust-native with JSON output

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-proton", version = "0.1.0", about = "Proton/Wine-GE manager for SynthOS")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
    #[arg(long, global = true)]
    json: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// List installed Proton versions
    List,
    /// Install the latest GE-Proton
    Install { version: Option<String> },
    /// Set Proton version for a Steam game
    Set { game_id: String, proton: String },
    /// Show configuration for a game
    Config { game_id: String },
    /// Show current status
    Status,
    /// Remove a Proton version
    Remove { name: String },
}

#[derive(Debug, Serialize)]
struct ProtonInfo {
    name: String,
    version: String,
    path: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct GameConfig {
    games: HashMap<String, GameEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
struct GameEntry {
    proton: String,
    options: Vec<String>,
}

const PROTON_DIR: &str = "/usr/share/steam/compatibilitytools.d";
const GAME_CONFIG: &str = "/etc/synthex/proton-games.json";

fn list_protons(json: bool) -> Result<()> {
    let mut versions = Vec::new();
    if let Ok(entries) = std::fs::read_dir(PROTON_DIR) {
        for entry in entries.flatten() {
            let ver_path = entry.path().join("version");
            let ver = std::fs::read_to_string(&ver_path).unwrap_or_default();
            versions.push(ProtonInfo {
                name: entry.file_name().to_string_lossy().to_string(),
                version: ver.trim().to_string(),
                path: entry.path().to_string_lossy().to_string(),
            });
        }
    }
    if json {
        println!("{}", serde_json::to_string_pretty(&versions)?);
    } else {
        println!("
  Installed Proton Versions:
");
        if versions.is_empty() {
            println!("    (none installed)");
        }
        for v in &versions {
            println!("    {} ({})", v.name, v.version);
        }
    }
    Ok(())
}

fn install_ge() -> Result<()> {
    println!("Downloading latest GE-Proton...");
    // In production, this uses ureq/reqwest to fetch from GitHub
    // For now, print instructions
    println!("  wget https://github.com/GloriousEggroll/proton-ge-custom/releases/latest              tar -xf proton-ge-*.tar.gz -C {PROTON_DIR}");
    println!("Reboot Steam to see new Proton versions.");
    Ok(())
}

fn set_game(game_id: &str, proton: &str) -> Result<()> {
    let mut config: GameConfig = std::fs::read_to_string(GAME_CONFIG)
        .ok()
        .and_then(|s| serde_json::from_str(&s).ok())
        .unwrap_or(GameConfig { games: HashMap::new() });
    config.games.insert(game_id.to_string(), GameEntry {
        proton: proton.to_string(),
        options: vec![],
    });
    if let Some(parent) = std::path::Path::new(GAME_CONFIG).parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    std::fs::write(GAME_CONFIG, serde_json::to_string_pretty(&config)?)?;
    println!("Set game {game_id} to use {proton}");
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Commands::List => list_protons(cli.json),
        Commands::Install { version: _ } => install_ge(),
        Commands::Set { game_id, proton } => set_game(&game_id, &proton),
        Commands::Config { game_id } => { println!("Game {game_id} config"); Ok(()) },
        Commands::Status => list_protons(cli.json),
        Commands::Remove { name } => {
            let path = format!("{PROTON_DIR}/{name}");
            if std::path::Path::new(&path).exists() {
                std::fs::remove_dir_all(&path)?;
                println!("Removed {name}");
            } else {
                println!("Not found: {name}");
            }
            Ok(())
        }
    }
}
