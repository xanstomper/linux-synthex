# 19 — Benchmark Plan

Defines how to measure AETHER CORE against the MVP/Scaling targets (17). All benchmarks are reproducible via `scripts/bench`.

## 1. Dimensions & SLIs

| Dimension | SLI | Target |
|-----------|-----|--------|
| Agent spawn | cold→ready latency | <200ms (prewarmed), <2s cold |
| Retrieval | p50/p95 semantic+graph | <50ms hot / <800ms cold |
| Event ingest | sustained events/sec | ≥100k/s at scale |
| Memory store | write p95 | <10ms |
| Graph traversal | 3-hop @1M nodes | <200ms |
| Replay | reconstruct 1h @1k/s | <30s |
| Token validate | p99 | <1ms |
| Footprint | idle RSS | <150MB |

## 2. Workload Generators
- `bench-agent`: spawns N agents issuing mixed intents (read/write/exec).
- `bench-event`: replays synthetic + real event streams at target rates.
- `bench-graph`: bulk-load M nodes/edges; run Cypher-like query suite.
- `bench-retrieval`: queries across tiers with configurable cache hit ratio.

## 3. Methodology
1. Ephemeral PG + Qdrant + graph via testcontainers.
2. Load with `bench-*` at递增 N (5 → 25 → 100 agents; 10k → 1M → 5M nodes).
3. Capture metrics: Prometheus scrape + `tracing` spans; export to JSON.
4. Soak (12h) for memory leaks / drift; chaos (kill runtime shard) for recovery.

## 4. Cognitive Benchmarks
- **Consolidation quality:** precision/recall of dedup merges; crystallized-fact agreement vs human label.
- **Attention/Curiosity:** diversity of explored graph regions; serendipity hit-rate (useful unexpected links).
- **Dissonance/Truth:** false-fact injection detection rate; provenance correctness.

## 5. Security Benchmarks
- Detection latency for YARA/Sigma/AI lanes on a labeled malware + injection corpus.
- False-positive rate on benign agent traffic (target <1%).
- Reversibility: time-to-rollback of a destructive op (target <5s).

## 6. Reporting
- `scripts/bench --emit report.md` → table + charts (latency CDF, throughput).
- Gating: CI fails if p95 retrieval or spawn regresses >15% vs baseline.

## 7. Tooling
- `tokio` load drivers; `hdrhistogram` for latency; `criterion` for micro-benchmarks; `grafana` dashboards.
