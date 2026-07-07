use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::{fs, path::PathBuf, process::Command};

const HIST: &str = "/var/lib/synthupdate/history.json";

#[derive(Debug,Serialize,Deserialize)]
struct E { id: String, date: String, pkgs: u32, status: String, deploy: String }
#[derive(Debug,Serialize,Deserialize)]
struct US { entries: Vec<E>, pending: u32, last_check: String, current: String }

#[derive(Parser)]
#[command(name="synthupdate",about="SynthUpdate System Update Manager")]
struct Cli { #[command(subcommand)] command: Commands }
#[derive(Subcommand)]
enum Commands { Check, Apply, Rollback, History, Status }

fn load() -> Result<US> {
    let p = PathBuf::from(HIST);
    if p.exists() { Ok(serde_json::from_str(&fs::read_to_string(&p)?)?) }
    else { Ok(US { entries: vec![], pending: 0, last_check: "never".into(), current: "-".into() }) }
}
fn save(s: &US) -> Result<()> {
    let p = PathBuf::from(HIST);
    if let Some(par) = p.parent() { fs::create_dir_all(par)?; }
    fs::write(&p, serde_json::to_string_pretty(s)?)?; Ok(())
}
fn now() -> String { std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs().to_string()).unwrap_or("0".into()) }
fn ostree(args: &[&str], desc: &str) -> Result<String> {
    println!("  \x1b[33m{}...\x1b[0m", desc);
    let o = Command::new("rpm-ostree").args(args).output().with_context(|| desc.to_string())?;
    Ok(String::from_utf8_lossy(&o.stdout).to_string())
}

fn check() -> Result<()> {
    let mut s = load()?;
    let out = ostree(&["update", "--check"], "Checking")?;
    s.last_check = now(); s.pending = out.lines().filter(|l| l.contains("Upgrade")||l.contains("Pending")).count() as u32;
    save(&s)?; println!("{}", out);
    if s.pending > 0 { println!("  \x1b[92m{} updates available.\x1b[0m", s.pending); }
    else { println!("  \x1b[92mUp to date.\x1b[0m"); }
    Ok(())
}

fn apply() -> Result<()> {
    let out = ostree(&["update"], "Applying updates")?;
    let mut s = load()?; let ts = now();
    let deploy = out.lines().find(|l| l.contains("Deployment")).unwrap_or(&"unknown").to_string();
    s.entries.push(E { id: format!("upd-{}", ts), date: ts, pkgs: s.pending, status: "applied".into(), deploy: deploy.clone() });
    s.pending = 0; s.current = deploy.clone(); save(&s)?; println!("{}", out);
    println!("  \x1b[92mApplied. Reboot recommended.\x1b[0m");
    Ok(())
}

fn rollback() -> Result<()> {
    let out = ostree(&["rollback"], "Rolling back")?;
    let mut s = load()?; let ts = now();
    s.entries.push(E { id: format!("rb-{}", ts), date: ts, pkgs: 0, status: "rollback".into(), deploy: out.clone() });
    save(&s)?; println!("{}", out); println!("  \x1b[93mRollback done.\x1b[0m");
    Ok(())
}

fn history() -> Result<()> {
    let s = load()?; println!("\n  \x1b[33mHistory:\x1b[0m");
    if s.entries.is_empty() {
        let out = Command::new("rpm-ostree").args(["status"]).output().map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default();
        println!("{}", out); return Ok(());
    }
    for e in s.entries.iter().rev() {
        let c = match e.status.as_str() { "applied" => "\x1b[92m", "rollback" => "\x1b[93m", _ => "\x1b[91m" };
        println!("  {}[{}]\x1b[0m {} {} pkgs deploy={}", c, e.status, e.date, e.pkgs, e.deploy);
    }
    Ok(())
}

fn status() -> Result<()> {
    let s = load()?;
    let out = Command::new("rpm-ostree").args(["status"]).output().map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default();
    println!("\n  \x1b[33mSynthUpdate\x1b[0m");
    println!("  Last check: {}  Pending: {}  History: {}  Deploy: {}", s.last_check, s.pending, s.entries.len(), s.current);
    println!("  rpm-ostree:\n{}", out);
    Ok(())
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Commands::Check => check(), Commands::Apply => apply(),
        Commands::Rollback => rollback(), Commands::History => history(),
        Commands::Status => status(),
    }
}
