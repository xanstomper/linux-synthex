# Updater (Mint/Bazzite-style)

The `synthex-update-sync` feature is the **follow-the-upstream, never-brick**
coordinator that mirrors Mint/Bazzite/Nobara-style update followers. It
does **not** perform the actual build — that runs in the Fedora builder
container. What it does is **honest orchestration**: detect, record,
queue, snapshot.

See `docs/AIOS.md#synthex-update-sync--mintbazzite-style-upstream-trackerusrsbinsynthex-update-sync`
for the CLI surface. This document focuses on **what the orchestrator
does and does not do**, and the operational model.

## What is the real contract

```
┌──────────┐  HTTP  ┌───────────────────────────────┐
│ Bodhi    │◀──────│  synthex-update-sync check/   │
│ (Fedora) │       │     status                    │
└──────────┘       │                                │
                   │  • compares installed to latest │
                   │  • writes candidate.json      │
                   │  • (apply) takes snapshot     │
                   │  • writes queue.jsonl         │
                   └──────────────┬────────────────┘
                                  │
                                  ▼
                       ┌──────────────────┐
                       │   queue.jsonl     │
                       │   update-state    │
                       └─────────┬────────┘
                                 │
                                 ▼
                  ┌────────────────────────────┐
                  │ Fedora builder container     │
                  │ • reads queue.jsonl         │
                  │ • runs rpmbuild / mock      │
                  │ • publishes into local repo  │
                  │ • synthex-snapshot rollback  │
                  │   if install fails           │
                  └────────────────────────────┘
```

**The orchestrator is honest**: it never claims a rebuild happened. If
you see a `queue.jsonl` line, it means a real Fedora builder job should
consume that line.

## States and transitions

The state file (`/var/lib/synthex/update-state.json`) records:

```json
{
  "queued": 5,
  "at": 1779123456.0,
  "rollback": "snapper" or "none",
  "snapshot": "pre-update" or null
}
```

- `queued`: number of rebuild jobs written into `queue.jsonl` by the
  last `apply`.
- `at`: epoch time of the last `apply`.
- `rollback`: tool available for rollback (`snapper`, `synthex-snapshot`,
  or `none`).
- `snapshot`: the snapshot description the next `rollback` should use.

## Operational workflow

### 1. Configure tracked packages

Edit `/etc/synthex/upstream/synth-pkgs.conf` (see `docs/AIOS.md` for the
full schema). Add the package names you want to track. For each tracked
package, the loader will:

- Query Bodhi for the latest title.
- Compare against the locally installed version (`rpm -q`).
- Stage and queue accordingly.

### 2. Check + stage daily (or on a timer)

The `synthex-sync-updates.timer` runs daily at 04:00 (`OnCalendar=*-*-*
04:00:00 Persistent=true`) and invokes:

```bash
/usr/sbin/synthex-update-sync stage
```

This populates `/var/cache/synthex/updates/<pkg>/candidate.json`.

### 3. Apply (snapshots first)

`synthex-update-sync apply` is the **only** command that may modify the
system outside the local cache. It does this:

1. **Snapshot** via `synthex-snapshot create pre-update`.
2. Appends one `queue.jsonl` line per tracked package.
3. Records the snapshot in `update-state.json`.

If you’re not running the Fedora builder container yet, the queue just
accumulates. When the container picks it up, it builds + publishes into
the repo.

### 4. Rollback (if a published build breaks)

```bash
synthex-update-sync rollback
```

This invokes `synthex-snapshot rollback` or `snapper -c root rollback`,
restoring the pre-apply state. Use it immediately if the latest apply
went bad.

## Why we don’t claim a rebuild here

The previous version of this script wrote a log line that said
`rebuilt+imported gamescope ...`. **That was a lie.** We removed it.
The orchestrator now writes a real `queue.jsonl` and tells you where
the rebuild happens:

```
synthex: queued 5 rebuild job(s) for the Fedora builder -> queue.jsonl
```

Honest: a line in `queue.jsonl` means “the builder must do this”, not
“this already happened”.

## What is shipped in this repo

- The orchestrator: `configs/upstream/synthex-update-sync.py`
- The config: `configs/upstream/synth-pkgs.conf` (in the RPM at
  `/etc/synthex/upstream/synth-pkgs.conf`)
- The timer + service: `configs/aios/synthex-sync-updates.{service,timer}`
  (in the RPM under `/usr/lib/systemd/system/`)
- The CLI wiring: `configs/aios/synthex update …` (in `/usr/bin/synthex`)

## Verification

`configs/tests/verify.sh` runs `status`/`stage`/`apply`/`rollback` in a
sandbox and asserts the real `queue.jsonl` was written. See the harness
output.

## Failure modes and recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| `status` returns nothing | No network to Bodhi | run later (offline-tolerant) |
| `apply` writes no `queue.jsonl` | Tracker empty / all disabled | edit `synth-pkgs.conf` |
| `rollback` says "no snapshot tool available" | No `synthex-snapshot` / `snapper` | install `snapper` + btrfs |
| Bodhi returns empty for a package | Only released in non-fedora repo (rpmfusion etc) | the tracker still works; empty title means no Fedora-side update yet |

## Extending the tracker

See `docs/EXTENDING.md#adding-a-new-tracked-package`.
