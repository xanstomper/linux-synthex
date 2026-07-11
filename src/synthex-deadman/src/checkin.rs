// SPDX-License-Identifier: GPL-3.0-or-later
//! synthex-checkin — prove the machine is still attended (Dead Man's Switch).
//!
//! Writes the current epoch seconds to /run/synthex-deadman/last_checkin so the
//! synthex-deadman daemon knows the system has not been abandoned.

use std::time::{SystemTime, UNIX_EPOCH};

fn main() {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let dir = "/run/synthex-deadman";
    std::fs::create_dir_all(dir).ok();
    let path = format!("{}/last_checkin", dir);
    if let Err(e) = std::fs::write(&path, secs.to_string()) {
        eprintln!("synthex-checkin: failed to write {}: {}", path, e);
        std::process::exit(1);
    }
    println!("check-in recorded at epoch {}", secs);
}
