use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::HashMap,
    fs,
    os::unix::fs::PermissionsExt,
    path::PathBuf,
    process::Command,
};
use walkdir::WalkDir;

// Constants
const STATE_FILE: &str = "/var/lib/synthshield/state.json";
const BASELINE_DIR: &str = "/var/lib/synthshield/baselines";
const MONITORED_DIRS: &[&str] = &["/etc", "/usr/bin", "/usr/sbin", "/usr/lib", "/boot"];
const MAX_HASHES: usize = 100_000;

// Types
#[derive(Debug, Clone, Serialize, Deserialize)]
struct FileHash {
    path: String,
    sha256: String,
    size: u64,
    mode: u32,
    uid: u32,
    gid: u32,
    mtime_secs: u64,
}

#[derive(Debug, Serialize, Deserialize)]
struct ShieldState {
    active: bool,
    snapshot_count: u64,
    last_scan: String,
    last_scan_files: usize,
    last_scan_modified: usize,
    last_scan_added: usize,
    last_scan_removed: usize,
    baseline_hashes: Vec<FileHash>,
}

impl Default for ShieldState {
    fn default() -> Self {
        Self {
            active: false,
            snapshot_count: 0,
            last_scan: "never".into(),
            last_scan_files: 0,
            last_scan_modified: 0,
            last_scan_added: 0,
            last_scan_removed: 0,
            baseline_hashes: Vec::new(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct ScanResult {
    total_files: usize,
    modified: Vec<String>,
    added: Vec<String>,
    removed: Vec<String>,
    timestamp: String,
}

// CLI
#[derive(Parser)]
#[command(name = "synthshield", about = "SynthShield - File Integrity & Snapshot Manager")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Status,
    Scan,
    Baseline,
    Rollback {
        #[arg(long)]
        snapshot: String,
    },
    Snapshots,
    Diff {
        #[arg(long)]
        file: Option<String>,
    },
    Protect {
        #[arg(long)]
        path: String,
    },
    Verify {
        #[arg(long)]
        path: String,
    },
}

// Helpers
fn now() -> String {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn ensure_dir(path: &str) -> Result<()> {
    let p = PathBuf::from(path);
    if !p.exists() {
        fs::create_dir_all(&p)?;
        fs::set_permissions(&p, fs::Permissions::from_mode(0o700))?;
    }
    Ok(())
}

fn write_secure(path: &str, data: &[u8]) -> Result<()> {
    let p = PathBuf::from(path);
    if let Some(par) = p.parent() {
        ensure_dir(par.to_str().unwrap_or("/tmp"))?;
    }
    fs::write(&p, data)?;
    fs::set_permissions(&p, fs::Permissions::from_mode(0o600))?;
    Ok(())
}

fn load_state() -> Result<ShieldState> {
    let p = PathBuf::from(STATE_FILE);
    if !p.exists() { return Ok(ShieldState::default()); }
    let data = fs::read_to_string(&p)?;
    Ok(serde_json::from_str(&data)?)
}

fn save_state(s: &ShieldState) -> Result<()> {
    let json = serde_json::to_string_pretty(s)?;
    write_secure(STATE_FILE, json.as_bytes())
}

fn hash_file_contents(path: &str) -> Result<String> {
    let data = fs::read(path)
        .with_context(|| format!("Failed to read {}", path))?;
    let mut hasher = Sha256::new();
    hasher.update(&data);
    Ok(hex::encode(hasher.finalize()))
}

/// Collect file metadata + content hash for a directory tree
fn collect_hashes(dirs: &[&str]) -> Result<Vec<FileHash>> {
    let mut hashes = Vec::new();
    for dir in dirs {
        let pb = PathBuf::from(dir);
        if !pb.exists() { continue; }
        for entry in WalkDir::new(dir)
            .follow_links(false)
            .max_depth(6)
            .into_iter()
            .flatten()
        {
            let p = entry.path();
            if !p.is_file() { continue; }
            if hashes.len() >= MAX_HASHES { break; }
            // Skip files that are too large (>100MB)
            if let Ok(meta) = fs::metadata(p) {
                if meta.len() > 100 * 1024 * 1024 { continue; }
                if let Ok(sha) = hash_file_contents(p.to_str().unwrap_or("")) {
                    let mtime = meta.modified().ok()
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0);
                    hashes.push(FileHash {
                        path: p.to_string_lossy().into_owned(),
                        sha256: sha,
                        size: meta.len(),
                        mode: meta.permissions().mode(),
                        uid: 0,
                        gid: 0,
                        mtime_secs: mtime,
                    });
                }
            }
        }
    }
    Ok(hashes)
}

fn cmd_status() -> Result<()> {
    let s = load_state()?;
    let snapper = Command::new("snapper").arg("--version").output().map(|o| o.status.success()).unwrap_or(false);
    println!("\n  \x1b[93m=== SynthShield -- File Integrity ===\x1b[0m\n");
    let sc = if s.active { "\x1b[92mACTIVE" } else { "\x1b[91mINACTIVE" };
    println!("  Service:     {} \x1b[0m", sc);
    println!("  Snapshots:   {}", s.snapshot_count);
    println!("  Last scan:   {}", s.last_scan);
    println!("  Files:       {} in baseline", s.baseline_hashes.len());
    println!("  Last diff:   +{} added, ~{} modified, -{} removed", s.last_scan_added, s.last_scan_modified, s.last_scan_removed);
    let sn = if snapper { "\x1b[92minstalled" } else { "\x1b[93mnot found" };
    println!("  snapper:     {} \x1b[0m", sn);
    println!("  State:       {}", STATE_FILE);
    println!();
    Ok(())
}

fn cmd_baseline() -> Result<()> {
    println!("  \x1b[93mRecording baseline (SHA-256 content hash)...\x1b[0m");
    let mut state = load_state()?;
    let hashes = collect_hashes(MONITORED_DIRS)?;
    state.baseline_hashes = hashes;
    state.last_scan = now();
    state.active = true;
    save_state(&state)?;
    println!("  \x1b[92m+ Baseline recorded: {} files.\x1b[0m\n", state.baseline_hashes.len());
    Ok(())
}

fn cmd_scan() -> Result<()> {
    let mut state = load_state()?;
    if state.baseline_hashes.is_empty() {
        println!("  \x1b[33mNo baseline recorded. Running baseline first...\x1b[0m");
        let hashes = collect_hashes(MONITORED_DIRS)?;
        state.baseline_hashes = hashes;
        state.active = true;
    }
    println!("  \x1b[93mScanning filesystem (SHA-256 content comparison)...\x1b[0m");
    // Build lookup from baseline
    let baseline_map: HashMap<String, &FileHash> = state.baseline_hashes.iter()
        .map(|h| (h.path.clone(), h))
        .collect();
    // Scan current state
    let current = collect_hashes(MONITORED_DIRS)?;
    let current_map: HashMap<String, &FileHash> = current.iter()
        .map(|h| (h.path.clone(), h))
        .collect();
    let mut modified = Vec::new();
    let mut added = Vec::new();
    let mut removed = Vec::new();
    // Check for modified and added
    for (path, cur) in &current_map {
        match baseline_map.get(path) {
            Some(base) => {
                // Compare actual content hash, not just metadata
                if base.sha256 != cur.sha256 {
                    modified.push(path.clone());
                }
            }
            None => {
                added.push(path.clone());
            }
        }
    }
    // Check for removed
    for path in baseline_map.keys() {
        if !current_map.contains_key(path) {
            removed.push(path.clone());
        }
    }
    let total = current.len();
    state.last_scan = now();
    state.last_scan_files = total;
    state.last_scan_modified = modified.len();
    state.last_scan_added = added.len();
    state.last_scan_removed = removed.len();
    save_state(&state)?;
    if modified.is_empty() && added.is_empty() && removed.is_empty() {
        println!("  \x1b[92mAll {} files match baseline.\x1b[0m\n", total);
    } else {
        println!("  \x1b[91mIntegrity issues found:\x1b[0m");
        if !modified.is_empty() {
            println!("  \x1b[91m  ~ {} MODIFIED:\x1b[0m", modified.len());
            for p in modified.iter().take(20) { println!("      {}", p); }
            if modified.len() > 20 { println!("      ... and {} more", modified.len()-20); }
        }
        if !added.is_empty() {
            println!("  \x1b[93m  + {} ADDED:\x1b[0m", added.len());
            for p in added.iter().take(20) { println!("      {}", p); }
            if added.len() > 20 { println!("      ... and {} more", added.len()-20); }
        }
        if !removed.is_empty() {
            println!("  \x1b[91m  - {} REMOVED:\x1b[0m", removed.len());
            for p in removed.iter().take(20) { println!("      {}", p); }
            if removed.len() > 20 { println!("      ... and {} more", removed.len()-20); }
        }
        println!();
    }
    Ok(())
}

fn cmd_rollback(id: &str) -> Result<()> {
    println!("  \x1b[93mRollback to snapshot '{}'...\x1b[0m", id);
    let status = Command::new("snapper")
        .args(["--config", "root", "undochange", &format!("{}..0", id)])
        .status();
    match status {
        Ok(s) if s.success() => println!("  \x1b[92mRollback complete.\x1b[0m"),
        _ => println!("  \x1b[91mRollback failed (is snapper/BTRFS configured?)\x1b[0m"),
    }
    println!();
    Ok(())
}

fn cmd_snapshots() -> Result<()> {
    println!("  \x1b[93mSnapshots:\x1b[0m\n");
    match Command::new("snapper").args(["--config", "root", "list"]).output() {
        Ok(o) => {
            let out = String::from_utf8_lossy(&o.stdout);
            if out.trim().is_empty() { println!("  (no snapshots)"); } else { println!("{}", out); }
        }
        Err(_) => println!("  \x1b[33msnapper not available (BTRFS may not be in use)\x1b[0m"),
    }
    println!();
    Ok(())
}

fn cmd_verify(path: &str) -> Result<()> {
    let state = load_state()?;
    let current_hash = hash_file_contents(path)?;
    let base = state.baseline_hashes.iter().find(|h| h.path == path);
    match base {
        Some(b) if b.sha256 == current_hash => {
            println!("  \x1b[92m[OK] {} -- matches baseline\x1b[0m", path);
        }
        Some(b) => {
            println!("  \x1b[91m[TAMPERED] {}\x1b[0m", path);
            println!("    baseline: {}...", &b.sha256[..32]);
            println!("    current:  {}...", &current_hash[..32]);
        }
        None => {
            println!("  \x1b[93m[NOT IN BASELINE] {}\x1b[0m", path);
        }
    }
    println!();
    Ok(())
}

fn cmd_diff(_file: &Option<String>) -> Result<()> {
    let state = load_state()?;
    if state.last_scan_modified == 0 && state.last_scan_added == 0 && state.last_scan_removed == 0 {
        println!("  \x1b[93mNo changes detected in last scan.\x1b[0m");
        return Ok(());
    }
    println!("  \x1b[96mLast scan results:\x1b[0m\n");
    println!("  Modified: {} files", state.last_scan_modified);
    println!("  Added:    {} files", state.last_scan_added);
    println!("  Removed:  {} files", state.last_scan_removed);
    println!();
    Ok(())
}

fn cmd_protect(path: &str) -> Result<()> {
    let pb = PathBuf::from(path);
    if !pb.exists() { anyhow::bail!("Path does not exist: {}", path); }
    let mut state = load_state()?;
    if let Ok(sha) = hash_file_contents(path) {
        if let Ok(meta) = fs::metadata(path) {
            state.baseline_hashes.retain(|h| h.path != path);
            state.baseline_hashes.push(FileHash {
                path: path.into(),
                sha256: sha,
                size: meta.len(),
                mode: meta.permissions().mode(),
                uid: 0, gid: 0,
                mtime_secs: meta.modified().ok().and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok()).map(|d| d.as_secs()).unwrap_or(0),
            });
            save_state(&state)?;
            println!("  \x1b[92m+ Now protecting: {}\x1b[0m\n", path);
        }
    }
    Ok(())
}

fn main() -> Result<()> {
    ensure_dir("/var/lib/synthshield")?;
    ensure_dir(BASELINE_DIR)?;
    match Cli::parse().command {
        Commands::Status => cmd_status(),
        Commands::Scan => cmd_scan(),
        Commands::Baseline => cmd_baseline(),
        Commands::Rollback { snapshot } => cmd_rollback(&snapshot),
        Commands::Snapshots => cmd_snapshots(),
        Commands::Diff { file } => cmd_diff(&file),
        Commands::Protect { path } => cmd_protect(&path),
        Commands::Verify { path } => cmd_verify(&path),
    }
}
