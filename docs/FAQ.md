# FAQ

Frequently asked questions. Read the doc linked in each answer for the
full detail.

## Why didn’t you build a custom kernel?

See `docs/KERNEL.md`. A custom kernel (BORE, CachyOS, Rust-for-Linux)
is fragile because `CONFIG_RUST=y` pins a specific
Rust-for-Linux toolchain, and the BORE/CachyOS patches drift between
minor kernel versions. The Fedora kernel already ships `PREEMPT_DYNAMIC`,
`NO_HZ_FULL`, `HZ_1000`, `SCHEDUTIL`, and modern AMD/Intel P-state
drivers. Shipping the Fedora kernel is lower risk and already the right
amount of gaming optimisation.

## Why do the daemons get packaged without compiling them in rpmbuild?

Building a full Cargo workspace inside every RPM is expensive (8 minutes
per package, 42 daemons). Instead we run `cargo build --workspace
--release` once, and the RPM specs copy the prebuilt binaries from
`target/release/` into the buildroot. This is what makes the host-side
build fast. The daemons are built in `rpmbuild` only if you want to
prove them; in production the container does the heavy work.

## Why is `synthex-update-sync apply` a no-op for the actual rebuild?

Because the **actual** fetch+compile must run in the Fedora builder
container (it needs network + a build environment). The orchestrator is
correct and honest: it takes a snapshot and writes a real
`queue.jsonl`. Claiming it "rebuilt+imported" without doing so would
be a lie; we removed that. `docs/UPDATER.md`.

## Why does `verify.sh` use sandbox paths?

Because we don’t want the **test** itself to touch your real
`/var/lib/synthex`, `/var/cache/synthex`, or `/etc`. Everything runs in
a `mktemp -d` sandbox (via `SYNTHX_*` env vars). This makes the harness
safe to run on any host, including CI. `docs/REFERENCE.md`.

## Why do you ship a swap of RAM (zram) instead of disabling swap?

zram is **compressed RAM**, not disk IO — it keeps pages in memory while
giving you swap semantics. It never destroys disk swap (we preserve it
as fallback). It’s the safe default that avoids the classic "swap
spinning" on 8–16GB machines. `docs/PERFORMANCE.md`.

## Why do you default the CPU governor to `schedutil`, not `performance`?

Because forcing `performance` on laptops both drains battery and heats
it. `schedutil` ranges the cores already; `performance` is opt-in via
`synthex-gov max`. We keep the safe default. `docs/PERFORMANCE.md`.

## Why don’t you enable DBus/Port/NVIDIA “gamebois” claims?

Because we don’t fake features. The `synthex` console only does what the
actual daemons support. `docs/AIOS.md`.

## Why is `synthex` a shell script, not a big C++/Rust app?

Because the AI functionality lives in `synthex-brain` /
`synthex-hermes`. The console is a thin, **local-first** front end that
forwards to them (`recall`, `status`) and falls back to AETHER if
needed. Shell is fine for a dispatcher; a bigger client would just
re-explain what the daemon already provides. `docs/AIOS.md`.

## I added a package to `synth-pkgs.conf`; `status` shows `n/a`.

That means Fedora’s Bodhi returned no update for that name. Many base
Fedora packages never go through Bodhi. It’s normal. The orchestrator
still stages them (it has a `candidate.json`); it just can’t claim a
specific “update available” until you switch to the repodata-based
upstream check (a future enhancement). `docs/UPDATER.md`.

## `synthex install <pkg> --yes` on a non-dnf host does nothing?

Yes. On a plain Linux Mint box `dnf` isn’t installed, so the installer
**simulates** the commands (non-destructive) and steps back to confirm.
That’s deliberate: you don’t want the AIOS install experiments bubbling
a package manager you don’t have. On a real SynthOS (Fedora-based) box,
`dnf` is present and installs for real.

## Why should `sudo grep createrepo_c` exit clean?

Because `createrepo_c` is a real binary (`createrepo-c` package on
Debian/Ubuntu). In `build/scripts/local-repo.sh` we detect it. If you
get the *other* error (rpm build), the fix is in `~/.rpmmacros`.

## I want CI. What’s the one thing to gate on?

The exit code of `configs/tests/verify.sh`. Add it to your pre-merge /
pre-push hooks:

```bash
if ! (cd linux-synthex && configs/tests/verify.sh); then
  echo "AIOS verify failed" ; exit 1 ; fi
```

## Is the ISO done? / Is it bootable?

The pieces are wired and verifiable. The **final** ISO is not produced
in this environment — assembling it runs **in the Fedora 41 container**
(with livecd-creator / lorax). `build/run-iso-build.sh` is the one
command; it’s a long, network-heavy job meant for a monitored run. See
`docs/ISO.md` and `docs/KERNEL.md`.

## Where’s the actual source code of the AI daemons?

Under `src/` — e.g. `src/synthex-brain/`, `src/synthex-hermes/`,
`src/synthex-system-daemon/` etc. They’re compiled into the 42 binaries
in `target/release/` (see `docs/DAEMONS.md`). The assistant console is a
thin wrapper over the brain/hermes + AETTER on the local bus.

## I want to add one thing. Where do I start?

Read `docs/EXTENDING.md` — it has a recipe for:
- a new daemon,
- a new tracked package,
- a new sysctl default,
- a new persona,
- a new kickstart edition,
- a new verify-harness test.

Then `docs/PACKAGING.md` for the spec conventions, and
`docs/RUNBOOK.md` for the exact commands.

## More detail?

Every file that behaves at runtime has an entry in `docs/REFERENCE.md`
(the forensic reference). Start there if you’re debugging today’s
`verify.sh`-failing step.