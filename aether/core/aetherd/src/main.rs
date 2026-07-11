// SPDX-License-Identifier: MIT OR Apache-2.0
//! aetherd — AETHER CORE Central Consciousness Daemon (CCD).
//!
//! The permanent AI-cognition substrate for SynthOS. Agents are temporary
//! workers that never talk to each other directly; they publish/subscribe on
//! the [`event_bus`] and request privileges through the capability [`broker`].
//!
//! Subsystems:
//!   • event_bus   — in-process pub/sub (stands in for NATS)
//!   • memory      — SQLite-backed typed memory graph + hybrid retrieval
//!   • workspace   — live structural model (projects/files/tasks/…)
//!   • planning    — Goal→Objective→Task→Subtask→Action decomposition
//!   • reflection  — after-action review
//!   • broker      — capability tokens, audit log, rate limits, approvals
//!   • agent       — scoped agent identities + registry
//!   • cognitive   — attention / curiosity / consolidation engines
//!   • api         — newline-JSON-over-TCP API + in-process DaemonApi trait
#![allow(dead_code)]

use std::sync::Arc;
use std::time::Duration;

use anyhow::{Context, Result};
use clap::Parser;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

mod agent;
mod api;
mod broker;
mod cognitive;
mod daemon;
mod event_bus;
mod memory;
mod planning;
mod reflection;
mod workspace;

use agent::{AgentIdentity, TrustLevel};
use api::DaemonApi;
use broker::CapabilityToken;
use daemon::Daemon;
use memory::{MemoryGraph, MemoryKind};

/// AETHER CORE Central Consciousness Daemon.
#[derive(Debug, Parser)]
#[command(name = "aetherd", version, about = "AETHER CORE — Central Consciousness Daemon")]
struct Cli {
    /// Path to the SQLite memory database (":memory:" for ephemeral).
    #[arg(long, default_value = "/tmp/aether/memory.db")]
    db_path: String,

    /// TCP address for the JSON-line API server.
    #[arg(long, default_value = "127.0.0.1:8787")]
    listen: String,

    /// Log level (error|warn|info|debug|trace).
    #[arg(long, default_value = "info")]
    log_level: String,

    /// Seconds between curiosity scans.
    #[arg(long, default_value_t = 300)]
    curiosity_secs: u64,

    /// Seconds between memory consolidation passes.
    #[arg(long, default_value_t = 900)]
    consolidate_secs: u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new(format!("aetherd={}", cli.log_level))),
        )
        .init();

    info!("AETHER CORE — Central Consciousness Daemon starting");

    // Ensure the DB directory exists (unless ephemeral).
    if cli.db_path != ":memory:" {
        if let Some(parent) = std::path::Path::new(&cli.db_path).parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("create db dir {}", parent.display()))?;
        }
    }

    let memory = Arc::new(MemoryGraph::open(&cli.db_path).context("open memory graph")?);
    info!(memories = memory.len(), db = %cli.db_path, "memory graph ready");

    let daemon = Arc::new(Daemon::new(memory));

    // Seed a demo agent + bootstrap memories (smoke-test material).
    bootstrap(&daemon)?;

    // Background cognition tasks.
    spawn_event_logger(daemon.clone());
    spawn_curiosity(daemon.clone(), Duration::from_secs(cli.curiosity_secs));
    spawn_consolidator(daemon.clone(), Duration::from_secs(cli.consolidate_secs));
    spawn_aging(daemon.clone());

    // API server.
    let api_daemon = daemon.clone();
    let listen = cli.listen.clone();
    let server = tokio::spawn(async move {
        if let Err(e) = api::serve(api_daemon, &listen).await {
            warn!("API server exited: {e}");
        }
    });

    // Wait for shutdown signal.
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {
            info!("SIGINT received — shutting down");
        }
        _ = server => {
            warn!("API server task ended");
        }
    }

    info!(
        memories = daemon.memory.len(),
        agents = daemon.agents.read().unwrap().len(),
        "AETHER CORE stopped cleanly"
    );
    Ok(())
}


/// Seed a specialised agent and a couple of memories, and demonstrate the
/// in-process [`DaemonApi`] so `cargo run` shows the daemon actually working.
fn bootstrap(daemon: &Arc<Daemon>) -> Result<()> {
    // Register a scoped agent through the registry + broker.
    let agent = AgentIdentity::new("scout-01", "code-research")
        .with_capabilities(vec![CapabilityToken::ReadFile, CapabilityToken::SearchCode])
        .with_trust(TrustLevel::Medium);
    let agent_id = {
        let mut reg = daemon.agents.write().unwrap();
        reg.register(agent)
    };
    {
        let mut broker = daemon.broker.write().unwrap();
        broker.grant(&agent_id, CapabilityToken::ReadFile);
        broker.grant(&agent_id, CapabilityToken::SearchCode);
    }
    daemon.event_bus.publish(event_bus::Event::AgentStarted {
        agent_id: agent_id.clone(),
    });
    info!(%agent_id, "bootstrapped demo agent 'scout-01'");

    // Exercise the DaemonApi trait directly (in-process API smoke test).
    let m1 = daemon.add_memory(
        MemoryKind::Semantic,
        "AETHER CORE is the permanent cognition substrate for SynthOS.".into(),
        Some(0.9),
    )?;
    let m2 = daemon.add_memory(
        MemoryKind::Procedural,
        "Agents must request capabilities via the broker, never act directly.".into(),
        Some(0.8),
    )?;
    daemon
        .memory
        .relate(&m1, &m2, memory::RelationKind::RelatedTo, 1.0)?;

    let goal = daemon.create_goal("Index the SynthOS source tree".into())?;
    info!(%goal, "bootstrapped demo goal");

    let hits = daemon.query_memory("substrate", 5)?;
    info!(results = hits.len(), "in-process query_memory smoke test ok");

    Ok(())
}

/// Log every event flowing across the bus (demonstrates subscription).
fn spawn_event_logger(daemon: Arc<Daemon>) {
    let mut rx = daemon.event_bus.subscribe();
    tokio::spawn(async move {
        loop {
            match rx.recv().await {
                Ok(env) => {
                    info!(seq = env.seq, kind = env.event.kind(), "event");
                }
                Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                    warn!("event logger lagged, dropped {n} events");
                }
                Err(tokio::sync::broadcast::error::RecvError::Closed) => break,
            }
        }
    });
}

/// Periodic curiosity scan: propose investigations as goals.
fn spawn_curiosity(daemon: Arc<Daemon>, every: Duration) {
    tokio::spawn(async move {
        let mut tick = tokio::time::interval(every);
        loop {
            tick.tick().await;
            let proposals = daemon.curiosity.scan(&daemon.memory);
            for ev in proposals {
                let n = daemon.event_bus.publish(ev);
                info!(receivers = n, "curiosity proposed an investigation");
            }
        }
    });
}

/// Periodic memory consolidation: summarise episodic memory into reflections.
fn spawn_consolidator(daemon: Arc<Daemon>, every: Duration) {
    tokio::spawn(async move {
        let mut tick = tokio::time::interval(every);
        loop {
            tick.tick().await;
            match daemon.consolidator.consolidate(&daemon.memory) {
                Ok(Some(id)) => info!(reflection = %id, "memory consolidated"),
                Ok(None) => {}
                Err(e) => warn!("consolidation failed: {e}"),
            }
        }
    });
}

/// Hourly memory aging: decay importance with a 24h half-life.
fn spawn_aging(daemon: Arc<Daemon>) {
    tokio::spawn(async move {
        let mut tick = tokio::time::interval(Duration::from_secs(3600));
        loop {
            tick.tick().await;
            match daemon.memory.age(chrono::Duration::hours(24)) {
                Ok(n) => info!(updated = n, "memory aging pass complete"),
                Err(e) => warn!("aging failed: {e}"),
            }
        }
    });
}
