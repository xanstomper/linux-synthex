// SPDX-License-Identifier: GPL-3.0-or-later
//! synthex-predictive — Markov-chain predictive application launcher.
//!
//! • Records every application launch into a local JSON database.
//! • Trains an order-3 n-gram Markov chain over the launch sequence.
//! • Falls back to a time-of-day frequency histogram when data is sparse.
//! • Pre-launches the most likely next app (via gtk-launch) once confidence
//!   exceeds a configurable threshold — so the app is ready before you click.
//!
//! All learning is local; the model lives under
//! ~/.local/share/synthex/predictive/.  Nothing leaves the machine.

use anyhow::{Context, Result};
use chrono::{Datelike, Local, Timelike};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::Duration;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

const NGRAM: usize = 3;
const CONF_THRESHOLD: f64 = 0.80;
const TRAIN_EVERY: Duration = Duration::from_secs(3600);
const PRELAUNCH_EVERY: Duration = Duration::from_secs(60);
#[allow(dead_code)]
const STALE_SECS: u64 = 300;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct LaunchEvent {
    ts: i64,
    app: String,
    hour: u32,
    dow: u32,
}

#[derive(Debug, Serialize, Deserialize, Default)]
struct Db {
    events: Vec<LaunchEvent>,
}

#[derive(Default)]
struct Model {
    transitions: HashMap<Vec<String>, HashMap<String, u64>>,
    by_hour: HashMap<u32, HashMap<String, u64>>,
    #[allow(dead_code)]
    total: usize,
}

impl Db {
    fn path() -> PathBuf {
        dirs::data_dir()
            .unwrap_or_else(|| PathBuf::from("/tmp"))
            .join("synthex/predictive/db.json")
    }
    fn load() -> Db {
        let p = Self::path();
        if let Ok(s) = std::fs::read_to_string(&p) {
            serde_json::from_str(&s).unwrap_or_default()
        } else {
            Db::default()
        }
    }
    fn save(&self) -> Result<()> {
        let p = Self::path();
        if let Some(parent) = p.parent() {
            std::fs::create_dir_all(parent).context("create predictive data dir")?;
        }
        std::fs::write(&p, serde_json::to_string_pretty(self)?)
            .context("write predictive db")
    }
    fn record(&mut self, app: &str) {
        let now = Local::now();
        self.events.push(LaunchEvent {
            ts: now.timestamp(),
            app: app.to_string(),
            hour: now.hour(),
            dow: now.weekday().num_days_from_monday(),
        });
        // keep at most 50k events
        if self.events.len() > 50_000 {
            let drop = self.events.len() - 50_000;
            self.events.drain(0..drop);
        }
    }
}

impl Model {
    fn train(db: &Db) -> Model {
        let mut m = Model { total: db.events.len(), ..Default::default() };
        let mut ctx: Vec<String> = Vec::new();
        for ev in &db.events {
            if !ctx.is_empty() {
                let key = ctx.clone();
                let entry = m.transitions.entry(key).or_default();
                *entry.entry(ev.app.clone()).or_default() += 1;
            }
            *m.by_hour.entry(ev.hour).or_default()
                .entry(ev.app.clone())
                .or_default() += 1;
            ctx.push(ev.app.clone());
            if ctx.len() > NGRAM {
                ctx.remove(0);
            }
        }
        m
    }
    fn predict(&self, recent: &[String], top_n: usize) -> Vec<(String, f64)> {
        let ctx: Vec<String> = recent.iter().rev().take(NGRAM).cloned().collect();
        let mut out: Vec<(String, f64)> = Vec::new();
        if let Some(row) = self.transitions.get(&ctx) {
            let total: u64 = row.values().sum();
            if total > 0 {
                for (app, c) in row {
                    out.push((app.clone(), *c as f64 / total as f64));
                }
            }
        }
        if out.is_empty() {
            // time-of-day fallback
            let hour = Local::now().hour();
            if let Some(row) = self.by_hour.get(&hour) {
                let total: u64 = row.values().sum();
                if total > 0 {
                    for (app, c) in row {
                        out.push((app.clone(), *c as f64 / total as f64 * 0.9));
                    }
                }
            }
        }
        out.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        out.truncate(top_n);
        out
    }
}

fn prelaunch(app: &str) {
    info!("pre-launching predicted app: {}", app);
    let _ = std::process::Command::new("gtk-launch").arg(app).spawn();
    // fallback for non-desktop-file app ids
    let _ = std::process::Command::new("xdg-open").arg(app).spawn();
}

async fn run_daemon() -> Result<()> {
    let db = Mutex::new(Db::load());
    let model = Mutex::new(Model::train(&db.lock().unwrap()));
    let mut last_train = std::time::Instant::now();
    let mut last_prelaunch = std::time::Instant::now();

    loop {
        if last_train.elapsed() >= TRAIN_EVERY {
            let d = db.lock().unwrap();
            *model.lock().unwrap() = Model::train(&d);
            last_train = std::time::Instant::now();
            info!("retrained predictive model ({} events)", d.events.len());
        }
        if last_prelaunch.elapsed() >= PRELAUNCH_EVERY {
            let d = db.lock().unwrap();
            let recent: Vec<String> = d.events.iter().rev().take(NGRAM).map(|e| e.app.clone()).collect();
            let preds = model.lock().unwrap().predict(&recent, 2);
            for (app, conf) in preds {
                if conf >= CONF_THRESHOLD {
                    prelaunch(&app);
                }
            }
            last_prelaunch = std::time::Instant::now();
        }
        tokio::time::sleep(Duration::from_secs(15)).await;
    }
}

fn cmd_record(app: &str) -> Result<()> {
    let mut db = Db::load();
    db.record(app);
    db.save()?;
    println!("[predictive] recorded launch: {}", app);
    Ok(())
}

fn cmd_predict(n: usize) -> Result<()> {
    let db = Db::load();
    let model = Model::train(&db);
    let recent: Vec<String> = db.events.iter().rev().take(NGRAM).map(|e| e.app.clone()).collect();
    let preds = model.predict(&recent, n);
    println!("Top {} predictions:", n);
    for (i, (app, conf)) in preds.iter().enumerate() {
        println!("  {}. {}  ({:.0}%)", i + 1, app, conf * 100.0);
    }
    Ok(())
}

fn cmd_status() -> Result<()> {
    let db = Db::load();
    println!("SynthOS Predictive Launcher");
    println!("  Recorded launches : {}", db.events.len());
    println!("  Threshold         : {:.0}%", CONF_THRESHOLD * 100.0);
    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("synthex_predictive=info".parse().unwrap()))
        .init();
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        return run_daemon().await;
    }
    match args[1].as_str() {
        "daemon" => run_daemon().await,
        "record" => {
            if args.len() < 3 { anyhow::bail!("usage: synthex-predictive record <app-id>"); }
            cmd_record(&args[2])
        }
        "predict" => {
            let n: usize = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(5);
            cmd_predict(n)
        }
        "status" => cmd_status(),
        other => {
            warn!("unknown subcommand: {}", other);
            Ok(())
        }
    }
}
