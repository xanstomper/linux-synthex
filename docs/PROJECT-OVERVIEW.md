# Project Overview

One-paragraph-per-component so you can see the **whole** SynthOux at
once. The "docs for literally everything" entry point.

## What SynthOS is

A **Fedora-based, gaming- and AI-first desktop Linux distribution** (plus
an **assistant console** and a **Mint/Bazzitte-style updater**) that:

- ships a curated local RPM repo of ~125 Synth-specific packages,
- vendors the official **Fedora kernel** (no custom-kernel fragility),
- adds an **AI-OS layer** (`synthex`, `doctor`, `persona`, `install`,
  `update-sync`) that is **local-first, private, reversible, and honest**,
- ships safe **performance defaults** (gamescope, gamemode, zram,
  governor switches),
- builds its ISO in a **Fedora 41 container** via `livecd-creator`, and
- is validated by a single **verify harness**.

## Component map

| Layer | Files | Docs |
|---|---|---|
| The AIOS umbrella RPM | `packages/spec-files/synthex-aios.spec` | `docs/PACKAGING.md`, `docs/REFERENCE.md` |
| The assistant console | `configs/aios/synthex` | `docs/AIOS.md` |
| The doctor | `configs/aios/synthex-doctor` | `docs/AIOS.md` |
| The persona picker | `configs/aios/synthex-persona` | `docs/AIOS.md` |
| The guarded installer | `configs/aios/synthex-install` | `docs/AIOS.md`, `docs/FLOWS.md` |
| The upstream tracker | `configs/upstream/synthex-update-sync.py` | `docs/UPDATER.md`, `docs/FLOWS.md` |
| First-boot defaults | `configs/aios/synthex-defaults` | `docs/AIOS.md`, `docs/FLOWS.md` |
| The perf layer | `configs/performance/` | `docs/PERFORMANCE.md` |
| The verify harness | `configs/tests/verify.sh` | `docs/README.md` |
| The local RPM repo | `build/repo/` | `docs/PACKAGING.md` |
| The ISO assembler | `build/scripts/build-iso-fixed.sh` | `docs/ISO.md` |
| The ISO runner | `build/run-iso-build.sh` | `docs/ISO.md` |
| The Fedora kernel | vendored in `build/repo/` | `docs/KERNEL.md` |
| The daemons | `target/release/` from `src/` | `docs/DAEMONS.md`, `docs/SRC-TREE.md` |

## Starting points (by role)

- **New to the project**: `docs/README.md` → `docs/ARCHITECTURE.md` → `docs/RUNBOOK.md`.
- **Trying to build**: `docs/BUILD.md` + `docs/PACKAGING.md`.
- **Trying to debug / extend**: `docs/TROUBLESHOOTING.md` → `docs/EXTENDING.md` → `docs/REFERENCE.md`.
- **Auditing**: `docs/DAEMONS.md`, `docs/PACKAGES.md`, `docs/PORTS-IPC.md`, `docs/SECURITY.md`.