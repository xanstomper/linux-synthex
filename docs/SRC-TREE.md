# Source Tree Walkthrough — `src/`

`src/` holds the **project source code**: the Rust daemons (in a Cargo
workspace) plus a handful of Python/app dirs. This is where the "real"
daemons live (see `docs/DAEMONS.md` for the compiled-binary list).

The top-level `Cargo.toml` defines a large Cargo **workspace**. The two
key commands:

```bash
cargo check --workspace            # type-check everything (fast)
cargo build --workspace --release  # produce the 42 binaries in target/release/
```

The current workspace has **82 member directories** under `src/` (and
the separate `aether/core` workspace).

## The top-level workspace members (from `Cargo.toml`)

```
# Core daemons
src/synthex-system-daemon
src/hwdaemon
src/desktopd
src/gpu-setupd
src/stored
src/ai-daemon
src/snapshot-manager

# CLI tools
src/synthex-cli
src/synthbox

# Security
src/synthguard
src/synthshield
src/synthvault
src/synthidentity

# System management
src/synthupdate
src/synthnet
src/synthex-app-installer
src/synthex-compat-db
src/synthex-codec-installer-rs
src/synthex-handheld-rs
src/synthex-kernel-manager-rs
src/synthex-perf-tuning-rs
src/synthex-proton-manager-rs
src/synthex-recovery-rs
src/synthex-service-manager-rs
src/synthex-system-report-rs
src/synthex-terminal-workspace
src/synthex-wine-manager

# Integration
src/installer-detect
src/integration-engine

# Rust tool suite (sub-crates)
src/synthex-rust-tools/synthex-pkg
src/synthex-rust-tools/synthex-update-manager
src/synthex-rust-tools/synthex-driver-manager
src/synthex-rust-tools/synthex-drip-sync

# Niche daemons
src/synthex-deadman
src/synthex-meshnet
src/synthex-predictive

# Brain OS — AI-native runtime
src/synthex-brain
src/synthex-agent-sandbox
src/synthex-workspace-ai
src/synthex-neural-ipc
```

The rest of `src/` contains the **Python tools** (e.g.
`synthex-tray`, `synthex-disk-health`, `synthex-workspace`,
`synthex-predictive-launch`, `synthex-welcome`, etc.) and **GUI
skeletons** (`synthex-control-center`, `synthex-studio`,
`synthex-app-manager`, `synthex-blueprint`, `synthex-oobe`,
`synthex-webapp-engine`, and the COSMIC-era `ui/` trees).

## Guidance by kind

| Kind | Convention | Where |
|---|---|---|
| Rust daemon | `Cargo.toml` + `src/main.rs`, `binary name = synthex-*` | workspace member |
| Python CLI | `main.py` at `src/<name>/main.py` | `configs/*` install as launcher |
| Python+Towers shell script | `src/<name>/<name>` (bash) or `scripts/` | any CLI that wants a shebang |
| QML/GTK GUI | `src/<name>/ui/`, `src/<name>/CMakeLists.txt` | the control-center/studio path |

> The binaries you will find in `target/release/` are the **Rust** ones.
> Everything else is Python/sh and is packaged as `noarch` with a
> launcher script in the spec (see `docs/PACKAGING.md`).

## Verification
Run `cargo check --workspace`; expect it to finish. Run
`configs/tests/verify.sh` to prove the AIOS layer still talks to the
built `synthex-brain`.