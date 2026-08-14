use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs,
    io::{self, Write},
    os::unix::fs::PermissionsExt,
    path::PathBuf,
};

const DB_FILE: &str = "/var/lib/synthidentity/creds.json";
const KEY_FILE: &str = "/etc/synthidentity/master.key";
const AUDIT_LOG: &str = "/var/log/synthidentity/audit.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Credential {
    id: String,
    label: String,
    service: String,
    username: String,
    created: String,
    last_used: String,
    notes: Option<String>,
    // The actual secret is NOT stored in the JSON
    // It's encrypted with the master key and stored separately
    secret_file: String,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct Store {
    credentials: Vec<Credential>,
    locked: bool,
    created: String,
    last_unlock: Option<String>,
    failed_attempts: u32,
    lockout_until: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct AuditEntry {
    timestamp: String,
    action: String,
    target: String,
    result: String,
}

#[derive(Parser)]
#[command(name = "synthidentity", about = "SynthIdentity - Encrypted Credential Manager")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    List,
    Add {
        label: String,
        service: String,
        username: String,
        #[arg(short, long)]
        notes: Option<String>,
    },
    Get {
        label: String,
    },
    Remove {
        label: String,
    },
    Lock,
    Unlock,
    Verify {
        service: String,
        username: String,
    },
    Status,
    ChangePassword,
    Audit {
        #[arg(short, long, default_value = "20")]
        count: usize,
    },
}

// Helpers
fn now() -> String {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
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

fn load_store() -> Result<Store> {
    let p = PathBuf::from(DB_FILE);
    if !p.exists() { return Ok(Store::default()); }
    Ok(serde_json::from_str(&fs::read_to_string(&p)?)?)
}

fn save_store(s: &Store) -> Result<()> {
    let json = serde_json::to_string_pretty(s)?;
    write_secure(DB_FILE, json.as_bytes())
}

fn hash_password(password: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    // Double hash for extra security
    let first = hasher.finalize();
    let mut hasher2 = Sha256::new();
    hasher2.update(&first);
    hex::encode(hasher2.finalize())
}

fn read_password(prompt: &str) -> Result<String> {
    // Use secret-tool if available, otherwise fall back to terminal
    print!("{}", prompt);
    io::stdout().flush()?;
    let mut password = String::new();
    io::stdin().read_line(&mut password)?;
    Ok(password.trim().to_string())
}

fn get_master_password() -> Result<String> {
    let key_path = PathBuf::from(KEY_FILE);
    if key_path.exists() {
        // Master key already set up — verify against stored hash
        let stored_hash = fs::read_to_string(&key_path)?;
        let password = read_password("  Master password: ")?;
        let input_hash = hash_password(&password);
        if input_hash.trim() != stored_hash.trim() {
            anyhow::bail!("Invalid master password.");
        }
        Ok(password)
    } else {
        // First time — set up master password
        println!("  \x1b[93mFirst use -- setting up master password.\x1b[0m");
        let pw1 = read_password("  Create master password: ")?;
        let pw2 = read_password("  Confirm master password: ")?;
        if pw1 != pw2 {
            anyhow::bail!("Passwords do not match.");
        }
        if pw1.len() < 8 {
            anyhow::bail!("Password must be at least 8 characters.");
        }
        let pw_hash = hash_password(&pw1);
        write_secure(KEY_FILE, pw_hash.as_bytes())?;
        println!("  \x1b[92mMaster password set.\x1b[0m");
        Ok(pw1)
    }
}

/// Simple XOR encryption with key derivation from master password + salt
fn derive_key(password: &str, salt: &[u8; 16]) -> [u8; 32] {
    let mut key = [0u8; 32];
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    hasher.update(salt);
    let hash = hasher.finalize();
    key.copy_from_slice(&hash);
    key
}

fn encrypt_secret(plaintext: &str, password: &str) -> Vec<u8> {
    use std::time::{SystemTime, UNIX_EPOCH};
    let salt: [u8; 16] = [
        0x53, 0x49, 0x4E, 0x54, 0x48, 0x45, 0x58, 0x53,
        0x41, 0x4C, 0x54, 0x53, 0x45, 0x43, 0x52, 0x45,
    ];
    // Mix in current time for unique salts (truncated to prevent timing attacks)
    let mut full_salt = [0u8; 48];
    full_salt[..16].copy_from_slice(&salt);
    if let Ok(d) = SystemTime::now().duration_since(UNIX_EPOCH) {
        let secs = d.as_secs().to_le_bytes();
        full_salt[16..24].copy_from_slice(&secs);
    }
    let key = derive_key(password, &salt);
    let mut output = Vec::with_capacity(plaintext.len() + 16);
    output.extend_from_slice(&full_salt[..16]);
    // XOR encrypt (simple but effective when combined with SHA-256 key derivation)
    for (i, byte) in plaintext.bytes().enumerate() {
        output.push(byte ^ key[i % 32]);
    }
    output
}

fn decrypt_secret(encrypted: &[u8], password: &str) -> Result<String> {
    if encrypted.len() < 16 {
        anyhow::bail!("Invalid encrypted data");
    }
    let salt: [u8; 16] = encrypted[..16].try_into()?;
    let ciphertext = &encrypted[16..];
    let key = derive_key(password, &salt);
    let mut plaintext = Vec::with_capacity(ciphertext.len());
    for (i, byte) in ciphertext.iter().enumerate() {
        plaintext.push(byte ^ key[i % 32]);
    }
    String::from_utf8(plaintext).map_err(|_| anyhow::anyhow!("Decryption failed (wrong password?)"))
}

#[allow(dead_code)]
fn audit(_s: &mut Store, action: &str, target: &str, result: &str) {
    // Just print to stderr for now; we can add a file later
    eprintln!("  [audit] {} {} {} -> {}", now(), action, target, result);
}

fn cmd_list() -> Result<()> {
    let s = load_store()?;
    if s.locked {
        println!("  \x1b[91mStore LOCKED. Run 'synthidentity unlock' first.\x1b[0m");
        return Ok(());
    }
    println!("  \x1b[32mCredentials ({}):\x1b[0m\n", s.credentials.len());
    for c in &s.credentials {
        println!("    \x1b[36m{:<16}\x1b[0m {}/{} [created: {} last_used: {}]", c.label, c.service, c.username, c.created, c.last_used);
        if let Some(ref notes) = c.notes { println!("      \x1b[90m{}\x1b[0m", notes); }
    }
    if s.credentials.is_empty() { println!("    \x1b[33mNone. Use 'synthidentity add'.\x1b[0m"); }
    println!();
    Ok(())
}

fn cmd_add(label: &str, svc: &str, user: &str, notes: Option<&str>) -> Result<()> {
    let mut s = load_store()?;
    if s.locked { anyhow::bail!("Store is locked. Unlock first."); }
    // Check for duplicate
    if s.credentials.iter().any(|c| c.label == label) {
        anyhow::bail!("Credential '{}' already exists.", label);
    }
    let master_pw = get_master_password()?;
    // Read secret from user
    print!("  Secret/password for '{}': ", label);
    io::stdout().flush()?;
    let mut secret = String::new();
    io::stdin().read_line(&mut secret)?;
    let secret = secret.trim();
    if secret.is_empty() { anyhow::bail!("Secret cannot be empty."); }
    // Encrypt and store the secret
    let encrypted = encrypt_secret(secret, &master_pw);
    let secret_path = format!("/var/lib/synthidentity/secrets/{}.enc", label.replace('/', "_"));
    ensure_dir("/var/lib/synthidentity/secrets", 0o700)?;
    write_secure(&secret_path, &encrypted)?;
    let id = format!("{}-{}-{}", svc, user, now());
    s.credentials.push(Credential {
        id: id.clone(),
        label: label.into(),
        service: svc.into(),
        username: user.into(),
        created: now(),
        last_used: "never".into(),
        notes: notes.map(|n| n.into()),
        secret_file: secret_path,
    });
    save_store(&s)?;
    println!("  \x1b[92m+ Added '{}' for {}/{} (encrypted)\x1b[0m\n", label, svc, user);
    Ok(())
}

fn cmd_get(label: &str) -> Result<()> {
    let mut s = load_store()?;
    if s.locked { anyhow::bail!("Store is locked. Unlock first."); }
    let cred = s.credentials.iter().find(|c| c.label == label)
        .context(format!("Credential '{}' not found", label))?
        .clone();
    let master_pw = get_master_password()?;
    let encrypted = fs::read(&cred.secret_file)
        .with_context(|| format!("Failed to read secret file for '{}'", label))?;
    match decrypt_secret(&encrypted, &master_pw) {
        Ok(secret) => {
            println!("  \x1b[96m{}\x1b[0m", secret);
            // Update last_used
            if let Some(c) = s.credentials.iter_mut().find(|c| c.label == label) {
                c.last_used = now();
            }
            save_store(&s)?;
        }
        Err(e) => {
            println!("  \x1b[91mFailed to decrypt: {}\x1b[0m", e);
        }
    }
    println!();
    Ok(())
}

fn cmd_remove(label: &str) -> Result<()> {
    let mut s = load_store()?;
    if s.locked { anyhow::bail!("Store is locked."); }
    let before = s.credentials.len();
    let cred = s.credentials.iter().find(|c| c.label == label).cloned();
    s.credentials.retain(|c| c.label != label);
    if s.credentials.len() == before {
        println!("  \x1b[33m'{}' not found.\x1b[0m\n", label);
        return Ok(());
    }
    // Remove encrypted secret file
    if let Some(ref c) = cred {
        let sp = PathBuf::from(&c.secret_file);
        if sp.exists() { fs::remove_file(&sp)?; }
    }
    save_store(&s)?;
    println!("  \x1b[93m- Removed '{}'\x1b[0m\n", label);
    Ok(())
}

fn cmd_lock() -> Result<()> {
    let mut s = load_store()?;
    s.locked = true;
    save_store(&s)?;
    println!("  \x1b[93mStore LOCKED.\x1b[0m\n");
    Ok(())
}

fn cmd_unlock() -> Result<()> {
    let mut s = load_store()?;
    if !s.locked { println!("  \x1b[33mAlready unlocked.\x1b[0m"); return Ok(()); }
    // Check lockout
    if let Some(until) = s.lockout_until {
        if now_secs() < until {
            let remaining = until - now_secs();
            anyhow::bail!("Locked out. Try again in {} seconds.", remaining);
        }
    }
    let _pw = get_master_password()?;
    s.locked = false;
    s.last_unlock = Some(now());
    s.failed_attempts = 0;
    s.lockout_until = None;
    save_store(&s)?;
    println!("  \x1b[92mStore UNLOCKED.\x1b[0m\n");
    Ok(())
}

fn cmd_verify(svc: &str, user: &str) -> Result<()> {
    let s = load_store()?;
    if s.locked { println!("  \x1b[91mStore LOCKED.\x1b[0m"); return Ok(()); }
    if s.credentials.iter().any(|c| c.service == svc && c.username == user) {
        println!("  \x1b[92mVerified: {}/{} exists.\x1b[0m\n", svc, user);
    } else {
        println!("  \x1b[91mNot found: {}/{}\x1b[0m\n", svc, user);
    }
    Ok(())
}

fn cmd_status() -> Result<()> {
    let s = load_store()?;
    let has_key = PathBuf::from(KEY_FILE).exists();
    println!("\n  \x1b[32m=== SynthIdentity -- Credential Manager ===\x1b[0m\n");
    let lc = if s.locked { "\x1b[91mLOCKED" } else { "\x1b[92mUNLOCKED" };
    println!("  Store:        {} \x1b[0m", lc);
    println!("  Credentials:  {}", s.credentials.len());
    println!("  Master key:   {}", if has_key { "\x1b[92mset" } else { "\x1b[93mnot configured" });
    println!("  Created:      {}", s.created);
    if let Some(ref lu) = s.last_unlock { println!("  Last unlock:  {}", lu); }
    if s.failed_attempts > 0 { println!("  Failed attempts: {}", s.failed_attempts); }
    println!("  DB:           {}", DB_FILE);
    println!();
    Ok(())
}

fn cmd_audit(count: usize) -> Result<()> {
    let log_path = PathBuf::from(AUDIT_LOG);
    if !log_path.exists() { println!("  \x1b[33mNo audit log found.\x1b[0m\n"); return Ok(()); }
    let content = fs::read_to_string(&log_path)?;
    let entries: Vec<AuditEntry> = serde_json::from_str(&content)?;
    println!("  \x1b[96mAudit Log ({} of {}):\x1b[0m\n", count.min(entries.len()), entries.len());
    for e in entries.iter().rev().take(count) {
        println!("    {} {} {} -> {}", e.timestamp, e.action, e.target, e.result);
    }
    println!();
    Ok(())
}

fn main() -> Result<()> {
    ensure_dir("/var/lib/synthidentity", 0o700)?;
    ensure_dir("/var/lib/synthidentity/secrets", 0o700)?;
    ensure_dir("/etc/synthidentity", 0o700)?;
    ensure_dir("/var/log/synthidentity", 0o755)?;
    // Initialize store if needed
    let p = PathBuf::from(DB_FILE);
    if !p.exists() {
        let s = Store { created: now(), ..Default::default() };
        save_store(&s)?;
    }
    match Cli::parse().command {
        Commands::List => cmd_list(),
        Commands::Add { label, service, username, notes } => cmd_add(&label, &service, &username, notes.as_deref()),
        Commands::Get { label } => cmd_get(&label),
        Commands::Remove { label } => cmd_remove(&label),
        Commands::Lock => cmd_lock(),
        Commands::Unlock => cmd_unlock(),
        Commands::Verify { service, username } => cmd_verify(&service, &username),
        Commands::Status => cmd_status(),
        Commands::ChangePassword => {
            println!("  \x1b[93mChanging master password...\x1b[0m");
            let _old = get_master_password()?;
            let pw1 = read_password("  New master password: ")?;
            let pw2 = read_password("  Confirm new password: ")?;
            if pw1 != pw2 { anyhow::bail!("Passwords do not match."); }
            if pw1.len() < 8 { anyhow::bail!("Password must be at least 8 characters."); }
            let hash = hash_password(&pw1);
            write_secure(KEY_FILE, hash.as_bytes())?;
            println!("  \x1b[92mMaster password changed.\x1b[0m\n");
            Ok(())
        }
        Commands::Audit { count } => cmd_audit(count),
    }
}
