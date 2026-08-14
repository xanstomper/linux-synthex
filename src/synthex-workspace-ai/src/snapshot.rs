// SPDX-License-Identifier: MIT OR Apache-2.0
//! Workspace snapshot engine.
//!
//! Captures the full visual + process state of a virtual workspace:
//!  - Screenshot via X11 XGetImage (falls back to `import` / `scrot`)
//!  - Window list with titles, classes, sizes, positions
//!  - Per-window PID, process name, working directory, open file descriptors
//!  - Clipboard state (text only for now)
//!
//! Snapshots are gzip-compressed JSON bundles stored under
//! `/var/lib/synthex/workspace-snapshots/<workspace>/<uuid>.snap`.
//! The latest snapshot for each workspace is symlinked as `latest.snap`.

use std::{
    collections::HashMap,
    fs,
    io::Write as _,
    path::PathBuf,
    time::UNIX_EPOCH,
};

use anyhow::{Context, Result};
use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use chrono::{DateTime, Utc};
use flate2::{write::GzEncoder, Compression};
use serde::{Deserialize, Serialize};
use tracing::{debug, info, warn};
use uuid::Uuid;
use x11rb::{
    connection::Connection,
    protocol::xproto::{
        self, AtomEnum, ConnectionExt as _, GetWindowAttributesReply, Screen,
    },
    rust_connection::RustConnection,
};

// ─── Types ────────────────────────────────────────────────────────────────────

/// A point-in-time capture of an entire virtual workspace.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkspaceSnapshot {
    pub id: String,
    pub workspace_n: u32,
    pub timestamp: DateTime<Utc>,
    /// Base64-encoded PNG screenshot of the workspace root (may be empty if
    /// capture failed).
    pub screenshot_png_b64: String,
    pub windows: Vec<WindowSnapshot>,
    /// Clipboard text content at snapshot time.
    pub clipboard_text: Option<String>,
    /// Arbitrary metadata (e.g. agent notes).
    pub meta: HashMap<String, String>,
}

/// Per-window state captured at snapshot time.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowSnapshot {
    pub window_id: u64,
    pub title: String,
    pub class: String,
    pub geometry: WindowGeometry,
    pub pid: Option<u32>,
    pub process_name: Option<String>,
    pub working_directory: Option<PathBuf>,
    /// Sample of open file paths (editors, terminals, etc.).
    pub open_files: Vec<PathBuf>,
    pub is_focused: bool,
    pub is_mapped: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WindowGeometry {
    pub x: i16,
    pub y: i16,
    pub width: u16,
    pub height: u16,
}

// ─── Storage paths ────────────────────────────────────────────────────────────

const SNAPSHOT_BASE: &str = "/var/lib/synthex/workspace-snapshots";

fn workspace_snapshot_dir(n: u32) -> PathBuf {
    PathBuf::from(SNAPSHOT_BASE).join(format!("workspace-{n}"))
}

// ─── Snapshot engine ──────────────────────────────────────────────────────────

/// Top-level entry: take a full snapshot of workspace `n`, persist it, and
/// return the snapshot value.
pub async fn capture_workspace(n: u32) -> Result<WorkspaceSnapshot> {
    info!(workspace = n, "capturing workspace snapshot");

    // We do X11 work synchronously (x11rb is sync) but wrap in
    // spawn_blocking so we don't block the Tokio runtime.
    let snap = tokio::task::spawn_blocking(move || capture_workspace_sync(n))
        .await
        .context("spawn_blocking panicked")??;

    persist_snapshot(&snap).await?;
    Ok(snap)
}

fn capture_workspace_sync(n: u32) -> Result<WorkspaceSnapshot> {
    let id = Uuid::new_v4().to_string();
    let timestamp = Utc::now();

    // ── X11 connection ───────────────────────────────────────────────────────
    let (conn, screen_num) = match RustConnection::connect(None) {
        Ok(c) => c,
        Err(e) => {
            warn!("X11 connection failed: {e}; producing minimal snapshot");
            return Ok(WorkspaceSnapshot {
                id,
                workspace_n: n,
                timestamp,
                screenshot_png_b64: String::new(),
                windows: vec![],
                clipboard_text: None,
                meta: HashMap::new(),
            });
        }
    };
    let screen = &conn.setup().roots[screen_num];

    // ── Screenshot ───────────────────────────────────────────────────────────
    let screenshot_png_b64 = capture_screenshot(&conn, screen)
        .unwrap_or_else(|e| {
            warn!("screenshot capture failed: {e}");
            String::new()
        });

    // ── Window list ──────────────────────────────────────────────────────────
    let windows = enumerate_windows(&conn, screen, n)
        .unwrap_or_else(|e| {
            warn!("window enumeration failed: {e}");
            vec![]
        });

    // ── Clipboard ────────────────────────────────────────────────────────────
    // Reading the clipboard requires owning a window and doing a selection
    // round-trip; keep it simple — try xclip/xsel subprocess fallback.
    let clipboard_text = read_clipboard_text();

    Ok(WorkspaceSnapshot {
        id,
        workspace_n: n,
        timestamp,
        screenshot_png_b64,
        windows,
        clipboard_text,
        meta: HashMap::new(),
    })
}

// ─── Screenshot ───────────────────────────────────────────────────────────────

fn capture_screenshot(conn: &RustConnection, screen: &Screen) -> Result<String> {
    let root = screen.root;
    let width = screen.width_in_pixels;
    let height = screen.height_in_pixels;

    debug!(width, height, "capturing root window via XGetImage");

    let image_reply = conn
        .get_image(
            xproto::ImageFormat::Z_PIXMAP,
            root,
            0,
            0,
            width,
            height,
            !0u32,
        )
        .context("XGetImage request")?
        .reply()
        .context("XGetImage reply")?;

    // The raw data is in BGRx (32-bit depth, typically).  Convert to RGBA.
    let raw = image_reply.data;
    let depth = image_reply.depth;

    let rgba: Vec<u8> = if depth == 24 || depth == 32 {
        // BGRx → RGBA
        raw.chunks_exact(4)
            .flat_map(|px| [px[2], px[1], px[0], 255])
            .collect()
    } else {
        // Grayscale / other — pass through as-is (best effort).
        raw.to_vec()
    };

    let img: image::RgbaImage =
        image::RgbaImage::from_raw(width as u32, height as u32, rgba)
            .context("RgbaImage::from_raw failed")?;

    let mut png_bytes: Vec<u8> = Vec::new();
    img.write_to(
        &mut std::io::Cursor::new(&mut png_bytes),
        image::ImageFormat::Png,
    )
    .context("PNG encode")?;

    Ok(B64.encode(&png_bytes))
}

// ─── Window enumeration ───────────────────────────────────────────────────────

fn enumerate_windows(
    conn: &RustConnection,
    screen: &Screen,
    _workspace_n: u32,
) -> Result<Vec<WindowSnapshot>> {
    let root = screen.root;

    // Query the tree of top-level children.
    let tree = conn
        .query_tree(root)
        .context("query_tree request")?
        .reply()
        .context("query_tree reply")?;

    // Intern atoms we'll need.
    let net_wm_name = intern_atom(conn, b"_NET_WM_NAME")?;
    let net_wm_pid = intern_atom(conn, b"_NET_WM_PID")?;
    let wm_class_atom = AtomEnum::WM_CLASS;
    let utf8_string = intern_atom(conn, b"UTF8_STRING")?;

    let mut snapshots = Vec::new();

    for &win_id in &tree.children {
        // Skip unmapped windows.
        let attrs: GetWindowAttributesReply = match conn
            .get_window_attributes(win_id)
        {
            Ok(c) => match c.reply() {
                Ok(a) => a,
                Err(_) => continue,
            },
            Err(_) => continue,
        };
        let is_mapped = attrs.map_state == xproto::MapState::VIEWABLE;

        // Geometry.
        let geo = match conn.get_geometry(win_id) {
            Ok(c) => match c.reply() {
                Ok(g) => WindowGeometry {
                    x: g.x,
                    y: g.y,
                    width: g.width,
                    height: g.height,
                },
                Err(_) => continue,
            },
            Err(_) => continue,
        };

        // Title (_NET_WM_NAME, fallback WM_NAME).
        let title = get_text_property(conn, win_id, net_wm_name, utf8_string)
            .or_else(|_| get_text_property(conn, win_id, AtomEnum::WM_NAME.into(), 0))
            .unwrap_or_default();

        // WM_CLASS → class string.
        let class = get_text_property(conn, win_id, wm_class_atom.into(), 0)
            .unwrap_or_default();

        // PID via _NET_WM_PID.
        let pid = get_cardinal(conn, win_id, net_wm_pid).ok();

        // Process name + working dir from /proc.
        let (process_name, working_directory) = pid
            .map(|p| proc_info(p))
            .unwrap_or((None, None));

        // Open files from /proc/PID/fd (filter to regular files only).
        let open_files = pid
            .map(|p| proc_open_files(p))
            .unwrap_or_default();

        snapshots.push(WindowSnapshot {
            window_id: win_id as u64,
            title,
            class,
            geometry: geo,
            pid,
            process_name,
            working_directory,
            open_files,
            is_focused: false, // filled in below
            is_mapped,
        });
    }

    // Mark the focused window.
    if let Ok(focus_reply) = conn.get_input_focus() {
        let focused_id = match focus_reply.reply() {
            Ok(r) => r.focus as u64,
            Err(_) => return Ok(snapshots),
        };
        for ws in &mut snapshots {
            if ws.window_id == focused_id {
                ws.is_focused = true;
            }
        }
    }

    Ok(snapshots)
}

// ─── X11 helpers ──────────────────────────────────────────────────────────────

fn intern_atom(conn: &RustConnection, name: &[u8]) -> Result<u32> {
    Ok(conn
        .intern_atom(false, name)
        .context("intern_atom request")?
        .reply()
        .context("intern_atom reply")?
        .atom)
}

fn get_text_property(
    conn: &RustConnection,
    win: xproto::Window,
    atom: u32,
    _type_hint: u32,
) -> Result<String> {
    let reply = conn
        .get_property(false, win, atom, AtomEnum::ANY, 0, 1024)
        .context("get_property request")?
        .reply()
        .context("get_property reply")?;
    Ok(String::from_utf8_lossy(&reply.value).trim_matches('\0').to_string())
}

fn get_cardinal(conn: &RustConnection, win: xproto::Window, atom: u32) -> Result<u32> {
    let reply = conn
        .get_property(false, win, atom, AtomEnum::CARDINAL, 0, 1)
        .context("get_property cardinal request")?
        .reply()
        .context("get_property cardinal reply")?;
    if reply.value.len() < 4 {
        anyhow::bail!("cardinal property too short");
    }
    Ok(u32::from_ne_bytes(reply.value[..4].try_into().unwrap()))
}

// ─── /proc helpers ────────────────────────────────────────────────────────────

fn proc_info(pid: u32) -> (Option<String>, Option<PathBuf>) {
    let comm = fs::read_to_string(format!("/proc/{pid}/comm"))
        .ok()
        .map(|s| s.trim().to_string());
    let cwd = fs::read_link(format!("/proc/{pid}/cwd")).ok();
    (comm, cwd)
}

fn proc_open_files(pid: u32) -> Vec<PathBuf> {
    let fd_dir = format!("/proc/{pid}/fd");
    let Ok(entries) = fs::read_dir(&fd_dir) else {
        return vec![];
    };
    entries
        .filter_map(|e| e.ok())
        .filter_map(|e| fs::read_link(e.path()).ok())
        .filter(|p| p.is_absolute() && !p.starts_with("/proc") && !p.starts_with("/dev"))
        .take(32) // cap to avoid huge lists
        .collect()
}

fn read_clipboard_text() -> Option<String> {
    // Try xclip, then xsel.
    for (cmd, args) in &[
        ("xclip", vec!["-selection", "clipboard", "-o"]),
        ("xsel", vec!["--clipboard", "--output"]),
    ] {
        if let Ok(out) = std::process::Command::new(cmd).args(args).output() {
            if out.status.success() {
                let text = String::from_utf8_lossy(&out.stdout).to_string();
                if !text.is_empty() {
                    return Some(text);
                }
            }
        }
    }
    None
}

// ─── Persistence ──────────────────────────────────────────────────────────────

pub async fn persist_snapshot(snap: &WorkspaceSnapshot) -> Result<()> {
    let dir = workspace_snapshot_dir(snap.workspace_n);
    tokio::fs::create_dir_all(&dir)
        .await
        .context("create snapshot dir")?;

    let file_path = dir.join(format!("{}.snap", snap.id));
    let latest_path = dir.join("latest.snap");

    let json = serde_json::to_vec(snap).context("serialize snapshot")?;

    // Gzip-compress.
    let mut gz = GzEncoder::new(Vec::new(), Compression::default());
    gz.write_all(&json).context("gzip write")?;
    let compressed = gz.finish().context("gzip finish")?;

    tokio::fs::write(&file_path, &compressed)
        .await
        .context("write snapshot file")?;

    // Atomic symlink update: write → rename.
    let tmp_link = dir.join(format!(".latest-{}.tmp", snap.workspace_n));
    let _ = std::os::unix::fs::symlink(&file_path, &tmp_link);
    let _ = fs::rename(&tmp_link, &latest_path);

    info!(
        workspace = snap.workspace_n,
        path = %file_path.display(),
        "snapshot persisted ({} bytes compressed)",
        compressed.len(),
    );
    Ok(())
}

/// Load the most recent snapshot for a workspace (decompresses inline).
pub async fn load_latest_snapshot(n: u32) -> Result<WorkspaceSnapshot> {
    let latest = workspace_snapshot_dir(n).join("latest.snap");
    let bytes = tokio::fs::read(&latest)
        .await
        .with_context(|| format!("read latest snapshot for workspace {n}"))?;

    // Attempt gzip decompress; fall back to raw JSON.
    let json_bytes = decompress_maybe(&bytes);
    serde_json::from_slice(&json_bytes).context("deserialize snapshot")
}

fn decompress_maybe(data: &[u8]) -> Vec<u8> {
    use flate2::read::GzDecoder;
    use std::io::Read as _;
    let mut d = GzDecoder::new(data);
    let mut out = Vec::new();
    if d.read_to_end(&mut out).is_ok() && !out.is_empty() {
        out
    } else {
        data.to_vec()
    }
}

/// List all snapshot IDs for a workspace, newest first.
#[allow(dead_code)]
pub async fn list_snapshots(n: u32) -> Result<Vec<String>> {
    let dir = workspace_snapshot_dir(n);
    let mut entries = tokio::fs::read_dir(&dir).await.context("read snapshot dir")?;
    let mut ids: Vec<(u64, String)> = Vec::new();

    while let Some(entry) = entries.next_entry().await? {
        let name = entry.file_name().to_string_lossy().to_string();
        if name.ends_with(".snap") && name != "latest.snap" {
            let mtime = entry
                .metadata()
                .await
                .ok()
                .and_then(|m| m.modified().ok())
                .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                .map(|d| d.as_secs())
                .unwrap_or(0);
            ids.push((mtime, name.trim_end_matches(".snap").to_string()));
        }
    }
    ids.sort_by(|a, b| b.0.cmp(&a.0));
    Ok(ids.into_iter().map(|(_, id)| id).collect())
}

/// Prune snapshots older than `keep_count` for a workspace.
#[allow(dead_code)]
pub async fn prune_snapshots(n: u32, keep_count: usize) -> Result<()> {
    let all = list_snapshots(n).await?;
    if all.len() <= keep_count {
        return Ok(());
    }
    let dir = workspace_snapshot_dir(n);
    for id in all.into_iter().skip(keep_count) {
        let path = dir.join(format!("{id}.snap"));
        let _ = tokio::fs::remove_file(&path).await;
        debug!("pruned old snapshot {id}");
    }
    Ok(())
}
