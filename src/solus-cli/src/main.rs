// SPDX-License-Identifier: MIT OR Apache-2.0
//
// solus-cli — Unified command-line interface for Solus Linux
//
// Provides: info, hardware, gpu, layout, status, version subcommands.
// Replaces the shell-based tools (solus-gpu-switch, solus-layout, etc.)
// with a single Rust binary.

use anyhow::Result;
use clap::{Parser, Subcommand};

mod hardware;
mod status;

#[derive(Parser)]
#[command(name = "solus", version, about = "Solus Linux — unified system tool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Show system information
    Info,
    /// Detect and display hardware
    Hardware {
        /// Output as JSON
        #[arg(long)]
        json: bool,
    },
    /// GPU information and switching
    Gpu {
        #[command(subcommand)]
        action: GpuAction,
    },
    /// System status overview
    Status,
}

#[derive(Subcommand)]
enum GpuAction {
    /// List detected GPUs
    List,
    /// Switch GPU mode (nvidia, integrated, hybrid, compute)
    Switch {
        mode: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Info => {
            let sys_info = status::system_info();
            println!("{sys_info}");
        }
        Commands::Hardware { json } => {
            let hw = hardware::detect_hardware()?;
            if json {
                println!("{}", serde_json::to_string_pretty(&hw)?);
            } else {
                println!("{hw}");
            }
        }
        Commands::Gpu { action } => {
            match action {
                GpuAction::List => {
                    let hw = hardware::detect_hardware()?;
                    for (i, gpu) in hw.gpus.iter().enumerate() {
                        println!("GPU {i}: {vendor} {device} ({driver})",
                            vendor = gpu.vendor,
                            device = gpu.device,
                            driver = gpu.driver,
                        );
                    }
                }
                GpuAction::Switch { mode } => {
                    println!("Switching to GPU mode: {mode}");
                    // Write mode to /run/solus/gpu-mode for the daemon to pick up
                    if let Err(e) = std::fs::write("/run/solus/gpu-mode", &mode) {
                        eprintln!("Failed to set GPU mode: {e}");
                    }
                }
            }
        }
        Commands::Status => {
            let sys_info = status::system_info();
            println!("{sys_info}");
        }
    }

    Ok(())
}
