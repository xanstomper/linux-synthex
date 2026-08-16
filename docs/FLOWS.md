# Flows & State Machines

The operational flows that the AIOS layer actually executes. Wire format,
state transitions, rollback semantics.

---

## Flow A — `synthex install <x> --yes`

```
 ┌─ resolve(dnf cmd) ─┐
 │  nvidia: dnf install -y nvidia-driver nvidia-modprobe
 │  ...
 └────────┬────────────┘
          │
          v
   [ pre-snapshot: synthex-snapshot create pre-<x> ]
          │ (if synthex-snapshot missing → warn, continue)
          v
   [ dnf install -y <cmd> ]
          │
   ┌──────┴──────┐
   │ success     │ fail
   │   v         v
   │ doctor      snapper rollback  -> exit 1
   │ verify
   │ exit 0
```

Guarantees:
- Without `--yes`, the command **never** runs (dry-run only).
- If `dnf` isn’t present (host), it simulates (non-destructive).
- Snapshot first, rollback on failure.

State:
```
(never run) --pre-snapshot--> (running) --ok--> (done, doctor)
                    |                          \
                    | fail                      nok→ (rollback) -> (rolled back)
                    v
              (rollback)
```

## Flow B — `synthex-update-sync apply`

```
  for tracked pkg:
     upstream_latest(name) via Bodhi (network, best-effort)
     [stage]      writes <STAGE>/<name>/candidate.json  (network info)
  ...
  apply:
     [ pre-snapshot: synthex-snapshot create pre-update ]  (if tool present)
     appends to <REPO>/queue.jsonl:
        {"pkg": name, "repo": repo, "to": "builder", "requested": ...}
     writes <STATE>/update-state.json: {queued:N, rollback:..., snapshot:...}
```

- It does **not** perform a rebuild — it writes a real queue for a
  later step.
- `rollback` reads `update-state.json` and calls
  `synthex-snapshot rollback` or `snapper -c root rollback`.

## Flow C — `synthex persona gamer/creator/…`

```
  synthex-persona <profile>
    |  -- (list mode) if no arg → print menu, exit
    |  install meta package via dnf (simulate if no dnf)
    |  enable/disable units per profile (always idempotent, || true)
    v
  echo "synthex persona is now: <profile>"
```

## Flow D — first boot (`synthex-defaults.service` → `synthex-defaults`)

`synthex-defaults enable-all`:

```
  if snapper + /etc/snapper/configs/root → snapper create firstboot-default
  for each unit in (zram, predictive, predictive-launch, brain, hermes,
                     snapshot, snapper-timeline, btrfs-scrub, fstrim):
     if list-unit-files $u → systemctl enable $u
  if zram present → start
  print "synthex-defaults: done"
```

This is what lives on a **live** image. On a normal installed box,
`/etc/synthex/live-mode` won’t exist (unless the kickstart touched it);
`ConditionPathExists` gates the oneshot so it runs only once.

## Flow E — `synthex` console

```
synthex <cmd> [args]
   status  → $BRAIN status  (or aether socket probe)
   ask "q" → $BRAIN recall "q"  → fallback aether
   memory  → $BRAIN status
   doctor  → $synthex-doctor
   persona → $syth-persona
   update  → $synthex-update-sync <sub>
   install → $synthex-install
   help    → usage
```

Precedence: `synthex-hermes` > `synthex-brain` > `synthex-workspace-ai`
(whichever exists on `$PATH` first). If none, falls back to AETHER;
if AETHER isn’t listening, prints a helpful message and exits 0.

---

## State files

| File | Written by | Read by | Schema |
|---|---|---|---|
| `/var/lib/synthex/update-state.json` | `apply` | `rollback` | `{queued, at, rollback, snapshot}` |
| `/var/cache/synthex/updates/<name>/candidate.json` | `stage` | `apply`/daemon | `{name, latest, at}` |
| `/var/lib/synthex/repo/queue.jsonl` | `apply` | Fedora builder | one JSON per package |
| `/run/synthex/governor` | `synthex-gov` | any */kill trigger | last governor |

---

## Idempotency / reversibility

Every **modifying** operation (install, apply, persona-toggling units,
first-boot enable) is either:

- **idempotent** (running twice is safe — units already enabled,
  queue lines appended, snapshots only if the tool is present), or
- **reversible** (snapshot before, rollback after).

The only non-idempotent append is `queue.jsonl` (it accumulates until
the builder consumes it). That’s by design — the queue is a persistent
log of work, not a reversible side effect.

---

## The one non-reversible default

`synthex-gov max` sets `performance`. To restore, run
`synthex-gov balanced` (`schedutil`). There’s no "persistent across
reboot" lock-in — it’s just a `/sys` write until reboot, after which
the default `schedutil` is loaded again. If you want it to persist,
you’d add it to `/etc/ssc` (not shipped).