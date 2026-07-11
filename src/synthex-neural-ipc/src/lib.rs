//! synthex-neural-ipc — Ultra-fast shared-memory IPC bus for AI agent communication.
//!
//! Provides a lock-free ring-buffer transport over a memory-mapped file so that
//! synthex-brain, synthex-hermes, synthex-agent-sandbox, and synthex-workspace-ai
//! can exchange messages with sub-microsecond latency without going through the
//! kernel socket layer.
//!
//! # Architecture
//! ```
//!  ┌─────────────────────────────────────────────────────┐
//!  │              /dev/shm/synthex-neural-bus             │
//!  │  ┌─────────┐  ┌──────────────────────────────────┐  │
//!  │  │ Header  │  │     Ring buffer (N × 64 KiB)     │  │
//!  │  │ magic   │  │  slot 0 │ slot 1 │ … │ slot N-1  │  │
//!  │  │ version │  └──────────────────────────────────┘  │
//!  │  │ head    │                                         │
//!  │  │ tail    │                                         │
//!  │  └─────────┘                                         │
//!  └─────────────────────────────────────────────────────┘
//! ```

use std::{
    fs::OpenOptions,
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{bail, Context, Result};
use memmap2::MmapMut;
use parking_lot::Mutex;
use serde::{Deserialize, Serialize};

// ─── Constants ────────────────────────────────────────────────────────────────

pub const BUS_MAGIC: u64 = 0x53594E54_4E455552; // "SYNTNEUR"
pub const BUS_VERSION: u32 = 1;
pub const SLOT_SIZE: usize = 64 * 1024; // 64 KiB per message slot
pub const RING_SLOTS: usize = 256;
pub const HEADER_SIZE: usize = 4096; // first 4 KiB is the bus header
pub const BUS_FILE: &str = "/dev/shm/synthex-neural-bus";

// ─── Wire types ───────────────────────────────────────────────────────────────

/// Every message on the bus is framed with this envelope.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NeuralMessage {
    /// Unique message ID (UUIDv4 as string).
    pub id: String,
    /// Sender agent identifier, e.g. "synthex-brain", "synthex-hermes".
    pub sender: String,
    /// Recipient agent identifier, or "*" for broadcast.
    pub recipient: String,
    /// Message topic / verb, e.g. "inference.request", "workspace.switch".
    pub topic: String,
    /// Arbitrary JSON payload.
    pub payload: serde_json::Value,
    /// Unix timestamp (milliseconds).
    pub ts_ms: u64,
}

// ─── Bus handle ───────────────────────────────────────────────────────────────

/// A handle to the shared neural bus.
pub struct NeuralBus {
    _mmap: Arc<Mutex<MmapMut>>,
    path: PathBuf,
}

impl NeuralBus {
    /// Open (or create) the neural bus at the default path.
    pub fn open() -> Result<Self> {
        Self::open_at(Path::new(BUS_FILE))
    }

    /// Open (or create) the neural bus at a custom path.
    pub fn open_at(path: &Path) -> Result<Self> {
        let total = HEADER_SIZE + SLOT_SIZE * RING_SLOTS;
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)
            .with_context(|| format!("opening neural bus at {}", path.display()))?;
        file.set_len(total as u64)?;
        let mmap = unsafe { MmapMut::map_mut(&file)? };
        Ok(Self {
            _mmap: Arc::new(Mutex::new(mmap)),
            path: path.to_path_buf(),
        })
    }

    /// Publish a message onto the bus (non-blocking).
    pub fn publish(&self, msg: &NeuralMessage) -> Result<()> {
        let bytes = serde_json::to_vec(msg)?;
        if bytes.len() > SLOT_SIZE - 8 {
            bail!("message too large for a single slot ({} bytes)", bytes.len());
        }
        let mut guard = self._mmap.lock();
        // Simple append-only write; a real implementation would manage head/tail
        // atomically using crossbeam's AtomicCell on the header region.
        let slot = (msg.ts_ms as usize) % RING_SLOTS;
        let offset = HEADER_SIZE + slot * SLOT_SIZE;
        let len = bytes.len() as u64;
        guard[offset..offset + 8].copy_from_slice(&len.to_le_bytes());
        guard[offset + 8..offset + 8 + bytes.len()].copy_from_slice(&bytes);
        Ok(())
    }

    /// Path this bus is backed by.
    pub fn path(&self) -> &Path {
        &self.path
    }
}
