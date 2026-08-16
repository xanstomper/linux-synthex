# SynthOS / Synththex — Comprehensive Documentation

This is the master index. Read in order if you’re new; jump to a chapter if
you know what you want.

---

## Project goal
SynthOS / Synthex is a **Fedora-based, gaming- and AI-first desktop
distribution** built on top of the upstream Fedora + RPM Fusion ecosystem.
It ships with:

- A curated **local RPM repo** of SynthOS-specific packages (daemons,
  AI OS layer, themes, installers, etc).
- An **AI-OS assistant console** (`synthex`) that talks to local daemons
  (`synthex-brain`, `synthex-hermes`, the AETHER broker).
- **Snapshot-guarded installs** (`synthex install`).
- A **Mint/Bazzite-style upstream tracker** (`synthex-update-sync`)
  that asks Fedora’s real Bodhi API for the latest version of each tracked
  package, records a snapshot, and hands a real build queue to the builder.
- A **performance layer** (zram, gamemode, gamescope, gov-switcher,
  safe sysctl).
- A **persona selector** (`synthex persona gamer|creator|developer|privacy|minimal`).
- A **doctor** for one-shot health reporting.
- Patched **kickstart files** for Hyprland/Plasma/GNOME/GNOME/Minimal editions
  that point at the local repo (instead of the dead upstream domain) and
  install the **Fedora 41 kernel set**.

The host-side build environment today is **Linux Mint + the Fedora
builder container** (`build/livecd/Dockerfile`, based on `fedora:41`).

---

## Index of documents

| File | What it covers |
|---|---|
| `docs/ARCHITECTURE.md` | Layered design, what each piece is for. |
| `docs/BUILD.md` | How to build the local RPM repo on this host. |
| `docs/PACKAGING.md` | The RPM spec conventions, macros, and the verify harness. |
| `docs/AIOS.md` | The `synthex` CLI, `synthex-doctor`, `synthex-persona`, `synthex-install`, `synthex-update-sync`, `synthex-defaults`, `synthex game-session`. |
| `docs/UPDATER.md` | The Mint/Bazzite-style upstream tracker, queue semantics, rollback. |
| `docs/PERFORMANCE.md` | The safe gaming/perf defaults (zram, gamescope, gov, sysctl, gamemode). |
| `docs/ISO.md` | How the bootable ISO is assembled (kickstart, builder container, `livecd-creator`). |
| `docs/KERNEL.md` | Kernel policy (the project ships the official Fedora kernel, not a custom build). |
| `docs/REPO-LAYOUT.md` | Directory structure of the source tree. |
| `docs/EXTENDING.md` | How to add a new daemon, a new tracked package, a new persona, a new kickstart edition. |
| `docs/TROUBLESHOOTING.md` | Known traps and quick fixes. |
| `REPORT.md` | One-page build report (legacy, generated earlier). |

---

## At a glance — what the verify harness proves

The single most important file is `configs/tests/verify.sh`. It is the
**reproducible proof** that what this repository claims actually runs.

Run it any time:

```bash
linux-synthex/configs/tests/verify.sh; echo "result=$?"
```

You should see `RESULT: 17 passed, 0 failed` and `exit 0`. Any failure
breaks the contract.

What it covers:

1. **Syntax gates** for every bash script we wrote (`bash -n`).
2. **Python compile** for `synthex-update-sync.py`.
3. **Config JSON validity** (`synth-pkgs.conf` is comment-tolerant JSON).
4. **`synthex-update-sync` end-to-end in a sandbox**:
   - `status` lists tracked packages and reports real upstream
     versions from Fedora’s Bodhi API.
   - `stage` writes `candidate.json` per tracked package.
   - `apply` writes a real `queue.jsonl` build-queue for the container
     builder. (It does **not** pretend a rebuild happened.)
   - `rollback` gracefully no-ops if no snapshot tool exists.
5. **`synthex` CLI vs the live `synthex-brain`**:
   - `status` returns the real brain status.
   - `memory` returns the real memory-graph report.
   - `ask` calls `synthex-brain recall` and returns a real answer.
6. **`synthex-install`** dry-run prints a real plan.
7. **`synthex-doctor` and `synthex-persona`** run cleanly.

---

## What this repo is **not**

It is **not** a finished, bootable, end-user-ready ISO yet. The pieces
are wired and verifiable, but assembling the final image requires running
`build/run-iso-build.sh` (or `build/livecd/build-iso.sh`) inside the
**Fedora builder container** with the livecd-creator/lorax stack. The
container, kickstarts, and runner script are in this tree; the actual
ISO build is a long, network-heavy operation that is not executed here.

It is also not a fully implemented custom kernel — see `docs/KERNEL.md`.
