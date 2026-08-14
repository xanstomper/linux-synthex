use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use sha2::Digest;
use std::{
    fs,
    os::unix::fs::PermissionsExt,
    path::PathBuf,
    process::{Command, Stdio},
};

const CFG_FILE: &str = "/etc/synthvault/volumes.json";
const KEY_DIR: &str = "/etc/synthvault/keys";
#[allow(dead_code)]
const AUDIT_LOG: &str = "/var/log/synthvault/audit.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Volume {
    name: String,
    device: String,
    mount: String,
    tpm: bool,
    created: String,
    mapper_name: String,
    size_hint: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct KeySlot {
    slot: u32,
    label: String,
    added: String,
    fingerprint: String,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct VaultState {
    volumes: Vec<Volume>,
    keys: Vec<KeySlot>,
    audit_trail: Vec<AuditEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct AuditEntry {
    timestamp: String,
    action: String,
    target: String,
    result: String,
    user: String,
}

#[derive(Parser)]
#[command(name = "synthvault", about = "SynthVault - Secure Storage Manager")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Init {
        name: String,
        device: String,
        mount_point: String,
        #[arg(long)] tpm: bool,
    },
    Mount { name: String },
    Unmount { name: String },
    Encrypt {
        #[arg(long)] dir: String,
        #[arg(long)] output: Option<String>,
    },
    Decrypt {
        #[arg(long)] file: String,
        #[arg(long)] output: Option<String>,
    },
    Status,
    Keys {
        #[command(subcommand)]
        action: KeyAction,
    },
    Audit {
        #[arg(short, long, default_value = "20")]
        count: usize,
    },
    Lockdown,
}

#[derive(Subcommand)]
enum KeyAction {
    List,
    Add {
        slot: u32,
        keyfile: String,
        #[arg(long)]
        label: Option<String>,
    },
    Remove {
        slot: u32,
    },
    Verify {
        slot: u32,
        keyfile: String,
    },
}

// Helpers
fn now() -> String {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn current_user() -> String {
    std::env::var("USER").unwrap_or_else(|_| "unknown".into())
}

fn ensure_dir(path: &str, mode: u32) -> Result<()> {
    let p = PathBuf::from(path);
    if !p.exists() {
        fs::create_dir_all(&p)?;
        fs::set_permissions(&p, fs::Permissions::from_mode(mode))?;
    }
    Ok(())
}

fn write_secure(path: &str, data: &[u8]) -> Result<()> {
    let p = PathBuf::from(path);
    if let Some(par) = p.parent() {
        ensure_dir(par.to_str().unwrap_or("/tmp"), 0o700)?;
    }
    fs::write(&p, data)?;
    fs::set_permissions(&p, fs::Permissions::from_mode(0o600))?;
    Ok(())
}

fn load_state() -> Result<VaultState> {
    let p = PathBuf::from(CFG_FILE);
    if !p.exists() { return Ok(VaultState::default()); }
    Ok(serde_json::from_str(&fs::read_to_string(&p)?)?)
}

fn save_state(s: &VaultState) -> Result<()> {
    let json = serde_json::to_string_pretty(s)?;
    write_secure(CFG_FILE, json.as_bytes())
}

fn audit(s: &mut VaultState, action: &str, target: &str, result: &str) {
    s.audit_trail.push(AuditEntry {
        timestamp: now(),
        action: action.into(),
        target: target.into(),
        result: result.into(),
        user: current_user(),
    });
    // Cap audit trail at 1000 entries
    let len = s.audit_trail.len();
    if len > 1000 { s.audit_trail.drain(..len - 1000); }
}

fn cmd_init(name: &str, dev: &str, mount: &str, tpm: bool) -> Result<()> {
    let mut s = load_state()?;
    if s.volumes.iter().any(|v| v.name == name) {
        anyhow::bail!("Volume '{}' already exists", name);
    }
    // Validate device path
    if !dev.starts_with("/dev/") {
        anyhow::bail!("Invalid device path: must start with /dev/"
        );
    }
    let devpb = PathBuf::from(dev);
    if !devpb.exists() {
        anyhow::bail!("Device {} does not exist", dev);
    }
    println!("  \x1b[35mInitializing LUKS2 volume '{}' on {} -> {}\x1b[0m", name, dev, mount);
    println!("  \x1b[93mWARNING: This will ERASE all data on {}\x1b[0m", dev);
    let status = Command::new("cryptsetup")
        .args(["luksFormat", "--type", "luks2", "--batch-mode", dev])
        .status()
        .context("Failed to run cryptsetup luksFormat")?;
    if !status.success() {
        anyhow::bail!("cryptsetup luksFormat failed with status: {}", status);
    }
    if tpm {
        println!("  \x1b[93mEnrolling TPM2 key...\x1b[0m");
        let tpm_status = Command::new("systemd-cryptenroll")
            .args(["--tpm2-device=auto", dev])
            .status();
        match tpm_status {
            Ok(s) if s.success() => println!("  \x1b[92mTPM2 enrolled.\x1b[0m"),
            _ => println!("  \x1b[93mTPM2 enrollment failed (continuing without TPM)\x1b[0m"),
        }
    }
    let mapper = format!("sv-{}", name);
    s.volumes.push(Volume {
        name: name.into(),
        device: dev.into(),
        mount: mount.into(),
        tpm,
        created: now(),
        mapper_name: mapper,
        size_hint: None,
    });
    audit(&mut s, "init", name, "success");
    save_state(&s)?;
    println!("  \x1b[92mVolume '{}' initialized.\x1b[0m\n", name);
    Ok(())
}

fn cmd_mount(name: &str) -> Result<()> {
    let mut state = load_state()?;
    let vol = state.volumes.iter().find(|v| v.name == name)
        .context(format!("Volume '{}' not found", name))?
        .clone();
    fs::create_dir_all(&vol.mount)?;
    let devmapper = format!("/dev/mapper/{}", vol.mapper_name);
    let open_status = if vol.tpm {
        Command::new("systemd-cryptsetup").args(["attach", &vol.mapper_name, &vol.device]).status()
    } else {
        Command::new("cryptsetup").args(["open", &vol.device, &vol.mapper_name]).status()
    };
    match open_status {
        Ok(o) if o.success() => {}
        _ => anyhow::bail!("Failed to open encrypted volume '{}'", name),
    }
    let mount_status = Command::new("mount").args([&devmapper, &vol.mount]).status();
    match mount_status {
        Ok(m) if m.success() => {
            audit(&mut state, "mount", name, "success");
            save_state(&state)?;
            println!("  \x1b[92mMounted '{}' at {}\x1b[0m\n", name, vol.mount);
        }
        _ => {
            audit(&mut state, "mount", name, "mount_failed");
            save_state(&state)?;
            anyhow::bail!("Failed to mount {} at {}", devmapper, vol.mount);
        }
    }
    Ok(())
}

fn cmd_unmount(name: &str) -> Result<()> {
    let mut state = load_state()?;
    let vol = state.volumes.iter().find(|v| v.name == name)
        .context(format!("Volume '{}' not found", name))?
        .clone();
    let umount = Command::new("umount").args([&vol.mount]).status();
    match umount {
        Ok(st) if st.success() => {
            let close = Command::new("cryptsetup").args(["close", &vol.mapper_name]).status();
            match close {
                Ok(_c) if _c.success() => {
                    audit(&mut state, "unmount", name, "success");
                    save_state(&state)?;
                    println!("  \x1b[92mUnmounted '{}'.\x1b[0m\n", name);
                }
                _ => {
                    println!("  \x1b[93mUnmounted but mapper close failed.\x1b[0m\n");
                    audit(&mut state, "unmount", name, "close_failed");
                    save_state(&state)?;
                }
            }
        }
        _ => anyhow::bail!("Failed to unmount {}", vol.mount),
    }
    Ok(())
}

fn cmd_encrypt(dir: &str, out: Option<&str>) -> Result<()> {
    let p = PathBuf::from(dir);
    if !p.exists() { anyhow::bail!("Directory '{}' does not exist", dir); }
    let default_out = format!("{}.enc", dir);
    let output = out.unwrap_or(&default_out);
    println!("  \x1b[35mEncrypting '{}' -> '{}'\x1b[0m", dir, output);
    let tar = Command::new("tar")
        .args(["-cf", "-", dir])
        .stdout(Stdio::piped())
        .spawn()
        .context("Failed to start tar")?;
    let tar_stdout = tar.stdout.context("Failed to capture tar stdout")?;
    let gpg_status = Command::new("gpg")
        .args(["--symmetric", "--cipher-algo", "AES256", "--output", output])
        .stdin(Stdio::from(tar_stdout))
        .status()
        .context("Failed to run gpg")?;
    if !gpg_status.success() {
        anyhow::bail!("gpg encryption failed");
    }
    println!("  \x1b[92mEncrypted -> {}\x1b[0m\n", output);
    Ok(())
}

fn cmd_decrypt(file: &str, out: Option<&str>) -> Result<()> {
    let p = PathBuf::from(file);
    if !p.exists() { anyhow::bail!("File '{}' does not exist", file); }
    let output = out.unwrap_or(".");
    println!("  \x1b[35mDecrypting '{}' -> '{}'\x1b[0m", file, output);
    let gpg = Command::new("gpg")
        .args(["--decrypt", "--output", "-", file])
        .stdout(Stdio::piped())
        .spawn()
        .context("Failed to run gpg decrypt")?;
    let tar_status = Command::new("tar")
        .args(["-xf", "-", "-C", output])
        .stdin(Stdio::from(gpg.stdout.context("Failed to capture gpg stdout")?))
        .status()
        .context("Failed to extract")?;
    if tar_status.success() {
        println!("  \x1b[92mDecrypted -> {}\x1b[0m\n", output);
    } else {
        anyhow::bail!("Decryption/extraction failed");
    }
    Ok(())
}

fn cmd_status() -> Result<()> {
    let s = load_state()?;
    println!("\n  \x1b[35m=== SynthVault -- Secure Storage ===\x1b[0m\n");
    if s.volumes.is_empty() {
        println!("  \x1b[33mNo volumes configured. Use 'synthvault init' to create one.\x1b[0m");
    } else {
        for vol in &s.volumes {
            let mounted = PathBuf::from(&vol.mount).exists()
                && Command::new("mountpoint").arg(&vol.mount).output()
                    .map(|o| o.status.success()).unwrap_or(false);
            let mc = if mounted { "\x1b[92mmounted" } else { "\x1b[91munmounted" };
            println!("  \x1b[36m{:<16}\x1b[0m {} -> {} [{}] tpm={}",
                vol.name, vol.device, vol.mount, mc, vol.tpm);
        }
    }
    println!("\n  \x1b[96mKey Slots:\x1b[0m");
    if s.keys.is_empty() {
        println!("    (none)");
    } else {
        for k in &s.keys {
            println!("    Slot {} - {} (added: {})", k.slot, k.label, k.added);
        }
    }
    println!("\n  Audit entries: {}", s.audit_trail.len());
    println!("  Key dir: {}\n", KEY_DIR);
    Ok(())
}

fn cmd_keys_add(slot: u32, keyfile: &str, label: Option<&str>) -> Result<()> {
    let kf = PathBuf::from(keyfile);
    if !kf.exists() { anyhow::bail!("Key file '{}' does not exist", keyfile); }
    ensure_dir(KEY_DIR, 0o700)?;
    // Copy keyfile with strict permissions
    let dest = PathBuf::from(KEY_DIR).join(format!("slot{}.key", slot));
    fs::copy(&kf, &dest)?;
    fs::set_permissions(&dest, fs::Permissions::from_mode(0o600))?;
    let mut s = load_state()?;
    // Remove existing entry for this slot
    s.keys.retain(|k| k.slot != slot);
    let fingerprint = {
        let data = fs::read(&kf)?;
        let mut hasher = sha2::Sha256::new();
        hasher.update(&data);
        hex::encode(hasher.finalize())
    };
    s.keys.push(KeySlot {
        slot,
        label: label.unwrap_or(&format!("key-{}", slot)).into(),
        added: now(),
        fingerprint: fingerprint[..16].into(),
    });
    audit(&mut s, "key-add", &format!("slot{}", slot), "success");
    save_state(&s)?;
    println!("  \x1b[92m+ Key slot {} added.\x1b[0m\n", slot);
    Ok(())
}

fn cmd_keys_remove(slot: u32) -> Result<()> {
    let mut s = load_state()?;
    let before = s.keys.len();
    s.keys.retain(|k| k.slot != slot);
    if s.keys.len() == before {
        println!("  \x1b[33mKey slot {} not found.\x1b[0m\n", slot);
        return Ok(());
    }
    let keyfile = PathBuf::from(KEY_DIR).join(format!("slot{}.key", slot));
    if keyfile.exists() {
        fs::remove_file(&keyfile)?;
    }
    audit(&mut s, "key-remove", &format!("slot{}", slot), "success");
    save_state(&s)?;
    println!("  \x1b[93m- Key slot {} removed.\x1b[0m\n", slot);
    Ok(())
}

fn cmd_keys_list() -> Result<()> {
    let kd = PathBuf::from(KEY_DIR);
    println!("  \x1b[96mKey Directory: {}\x1b[0m\n", KEY_DIR);
    if kd.exists() {
        let mut found = false;
        for e in fs::read_dir(&kd)?.flatten() {
            found = true;
            let meta = fs::metadata(e.path()).ok();
            println!("    {} [{} bytes]", e.file_name().to_string_lossy(),
                meta.as_ref().map(|m| m.len()).unwrap_or(0));
        }
        if !found { println!("    (empty)"); }
    } else {
        println!("    (directory does not exist)");
    }
    println!();
    Ok(())
}

fn cmd_keys_verify(slot: u32, keyfile: &str) -> Result<()> {
    let keyfile_path = PathBuf::from(KEY_DIR).join(format!("slot{}.key", slot));
    if !keyfile_path.exists() {
        println!("  \x1b[91mKey slot {} not found.\x1b[0m\n", slot);
        return Ok(());
    }
    let stored = fs::read(&keyfile_path)?;
    let provided = fs::read(keyfile)?;
    if stored == provided {
        println!("  \x1b[92mKey slot {} verified -- matches.\x1b[0m\n", slot);
    } else {
        println!("  \x1b[91mKey slot {} MISMATCH -- keyfile does not match stored key.\x1b[0m\n", slot);
    }
    Ok(())
}

fn cmd_audit(count: usize) -> Result<()> {
    let s = load_state()?;
    println!("  \x1b[96mAudit Trail ({} of {}):\x1b[0m\n", count.min(s.audit_trail.len()), s.audit_trail.len());
    for entry in s.audit_trail.iter().rev().take(count) {
        let rc = if entry.result == "success" { "\x1b[92m" } else { "\x1b[91m" };
        println!("    {} [{}] {} {} -> {}{}\x1b[0m", entry.timestamp, entry.user, entry.action, entry.target, rc, entry.result);
    }
    if s.audit_trail.is_empty() { println!("    (no entries)"); }
    println!();
    Ok(())
}

fn cmd_lockdown() -> Result<()> {
    println!("  \x1b[93mRunning security lockdown check...\x1b[0m\n");
    let s = load_state()?;
    let mut issues = 0;
    // Check key file permissions
    let kd = PathBuf::from(KEY_DIR);
    if kd.exists() {
        for e in fs::read_dir(&kd)?.flatten() {
            if let Ok(meta) = fs::metadata(e.path()) {
                let mode = meta.permissions().mode() & 0o7777;
                if mode != 0o600 {
                    println!("  \x1b[91m  [!!] {} has permissive mode {:o} (should be 600)\x1b[0m", e.path().display(), mode);
                    issues += 1;
                }
            }
        }
    }
    // Check config file permissions
    let cfg = PathBuf::from(CFG_FILE);
    if cfg.exists() {
        if let Ok(meta) = fs::metadata(&cfg) {
            let mode = meta.permissions().mode() & 0o7777;
            if mode != 0o600 {
                println!("  \x1b[91m  [!!] {} has permissive mode {:o}\x1b[0m", CFG_FILE, mode);
                issues += 1;
            }
        }
    }
    // Check for stale/unused key files
    let active_slots: Vec<u32> = s.keys.iter().map(|k| k.slot).collect();
    if kd.exists() {
        for e in fs::read_dir(&kd)?.flatten() {
            let name = e.file_name().to_string_lossy().to_string();
            if let Some(slot_str) = name.strip_prefix("slot").and_then(|s| s.strip_suffix(".key")) {
                if let Ok(slot) = slot_str.parse::<u32>() {
                    if !active_slots.contains(&slot) {
                        println!("  \x1b[93m  [!] Orphaned key file: {} (not in state)\x1b[0m", name);
                        issues += 1;
                    }
                }
            }
        }
    }
    if issues == 0 {
        println!("  \x1b[92mAll clear -- no security issues found.\x1b[0m");
    } else {
        println!("\n  \x1b[91m{} issues found.\x1b[0m", issues);
    }
    println!();
    Ok(())
}

fn main() -> Result<()> {
    ensure_dir("/var/log/synthvault", 0o755)?;
    ensure_dir(KEY_DIR, 0o700)?;
    match Cli::parse().command {
        Commands::Init { name, device, mount_point, tpm } => cmd_init(&name, &device, &mount_point, tpm),
        Commands::Mount { name } => cmd_mount(&name),
        Commands::Unmount { name } => cmd_unmount(&name),
        Commands::Encrypt { dir, output } => cmd_encrypt(&dir, output.as_deref()),
        Commands::Decrypt { file, output } => cmd_decrypt(&file, output.as_deref()),
        Commands::Status => cmd_status(),
        Commands::Keys { action } => match action {
            KeyAction::List => cmd_keys_list(),
            KeyAction::Add { slot, keyfile, label } => cmd_keys_add(slot, &keyfile, label.as_deref()),
            KeyAction::Remove { slot } => cmd_keys_remove(slot),
            KeyAction::Verify { slot, keyfile } => cmd_keys_verify(slot, &keyfile),
        },
        Commands::Audit { count } => cmd_audit(count),
        Commands::Lockdown => cmd_lockdown(),
    }
}
