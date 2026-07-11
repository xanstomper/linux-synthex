# 15 — MVP Roadmap

Goal: a runnable single-host daemon that proves the core loop — **intent → capability-checked agent → memory → graph → observable**.

## Milestones (8–12 weeks)

### M1 — Daemon Skeleton (wk 1–2)
- `aetherd` systemd service in Rust; `aether-common` types; config loader.
- Append-only Event Bus (file-backed) with hash chaining + pub/sub.
- gRPC Daemon + Agent stubs (tonic).

### M2 — Memory + Graph (wk 2–4)
- PostgreSQL facts/events; Qdrant embeddings; graph DB nodes/edges.
- 5-tier memory model; basic store/retrieve; typed relations (05/06).
- `RetrieveMemory` + `TraverseGraph` RPCs.

### M3 — Capability Broker (wk 4–6)
- Token minting (ed25519), scope validation, audit log, L0–L3 tiers.
- One sandbox backend (namespaces + cgroups + seccomp) for `ExecuteCommand`/`Filesystem`.
- Rate limiting + execution tracing.

### M4 — Agent Runtime (wk 5–7)
- Provider adapters: OpenAI + Local (llama.cpp) first; Claude/Gemini next.
- Scoped AgentView (working window + graph neighborhood).
- Thought/tool event emission; session replay from log.

### M5 — Sentinel Lite (wk 6–9)
- Signature detection (YARA + Sigma) + basic behavioral baseline.
- Agent Risk/Trust scoring; L2 approval prompts in UI.
- Reversible journal for destructive ops.

### M6 — Mission Control Basic (wk 7–10)
- Right-side overlay; Quick View + Workspace Mode.
- Agent cards, live thought/code stream, tool timeline, capability approval center.
- Signature Brain Pane (basic neural render).

### M7 — Cognitive MVP (wk 9–12)
- Attention Engine + Memory Consolidator + Curiosity Engine.
- Workspace Time Machine (snapshot + replay).
- Intent-based search.

## Definition of Done (MVP)
- Submit an intent via UI → agent runs in sandbox → writes a file → fact+edge persisted → visible in Canvas/Replay.
- All agent actions capability-checked and auditable.
- Single-host, local-first, no cloud required.

## Risks
- Sandbox complexity on varied kernels → start with container-based sandbox.
- Provider API drift → adapter layer + contract tests.
