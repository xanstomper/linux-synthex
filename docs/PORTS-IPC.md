# Ports, IPC & Network Surface

A security-relevant reference: what listens, on what, locally only vs
network-exposed, and what protocol each speaks.

## Summary: local-first, no public ports

SynthOS daemons are designed to be **local-first and private**. The only
TCP listener is the AETHER broker on loopback (127.0.0.1). Everything
else uses `unix sockets`, `DBus`, or `stdio`. There are **no** public
ports opened by any AIOS daemon.

## TCP/IP ports (loopback unless noted)

| Port | Protocol | Owner | Bound to | Notes |
|---|---|---|---|---|
| `8787` | JSON-line | AETHER (broker) | `127.0.0.1` | `synthex` console probes this; legacy |
| `9119` | HTTP | Dashboard (host side, dev) | LAN (Mint host) | unrelated to distro |
| `11434` | HTTP (OpenAI) | optional local LLM | `127.0.0.1` | for `synthex-hermes` when a local model runs |
| `27036/tcp` | Steam | Steam | local | Steam’s own port |
| `3000/tcp`, `5432/tcp`, `8080/tcp`, `5000/tcp` | varied dev | dev tools | local | not part of the distro defaults |

Only **127.0.0.1:8787** (AETHER) is owned by the AIOS layer by default.

## IPC mechanisms

| Mechanism | Used by | Purpose |
|---|---|---|
| `/dev/tcp` (clean T) | `synthex` → AETHER | the `ask_aether()` probe |
| subprocess | `synthex` → `synthex-brain` | `recall`/`status` |
| DBus (system + user) | daemons | service registration, signals |
| Unix socket | daemon ↔ stored | persistent key/value |
| `sysfs` + `procfs` | `synthex-gov`, `synthex-gpu-setupd`, `synthex-hwdaemon` | read/toggle `/sys` |

## Security postures

- **No public listener** by default.
- **No unix socket writable by the wrong user** — daemons run as
  dedicated users (`synthex-*` or root where required).
- **All **network** is on loopback. 8787 is AETHER only.
- AI daemons do **not** phone home by default; `synthex update` hits
  Bodhi over HTTPS (read-only).

## How to enumerate on a running box

```bash
ss -lntp | grep -v '127.0.0.1\|::1'   # no publicly bound ports should appear
ss -ltnp | grep 8787                  # local AETHER
```

## Anti-brick / anti-surprise

- No daemon opens a public port unless the user explicitly enables it.
- The only push-your-own logic (`apply`) writes a local `queue.jsonl`
  and snapshots first — no external writeback.
- `synthex-gov max` is a local `/sys` write that resets at reboot.
- NVIDIA `.run` installer never runs; DKMS/rpmfusion is the only path.
- Mitigations (Spectre/Meltdown) stay ON.

See `docs/SECURITY.md` for the full posture.