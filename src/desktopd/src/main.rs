// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-desktopd — Desktop layout/theme/mode engine for SynthOS
//
// Manages KDE Plasma layouts (Mint, Windows, macOS, gaming, minimal),
// applies system themes, switches SDDM greeter themes, and controls
// desktop mode transitions. Rust rewrite of the C++ daemon.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use tracing::{error, info, warn};

mod dbus;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct LayoutConfig {
    pub name: String,
    pub display_name: String,
    pub description: String,
    pub panel_config: String,
    pub theme: String,
    pub sddm_theme: Option<String>,
    pub icon_theme: String,
    pub cursor_theme: String,
    pub fonts: HashMap<String, String>,
    pub wallpaper: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct DesktopState {
    pub current_layout: String,
    pub theme_mode: ThemeMode,
    pub panel_height: u32,
    pub transparency: f32,
}

#[derive(Serialize, Deserialize, Debug, Clone, Copy, PartialEq)]
pub enum ThemeMode {
    Light,
    Dark,
    Auto,
}

impl Default for LayoutConfig {
    fn default() -> Self {
        Self {
            name: "mint".into(),
            display_name: "Synthex Mint".into(),
            description: "Classic Mint-style layout with bottom panel".into(),
            panel_config: "synthex-mint".into(),
            theme: "synthex-mint-dark".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus-Dark".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-mint-dark".into(),
        }
    }
}

pub struct DesktopDaemon {
    state: DesktopState,
    layouts: HashMap<String, LayoutConfig>,
}

impl DesktopDaemon {
    pub fn new() -> Self {
        let mut layouts = HashMap::new();

        layouts.insert("mint".into(), LayoutConfig {
            name: "mint".into(),
            display_name: "Synthex Mint".into(),
            description: "Classic Mint-style layout with bottom panel, window list, green Mint-Y theme".into(),
            panel_config: "synthex-mint".into(),
            theme: "synthex-mint-dark".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus-Dark".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-mint-dark".into(),
        });

        layouts.insert("windows".into(), LayoutConfig {
            name: "windows".into(),
            display_name: "Windows 11".into(),
            description: "Windows 11-style layout with centered taskbar, Windows key shortcuts".into(),
            panel_config: "windows-11".into(),
            theme: "synthex-windows".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-dark-4k".into(),
        });

        layouts.insert("gaming".into(), LayoutConfig {
            name: "gaming".into(),
            display_name: "Gaming".into(),
            description: "Minimal layout for gaming — clean desktop, GameMode integration".into(),
            panel_config: "gaming".into(),
            theme: "synthex-gaming".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus-Dark".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-gaming".into(),
        });

        layouts.insert("macos".into(), LayoutConfig {
            name: "macos".into(),
            display_name: "macOS".into(),
            description: "macOS-style layout with global menu, dock, top bar".into(),
            panel_config: "macos".into(),
            theme: "synthex-mac".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-dark-4k".into(),
        });

        layouts.insert("minimal".into(), LayoutConfig {
            name: "minimal".into(),
            display_name: "Minimal".into(),
            description: "Minimal layout for power users — slim panel, no widgets".into(),
            panel_config: "minimal".into(),
            theme: "synthex-minimal".into(),
            sddm_theme: Some("synthex-sddm".into()),
            icon_theme: "Papirus".into(),
            cursor_theme: "Synthex-Cursor".into(),
            fonts: HashMap::new(),
            wallpaper: "/usr/share/wallpapers/synthex-dark-4k".into(),
        });

        Self {
            state: DesktopState {
                current_layout: "mint".into(),
                theme_mode: ThemeMode::Dark,
                panel_height: 48,
                transparency: 0.9,
            },
            layouts,
        }
    }

    pub fn apply_layout(&mut self, name: &str) -> Result<()> {
        let layout = self.layouts.get(name)
            .with_context(|| format!("Unknown layout: {name}"))?;

        info!("Applying layout: {} ({})", layout.display_name, layout.name);
        self.state.current_layout = name.to_string();

        // Apply Plasma layout via config script
        let script = format!("/usr/share/synthex/scripts/apply-layout.sh");
        if Path::new(&script).exists() {
            let output = std::process::Command::new("bash")
                .args([&script, name])
                .output()?;
            if !output.status.success() {
                warn!("apply-layout.sh exited with error");
            }
        } else {
            // Write layout config for other tools to pick up
            let config_dir = Path::new("/run/synthex/desktop");
            std::fs::create_dir_all(config_dir)?;
            let layout_json = serde_json::to_string_pretty(layout)?;
            std::fs::write(config_dir.join("current-layout.json"), &layout_json)?;

            // Write Plasma config if writable config files exist
            let plasma_config = format!(
                "[Panels][Panel-1]\nposition=bottom\nheight={}\nfloating=false\n",
                self.state.panel_height
            );
            let config_path = dirs::home_dir()
                .map(|h| h.join(".config/plasma-org.kde.plasma.desktop-appletsrc"));
            if let Some(path) = config_path {
                let _ = std::fs::write(&path, &plasma_config);
            }
        }

        info!("Layout applied: {}", name);
        Ok(())
    }

    pub fn set_theme_mode(&mut self, mode: ThemeMode) -> Result<()> {
        info!("Setting theme mode: {mode:?}");
        self.state.theme_mode = mode;

        // Apply via lookandfeeltool (KDE) or write config
        match mode {
            ThemeMode::Dark => {
                let _ = std::process::Command::new("lookandfeeltool")
                    .args(["-a", "org.synthex.desktop.dark"])
                    .status();
            }
            ThemeMode::Light => {
                let _ = std::process::Command::new("lookandfeeltool")
                    .args(["-a", "org.synthex.desktop.light"])
                    .status();
            }
            ThemeMode::Auto => {
                // Schedule day/night transition
                let _ = std::process::Command::new("lookandfeeltool")
                    .args(["-a", "org.synthex.desktop.dark"])
                    .status();
            }
        }

        // Write state
        let _ = std::fs::create_dir_all("/run/synthex/desktop");
        let state_json = serde_json::to_string_pretty(&self.state)?;
        std::fs::write("/run/synthex/desktop/state.json", &state_json)?;

        Ok(())
    }

    pub fn get_layout(&self, name: &str) -> Option<&LayoutConfig> {
        self.layouts.get(name)
    }

    pub fn list_layouts(&self) -> Vec<&LayoutConfig> {
        self.layouts.values().collect()
    }
}

fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "synthex_desktopd=info".into()),
        )
        .init();

    info!("Synthex Desktop Daemon starting");
    let mut daemon = DesktopDaemon::new();

    // Apply default layout
    if let Err(e) = daemon.apply_layout("mint") {
        error!("Failed to apply default layout: {e:#}");
    }

    // Start D-Bus service
    let rt = tokio::runtime::Runtime::new()?;
    rt.block_on(async {
        if let Err(e) = dbus::run_service(daemon).await {
            error!("D-Bus service exited: {e:#}");
        }
    });

    Ok(())
}
