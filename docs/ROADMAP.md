# Roadmap & Status

Honest, current status of the SynthOS project and what's next. This
documents **both** what is real and working **and** what is aspirational
so nobody mistakes an idea for a feature.

## Legend

- ✅ Done / verified (host or container)
- 🟡 Partial / needs the Fedora builder
- 🟠 Planned
- ❌ Deprecated / superseded

## 1. Core distribution

| Item | Status |
|---|---|
| Local RPM repo (125/173 specs) | ✅ |
| Local repo consumes Fedora kernel | ✅ |
| 5 kickstart editions patched | ✅ |
| Fedora 41 builder image | 🟡 |
| Bootable ISO produced+validated | 🟡 (in container) |
| Calamares installer full config | 🟠 |
| COSMIC DE | 🟠 (needs vendored tar + cargo) |
| rust-utils CLI suite | 🟠 |

## 2. AIOS layer

| Item | Status |
|---|---|
| `synthex` console → brain | ✅ |
| `synthex-doctor` | ✅ |
| `synthex-persona` (5 profiles) | ✅ |
| `synthex-install` (guarded) | ✅ |
| `synthex-update-sync` (real Bodhi + queue) | ✅ |
| `synthex-defaults` first-boot | ✅ |
| verify harness 17/17 | ✅ |
| CPU/GPU/audio/perf defaults | ✅ |

## 3. AI daemons

| Item | Status |
|---|---|
| 42 prebuilt binaries | ✅ (cargo build --workspace --release) |
| Packages for ~most daemons | ✅ |
| Full systemd unit coverage | 🟡 |
| `synthex privacy` switch | 🟠 |
| Global hotkey AI command-palette | 🟠 |

## 4. Security / perf

| Item | Status |
|---|---|
| Snapshot-before-install | ✅ |
| Snapshot-before-update | ✅ |
| zram | ✅ |
| gamemode / gamescope | ✅ (packaged) |
| Microupdate framework | 🟡 |
| SELinux module for dashboard | 🟠 (part stub) |

## 5. Release

| Item | Status |
|---|---|
| Version scheme (2026.10 / Ignition) | ✅ |
| `release.sh` (iso + checksums + sign) | ✅ |
| ISO validation | ✅ |
| Torrent publishing | 🟡 (needs transmission) |
| push to server | 🟠 (stub host) |

## What to build next (by impact)

1. **Real Fedora-builder ISO** (the single finish line to a bootable
   image).
2. **CONFIRM + build the pending 48** in the container (COSMIC if the
   tar URLs resolve; else rust-utils).
3. **`synthex privacy`** toggle (security UX).
4. **Air hotkey AI palette**.
5. **Persona→first-boot wiring** to a real OOBE.

## Non-goals (deliberate)

- Custom kernel (we ship the Fedora kernel).
- Rebasing mint.
- Disabling mitigations.
- Vendor-binary GPU `.run` installers.

`docs/PENDING.md` lists the 48 unbuilt specs and **why**.
`docs/ALL-DOCS.md` notes the version-string divergence between the
legacy and new eras.