use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::{fs, path::PathBuf, process::Command, collections::HashMap};

const RULES: &str = "/etc/synthnet/rules.json";

#[derive(Debug,Serialize,Deserialize)]
struct R { app: String, action: String, proto: String, port: u16, created: String }
#[derive(Debug,Serialize,Deserialize)]
struct S { active: bool, rules: Vec<R>, profile: String, iface: String }

fn profiles() -> HashMap<&'static str, Vec<&'static str>> {
    let mut m = HashMap::new();
    m.insert("strict", vec!["Drop all inbound","Allow established","Allow loopback","Allow DNS"]);
    m.insert("gaming", vec!["Allow established","Drop inbound","Allow loopback","Allow DNS","Allow game ports 27000-27036,3478,4380"]);
    m.insert("dev", vec!["Allow established","Allow loopback","Allow DNS","Allow SSH(22),HTTP(80),HTTPS(443)"]);
    m.insert("home", vec!["Allow established","Allow LAN inbound","Allow loopback","Allow DNS","Allow HTTP/HTTPS,mDNS,SMB"]);
    m
}

#[derive(Parser)]
#[command(name="synthnet",about="SynthNet Firewall & Network Policy Manager")]
struct Cli { #[command(subcommand)] command: Commands }
#[derive(Subcommand)]
enum Commands { Status, Block { app: String }, Allow { app: String }, Profile { name: String }, Rules }

fn load() -> Result<S> {
    let p = PathBuf::from(RULES);
    if p.exists() { Ok(serde_json::from_str(&fs::read_to_string(&p)?)?) }
    else { Ok(S { active: false, rules: vec![], profile: "none".into(), iface: "-".into() }) }
}
fn save(s: &S) -> Result<()> {
    let p = PathBuf::from(RULES);
    if let Some(par) = p.parent() { fs::create_dir_all(par)?; }
    fs::write(&p, serde_json::to_string_pretty(s)?)?; Ok(())
}
fn now() -> String { std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs().to_string()).unwrap_or("0".into()) }

fn status() -> Result<()> {
    let s = load()?;
    let ufw = Command::new("ufw").arg("status").output().map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string()).unwrap_or("unknown".into());
    println!("\n  \x1b[34mSynthNet Firewall\x1b[0m");
    println!("  Service: {}  Profile: \x1b[96m{}\x1b[0m  Rules: {}  UFW: {}",
        if s.active { "\x1b[92mACTIVE\x1b[0m" } else { "\x1b[91mINACTIVE\x1b[0m" }, s.profile, s.rules.len(), ufw);
    Ok(())
}

fn block(app: &str) -> Result<()> {
    let mut s = load()?; s.rules.push(R { app: app.into(), action: "block".into(), proto: "any".into(), port: 0, created: now() });
    s.active = true; save(&s)?; Command::new("ufw").args(["deny","out","to","any"]).status().ok();
    println!("  \x1b[91mBlocked '{}'\x1b[0m", app); Ok(())
}

fn allow(app: &str) -> Result<()> {
    let mut s = load()?; s.rules.retain(|r| r.app != app);
    s.rules.push(R { app: app.into(), action: "allow".into(), proto: "any".into(), port: 0, created: now() });
    s.active = true; save(&s)?; Command::new("ufw").args(["allow","out","to","any"]).status().ok();
    println!("  \x1b[92mAllowed '{}'\x1b[0m", app); Ok(())
}

fn profile(name: &str) -> Result<()> {
    let p = profiles();
    match p.get(name) {
        Some(rules) => {
            let mut s = load()?; s.profile = name.into(); s.active = true; save(&s)?;
            println!("  \x1b[96mProfile '{}' applied:\x1b[0m", name); for r in rules { println!("    - {}", r); } Ok(())
        }
        None => { println!("  \x1b[33mAvailable: {}\x1b[0m", p.keys().cloned().collect::<Vec<_>>().join(", ")); anyhow::bail!("unknown") }
    }
}

fn rules() -> Result<()> {
    let s = load()?; println!("\n  \x1b[34mRules ({}):\x1b[0m", s.rules.len());
    for r in &s.rules { let c = if r.action=="block"{"\x1b[91m"}else{"\x1b[92m"}; println!("  {}[{}]\x1b[0m {} {}:{}",c,r.action,r.app,r.proto,r.port); }
    if s.rules.is_empty() { println!("  \x1b[33mNo rules.\x1b[0m"); }
    if let Ok(o) = Command::new("ufw").args(["status","numbered"]).output() { println!("{}", String::from_utf8_lossy(&o.stdout)); }
    Ok(())
}

fn main() -> Result<()> {
    match Cli::parse().command {
        Commands::Status => status(), Commands::Block { app } => block(&app),
        Commands::Allow { app } => allow(&app), Commands::Profile { name } => profile(&name),
        Commands::Rules => rules(),
    }
}
