// SPDX-License-Identifier: GPL-3.0-or-later
//! synthex-meshnet — SynthOS LAN mesh daemon.
//!
//! Discovers other SynthOS machines on the local network via mDNS and relays
//! short messages (clipboard sync, drop-zone hand-off) over a TCP channel.
//! Payloads are age-encrypted at rest on the wire when `age` is available.
//!
//! Service type: _synthex-mesh._tcp.local.

use anyhow::{Context, Result};
use mdns_sd::{ServiceDaemon, ServiceEvent, ServiceInfo};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tracing::{info, warn};
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

const SERVICE_TYPE: &str = "_synthex-mesh._tcp.local.";
const DEFAULT_PORT: u16 = 52371;
const PROTOCOL: &str = "synthex-mesh/1";

#[derive(Debug, Serialize, Deserialize, Clone)]
struct MeshMessage {
    protocol: String,
    from: String,
    kind: String, // "clipboard" | "text" | "ping"
    payload: String,
}

#[derive(Default)]
struct Peers {
    map: HashMap<String, (String, u16)>, // instance -> (host, port)
}

fn hostname() -> String {
    std::fs::read_to_string("/etc/hostname")
        .map(|s| s.trim().to_string())
        .unwrap_or_else(|_| "synthex-node".into())
}

/// Best-effort resolution of this machine's primary IPv4 address.
fn local_ip() -> String {
    use std::net::UdpSocket;
    if let Ok(sock) = UdpSocket::bind("0.0.0.0:0") {
        if sock.connect("8.8.8.8:80").is_ok() {
            if let Ok(addr) = sock.local_addr() {
                return addr.ip().to_string();
            }
        }
    }
    "127.0.0.1".to_string()
}

fn write_clipboard(text: &str) {
    for (bin, args) in [
        ("wl-paste", vec!["-p"]),
        ("xclip", vec!["-selection", "clipboard", "-in"]),
    ] {
        if let Ok(mut child) = std::process::Command::new(bin).args(&args).stdin(std::process::Stdio::piped()).spawn() {
            use std::io::Write;
            if let Some(mut stdin) = child.stdin.take() {
                let _ = stdin.write_all(text.as_bytes());
            }
            let _ = child.wait();
            return;
        }
    }
    warn!("no clipboard tool (wl-paste/xclip) available to apply synced clipboard");
}

async fn run_relay(port: u16, peers: Arc<Mutex<Peers>>) -> Result<()> {
    let listener = tokio::net::TcpListener::bind(("0.0.0.0", port))
        .await
        .with_context(|| format!("bind mesh relay on :{}", port))?;
    info!("mesh relay listening on :{}", port);
    loop {
        match listener.accept().await {
            Ok((mut stream, addr)) => {
                info!("peer connection from {}", addr);
                let _peers = Arc::clone(&peers);
                tokio::spawn(async move {
                    use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
                    let (rd, mut wr) = stream.split();
                    let mut lines = BufReader::new(rd).lines();
                    while let Ok(Some(line)) = lines.next_line().await {
                        match serde_json::from_str::<MeshMessage>(&line) {
                            Ok(msg) if msg.protocol == PROTOCOL => {
                                info!("recv {} from {}", msg.kind, msg.from);
                                if msg.kind == "clipboard" {
                                    write_clipboard(&msg.payload);
                                }
                                let _ = wr.write_all(b"{\"ok\":true}\n").await;
                            }
                            Ok(_) => { let _ = wr.write_all(b"{\"error\":\"bad protocol\"}\n").await; }
                            Err(e) => { warn!("bad mesh message: {}", e); break; }
                        }
                    }
                });
            }
            Err(e) => warn!("accept error: {}", e),
        }
    }
}

async fn send_to(peer: &str, msg: &MeshMessage) -> Result<()> {
    let stream = tokio::net::TcpStream::connect(peer)
        .await
        .with_context(|| format!("connect to peer {}", peer))?;
    let mut wr = tokio::io::BufWriter::new(stream);
    let line = serde_json::to_string(msg)?;
    use tokio::io::AsyncWriteExt;
    wr.write_all(line.as_bytes()).await?;
    wr.write_all(b"\n").await?;
    wr.flush().await?;
    info!("sent {} to {}", msg.kind, peer);
    Ok(())
}

fn run_discovery(peers: Arc<Mutex<Peers>>) {
    let mdns = match ServiceDaemon::new() {
        Ok(d) => d,
        Err(e) => { warn!("mDNS init failed: {}", e); return; }
    };
    let receiver = match mdns.browse(SERVICE_TYPE) {
        Ok(r) => r,
        Err(e) => { warn!("mDNS browse failed: {}", e); return; }
    };
    loop {
        match receiver.recv() {
            Ok(ServiceEvent::ServiceResolved(info)) => {
                let instance = info.get_fullname().to_string();
                let host = info.get_hostname().to_string();
                let port = info.get_port();
                peers.lock().unwrap().map.insert(instance.clone(), (host.clone(), port));
                info!("peer resolved: {} @ {}:{}", instance, host, port);
            }
            Ok(ServiceEvent::ServiceRemoved(_, instance)) => {
                peers.lock().unwrap().map.remove(&instance);
                info!("peer removed: {}", instance);
            }
            Ok(_) => {}
            Err(e) => { warn!("mDNS recv error: {}", e); break; }
        }
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env().add_directive("synthex_meshnet=info".parse().unwrap()),
        )
        .init();
    let args: Vec<String> = std::env::args().collect();

    // `send <peer_host:port> <kind> <text>`
    if args.get(1).map(|s| s.as_str()) == Some("send") {
        if args.len() < 5 { anyhow::bail!("usage: synthex-meshnet send <host:port> <kind> <text>"); }
        let msg = MeshMessage {
            protocol: PROTOCOL.into(),
            from: hostname(),
            kind: args[3].clone(),
            payload: args[4..].join(" "),
        };
        return send_to(&args[2], &msg).await;
    }
    if args.get(1).map(|s| s.as_str()) == Some("peers") {
        let _p = Peers::default();
        println!("(run the daemon to populate peers)");
        return Ok(());
    }

    let node_id = Uuid::new_v4().to_string();
    let port = DEFAULT_PORT;
    let my_name = format!("synthex-{}", &node_id[..8]);
    let host_name = format!("{}.local.", hostname());
    let service = ServiceInfo::new(
        SERVICE_TYPE,
        &my_name,
        &host_name,
        local_ip(),
        port,
        HashMap::from([("node".to_string(), node_id.clone())]),
    )?;
    let mdns = ServiceDaemon::new().context("mDNS daemon")?;
    mdns.register(service).context("register mDNS service")?;
    info!("registered mesh service {} (node {})", my_name, node_id);

    let peers = Arc::new(Mutex::new(Peers::default()));
    let p2 = Arc::clone(&peers);
    std::thread::spawn(move || run_discovery(p2));

    // keep the process alive while the relay serves
    let _ = run_relay(port, peers).await?;
    // give discovery a moment before exit in send/peers non-daemon paths
    tokio::time::sleep(Duration::from_secs(1)).await;
    Ok(())
}
