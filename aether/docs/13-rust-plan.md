# 13 — Rust Implementation Plan

`aetherd` is implemented in Rust (2021 edition, stable). Targets: `x86_64-unknown-linux-gnu`, with musl/`aarch64` later.

## 1. Workspace Crate Layout

```
aether/
├── Cargo.toml                # workspace
├── crates/
│   ├── aether-core/          # orchestrator, intent routing, registry
│   ├── aether-memory/        # 5-tier memory, consolidator, crystallizer
│   ├── aether-graph/         # graph ingestion, traversal
│   ├── aether-broker/        # capability tokens, validation, audit
│   ├── aether-runtime/       # agent sandbox + provider adapters
│   ├── aether-eventbus/      # append-only log, pub/sub, replay
│   ├── aether-sentinel/      # security core + detection
│   ├── aether-cognitive/     # dreams/attention/curiosity/dissonance...
│   ├── aether-workspace/     # semantic desktop, time machine
│   ├── aether-api/           # gRPC (tonic) services
│   ├── aether-storage/       # PG/Qdrant/Graph/FS adapters
│   ├── aether-sandbox/       # namespaces/cgroups/seccomp/gvisor
│   └── aether-common/        # shared types, ids, errors
├── proto/                    # .proto definitions
└── configs/                  # default YAML/TOML
```

## 2. Key Dependencies

| Crate | Use |
|-------|-----|
| `tokio` | async runtime |
| `tonic` / `prost` | gRPC + protobuf |
| `sqlx` | PostgreSQL (async, compile-time checked) |
| `qdrant-client` | vector DB |
| `neo4rs` | graph DB driver |
| `ed25519-dalek` | token signatures |
| `serde` / `serde_json` | (de)serialization |
| `tracing` / `opentelemetry` | observability |
| `nix` / `runc` / `caps` | sandbox primitives |
| `rkyv` / `zstd` | fast/compressed event codec |
| `rand` / `uuid` | ids/nonces |

## 3. Module Signatures (representative)

```rust
// aether-broker
pub fn mint_token(agent: &Agent, cap: Capability, scope: Scope,
                  policy: &Policy) -> Result<CapabilityToken>;
pub fn validate(token: &CapabilityToken, intent: &Intent) -> Decision;

// aether-memory
pub async fn store(rec: MemoryRecord) -> Result<MemoryId>;
pub async fn retrieve(query: SemanticQuery, view: &AgentView) -> Vec<MemoryRecord>;
pub fn consolidate(&mut self) -> ConsolidationReport;

// aether-runtime
pub async fn spawn(agent: AgentSpec, token: CapabilityToken) -> Result<AgentHandle>;
pub trait LlmProvider { async fn complete(&self, req: CompletionRequest,
                                          ctx: MemoryContext) -> Result<Completion>; }

// aether-eventbus
pub fn append(event: Event) -> Result<()>;
pub fn subscribe(topic: Topic, acl: &TopicAcl) -> Subscription;
pub fn replay(from: SnapshotId, to: Timestamp) -> impl Iterator<Item=Event>;
```

## 4. Build & Run
- `cargo build --release` → `target/release/aetherd`.
- systemd unit `aetherd.service` (unprivileged user `aether`; ambient caps dropped).
- Config via `/etc/aether/aether.toml`; secrets via kernel keyring/TPM.

## 5. Testing Strategy
- Unit: each crate; property tests for token signing/replay determinism.
- Integration: ephemeral Postgres + in-memory Qdrant + embedded graph using testcontainers.
- Fuzz: event-log parser, capability scope matcher.
