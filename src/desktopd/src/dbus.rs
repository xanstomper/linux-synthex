// D-Bus interface for solus-desktopd

use anyhow::Result;
use std::sync::Mutex;
use tracing::info;
use zbus::connection::Builder;
use zbus::interface;

use crate::{DesktopDaemon, ThemeMode};

pub struct DesktopInterface {
    daemon: Mutex<DesktopDaemon>,
}

impl DesktopInterface {
    pub fn new(daemon: DesktopDaemon) -> Self {
        Self { daemon: Mutex::new(daemon) }
    }
}

#[interface(name = "org.solus.Desktop")]
impl DesktopInterface {
    /// Apply a desktop layout by name
    #[zbus(name = "ApplyLayout")]
    async fn apply_layout(&self, name: &str) -> String {
        match self.daemon.lock() {
            Ok(mut daemon) => match daemon.apply_layout(name) {
                Ok(_) => format!("ok: applied layout '{name}'"),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Set theme mode (dark, light, auto)
    #[zbus(name = "SetThemeMode")]
    async fn set_theme_mode(&self, mode: &str) -> String {
        let theme = match mode {
            "dark" => ThemeMode::Dark,
            "light" => ThemeMode::Light,
            "auto" => ThemeMode::Auto,
            _ => return format!("error: unknown mode '{mode}'"),
        };
        match self.daemon.lock() {
            Ok(mut daemon) => match daemon.set_theme_mode(theme) {
                Ok(_) => format!("ok: theme set to '{mode}'"),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// List available layouts
    #[zbus(name = "ListLayouts")]
    async fn list_layouts(&self) -> Vec<String> {
        match self.daemon.lock() {
            Ok(daemon) => {
                daemon.list_layouts().iter().map(|l| format!("{}: {}", l.name, l.display_name)).collect()
            }
            Err(_) => vec![],
        }
    }

    /// Get current layout name
    #[zbus(property, name = "CurrentLayout")]
    async fn current_layout(&self) -> String {
        self.daemon.lock().map(|d| d.state.current_layout.clone()).unwrap_or_default()
    }
}

pub async fn run_service(daemon: DesktopDaemon) -> Result<()> {
    let interface = DesktopInterface::new(daemon);
    let _connection = Builder::session()?
        .name("org.solus.Desktop")?
        .serve_at("/org/solus/Desktop", interface)?
        .build()
        .await?;

    info!("solus-desktopd D-Bus service running on org.solus.Desktop");
    std::future::pending::<()>().await;
    Ok(())
}
