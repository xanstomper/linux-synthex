# 14 — Directory Structure

The complete planned `aether/` tree (design + future source). Only `docs/` and `README.md` exist today; the rest is the target layout from [13-rust-plan.md](./13-rust-plan.md).

```
/home/jewboy420/linux-synthex/aether/
├── README.md                      # index (this repo root)
├── docs/                          # all design deliverables (01–20)
│   ├── 01-architecture.md
│   ├── 02-components.md
│   ├── 03-event-flow.md
│   ├── 04-data-models.md
│   ├── 05-memory-schema.md
│   ├── 06-graph-schema.md
│   ├── 07-capability-broker.md
│   ├── 08-security.md
│   ├── 09-agent-runtime.md
│   ├── 10-workspace-model.md
│   ├── 11-api.md
│   ├── 12-db-schema.md
│   ├── 13-rust-plan.md
│   ├── 14-directory-structure.md
│   ├── 15-mvp-roadmap.md
│   ├── 16-production-roadmap.md
│   ├── 17-scaling-roadmap.md
│   ├── 18-threat-model.md
│   ├── 19-benchmark-plan.md
│   └── 20-cognitive-features.md
├── Cargo.toml                     # rust workspace (future)
├── crates/                        # rust crates (future)
│   ├── aether-core/  aether-memory/  aether-graph/
│   ├── aether-broker/  aether-runtime/  aether-eventbus/
│   ├── aether-sentinel/  aether-cognitive/  aether-workspace/
│   ├── aether-api/  aether-storage/  aether-sandbox/  aether-common/
├── proto/                         # gRPC .proto definitions
├── configs/                       # aether.toml, policies, sentinel rules
│   ├── aether.toml
│   ├── capabilities.yaml
│   ├── sentinel/
│   │   ├── yara/   sigma/   feeds/   policies/
├── ui/                            # SynthOS Mission Control (future)
│   ├── overlay/  themes/  brain-pane/
├── scripts/                       # install, migrate, replay tooling
├── migrations/                    # SQL + graph schema migrations
├── tests/                         # integration / fuzz
└── systemd/                       # aetherd.service, aether-sentinel.service
```

## Runtime State (host)

```
/var/lib/aether/
├── artifacts/                     # content-addressed blobs
├── snapshots/                     # time-machine deltas
├── models/                        # local LLM cache
├── eventlog/                      # append-only event segments
└── graph/                         # graph db data dir
/etc/aether/                       # config + policies
```

## Notes
- `docs/` is the single source of design truth; code crates reference doc numbers in module headers.
- `configs/sentinel/` ships default YARA/Sigma rules; feeds pulled at runtime (air-gapped optional).
- `ui/` is the Mission Control overlay (see 10); built separately from the daemon.
