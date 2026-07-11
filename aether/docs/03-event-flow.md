# 03 — Event Flow Diagrams

AETHER CORE is **event-sourced**. Every state mutation, agent action, and cognitive inference is an immutable event on the append-only Event Bus. This enables pub/sub, deterministic replay, and session reconstruction.

## 1. Event Taxonomy

| Event Type | Producer | Example |
|------------|----------|---------|
| `IntentReceived` | Core | user request parsed |
| `CapabilityRequested` | Agent / Core | token request |
| `CapabilityGranted/Denied` | Broker | token minted |
| `AgentSpawned/Terminated` | Runtime | sandbox created |
| `ThoughtEmitted` | Agent | reasoning token |
| `ToolCallIssued` | Agent | WriteFile invoked |
| `FactStored` | Memory | semantic fact persisted |
| `GraphEdgeAdded` | Graph | RELATED_TO edge |
| `CognitiveEvent` | Engines | Dream/Dissonance/Serendipity |
| `SecurityAlert` | Sentinel | anomaly detected |
| `MemoryConsolidated` | Memory | crystallization |

## 2. Publish / Subscribe Topology

```mermaid
flowchart TB
    subgraph PROD["Producers"]
        A[Agent Runtime]
        M[Memory]
        G[Graph]
        C[Capability Broker]
        S[Sentinel]
        E[Cognitive Engines]
    end
    BUS[Event Bus / Log]
    subgraph CONS["Subscribers"]
        OB[Observatory / UI]
        RL[Replay Engine]
        ML[ML Anomaly Model]
        ARCH[Archiver / Tiers]
        REACT[Reactive Rules]
    end
    PROD --> BUS
    BUS --> CONS
```

## 3. Replay Flow (deterministic reconstruction)

```mermaid
sequenceDiagram
    participant R as Replay Engine
    participant Log as Append-only Event Log
    participant Snap as Snapshot Store
    participant State as Materialized View
    R->>Snap: Load latest snapshot @ T0
    R->>Log: Stream events (T0..Ttarget)
    loop each event
        Log-->>R: Event e
        R->>State: Apply(e) deterministically
    end
    R-->>State: Consistent state at Ttarget
```

## 4. Agent Subscription Model

Agents subscribe to **scoped topics** only (zero-trust pub/sub). Topic names are capability-prefixed.

```mermaid
flowchart LR
    AGENT[Agent: research-07] -->|sub: agent.research-07.#| BUS[Event Bus]
    AGENT -->|sub: memory.episodic.read| BUS
    AGENT -.->|denied: agent.other-*.#| BUS
    BROKER[Capability Broker] -->|enforces topic ACL| BUS
```

## 5. End-to-End Tool-Call Event Flow

```mermaid
sequenceDiagram
    participant Ag as Agent
    participant Bus as Event Bus
    participant Br as Broker
    participant Sent as Sentinel
    participant FS as Filesystem
    Ag->>Bus: ToolCallIssued(WriteFile, token)
    Bus->>Br: validate(token, scope)
    Bus->>Sent: pre-exec defense check
    Sent-->>Br: safe (journaled)
    Br->>FS: apply op inside sandbox
    FS-->>Bus: FactStored + GraphEdgeAdded
    Bus->>Ag: result
    Bus->>OB: streamed to Observatory
```

## 6. Event Schema (canonical)

```json
{
  "id": "evt_01H...",
  "ts": "2026-07-11T08:00:00Z",
  "type": "ToolCallIssued",
  "producer": "agent:research-07",
  "topic": "agent.research-07.tools",
  "trace_id": "trace_abc",
  "capability": "WriteFile",
  "payload": { "path": "/ws/proj/notes.md", "bytes": 2048 },
  "hash": "sha256:...",
  "prev": "evt_01H_prev"
}
```

Events are content-addressed (`hash` chained to `prev`) to guarantee tamper-evidence used by the Forensics Engine.
