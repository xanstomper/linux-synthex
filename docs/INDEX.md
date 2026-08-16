# Documentation Index

Complete map of every documentation file in this repository. **Read
`README.md` first.**

## Master / overview

| Doc | Purpose |
|---|---|
| `README.md` | What SynthOS is & isn't; what verify proves. |
| `INDEX.md` | This file. |
| `PROJECT-OVERVIEW.md` | One paragraph per layer — the whole at a glance. |
| `GLOSSARY.md` | Every term/acronym defined. |

## Architecture & structure

| Doc | Purpose |
|---|---|
| `ARCHITECTURE.md` | Layers, three guarantees, data flow. |
| `REPO-LAYOUT.md` | Directory map + where to put things. |
| `SRC-TREE.md` | The `src/` Cargo workspace + Python tools. |
| `CONFIG-FILES.md` | Every runtime config file shipped (units, sysctl, gamemode, snapper, state). |
| `ENV.md` | Every env-var, rpm-macro, config key. |
| `CONFIGS-REGISTER.md` | Every file under `configs/*` (35 subsystems). |
| `SPEC-PATTERNS.md` | The 7 spec shapes and their common bugs. |
| `TESTING.md` | How to test everything (verify.sh mechanics + per-tool). |
| `PORTS-IPC.md` | Network/IPC surface, loopback-only, security postures. |

## Building & packaging

| Doc | Purpose |
|---|---|
| `BUILD.md` | Host-side build (apt deps, rpmbuild, createrepo_c). |
| `TOOLS.md` | Every build/scripts* tool (make-srctars, local-repo, build_batch, gen-grub, hardware-detect, post-install, prepare-kickstart, validate-iso, build-iso*, release, build-all). |
| `PACKAGING.md` | Spec conventions, macros, the umbrella, add-a-spec. |
| `PACKAGES.md` | The 173-spec catalog (build status). |
| `PENDING.md` | The 48 not-yet-built specs, grouped, with the exact reason each. |
| `RELEASE.md` | Versioning, build.sh, checksums, signing, codename "Ignition". |
| `INSTALLER.md` | Calamares installer. |
| `ISO.md` | Two-stage ISO build; the boot bug + fix. |
| `KICKSTARTS.md` | The 5 editions; original vs patched; %post. |
| `KERNEL.md` | Why Fedora kernel (no custom). |
| `KERNEL-CONFIG.md` | The kernel config files (config-x86_64, cmdline, dracut, defconfig, spec) + the "Solus" leftover. |

## Features

| Doc | Purpose |
|---|---|
| `AIOS.md` | The assistant console layer (all subcommands + examples). |
| `DAEMONS.md` | All 42 daemons, units, surface. |
| `UPDATER.md` | The Mint/Bazzite-style updater (Bodhi, queue, rollback). |
| `PERFORMANCE.md` | Safe perf defaults. |
| `SECURITY.md` | Default posture, `synthex privacy`, out-of-scope. |
| `HARDWARE.md` | CPU/GPU/audio/wireless/controller/firmware matrix. |

## Operations

| Doc | Purpose |
|---|---|
| `RUNBOOK.md` | Step-by-step runbooks (14 procedures). |
| `FLOWS.md` | State machines for install/apply/persona/first-boot/console. |
| `EXTENDING.md` | Recipes for new daemon/pkg/persona/kickstart/test. |
| `TROUBLESHOOTING.md` | Failure modes + fixes. |
| `CHEATSHEET.md` | Quick reference. |
| `FAQ.md` | Common questions. |

## Reference

| Doc | Purpose |
|---|---|
| `REFERENCE.md` | Forensic reference of every `configs/*` file. |
| `REPORT.md` (legacy) | One-page build report from earlier. |

## Pre-existing docs (kept, unmodified)

`build-guide.md`, `CHANGELOG.md`, `INSTALL-ARCHITECTURE.md`,
`INSTALLER-ARCHITECTURE.md`, `PACKAGER-README.md`,
`RELEASE-NOTES-2026.10.md`, and subdirs `architecture/ build/
developer/ security/ user/`.

## The one command

```bash
configs/tests/verify.sh; echo $?
```

Gate CI on this.