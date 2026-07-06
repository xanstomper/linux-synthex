use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use std::process::Command;
use tracing_subscriber::EnvFilter;

/// Solus Package Manager — DNF5 wrapper with Solus-specific features
///
/// Provides package search, install, remove, and info commands with
/// Solus repository support, category browsing, and Flatpak integration.
#[derive(Parser, Debug)]
#[command(name = "solus-pkg", version = "0.1.0", about)]
enum Cli {
    /// Install packages
    Install {
        /// Package name(s)
        packages: Vec<String>,
        /// Non-interactive mode
        #[arg(short, long)]
        yes: bool,
    },
    /// Remove packages
    Remove {
        /// Package name(s)
        packages: Vec<String>,
    },
    /// Search packages
    Search {
        /// Search term
        query: String,
    },
    /// Show package info
    Info {
        /// Package name
        package: String,
    },
    /// List installed packages
    List {
        /// Filter by pattern
        pattern: Option<String>,
    },
    /// List Solus repository packages by category
    Categories {
        /// Show packages in a category
        category: Option<String>,
    },
    /// Update package database
    Refresh,
    /// Verify package integrity
    Verify {
        /// Package name
        package: Option<String>,
    },
    /// Search for packages in Solus repos only
    Solus {
        /// Search term
        query: Option<String>,
        /// List all Solus packages
        #[arg(long)]
        all: bool,
    },
}

#[derive(Debug, Serialize, Deserialize)]
struct PackageInfo {
    name: String,
    version: String,
    release: String,
    arch: String,
    summary: String,
    license: String,
    description: String,
    url: String,
    size: String,
    install_size: String,
    repo: String,
    dependencies: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct SolusRepo {
    name: String,
    baseurl: String,
    gpgkey: String,
    enabled: bool,
}

fn dnf_command() -> Command {
    Command::new("dnf5")
}

fn run_dnf(args: &[&str]) -> Result<String> {
    let output = dnf_command()
        .args(args)
        .output()
        .context("Failed to run dnf5")?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    if !output.status.success() {
        anyhow::bail!("dnf5 failed:\n{stderr}");
    }
    Ok(stdout)
}

fn run_dnf_interactive(args: &[&str], yes: bool) -> Result<bool> {
    let mut cmd = dnf_command();
    cmd.args(args);
    if yes {
        cmd.arg("-y");
    }
    let status = cmd.status().context("Failed to run dnf5")?;
    Ok(status.success())
}

fn install(packages: &[String], yes: bool) -> Result<()> {
    let pkg_list: Vec<&str> = packages.iter().map(|s| s.as_str()).collect();
    let mut args = vec!["install"];
    args.extend_from_slice(&pkg_list);

    println!("📦 Installing {} package(s)...", packages.len());
    for pkg in packages {
        println!("  • {pkg}");
    }

    if run_dnf_interactive(&args, yes)? {
        println!("✅ Installation complete");
    } else {
        anyhow::bail!("Installation failed");
    }
    Ok(())
}

fn remove(packages: &[String]) -> Result<()> {
    let pkg_list: Vec<&str> = packages.iter().map(|s| s.as_str()).collect();
    let mut args = vec!["remove", "-y"];
    args.extend_from_slice(&pkg_list);

    println!("🗑 Removing {} package(s)...", packages.len());
    if run_dnf_interactive(&args, true)? {
        println!("✅ Removal complete");
    } else {
        anyhow::bail!("Removal failed");
    }
    Ok(())
}

fn search(query: &str) -> Result<()> {
    println!("🔍 Searching for '{query}'...");
    let output = run_dnf(&["search", query])?;
    if output.trim().is_empty() {
        println!("No results found");
    } else {
        for line in output.lines().filter(|l| !l.is_empty()) {
            println!("{line}");
        }
    }
    Ok(())
}

fn info(package: &str) -> Result<()> {
    let output = run_dnf(&["info", package])?;
    println!("=== Package Info: {package} ===");
    for line in output.lines() {
        println!("{line}");
    }
    Ok(())
}

fn list_installed(pattern: Option<&str>) -> Result<()> {
    let mut args = vec!["list", "--installed"];
    if let Some(p) = pattern {
        args.push(p);
    }
    let output = run_dnf(&args)?;
    let count = output.lines().filter(|l| !l.is_empty()).count();
    println!("📋 Installed packages ({count})");
    println!("{output}");
    Ok(())
}

fn refresh() -> Result<()> {
    println!("🔄 Refreshing package database...");
    let output = run_dnf(&["refresh"])?;
    println!("{output}");
    println!("✅ Database refreshed");
    Ok(())
}

fn verify(package: Option<&str>) -> Result<()> {
    if let Some(pkg) = package {
        let output = run_dnf(&["verify", pkg])?;
        println!("{output}");
    } else {
        let output = run_dnf(&["verify"])?;
        println!("{output}");
    }
    println!("✅ Verification complete");
    Ok(())
}

fn list_categories(category: Option<&str>) -> Result<()> {
    let solus_repo = "/etc/yum.repos.d/solus.repo";
    let repo_content = std::fs::read_to_string(solus_repo).unwrap_or_default();

    println!("=== Solus Package Categories ===");
    println!();
    println!("Available categories (groupinstall):");
    println!("  solus-core         — Base system (kernel, systemd, dnf5)");
    println!("  solus-plasma       — KDE Plasma desktop environment");
    println!("  solus-gnome        — GNOME desktop environment");
    println!("  solus-hyprland     — Hyprland compositor environment");
    println!("  solus-gaming       — Gaming stack (Steam, Proton, Wine)");
    println!("  solus-developer    — Development tools (Rust, Python, Go)");
    println!("  solus-creator      — Content creation (Blender, Kdenlive)");
    println!("  solus-ai           — AI/ML tools (Ollama, WebUI)");
    println!("  solus-rust-tools   — Rust utility suite (rg, fd, bat, eza)");
    println!("  solus-nvidia       — NVIDIA proprietary drivers");
    println!("  solus-optimus      — NVIDIA Optimus switching tools");
    println!("  solus-codecs       — Multimedia codecs");
    println!("  solus-containers   — Podman, Docker, Distrobox");

    if let Some(cat) = category {
        println!("\n=== Packages in '{cat}' ===");
        let output = run_dnf(&[
            "group",
            "info",
            cat,
        ])
        .unwrap_or_else(|_| format!("Category '{cat}' not found or not installed"));
        println!("{output}");
    }
    Ok(())
}

fn list_solus_packages(query: Option<&str>, all: bool) -> Result<()> {
    let repo_flag = "--repo=solus";

    if all {
        println!("📋 Listing all Solus repository packages...");
        let output = run_dnf(&["list", "--available", repo_flag])?;
        println!("{output}");
    } else if let Some(q) = query {
        println!("🔍 Searching Solus repos for '{q}'...");
        let output = run_dnf(&["search", repo_flag, q])?;
        println!("{output}");
    } else {
        println!("Usage: solus-pkg solus --all (list all) or solus-pkg solus <query> (search)");
    }
    Ok(())
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .with_target(false)
        .compact()
        .init();

    let cli = Cli::parse();

    match cli {
        Cli::Install { packages, yes } => install(&packages, yes),
        Cli::Remove { packages } => remove(&packages),
        Cli::Search { query } => search(&query),
        Cli::Info { package } => info(&package),
        Cli::List { pattern } => list_installed(pattern.as_deref()),
        Cli::Refresh => refresh(),
        Cli::Verify { package } => verify(package.as_deref()),
        Cli::Categories { category } => list_categories(category.as_deref()),
        Cli::Solus { query, all } => list_solus_packages(query.as_deref(), all),
    }
}
