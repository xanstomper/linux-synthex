# AETHER CORE

> **An operating-system-level AI consciousness daemon** — a cognition substrate that turns a Linux desktop (SynthOS) into a persistent, self-aware cognitive workspace.

AETHER CORE is **not** a chatbot, agent-wrapper, or IDE assistant. It is a long-running OS daemon (`aetherd`) that provides:

- A **unified memory substrate** (Episodic / Semantic / Procedural / Working / Reflection) backed by a hybrid store (PostgreSQL + Qdrant + Graph DB + filesystem).
- A **knowledge graph** spanning projects, repos, files, tasks, goals, agents, people, services, containers, and infrastructure.
- A **capability broker** implementing a zero-trust, auditable execution model for every agent action.
- An **agent runtime** that is provider-agnostic (Claude / OpenAI / Gemini / Local) and fully sandboxed.
- **AETHER SENTINEL** — an integrated, auditable + reversible security architecture.
- **SynthOS Mission Control** — a right-side sliding overlay UI for observing and steering the cognitive workspace.
- A set of **unique cognitive features** (Memory Dreams, Attention Engine, Curiosity Engine, Cognitive Dissonance Detector, Cognitive Honeypots, Trust Decay, Reality Model / Digital Twin, Future Simulation Engine, Knowledge DNA, Truth Engine, Self-Generated Research, Idea Incubator, Serendipity Engine, Personal Operating Theory, Model Routing, Agent Reputation / Mentorship / Debates, Semantic Process Manager, Memory Consolidator).

## Design Documents

| # | Document | Topic |
|---|----------|-------|
| 00 | [README.md](./README.md) | This index |
| 01 | [docs/01-architecture.md](./docs/01-architecture.md) | Full architecture overview + data flow |
| 02 | [docs/02-components.md](./docs/02-components.md) | Component diagrams |
| 03 | [docs/03-event-flow.md](./docs/03-event-flow.md) | Event flow / pub-sub / replay |
| 04 | [docs/04-data-models.md](./docs/04-data-models.md) | Core data models |
| 05 | [docs/05-memory-schema.md](./docs/05-memory-schema.md) | Memory schema + relationship types |
| 06 | [docs/06-graph-schema.md](./docs/06-graph-schema.md) | Knowledge graph schema |
| 07 | [docs/07-capability-broker.md](./docs/07-capability-broker.md) | Capability system design |
| 08 | [docs/08-security.md](./docs/08-security.md) | Zero-Trust security design |
| 09 | [docs/09-agent-runtime.md](./docs/09-agent-runtime.md) | Agent runtime design |
| 10 | [docs/10-workspace-model.md](./docs/10-workspace-model.md) | Workspace model |
| 11 | [docs/11-api.md](./docs/11-api.md) | gRPC API specification |
| 12 | [docs/12-db-schema.md](./docs/12-db-schema.md) | Database schema (hybrid storage) |
| 13 | [docs/13-rust-plan.md](./docs/13-rust-plan.md) | Rust implementation plan |
| 14 | [docs/14-directory-structure.md](./docs/14-directory-structure.md) | aether/ directory tree |
| 15 | [docs/15-mvp-roadmap.md](./docs/15-mvp-roadmap.md) | MVP roadmap |
| 16 | [docs/16-production-roadmap.md](./docs/16-production-roadmap.md) | Production roadmap |
| 17 | [docs/17-scaling-roadmap.md](./docs/17-scaling-roadmap.md) | Scaling roadmap |
| 18 | [docs/18-threat-model.md](./docs/18-threat-model.md) | Threat model |
| 19 | [docs/19-benchmark-plan.md](./docs/19-benchmark-plan.md) | Benchmark plan |
| 20 | [docs/20-cognitive-features.md](./docs/20-cognitive-features.md) | Unique cognitive features |

## AETHER SENTINEL (Security Architecture)
Documented inline in [08-security.md](./docs/08-security.md) (Sentinel Core, Threat Detection Engine, Agent Security Monitor, Malware Analysis Sandbox, Real-Time Defense, System Integrity, Forensics, Security Copilot, Threat Scoring, Zero-Trust).

## SynthOS Mission Control (Frontend)
Documented in [10-workspace-model.md](./docs/10-workspace-model.md) and [09-agent-runtime.md](./docs/09-agent-runtime.md), with the dedicated Mission Control section consolidated in [10-workspace-model.md](./docs/10-workspace-model.md).

## Guiding Principles
1. **The daemon owns cognition; agents are ephemeral tenants.** Agents are spawned, scoped, and torn down — memory and identity persist in the daemon.
2. **Zero-trust by construction.** Every action is a capability-checked, logged, reversible intent.
3. **Hybrid memory.** Hot facts in Postgres, embeddings in Qdrant, relationships in a graph DB, artifacts on the filesystem.
4. **Provider-agnostic intelligence.** Swap LLM backends without touching the substrate.
5. **Observable by default.** Everything is an event; everything is replayable.

## Build & run

AETHER CORE is implemented in Rust at [`aether/core/`](./core/). See [the core README](./core/README.md) for architecture, build instructions, and API smoke tests.

The daemon (`aetherd`) is packaged as **`synthex-aether`** (RPM), deployed as a hardened systemd service (`synthex-aether.service`), and installed at `/usr/lib/synthex/aetherd`. On SynthOS it is started before any agent daemons and provides the OS-level AI cognition substrate.

> **This directory now contains real application code** — the design documents drove the implementation, and the crate at `aether/core/` produces the `aetherd` binary. The documents remain as living specifications for the production roadmap.
