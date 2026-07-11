# 02 — Component Diagrams

This document details the internal components of each AETHER CORE subsystem using Mermaid component diagrams.

## 1. Core Daemon Components

```mermaid
flowchart LR
    subgraph aetherd
        ORCH[Orchestrator]
        SCHED[Scheduler / Intent Queue]
        REG[Component Registry]
        HEALTH[Liveness & Metrics]
        ORCH --> SCHED
        ORCH --> REG
        ORCH --> HEALTH
    end
```

## 2. Memory Subsystem

```mermaid
flowchart TB
    MEM[Memory Subsystem] --> WM[Working Memory (Redis/LRU)]
    MEM --> EM[Episodic Store]
    MEM --> SM[Semantic Store]
    MEM --> PM[Procedural Store]
    MEM --> RM[Reflection Store]
    MEM --> CONSOL[Memory Consolidator]
    MEM --> CRYS[Crystallization Engine]
    MEM --> DEDUP[Dedup / Compression]
    CONSOL --> CRYS
    CRYS --> SM
```

## 3. Graph Subsystem

```mermaid
flowchart TB
    G[Graph Subsystem] --> ING[Ingestion & Inferrer]
    G --> IDX[Index / Partition Manager]
    G --> TRAV[Traversal Engine]
    G --> EMB[Embedded + External Graph DB]
    TRAV --> EMB
    ING --> EMB
```

## 4. Capability Broker

```mermaid
flowchart TB
    CB[Capability Broker] --> TOK[Token Mint]
    CB --> VAL[Permission Validator]
    CB --> AUD[Audit Logger]
    CB --> APP[Approval Workflow]
    CB --> RL[Rate Limiter]
    CB --> SBX[Sandbox Enforcer]
    CB --> TRACE[Execution Tracer]
```

## 5. Agent Runtime

```mermaid
flowchart TB
    AR[Agent Runtime] --> PROV[Provider Adapter Layer]
    AR --> SBX2[Sandbox Manager]
    AR --> VIEW[Workspace / Memory View Builder]
    AR --> SUB[Event Subscriber]
    AR --> TRACE2[Trace Collector]
    PROV --> P1[Claude]
    PROV --> P2[OpenAI]
    PROV --> P3[Gemini]
    PROV --> P4[Local]
```

## 6. Sentinel Security Core

```mermaid
flowchart TB
    SENT[Sentinel Core] --> TDE[Threat Detection Engine]
    SENT --> ASM[Agent Security Monitor]
    SENT --> MAL[Malware Analysis Sandbox]
    SENT --> RTD[Real-Time Defense]
    SENT --> SIE[System Integrity Engine]
    SENT --> FORENS[Forensics Engine]
    SENT --> SCOP[Security Copilot]
    SENT --> TS[Threat Scoring]
    TDE --> SIG[Signature: YARA/Sigma/Feeds]
    TDE --> BEH[Behavioral]
    TDE --> AIAI[AI Anomaly]
```

## 7. SynthOS Mission Control (Frontend)

```mermaid
flowchart TB
    UI[Mission Control Overlay] --> OBS[Agent Observatory]
    UI --> CANVAS[Live Workspace Canvas]
    UI --> RADAR[Cognitive Radar]
    UI --> SEC[Security View]
    UI --> MEXP[Memory Explorer]
    UI --> BRAIN[Signature Brain Pane]
    OBS --> AC[Agent Cards]
    OBS --> TS2[Thought Stream]
    OBS --> COD[Live Code Stream]
    OBS --> TL[Tool Timeline]
    OBS --> APP2[Capability Approval Center]
    OBS --> RP[Session Replay]
```

## 8. Storage Layer Components

```mermaid
flowchart LR
    STORE[Hybrid Storage] --> PG[(PostgreSQL: facts, DDL)]
    STORE --> QD[(Qdrant: embeddings)]
    STORE --> GDB[(Graph DB: relations)]
    STORE --> FS[(Filesystem: artifacts)]
    STORE --> TIER[Memory Tier Manager]
    TIER --> HOT[Working/Episodic]
    TIER --> WARM[Semantic]
    TIER --> COLD[Cold Archive]
```
