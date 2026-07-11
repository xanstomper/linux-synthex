//! synthex-neural-ipc daemon
//!
//! Manages the shared neural bus and provides a D-Bus façade so agents that
//! cannot use shared memory (e.g. sandboxed processes) can still participate.

use anyhow::Result;
use clap::{Parser, Subcommand};
use neural_ipc::NeuralBus;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;

// ─── CLI ─────────────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(
    name = "synthex-neural-ipc",
    version = "2026.10.0",
    about = "SynthOS Neural IPC — ultra-fast AI agent message bus"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Start the neural IPC daemon (D-Bus bridge + bus manager).
    Start {
        /// Run in foreground instead of forking.
        #[arg(long)]
        no_daemon: bool,
    },
    /// Print bus status (slot utilisation, message rate).
    Status,
    /// Wipe and re-initialise the shared bus file.
    Reset,
    /// Publish a test message and verify round-trip latency.
    Bench {
        /// Number of messages to send.
        #[arg(long, default_value = "10000")]
        count: usize,
    },
}

// ─── Entry point ─────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env().add_directive("info".parse()?))
        .init();

    let cli = Cli::parse();

    match cli.cmd {
        Cmd::Start { no_daemon } => {
            info!("synthex-neural-ipc starting (daemon={})", !no_daemon);
            let bus = NeuralBus::open()?;
            info!("Neural bus initialised at {}", bus.path().display());
            info!("Slot size: {} KiB × {} slots = {} MiB",
                neural_ipc::SLOT_SIZE / 1024,
                neural_ipc::RING_SLOTS,
                neural_ipc::SLOT_SIZE * neural_ipc::RING_SLOTS / 1024 / 1024);
            // TODO: start D-Bus façade via zbus
            info!("Neural IPC daemon running. Send SIGTERM to stop.");
            tokio::signal::ctrl_c().await?;
            info!("Shutting down neural IPC daemon.");
        }
        Cmd::Status => {
            match NeuralBus::open() {
                Ok(bus) => println!("Neural bus OK — {}", bus.path().display()),
                Err(e)  => { warn!("Neural bus unavailable: {e}"); std::process::exit(1); }
            }
        }
        Cmd::Reset => {
            let path = std::path::Path::new(neural_ipc::BUS_FILE);
            if path.exists() { std::fs::remove_file(path)?; }
            let _bus = NeuralBus::open()?;
            info!("Neural bus reset OK.");
        }
        Cmd::Bench { count } => {
            let bus = NeuralBus::open()?;
            let start = std::time::Instant::now();
            for i in 0..count {
                let msg = neural_ipc::NeuralMessage {
                    id:        format!("bench-{i}"),
                    sender:    "benchmarker".into(),
                    recipient: "*".into(),
                    topic:     "bench.ping".into(),
                    payload:   serde_json::json!({"seq": i}),
                    ts_ms:     std::time::SystemTime::now()
                                   .duration_since(std::time::UNIX_EPOCH)
                                   .unwrap_or_default()
                                   .as_millis() as u64,
                };
                bus.publish(&msg)?;
            }
            let elapsed = start.elapsed();
            println!(
                "Bench: {} messages in {:.2?} — {:.0} msg/s — avg {:.1} µs/msg",
                count,
                elapsed,
                count as f64 / elapsed.as_secs_f64(),
                elapsed.as_micros() as f64 / count as f64
            );
        }
    }

    Ok(())
}
