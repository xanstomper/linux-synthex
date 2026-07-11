#!/usr/bin/env bash
# gen-ipc-key.sh — Generate the HMAC key used by synthex-neural-ipc.
#
# Runs once at package post-install if /etc/synthex/neural-ipc.key doesn't exist.
# Safe to re-run: exits 0 without overwriting an existing key.
#
# Key rotation: delete /etc/synthex/neural-ipc.key and restart synthex-neural-ipc.

set -euo pipefail

KEY_FILE="/etc/synthex/neural-ipc.key"
KEY_DIR="/etc/synthex"
GROUP="synthex-brain"
KEY_LEN=64  # 512-bit HMAC key

if [[ -f "$KEY_FILE" ]]; then
    echo "neural-ipc key already exists at $KEY_FILE — skipping generation" >&2
    exit 0
fi

mkdir -p "$KEY_DIR"
chmod 750 "$KEY_DIR"

# Generate key from /dev/urandom (64 raw bytes → 128 hex chars)
dd if=/dev/urandom bs=1 count="$KEY_LEN" status=none | xxd -p -c 256 > "$KEY_FILE"

chmod 640 "$KEY_FILE"
chown root:"$GROUP" "$KEY_FILE"

echo "Generated new Neural IPC HMAC key at $KEY_FILE ($(wc -c < "$KEY_FILE") bytes)" >&2
