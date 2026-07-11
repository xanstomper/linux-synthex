// SPDX-License-Identifier: GPL-3.0-or-later
//
// synthex-neural-ipc — Wire Protocol
//
// Wire format: 4-byte little-endian length prefix followed by a UTF-8 JSON body.
// Maximum inline message size: 4 MiB.  Larger payloads are passed via a
// ShmRef (shared-memory reference) embedded in the payload field.

use serde::{Deserialize, Serialize};

/// Channel names recognised by the broker.
pub const CHANNEL_BRAIN:        &str = "brain";
pub const CHANNEL_WORKSPACE:    &str = "workspace";
pub const CHANNEL_CAPABILITIES: &str = "capabilities";
pub const CHANNEL_ALERTS:       &str = "alerts";
pub const CHANNEL_CONTEXT:      &str = "context";
pub const CHANNEL_AGENT_PREFIX: &str = "agent/";

/// Maximum inline payload (4 MiB).  Larger data must use ShmRef.
pub const MAX_INLINE_BYTES: usize = 4 * 1024 * 1024;

/// Length prefix size (u32 LE).
pub const FRAME_HEADER_LEN: usize = 4;

// ── Message types ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageType {
    // Pub/sub
    Publish,
    Subscribe,
    Unsubscribe,

    // Request / reply
    Request,
    Reply,
    Error,

    // Brain-daemon control
    BrainEvent,
    WorkspaceEvent,
    CapabilityGrant,
    CapabilityRevoke,
    SecurityAlert,
    ContextUpdate,

    // Lifecycle
    Ping,
    Pong,
    Shutdown,

    // Large-data transfer via shared memory
    ShmPublish,
    ShmRequest,
    ShmReply,
}

// ── Reference into shared memory ─────────────────────────────────────────────

/// A reference to a POSIX shared-memory segment that holds large payload data.
/// The receiver maps this segment, reads `size` bytes starting at `offset`,
/// and then decrements the refcount via `shmem_release`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShmRef {
    /// POSIX shm name (e.g. "/synthex-ipc-a3f9c2b1").
    pub name: String,
    /// Total size of the segment in bytes.
    pub size: usize,
    /// Byte offset within the segment where the payload begins.
    pub offset: usize,
    /// Number of bytes of meaningful data starting at `offset`.
    pub data_len: usize,
}

// ── On-wire message ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    /// UUIDv4 — uniquely identifies this message.
    pub id: String,

    /// Sender identifier (agent name, daemon name, or "broker").
    pub from: String,

    /// Destination channel (see CHANNEL_* constants) or agent name.
    pub to: String,

    /// Message semantics.
    pub msg_type: MessageType,

    /// Inline JSON payload (up to MAX_INLINE_BYTES).
    /// For large data, contains a serialised ShmRef instead.
    pub payload: serde_json::Value,

    /// HMAC-SHA256 over `id|from|to|msg_type|timestamp` — prevents spoofing.
    /// Stored as a 64-character lowercase hex string.
    pub hmac: String,

    /// Unix timestamp in milliseconds (UTC).
    pub timestamp: i64,

    /// Message TTL in milliseconds.  The broker drops messages whose age
    /// exceeds this value before delivery.  0 = never expires.
    pub ttl_ms: u32,

    /// Optional correlation id for request/reply pairing.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub correlation_id: Option<String>,
}

impl Message {
    /// Construct a new outgoing message with a fresh UUIDv4 id and the
    /// current wall-clock timestamp.  The caller is responsible for filling
    /// in `hmac` via [`sign`] before sending.
    pub fn new(
        from: impl Into<String>,
        to: impl Into<String>,
        msg_type: MessageType,
        payload: serde_json::Value,
        ttl_ms: u32,
    ) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            from: from.into(),
            to: to.into(),
            msg_type,
            payload,
            hmac: String::new(), // filled by sign()
            timestamp: now_ms(),
            ttl_ms,
            correlation_id: None,
        }
    }

    /// Returns `true` if the message has exceeded its TTL.
    pub fn is_expired(&self) -> bool {
        if self.ttl_ms == 0 {
            return false;
        }
        let age = now_ms().saturating_sub(self.timestamp) as u32;
        age > self.ttl_ms
    }

    /// Serialise to a length-prefixed frame ready for writing to a socket/pipe.
    pub fn to_frame(&self) -> anyhow::Result<bytes::Bytes> {
        let json = serde_json::to_vec(self)?;
        if json.len() > MAX_INLINE_BYTES {
            anyhow::bail!(
                "message payload too large ({} bytes > {} limit)",
                json.len(),
                MAX_INLINE_BYTES
            );
        }
        let mut buf = bytes::BytesMut::with_capacity(FRAME_HEADER_LEN + json.len());
        buf.extend_from_slice(&(json.len() as u32).to_le_bytes());
        buf.extend_from_slice(&json);
        Ok(buf.freeze())
    }

    /// Parse a length-prefixed frame.  `data` must not include the 4-byte
    /// header (caller strips it beforehand).
    pub fn from_json_bytes(data: &[u8]) -> anyhow::Result<Self> {
        Ok(serde_json::from_slice(data)?)
    }
}

/// Current wall-clock time in milliseconds since the Unix epoch.
pub fn now_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as i64
}

// ── HMAC helpers ─────────────────────────────────────────────────────────────

use hmac::{Hmac, Mac};
use sha2::Sha256;

type HmacSha256 = Hmac<Sha256>;

/// Sign `msg` in-place using `key`.
pub fn sign(msg: &mut Message, key: &[u8]) {
    let material = format!(
        "{}|{}|{}|{:?}|{}",
        msg.id, msg.from, msg.to, msg.msg_type, msg.timestamp
    );
    let mut mac = HmacSha256::new_from_slice(key).expect("HMAC accepts any key length");
    mac.update(material.as_bytes());
    let result = mac.finalize().into_bytes();
    msg.hmac = hex::encode(result);
}

/// Verify that `msg.hmac` matches `key`.  Returns `true` on success.
pub fn verify(msg: &Message, key: &[u8]) -> bool {
    let material = format!(
        "{}|{}|{}|{:?}|{}",
        msg.id, msg.from, msg.to, msg.msg_type, msg.timestamp
    );
    let mut mac = HmacSha256::new_from_slice(key).expect("HMAC accepts any key length");
    mac.update(material.as_bytes());
    let expected = mac.finalize().into_bytes();
    hex::encode(expected) == msg.hmac
}
