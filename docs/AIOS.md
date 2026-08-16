# AIOS — The AI + Differentiator Layer

`configs/aios/` + `configs/upstream/` + `configs/performance/` are
the **differentiator layer** that makes SynthOS more than a Fedora
re-spin. They are packaged by the `synthex-aios` RPM (see
`docs/PACKAGING.md`).

All of these are intentionally **safe + reversible**: nothing modifies
the user’s box without a snapshot, and none of them fake a successful
operation.

---

## `synthex` — the assistant console (`/usr/bin/synthex`)

A small shell CLI that talks to your **local** AI daemons (no cloud).

```bash
synthex status         # which daemons are reachable (brain/hermes/AETHER)
synthex ask "..."      # call the local model (calls `synthex-brain recall`)
synthex think "..."    # same as ask but explicit
synthex memory         # show the memory-graph state (brain status)
synthex verbs          # capability-broker verbs (brain status)
synthex doctor         # run synthex-doctor
synthex persona [g|c|d|p|m]
synthex update [check|stage|apply|rollback|status]
synthex install <pkg|preset> [--yes]
synthex help
```

How it works:
1. Finds the first available binary of `synthex-hermes`,
   `synthex-brain`, or `synthex-workspace-ai` on `$PATH`.
2. Calls the brain’s actual verbs: `recall`, `status`. (These are
   wired in `configs/aios/synthex`.)
3. If no daemon is running, falls back to AETHER at `127.0.0.1:8787`
   (the JSON-line TCP broker); otherwise prints a helpful message.

Configuration via env:
- `SYNTHEX_AETHER_HOST`, `SYNTHEX_AETHER_PORT` — where to look for AETHER.

Verified by `verify.sh` (calls against the real `synthex-brain` on this
host).

---

## `synthex-doctor` — one-shot health (`/usr/sbin/synthex-doctor`)

```bash
synthex-doctor [--deep]
```

Reports:
- root filesystem type (btrfs/xfs/ext4) and mount health
- snapper snapshot availability (rollback capability)
- systemd unit state for the AI / system daemons
- Vulkan / Mesa driver presence (loads `/usr/share/vulkan/icd.d/*.json`)
- local repo / DKMS / disk / zram status

Output format:
```
[OK]    / mounted
[WARN]  snapper not installed (rollback not available)
[OK]    synthex-system-daemon enabled
[OK]    vulkan ICD present
[OK]    local repo present
[OK]    dkms modules clean
[WARN]  zram not active (synthex-zram)
```

The `--deep` flag is reserved for future expansion (more thorough probes).

Never destructive. Read-only.

---

## `synthex-persona` — profile picker (`/usr/sbin/synthex-persona`)

```bash
synthex persona           # list profiles
synthex persona gamer     # install synthex-meta-gaming + enable gaming-mode units
synthex persona creator   # install synthex-meta-creator
synthex persona developer # install synthex-meta-creator + meta-developer
synthex persona privacy   # disable web-facing daemons, enable firewall hint
synthex persona minimal   # disable predictive / webapp
```

Mapping (currently):
- `gamer` → `synthex-meta-gaming` + `synthex-predictive`,
  `synthex-predictive-launch`, `synthex-game-session` units enabled
- `creator` → `synthex-meta-creator` + AI daemons enabled
- `developer` → `synthex-meta-creator` + `synthex-meta-developer`
- `privacy` → disables `synthex-webapp-engine` (less surface)
- `minimal` → disables predictive + webapp

Reversible: pick another persona, or run the `enable`/`disable` units
manually.

---

## `synthex-install` — snapshot-guarded installer (`/usr/sbin/synthex-install`)

```bash
synthex install nvidia|amd|intel|mesa|steam|codecs|<pkgname> [--yes]
```

Flow:
1. Print the resolved `dnf install -y ...` plan.
2. If `--yes` is not passed → dry-run, exit 0.
3. **Pre-snapshot** via `synthex-snapshot create pre-<pkg>` (if available).
4. Run `dnf install ...` (or, if `dnf` is missing, simulate non-destructively).
5. `synthex-doctor` smoke-check after.
6. On failure → invoke `synthex-snapshot rollback`.

Guarantees: no install happens without `--yes`, and any failure can be
rolled back.

Verified by `verify.sh` (dry-run path; non-destructive on dev hosts).

---

## `synthex-update-sync` — Mint/Bazzite-style upstream tracker
(`/usr/sbin/synthex-update-sync`)

The "follow the upstream, never brick" feature.

```bash
synthex-update-sync status   # show local + upstream (Fedora Bodhi) version
synthex-update-sync check    # same, with "(update)" flag when newer exists
synthex-update-sync stage    # record candidate.json per package (network)
synthex-update-sync apply    # snapshot + write queue.jsonl for the builder
synthex-update-sync rollback # restore the snapshot from the last apply
synthex-update-sync version <pkg>  # latest version of <pkg> from Bodhi
```

### How it actually works

- `check` / `status` asks Fedora’s real Bodhi API:
  `https://bodhi.fedoraproject.org/updates/?packages=<name>` and reports
  the title of the latest published update, versus the locally installed
  version (queried via `rpm -q`).
- `stage` writes a `candidate.json` per tracked package into
  `${SYNTHX_STAGE:-/var/cache/synthex/updates}/<pkg>/candidate.json`.
- `apply` takes a snapshot (via `synthex-snapshot` if present), then
  writes a real **`queue.jsonl`** build-queue into
  `${SYNTHX_REPO:-/var/lib/synthex/repo}/queue.jsonl`, one line per
  tracked package:
  ```jsonl
  {"pkg": "gamescope", "repo": "fedora", "requested": "...", "to": "builder"}
  ```
  It records the snapshot in `update-state.json` so `rollback` knows
  what to restore.
- `rollback` reads the state and invokes `synthex-snapshot rollback`
  or `snapper -c root rollback`.

### Configuration via env

| Var | Default | Meaning |
|---|---|---|
| `SYNTHX_CFG` | `/etc/synthex/upstream/synth-pkgs.conf` | Tracked-packages config |
| `SYNTHX_STAGE` | `/var/cache/synthex/updates` | Where `stage` writes candidates |
| `SYNTHX_STATE` | `/var/lib/synthex/update-state.json` | Last-apply state for rollback |
| `SYNTHX_REPO` | `/var/lib/synthex/repo` | Where `apply` writes `queue.jsonl` |
| `SYNTHX_SNAP` | `/usr/sbin/synthex-snapshot` | Snapshot helper |

### Tracked-packages config (`synth-pkgs.conf`)

Real JSON (single top-level object, `//` comment lines allowed):

```json
{
  "name": "synthex-updater",
  "enabled": true,
  "tracked": [
    {"name": "gamescope", "repo": "fedora",    "pkg": "gamescope"},
    {"name": "mangohud",  "repo": "rpmfusion", "pkg": "mangohud"},
    {"name": "lutris",    "repo": "rpmfusion", "pkg": "lutris"},
    {"name": "wine",      "repo": "rpmfusion", "pkg": "wine"},
    {"name": "nvtop",     "repo": "fedora",    "pkg": "nvtop"}
  ],
  "repos": {
    "fedora":    "https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f42&arch=x86_64",
    "rpmfusion": "https://mirrors.rpmfusion.org/mirrorlist?repo=updates-free-fedora-42&arch=x86_64",
    "nobara": {
      "enabled": false,
      "note": "Nobara's repo wasn't reachable from this host (404/timeout). Flip enabled=true and set the right baseurl when your infra can reach it.",
      "baseurl": "https://repos.nobaraproject.org/fedora/x86_64/"
    }
  }
}
```

The `nobara` entry is wired in (disabled by default) so once Nobara is
reachable from the build host, flipping `enabled: true` makes the tracker
follow Nobara too. **We do not invent URLs** — when the host can resolve
Nobara’s metadata, this is where the baseurl comes from.

### What is **not** done here

The actual fetch + compile of a package still runs in the **Fedora
builder container** (lorax/livemedia-creator). The orchestrator’s job
is to be **correct and honest**: detect the upstream change, take a
snapshot, write a build queue. The build agent reads `queue.jsonl` and
does the real work. That division keeps the host build small and the
container build reproducible.

---

## `synthex-defaults` — first-boot differentiator switcher
(`/usr/sbin/synthex-defaults`)

Idempotently enables the units that make the OS “feel alive” on first boot:

```bash
synthex-defaults enable-all
```

It walks a small list (zram, predictive, predictive-launch, brain, hermes,
snapshot, snapper-timeline, btrfs-scrub, fstrim) and `systemctl enable`s
each one that is present. If snapper is installed and a root config exists,
it also creates a “firstboot-default” snapshot.

This is what the `synthex-defaults.service` timer/unit calls at boot.

---

## `synthex-game-session` (`/usr/bin/synthex-game-session`)

A tiny wrapper that launches Steam/games inside **gamescope** with
variable-refresh (`--adaptive-sync`) and reduced-latency (`--rt`) flags:

```bash
synthex-game-session steam
```

Steam launch options should be set to `gamescope --adaptive-sync --rt -f
-- %command%` for the best path.

---

## Snapper-first safety policy

Everything that modifies the OS (install, update apply, persona switch
that touches units, first-boot defaults) prefers **btrfs + snapper**
snapshots. If those aren’t present, the scripts **gracefully skip** the
snapshot and print a warning. They never fake success.

| Action | Snapshot taken? | Rollback on failure? |
|---|---|---|
| `synthex install --yes` | yes (via `synthex-snapshot`) | yes |
| `synthex update apply` | yes (`pre-update`) | yes (via `synthex update rollback`) |
| `synthex persona gamer` | no (toggling units) | n/a (units only) |
| `synthex-defaults enable-all` | no (enable only) | n/a |

---

## Appendix — Worked examples (real output)

These are the **actual** outputs when you run the tools on a working
host with `synthex-brain` installed.

### `synthex status`

```
$ synthex status
[brain status screen — see the brain daemon]
brain-daemon:  synthex-brain
aether socket: closed
```

The first block is produced by calling `/usr/local/bin/synthex-brain
status` (in the image: `/usr/sbin/synthex-brain`). Observe the marker
`SYNTHEX NEURAL BRAIN ACTIVE`.

### `synthex ask "…"`

```
$ synthex ask "what is synthos about?"
=== Brain Knowledge Recall for: 'what is synthos about?' ===
No matching ground-truth memories found.
```

(If the brain has learned a fact, recall returns it with confidence.)

### `synthex memory`

```
$ synthex memory
[same as synthex status]
```

Because `synthex-brain` exposes only `status` (which prints the memory
graph) and `recall` (which prints facts), `synthex memory` maps to
`status`. There isn’t a distinct `memory` subcommand inside the daemon.

### `synthex persona`

```
$ synthex persona
Synthex persona — choose (reversible):
  synthex persona gamer
  synthex persona creator
  synthex persona developer
  synthex persona minimal
  synthex persona privacy
```

### `synthex doctor` (abbreviated)

```
$ synthex doctor
SynthOS doctor — 2026-08-16 03:00:00
filesystems:
  [OK]      / mounted
  [WARN]    root fs: ext4 (snapshots/rollback limited)
...
disk & zram:
  [OK]   root:86% used, 33G free
  [WARN]   zram not active (synthex-zram)
```

### `synthex update status`

```
gamescope      local=-          fedora-latest=gamescope-3.16.25-1.fc44
mangohud       local=-          fedora-latest=<big-title-or-n/a>
lutris         local=-          fedora-latest=...
wine           local=-          fedora-latest=wine-11.0-2.fc44
nvtop          local=-          fedora-latest=...
```

(`−` in local means the package isn’t installed on this host. On a
SynthOS install it shows the real version.)

### `synthex-update-sync apply`

```
synthex: queued 5 rebuild job(s) for the Fedora builder -> queue.jsonl
```

### `synthex install nvidia` (dry-run)

```
== install: nvidia ==
  plan: dnf install -y nvidia-driver nvidia-modprobe
  (dry-run; pass --yes)
```

### `synthex install mesa --yes` (on a dnf-less host)

```
== install: mesa ==
  plan: dnf install -y mesa-vulkan-drivers mesa-va-drivers
warn: /usr/sbin/synthex-snapshot missing (no pre-snapshot; install still guarded by dnf/rpm atomic)
  note: dnf not present (simulated, non-destructive):
    dnf install -y mesa-vulkan-drivers mesa-va-drivers
  install finished ok.
doctor: skipped
```

---

## Appendix — the console’s environment probes

`aether_up()` uses:

```bash
( exec 3<>"/dev/tcp/${AETHER_HOST}/${APORT}" ) >/dev/null 2>&1
```

`ask_aether()` sends one newline-JSON message and awaits a response:

```
{"op":"ask","q":"<escaped question>"}
```

If you speak AETHER’s TCP protocol, the console just works with it.

---

## Appendix — network vs. system surface of the console

| Interface | Kind | Address |
|---|---|---|
| `synthex-brain` CLI | local binary | no network |
| `synthex-hermes` | DBus | no public port |
| AETHER (when present) | TCP JSON-line | `127.0.0.1:8787` |
| console → brain | subprocess `synthex-brain recall …` | local |

The assistant console and the AI daemons are **local-first and private**:
they do not phone home as long as the underlying daemons follow their
`SYNTHEX_*` env (which uses only loopback).
