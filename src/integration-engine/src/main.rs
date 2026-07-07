// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-integration-engine — Upstream monitoring and integration for SynthOS
//
// Monitors upstream Linux projects (Arch, Fedora, Nobara, Bazzite, CachyOS,
// KDE, Mesa, Kernel, Proton-GE, Wine-GE, PipeWire), classifies changes,
// and feeds approved candidates into the Synthex testing pipeline.
//
// Does NOT automatically merge. All changes require review + testing.

use anyhow::Result;
use chrono::{DateTime, Utc};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use tracing::{error, info};

#[derive(Parser)]
#[command(name = "synthex-integration-engine", version = "0.1.0",
          about = "SynthOS upstream integration and monitoring engine")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Scan,
    Status,
    Pending { #[arg(short, long)] category: Option<String> },
    Show { id: String },
    Approve { id: String },
    Reject { id: String, #[arg(short, long)] reason: String },
    Report { id: String },
    Daemon,
    Config,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
enum UpstreamSource {
    Arch, Fedora, Nobara, Bazzite, CachyOS, KDE, Mesa, LinuxKernel, ProtonGE, WineGE, PipeWire,
}

impl UpstreamSource {
    fn display_name(&self) -> &'static str {
        match self {
            Self::Arch => "Arch Linux", Self::Fedora => "Fedora", Self::Nobara => "Nobara",
            Self::Bazzite => "Bazzite", Self::CachyOS => "CachyOS", Self::KDE => "KDE Plasma",
            Self::Mesa => "Mesa", Self::LinuxKernel => "Linux Kernel", Self::ProtonGE => "Proton-GE",
            Self::WineGE => "Wine-GE", Self::PipeWire => "PipeWire",
        }
    }
    fn tracking_url(&self) -> &'static str {
        match self {
            Self::Arch => "https://archlinux.org/packages/",
            Self::Fedora => "https://src.fedoraproject.org/",
            Self::Nobara => "https://github.com/nicor-dev/nobara-meta",
            Self::Bazzite => "https://github.com/ublue-os/bazzite",
            Self::CachyOS => "https://github.com/CachyOS",
            Self::KDE => "https://invent.kde.org/plasma/",
            Self::Mesa => "https://gitlab.freedesktop.org/mesa/mesa",
            Self::LinuxKernel => "https://www.kernel.org/",
            Self::ProtonGE => "https://github.com/GloriousEggroll/proton-ge-custom",
            Self::WineGE => "https://github.com/GloriousEggroll/Wine-GE",
            Self::PipeWire => "https://gitlab.freedesktop.org/pipewire/pipewire",
        }
    }
    fn all() -> Vec<Self> {
        vec![Self::Arch, Self::Fedora, Self::Nobara, Self::Bazzite, Self::CachyOS,
             Self::KDE, Self::Mesa, Self::LinuxKernel, Self::ProtonGE, Self::WineGE, Self::PipeWire]
    }
}

impl std::fmt::Display for UpstreamSource {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.display_name())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
enum ChangeCategory {
    Security, Performance, Gaming, Hardware, Reliability, Desktop, Packaging,
}

impl ChangeCategory {
    fn icon(&self) -> &'static str {
        match self {
            Self::Security => "\u{1f512}", Self::Performance => "\u{26a1}", Self::Gaming => "\u{1f3ae}",
            Self::Hardware => "\u{1f5a5}", Self::Reliability => "\u{1f6e1}", Self::Desktop => "\u{1f5a5}",
            Self::Packaging => "\u{1f4e6}",
        }
    }
    fn display_name(&self) -> &'static str {
        match self {
            Self::Security => "Security", Self::Performance => "Performance", Self::Gaming => "Gaming",
            Self::Hardware => "Hardware", Self::Reliability => "Reliability", Self::Desktop => "Desktop",
            Self::Packaging => "Packaging",
        }
    }
}

impl std::fmt::Display for ChangeCategory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} {}", self.icon(), self.display_name())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
enum Priority { Critical, Recommended, Experimental }

impl Priority {
    fn as_str(&self) -> &'static str {
        match self {
            Self::Critical => "CRITICAL", Self::Recommended => "RECOMMENDED", Self::Experimental => "EXPERIMENTAL",
        }
    }
}

impl std::fmt::Display for Priority {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
enum CandidateStatus {
    Detected, Analyzing, PendingReview, Approved, Rejected, Testing, Merged, Failed,
}

impl CandidateStatus {
    fn display_name(&self) -> &'static str {
        match self {
            Self::Detected => "Detected", Self::Analyzing => "Analyzing", Self::PendingReview => "Pending Review",
            Self::Approved => "Approved", Self::Rejected => "Rejected", Self::Testing => "In Testing",
            Self::Merged => "Merged", Self::Failed => "Failed",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Candidate {
    id: String,
    source: UpstreamSource,
    category: ChangeCategory,
    priority: Priority,
    title: String,
    description: String,
    upstream_version: String,
    current_synthex_version: Option<String>,
    changelog_url: Option<String>,
    commit_hash: Option<String>,
    detected_at: DateTime<Utc>,
    status: CandidateStatus,
    compatibility_score: Option<u8>,
    risk_level: Option<String>,
    affected_packages: Vec<String>,
    synthex_patches_needed: Vec<String>,
    notes: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ScanStats {
    total_scans: u64,
    total_found: u64,
    approved: u64,
    rejected: u64,
    merged: u64,
    failed: u64,
    security: u64,
    performance: u64,
    gaming: u64,
    hardware: u64,
}

impl Default for ScanStats {
    fn default() -> Self {
        Self { total_scans: 0, total_found: 0, approved: 0, rejected: 0, merged: 0,
               failed: 0, security: 0, performance: 0, gaming: 0, hardware: 0 }
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct EngineState {
    candidates: Vec<Candidate>,
    upstream_snapshots: HashMap<String, String>,
    last_scan: Option<DateTime<Utc>>,
    stats: ScanStats,
}

impl EngineState {
    fn load(path: &PathBuf) -> Self {
        if path.exists() {
            if let Ok(c) = std::fs::read_to_string(path) {
                if let Ok(s) = serde_json::from_str(&c) { return s; }
            }
        }
        Self { candidates: vec![], upstream_snapshots: HashMap::new(),
               last_scan: None, stats: ScanStats::default() }
    }
    fn save(&self, path: &PathBuf) -> Result<()> {
        if let Some(p) = path.parent() { std::fs::create_dir_all(p)?; }
        std::fs::write(path, serde_json::to_string_pretty(self)?)?;
        Ok(())
    }
    fn state_path() -> PathBuf {
        dirs::state_dir().unwrap_or_else(|| PathBuf::from("/var/lib"))
            .join("synthex").join("integration-engine").join("state.json")
    }
    fn update_stats(&mut self) {
        self.stats.total_found = self.candidates.len() as u64;
        self.stats.security = self.candidates.iter().filter(|c| c.category == ChangeCategory::Security).count() as u64;
        self.stats.performance = self.candidates.iter().filter(|c| c.category == ChangeCategory::Performance).count() as u64;
        self.stats.gaming = self.candidates.iter().filter(|c| c.category == ChangeCategory::Gaming).count() as u64;
        self.stats.hardware = self.candidates.iter().filter(|c| c.category == ChangeCategory::Hardware).count() as u64;
    }
}

// ─── Scanners ─────────────────────────────────────────────────────────

async fn scan_proton_ge(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(rel) = r.json::<serde_json::Value>().await {
                let tag = rel["tag_name"].as_str().unwrap_or("unknown");
                let body = rel["body"].as_str().unwrap_or("");
                out.push(Candidate {
                    id: format!("proton-ge-{tag}"), source: UpstreamSource::ProtonGE,
                    category: ChangeCategory::Gaming, priority: Priority::Recommended,
                    title: format!("Proton-GE update: {tag}"),
                    description: body.chars().take(500).collect(),
                    upstream_version: tag.into(), current_synthex_version: None,
                    changelog_url: rel["html_url"].as_str().map(String::from),
                    commit_hash: None, detected_at: Utc::now(),
                    status: CandidateStatus::PendingReview,
                    compatibility_score: Some(90), risk_level: Some("low".into()),
                    affected_packages: vec!["proton-ge-custom".into()],
                    synthex_patches_needed: vec![],
                    notes: "Latest Proton-GE release".into(),
                });
            }
        }
    }
    out
}

async fn scan_kernel(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://www.kernel.org/releases.json";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(releases) = r.json::<serde_json::Value>().await {
                if let Some(entries) = releases["releases"].as_array() {
                    for entry in entries.iter().take(2) {
                        let ver = entry["version"].as_str().unwrap_or("unknown");
                        let stable = entry["stable"].as_bool().unwrap_or(false);
                        let lt = entry["longterm"].as_bool().unwrap_or(false);
                        let pri = if lt { Priority::Critical } else if stable { Priority::Recommended } else { Priority::Experimental };
                        out.push(Candidate {
                            id: format!("kernel-{ver}"), source: UpstreamSource::LinuxKernel,
                            category: ChangeCategory::Security, priority: pri,
                            title: format!("Linux kernel {ver} available"),
                            description: format!("Kernel {ver} ({})", if stable { "stable" } else if lt { "longterm" } else { "mainline" }),
                            upstream_version: ver.into(), current_synthex_version: None,
                            changelog_url: None, commit_hash: None, detected_at: Utc::now(),
                            status: CandidateStatus::PendingReview,
                            compatibility_score: Some(75), risk_level: Some("medium".into()),
                            affected_packages: vec!["kernel-core".into(), "kernel-zen".into()],
                            synthex_patches_needed: vec!["Reapply BORE/EEVDF patches".into(), "Validate NVIDIA compat".into()],
                            notes: "Kernel update — requires full validation".into(),
                        });
                    }
                }
            }
        }
    }
    out
}

async fn scan_mesa(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://gitlab.freedesktop.org/api/v4/projects/1293864/repository/tags?per_page=3";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(tags) = r.json::<serde_json::Value>().await {
                if let Some(arr) = tags.as_array() {
                    if let Some(tag) = arr.first() {
                        let name = tag["name"].as_str().unwrap_or("unknown");
                        out.push(Candidate {
                            id: format!("mesa-{name}"), source: UpstreamSource::Mesa,
                            category: ChangeCategory::Hardware, priority: Priority::Recommended,
                            title: format!("Mesa update: {name}"),
                            description: format!("Mesa GPU driver stack update: {name}"),
                            upstream_version: name.into(), current_synthex_version: None,
                            changelog_url: Some(format!("https://gitlab.freedesktop.org/mesa/mesa/-/tags/{name}")),
                            commit_hash: None, detected_at: Utc::now(),
                            status: CandidateStatus::PendingReview,
                            compatibility_score: Some(80), risk_level: Some("low".into()),
                            affected_packages: vec!["mesa".into(), "mesa-vulkan-drivers".into()],
                            synthex_patches_needed: vec![],
                            notes: "GPU driver stack update".into(),
                        });
                    }
                }
            }
        }
    }
    out
}

async fn scan_bazzite(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://api.github.com/repos/ublue-os/bazzite/releases/latest";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(rel) = r.json::<serde_json::Value>().await {
                let tag = rel["tag_name"].as_str().unwrap_or("unknown");
                let body = rel["body"].as_str().unwrap_or("");
                out.push(Candidate {
                    id: format!("bazzite-{tag}"), source: UpstreamSource::Bazzite,
                    category: ChangeCategory::Gaming, priority: Priority::Recommended,
                    title: format!("Bazzite release: {tag}"),
                    description: body.chars().take(500).collect(),
                    upstream_version: tag.into(), current_synthex_version: None,
                    changelog_url: rel["html_url"].as_str().map(String::from),
                    commit_hash: None, detected_at: Utc::now(),
                    status: CandidateStatus::PendingReview,
                    compatibility_score: Some(65), risk_level: Some("medium".into()),
                    affected_packages: vec!["gamescope".into()],
                    synthex_patches_needed: vec!["Review Gamescope patches".into()],
                    notes: "Bazzite gaming improvements".into(),
                });
            }
        }
    }
    out
}

async fn scan_nobara(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://api.github.com/repos/nicor-dev/nobara-meta/commits?per_page=3";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(commits) = r.json::<serde_json::Value>().await {
                if let Some(arr) = commits.as_array() {
                    for commit in arr.iter().take(3) {
                        let msg = commit["commit"]["message"].as_str().unwrap_or("");
                        let sha = commit["sha"].as_str().unwrap_or("unknown");
                        out.push(Candidate {
                            id: format!("nobara-{}", &sha[..8]), source: UpstreamSource::Nobara,
                            category: ChangeCategory::Gaming, priority: Priority::Recommended,
                            title: format!("Nobara: {}", msg.chars().take(80).collect::<String>()),
                            description: msg.into(), upstream_version: sha[..8].into(),
                            current_synthex_version: None,
                            changelog_url: commit["html_url"].as_str().map(String::from),
                            commit_hash: Some(sha.into()), detected_at: Utc::now(),
                            status: CandidateStatus::PendingReview,
                            compatibility_score: Some(75), risk_level: Some("medium".into()),
                            affected_packages: vec![],
                            synthex_patches_needed: vec!["Review Nobara gaming patches".into()],
                            notes: "Check Nobara-specific gaming patches".into(),
                        });
                    }
                }
            }
        }
    }
    out
}

async fn scan_cachyos(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://api.github.com/repos/CachyOS/linux-cachyos/commits?per_page=3";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(commits) = r.json::<serde_json::Value>().await {
                if let Some(arr) = commits.as_array() {
                    for commit in arr.iter().take(3) {
                        let msg = commit["commit"]["message"].as_str().unwrap_or("");
                        let sha = commit["sha"].as_str().unwrap_or("unknown");
                        out.push(Candidate {
                            id: format!("cachyos-{}", &sha[..8]), source: UpstreamSource::CachyOS,
                            category: ChangeCategory::Performance, priority: Priority::Recommended,
                            title: format!("CachyOS: {}", msg.chars().take(80).collect::<String>()),
                            description: msg.into(), upstream_version: sha[..8].into(),
                            current_synthex_version: None,
                            changelog_url: commit["html_url"].as_str().map(String::from),
                            commit_hash: Some(sha.into()), detected_at: Utc::now(),
                            status: CandidateStatus::PendingReview,
                            compatibility_score: Some(70), risk_level: Some("medium".into()),
                            affected_packages: vec!["kernel-zen".into()],
                            synthex_patches_needed: vec!["Review BORE scheduler patches".into()],
                            notes: "Performance kernel patches".into(),
                        });
                    }
                }
            }
        }
    }
    out
}

async fn scan_arch(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://archlinux.org/packages/?q=&repo=Core&arch=x86_64&sort=pkg_last_update";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            let body = r.text().await.unwrap_or_default();
            if body.contains("2026") {
                out.push(Candidate {
                    id: "arch-core-updates".into(), source: UpstreamSource::Arch,
                    category: ChangeCategory::Packaging, priority: Priority::Recommended,
                    title: "Arch Linux core repository updates available".into(),
                    description: "Arch core packages updated. Review for Synthex-relevant improvements.".into(),
                    upstream_version: "latest".into(), current_synthex_version: None,
                    changelog_url: Some("https://archlinux.org/packages/".into()),
                    commit_hash: None, detected_at: Utc::now(),
                    status: CandidateStatus::PendingReview,
                    compatibility_score: Some(80), risk_level: Some("low".into()),
                    affected_packages: vec![],
                    synthex_patches_needed: vec!["Review for relevant package updates".into()],
                    notes: "Arch core repo monitoring".into(),
                });
            }
        }
    }
    out
}

async fn scan_wine_ge(client: &reqwest::Client) -> Vec<Candidate> {
    let mut out = vec![];
    let url = "https://api.github.com/repos/GloriousEggroll/Wine-GE/releases/latest";
    if let Ok(r) = client.get(url).header("User-Agent", "synthex-ie/0.1").send().await {
        if r.status().is_success() {
            if let Ok(rel) = r.json::<serde_json::Value>().await {
                let tag = rel["tag_name"].as_str().unwrap_or("unknown");
                let body = rel["body"].as_str().unwrap_or("");
                out.push(Candidate {
                    id: format!("wine-ge-{tag}"), source: UpstreamSource::WineGE,
                    category: ChangeCategory::Gaming, priority: Priority::Recommended,
                    title: format!("Wine-GE update: {tag}"),
                    description: body.chars().take(500).collect(),
                    upstream_version: tag.into(), current_synthex_version: None,
                    changelog_url: rel["html_url"].as_str().map(String::from),
                    commit_hash: None, detected_at: Utc::now(),
                    status: CandidateStatus::PendingReview,
                    compatibility_score: Some(85), risk_level: Some("low".into()),
                    affected_packages: vec!["wine-ge".into()],
                    synthex_patches_needed: vec![],
                    notes: "Wine-GE compatibility update".into(),
                });
            }
        }
    }
    out
}

// ─── Report ───────────────────────────────────────────────────────────

fn print_status(state: &EngineState) {
    println!();
    println!("{}", "\u{2550}".repeat(60));
    println!("  Synthex Integration Engine \u{2014} Status");
    println!("{}", "\u{2560}".repeat(60));
    println!("  Last Scan:     {}", state.last_scan.map(|d| d.format("%Y-%m-%d %H:%M UTC").to_string()).unwrap_or_else(|| "never".into()));
    println!("  Total:         {} candidates", state.stats.total_found);
    println!("  Security:      {}", state.stats.security);
    println!("  Performance:   {}", state.stats.performance);
    println!("  Gaming:        {}", state.stats.gaming);
    println!("  Hardware:      {}", state.stats.hardware);
    println!("  Approved:      {}", state.stats.approved);
    println!("  Rejected:      {}", state.stats.rejected);
    println!("{}", "\u{2550}".repeat(60));

    let pending: Vec<_> = state.candidates.iter().filter(|c| c.status == CandidateStatus::PendingReview).collect();
    if !pending.is_empty() {
        println!("\n  Pending ({})\n", pending.len());
        for c in &pending {
            println!("  [{}] {} {}", c.id, c.category, c.title);
            println!("    Source: {} | Risk: {} | Score: {}/100", c.source,
                c.risk_level.as_deref().unwrap_or("?"), c.compatibility_score.unwrap_or(0));
        }
    }
}

// ─── Main ──────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::try_from_default_env()
            .unwrap_or_else(|_| "synthex_integration_engine=info".into()))
        .with_target(false).compact().init();

    let cli = Cli::parse();
    let state_path = EngineState::state_path();
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30)).build().unwrap_or_default();

    match cli.command {
        Commands::Scan => {
            println!("\u{1f50d} Scanning upstream sources...");
            let mut state = EngineState::load(&state_path);
            let mut total = 0u32;

            let scan_groups: Vec<(&str, Vec<Candidate>)> = vec![
                ("Proton-GE", scan_proton_ge(&client).await),
                ("Kernel", scan_kernel(&client).await),
                ("Mesa", scan_mesa(&client).await),
                ("Bazzite", scan_bazzite(&client).await),
                ("Nobara", scan_nobara(&client).await),
                ("CachyOS", scan_cachyos(&client).await),
                ("Arch", scan_arch(&client).await),
                ("Wine-GE", scan_wine_ge(&client).await),
            ];

            for (name, candidates) in scan_groups {
                let count = candidates.len();
                print!("  Scanning {name:<20} ");
                for c in candidates {
                    if !state.candidates.iter().any(|x| x.id == c.id) {
                        state.candidates.push(c);
                        total += 1;
                    }
                }
                println!("\u{2705} {count} candidate(s)");
            }

            state.last_scan = Some(Utc::now());
            state.stats.total_scans += 1;
            state.update_stats();
            state.save(&state_path)?;

            println!("\n\u{2705} Scan complete: {total} new candidate(s)");
            println!("   Total: {}", state.candidates.len());
        }

        Commands::Status => {
            let state = EngineState::load(&state_path);
            print_status(&state);
        }

        Commands::Pending { category } => {
            let state = EngineState::load(&state_path);
            let pending: Vec<_> = state.candidates.iter()
                .filter(|c| c.status == CandidateStatus::PendingReview)
                .filter(|c| category.as_ref().map_or(true, |cat| match cat.as_str() {
                    "security" => c.category == ChangeCategory::Security,
                    "performance" => c.category == ChangeCategory::Performance,
                    "gaming" => c.category == ChangeCategory::Gaming,
                    "hardware" => c.category == ChangeCategory::Hardware,
                    _ => true,
                }))
                .collect();
            if pending.is_empty() { println!("\u{2705} No pending candidates"); }
            else {
                println!("\n  Pending ({}):\n", pending.len());
                for (i, c) in pending.iter().enumerate() {
                    println!("{}. [{}] {} — {}", i+1, c.id, c.category, c.title);
                    println!("   {} | {} | {}/100", c.source, c.priority, c.compatibility_score.unwrap_or(0));
                }
            }
        }

        Commands::Show { id } => {
            let state = EngineState::load(&state_path);
            match state.candidates.iter().find(|c| c.id == id) {
                Some(c) => println!("{}", serde_json::to_string_pretty(c)?),
                None => error!("Not found: {id}"),
            }
        }

        Commands::Approve { id } => {
            let mut state = EngineState::load(&state_path);
            match state.candidates.iter_mut().find(|c| c.id == id) {
                Some(c) => { c.status = CandidateStatus::Approved; state.stats.approved += 1; state.save(&state_path)?; println!("\u{2705} Approved {id}"); }
                None => error!("Not found: {id}"),
            }
        }

        Commands::Reject { id, reason } => {
            let mut state = EngineState::load(&state_path);
            match state.candidates.iter_mut().find(|c| c.id == id) {
                Some(c) => { c.status = CandidateStatus::Rejected; c.notes = format!("Rejected: {reason}"); state.stats.rejected += 1; state.save(&state_path)?; println!("\u{274c} Rejected {id}: {reason}"); }
                None => error!("Not found: {id}"),
            }
        }

        Commands::Report { id } => {
            let state = EngineState::load(&state_path);
            match state.candidates.iter().find(|c| c.id == id) {
                Some(c) => {
                    println!("\n=== Integration Report ===");
                    println!("  Title:    {}", c.title);
                    println!("  Source:   {}", c.source);
                    println!("  Category: {}", c.category);
                    println!("  Priority: {}", c.priority);
                    println!("  Version:  {}", c.upstream_version);
                    println!("  Risk:     {}", c.risk_level.as_deref().unwrap_or("?"));
                    println!("  Compat:   {}/100", c.compatibility_score.unwrap_or(0));
                    println!("  Status:   {}", c.status.display_name());
                    println!("\n  {}", c.description);
                    if !c.affected_packages.is_empty() {
                        println!("\n  Packages: {}", c.affected_packages.join(", "));
                    }
                    if !c.synthex_patches_needed.is_empty() {
                        println!("\n  Patches needed:");
                        for p in &c.synthex_patches_needed { println!("    \u{26a0} {p}"); }
                    }
                }
                None => error!("Not found: {id}"),
            }
        }

        Commands::Daemon => {
            info!("Integration Engine daemon starting (hourly scans)");
            let mut interval = tokio::time::interval(std::time::Duration::from_secs(3600));
            loop {
                interval.tick().await;
                info!("Running scheduled scan...");
                let mut state = EngineState::load(&state_path);
                for c in scan_proton_ge(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_kernel(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_mesa(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_bazzite(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_nobara(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_cachyos(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_arch(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                for c in scan_wine_ge(&client).await { if !state.candidates.iter().any(|x| x.id == c.id) { state.candidates.push(c); } }
                state.last_scan = Some(Utc::now());
                state.stats.total_scans += 1;
                state.update_stats();
                let _ = state.save(&state_path);
            }
        }

        Commands::Config => {
            println!("Synthex Integration Engine Configuration\n");
            for s in UpstreamSource::all() {
                println!("  {} — {}", s, s.tracking_url());
            }
            println!("\nState: {}", EngineState::state_path().display());
        }
    }
    Ok(())
}
