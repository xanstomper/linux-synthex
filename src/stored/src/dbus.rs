// D-Bus interface for solus-stored

use anyhow::Result;
use std::sync::Mutex;
use tracing::info;
use zbus::interface;

use crate::StoreDaemon;

pub struct StoreInterface {
    daemon: Mutex<StoreDaemon>,
}

impl StoreInterface {
    pub fn new(daemon: StoreDaemon) -> Self {
        Self { daemon: Mutex::new(daemon) }
    }
}

#[interface(name = "org.solus.SoftwareCenter")]
impl StoreInterface {
    /// Get available updates
    #[zbus(name = "CheckUpdates")]
    async fn check_updates(&self) -> String {
        match self.daemon.lock() {
            Ok(daemon) => match daemon.check_updates() {
                Ok(info) => serde_json::to_string(&info).unwrap_or_default(),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Run system update
    #[zbus(name = "RunUpdates")]
    async fn run_updates(&self) -> String {
        match self.daemon.lock() {
            Ok(daemon) => match daemon.run_updates() {
                Ok(_) => "ok: update started".into(),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Search packages
    #[zbus(name = "SearchPackages")]
    async fn search_packages(&self, query: &str) -> String {
        match self.daemon.lock() {
            Ok(daemon) => match daemon.search_packages(query) {
                Ok(pkgs) => serde_json::to_string(&pkgs).unwrap_or_default(),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Install package
    #[zbus(name = "InstallPackage")]
    async fn install_package(&self, name: &str) -> String {
        match self.daemon.lock() {
            Ok(daemon) => match daemon.install_package(name) {
                Ok(_) => format!("ok: installed {name}"),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Remove package
    #[zbus(name = "RemovePackage")]
    async fn remove_package(&self, name: &str) -> String {
        match self.daemon.lock() {
            Ok(daemon) => match daemon.remove_package(name) {
                Ok(_) => format!("ok: removed {name}"),
                Err(e) => format!("error: {e}"),
            },
            Err(e) => format!("error: lock failed: {e}"),
        }
    }

    /// Get repository list
    #[zbus(name = "GetRepos")]
    async fn get_repos(&self) -> String {
        match self.daemon.lock() {
            Ok(daemon) => serde_json::to_string(&daemon.repos).unwrap_or_default(),
            Err(_) => "[]".into(),
        }
    }
}

pub async fn run_service(daemon: StoreDaemon) -> Result<()> {
    let interface = StoreInterface::new(daemon);
    let _connection = zbus::ConnectionBuilder::session()?
        .name("org.solus.SoftwareCenter")?
        .interface("org.solus.SoftwareCenter", interface)?
        .build()
        .await?;

    info!("solus-stored D-Bus service running on org.solus.SoftwareCenter");
    std::future::pending::<()>().await;
    Ok(())
}
