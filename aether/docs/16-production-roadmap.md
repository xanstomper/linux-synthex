# 16 — Production Roadmap

Beyond MVP: harden, integrate, and make it safe for daily multi-agent desktop use.

## P1 — Reliability & Ops (0–3 mo post-MVP)
- High-availability event log (WAL + replication); crash-safe replay.
- Health/metrics (Prometheus + OpenTelemetry); structured tracing for every trace_id.
- Automated migrations; blue/green config rollout; policy dry-run mode.
- Backup/restore for PG + graph + artifacts; disaster replay test.

## P2 — Full Sentinel (1–4 mo)
- AI Anomaly model trained on local event corpus.
- Malware Analysis Sandbox (gVisor air-gap) wired into ingest.
- System Integrity Engine (eBPF runtime measurement); TPM-backed key storage + key rotation.
- Forensics Engine + incident timelines; Security Copilot agent.

## P3 — Full Capability Catalog (2–5 mo)
- Remaining capabilities: UseKubernetes, SystemControl, Email, Calendar, MCP, Custom.
- Approval workflows with multi-party / quorum for critical ops.
- Sandbox variety: Docker, K8s job sandboxes, browser isolation.

## P4 — Cognitive Maturity (3–6 mo)
- All 18 cognitive features (20) operational and cross-validating.
- Truth Engine + Knowledge DNA + Personal Operating Theory.
- Agent Reputation / Mentorship / Debates loops.

## P5 — Multi-User & Governance (4–7 mo)
- Person/role model; shared vs private workspaces; delegation.
- Policy-as-code (Rego/CEL); compliance export; tenant isolation.
- Audit attestation + SOC2-style controls documentation.

## P6 — Ecosystem (6–9 mo)
- MCP server registry; plugin marketplace for capabilities.
- Public gRPC client SDKs (Rust/TS/Python); web Mission Control.
- Federated AETHER nodes (peer graph sync, selective sharing).

## Exit Criteria for "Production"
- 99.9% daemon uptime over 30 days; zero un-audited privileged actions.
- All critical ops reversible; mean forensic reconstruction < 5 min.
- Full cognitive suite live; Sentinel L3 auto-containment verified.
