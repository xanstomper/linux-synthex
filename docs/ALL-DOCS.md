# Complete Documentation Index (All Docs, Both Generations)

This is the **full** catalogue of every documentation file in the repo —
both the new AIOS-era docs (2026.10) **and** the older "Synthex 4.6
Fortitude" docs (in subdirectories). It is the authoritative "what doc
is where" reference.

## ⚠️ Version note (two generations)

The repo has **two doc generations that disagree on the version**:

| Generation | Version string | Location |
|---|---|---|
| Older (pre-AIOS) | "Synthex 4.6 Fortitude" | `docs/architecture/`, `docs/build/`, `docs/developer/`, `docs/security/`, `docs/user/`, plus top-level files |
| Newer (this pass) | "SynthOS 2026.10 Ignition" | `docs/*.md` (root level, the AIOS layer) |

The functional truth is **2026.10 / Ignition** (see `VERSION`).
The "4.6 Fortitude" text in the older docs is **stale** and should be
treated as historical. Where they conflict, the new `docs/*.md` wins.

---

## A. New docs (`docs/*.md`, root-level)

### Master / overview
- `README.md` — what SynthOS is & isn't, what verify proves.
- `INDEX.md` — this map’s subset.
- `PROJECT-OVERVIEW.md` — one-paragraph-per-layer.
- `GLOSSARY.md` — term/acronym definitions.

### Architecture & structure
- `ARCHITECTURE.md`
- `REPO-LAYOUT.md`
- `SRC-TREE.md`
- `CONFIG-FILES.md`, `CONFIGS-REGISTER.md`
- `ENV.md`
- `PORTS-IPC.md`
- `BOOT.md` — boot/live flow.

### Build & packaging
- `BUILD.md`, `TOOLS.md`, `PACKAGING.md`, `SPEC-PATTERNS.md`,
  `PACKAGES.md`, `PENDING.md`, `RELEASE.md`, `INSTALLER.md`,
  `ISO.md`, `KICKSTARTS.md`, `KERNEL.md`, `KERNEL-CONFIG.md`.

### Features
- `AIOS.md`, `DAEMONS.md`, `UPDATER.md`, `PERFORMANCE.md`,
  `SECURITY.md`, `HARDWARE.md`.

### Operations
- `RUNBOOK.md`, `FLOWS.md`, `TESTING.md`, `EXTENDING.md`,
  `TROUBLESHOOTING.md`, `CHEATSHEET.md`, `FAQ.md`.

### Reference
- `REFERENCE.md`, `REPORT.md` (legacy).

## B. Pre-existing docs (older generation, kept)

### Top-level
- `build-guide.md`
- `CHANGELOG.md`
- `INSTALL-ARCHITECTURE.md`
- `INSTALLER-ARCHITECTURE.md`
- `PACKAGER-README.md`
- `RELEASE-NOTES-2026.10.md`

### `docs/architecture/`
- `synthex-architecture.md` — full layer diagram, boot sequence, DBus
  topology.
- `rust-architecture.md` — Rust crate topology.

### `docs/build/`
- `build-guide.md` — the old build guide.

### `docs/developer/`
- `building-packages.md`
- `api-docs.md` — API docs for AI Hub, Gaming Control Center, Security
  Dashboard, Software Center.
- `contributing.md` — Code of Conduct, PR workflow, review process.

### `docs/security/`
- `security-guide.md` — threat model, SELinux, firewall.
- `privacy-and-security.md`

### `docs/user/`
- `getting-started.md` — desktop tour, app launcher, settings, etc.
- `installation-guide.md`

## C. Which to read by role

| Role | Read |
|---|---|
| New user | `docs/user/getting-started.md`, `docs/user/installation-guide.md`, `docs/FAQ.md` |
| Admin / security | `docs/security/security-guide.md`, `docs/SECURITY.md`, `docs/PORTS-IPC.md` |
| Builder | `docs/BUILD.md`, `docs/PACKAGING.md`, `docs/TOOLS.md`, `docs/RUNBOOK.md` |
| Distro maintainer | `docs/PACKAGES.md`, `docs/PENDING.md`, `docs/ISO.md`, `docs/RELEASE.md` |
| Developer (AIOS) | `docs/AIOS.md`, `docs/REFERENCE.md`, `docs/DAEMONS.md` |
| Developer (API) | `docs/developer/api-docs.md` |
| Contributor | `docs/developer/contributing.md`, `docs/EXTENDING.md`, `docs/TESTING.md` |
| Everything | `docs/REFERENCE.md` (new) + `docs/architecture/synthex-architecture.md` (old) |

## D. Reconciliation TODO

The following are **known stale** in the older docs and should be ported
to the new-era ones (or marked legacy):

- Version string "4.6 Fortitude" → "2026.10 Ignition".
- The `api.getsynthex.org` base URL — check whether it's still the plan.
- Some daemon names in the API docs predate the current daemon set.
- The top-level README's "7 Desktop Profiles" vs the persona set
  (gamer/creator/developer/privacy/minimal).

When editing docs, prefer the new `docs/*.md` as the source of truth and
carry any genuinely-new content forward from the legacy set into it.