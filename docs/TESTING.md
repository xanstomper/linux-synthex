# Testing

Everything you can run to verify the repo behaves as documented. The
short answer is in `docs/README.md`; this is the detailed **test
dictionary**.

## The one gate: `verify.sh`

```bash
configs/tests/verify.sh; echo $?
```

Exit 0 = the AIOS layer **and** the build/prove path is healthy. It is
the CI gate.

### What it actually runs (order)

| Check | Asserts | Failure looks like |
|---|---|---|
| `bash -n` aios devices | no syntax error | `FAIL bash: ...` |
| `python3 -m py_compile` update-sync | valid Python | `FAIL py: ...` |
| config JSON | `synth-pkgs.conf` parses | `FAIL config json` |
| `update-sync status` | lists tracked+real versions | `FAIL up: status lists tracked` |
| `update-sync stage` | writes `candidate.json`, no crash | `FAIL up: stage (no crash)` |
| `update-sync apply` | writes `queue.jsonl`, snapshot | `FAIL up: apply (no crash)` |
| `queue.jsonl` | real non-empty queue written | `FAIL up: queue.jsonl written` |
| `synthex status/memory/ask` | against the **real** `synthex-brain` | `FAIL cli status/memory/ask-ok` |
| `synthex-install nvidia` | dry-run prints plan | `FAIL install-ok dry-run` |
| `update rollback` | graceful no-op when no snap tool | `FAIL rollback (graceful)` |
| `doctor` | runs to completion | `FAIL doctor runs` |
| `persona` | lists profiles | `FAIL persona lists` |

### Running it in a true sandbox

It exports `SYNTHX_CFG`, `SYNTHX_STAGE`, `SYNTHX_STATE`, `SYNTHX_REPO`
to a `mktemp -d`, so nothing touches your real `/var`. That’s why it’s
safe to run on CI or a dev box.

### Making verify.sh slower/faster

`verify.sh` makes **real HTTP** to Bodhi in `update-sync status`. If
you’re offline, those checks still pass (they just print `n/a`) but they
can add latency. Set a short `curl -m 25` in `synthex-update-sync` is
already the bound. If you want to skip network entirely, provide a zeroed
`SYNTHX_CFG` (empty `tracked`) so no Bodhi call is made.

## 2. Per-tool manual tests

| Tool | Test (expected) |
|---|---|
| `synthex status` | brain status / no-daemon fallback |
| `synthex ask "…"` | recall line / fallback |
| `synthex memory` | brain status |
| `synthex verbs` | brain status |
| `synthex persona gamer` | enable gamemode + meta, prints “persona is now: gamer” |
| `synthex install nvidia` | dry-run plan |
| `synthex update status` | per-package N/A/update flags |
| `synthex-gov max` | prints `performance` (returns 0 even without cpufreq) |
| `synthex-game-session` | wraps a command in gamescope |

## 3. Build-level tests

```bash
# source tarballs (reproducible)
build/scripts/make-srctars.sh 2026.10
# each spec builds
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-system-daemon.spec ...
# repo indexes
( cd build/repo/noarch && createrepo_c . )
( cd build/repo/x86_64  && createrepo_c . )
```

## 4. ISO-level tests

See `docs/ISO.md`. The runner `build/run-iso-build.sh` validates the
ISO: squashfs superblock present, no Ubuntu kernel, single-pass xorriso.
`build/scripts/validate-iso.sh [ISO]` is the richer validator.

## 5. Test your new code the same way

1. Write the tool/script.
2. `bash -n` it.
3. `verify.sh` (exit 0).
4. Smoke it manually.
5. Add a line to `configs/tests/verify.sh` if it should be guarded.

`docs/EXTENDING.md` has the exact recipe for adding a new check.

## 6. Known test caveats

- `synthex-doctor` hits `snapper`, `vulkaninfo`, `dkms` — on a dev host
  these are absent → prints `WARN`. The harness only requires the
  script to **run** and exit 0 (`doctor runs`), not to print all-OK.
- `synthex-brain` is required for `cli status/memory/ask`. If it isn’t
  on `$PATH`, verify.sh prints `SKIP ... (no synthex-brain on this box)`
  and counts it as OK (so CI still runs where the AI toolchain isn’t).
- `update-sync` network steps: offline yields `n/a`, not failure.