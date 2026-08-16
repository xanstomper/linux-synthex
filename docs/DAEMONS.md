# Daemon & Binary Inventory

Every **compiled** binary that the project ships, its purpose, its
systemd unit (if any), and its network/service surface.

## How to get the list yourself

```bash
cd linux-synthex
cargo build --workspace --release 2>/dev/null   # 1-time
ls target/release/
```

The current release build produces **42 binaries**:

```
synthbox                           synthex-agent-sandbox
synthex-ai-daemon                  synthex-app-installer
synthex-brain                      synthex-checkin
synthex-codec-installer-rs         synthex-compat-db
synthex-deadman                    synthex-desktopd
synthex-drip-sync                  synthex-driver-manager
synthex-gpu-setupd                 synthex-handheld-rs
synthex-hermes                     synthex-hwdaemon
synthex-installer-detect           synthex-integration-engine
synthex-kernel-manager             synthex-meshnet
synthex-neural-ipc                 synthex-perf-tuning-rs
synthex-pkg                        synthex-predictive
synthex-proton-manager-rs          synthex-recovery
synthex-service-manager            synthex-snapshot
synthex-stored                     synthex-system-daemon
synthex-system-report-rs           synthex-terminal-workspace
synthex-update-manager             synthex-wine-manager
synthex-workspace-ai               synthguard
synthidentity                      synthnet
synthshield                        synthupdate
synthvault
```

## Category map

### Core OS daemon (the "heart")

| Binary | Unit (example) | Purpose |
|---|---|---|
| `synthex-system-daemon` | `synthex-system-daemon.service` | Top-level OS supervisor: coordinates the other daemons, settings, policies. |
| `synthex-stored` | `synthex-stored.service` | Long-lived key/value store (SQLite-backed) for daemon state and user data. |
| `synthex-desktopd` | `synthex-desktopd.service` | Desktop session helper (Wayland/X11 integration, status). |
| `synthex-hwdaemon` | `synthex-hwdaemon.service` | Hardware abstraction: enumerates, monitors, configures HW state. |
| `synthex-gpu-setupd` | `synthex-gpu-setupd.service` | GPU vendor detection + startup driver setup (AMD/Intel/NVIDIA). |
| `synthex-integration-engine` | `synthex-integration-engine.service` | Bridges / integrates external components (HID mapping, scripts). |
| `synthex-snapshot` | `synthex-snapshot.service` | Btrfs snapshot helper (used by install/update for rollback). |
| `synthex-deadman` + `synthex-checkin` | sibling units | Watchdog: checks systemd units, auto-restarts, alerts on repeat failure. |
| `synthex-installer-detect` | (oneshot) | Hardware/GPU detection at install time. |

### AI / Brain (the differentiator)

| Binary | Purpose |
|---|---|
| `synthex-brain` | On-device conversational + long-term memory daemon (the "Neural Brain"). Exposes `status/recall/ground/learn/json`. |
| `synthex-hermes` | Agent/assistant orchestration daemon that talks to the brain + capability broker. |
| `synthex-workspace-ai` | Workspace-aware assistant (contextual answers about projects/files). |
| `synthex-agent-sandbox` | Isolated environment in which AI agents run capability-gated. |
| `synthex-neural-ipc` | Local inference/pre/post axes IPC (model plumbing for the brain). |
| `synthex-ai-daemon` | Ties AI daemons together; start/stop/restart per agent scope. |

### Device & driver managers

| Command | Purpose |
|---|---|
| `synthex-driver-manager` | Detect + install/revealer driver (AMD/Intel/NVIDIA). |
| `synthex-gpu-switch` | Opt-in GPU switching / GPU power-mode toggle. |
| `synthex-input-remapper` | Remap gamepad / keyboard (user-level). |

### Update / recover / security

| Command | Purpose |
|---|---|
| `synthex-update-manager` | System/package update manager (snapshot-aware). |
| `synthex-codec-installer-rs` | Multimedia codec installer (rpmfusion). |
| `synthex-proton-manager-rs` | DXVK / VKD3D / Proton compatibility layer manager. |
| `synthex-recovery` | Rescue/recovery utilities. |
| `synthguard` | Zero-trust guard: capability gate for system actions. |
| `synthshield` | Threat/risk shield: firewall + block outbound for daemons. |
| `synthvault` | On-disk encrypted vault (AES-256 configuration). |
| `synthidentity` | Key/identity management for agents + system services. |
| `synthnet` | Network policy / firewall helper. |
| `synthupdate` | Lightweight A-B verification of updates before apply. |
| `synthbox` | Container/AppImage sandbox runner. |

### Creator / workstation (the "AI creator" story)

| Command | Purpose |
|---|---|
| `synthex-terminal-workspace` | Terminal multiplexing + workspace integration. |
| `synthex-webapp-engine` | Sandbox hosting for web-app-like tools. |
| `synthex-compat-db` | Compatibility database (game/app → driver/settings). |
| `synthex-app-installer` | Flatpak/app store / one-click installer. |
| `synthex-drip-sync` | Dropbox/drive-style sync for small files. |
| `synthex-pkg` | Package (rpm/flatpack) query helper. |
| `synthex-system-report-rs` | Hardware/OS report generator. |
| `synthex-wine-manager` | Wine prefix manager for gaming/apps. |
| `synthex-handheld-rs` | Steam-Deck-style handheld controller/config. |

## Which are wired to `synthex-doctor` / `synthex-defaults`

`synthex-defaults enable-all` toggles a subset:

- `synthex-brain.service`
- `synthex-hermes.service`
- `synthex-snapshot.service`
- `synthex-predictive.service` (a daemon whose binary is `synthex-predictive`)
- `synthex-predictive-launch.service` (predictive-launch tracks usage
  patterns; ships via the `synthex-predictive-launch` RPM)

`synthex-doctor` checks the running state of:

- `synthex-system-daemon`
- `synthex-brain`
- `synthex-hermes`
- `synthex-hwdaemon`

## Units that ship but are centralized in `synthex-aios`

The AIOS umbrella RPM (`packages/spec-files/synthex-aios.spec`) ships the
service units that the daemons enable:

- `synthex-defaults.service`
- `synthex-zram.service`
- `synthex-sync-updates.service`
- `synthex-sync-updates.timer`

## Service surface (network / IPC)

| Daemon | Kind | Address/port | Notes |
|---|---|---|---|
| `synthex-brain` | unix socket / DBus | local only | CLI: `synthex-brain status` |
| `synthex-hermes` | DBus/localhost | `127.0.0.1` | bounded |
| AETHER (older) | TCP JSON-line | `127.0.0.1:8787` | `synthex` console probes this |

Only the AETHER broker listens on a TCP port (127.0.0.1, loopback). All
other daemons use sockets/DBus/loopback and expose **no** public
network surface.

## Enabling / disabling

```bash
systemctl enable --now synthex-system-daemon
systemctl disable synthex-webapp-engine   # less surface
synthex persona privacy                   # disable web-facing daemons
```

## Health check

```bash
synthex-doctor        # reports active/enabled state of the core daemons
```

See `docs/AIOS.md#synthex-doctor--usr-sbin-synthex-doctor` for the
output format.