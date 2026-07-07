// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-cli — Unified command-line interface for SynthOS
//
// The single Rust binary that replaces all shell-based tools.
// Provides: info, hardware, gpu, status, doctor, mode, gaming,
//           update, snapshot, rollback, health.

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::process::Command;

mod hardware;
mod status;

#[derive(Parser)]
#[command(name = "synthex", version, about = "SynthOS — unified system tool")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Show system information
    Info,
    /// Detect and display hardware
    Hardware {
        #[arg(long)]
        json: bool,
    },
    /// GPU information and switching
    Gpu {
        #[command(subcommand)]
        action: GpuAction,
    },
    /// System status overview
    Status,
    /// Run system diagnostics and fix common issues
    Doctor,
    /// Switch performance mode (gaming, balanced, battery, creator)
    Mode {
        mode: Option<String>,
    },
    /// Toggle gaming mode on/off
    Gaming {
        state: Option<String>,
    },
    /// Check for and apply system updates
    Update {
        #[arg(long)]
        check: bool,
        #[arg(long)]
        snapshot: bool,
    },
    /// Create a Btrfs snapshot
    Snapshot {
        #[arg(short, long, default_value = "manual snapshot")]
        description: String,
    },
    /// Show rollback instructions
    Rollback,
    /// Quick system health check
    Health,
    /// List and manage system services
    Services {
        #[command(subcommand)]
        action: Option<ServiceAction>,
    },
    /// Show and manage GPU/display drivers
    Drivers,
    /// View system logs
    Logs {
        /// Service or subsystem to view
        service: Option<String>,
        /// Number of lines to show
        #[arg(short, long, default_value = "30")]
        lines: usize,
    },
}

#[derive(Subcommand)]
enum GpuAction {
    List,
    Switch { mode: String },
}

#[derive(Subcommand)]
enum ServiceAction {
    /// List all Synthex services
    List,
    /// Check status of a specific service
    Status { name: String },
    /// Start a service
    Start { name: String },
    /// Stop a service
    Stop { name: String },
    /// Restart a service
    Restart { name: String },
}

fn run_cmd(cmd: &str, args: &[&str]) -> Result<String> {
    let output = Command::new(cmd)
        .args(args)
        .output()
        .with_context(|| format!("Failed to run {cmd}"))?;
    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}

fn run_cmd_status(cmd: &str, args: &[&str]) -> bool {
    Command::new(cmd)
        .args(args)
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

// ─── Doctor ────────────────────────────────────────────────────────────

fn run_doctor() -> Result<()> {
    println!("╔══════════════════════════════════════════════╗");
    println!("║        Synthex Doctor — System Diagnostics    ║");
    println!("╚══════════════════════════════════════════════╝\n");
    let mut issues: u32 = 0;

    println!("📋 Services...");
    for svc in &["synthex-desktopd", "synthex-hwdaemon", "synthex-gpu-setupd",
                  "synthex-stored", "synthex-system-daemon"] {
        let unit = format!("{svc}.service");
        let active = run_cmd_status("systemctl", &["is-active", &unit]);
        let enabled = run_cmd_status("systemctl", &["is-enabled", &unit]);
        if active && enabled { println!("  ✅ {svc}"); }
        else { println!("  ⚠  {svc} — active:{active} enabled:{enabled}"); issues += 1; }
    }

    println!("\n📋 GPU...");
    let hw = hardware::detect_hardware()?;
    for gpu in &hw.gpus {
        let ok = gpu.driver != "unknown" && gpu.driver != "nouveau";
        println!("  {} {} — {}", if ok {"✅"} else {"⚠ "}, gpu.device, gpu.driver);
        if !ok { issues += 1; }
    }

    println!("\n📋 Disk...");
    if let Ok(output) = Command::new("df").args(["-h", "/"]).output() {
        for line in String::from_utf8_lossy(&output.stdout).lines().skip(1) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if let Some(p) = parts.get(4) {
                if let Ok(pct) = p.trim_end_matches('%').parse::<u32>() {
                    println!("  {} Root: {pct}%", if pct > 80 {"⚠ "} else {"✅"});
                    if pct > 80 { issues += 1; }
                }
            }
        }
    }

    println!("\n📋 Security...");
    let sel = run_cmd("getenforce", &[]).unwrap();
    let sel = sel.trim();
    println!("  {} SELinux: {sel}", if sel == "Enforcing" {"✅"} else {"⚠ "});
    if sel != "Enforcing" { issues += 1; }
    let fw = run_cmd_status("firewall-cmd", &["--state"]);
    println!("  {} Firewall: {}", if fw {"✅"} else {"⚠ "}, if fw {"active"} else {"inactive"});
    if !fw { issues += 1; }

    println!("\n📋 Audio...");
    let pw = run_cmd_status("systemctl", &["is-active", "pipewire.service"]);
    println!("  {} PipeWire", if pw {"✅"} else {"⚠ "});
    if !pw { issues += 1; }

    println!("\n╔══════════════════════════════════════════════╗");
    if issues == 0 { println!("║  ✅ System looks healthy                     ║"); }
    else { println!("║  ⚠  Found {issues} issue(s)                          ║"); }
    println!("╚══════════════════════════════════════════════╝");
    Ok(())
}

// ─── Mode / Gaming / Update / Snapshot / Health ────────────────────────

fn run_mode(mode: Option<&str>) -> Result<()> {
    match mode {
        Some(m) => {
            std::fs::create_dir_all("/run/synthex").ok();
            std::fs::write("/run/synthex/performance-mode", m).ok();
            let gov = match m {"gaming"|"creator"=>"performance","battery"=>"powersave",_=>"schedutil"};
            let cpus = std::fs::read_dir("/sys/devices/system/cpu/").unwrap();
            for e in cpus.flatten() {
                let n = e.file_name().to_string_lossy().to_string();
                if n.starts_with("cpu") && n[3..].chars().all(|c| c.is_ascii_digit()) {
                    std::fs::write(e.path().join("cpufreq/scaling_governor"), gov).ok();
                }
            }
            println!("✅ Mode: {m} | Governor: {gov}");
        }
        None => {
            let c = std::fs::read_to_string("/run/synthex/performance-mode").unwrap_or_else(|_|"balanced".into());
            println!("Current: {}\nAvailable: gaming, balanced, battery, creator", c.trim());
        }
    }
    Ok(())
}

// ─── Gaming ────────────────────────────────────────────────────────────

fn run_gaming(state: Option<&str>) -> Result<()> {
    let current = std::fs::read_to_string("/run/synthex/gaming-mode")
        .unwrap_or_else(|_| "off".into());
    let current = current.trim().to_string();

    let toggle = match state {
        Some(s) => s == "on",
        None => current == "off",
    };

    if toggle {
        println!("🎮 Enabling gaming mode...");

        let cpus = std::fs::read_dir("/sys/devices/system/cpu/").unwrap();
        for e in cpus.flatten() {
            let n = e.file_name().to_string_lossy().to_string();
            if n.starts_with("cpu") && n[3..].chars().all(|c| c.is_ascii_digit()) {
                std::fs::write(e.path().join("cpufreq/scaling_governor"), "performance").ok();
            }
        }

        std::fs::create_dir_all("/run/synthex").ok();
        std::fs::write("/run/synthex/gaming-mode", "on").ok();

        if run_cmd_status("which", &["gamemoded"]) {
            run_cmd_status("gamemoded", &["-d"]);
            println!("  ✅ gamemoded started");
        } else {
            println!("  ⚠  gamemoded not installed");
        }

        run_cmd_status("gsettings", &["set", "org.gnome.desktop.interface", "enable-animations", "false"]);

        println!("  ✅ CPU governors: performance");
        println!("  ✅ Gaming mode: ON");
    } else {
        println!("🎮 Disabling gaming mode...");

        let cpus = std::fs::read_dir("/sys/devices/system/cpu/").unwrap();
        for e in cpus.flatten() {
            let n = e.file_name().to_string_lossy().to_string();
            if n.starts_with("cpu") && n[3..].chars().all(|c| c.is_ascii_digit()) {
                std::fs::write(e.path().join("cpufreq/scaling_governor"), "schedutil").ok();
            }
        }

        std::fs::write("/run/synthex/gaming-mode", "off").ok();
        run_cmd_status("pkill", &["gamemoded"]);
        run_cmd_status("gsettings", &["set", "org.gnome.desktop.interface", "enable-animations", "true"]);

        println!("  ✅ CPU governors: schedutil");
        println!("  ✅ Gaming mode: OFF");
    }
    Ok(())
}

// ─── Update ────────────────────────────────────────────────────────────

fn run_update(check_only: bool, with_snapshot: bool) -> Result<()> {
    if with_snapshot && !check_only {
        println!("📸 Creating pre-update snapshot...");
        run_snapshot("pre-update snapshot")?;
    }

    if check_only {
        println!("🔍 Checking for updates...");
        let output = run_cmd("dnf5", &["check-update"])?;
        let lines: Vec<&str> = output.lines().collect();
        let count = lines.iter()
            .filter(|l| !l.is_empty() && !l.starts_with("Last") && !l.starts_with("Obsoleting"))
            .count();
        if count > 0 {
            println!("  📦 {count} update(s) available:");
            for l in &lines {
                if !l.is_empty() && !l.starts_with("Last") && !l.starts_with("Obsoleting") {
                    println!("    {l}");
                }
            }
        } else {
            println!("  ✅ System is up to date");
        }
    } else {
        println!("⬆️  Applying system updates...");
        let status = Command::new("dnf5")
            .args(["upgrade", "-y"])
            .status()
            .context("Failed to run dnf5 upgrade")?;
        if status.success() {
            println!("  ✅ Updates applied successfully");
        } else {
            println!("  ⚠  Some updates failed — check output above");
        }
    }
    Ok(())
}

// ─── Snapshot ──────────────────────────────────────────────────────────

fn run_snapshot(desc: &str) -> Result<()> {
    println!("📸 Creating snapshot: {desc}");
    let ok = run_cmd_status("snapper", &["-c", "root", "create", "-d", desc]);
    if ok {
        println!("  ✅ Snapshot created successfully");
    } else {
        println!("  ⚠  Snapshot failed — is snapper configured for root?");
        println!("     Run: snapper -c root create-config /");
    }
    Ok(())
}

// ─── Rollback ──────────────────────────────────────────────────────────

fn run_rollback() -> Result<()> {
    println!("⏪ Available snapshots:\n");
    let output = run_cmd("snapper", &["-c", "root", "list", "--columns", "number,date,description"])?;
    println!("{output}");

    println!("To rollback to a specific snapshot:");
    println!("  1. Reboot into a live USB");
    println!("  2. Mount root subvolume:");
    println!("     mount /dev/sda3 /mnt");
    println!("  3. Delete current root subvolume:");
    println!("     btrfs subvolume delete /mnt/@");
    println!("  4. Restore snapshot (replace NUMBER):");
    println!("     btrfs subvolume snapshot /mnt/.snapshots/NUMBER/snapshot /mnt/@");
    println!("  5. Reboot");
    Ok(())
}

// ─── Services ──────────────────────────────────────────────────────────

const SYNTHEX_SERVICES: &[&str] = &[
    "synthex-desktopd", "synthex-hwdaemon", "synthex-gpu-setupd", "synthex-stored",
    "synthex-system-daemon", "synthex-ai-daemon", "synthex-integration-engine",
    "synthex-snapshot-manager", "synthex-gaming-mode", "synthex-auto-tune",
    "synthex-ananicy", "synthex-hermes", "synthex-power-profiles",
];

fn run_services(action: Option<ServiceAction>) -> Result<()> {
    match action {
        None | Some(ServiceAction::List) => {
            println!("\n  🔧 Synthex Services\n");
            println!("  {:<35} {:<10} {:<10}", "Service", "Active", "Enabled");
            println!("  {}", "─".repeat(60));
            for svc in SYNTHEX_SERVICES {
                let unit = format!("{svc}.service");
                let active = run_cmd_status("systemctl", &["is-active", &unit]);
                let enabled = run_cmd_status("systemctl", &["is-enabled", &unit]);
                let icon = if active && enabled { "✅" } else if active { "⚡" } else { "❌" };
                let a_str = if active { "active" } else { "inactive" };
                let e_str = if enabled { "enabled" } else { "disabled" };
                println!("  {icon} {svc:<33} {a_str:<10} {e_str:<10}");
            }
            println!();
        }
        Some(ServiceAction::Status { name }) => {
            let unit = format!("{name}.service");
            let output = run_cmd("systemctl", &["status", &unit])?;
            println!("{output}");
        }
        Some(ServiceAction::Start { name }) => {
            let unit = format!("{name}.service");
            let ok = run_cmd_status("systemctl", &["start", &unit]);
            println!("{}", if ok { format!("✅ Started {name}") } else { format!("❌ Failed to start {name}") });
        }
        Some(ServiceAction::Stop { name }) => {
            let unit = format!("{name}.service");
            let ok = run_cmd_status("systemctl", &["stop", &unit]);
            println!("{}", if ok { format!("✅ Stopped {name}") } else { format!("❌ Failed to stop {name}") });
        }
        Some(ServiceAction::Restart { name }) => {
            let unit = format!("{name}.service");
            let ok = run_cmd_status("systemctl", &["restart", &unit]);
            println!("{}", if ok { format!("✅ Restarted {name}") } else { format!("❌ Failed to restart {name}") });
        }
    }
    Ok(())
}

// ─── Drivers ───────────────────────────────────────────────────────────

fn run_drivers() -> Result<()> {
    println!("\n  🖥  Driver Status\n");
    let hw = hardware::detect_hardware()?;

    println!("  GPUs:");
    for (i, gpu) in hw.gpus.iter().enumerate() {
        let icon = if gpu.driver != "unknown" && gpu.driver != "nouveau" { "✅" } else { "⚠ " };
        println!("    {icon} GPU{i}: {} {} — driver: {}", gpu.vendor, gpu.device, gpu.driver);
    }

    // Check Vulkan
    print!("\n  Vulkan: ");
    let vk = run_cmd_status("vulkaninfo", &["--summary"]);
    println!("{}", if vk { "✅ available" } else { "⚠  not found" });

    // Check NVIDIA
    if let Ok(output) = Command::new("nvidia-smi").arg("--query-gpu=name,driver_version,memory.total").arg("--format=csv,noheader").output() {
        let text = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !text.is_empty() {
            println!("  NVIDIA: ✅ {text}");
        }
    }

    // Check Mesa
    if let Ok(output) = Command::new("glxinfo").args(["-B"]).output() {
        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            if line.contains("OpenGL renderer") || line.contains("OpenGL version") {
                println!("  {}", line.trim());
            }
        }
    }

    println!();
    Ok(())
}

// ─── Logs ──────────────────────────────────────────────────────────────

fn run_logs(service: Option<&str>, lines: usize) -> Result<()> {
    let count = lines.to_string();
    match service {
        Some(svc) => {
            println!("\n  📜 Logs for {svc} (last {lines} lines):\n");
            let output = run_cmd("journalctl", &["-u", svc, "-n", &count, "--no-pager"])?;
            println!("{output}");
        }
        None => {
            println!("\n  📜 Synthex System Logs (last {lines} lines):\n");
            let output = run_cmd("journalctl", &["-b", "-n", &count, "--no-pager", "-o", "short-iso"])?;
            println!("{output}");
        }
    }
    Ok(())
}

// ─── Health ────────────────────────────────────────────────────────────

fn run_health() -> Result<()> {
    println!("🏥 System Health Check\n");
    let mut ok = true;

    let sd = run_cmd_status("systemctl", &["is-system-running"]);
    println!("  {} systemd: {}", if sd { "✅" } else { "⚠ " }, if sd { "running" } else { "degraded" });
    if !sd { ok = false; }

    let pw = run_cmd_status("systemctl", &["is-active", "pipewire.service"]);
    println!("  {} audio (pipewire): {}", if pw { "✅" } else { "⚠ " }, if pw { "active" } else { "inactive" });
    if !pw { ok = false; }

    let net = run_cmd_status("ping", &["-c", "1", "-W", "2", "1.1.1.1"]);
    println!("  {} network: {}", if net { "✅" } else { "⚠ " }, if net { "connected" } else { "no connectivity" });
    if !net { ok = false; }

    if let Ok(meminfo) = std::fs::read_to_string("/proc/meminfo") {
        let mut total = 0u64;
        let mut avail = 0u64;
        for line in meminfo.lines() {
            if let Some(v) = line.strip_prefix("MemTotal:") {
                total = v.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
            }
            if let Some(v) = line.strip_prefix("MemAvailable:") {
                avail = v.split_whitespace().next().unwrap_or("0").parse().unwrap_or(0);
            }
        }
        if total > 0 {
            let used_pct = ((total - avail) * 100) / total;
            let mem_ok = used_pct < 90;
            println!("  {} memory: {used_pct}% used ({} MB / {} MB)",
                if mem_ok { "✅" } else { "⚠ " },
                (total - avail) / 1024, total / 1024);
            if !mem_ok { ok = false; }
        }
    }

    println!();
    if ok {
        println!("  ✅ System is healthy");
    } else {
        println!("  ⚠  Some checks failed — review above");
    }
    Ok(())
}

// ─── Main ──────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Info => println!("{}", status::system_info()),
        Commands::Hardware { json } => {
            let hw = hardware::detect_hardware()?;
            if json { println!("{}", serde_json::to_string_pretty(&hw)?); }
            else { println!("{hw}"); }
        }
        Commands::Gpu { action } => match action {
            GpuAction::List => {
                let hw = hardware::detect_hardware()?;
                for (i, gpu) in hw.gpus.iter().enumerate() {
                    println!("GPU {i}: {} {} ({})", gpu.vendor, gpu.device, gpu.driver);
                }
            }
            GpuAction::Switch { mode } => {
                std::fs::create_dir_all("/run/synthex").ok();
                std::fs::write("/run/synthex/gpu-mode", &mode).ok();
                println!("✅ GPU: {mode} — logout to apply");
            }
        },
        Commands::Status => println!("{}", status::system_info()),
        Commands::Doctor => run_doctor()?,
        Commands::Mode { mode } => run_mode(mode.as_deref())?,
        Commands::Gaming { state } => run_gaming(state.as_deref())?,
        Commands::Update { check, snapshot } => run_update(check, snapshot)?,
        Commands::Snapshot { description } => run_snapshot(&description)?,
        Commands::Rollback => run_rollback()?,
        Commands::Health => run_health()?,
        Commands::Services { action } => run_services(action)?,
        Commands::Drivers => run_drivers()?,
        Commands::Logs { service, lines } => run_logs(service.as_deref(), lines)?,
    }

    Ok(())
}
