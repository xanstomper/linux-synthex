//! SynthOS Welcome Application
//!
//! Launched automatically by the firstboot service on first login.
//! Presents a multi-page wizard to guide the user through:
//!   - Desktop profile selection
//!   - App bundle installation
//!   - Network configuration
//!   - Tips & tricks
//!
//! Uses QML for the UI, launched via a subprocess wrapper.
//! Writes `~/.config/synthex/welcome-done` on completion.

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::{Command, exit};

fn state_file() -> PathBuf {
    let config = env::var("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from(env::var("HOME").unwrap_or_default()).join(".config"));
    config.join("synthex").join("welcome-done")
}

fn mark_complete() {
    if let Some(parent) = state_file().parent() {
        fs::create_dir_all(parent).ok();
    }
    fs::write(state_file(), b"").ok();
}

fn already_done() -> bool {
    state_file().exists()
}

fn main() {
    let args: Vec<String> = env::args().collect();

    // --force bypasses the already-done check
    let force = args.contains(&"--force".to_string());

    if already_done() && !force {
        eprintln!("synthex-welcome: already completed (remove ~/.config/synthex/welcome-done to re-run)");
        exit(0);
    }

    // Launch the QML UI
    let qml_file = "/usr/share/synthex/welcome/Main.qml";

    let status = Command::new("qml")
        .args([qml_file])
        .status()
        .or_else(|_| {
            // Fallback: try qmlscene (Qt5 hosts)
            Command::new("qmlscene")
                .args([qml_file])
                .status()
        });

    match status {
        Ok(s) if s.success() => {
            mark_complete();
        }
        Ok(s) => {
            eprintln!("synthex-welcome: QML exited with status {:?}", s.code());
            // Still mark complete so we don't re-launch on crash
            mark_complete();
            exit(s.code().unwrap_or(1));
        }
        Err(e) => {
            eprintln!("synthex-welcome: failed to launch QML runtime: {e}");
            eprintln!("Install: sudo dnf install qt6-qtdeclarative-devel");
            exit(127);
        }
    }
}
