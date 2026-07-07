// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-apps — One-command installer for 60+ popular apps

use anyhow::Result;
use clap::Parser;
use colored::*;
use dialoguer::{theme::ColorfulTheme, MultiSelect, Select};
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-apps", version = "0.1.0", about = "Install 60+ popular apps easily")]
struct Cli {
    #[command(subcommand)]
    cmd: AppCommand,
}

#[derive(clap::Subcommand)]
enum AppCommand {
    /// List all available apps
    List,
    /// Install an app by name
    Install { app: String },
    /// Install multiple apps at once (space-separated)
    Batch { apps: Vec<String> },
    /// Interactive numbered menu to pick bundles or individual apps
    Interactive,
    /// Deprecated — use `interactive` instead
    Menu,
    /// Install recommended bundle (brave, discord, vlc, spotify)
    Essentials,
    /// Install gaming bundle (steam, lutris, heroic, gamescope, mangohud, gamemode, protonup, retroarch, discord)
    Gaming,
    /// Install privacy bundle (brave, tor, veracrypt, cryptsetup)
    Privacy,
    /// Install development bundle (vscode, docker, podman, distrobox, neovim, gitkraken, jetbrains)
    Dev,
    /// Install creative bundle (blender, gimp, krita, inkscape, kdenlive, obs, libreoffice, onlyoffice, obsidian)
    Creative,
    /// Install communication bundle (discord, telegram, signal, slack, element, zoom, thunderbird)
    Communication,
    /// Install office bundle (libreoffice, onlyoffice, obsidian, thunderbird, mailspring)
    Office,
    /// Install every single app in the registry
    All,
    /// Install AI & Agents bundle (ollama, hermes, opencode, codex, synthex-agent, open-webui)
    Ai,
    /// Install all 7 browsers
    Browsers,
    /// Install all messaging apps
    Messaging,
    /// Install all multimedia apps (vlc, mpv, obs, kdenlive, spotify, audacity)
    Multimedia,
}

const APPS: &[(&str, &str, &str)] = &[
    // ── Browsers ──
    ("firefox", "Firefox", "dnf install -y firefox"),
    ("brave", "Brave Browser", "flatpak install -y flathub com.brave.Browser 2>/dev/null; dnf install -y brave-browser 2>/dev/null"),
    ("chrome", "Google Chrome", "flatpak install -y flathub com.google.Chrome 2>/dev/null; dnf install -y google-chrome-stable 2>/dev/null"),
    ("tor", "Tor Browser", "flatpak install -y flathub org.torproject.Torbrowser 2>/dev/null; dnf install -y torbrowser-launcher 2>/dev/null"),
    ("edge", "Microsoft Edge", "flatpak install -y flathub com.microsoft.Edge"),
    ("vivaldi", "Vivaldi", "flatpak install -y flathub com.vivaldi.Vivaldi"),
    ("opera", "Opera", "flatpak install -y flathub com.opera.Opera"),
    // ── Messaging ──
    ("discord", "Discord", "flatpak install -y flathub com.discordapp.Discord 2>/dev/null; dnf install -y discord 2>/dev/null"),
    ("telegram", "Telegram", "flatpak install -y flathub org.telegram.desktop 2>/dev/null; dnf install -y telegram-desktop 2>/dev/null"),
    ("signal", "Signal Desktop", "flatpak install -y flathub org.signal.Signal"),
    ("whatsapp", "WhatsApp Desktop", "flatpak install -y flathub io.github.mimbrero.WhatsAppDesktop"),
    ("slack", "Slack", "flatpak install -y flathub com.slack.Slack"),
    ("element", "Element", "flatpak install -y flathub im.riot.Riot"),
    ("zoom", "Zoom", "flatpak install -y flathub us.zoom.Zoom"),
    ("thunderbird", "Thunderbird", "dnf install -y thunderbird"),
    ("mailspring", "Mailspring", "flatpak install -y flathub com.getmailspring.Mailspring"),
    // ── Gaming ──
    ("steam", "Steam", "dnf install -y steam"),
    ("lutris", "Lutris", "dnf install -y lutris"),
    ("heroic", "Heroic Launcher", "flatpak install -y flathub com.heroicgameslauncher.hgl"),
    ("gamescope", "Gamescope", "dnf install -y gamescope"),
    ("mangohud", "MangoHud", "dnf install -y mangohud"),
    ("gamemode", "GameMode", "dnf install -y gamemode"),
    ("protonup", "ProtonUp-Qt", "flatpak install -y flathub net.davidotek.pupgui2"),
    ("retroarch", "RetroArch", "flatpak install -y flathub org.libretro.RetroArch"),
    // ── Multimedia ──
    ("vlc", "VLC Media Player", "dnf install -y vlc"),
    ("mpv", "MPV Player", "dnf install -y mpv"),
    ("obs", "OBS Studio", "dnf install -y obs-studio"),
    ("kdenlive", "Kdenlive Video Editor", "dnf install -y kdenlive"),
    ("spotify", "Spotify", "flatpak install -y flathub com.spotify.Client 2>/dev/null; dnf install -y spotify-client 2>/dev/null"),
    ("audacity", "Audacity", "dnf install -y audacity"),
    // ── Creative ──
    ("blender", "Blender 3D", "dnf install -y blender"),
    ("gimp", "GIMP Image Editor", "dnf install -y gimp"),
    ("krita", "Krita Painting", "dnf install -y krita"),
    ("inkscape", "Inkscape Vector Editor", "dnf install -y inkscape"),
    ("libreoffice", "LibreOffice", "dnf install -y libreoffice"),
    ("onlyoffice", "OnlyOffice", "flatpak install -y flathub org.onlyoffice.desktopeditors"),
    ("obsidian", "Obsidian Notes", "flatpak install -y flathub md.obsidian.Obsidian"),
    // ── Development ──
    ("vscode", "VS Code", "flatpak install -y flathub com.visualstudio.code 2>/dev/null; dnf install -y code 2>/dev/null"),
    ("docker", "Docker", "dnf install -y docker-ce docker-ce-cli containerd.io 2>/dev/null; dnf install -y docker 2>/dev/null"),
    ("podman", "Podman", "dnf install -y podman"),
    ("distrobox", "Distrobox", "dnf install -y distrobox"),
    ("gitkraken", "GitKraken", "flatpak install -y flathub com.axosoft.GitKraken"),
    ("neovim", "Neovim", "dnf install -y neovim"),
    ("jetbrains", "JetBrains IntelliJ IDEA", "flatpak install -y flathub com.jetbrains.IntelliJ-IDEA-Community"),
    // ── AI & Agents ──
    ("ollama", "Ollama", "curl -fsSL https://ollama.com/install.sh | sh"),
    ("hermes", "Hermes AI", "pip install hermes-cli 2>/dev/null; cargo install hermes-cli 2>/dev/null"),
    ("opencode", "OpenCode", "npm install -g @opencode/cli 2>/dev/null; pip install opencode-cli 2>/dev/null"),
    ("codex", "Codex CLI", "pip install codex-cli 2>/dev/null; npm install -g @openai/codex 2>/dev/null"),
    ("synthex-agent", "Synthex Agent", "cargo install synthex-agent 2>/dev/null; pip install synthex-agent 2>/dev/null"),
    ("open-webui", "Open WebUI", "pip install open-webui 2>/dev/null; docker pull ghcr.io/open-webui/open-webui:main 2>/dev/null"),
    // ── Utilities ──
    ("syncthing", "Syncthing", "dnf install -y syncthing"),
    ("qbittorrent", "qBittorrent", "dnf install -y qbittorrent"),
    ("gparted", "GParted", "dnf install -y gparted"),
    ("btop", "Btop", "dnf install -y btop"),
    ("fastfetch", "Fastfetch", "dnf install -y fastfetch"),
    ("tmux", "Tmux", "dnf install -y tmux"),
    ("neofetch", "Neofetch", "dnf install -y neofetch"),
    ("wireshark", "Wireshark", "dnf install -y wireshark"),
    ("veracrypt", "VeraCrypt", "dnf install -y veracrypt 2>/dev/null; flatpak install -y flathub org.veracrypt.VeraCrypt 2>/dev/null"),
    ("cryptsetup", "Cryptsetup", "dnf install -y cryptsetup"),
];

fn banner(msg: &str, color: Color) {
    println!();
    println!(
        "{} {}",
        "═══".bold().color(color),
        msg.bold().color(color)
    );
    println!();
}

fn step(msg: impl AsRef<str>) {
    println!("  {} {}", "▶".cyan().bold(), msg.as_ref().bold());
}

fn success(msg: impl AsRef<str>) {
    println!("  {} {}", "✓".green().bold(), msg.as_ref().green());
}

fn failure(msg: impl AsRef<str>) {
    eprintln!("  {} {}", "✗".red().bold(), msg.as_ref().red());
}

fn skipped(msg: impl AsRef<str>) {
    println!("  {} {}", "⚠".yellow().bold(), msg.as_ref().yellow());
}

fn install(id: &str) -> Result<()> {
    if let Some((_, name, cmd)) = APPS.iter().find(|(i, _, _)| *i == id) {
        step(format!("Installing {} ({})…", name, id));
        let status = Command::new("sh").args(["-c", cmd]).status()?;
        if status.success() {
            success(format!("{} installed", id));
        } else {
            failure(format!("{} failed (exit {})", id, status));
        }
    } else {
        failure(format!("Unknown app: {}", id));
        skipped("Run 'synthex-apps list' to see available apps.");
    }
    Ok(())
}

fn install_bundle(name: &str, ids: &[&str]) -> Result<()> {
    banner(&format!("Installing {}", name), Color::Blue);
    for id in ids {
        install(id)?;
    }
    success(format!("{} complete", name));
    Ok(())
}

fn run_interactive() -> Result<()> {
    let theme = ColorfulTheme::default();
    let bundle_names = &[
        "📦 Essentials",
        "🎮 Gaming",
        "🛡️  Privacy",
        "💻 Development",
        "🎨 Creative",
        "💬 Communication",
        "📄 Office",
        "🤖 AI & Agents",
        "🌐 All Browsers",
        "✉️ All Messaging",
        "🎵 All Multimedia",
        "📋 Individual apps…",
    ];
    let bundles: &[&[&str]] = &[
        &["brave", "discord", "vlc", "spotify"],
        &["steam", "lutris", "heroic", "gamescope", "mangohud", "gamemode", "protonup", "retroarch", "discord"],
        &["brave", "tor", "veracrypt", "cryptsetup"],
        &["vscode", "docker", "podman", "distrobox", "neovim", "gitkraken", "jetbrains"],
        &["blender", "gimp", "krita", "inkscape", "kdenlive", "obs", "libreoffice", "onlyoffice", "obsidian"],
        &["discord", "telegram", "signal", "slack", "element", "zoom", "thunderbird"],
        &["libreoffice", "onlyoffice", "obsidian", "thunderbird", "mailspring"],
        &["ollama", "hermes", "opencode", "codex", "synthex-agent", "open-webui"],
        &["firefox", "brave", "chrome", "tor", "edge", "vivaldi", "opera"],
        &["discord", "telegram", "signal", "whatsapp", "slack", "element", "zoom", "thunderbird", "mailspring"],
        &["vlc", "mpv", "obs", "kdenlive", "spotify", "audacity"],
    ];

    banner("Interactive Installer", Color::Green);
    let selection = Select::with_theme(&theme)
        .with_prompt("Pick a bundle or choose individual apps")
        .items(bundle_names)
        .default(0)
        .interact()?;

    if selection == bundle_names.len() - 1 {
        // Individual apps via MultiSelect
        let app_names: Vec<String> = APPS.iter().map(|(_, n, _)| n.to_string()).collect();
        let chosen = MultiSelect::with_theme(&theme)
            .with_prompt("Select apps to install (space to toggle, enter to confirm)")
            .items(&app_names)
            .interact()?;
        if chosen.is_empty() {
            skipped("No apps selected.");
            return Ok(());
        }
        let app_ids: Vec<&str> = chosen.iter().map(|&i| APPS[i].0).collect();
        for id in &app_ids {
            install(id)?;
        }
    } else {
        install_bundle(bundle_names[selection], bundles[selection])?;
    }

    println!();
    success("All selected installations finished.");
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        AppCommand::List => {
            banner("Available Apps (60+)", Color::Green);
            println!("  {:<22} {}", "ID".bold(), "Name".bold());
            println!("  {}", "─".repeat(54));
            for (id, name, _) in APPS {
                println!("  {:<22} {}", id.green(), name);
            }
            println!();
            println!("{}", "Usage: synthex-apps install <id>".yellow());
            println!("{}", "       synthex-apps batch <id1> <id2> …".yellow());
            println!("{}", "       synthex-apps interactive".yellow());
            println!("{}", "       synthex-apps browsers | messaging | multimedia | ai".yellow());
        }
        AppCommand::Install { app } => {
            banner(&format!("Installing {}", app), Color::Cyan);
            install(&app)?;
        }
        AppCommand::Batch { apps } => {
            if apps.is_empty() {
                failure("No apps specified.");
                skipped("Usage: synthex-apps batch brave discord steam");
                return Ok(());
            }
            banner("Batch Install", Color::Magenta);
            for app in &apps {
                install(app)?;
            }
        }
        AppCommand::Interactive | AppCommand::Menu => {
            run_interactive()?;
        }
        AppCommand::Essentials => {
            install_bundle("Essentials Bundle", &["brave", "discord", "vlc", "spotify"])?;
        }
        AppCommand::Gaming => {
            install_bundle("Gaming Bundle", &["steam", "lutris", "heroic", "gamescope", "mangohud", "gamemode", "protonup", "retroarch", "discord"])?;
        }
        AppCommand::Privacy => {
            install_bundle("Privacy Bundle", &["brave", "tor", "veracrypt", "cryptsetup"])?;
        }
        AppCommand::Dev => {
            install_bundle("Development Bundle", &["vscode", "docker", "podman", "distrobox", "neovim", "gitkraken", "jetbrains"])?;
        }
        AppCommand::Creative => {
            install_bundle("Creative Bundle", &["blender", "gimp", "krita", "inkscape", "kdenlive", "obs", "libreoffice", "onlyoffice", "obsidian"])?;
        }
        AppCommand::Communication => {
            install_bundle("Communication Bundle", &["discord", "telegram", "signal", "slack", "element", "zoom", "thunderbird"])?;
        }
        AppCommand::Office => {
            install_bundle("Office Bundle", &["libreoffice", "onlyoffice", "obsidian", "thunderbird", "mailspring"])?;
        }
        AppCommand::All => {
            banner("Full Install — Every App in the Registry", Color::BrightYellow);
            step(format!("{} apps to install…", APPS.len()));
            for (id, _, _) in APPS {
                install(id)?;
            }
        }
        AppCommand::Ai => {
            install_bundle("AI & Agents Bundle", &["ollama", "hermes", "opencode", "codex", "synthex-agent", "open-webui"])?;
        }
        AppCommand::Browsers => {
            install_bundle("All Browsers", &["firefox", "brave", "chrome", "tor", "edge", "vivaldi", "opera"])?;
        }
        AppCommand::Messaging => {
            install_bundle("All Messaging Apps", &["discord", "telegram", "signal", "whatsapp", "slack", "element", "zoom", "thunderbird", "mailspring"])?;
        }
        AppCommand::Multimedia => {
            install_bundle("All Multimedia Apps", &["vlc", "mpv", "obs", "kdenlive", "spotify", "audacity"])?;
        }
    }
    Ok(())
}
