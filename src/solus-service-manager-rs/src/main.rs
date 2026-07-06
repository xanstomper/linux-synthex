// SPDX-License-Identifier: MIT OR Apache-2.0
use anyhow::Result;
use clap::{Parser, Subcommand};
use std::process::Command;
use tracing::info;

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

#[derive(Parser)]
#[command(name="solus-service", version="0.1.0", about="Solus Linux service manager")]
struct Cli { #[command(subcommand)] cmd: Commands }

#[derive(Subcommand)]
enum Commands {
    List { #[arg(default_value="all")] filter: String },
    Status { service: String },
    Start { service: String },
    Stop { service: String },
    Restart { service: String },
    Enable { service: String },
    Disable { service: String },
    Failed,
    Solus,
    Summary,
}

fn list_solus() {
    println!("  ☀️  Solus Services:\n");
    for svc in ["solus-desktopd","solus-hwdaemon","solus-gpu-setupd","solus-stored",
                "solus-system-daemon","solus-ai-daemon","solus-integration-engine",
                "solus-snapshot-manager","solus-oobe","solus-workspace"] {
        let active = systemctl_ok(&["is-active",&format!("{svc}.service")]);
        let enabled = systemctl_ok(&["is-enabled",&format!("{svc}.service")]);
        let icon = if active { "✅" } else if enabled { "🟡" } else { "⚪" };
        println!("    {icon} {:<35} active:{active} enabled:{enabled}", svc);
    }
}

fn list_services(filter: &str) {
    match filter {
        "running" => { println!("  🟢 Running:\n"); let out = systemctl(&["list-units","--type=service","--state=running","--no-pager","--no-legend"]); for l in out.lines() { let p: Vec<&str> = l.split_whitespace().collect(); if !p.is_empty() { println!("    ✅ {:<40} {}", p[0], p.get(3).unwrap_or(&"")); } } }
        "failed" => { println!("  🔴 Failed:\n"); let out = systemctl(&["--failed","--no-pager","--no-legend"]); if out.trim().is_empty() { println!("    ✅ No failed services"); } else { for l in out.lines() { let p: Vec<&str> = l.split_whitespace().collect(); if !p.is_empty() { println!("    ❌ {:<40} {}", p[0], p.get(3).unwrap_or(&"")); } } } }
        "solus" => list_solus(),
        _ => { let out = systemctl(&["list-units","--type=service","--no-pager","--no-legend"]); for l in out.lines() { let p: Vec<&str> = l.split_whitespace().collect(); if !p.is_empty() { let st = p.get(2).unwrap_or(&""); let ic = if *st=="active" {"🟢"} else if *st=="failed" {"🔴"} else {"⚪"}; println!("    {ic} {:<40} {:<10} {}", p[0], st, p.get(3).unwrap_or(&"")); } } }
    }
}

fn do_action(action: &str, svc: &str) {
    info!("{action} {svc}");
    if systemctl_ok(&[action, svc]) { println!("  ✅ {action} {svc}"); }
    else { println!("  ❌ {action} {svc} failed"); }
}

fn main() -> Result<()> {
    tracing_subscriber::fmt().with_env_filter(
        tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_|"solus_service=info".into()))
        .with_target(false).compact().init();
    let cli = Cli::parse();
    match cli.cmd {
        Commands::List{filter} => list_services(&filter),
        Commands::Status{service} => println!("{}", systemctl(&["status",&service,"--no-pager"])),
        Commands::Start{service} => do_action("start",&service),
        Commands::Stop{service} => do_action("stop",&service),
        Commands::Restart{service} => do_action("restart",&service),
        Commands::Enable{service} => do_action("enable",&service),
        Commands::Disable{service} => do_action("disable",&service),
        Commands::Failed => list_services("failed"),
        Commands::Solus => list_solus(),
        Commands::Summary => { let r = systemctl(&["list-units","--type=service","--state=running","--no-pager","--no-legend"]); let nr = r.lines().filter(|l|!l.trim().is_empty()).count(); let f = systemctl(&["--failed","--no-pager","--no-legend"]); let nf = f.lines().filter(|l|!l.trim().is_empty()).count(); println!("\n  📊 Summary: {nr} running, {nf} failed, system: {}", systemctl(&["is-system-running"]).trim()); }
    }
    Ok(())
}
