# 04 — Core Data Models

These are the canonical Rust-struct-level data models that back AETHER CORE. Storage bindings (SQL/JSON) are in [12-db-schema.md](./12-db-schema.md).

## 1. Identity & Actors

```rust
pub struct Agent {
    pub id: AgentId,
    pub name: String,
    pub provider: ProviderKind,        // Claude | OpenAI | Gemini | Local
    pub persona: Persona,
    pub sandbox_id: SandboxId,
    pub capability_token: TokenId,
    pub reputation: Reputation,        // trust, accuracy, mentorship score
    pub created_at: DateTime<Utc>,
    pub state: AgentState,             // Spawning|Running|Idle|Paused|Terminated
}

pub struct Person {
    pub id: PersonId,
    pub handle: String,
    pub role: String,                  // owner, collaborator, external
    pub pgp_key: Option<String>,
}

pub struct Service {
    pub id: ServiceId,
    pub kind: ServiceKind,             // db|docker|k8s|web|mcp|custom
    pub endpoint: Url,
    pub health: HealthStatus,
}
```

## 2. Workspace & Intent

```rust
pub struct Workspace {
    pub id: WorkspaceId,
    pub label: String,
    pub semantic_index: Vec<EmbeddingId>,
    pub snapshot_chain: Vec<SnapshotId>,
}

pub struct Intent {
    pub id: IntentId,
    pub raw: String,
    pub parsed: ParsedIntent,          // goal graph reference
    pub origin: Origin,                // user | agent | scheduled | external
    pub priority: u8,
    pub status: IntentStatus,
}

pub struct Goal {
    pub id: GoalId,
    pub title: String,
    pub parent: Option<GoalId>,
    pub success_criteria: Vec<Criterion>,
    pub progress: f32,
}
```

## 3. Memory Records (generic)

```rust
pub enum MemoryTier { Working, Episodic, Semantic, Procedural, Reflection, Cold }

pub struct MemoryRecord {
    pub id: MemoryId,
    pub tier: MemoryTier,
    pub kind: MemoryKind,              // Fact | Episode | Procedure | Reflection
    pub content: Content,              // text | structured | artifact_ref
    pub embedding_id: Option<EmbeddingId>,
    pub timestamp: DateTime<Utc>,
    pub salience: f32,                 // attention weight
    pub confidence: f32,
    pub provenance: Provenance,
    pub expires_at: Option<DateTime<Utc>>,
    pub accesses: u64,                 // for decay/compression
}

pub struct Provenance {
    pub created_by: ActorId,
    pub discovered_by: Option<ActorId>,
    pub source_refs: Vec<Reference>,
}
```

## 4. Capability & Tokens

```rust
pub struct CapabilityToken {
    pub id: TokenId,
    pub agent_id: AgentId,
    pub capability: Capability,        // ReadFile|WriteFile|ExecuteCommand|...
    pub scope: Scope,                  // path prefix, service id, rate bucket
    pub permissions: PermissionSet,
    pub issued_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub signature: Signature,          // ed25519 by broker
    pub trace_id: TraceId,
}

pub struct AuditEntry {
    pub id: AuditId,
    pub token_id: TokenId,
    pub action: String,
    pub before: Option<SnapshotRef>,
    pub after: SnapshotRef,
    pub reversible: bool,
    pub decided_by: DecisionSource,    // auto|human|policy
}
```

## 5. Events (see 03-event-flow.md for wire form)

```rust
pub struct Event {
    pub id: EventId,
    pub ts: DateTime<Utc>,
    pub type_: EventType,
    pub producer: ActorId,
    pub topic: Topic,
    pub trace_id: TraceId,
    pub payload: serde_json::Value,
    pub hash: Hash,
    pub prev: Option<Hash>,
}
```
