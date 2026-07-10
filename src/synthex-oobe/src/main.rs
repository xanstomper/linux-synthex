//! SynthOS Out-of-Box Experience (OOBE)
//!
//! Runs inside the Calamares installer as a QML wizard page.
//! Called by the `synthexprofile` Calamares module to show the
//! desktop profile picker before partitioning begins.
//!
//! This binary wraps the QML UI and writes the selected profile
//! to the GlobalStorage key `synthexProfile` so Calamares can
//! read it during the EXEC phase.

use std::collections::HashMap;
use std::env;
use std::io::{self, Write};
use std::process::{Command, Stdio};

const QML_UI: &str = "/usr/share/calamares/synthex-oobe/Main.qml";

fn main() {
    let args: Vec<String> = env::args().collect();

    // --list-profiles → print JSON list and exit (used by synthexprofile module)
    if args.contains(&"--list-profiles".to_string()) {
        let profiles = serde_json::json!([
            { "id": "classic",  "name": "Classic Desktop",   "de": "KDE Plasma" },
            { "id": "focus",    "name": "Focus Mode",        "de": "KDE Plasma (minimal panels)" },
            { "id": "gaming",   "name": "Gaming Optimized",  "de": "KDE Plasma + gaming stack" },
            { "id": "pro",      "name": "Pro Workstation",   "de": "KDE Plasma + dev tools" },
            { "id": "studio",   "name": "Studio",            "de": "KDE Plasma + creative apps" },
            { "id": "lite",     "name": "Lite",              "de": "KDE Plasma (lightweight)" },
            { "id": "ai",       "name": "AI Workstation",    "de": "KDE Plasma + local LLM" },
        ]);
        println!("{}", serde_json::to_string_pretty(&profiles).unwrap());
        return;
    }

    // Launch QML UI and capture the selected profile from stdout
    let mut child = Command::new("qml")
        .args([QML_UI])
        .stdout(Stdio::piped())
        .spawn()
        .expect("Failed to launch OOBE QML — is qt6-qtdeclarative installed?");

    let output = child.wait_with_output().expect("OOBE process failed");

    if output.status.success() {
        let selected = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !selected.is_empty() {
            // Write to GlobalStorage via stdout (Calamares module reads this)
            println!("SYNTHEX_PROFILE={selected}");
        }
    } else {
        eprintln!("OOBE UI exited with error — defaulting to 'classic' profile");
        println!("SYNTHEX_PROFILE=classic");
    }
}
