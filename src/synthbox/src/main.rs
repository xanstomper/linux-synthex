use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::{
    collections::HashMap,
    fs,
    path::PathBuf,
    process::Command,
};

const PROFILES_FILE: &str = "/etc/synthbox/profiles.json";
const LOG_DIR: &str = "/var/log/synthbox";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Profile {
    name: String,
    net: bool,
    dirs: Vec<String>,
    exec: Vec<String>,
    desc: String,
    ipc: bool,
    dbus: bool,
    x11: bool,
    wayland: bool,
    devices: Vec<String>,
    env_blacklist: Vec<String>,
}

impl Default for Profile {
    fn default() -> Self {
        Self {
            name: String::new(),
            net: false,
            dirs: Vec::new(),
            exec: Vec::new(),
            desc: String::new(),
            ipc: false,
            dbus: false,
            x11: false,
            wayland: false,
            devices: Vec::new(),
            env_blacklist: vec!["DISPLAY".into(), "WAYLAND_DISPLAY".into(), "DBUS_SESSION_BUS_ADDRESS".into()],
        }
    }
}

fn builtin_profiles() -> HashMap<&'static str, Profile> {
    let mut m = HashMap::new();
    m.insert("browser", Profile {
        name: "browser".into(), net: true,
        dirs: vec!["$HOME/Downloads".into()],
        exec: vec!["firefox".into(), "chromium".into(), "brave".into()],
        desc: "Web browser (network + downloads only)".into(),
        ipc: false, dbus: false, x11: true, wayland: true,
        devices: vec![], env_blacklist: vec!["DBUS_SESSION_BUS_ADDRESS".into()],
    });
    m.insert("gaming", Profile {
        name: "gaming".into(), net: true,
        dirs: vec!["$HOME/.steam".into(), "$HOME/Games".into(), "$HOME/.local/share/Steam".into()],
        exec: vec!["steam".into(), "lutris".into(), "heroic".into()],
        desc: "Gaming (full GPU + network access)".into(),
        ipc: true, dbus: false, x11: true, wayland: true,
        devices: vec!["/dev/dri".into(), "/dev/input".into()], env_blacklist: vec![],
    });
    m.insert("office", Profile {
        name: "office".into(), net: true,
        dirs: vec!["$HOME/Documents".into(), "$HOME/Desktop".into()],
        exec: vec!["libreoffice".into(), "onlyoffice".into()],
        desc: "Office suite (document access + network)".into(),
        ipc: false, dbus: false, x11: true, wayland: true,
        devices: vec![], env_blacklist: vec![],
    });
    m.insert("dev", Profile {
        name: "dev".into(), net: true,
        dirs: vec!["$HOME/projects".into(), "$HOME/.config".into(), "/tmp".into()],
        exec: vec!["code".into(), "rustc".into(), "gcc".into(), "python".into(), "node".into()],
        desc: "Development (full access)".into(),
        ipc: true, dbus: true, x11: true, wayland: true,
        devices: vec![], env_blacklist: vec![],
    });
    m.insert("media", Profile {
        name: "media".into(), net: false,
        dirs: vec!["$HOME/Videos".into(), "$HOME/Music".into(), "$HOME/Pictures".into()],
        exec: vec!["vlc".into(), "mpv".into(), "spotify".into(), "firefox".into()],
        desc: "Media player (no network)".into(),
        ipc: false, dbus: false, x11: true, wayland: true,
        devices: vec![], env_blacklist: vec!["DBUS_SESSION_BUS_ADDRESS".into()],
    });
    m.insert("untrusted", Profile {
        name: "untrusted".into(), net: false,
        dirs: vec!["$HOME/Downloads".into()],
        exec: vec![],
        desc: "Untrusted app (maximum isolation)".into(),
        ipc: false, dbus: false, x11: false, wayland: false,
        devices: vec![], env_blacklist: vec!["DISPLAY", "WAYLAND_DISPLAY", "DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"].iter().map(|s| s.to_string()).collect(),
    });
    m
}

#[derive(Parser)]
#[command(name = "synthbox", about = "SynthBox - Sandboxed Application Runner")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    Run {
        app: String,
        #[arg(trailing_var_arg = true)]
        args: Vec<String>,
    },
    List,
    Create {
        name: String,
        #[arg(long)]
        net: bool,
        #[arg(long, action = clap::ArgAction::Append)]
        dir: Vec<String>,
    },
    Profiles,
    DryRun {
        app: String,
    },
}

fn ensure_dir(path: &str) -> Result<()> {
    let p = PathBuf::from(path);
    if !p.exists() {
        fs::create_dir_all(&p)?;
    }
    Ok(())
}

fn load_custom() -> Result<Vec<Profile>> {
    let p = PathBuf::from(PROFILES_FILE);
    if !p.exists() { return Ok(vec![]); }
    Ok(serde_json::from_str(&fs::read_to_string(&p)?)?)
}

fn save_custom(v: &[Profile]) -> Result<()> {
    let p = PathBuf::from(PROFILES_FILE);
    if let Some(par) = p.parent() { fs::create_dir_all(par)?; }
    let json = serde_json::to_string_pretty(v)?;
    fs::write(&p, json)?;
    Ok(())
}

fn find_profile(name: &str) -> Option<Profile> {
    let builtins = builtin_profiles();
    builtins.get(name).cloned().or_else(|| load_custom().ok()?.into_iter().find(|p| p.name == name))
}

fn build_bwrap_args(prof: &Profile, app: &str, extra_args: &[String]) -> Vec<String> {
    let mut args: Vec<String> = Vec::new();
    // Core isolation
    args.push("--unshare-all".into());
    args.push("--die-with-parent".into());
    // Filesystem: read-only base
    args.extend(["--ro-bind".into(), "/usr".into(), "/usr".into()]);
    args.extend(["--ro-bind".into(), "/etc".into(), "/etc".into()]);
    args.extend(["--ro-bind".into(), "/lib".into(), "/lib".into()]);
    args.extend(["--ro-bind".into(), "/lib64".into(), "/lib64".into()]);
    args.extend(["--ro-bind".into(), "/bin".into(), "/bin".into()]);
    args.extend(["--ro-bind".into(), "/sbin".into(), "/sbin".into()]);
    // Proc and dev
    args.extend(["--proc".into(), "/proc".into()]);
    args.extend(["--dev".into(), "/dev".into()]);
    args.extend(["--tmpfs".into(), "/tmp".into()]);
    args.extend(["--tmpfs".into(), "/run".into()]);
    // Home directory (read-write for the app)
    if let Ok(home) = std::env::var("HOME") {
        args.extend(["--bind".into(), home.clone(), home]);
    }
    // Shared directories from profile
    for dir in &prof.dirs {
        let expanded = dir.replace("$HOME", &std::env::var("HOME").unwrap_or_default());
        let pb = PathBuf::from(&expanded);
        if pb.exists() {
            if prof.net || prof.name == "dev" {
                args.extend(["--bind".into(), expanded.clone(), expanded]);
            } else {
                args.extend(["--ro-bind".into(), expanded.clone(), expanded]);
            }
        }
    }
    // Network
    if prof.net {
        args.push("--share-net".into());
    } else {
        // Explicitly deny network
        args.push("--unshare-net".into());
    }
    // IPC
    if prof.ipc {
        args.push("--share-ipc".into());
    }
    // Devices
    for dev in &prof.devices {
        if PathBuf::from(dev).exists() {
            args.extend(["--dev-bind".into(), dev.clone(), dev.clone()]);
        }
    }
    // Environment sanitization
    args.push("--clearenv".into());
    // Set safe defaults
    args.extend(["--setenv".into(), "PATH".into(), "/usr/local/bin:/usr/bin:/bin".into()]);
    args.extend(["--setenv".into(), "HOME".into(), std::env::var("HOME").unwrap_or_else(|_| "/tmp".into())]);
    args.extend(["--setenv".into(), "LANG".into(), std::env::var("LANG").unwrap_or_else(|_| "en_US.UTF-8".into())]);
    // X11 / Wayland passthrough
    if prof.x11 {
        if let Ok(display) = std::env::var("DISPLAY") {
            args.extend(["--setenv".into(), "DISPLAY".into(), display]);
        }
        if let Ok(xauth) = std::env::var("XAUTHORITY") {
            args.extend(["--ro-bind".into(), xauth.clone(), xauth]);
        }
    }
    if prof.wayland {
        if let Ok(wd) = std::env::var("WAYLAND_DISPLAY") {
            args.extend(["--setenv".into(), "WAYLAND_DISPLAY".into(), wd]);
        }
        if let Ok(xdg) = std::env::var("XDG_RUNTIME_DIR") {
            let wayland_sock = PathBuf::from(&xdg).join("wayland-0");
            if wayland_sock.exists() {
                args.extend(["--ro-bind".into(), xdg.clone(), xdg]);
            }
        }
    }
    // D-Bus (only for trusted profiles)
    if prof.dbus {
        if let Ok(dbus) = std::env::var("DBUS_SESSION_BUS_ADDRESS") {
            args.extend(["--setenv".into(), "DBUS_SESSION_BUS_ADDRESS".into(), dbus]);
        }
    }
    // Determine the actual binary to run
    let binary = prof.exec.first().map(|s| s.as_str()).unwrap_or(app);
    // Check if binary exists
    let which_output = Command::new("which").arg(binary).output();
    match which_output {
        Ok(o) if o.status.success() => {
            let path = String::from_utf8_lossy(&o.stdout).trim().to_string();
            args.push(path);
        }
        _ => {
            // Try running directly
            args.push(binary.to_string());
        }
    }
    // Pass extra arguments
    args.extend(extra_args.iter().cloned());
    args
}

fn cmd_run(app: &str, extra_args: &[String]) -> Result<()> {
    let prof = find_profile(app)
        .with_context(|| format!("Unknown profile '{}'. Use 'synthbox list' to see available profiles.", app))?;
    println!("  \x1b[96mSynthBox\x1b[0m -- Running '\x1b[93m{}\x1b[0m' with profile '\x1b[92m{}\x1b[0m'", app, prof.name);
    println!("  Net: {}  IPC: {}  X11: {}  Wayland: {}", if prof.net{"allowed"}else{"BLOCKED"}, if prof.ipc{"allowed"}else{"BLOCKED"}, if prof.x11{"allowed"}else{"BLOCKED"}, if prof.wayland{"allowed"}else{"BLOCKED"});
    println!("  Dirs: {}", prof.dirs.join(", "));
    // Check if bwrap is available
    if Command::new("which").arg("bwrap").output().map(|o| !o.status.success()).unwrap_or(true) {
        println!("  \x1b[91mbwrap not found. Install bubblewrap: 'sudo dnf install bubblewrap'\x1b[0m");
        println!("  \x1b[93m[dry-run] Would run: {}\x1b[0m", prof.exec.first().map(|s| s.as_str()).unwrap_or(app));
        return Ok(());
    }
    let bwrap_args = build_bwrap_args(&prof, app, extra_args);
    println!("  \x1b[90mExecuting: bwrap {}\x1b[0m\n", bwrap_args.join(" "));
    let status = Command::new("bwrap")
        .args(&bwrap_args)
        .status()
        .with_context(|| "Failed to execute bwrap")?;
    if !status.success() {
        println!("  \x1b[93mProcess exited with code {}\x1b[0m", status.code().unwrap_or(-1));
    }
    Ok(())
}

fn cmd_list() -> Result<()> {
    println!("  \x1b[95mBuilt-in Profiles:\x1b[0m\n");
    for (_, p) in builtin_profiles() {
        println!("    \x1b[96m{:<14}\x1b[0m net={:<5} ipc={:<5} {}", p.name, p.net, p.ipc, p.desc);
    }
    let custom = load_custom()?;
    if !custom.is_empty() {
        println!("\n  \x1b[93mCustom Profiles:\x1b[0m\n");
        for p in &custom {
            println!("    \x1b[93m{:<14}\x1b[0m net={:<5} ipc={:<5} {}", p.name, p.net, p.ipc, p.desc);
        }
    }
    println!();
    Ok(())
}

fn cmd_create(name: &str, net: bool, dirs: &[String]) -> Result<()> {
    if builtin_profiles().contains_key(name) {
        anyhow::bail!("'{}' is a built-in profile. Choose a different name.", name);
    }
    let mut custom = load_custom()?;
    if custom.iter().any(|p| p.name == name) {
        anyhow::bail!("Profile '{}' already exists.", name);
    }
    custom.push(Profile {
        name: name.into(),
        net,
        dirs: dirs.to_vec(),
        exec: vec![name.into()],
        desc: format!("Custom: net={} dirs={}", net, dirs.len()),
        ipc: false, dbus: false, x11: true, wayland: true,
        devices: vec![], env_blacklist: vec![],
    });
    save_custom(&custom)?;
    println!("  \x1b[92m+ Created profile '{}' (net={}, dirs=[{}])\x1b[0m\n", name, net, dirs.join(", "));
    Ok(())
}

fn cmd_dry_run(app: &str) -> Result<()> {
    let prof = find_profile(app)
        .with_context(|| format!("Unknown profile '{}'", app))?;
    println!("  \x1b[96mDry Run: {}\x1b[0m (profile: {})\n", app, prof.name);
    let bwrap_args = build_bwrap_args(&prof, app, &[]);
    println!("  bwrap \\");
    for (i, arg) in bwrap_args.iter().enumerate() {
        if i < bwrap_args.len() - 1 {
            println!("    {} \\", arg);
        } else {
            println!("    {}", arg);
        }
    }
    println!();
    Ok(())
}

fn main() -> Result<()> {
    ensure_dir(LOG_DIR)?;
    match Cli::parse().command {
        Commands::Run { app, args } => cmd_run(&app, &args),
        Commands::List => cmd_list(),
        Commands::Create { name, net, dir } => cmd_create(&name, net, &dir),
        Commands::Profiles => cmd_list(),
        Commands::DryRun { app } => cmd_dry_run(&app),
    }
}
