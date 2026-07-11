# AETHER CORE — Central Consciousness Daemon (`aetherd`)

AETHER CORE is an **OS-level AI cognition substrate** for SynthOS. `aetherd` is
the *permanent intelligence substrate*: it remembers, plans, reflects, and
brokers access to the system. **Agents are temporary workers** — they never talk
to each other directly. They publish/subscribe on the daemon's event bus and
request privileges through the daemon's capability broker.

This crate is an **MVP**: real, compiling Rust with working in-memory state and
SQLite persistence where feasible. Heavier pieces (LLM planning, embeddings,
NATS, gRPC) are represented by well-typed stubs with clean seams for later.

## Architecture

```
                      ┌──────────────────────────────────────────┐
   Agents (workers) ─▶│                 aetherd (CCD)            │
   (never P2P)        │                                          │
                      │  event_bus ── pub/sub (stands in for     │
                      │               NATS; tokio::broadcast)    │
                      │  broker    ── capability tokens + audit  │
                      │               + rate limits + approvals  │
                      │  memory    ── SQLite typed memory graph  │
                      │               + hybrid (cosine) retrieval│
                      │  workspace ── projects/repos/files/tasks │
                      │  planning  ── Goal→Objective→Task→…       │
                      │  reflection── after-action review        │
                      │  cognitive ── attention / curiosity /    │
                      │               consolidation engines      │
                      │  api       ── DaemonApi trait +          │
                      │               newline-JSON over TCP      │
                      └──────────────────────────────────────────┘
```

### Subsystems

| Module        | Responsibility |
|---------------|----------------|
| `event_bus`   | In-process publish/subscribe over `tokio::sync::broadcast`. `Event` enum: `FileCreated`, `FileModified`, `TaskCompleted`, `AgentStarted`, `AgentStopped`, `GoalCreated`, `MemoryAdded`, `ToolUsed`, `ErrorOccurred`, `PlanUpdated`. |
| `memory`      | Typed memory graph (`Episodic`/`Semantic`/`Procedural`/`Working`/`Reflection`) + 11 relation kinds, SQLite-backed with an in-memory index. `add`/`get`/`relate`/`query`/`traverse`, hybrid `retrieve` (cosine over optional `f32` embeddings), `age` (importance decay), `summarize`. |
| `workspace`   | Structural graph of `Project`/`Repo`/`File`/`Task`/`Goal`/`Agent`/`Conversation`/`Document`/`Person`/`Service`. Queries: `dependents_of`, `dependencies_of`, `blocked`. |
| `planning`    | Hierarchical `Goal → Objective → Task → Subtask → Action`, goal decomposition, dependency analysis (`ready_tasks`), plan repair (`repair`). |
| `reflection`  | After-action review producing findings, patterns, recommendations. |
| `broker`      | `CapabilityToken` enum (`ReadFile`, `WriteFile`, `SearchCode`, `ExecuteCommand`, `AccessDatabase`, `UseBrowser`, `UseGit`, `UseDocker`, `UseKubernetes`, `NetworkAccess`, `SystemControl`), request validation, append-only audit log, sliding-window rate limits, approval workflow for sensitive tokens. |
| `agent`       | `AgentIdentity` (id, capabilities, memory/workspace scope, trust level, audit trail, execution history, specialization) + `AgentRegistry`. |
| `cognitive`   | `AttentionEngine` (importance/urgency/novelty salience queue), `CuriosityEngine` (periodic scan → investigation goals), `MemoryConsolidator` (periodic episodic → reflection summarisation). |
| `api`         | `DaemonApi` trait (`add_memory`, `query_memory`, `create_goal`, `list_agents`, `publish_event`) + a minimal newline-delimited JSON-over-TCP server (no `tonic`/`prost`). |

## Dependencies

Minimal and all present in the local cargo cache:
`tokio`, `serde`, `serde_json`, `tracing`, `tracing-subscriber`, `chrono`,
`uuid`, `rusqlite` (bundled SQLite), `clap`, `anyhow`, `thiserror`.

## Build & run

```bash
cd aether/core
cargo build                       # compile the workspace
cargo run -p aetherd              # start the daemon (defaults below)

# Custom options:
cargo run -p aetherd -- \
    --db-path /tmp/aether/memory.db \
    --listen 127.0.0.1:8787 \
    --log-level debug
```

On startup the daemon opens (or creates) the SQLite memory DB, bootstraps a demo
agent (`scout-01`) and a few memories, exercises the in-process `DaemonApi`, and
starts the background cognition tasks + the TCP API. Press `Ctrl-C` to stop.

## API smoke test

The API speaks one JSON object per line. With the daemon running:

```bash
# Ping
printf '{"op":"ping"}\n' | nc 127.0.0.1 8787

# Add a memory
printf '{"op":"add_memory","kind":"Episodic","content":"user opened editor","importance":0.6}\n' \
    | nc 127.0.0.1 8787

# Query memory
printf '{"op":"query_memory","query":"editor","limit":5}\n' | nc 127.0.0.1 8787

# Create a goal (auto-decomposed)
printf '{"op":"create_goal","description":"refactor build system"}\n' | nc 127.0.0.1 8787

# List agents
printf '{"op":"list_agents"}\n' | nc 127.0.0.1 8787

# Daemon stats
printf '{"op":"stats"}\n' | nc 127.0.0.1 8787
```

Each returns a single JSON line: `{"status":"pong"}`,
`{"status":"ok","data":{…}}`, or `{"status":"error","message":"…"}`.

## Design notes / future work

* **Event bus → NATS/JetStream**: the `EventBus` API is intentionally small so it
  can be swapped for a real broker without touching call sites.
* **Embeddings**: `MemoryNode.embedding` is an optional `Vec<f32>`; `retrieve`
  already blends cosine similarity with lexical + importance signals. Wire an
  embedding model to populate the vectors.
* **Planning/Reflection**: decomposition and AAR are deterministic stubs with
  clear seams for an LLM planner.
* **API → gRPC**: the `DaemonApi` trait is transport-agnostic; the JSON/TCP
  server is one adapter. A `tonic` service can be added later as another adapter.
