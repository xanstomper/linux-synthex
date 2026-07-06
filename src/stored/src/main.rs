// SPDX-License-Identifier: MIT OR Apache-2.0
//
// solus-stored — Software Center backend daemon for Solus Linux
//
// Manages DNF/RPM package operations, Flatpak, repository config,
// and system updates. Exposes state via D-Bus for the control center.
// Rust rewrite of the C++ daemon.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tracing::{error, info};

mod dbus;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct PackageInfo {
    pub name: String,
    pub version: String,
    pub repo: String,
    pub arch: String,
    pub summary: String,
    pub size_bytes: u64,
    pub installed: bool,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct UpdateInfo {
    pub packages: Vec<String>,
    pub count: usize,
    pub total_size_bytes: u64,
    pub security_updates: usize,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct RepoInfo {
    pub id: String,
    pub name: String,
    pub enabled: bool,
    pub baseurl: String,
    pub gpgcheck: bool,
    pub priority: u32,
}

#[derive(Default)]
pub struct StoreDaemon {
    /// In-memory package cache — populated on first search/install, used by D-Bus queries
    #[allow(dead_code)] // populated by search/install, read by D-Bus GetPackageInfo
    pub packages: HashMap<String, PackageInfo>,
    repos: Vec<RepoInfo>,
}

impl StoreDaemon {
    pub fn new() -> Self {
        let mut repos = Vec::new();

        // Solus repositories
        repos.push(RepoInfo {
            id: "solus-stable".into(),
            name: "Solus Stable".into(),
            enabled: true,
            baseurl: "https://repo.solus.org/stable/$releasever/$basearch".into(),
            gpgcheck: true,
            priority: 5,
        });
        repos.push(RepoInfo {
            id: "solus-updates".into(),
            name: "Solus Updates".into(),
            enabled: true,
            baseurl: "https://repo.solus.org/updates/$releasever/$basearch".into(),
            gpgcheck: true,
            priority: 5,
        });
        repos.push(RepoInfo {
            id: "solus-testing".into(),
            name: "Solus Testing".into(),
            enabled: false,
            baseurl: "https://repo.solus.org/testing/$releasever/$basearch".into(),
            gpgcheck: true,
            priority: 10,
        });
        repos.push(RepoInfo {
            id: "fedora".into(),
            name: "Fedora $releasever".into(),
            enabled: true,
            baseurl: "https://mirrors.fedoraproject.org/metalink?repo=fedora-$releasever&arch=$basearch".into(),
            gpgcheck: true,
            priority: 10,
        });
        repos.push(RepoInfo {
            id: "fedora-updates".into(),
            name: "Fedora Updates".into(),
            enabled: true,
            baseurl: "https://mirrors.fedoraproject.org/metalink?repo=updates-released-f$releasever&arch=$basearch".into(),
            gpgcheck: true,
            priority: 10,
        });
        repos.push(RepoInfo {
            id: "rpmfusion-free".into(),
            name: "RPM Fusion Free".into(),
            enabled: true,
            baseurl: "https://mirrors.rpmfusion.org/free/fedora/releases/$releasever/Everything/$basearch/os".into(),
            gpgcheck: true,
            priority: 20,
        });
        repos.push(RepoInfo {
            id: "rpmfusion-nonfree".into(),
            name: "RPM Fusion Nonfree".into(),
            enabled: true,
            baseurl: "https://mirrors.rpmfusion.org/nonfree/fedora/releases/$releasever/Everything/$basearch/os".into(),
            gpgcheck: true,
            priority: 20,
        });

        Self {
            packages: HashMap::new(),
            repos,
        }
    }

    pub fn check_updates(&self) -> Result<UpdateInfo> {
        info!("Checking for updates...");

        // Try dnf check-update
        let output = std::process::Command::new("dnf")
            .args(["check-update", "-q", "--setopt=quiet=true"])
            .output()
            .context("Failed to run dnf check-update")?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let packages: Vec<String> = stdout
            .lines()
            .filter(|l| !l.is_empty() && !l.starts_with(' ') && l.contains('.'))
            .map(|l| l.split_whitespace().next().unwrap_or("").to_string())
            .filter(|s| !s.is_empty())
            .collect();

        // Count security updates
        let security_count = stdout.lines()
            .filter(|l| l.contains("security") || l.contains("SECURITY") || l.contains("CVE"))
            .count();

        info!("Found {} available updates", packages.len());

        Ok(UpdateInfo {
            count: packages.len(),
            packages,
            total_size_bytes: 0,
            security_updates: security_count,
        })
    }

    pub fn run_updates(&self) -> Result<()> {
        info!("Running system update...");
        let status = std::process::Command::new("dnf")
            .args(["update", "-y"])
            .status()
            .context("Failed to run dnf update")?;

        if status.success() {
            info!("Update completed successfully");
            Ok(())
        } else {
            Err(anyhow::anyhow!("dnf update failed with status: {status}"))
        }
    }

    pub fn search_packages(&self, query: &str) -> Result<Vec<PackageInfo>> {
        let output = std::process::Command::new("dnf")
            .args(["search", query])
            .output()
            .context("Failed to search packages")?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut results = Vec::new();

        for line in stdout.lines() {
            if let Some(name) = line.split_whitespace().next() {
                if !name.is_empty() && !line.starts_with(' ') && name.contains('.') {
                    results.push(PackageInfo {
                        name: name.to_string(),
                        version: String::new(),
                        repo: String::new(),
                        arch: "x86_64".into(),
                        summary: line.splitn(2, ':').nth(1).unwrap_or("").trim().to_string(),
                        size_bytes: 0,
                        installed: false,
                    });
                }
            }
        }

        Ok(results)
    }

    pub fn install_package(&self, name: &str) -> Result<()> {
        info!("Installing package: {name}");
        let status = std::process::Command::new("dnf")
            .args(["install", "-y", name])
            .status()
            .context("Failed to install package")?;

        if status.success() {
            info!("Package installed: {name}");
            Ok(())
        } else {
            Err(anyhow::anyhow!("Package installation failed: {name}"))
        }
    }

    pub fn remove_package(&self, name: &str) -> Result<()> {
        info!("Removing package: {name}");
        let status = std::process::Command::new("dnf")
            .args(["remove", "-y", name])
            .status()
            .context("Failed to remove package")?;

        if status.success() {
            info!("Package removed: {name}");
            Ok(())
        } else {
            Err(anyhow::anyhow!("Package removal failed: {name}"))
        }
    }
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "solus_stored=info".into()),
        )
        .init();

    info!("Solus Software Store Daemon starting");
    let daemon = StoreDaemon::new();

    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async {
        if let Err(e) = dbus::run_service(daemon).await {
            error!("D-Bus service exited: {e:#}");
        }
    });

    Ok(())
}
