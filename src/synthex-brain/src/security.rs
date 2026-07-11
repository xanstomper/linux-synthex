//! Machine-keyed encryption for memory-at-rest.
//!
//! Key derivation: SHA-256(machine-id ‖ domain-tag)
//! Cipher:         HMAC-SHA256–based XOR stream (PRF keystream).
//!
//! # Production upgrade path
//! Replace `xor_with_keystream` with AES-256-GCM (add the `aes-gcm` crate) for
//! authenticated encryption.  The key derivation and wire format remain identical.

use anyhow::{anyhow, Result};
use hmac::{Hmac, Mac};
use rand::RngCore;
use sha2::{Digest, Sha256};

type HmacSha256 = Hmac<Sha256>;

const DOMAIN_TAG: &[u8] = b"synthex-brain-memory-key-v1";
const NONCE_LEN: usize = 16;

// ── Key derivation ────────────────────────────────────────────────────────────

/// Derive a 32-byte key from the machine's unique identifier.
///
/// Sources tried in order:
///   1. `/etc/machine-id`          (systemd standard)
///   2. `/var/lib/dbus/machine-id` (dbus legacy)
///   3. Hard-coded fallback (no TPM / container environment)
pub fn derive_machine_key() -> [u8; 32] {
    let machine_id = read_machine_id();
    let mut hasher = Sha256::new();
    hasher.update(machine_id.trim().as_bytes());
    hasher.update(DOMAIN_TAG);
    hasher.finalize().into()
}

fn read_machine_id() -> String {
    std::fs::read_to_string("/etc/machine-id")
        .or_else(|_| std::fs::read_to_string("/var/lib/dbus/machine-id"))
        .unwrap_or_else(|_| {
            tracing::warn!("machine-id not found; using fallback encryption seed");
            "synthex-fallback-identity-00000000-0000-0000-0000".into()
        })
}

// ── Encrypt / decrypt ─────────────────────────────────────────────────────────

/// Encrypt `plaintext` and return an opaque token.
///
/// Wire format: `hex(nonce_16) ":" hex(ciphertext)`
pub fn encrypt_value(key: &[u8; 32], plaintext: &str) -> String {
    let mut nonce = [0u8; NONCE_LEN];
    rand::thread_rng().fill_bytes(&mut nonce);
    let ct = xor_stream(key, &nonce, plaintext.as_bytes());
    format!("{}:{}", hex_enc(&nonce), hex_enc(&ct))
}

/// Decrypt a token produced by [`encrypt_value`].
pub fn decrypt_value(key: &[u8; 32], token: &str) -> Result<String> {
    let (nonce_hex, ct_hex) = token
        .split_once(':')
        .ok_or_else(|| anyhow!("Malformed ciphertext token — missing ':'"))?;
    let nonce = hex_dec(nonce_hex)?;
    let ct = hex_dec(ct_hex)?;
    let plain = xor_stream(key, &nonce, &ct);
    String::from_utf8(plain).map_err(|e| anyhow!("Decrypted bytes are not valid UTF-8: {}", e))
}

// ── Internal helpers ──────────────────────────────────────────────────────────

/// XOR `data` with a keystream derived via HMAC-SHA256(key, nonce ‖ block_counter).
/// Each 32-byte HMAC block is consumed in order.
fn xor_stream(key: &[u8; 32], nonce: &[u8], data: &[u8]) -> Vec<u8> {
    let mut out = data.to_vec();
    let mut pos = 0usize;
    let mut block: u64 = 0;

    while pos < out.len() {
        let mut mac =
            HmacSha256::new_from_slice(key).expect("HMAC-SHA256 accepts any key length");
        mac.update(nonce);
        mac.update(&block.to_le_bytes());
        let ks = mac.finalize().into_bytes();
        block += 1;

        for &k in ks.iter() {
            if pos >= out.len() {
                break;
            }
            out[pos] ^= k;
            pos += 1;
        }
    }

    out
}

fn hex_enc(bytes: &[u8]) -> String {
    bytes.iter().fold(String::with_capacity(bytes.len() * 2), |mut s, b| {
        use std::fmt::Write;
        let _ = write!(s, "{:02x}", b);
        s
    })
}

fn hex_dec(s: &str) -> Result<Vec<u8>> {
    if s.len() % 2 != 0 {
        return Err(anyhow!("Odd-length hex string"));
    }
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).map_err(Into::into))
        .collect()
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip() {
        let key = [0x42u8; 32];
        let plain = r#"{"hello":"world","count":42}"#;
        let token = encrypt_value(&key, plain);
        let recovered = decrypt_value(&key, &token).expect("decrypt");
        assert_eq!(plain, recovered);
    }

    #[test]
    fn different_nonce_each_call() {
        let key = [0x01u8; 32];
        let t1 = encrypt_value(&key, "test");
        let t2 = encrypt_value(&key, "test");
        assert_ne!(t1, t2, "nonce must be random per call");
    }

    #[test]
    fn wrong_key_gives_garbage() {
        let key_a = [0xAAu8; 32];
        let key_b = [0xBBu8; 32];
        let token = encrypt_value(&key_a, "secret");
        let result = decrypt_value(&key_b, &token).unwrap();
        assert_ne!(result, "secret");
    }
}
