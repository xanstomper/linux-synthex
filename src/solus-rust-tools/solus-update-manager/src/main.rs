use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use tracing_subscriber::EnvFilter;

/// Solus Update Manager — checks, downloads, and applies system updates
///
/// Manages DNF5 updates with snapshot support via snapper/btrfs,
/// parallel download optimisation, and pre/post update hooks.
#[derive(Parser, Debug)]
#[command(name = "solus-update-manager", version = "0.1.0", about)]
enum Cli {
    /// Check for available updates
    Check {
        /// Show only security updates
        #[arg(short, long)]
        security: bool,
    },
    /// Download and apply available updates
    Update {
        /// Skip snapshot creation before updating
        #[arg(long)]
        no_snapshot: bool,
        /// Non-interactive mode (assume yes)
        #[arg(short, long)]
        yes: bool,
    },
    /// List update history
    History {
        /// Show last N entries
        #[arg(default_value = "10")]
        count: usize,
    },
    /// Create a system snapshot (btrfs)
    Snapshot {
        /// Snapshot description
        #[arg(short, long, default_value = "pre-update snapshot")]
        description: String,
    },
    /// Show update statistics
    Stats,
}

#[derive(Debug, Serialize, Deserialize)]
struct UpdateConfig {
    /// Automatically check for updates on startup
    auto_check: bool,
    /// Check interval in hours
    check_interval: u32,
    /// Create snapshots before updates
    snapshots: bool,
    /// Maximum parallel downloads
    max_parallel_downloads: u32,
    /// Update categories to include
    categories: Vec<String>,
}

impl Default for UpdateConfig {
    fn default() -> Self {
        Self {
            auto_check: true,
            check_interval: 6,
            snapshots: true,
            max_parallel_downloads: 5,
            categories: vec![
                "security".into(),
                "bugfix".into(),
                "enhancement".into(),
                "gaming".into(),
            ],
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct UpdateStatus {
    last_check: Option<DateTime<Utc>>,
    last_update: Option<DateTime<Utc>>,
    pending_updates: u32,
    security_updates: u32,
    system_snapshot: Option<String>,
}

impl UpdateStatus {
    fn load() -> Result<Self> {
        let path = Self::status_path();
        if path.exists() {
            let content = std::fs::read_to_string(&path)?;
            Ok(serde_json::from_str(&content)?)
        } else {
            Ok(Self {
                last_check: None,
                last_update: None,
                pending_updates: 0,
                security_updates: 0,
                system_snapshot: None,
            })
        }
    }

    fn save(&self) -> Result<()> {
        let path = Self::status_path();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let content = serde_json::to_string_pretty(self)?;
        std::fs::write(&path, content)?;
        Ok(())
    }

    fn status_path() -> PathBuf {
        dirs::state_dir()
            .unwrap_or_else(|| PathBuf::from("/var/lib"))
            .join("solus")
            .join("update-manager")
            .join("status.json")
    }

    fn config_path() -> PathBuf {
        dirs::config_dir()
            .unwrap_or_else(|| PathBuf::from("/etc"))
            .join("solus")
            .join("update-manager.toml")
    }
}

fn dnf_command() -> Command {
    Command::new("dnf5")
}

fn run_command(cmd: &mut Command, description: &str) -> Result<String> {
    tracing::info!("Running: {} ({description})", format!("{cmd:?}"));
    let output = cmd.output().context(format!("Failed to execute {description}"))?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        anyhow::bail!("{description} failed:\n{stderr}");
    }
    Ok(stdout)
}

fn check_updates(security_only: bool) -> Result<()> {
    let mut cmd = dnf_command();
    cmd.args(["check-update", "--quiet"]);
    if security_only {
        cmd.arg("--security");
    }
    match cmd.status() {
        Ok(status) if status.success() => {
            println!("✓ System is up to date. No updates available.");
        }
        Ok(_) => {
            // dnf check-update returns 100 when updates are available
            let mut list_cmd = dnf_command();
            list_cmd.args(["list", "--upgrades", "--quiet"]);
            if security_only {
                list_cmd.arg("--security");
            }
            let output = list_cmd
                .output()
                .context("Failed to list available updates")?;
            let stdout = String::from_utf8_lossy(&output.stdout);
            let count = stdout.lines().filter(|l| !l.is_empty()).count();
            println!(
                "📦 {} update{} available",
                count,
                if count == 1 { "" } else { "s" }
            );
            if !stdout.is_empty() {
                println!("{stdout}");
            }
        }
        Err(e) => anyhow::bail!("Failed to run dnf check-update: {e}"),
    }

    let mut status = UpdateStatus::load()?;
    status.last_check = Some(Utc::now());
    status.save()?;
    Ok(())
}

fn apply_updates(no_snapshot: bool, yes: bool) -> Result<()> {
    tracing::info!("Starting system update");

    // Create snapshot unless skipped
    if !no_snapshot {
        println!("📸 Creating pre-update BTRFS snapshot...");
        let snap_cmd = Command::new("snapper")
            .args(["-c", "root", "create", "-d", "pre-update snapshot"])
            .output();
        match snap_cmd {
            Ok(o) if o.status.success() => tracing::info!("Snapshot created"),
            Ok(_) => tracing::warn!("Snapshot creation failed (snapper may not be configured)"),
            Err(e) => tracing::warn!("snapper not available: {e}"),
        }
    }

    // Run dnf upgrade
    let mut cmd = dnf_command();
    cmd.args(["upgrade", "--refresh"]);
    if yes {
        cmd.arg("-y");
    }
    println!("🔄 Applying updates...");
    let status = cmd.status().context("Failed to run dnf upgrade")?;
    if status.success() {
        println!("✅ Updates applied successfully");
        let mut status = UpdateStatus::load()?;
        status.last_update = Some(Utc::now());
        status.save()?;
    } else {
        anyhow::bail!("dnf upgrade failed with status: {status}");
    }
    Ok(())
}

fn show_history(count: usize) -> Result<()> {
    let mut cmd = dnf_command();
    let output = cmd
        .args(["history", "--quiet"])
        .output()
        .context("Failed to get update history")?;
    let stdout = String::from_utf8_lossy(&output.stdout);
    let lines: Vec<&str> = stdout.lines().collect();
    let start = if lines.len() > count + 1 {
        lines.len() - count - 1
    } else {
        0
    };
    for line in &lines[start..] {
        println!("{line}");
    }
    Ok(())
}

fn create_snapshot(description: &str) -> Result<()> {
    let output = Command::new("snapper")
        .args(["-c", "root", "create", "-d", description])
        .output()
        .context("Failed to create snapper snapshot")?;
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        println!("✅ Snapshot created: {stdout}");
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        anyhow::bail!("Snapshot creation failed: {stderr}");
    }
    Ok(())
}

fn show_stats() -> Result<()> {
    let status = UpdateStatus::load()?;

    println!("=== Solus Update Manager ===");
    println!(
        "Last check:      {}",
        status
            .last_check
            .map(|d| d.to_rfc3339())
            .unwrap_or_else(|| "never".into())
    );
    println!(
        "Last update:     {}",
        status
            .last_update
            .map(|d| d.to_rfc3339())
            .unwrap_or_else(|| "never".into())
    );
    println!("Pending updates: {}", status.pending_updates);
    println!("Security:        {}", status.security_updates);

    // Show system info
    let sys = sysinfo::System::new_all();
    println!("\n=== System ===");
    println!(
        "OS:              {} {}",
        sys.long_os_version().unwrap_or_default(),
        sys.kernel_version().unwrap_or_default()
    );
    println!("Uptime:          {:?}", chrono::Duration::seconds(sys.uptime() as i64));

    Ok(())
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .with_target(false)
        .compact()
        .init();

    let config_path = UpdateStatus::config_path();
    let _config: UpdateConfig = if config_path.exists() {
        let content = std::fs::read_to_string(&config_path)?;
        toml::from_str(&content)?
    } else {
        let cfg = UpdateConfig::default();
        // Write default config if it doesn't exist
        if let Some(parent) = config_path.parent() {
            std::fs::create_dir_all(parent).ok();
        }
        std::fs::write(&config_path, toml::to_string_pretty(&cfg)?).ok();
        cfg
    };

    let cli = Cli::parse();

    match cli {
        Cli::Check { security } => check_updates(security),
        Cli::Update { no_snapshot, yes } => apply_updates(no_snapshot, yes),
        Cli::History { count } => show_history(count),
        Cli::Snapshot { description } => create_snapshot(&description),
        Cli::Stats => show_stats(),
    }
}
