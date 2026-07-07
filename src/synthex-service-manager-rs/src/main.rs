// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-service-manager - Enhanced service manager for SynthOS

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::Serialize;
use std::process::Command;

fn is_root() -> bool {
    Command::new("id").arg("-u").output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim() == "0")
        .unwrap_or(false)
}

fn systemctl(args: &[&str]) -> String {
    let out = if is_root() {
        Command::new("systemctl").args(args).output()
    } else {
        Command::new("sudo").arg("systemctl").args(args).output()
    };
    out.map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default()
}

fn systemctl_ok(args: &[&str]) -> bool {
    let out = if is_root() {
        Command::new("systemctl").args(args).status()
    } else {
        Command::new("sudo").arg("systemctl").args(args).status()
    };
    out.map(|s| s.success()).unwrap_or(false)
}

const SYNTHEX_SERVICES: &[(&str, &str, &str)] = &[
    ("synthex-desktopd", "Desktop environment", "session"),
    ("synthex-hwdaemon", "Hardware detection daemon", "system"),
    ("synthex-gpu-setupd", "GPU configuration daemon", "system"),
    ("synthex-stored", "State persistence daemon", "system"),
    ("synthex-system-daemon", "System orchestration", "system"),
    ("synthex-ai-daemon", "AI assistant daemon", "system"),
    ("synthex-integration-engine", "Upstream integration engine", "system"),
    ("synthex-snapshot-manager", "Btrfs snapshot manager", "system"),
    ("synthex-oobe", "First-boot setup wizard", "system"),
    ("synthex-workspace", "Workspace mode manager", "user"),
];

#[derive(Debug, Serialize)]
struct ServiceStatus {
    name: String,
    description: String,
    active: bool,
    enabled: bool,
    state: String,
}

#[derive(Debug, Serialize)]
struct ServiceSummary {
    total: usize,
    running: usize,
    failed: usize,
    synthex_services: Vec<ServiceStatus>,
    system_state: String,
}

#[derive(Parser)]
#[command(name="synthex-service", version="0.2.0", about="SynthOS service manager")]
struct Cli {
    #[command(subcommand)]
    cmd: Commands,
    #[arg(long, global = true)]
    json: bool,
}

#[derive(Subcommand)]
enum Commands {
    List { filter: Option<String> },
    Status { service: String },
    Start { service: String },
    Stop { service: String },
    Restart { service: String },
    Enable { service: String },
    Disable { service: String },
    Failed,
    Synthex,
    Summary,
    Health,
}

fn get_service_status(name: &str) -> ServiceStatus {
    let svc = if name.ends_with(".service") { name.to_string() } else { format!("{name}.service") };
    let active = systemctl_ok(&["is-active", &svc]);
    let enabled = systemctl_ok(&["is-enabled", &svc]);
    let state = if active { "running" } else if enabled { "inactive" } else { "not-found" };
    ServiceStatus {
        name: name.to_string(),
        description: String::new(),
        active, enabled, state: state.into(),
    }
}

fn list_synthex(json: bool) -> String {
    let mut services = Vec::new();
    for (name, desc, _) in SYNTHEX_SERVICES {
        let mut st = get_service_status(name);
        st.description = desc.to_string();
        services.push(st);
    }
    if json {
        return serde_json::to_string_pretty(&services).unwrap_or_default();
    }
    let mut out = String::new();
    out.push_str("\n  Synthex Services:\n");
    for s in &services {
        let icon = if s.active { "[OK]" } else if s.enabled { "[IDLE]" } else { "[OFF]" };
        out.push_str(&format!("    {icon} {:<35} {:<8} enabled:{}\n", s.name, s.state, s.enabled));
    }
    out
}

fn list_services(filter: &str, json: bool) -> String {
    if filter == "synthex" { return list_synthex(json); }
    let args: &[&str] = match filter {
        "running" => &["list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"],
        "failed" => &["--failed", "--no-pager", "--no-legend"],
        _ => &["list-units", "--type=service", "--no-pager", "--no-legend"],
    };
    let out = systemctl(args);
    if json {
        let services: Vec<ServiceStatus> = out.lines().filter(|l| !l.trim().is_empty()).map(|line| {
            let parts: Vec<&str> = line.split_whitespace().collect();
            let name = parts.first().copied().unwrap_or("?").trim_end_matches(".service").to_string();
            let state = parts.get(2).copied().unwrap_or("?").to_string();
            ServiceStatus {
                active: state == "active",
                enabled: false,
                name, description: String::new(), state,
            }
        }).collect();
        return serde_json::to_string_pretty(&services).unwrap_or_default();
    }
    if filter == "failed" && out.trim().is_empty() {
        return "  No failed services\n".to_string();
    }
    let mut result = format!("  {} services:\n\n", filter);
    for line in out.lines() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.is_empty() { continue; }
        let name = parts[0];
        let state = parts.get(2).unwrap_or(&"");
        let icon = if *state == "active" { "[OK]" } else if *state == "failed" { "[FAIL]" } else { "[ - ]" };
        result.push_str(&format!("    {icon} {:<45} {}\n", name, state));
    }
    result
}

fn get_summary() -> ServiceSummary {
    let all = systemctl(&["list-units", "--type=service", "--no-pager", "--no-legend"]);
    let total = all.lines().filter(|l| !l.trim().is_empty()).count();
    let running = systemctl(&["list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"]);
    let nr = running.lines().filter(|l| !l.trim().is_empty()).count();
    let failed = systemctl(&["--failed", "--no-pager", "--no-legend"]);
    let nf = failed.lines().filter(|l| !l.trim().is_empty()).count();
    let mut synthex_services = Vec::new();
    for (name, desc, _) in SYNTHEX_SERVICES {
        let mut st = get_service_status(name);
        st.description = desc.to_string();
        synthex_services.push(st);
    }
    ServiceSummary {
        total, running: nr, failed: nf,
        synthex_services,
        system_state: systemctl(&["is-system-running"]).trim().to_string(),
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let json = cli.json;

    match cli.cmd {
        Commands::List { filter } => {
            let f = filter.unwrap_or_default();
            let f = if f.is_empty() { "all" } else { &f };
            let out = list_services(f, json);
            if json { println!("{out}"); } else { print!("{out}"); }
        }
        Commands::Status { service } => {
            if json {
                let st = get_service_status(&service);
                println!("{}", serde_json::to_string_pretty(&st)?);
            } else {
                println!("{}", systemctl(&["status", &service, "--no-pager", "--lines", "30"]));
            }
        }
        Commands::Start { service } => {
            let ok = systemctl_ok(&["start", &service]);
            if ok { println!("  Started {service}"); } else { println!("  Failed to start {service}"); }
        }
        Commands::Stop { service } => {
            let ok = systemctl_ok(&["stop", &service]);
            if ok { println!("  Stopped {service}"); } else { println!("  Failed to stop {service}"); }
        }
        Commands::Restart { service } => {
            let ok = systemctl_ok(&["restart", &service]);
            if ok { println!("  Restarted {service}"); } else { println!("  Failed to restart {service}"); }
        }
        Commands::Enable { service } => {
            let ok = systemctl_ok(&["enable", &service]);
            if ok { println!("  Enabled {service}"); } else { println!("  Failed to enable {service}"); }
        }
        Commands::Disable { service } => {
            let ok = systemctl_ok(&["disable", &service]);
            if ok { println!("  Disabled {service}"); } else { println!("  Failed to disable {service}"); }
        }
        Commands::Failed => {
            let out = list_services("failed", json);
            if json { println!("{out}"); } else { print!("{out}"); }
        }
        Commands::Synthex => {
            let out = list_synthex(json);
            if json { println!("{out}"); } else { print!("{out}"); }
        }
        Commands::Summary => {
            let s = get_summary();
            if json {
                println!("{}", serde_json::to_string_pretty(&s)?);
            } else {
                println!("");
                println!("  Service Summary");
                println!("    Total:   {}", s.total);
                println!("    Running: {}", s.running);
                println!("    Failed:  {}", s.failed);
                println!("    System:  {}", s.system_state);
                println!("");
                println!("  Synthex Services:");
                for svc in &s.synthex_services {
                    let icon = if svc.active { "[OK]" } else if svc.enabled { "[IDLE]" } else { "[OFF]" };
                    println!("    {icon} {:<35} {}", svc.name, svc.state);
                }
            }
        }
        Commands::Health => {
            let s = get_summary();
            let total = s.total.max(1);
            let running_pct = (s.running as f64 / total as f64 * 100.0) as u32;
            let mut synthex_running = 0;
            for svc in &s.synthex_services { if svc.active { synthex_running += 1; } }
            let synthex_pct = if !s.synthex_services.is_empty() {
                (synthex_running as f64 / s.synthex_services.len() as f64 * 100.0) as u32
            } else { 0 };
            let score = if s.failed == 0 {
                (running_pct + synthex_pct) / 2
            } else {
                (running_pct + synthex_pct).saturating_sub((s.failed as u32) * 10)
            };
            if json {
                use std::collections::HashMap;
                let mut h = HashMap::new();
                h.insert("score", score);
                h.insert("running", s.running as u32);
                h.insert("failed", s.failed as u32);
                h.insert("total", s.total as u32);
                println!("{}", serde_json::to_string_pretty(&h)?);
            } else {
                let grade = match score {
                    90..=100 => "Excellent",
                    75..=89 => "Good",
                    50..=74 => "Fair",
                    _ => "Poor",
                };
                println!("  Service Health: {}/100 - {grade}", score);
                println!("    Running:    {} ({running_pct}%)", s.running);
                println!("    Failed:     {}", s.failed);
                println!("    Synthex:      {synthex_running}/{} ({synthex_pct}%)", s.synthex_services.len());
                if s.system_state != "running" {
                    println!("    System:     {} - not fully running!", s.system_state);
                }
            }
        }
    }
    Ok(())
}

