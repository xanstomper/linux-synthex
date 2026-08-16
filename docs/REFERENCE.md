# Reference — Every File Documented

This is the **complete reference** for every file in `configs/aios/`,
`configs/upstream/`, `configs/performance/`, and `configs/tests/`. For
each file: purpose, runtime behavior, every option/parameter, environment
variables, integration points, failure modes, and how to test.

If you’re looking for *what* to use when (decisions), see `docs/AIOS.md`,
`docs/PERFORMANCE.md`, `docs/UPDATER.md`. This document is the **forensic
reference** — read it when you’re debugging or modifying.

---

## Top-level files

### `configs/tests/verify.sh`

The verification harness. One file, one purpose: prove the AIOS layer
works end-to-end in a sandbox. **Run it any time** with
`configs/tests/verify.sh; echo $?`.

What it covers (each section is gated and prints PASS/FAIL):

| Section | What it asserts | How |
|---|---|---|
| Syntax gates | Every bash script lints (`bash -n`) | direct check |
| Python compile | `synthex-update-sync.py` is valid Python | `python3 -m py_compile` |
| Config JSON | `synth-pkgs.conf` parses as JSON (with `//` comments stripped) | `python3` parser script |
| update-sync | `status`, `stage`, `apply`, `rollback` all run in a sandbox | runs in `$WORK` (mktemp) |
| update-sync queue | A real `queue.jsonl` is written by `apply` | `-s` check |
| synthex CLI | `status`, `memory`, `ask` work against the **real** `synthex-brain` | direct invocation |
| synthex-install | Dry-run prints a real plan | `synthex-install nvidia` |
| doctor | Runs to completion | direct invocation |
| persona | Lists profiles including ones we added | direct invocation |

**Why this matters**: this is the only automated test of the AIOS layer.
Every change in `configs/aios/`, `configs/upstream/`, or
`configs/performance/` should pass `verify.sh` before being committed.

Environment: no special environment needed. The script creates a tmp
dir under `$TMPDIR` (default `/tmp`) and exports sandbox paths via
`SYNTHX_CFG`, `SYNTHX_STAGE`, `SYNTHX_STATE`, `SYNTHX_REPO` so the
updater doesn't touch your real `/var`.

Extending: see `docs/EXTENDING.md#adding-a-test-to-the-verify-harness`.

---

## `configs/aios/` — the AI-OS layer

### `configs/aios/synthex` → `/usr/bin/synthex`

**Type**: shell CLI.

**Purpose**: local-first assistant console. Talks to `synthex-brain` /
`synthex-hermes` / `synthex-workspace-ai` (whichever exists first on
`$PATH`). If none is available, falls back to AETHER at
`127.0.0.1:8787`. If both fail, prints a helpful message instead of
crashing.

**Subcommands**:

| Subcommand | Maps to | Output |
|---|---|---|
| `status` | `$BRAIN status` or AETHER probe | brain status text + aether socket state |
| `memory` | `$BRAIN status` | brain memory-graph state |
| `verbs` (alias `capabilities`) | `$BRAIN status` | capability-broker verbs |
| `ask <q...>` | `$BRAIN recall <q...>` | brain recalled text |
| `think <q...>` | `$BRAIN recall <q...>` | same as `ask` |
| `ask` (no arg) | REPL | interactive prompt, type questions, Ctrl-D to exit |
| `doctor` | `/usr/sbin/synthex-doctor` | health report |
| `persona [g\|c\|d\|p\|m]` | `/usr/sbin/synthex-persona` | persona info / toggle |
| `update <check\|stage\|apply\|rollback\|status>` | `/usr/sbin/synthex-update-sync` | upstream tracker |
| `install <pkg\|preset> [--yes]` | `/usr/sbin/synthex-install` | install plan / executed install |
| `help` | (this file) | usage line |

**Environment**:

- `SYNTHEX_AETHER_HOST` (default `127.0.0.1`).
- `SYNTHEX_AETHER_PORT` (default `8787`).

**Failure modes**: if no brain binary is on `$PATH` and AETHER is not
listening, the `ask` and `think` subcommands print a helpful
“no daemon” message and exit 0. Never crashes.

**Testing**: see `configs/tests/verify.sh` — calls `status`, `memory`,
`ask "hello"` against the real `synthex-brain`.

---

### `configs/aios/synthex-doctor` → `/usr/sbin/synthex-doctor`

**Type**: bash.

**Purpose**: one-shot health/integrity report.

**Output**: a block-per-section summary:

```
SynthOS doctor — YYYY-MM-DD HH:MM:SS

filesystems:
  [OK]      / mounted
  [WARN]    root fs: ext4 (snapshots/rollback limited)

snapshots/rollback (sets):
  [WARN]    snapper not installed (rollback not available)

daemons (AI + system):
  [OK]      enabled synthex-system-daemon (not running)
  [WARN]    not present: synthex-brain

GPU/driver layer:
  [OK]      vulkan: <gpu>
  [WARN]    vulkaninfo missing (vulkan-loader/vulkan-tools not installed)
  [OK]      vulkan ICD present

update/reproducibility:
  [OK]      local repo present
  [OK]      dkms modules clean

disk & zram:
  [OK]   root:86% used, 33G free
  [WARN]    zram not active (synthex-zram)
```

**Read-only.** Never writes.

**Failure modes**: any missing tool prints `[WARN]`, not `[FAIL]`. The
exit code is always 0 (the script is informational). Don’t `set -e` on
its output — if you want a real health gate, write your own script
that fails on `[FAIL]` matches.

**Testing**: `verify.sh` asserts the script exits 0.

---

### `configs/aios/synthex-persona` → `/usr/sbin/synthex-persona`

**Type**: bash.

**Purpose**: pick a profile that pre-installs the right meta package
and toggles the right daemons.

**Usage**:

```bash
synthex-persona                          # list profiles
synthex-persona gamer                    # apply gamer profile
synthex-persona creator                  # apply creator profile
synthex-persona developer                # apply developer profile
synthex-persona privacy                  # apply privacy profile
synthex-persona minimal                  # apply minimal profile
```

**Profile map** (current):

| Profile | Meta package(s) installed | Units enabled/disabled |
|---|---|---|
| `gamer` | `synthex-meta-gaming` | enables `synthex-game-session`, `synthex-predictive`, `synthex-predictive-launch` |
| `creator` | `synthex-meta-creator` | enables `synthex-ai-daemon`, `synthex-webapp-engine` |
| `developer` | `synthex-meta-creator` + `synthex-meta-developer` | same as creator |
| `privacy` | (none — disables) | disables `synthex-webapp-engine` |
| `minimal` | (none — disables) | disables `synthex-predictive`, `synthex-predictive-launch`, `synthex-webapp-engine` |

**Behavior**:

- List mode (no args): prints the profile menu.
- Apply mode: runs `dnf install -y <meta>` (or simulates if `dnf` is
  absent — non-destructive on dev hosts), then `systemctl enable` /
  `disable` the appropriate units.
- All `enable`/`disable` calls use `|| true` so a missing unit never
  fails the persona.

**Failure modes**: a missing meta package prints a note but does not
fail. Missing units are silently skipped.

**Testing**: `verify.sh` calls `synthex-persona` (list mode) and
asserts the output includes `gamer`.

---

### `configs/aios/synthex-install` → `/usr/sbin/synthex-install`

**Type**: bash.

**Purpose**: snapshot-guarded, non-destructive installer.

**Usage**:

```bash
synthex-install nvidia|amd|intel|mesa|steam|codecs|pkgname [--yes]
```

**Presets** (case statements in `resolve()`):

| Preset | Resolves to |
|---|---|
| `nvidia` | `dnf install -y nvidia-driver nvidia-modprobe` |
| `amd` | `dnf install -y mesa-vulkan-drivers vulkan-radeon libva` |
| `intel` | `dnf install -y mesa-vulkan-drivers vulkan-intel intel-media-driver` |
| `mesa` | `dnf install -y mesa-vulkan-drivers mesa-va-drivers` |
| `steam` | `dnf install -y steam` |
| `codecs` | `dnf install -y ffmpeg gstreamer1-plugins-bad-free-extras` |
| (anything else) | `dnf install -y <input>` |

**Flow**:

1. Resolve → print the resolved command.
2. If `--yes` is **not** given → dry-run, exit 0. **Always dry-run by
   default** — the user must opt in.
3. If `--yes`:
   a. Call `synthex-snapshot create pre-<target>` if present (else warn
      and continue).
   b. Run `dnf install -y <cmd>` (or simulate non-destructively if
      `dnf` is absent).
   c. If `dnf` succeeded → run `synthex-doctor` smoke-check.
   d. If `dnf` failed → invoke `synthex-snapshot rollback` and exit 1.

**Output**: each phase prints `RUN: <cmd>` / `snapshot: ok` /
`install finished ok` / `doctor: ok` etc. so the operator sees exactly
what happened.

**Failure modes**:

- No `--yes` → dry-run, never modifies the system.
- No `dnf` (e.g. on this build host) → prints a simulation note, exits 0.
- No `synthex-snapshot` → snapshot step skipped, install still runs.
- `dnf` fails → rollback attempted, exit 1.

**Testing**: `verify.sh` runs `synthex-install nvidia` (dry-run) and
asserts the output contains `plan`.

---

### `configs/aios/synthex-defaults` → `/usr/sbin/synthex-defaults`

**Type**: bash.

**Purpose**: idempotently enable the “differentiator” units on first boot.

**Usage**:

```bash
synthex-defaults enable-all
```

**Behavior**: walks a fixed list of units:

```
synthex-zram.service
synthex-predictive.service
synthex-predictive-launch.service
synthex-brain.service
synthex-hermes.service
synthex-snapshot.service
snapper-timeline.timer
btrfs-scrub@-.timer
fstrim.timer
```

For each unit:

- If `systemctl list-unit-files <name>` returns it → `enable`.
- If `synthex-zram.service` exists → also `start` it.

If snapper is installed and `/etc/snapper/configs/root` exists, also
creates a `firstboot-default` snapshot.

**Failure modes**: silently ignores missing units and missing snapper.
Exits 0 always.

**Testing**: not in the verify harness directly (would need root for
systemctl). Smoke-tested manually on the host (`enable-all` ran, it
enabled `fstrim.timer`).

---

### `configs/aios/synthex-sync-updates.timer` + `.service`

**Type**: systemd units.

**Timer**: `OnCalendar=*-*-* 04:00:00 Persistent=true` — runs daily at
04:00 AM. The `Persistent=true` means missed runs are caught up on next
boot.

**Service**: `Type=oneshot ExecStart=/usr/sbin/synthex-update-sync stage`.

**WantedBy**: `multi-user.target` (timer) and `multi-user.target`
(service).

**Behavior**: every day at 04:00, the tracker stages the latest
candidate for each tracked package. To apply, run
`synthex-update-sync apply` manually (this is intentionally not
automated — apply should be an explicit operator decision, not a
midnight cron).

**Failure modes**: if `synthex-update-sync` is missing, the service
fails; the timer just logs and retries the next day.

---

### `configs/aios/install.sh`

**Type**: bash, idempotent.

**Purpose**: bake the AIOS layer into an image root (for livecd-creator
or a chroot build).

**Usage**:

```bash
./install.sh [installroot]   # default /
```

**Behavior**: copies the layer’s files to the install root:

```
/usr/bin/synthex                 (CLI)
/usr/sbin/synthex-defaults       (first-boot)
/usr/lib/systemd/system/synthex-defaults.service
/etc/snapper/configs/root        (starter btrfs config)
```

Exits 1 if the install root has no `/etc` directory.

**Testing**: not in the verify harness (would need to operate on a
fake root and check the layout).

---

### `configs/aios/post-install.sh`

**Type**: bash.

**Purpose**: `%post` snippet to enable the always-on pieces when the
AIOS layer ships in an image.

**Behavior**:

- Run the inner `install.sh` against the installed root.
- Enable `synthex-defaults.service` and `synthex-zram.service`.
- Enable `synthex-predictive.service` and
  `synthex-predictive-launch.service`.
- If snapper is available → enable timeline + scrub + fstrim timers,
  create a default snapshot.
- Print info on the perf sysctl files.

All `systemctl` calls use `|| true`.

---

## `configs/upstream/` — the Mint/Bazzite-style tracker

### `configs/upstream/synthex-update-sync.py` → `/usr/sbin/synthex-update-sync`

**Type**: Python 3.

**Purpose**: real, honest, never-bricks upstream tracker.

**Subcommands**:

| Subcommand | Effect |
|---|---|
| `status` | For each tracked package, print local version + Fed Bodhi latest |
| `check` | Same, with `(update)` flag when local < latest |
| `stage` | Write `candidate.json` per package into `${SYNTHX_STAGE:-/var/cache/synthex/updates}/<pkg>/` |
| `apply` | Snapshot (if `synthex-snapshot` present) + append one `queue.jsonl` line per tracked package into `${SYNTHX_REPO:-/var/lib/synthex/repo}/queue.jsonl` + record state |
| `rollback` | Read state; invoke `synthex-snapshot rollback` or `snapper -c root rollback` |
| `version <pkg>` | Print the latest upstream title for `<pkg>` from Bodhi |

**Environment**:

| Var | Default | Effect |
|---|---|---|
| `SYNTHX_CFG` | `/etc/synthex/upstream/synth-pkgs.conf` | config file |
| `SYNTHX_STAGE` | `/var/cache/synthex/updates` | where stage writes candidates |
| `SYNTHX_STATE` | `/var/lib/synthex/update-state.json` | last apply + snapshot info |
| `SYNTHX_REPO` | `/var/lib/synthex/repo` | where apply writes queue.jsonl |
| `SYNTHX_SNAP` | `/usr/sbin/synthex-snapshot` | snapshot helper |
| `SYNTHX_QUEUE` | `${SYNTHX_REPO}/queue.jsonl` | override queue path |

**Key functions**:

- `installed_ver(pkg)`: returns the locally installed RPM version, or
  empty if not installed.
- `upstream_latest(name)`: HTTP GETs Bodhi
  (`https://bodhi.fedoraproject.org/updates/?packages=<name>`) and
  returns the title of the latest update. Returns `None` on network
  failure.
- `repo_url(cfg, repo_name)`: returns the base URL for the given repo
  (`fedora`, `rpmfusion`, or `nobara`). For `nobara`, returns `""` when
  `enabled: false` (so the tracker effectively skips it).
- `stage()`: writes one `candidate.json` per package.
- `apply()`: snapshots, then appends to `queue.jsonl`.
- `rollback()`: reads state and runs the rollback tool.

**Failure modes**:

- Offline (Bodhi unreachable) → `upstream_latest` returns `None`;
  `status`/`check` print `n/a`. `stage`/`apply` still run.
- No `synthex-snapshot` → snapshot step skipped (logged); `apply` still
  writes the queue.
- Bodhi returns empty for a package → `n/a` (normal — many Fedora
  base packages never go through Bodhi).

**Testing**: `verify.sh` runs `status` / `stage` / `apply` /
`rollback` in a sandbox and asserts a real `queue.jsonl` was written.

---

### `configs/upstream/synth-pkgs.conf` → `/etc/synthex/upstream/synth-pkgs.conf`

**Type**: JSON (single top-level object, `//` comments allowed).

**Schema**:

```json
{
  "name": "<string>",
  "enabled": <bool>,
  "tracked": [
    { "name": "<display>", "repo": "<fedora|rpmfusion|nobara>", "pkg": "<actual>" }
  ],
  "repos": {
    "fedora":    "<url>",
    "rpmfusion": "<url>",
    "nobara": { "enabled": <bool>, "note": "<text>", "baseurl": "<url>" }
  }
}
```

**Defaults** shipped: gamescope, mangohud, lutris, wine, nvtop.

**Validation**: the orchestrator skips tracked entries where `pkg` is
missing or where the resolved `repo_url` is empty (i.e. Nobara disabled).

**Extending**: add a tracked entry by editing the file. Re-run
`configs/tests/verify.sh; echo $?` to confirm.

---

## `configs/performance/` — the safe tuning layer

### `sysctl.d/00-synthex-vm.conf` → `/etc/sysctl.d/00-synthex-vm.conf`

```sysctl
vm.swappiness=10
vm.vfs_cache_pressure=160
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.overcommit_memory=1
kernel.nmi_watchdog=0
kernel.sched_autogroup_enabled=0
vm.max_map_count=2097152
```

Applied at boot via systemd-sysctl. **Reversible**: comment out a line
or delete the file; defaults restore.

### `sysctl.d/00-synthex-network.conf` → `/etc/sysctl.d/00-synthex-network.conf`

```sysctl
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.core.netdev_max_backlog=16384
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 655360 16777216
net.ipv4.tcp_adv_win_scale=1
```

Applied at boot. **Reversible**.

### `synthex-gov` → `/usr/bin/synthex-gov`

**Type**: bash.

**Usage**:

```bash
synthex-gov max        # set CPU governor = performance
synthex-gov balanced   # set CPU governor = schedutil (default)
```

Writes `/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor`.
Exits 0 even if cpufreq is not available (silent no-op).

### `zram.service` + `zram-setup` → `/usr/lib/systemd/system/synthex-zram.service` + `/usr/share/synthex/performance/zram-setup`

**Type**: systemd unit + bash.

**Behavior**: on boot, `zram-setup` runs as a oneshot, creating
`/dev/zram0` as compressed RAM swap (lz4, half RAM, capped at 8 GiB,
priority 100). **Disk swap preserved** as fallback.

**Failure modes**: silently exits 0 if zram unavailable.

### `gamemode.ini` → `/etc/gamemode.ini`

**Type**: ini.

Used by Feral’s `gamemode` package when a game holds its token.
See `docs/PERFORMANCE.md#gamemodeini` for the full key reference.

### `synthex-game-session` → `/usr/bin/synthex-game-session`

**Type**: bash.

**Usage**:

```bash
synthex-game-session steam
```

Wraps the command in `gamescope --adaptive-sync --rt -f --`. Steam
launch options should reference this wrapper for best results.

### `grub-synthex.cmdline`

**Type**: documentation.

Suggested (commented) GRUB cmdline additions that pair with the
performance layer. Not auto-applied.

### `install.sh`

Idempotent baker that copies the performance files into an image root
or live system. See `configs/aios/install.sh` for the same pattern.

---

## `configs/tests/`

### `verify.sh`

Already documented above. **One command to prove the whole AIOS
layer works.** Exit code is your gate.

---

## How to extend without breaking the reference

When adding a new file:

1. Add it to the correct `configs/<area>/` directory.
2. Update the spec (`packages/spec-files/synthex-aios.spec` or a new spec)
   to include it.
3. Regenerate tarballs if it lives in the repo tree:
   ```bash
   build/scripts/make-srctars.sh 2026.10
   ```
4. Rebuild + re-sync.
5. Add a check in `configs/tests/verify.sh`.
6. Run `configs/tests/verify.sh; echo $?` — must be 0.

Add the new file’s docs to **this** file in the matching section.