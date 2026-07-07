use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    collections::HashSet,
    fs,
    io::{BufRead, BufReader},
    os::unix::fs::PermissionsExt,
    path::PathBuf,
    process::Command,
};

// Constants
const ALERTS_FILE: &str = "/var/log/synthguard/alerts.json";
const WHITELIST_FILE: &str = "/etc/synthguard/whitelist.json";
const INTEGRITY_DB: &str = "/var/lib/synthguard/integrity.json";
const MAX_ALERTS: usize = 10_000;

// Data types
#[derive(Debug, Clone, Serialize, Deserialize)]
struct Alert {
    id: u64,
    severity: String,
    category: String,
    message: String,
    pid: u32,
    exe: String,
    timestamp: String,
    details: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct Whitelist {
    binaries: Vec<String>,
    syscalls: Vec<String>,
    ports: Vec<u16>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct IntegrityEntry {
    path: String,
    sha256: String,
    size: u64,
    mode: u32,
    recorded_at: String,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct IntegrityDb {
    entries: Vec<IntegrityEntry>,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct KernelSecurityState {
    lockdown: String,
    kptr_restrict: u8,
    dmesg_restrict: u8,
    perf_paranoid: i8,
    unprivileged_bpf_disabled: u8,
    randomize_va_space: u8,
    yama_ptrace_scope: u8,
    modules_disabled: bool,
    secure_boot: bool,
    iommu_enabled: bool,
    smep_enabled: bool,
    smap_enabled: bool,
    kaiser_enabled: bool,
}

// CLI
#[derive(Parser)]
#[command(name = "synthguard", about = "SynthGuard - Kernel-Level Security Monitor")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Status,
    Alerts { #[arg(short, long, default_value = "20")] count: usize, #[arg(short, long)] severity: Option<String> },
    Whitelist { #[command(subcommand)] action: WhitelistAction },
    Audit,
    Integrity { #[command(subcommand)] action: Option<IntegrityAction> },
    ScanSuid,
    Kernel,
    Monitor,
}

#[derive(Subcommand)]
enum WhitelistAction {
    Add { path: String },
    Remove { path: String },
    List,
}

#[derive(Subcommand)]
enum IntegrityAction {
    Baseline,
    Check,
    Show,
}

// Helpers
fn now() -> String {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs().to_string())
        .unwrap_or_else(|_| "0".into())
}

fn ensure_dir_secure(path: &str) -> Result<()> {
    let p = PathBuf::from(path);
    if !p.exists() {
        fs::create_dir_all(&p).with_context(|| format!("Failed to create {}", path))?;
        fs::set_permissions(&p, fs::Permissions::from_mode(0o700))?;
    }
    Ok(())
}

fn write_secure(path: &str, contents: &[u8]) -> Result<()> {
    let p = PathBuf::from(path);
    if let Some(par) = p.parent() {
        ensure_dir_secure(par.to_str().unwrap_or("/tmp"))?;
    }
    fs::write(&p, contents)?;
    fs::set_permissions(&p, fs::Permissions::from_mode(0o600))?;
    Ok(())
}

fn load_json<T: serde::de::DeserializeOwned + Default>(path: &str) -> Result<T> {
    let p = PathBuf::from(path);
    if !p.exists() { return Ok(T::default()); }
    let data = fs::read_to_string(&p).with_context(|| format!("Failed to read {}", path))?;
    serde_json::from_str(&data).with_context(|| format!("Failed to parse {}", path))
}

fn save_json<T: Serialize>(path: &str, data: &T) -> Result<()> {
    let json = serde_json::to_string_pretty(data)?;
    write_secure(path, json.as_bytes())
}

fn sanitize_path(input: &str) -> Result<String> {
    if input.contains('\0') { anyhow::bail!("Path contains null bytes"); }
    if input.contains("..") { anyhow::bail!("Path traversal not allowed"); }
    let p = PathBuf::from(input);
    Ok(p.canonicalize().unwrap_or(p).to_string_lossy().into_owned())
}

fn read_sysctl(key: &str) -> String {
    fs::read_to_string(format!("/proc/sys/{}", key.replace('.', "/")))
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "unreadable".into())
}

fn read_lockdown() -> String {
    fs::read_to_string("/sys/kernel/security/lockdown")
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "unsupported".into())
}

fn hash_file(path: &str) -> Result<String> {
    let data = fs::read(path)?;
    let mut hasher = Sha256::new();
    hasher.update(&data);
    Ok(hex::encode(hasher.finalize()))
}

fn push_alert(alerts: &mut Vec<Alert>, alert: Alert) {
    alerts.push(alert);
    if alerts.len() > MAX_ALERTS { alerts.drain(..alerts.len() - MAX_ALERTS); }
}

fn load_alerts() -> Result<Vec<Alert>> { load_json(ALERTS_FILE) }
fn save_alerts(a: &Vec<Alert>) -> Result<()> { save_json(ALERTS_FILE, a) }
fn load_whitelist() -> Result<Whitelist> { load_json(WHITELIST_FILE) }
fn save_whitelist(w: &Whitelist) -> Result<()> { save_json(WHITELIST_FILE, w) }

// Kernel checks
fn check_kernel() -> KernelSecurityState {
    let lockdown_raw = read_lockdown();
    let lockdown = lockdown_raw.split('(').next().unwrap_or("unknown").trim().to_string();
    KernelSecurityState {
        lockdown,
        kptr_restrict: read_sysctl("kernel.kptr_restrict").parse().unwrap_or(0),
        dmesg_restrict: read_sysctl("kernel.dmesg_restrict").parse().unwrap_or(0),
        perf_paranoid: read_sysctl("kernel.perf_event_paranoid").parse().unwrap_or(0),
        unprivileged_bpf_disabled: read_sysctl("kernel.unprivileged_bpf_disabled").parse().unwrap_or(0),
        randomize_va_space: read_sysctl("kernel.randomize_va_space").parse().unwrap_or(0),
        yama_ptrace_scope: read_sysctl("kernel.yama.ptrace_scope").parse().unwrap_or(0),
        modules_disabled: fs::read_to_string("/proc/sys/kernel/modules_disabled").map(|s| s.trim()=="1").unwrap_or(false),
        secure_boot: Command::new("mokutil").args(["--sb-state"]).output().map(|o| String::from_utf8_lossy(&o.stdout).contains("enabled")).unwrap_or(false),
        iommu_enabled: fs::read_to_string("/proc/cmdline").map(|c| c.contains("iommu=") && !c.contains("iommu=off")).unwrap_or(false),
        smep_enabled: fs::read_to_string("/proc/cpuinfo").map(|c| c.contains("smep")).unwrap_or(false),
        smap_enabled: fs::read_to_string("/proc/cpuinfo").map(|c| c.contains("smap")).unwrap_or(false),
        kaiser_enabled: fs::read_to_string("/sys/devices/system/cpu/vulnerabilities/meltdown").map(|s| s.contains("Mitigation")).unwrap_or(false),
    }
}

fn audit_score(ks: &KernelSecurityState) -> (u32, u32) {
    let mut s: u32 = 0;
    if ks.lockdown=="integrity" || ks.lockdown=="confidentiality" { s+=10; }
    if ks.kptr_restrict>=2 { s+=10; }
    if ks.dmesg_restrict>=1 { s+=10; }
    if ks.perf_paranoid>=2 { s+=10; }
    if ks.unprivileged_bpf_disabled>=1 { s+=10; }
    if ks.randomize_va_space>=2 { s+=10; }
    if ks.yama_ptrace_scope>=1 { s+=10; }
    if ks.modules_disabled { s+=10; }
    if ks.secure_boot { s+=10; }
    if ks.iommu_enabled { s+=10; }
    if ks.smap_enabled { s+=10; }
    if ks.smep_enabled { s+=10; }
    if ks.kaiser_enabled { s+=10; }
    (s, 130)
}

fn print_check(name: &str, ok: bool, detail: &str) {
    let (icon, _color) = if ok { ("\x1b[92m+", "") } else { ("\x1b[91m!", "") };
    println!("    {} {} {}\x1b[0m", icon, name, detail);
}

// Commands
fn cmd_status() -> Result<()> {
    let active = Command::new("systemctl").args(["is-active", "synthguard.service"]).output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim()=="active").unwrap_or(false);
    let ks = check_kernel();
    let (score, max) = audit_score(&ks);
    let pct = (score as f64 / max as f64 * 100.0) as u32;
    let alerts = load_alerts()?;
    let crit = alerts.iter().filter(|a| a.severity=="critical").count();
    let high = alerts.iter().filter(|a| a.severity=="high").count();
    let last = alerts.last().map(|a| a.timestamp.as_str()).unwrap_or("never");

    println!("\n  \x1b[96m=== SynthGuard -- Kernel Security Monitor ===\x1b[0m\n");
    let sc = if active { "\x1b[92m* ACTIVE" } else { "\x1b[91m! INACTIVE" };
    println!("  Service:  {} \x1b[0m", sc);
    let pc = if pct>=90 { "\x1b[92m" } else if pct>=70 { "\x1b[93m" } else { "\x1b[91m" };
    println!("  Score:    {}{}%\x1b[0m ({}/{})", pc, pct, score, max);
    println!("  Alerts:   {} total, \x1b[91m{} critical\x1b[0m, \x1b[93m{} high\x1b[0m", alerts.len(), crit, high);
    println!("  Last:     {}", last);
    println!("\n  \x1b[96mKernel Security:\x1b[0m");
    let ck = |n: &str, ok: bool| { let ic = if ok { "\x1b[92m[OK]" } else { "\x1b[91m[--]" }; println!("    {} {}\x1b[0m", ic, n); };
    ck(&format!("Lockdown:        {}", ks.lockdown), ks.lockdown=="integrity" || ks.lockdown=="confidentiality");
    ck(&format!("kptr_restrict:   {}", ks.kptr_restrict), ks.kptr_restrict>=2);
    ck(&format!("dmesg_restrict:  {}", ks.dmesg_restrict), ks.dmesg_restrict>=1);
    ck(&format!("ASLR:            {}", ks.randomize_va_space), ks.randomize_va_space>=2);
    ck(&format!("BPF restricted:  {}", ks.unprivileged_bpf_disabled>=1), ks.unprivileged_bpf_disabled>=1);
    ck(&format!("Secure Boot:     {}", ks.secure_boot), ks.secure_boot);
    ck(&format!("IOMMU:           {}", ks.iommu_enabled), ks.iommu_enabled);
    ck(&format!("SMEP/SMAP:       {}/{}", ks.smep_enabled, ks.smap_enabled), ks.smep_enabled && ks.smap_enabled);
    println!();
    Ok(())
}

fn cmd_alerts(count: usize, severity: &Option<String>) -> Result<()> {
    let mut alerts = load_alerts()?;
    alerts.reverse();
    if let Some(ref s) = severity { alerts.retain(|a| a.severity.eq_ignore_ascii_case(s)); }
    if alerts.is_empty() { println!("  \x1b[33mNo alerts.\x1b[0m"); return Ok(()); }
    println!("  \x1b[96mRecent Alerts ({} of {}):\x1b[0m\n", count.min(alerts.len()), alerts.len());
    for (i, al) in alerts.iter().enumerate().take(count) {
        let c = match al.severity.as_str() { "critical"=>"\x1b[91m", "high"=>"\x1b[93m", "medium"=>"\x1b[33m", _=>"\x1b[96m" };
        println!("  {}#{} [{}] {}{} \x1b[0m{} pid={} {}", c, i+1, al.timestamp, c, al.severity, al.category, al.pid, al.exe);
        println!("    \x1b[90m{}\x1b[0m", al.message);
        if let Some(ref d) = al.details { println!("    \x1b[90m  {}\x1b[0m", d); }
    }
    println!();
    Ok(())
}

fn cmd_whitelist_add(path: &str) -> Result<()> {
    let clean = sanitize_path(path)?;
    let mut wl = load_whitelist()?;
    if wl.binaries.contains(&clean) { println!("  \x1b[33mAlready whitelisted.\x1b[0m"); return Ok(()); }
    wl.binaries.push(clean.clone());
    save_whitelist(&wl)?;
    let mut a = load_alerts()?;
    let next_id = a.len() as u64 + 1;
    push_alert(&mut a, Alert { id: next_id, severity:"info".into(), category:"whitelist".into(),
        message: format!("Whitelisted: {}", clean), pid: std::process::id(), exe:"synthguard".into(), timestamp: now(), details: None });
    save_alerts(&a)?;
    println!("  \x1b[92m+ Whitelisted: {}\x1b[0m", clean);
    Ok(())
}

fn cmd_whitelist_remove(path: &str) -> Result<()> {
    let clean = sanitize_path(path)?;
    let mut wl = load_whitelist()?;
    let before = wl.binaries.len();
    wl.binaries.retain(|p| p != &clean);
    if wl.binaries.len() == before { println!("  \x1b[33mNot found.\x1b[0m"); } else {
        save_whitelist(&wl)?;
        println!("  \x1b[93m- Removed: {}\x1b[0m", clean);
    }
    Ok(())
}

fn cmd_whitelist_list() -> Result<()> {
    let wl = load_whitelist()?;
    println!("  \x1b[96mWhitelisted Binaries:\x1b[0m");
    if wl.binaries.is_empty() { println!("    (none)"); } else { for b in &wl.binaries { println!("    - {}", b); } }
    println!("  \n  \x1b[96mWhitelisted Syscalls:\x1b[0m");
    if wl.syscalls.is_empty() { println!("    (none)"); } else { for s in &wl.syscalls { println!("    - {}", s); } }
    println!();
    Ok(())
}

fn cmd_audit() -> Result<()> {
    println!("\n  \x1b[96m=== Full Security Audit ===\x1b[0m\n");
    let ks = check_kernel();
    let mut pass = 0u32;
    let mut fail = 0u32;
    macro_rules! check { ($name:expr, $ok:expr, $det:expr) => {
        if $ok { pass+=1; } else { fail+=1; }
        print_check($name, $ok, $det);
    }; }
    check!("Kernel lockdown", ks.lockdown=="integrity"||ks.lockdown=="confidentiality", &ks.lockdown);
    check!("Sysctl hardening", ks.kptr_restrict>=2&&ks.dmesg_restrict>=1&&ks.randomize_va_space>=2,
        &format!("kptr={} dmesg={} aslr={}", ks.kptr_restrict, ks.dmesg_restrict, ks.randomize_va_space));
    check!("BPF restricted", ks.unprivileged_bpf_disabled>=1, &format!("v={}", ks.unprivileged_bpf_disabled));
    check!("Secure Boot", ks.secure_boot, if ks.secure_boot{"enabled"}else{"disabled"});
    check!("IOMMU", ks.iommu_enabled, if ks.iommu_enabled{"active"}else{"inactive"});
    check!("SMEP+SMAP", ks.smep_enabled&&ks.smap_enabled, &format!("{}/{}", ks.smep_enabled, ks.smap_enabled));
    let modok = fs::read_to_string("/proc/sys/kernel/module.sig_enforce").map(|s| s.trim()=="1").unwrap_or(false);
    check!("Module signing", modok, if modok{"enforced"}else{"not enforced"});
    check!("Yama ptrace", ks.yama_ptrace_scope>=1, &format!("scope={}", ks.yama_ptrace_scope));
    let fw = Command::new("firewall-cmd").args(["--state"]).output().map(|o| String::from_utf8_lossy(&o.stdout).contains("running")).unwrap_or(false);
    check!("Firewall", fw, if fw{"running"}else{"NOT RUNNING"});
    let sel = Command::new("getenforce").output().map(|o| String::from_utf8_lossy(&o.stdout).trim()=="Enforcing").unwrap_or(false);
    let aap = fs::read_to_string("/sys/module/apparmor/parameters/enabled").map(|s| s.trim()=="Y").unwrap_or(false);
    check!("MAC (SELinux/AppArmor)", sel||aap, if sel{"SELinux"}else if aap{"AppArmor"}else{"NONE"});
    let aud = Command::new("systemctl").args(["is-active", "auditd"]).output().map(|o| String::from_utf8_lossy(&o.stdout).trim()=="active").unwrap_or(false);
    check!("auditd", aud, if aud{"active"}else{"inactive"});
    check!("Full ASLR", ks.randomize_va_space>=2, &format!("v={}", ks.randomize_va_space));
    let slab = fs::read_to_string("/proc/sys/kernel/slab_freelist_hardened").map(|s| s.trim()=="1").unwrap_or(false);
    check!("Slab hardening", slab, if slab{"active"}else{"inactive"});
    check!("Kptr hidden", ks.kptr_restrict>=2, &format!("v={}", ks.kptr_restrict));
    let total = pass+fail;
    let pct = if total>0 {(pass as f64/total as f64*100.0) as u32} else {0};
    let gc = if pct>=90{"\x1b[92m"}else if pct>=70{"\x1b[93m"}else{"\x1b[91m"};
    println!("\n  \x1b[96m========================================\x1b[0m");
    println!("  {}Score: {}/{} ({}%)\x1b[0m", gc, pass, total, pct);
    println!("  \x1b[96m========================================\x1b[0m\n");
    Ok(())
}

fn cmd_kernel() -> Result<()> {
    let ks = check_kernel();
    println!("\n  \x1b[96mKernel Security Status:\x1b[0m\n");
    println!("  Lockdown:           {}", read_lockdown());
    println!("  kptr_restrict:      {}", ks.kptr_restrict);
    println!("  dmesg_restrict:     {}", ks.dmesg_restrict);
    println!("  perf_event_paranoid: {}", ks.perf_paranoid);
    println!("  unprivileged_bpf:   {}", ks.unprivileged_bpf_disabled);
    println!("  randomize_va_space: {}", ks.randomize_va_space);
    println!("  yama.ptrace_scope:  {}", ks.yama_ptrace_scope);
    println!("  modules_disabled:   {}", ks.modules_disabled);
    println!("  Secure Boot:        {}", ks.secure_boot);
    println!("  IOMMU:              {}", ks.iommu_enabled);
    println!("  SMEP/SMAP:          {}/{}", ks.smep_enabled, ks.smap_enabled);
    println!("  KPTI:               {}", ks.kaiser_enabled);
    for (name, path) in [
        ("Meltdown", "/sys/devices/system/cpu/vulnerabilities/meltdown"),
        ("Spectre v1", "/sys/devices/system/cpu/vulnerabilities/spectre_v1"),
        ("Spectre v2", "/sys/devices/system/cpu/vulnerabilities/spectre_v2"),
        ("SSB", "/sys/devices/system/cpu/vulnerabilities/spec_store_bypass"),
        ("L1TF", "/sys/devices/system/cpu/vulnerabilities/l1tf"),
        ("MDS", "/sys/devices/system/cpu/vulnerabilities/mds"),
    ] {
        if let Ok(v) = fs::read_to_string(path) { println!("  {:18}{}", name, v.trim()); }
    }
    println!();
    Ok(())
}

fn scan_suid() -> Result<Vec<String>> {
    let dirs = ["/usr/bin", "/usr/sbin", "/bin", "/sbin"];
    let mut out = Vec::new();
    for d in &dirs {
        let pb = PathBuf::from(d);
        if !pb.exists() { continue; }
        if let Ok(entries) = fs::read_dir(&pb) {
            for e in entries.flatten() {
                if let Ok(m) = fs::metadata(e.path()) {
                    let mode = m.permissions().mode();
                    if mode & 0o4000 != 0 || mode & 0o2000 != 0 {
                        let fl = [if mode&0o4000!=0{"SUID"}else{""}, if mode&0o2000!=0{"SGID"}else{""}].join(" ");
                        out.push(format!("{} [{} mode={:o}]", e.path().display(), fl.trim(), mode & 0o7777));
                    }
                }
            }
        }
    }
    Ok(out)
}

fn cmd_scan_suid() -> Result<()> {
    let bins = scan_suid()?;
    println!("  \x1b[96mSUID/SGID Binaries:\x1b[0m\n");
    if bins.is_empty() { println!("  \x1b[92mNone found.\x1b[0m"); return Ok(()); }
    let safe: HashSet<&str> = ["/usr/bin/passwd","/usr/bin/sudo","/usr/bin/su","/usr/bin/chsh",
        "/usr/bin/chfn","/usr/bin/newgrp","/usr/bin/gpasswd","/usr/bin/mount","/usr/bin/umount",
        "/usr/bin/fusermount","/usr/bin/fusermount3","/usr/bin/pkexec"].iter().copied().collect();
    let mut review = 0;
    for b in &bins {
        let p = b.split(' ').next().unwrap_or("");
        if safe.contains(p) { println!("  \x1b[92m  [OK]\x1b[0m {}", b); }
        else { println!("  \x1b[93m  [!!]\x1b[0m {}", b); review+=1; }
    }
    println!("\n  Total: {} ({} need review)", bins.len(), review);
    println!();
    Ok(())
}

fn cmd_integrity_baseline() -> Result<()> {
    println!("  \x1b[93mRecording integrity baseline...\x1b[0m");
    let dirs = ["/etc", "/usr/bin", "/usr/sbin", "/boot"];
    let mut db = IntegrityDb::default();
    for d in &dirs {
        let pb = PathBuf::from(d);
        if !pb.exists() { continue; }
        if let Ok(entries) = fs::read_dir(&pb) {
            for e in entries.flatten() {
                let p = e.path();
                if p.is_file() {
                    if let (Ok(m), Ok(h)) = (fs::metadata(&p), hash_file(p.to_str().unwrap_or(""))) {
                        db.entries.push(IntegrityEntry { path: p.to_string_lossy().into_owned(), sha256: h, size: m.len(), mode: m.permissions().mode(), recorded_at: now() });
                    }
                }
            }
        }
    }
    save_json(INTEGRITY_DB, &db)?;
    println!("  \x1b[92m+ Baseline: {} files recorded.\x1b[0m\n", db.entries.len());
    Ok(())
}

fn cmd_integrity_check() -> Result<()> {
    let db: IntegrityDb = load_json(INTEGRITY_DB)?;
    if db.entries.is_empty() { println!("  \x1b[33mNo baseline. Run 'synthguard integrity baseline' first.\x1b[0m"); return Ok(()); }
    println!("  \x1b[93mChecking integrity...\x1b[0m\n");
    let mut modified = 0u32;
    let mut missing = 0u32;
    for e in &db.entries {
        if !PathBuf::from(&e.path).exists() { println!("  \x1b[91m  [MISSING] {}\x1b[0m", e.path); missing+=1; continue; }
        if let Ok(h) = hash_file(&e.path) {
            if h != e.sha256 { println!("  \x1b[91m  [MODIFIED] {}\x1b[0m", e.path); modified+=1; }
        }
    }
    if modified==0 && missing==0 { println!("  \x1b[92mAll {} files match baseline.\x1b[0m", db.entries.len()); }
    else { println!("\n  \x1b[91mIssues: {} modified, {} missing\x1b[0m", modified, missing); }
    println!();
    Ok(())
}

fn cmd_integrity_show() -> Result<()> {
    let db: IntegrityDb = load_json(INTEGRITY_DB)?;
    println!("  \x1b[96mIntegrity DB: {} entries\x1b[0m\n", db.entries.len());
    for e in db.entries.iter().take(30) {
        println!("    {} [{}B] {}...", e.path, e.size, &e.sha256[..16.min(e.sha256.len())]);
    }
    if db.entries.len()>30 { println!("    ... and {} more", db.entries.len()-30); }
    println!();
    Ok(())
}

fn cmd_monitor() -> Result<()> {
    println!("  \x1b[93mScanning for security events...\x1b[0m\n");
    let mut alerts = load_alerts()?;
    let mut new_count = 0u32;
    let start_id = alerts.len() as u64 + 1;
    // Check audit log
    if let Ok(f) = fs::File::open("/var/log/audit/audit.log") {
        for (i, line) in BufReader::new(f).lines().enumerate() {
            if let Ok(l) = line {
                if l.contains("SYSCALL") && l.contains("init_module") {
                    push_alert(&mut alerts, Alert { id: start_id+new_count as u64, severity:"high".into(), category:"kernel".into(),
                        message:"Kernel module load attempt".into(), pid:0, exe:"kernel".into(), timestamp:now(), details: Some(l[..200.min(l.len())].into()) });
                    new_count+=1;
                }
                if l.contains("AVC") && l.contains("denied") {
                    push_alert(&mut alerts, Alert { id: start_id+new_count as u64, severity:"medium".into(), category:"privilege".into(),
                        message:"SELinux denial".into(), pid:0, exe:"selinux".into(), timestamp:now(), details: Some(l[..200.min(l.len())].into()) });
                    new_count+=1;
                }
                if i > 10000 { break; }
            }
        }
    }
    // Check world-writable in critical dirs
    for d in ["/etc", "/usr/bin", "/usr/sbin"] {
        if let Ok(entries) = fs::read_dir(d) {
            for e in entries.flatten() {
                if let Ok(m) = fs::metadata(e.path()) {
                    if m.permissions().mode() & 0o002 != 0 {
                        push_alert(&mut alerts, Alert { id: start_id+new_count as u64, severity:"high".into(), category:"integrity".into(),
                            message: format!("World-writable: {}", e.path().display()), pid:0, exe:"monitor".into(), timestamp:now(),
                            details: Some(format!("mode={:o}", m.permissions().mode()&0o7777)) });
                        new_count+=1;
                    }
                }
            }
        }
    }
    save_alerts(&alerts)?;
    if new_count>0 { println!("  \x1b[93m! {} new alerts.\x1b[0m\n", new_count); }
    else { println!("  \x1b[92mNo new events.\x1b[0m\n"); }
    Ok(())
}

fn main() -> Result<()> {
    ensure_dir_secure("/var/log/synthguard")?;
    ensure_dir_secure("/var/lib/synthguard")?;
    ensure_dir_secure("/etc/synthguard")?;
    match Cli::parse().command {
        Commands::Status => cmd_status(),
        Commands::Alerts { count, severity } => cmd_alerts(count, &severity),
        Commands::Whitelist { action } => match action {
            WhitelistAction::Add { path } => cmd_whitelist_add(&path),
            WhitelistAction::Remove { path } => cmd_whitelist_remove(&path),
            WhitelistAction::List => cmd_whitelist_list(),
        },
        Commands::Audit => cmd_audit(),
        Commands::Integrity { action } => match action {
            Some(IntegrityAction::Baseline) => cmd_integrity_baseline(),
            Some(IntegrityAction::Check) => cmd_integrity_check(),
            Some(IntegrityAction::Show) => cmd_integrity_show(),
            None => cmd_integrity_check(),
        },
        Commands::ScanSuid => cmd_scan_suid(),
        Commands::Kernel => cmd_kernel(),
        Commands::Monitor => cmd_monitor(),
    }
}
