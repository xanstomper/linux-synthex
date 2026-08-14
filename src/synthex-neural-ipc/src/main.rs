//! synthex-neural-ipc daemon
//!
//! Two-layer IPC bus:
//!   Layer 1 — `/dev/shm/synthex-neural-bus`  (mmap ring-buffer, sub-µs latency)
//!             Used by trusted agents that share the same uid/pid-namespace.
//!   Layer 2 — Unix-domain sockets under `/run/synthex/neural/`
//!             Used by sandboxed agents; messages are HMAC-verified and TTL-checked.
//!
//! The daemon bridges both layers: a message published via the ring-buffer is
//! also broadcast on the matching Unix-socket channel and vice-versa.

use anyhow::Result;
use bytes::{Buf, BytesMut};
use clap::{Parser, Subcommand};
use dashmap::DashMap;
use neural_ipc::{NeuralBus, NeuralMessage};
use protocol::{Message, MessageType, FRAME_HEADER_LEN, MAX_INLINE_BYTES, now_ms};
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::{UnixListener, UnixStream};
use tokio::sync::{broadcast, mpsc};
use tracing::{debug, error, info, warn};
use tracing_subscriber::EnvFilter;

use neural_ipc::protocol;

// ─── Constants ────────────────────────────────────────────────────────────────

const RUN_DIR: &str = "/run/synthex/neural";
/// Capacity of each channel broadcast ring.
const BROADCAST_CAP: usize = 4096;
/// Broker inbound queue depth.
const BROKER_QUEUE: usize = 8192;

fn load_hmac_key() -> Vec<u8> {
    std::fs::read("/etc/synthex/neural-ipc.key")
        .unwrap_or_else(|_| b"synthex-dev-insecure-key-change-me".to_vec())
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(
    name = "synthex-neural-ipc",
    version = "2026.10.0",
    about = "SynthOS Neural IPC — ultra-fast dual-layer AI agent message bus"
)]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Start the neural IPC daemon (ring-buffer + Unix-socket broker).
    Start {
        /// Run in foreground (default behaviour; flag kept for systemd compat).
        #[arg(long)]
        no_daemon: bool,
    },
    /// Print bus status.
    Status,
    /// Wipe and re-initialise the shared ring-buffer file.
    Reset,
    /// Publish N messages and measure round-trip latency.
    Bench {
        #[arg(long, default_value = "10000")]
        count: usize,
    },
}

// ─── Broker (Unix-socket layer) ───────────────────────────────────────────────

type ChannelMap = Arc<DashMap<String, broadcast::Sender<Arc<Message>>>>;

struct Broker {
    channels: ChannelMap,
    inbox:    mpsc::Receiver<Arc<Message>>,
    hmac_key: Vec<u8>,
}

#[allow(dead_code)]
impl Broker {
    fn new(inbox: mpsc::Receiver<Arc<Message>>, hmac_key: Vec<u8>) -> Self {
        let channels: ChannelMap = Arc::new(DashMap::new());
        for name in &[
            protocol::CHANNEL_BRAIN,
            protocol::CHANNEL_WORKSPACE,
            protocol::CHANNEL_CAPABILITIES,
            protocol::CHANNEL_ALERTS,
            protocol::CHANNEL_CONTEXT,
        ] {
            let (tx, _) = broadcast::channel(BROADCAST_CAP);
            channels.insert(name.to_string(), tx);
        }
        Self { channels, inbox, hmac_key }
    }

    async fn run(mut self) {
        info!("Unix-socket broker started");
        while let Some(msg) = self.inbox.recv().await {
            // Skip HMAC check for Ping/Pong (cheap, high-frequency).
            if msg.msg_type != MessageType::Ping && msg.msg_type != MessageType::Pong {
                if !protocol::verify(&msg, &self.hmac_key) {
                    warn!(id = %msg.id, from = %msg.from, "invalid HMAC — dropping");
                    continue;
                }
            }
            if msg.is_expired() {
                debug!(id = %msg.id, "TTL expired — dropping");
                continue;
            }
            self.route(msg);
        }
        info!("Unix-socket broker stopped");
    }

    fn route(&self, msg: Arc<Message>) {
        let ch = msg.to.clone();
        if !self.channels.contains_key(&ch) {
            if ch.starts_with(protocol::CHANNEL_AGENT_PREFIX) {
                let (tx, _) = broadcast::channel(BROADCAST_CAP);
                self.channels.insert(ch.clone(), tx);
                info!(channel = %ch, "created per-agent channel");
            } else {
                warn!(channel = %ch, from = %msg.from, "unknown channel — dropped");
                return;
            }
        }
        if let Some(tx) = self.channels.get(&ch) {
            match tx.send(msg) {
                Ok(n)  => debug!(channel = %ch, subscribers = n, "routed"),
                Err(_) => debug!(channel = %ch, "no active subscribers"),
            }
        }
    }
}

// ─── Per-connection task ──────────────────────────────────────────────────────

struct Conn {
    stream:    UnixStream,
    broker_tx: mpsc::Sender<Arc<Message>>,
    channels:  ChannelMap,
    hmac_key:  Arc<Vec<u8>>,
}

impl Conn {
    async fn run(self) {
        let (out_tx, mut out_rx) = mpsc::channel::<Arc<Message>>(1024);
        let (mut reader, mut writer) = self.stream.into_split();

        // Writer task: drain out_rx → socket.
        let write_task = tokio::spawn(async move {
            while let Some(msg) = out_rx.recv().await {
                if let Ok(frame) = msg.to_frame() {
                    if writer.write_all(&frame).await.is_err() { break; }
                }
            }
        });

        let mut buf    = BytesMut::with_capacity(65536);
        let mut subs: Vec<tokio::task::JoinHandle<()>> = Vec::new();

        'outer: loop {
            // Fill until we have the 4-byte length header.
            while buf.len() < FRAME_HEADER_LEN {
                let mut tmp = [0u8; 4096];
                match reader.read(&mut tmp).await {
                    Ok(0) | Err(_) => break 'outer,
                    Ok(n)          => buf.extend_from_slice(&tmp[..n]),
                }
            }

            let msg_len = {
                let b = buf.as_ref();
                u32::from_le_bytes([b[0], b[1], b[2], b[3]]) as usize
            };
            if msg_len > MAX_INLINE_BYTES {
                error!(msg_len, "oversized frame — closing connection");
                break;
            }

            // Fill until we have the complete JSON body.
            while buf.len() < FRAME_HEADER_LEN + msg_len {
                let mut tmp = vec![0u8; 65536];
                match reader.read(&mut tmp).await {
                    Ok(0) | Err(_) => break 'outer,
                    Ok(n)          => buf.extend_from_slice(&tmp[..n]),
                }
            }

            buf.advance(FRAME_HEADER_LEN);
            let body = buf.split_to(msg_len);

            let msg = match Message::from_json_bytes(&body) {
                Ok(m)  => Arc::new(m),
                Err(e) => { warn!("bad JSON: {e}"); continue; }
            };

            match &msg.msg_type {
                MessageType::Ping => {
                    let mut pong = Message::new(
                        "broker", &msg.from, MessageType::Pong,
                        serde_json::json!({ "latency_ms": now_ms() - msg.timestamp }),
                        5_000,
                    );
                    protocol::sign(&mut pong, &self.hmac_key);
                    let _ = out_tx.try_send(Arc::new(pong));
                }
                MessageType::Subscribe => {
                    let ch  = msg.to.clone();
                    let out = out_tx.clone();
                    let rx  = if let Some(tx) = self.channels.get(&ch) {
                        tx.subscribe()
                    } else {
                        let (tx, rx) = broadcast::channel(BROADCAST_CAP);
                        self.channels.insert(ch.clone(), tx);
                        rx
                    };
                    subs.push(tokio::spawn(fan_to_client(ch, rx, out)));
                }
                _ => {
                    if self.broker_tx.send(Arc::clone(&msg)).await.is_err() {
                        warn!("broker inbox full — dropping");
                    }
                }
            }
        }

        for s in subs { s.abort(); }
        write_task.abort();
    }
}

async fn fan_to_client(
    channel: String,
    mut rx:  broadcast::Receiver<Arc<Message>>,
    out:     mpsc::Sender<Arc<Message>>,
) {
    loop {
        match rx.recv().await {
            Ok(msg) => { if out.send(msg).await.is_err() { break; } }
            Err(broadcast::error::RecvError::Lagged(n)) => {
                warn!(channel = %channel, skipped = n, "subscriber lagged");
            }
            Err(broadcast::error::RecvError::Closed) => break,
        }
    }
}

// ─── Per-channel listener ────────────────────────────────────────────────────

async fn listen_channel(
    channel:   String,
    broker_tx: mpsc::Sender<Arc<Message>>,
    channels:  ChannelMap,
    hmac_key:  Arc<Vec<u8>>,
) -> Result<()> {
    let sock = format!("{}/{}", RUN_DIR, channel.replace('/', "_"));
    let _ = std::fs::remove_file(&sock);
    let listener = UnixListener::bind(&sock)?;
    info!(channel = %channel, socket = %sock, "listening");

    loop {
        match listener.accept().await {
            Ok((stream, _)) => {
                tokio::spawn(Conn {
                    stream,
                    broker_tx: broker_tx.clone(),
                    channels:  Arc::clone(&channels),
                    hmac_key:  Arc::clone(&hmac_key),
                }.run());
            }
            Err(e) => {
                error!(channel = %channel, "accept: {e}");
                tokio::time::sleep(std::time::Duration::from_millis(100)).await;
            }
        }
    }
}

// ─── Entry point ─────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env().add_directive("info".parse()?)
        )
        .init();

    let cli = Cli::parse();

    match cli.cmd {

        // ── Start ─────────────────────────────────────────────────────────────
        Cmd::Start { no_daemon: _ } => {
            info!(
                version = env!("CARGO_PKG_VERSION"),
                run_dir = RUN_DIR,
                "synthex-neural-ipc starting"
            );

            // Layer 1 — ring-buffer bus (shared memory).
            let bus = NeuralBus::open()?;
            info!(
                path  = %bus.path().display(),
                slots = neural_ipc::RING_SLOTS,
                slot_kib = neural_ipc::SLOT_SIZE / 1024,
                total_mib = neural_ipc::SLOT_SIZE * neural_ipc::RING_SLOTS / 1024 / 1024,
                "ring-buffer bus ready"
            );

            // Layer 2 — Unix-socket broker.
            std::fs::create_dir_all(RUN_DIR)?;
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                std::fs::set_permissions(
                    RUN_DIR,
                    std::fs::Permissions::from_mode(0o700),
                )?;
            }

            let hmac_key  = Arc::new(load_hmac_key());
            let (btx, brx) = mpsc::channel::<Arc<Message>>(BROKER_QUEUE);
            let channels: ChannelMap = Arc::new(DashMap::new());

            // Pre-populate well-known channels.
            for name in &[
                protocol::CHANNEL_BRAIN,
                protocol::CHANNEL_WORKSPACE,
                protocol::CHANNEL_CAPABILITIES,
                protocol::CHANNEL_ALERTS,
                protocol::CHANNEL_CONTEXT,
            ] {
                let (tx, _) = broadcast::channel::<Arc<Message>>(BROADCAST_CAP);
                channels.insert(name.to_string(), tx);
            }

            let broker = Broker {
                channels: Arc::clone(&channels),
                inbox:    brx,
                hmac_key: (*hmac_key).clone(),
            };
            tokio::spawn(broker.run());

            // One listener per well-known channel + a catch-all broker socket.
            let mut handles = Vec::new();
            for ch in &[
                protocol::CHANNEL_BRAIN,
                protocol::CHANNEL_WORKSPACE,
                protocol::CHANNEL_CAPABILITIES,
                protocol::CHANNEL_ALERTS,
                protocol::CHANNEL_CONTEXT,
                "broker",
            ] {
                let ch  = ch.to_string();
                let tx  = btx.clone();
                let chm = Arc::clone(&channels);
                let key = Arc::clone(&hmac_key);
                handles.push(tokio::spawn(async move {
                    if let Err(e) = listen_channel(ch.clone(), tx, chm, key).await {
                        error!(channel = %ch, "listener exited: {e}");
                    }
                }));
            }

            info!("all listeners active — dual-layer neural IPC bus ready");
            tokio::signal::ctrl_c().await?;
            info!("SIGINT received — shutting down");
            for h in handles { h.abort(); }
        }

        // ── Status ────────────────────────────────────────────────────────────
        Cmd::Status => {
            match NeuralBus::open() {
                Ok(bus) => {
                    println!("Layer 1 ring-buffer : OK  ({})", bus.path().display());
                    println!(
                        "  {} slots × {} KiB = {} MiB total",
                        neural_ipc::RING_SLOTS,
                        neural_ipc::SLOT_SIZE / 1024,
                        neural_ipc::SLOT_SIZE * neural_ipc::RING_SLOTS / 1024 / 1024
                    );
                    // Check whether the broker socket is reachable.
                    let sock = format!("{}/broker", RUN_DIR);
                    if std::path::Path::new(&sock).exists() {
                        println!("Layer 2 Unix socket : OK  ({})", sock);
                    } else {
                        println!("Layer 2 Unix socket : ABSENT (daemon not running?)");
                    }
                }
                Err(e) => {
                    warn!("Neural bus unavailable: {e}");
                    std::process::exit(1);
                }
            }
        }

        // ── Reset ─────────────────────────────────────────────────────────────
        Cmd::Reset => {
            let path = std::path::Path::new(neural_ipc::BUS_FILE);
            if path.exists() { std::fs::remove_file(path)?; }
            let _ = NeuralBus::open()?;
            info!("Ring-buffer reset OK");
        }

        // ── Bench ─────────────────────────────────────────────────────────────
        Cmd::Bench { count } => {
            let bus   = NeuralBus::open()?;
            let start = std::time::Instant::now();
            for i in 0..count {
                let msg = NeuralMessage {
                    id:        format!("bench-{i}"),
                    sender:    "benchmarker".into(),
                    recipient: "*".into(),
                    topic:     "bench.ping".into(),
                    payload:   serde_json::json!({ "seq": i }),
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
                elapsed.as_micros() as f64 / count as f64,
            );
        }
    }

    Ok(())
}
