# Troubleshooting

Quick fixes for the most common failures.

## Verify harness fails

```
$ configs/tests/verify.sh
FAIL up: apply.log written
```

We renamed the artifact. The harness now checks `queue.jsonl` (the real
build queue), not `apply.log` (which used to be a fake). If you see
"queue.jsonl" missing, your `synthex-update-sync.py` is out of date. Pull
the latest version from `configs/upstream/synthex-update-sync.py`.

## `synthex-update-sync` errors with "could not read synth-pkgs.conf"

The config file uses **comment-tolerant JSON** (`//` line comments OK).
Make sure your file is at one of:

- `$SYNTHX_CFG` env var, or
- `/etc/synthex/upstream/synth-pkgs.conf`, or
- the path passed via `-c` (not currently implemented).

The shipped config is `configs/upstream/synth-pkgs.conf`.

## "Macro %_unitdir has empty body"

`rpm` on Ubuntu/Mint doesn't define Fedora's systemd macros. The fix is
in `~/.rpmmacros`:

```
%_unitdir /usr/lib/systemd/system
%_userunitdir /usr/lib/systemd/user
%_udevrulesdir /usr/lib/udev/rules.d
```

If you copy the block from `docs/PACKAGING.md#macro-conventions` into
`~/.rpmmacros`, every spec referencing these macros builds cleanly.

## "fg: no job control" in %build

This is `%meson` or `%py3_build` running under bash as `/bin/sh`
(`dash` on Ubuntu). The fix is again in `~/.rpmmacros`:

```
%__meson meson
%meson_build %__meson %{?_smp_mflags}
%meson_install %__meson install -C build --destdir %{buildroot}
%py3_build %{__python3} setup.py build
%py3_install %{__python3} setup.py install --root=%{buildroot}
```

For Python specs that don’t actually compile (just data files), edit the
spec to replace `%build` with `true`.

## `livecd-creator` fails with "Could not find kernel"

You forgot to add the kernel packages in the kickstart. They must be in
`%packages`:

```
kernel
kernel-core
kernel-modules
kernel-modules-core
kernel-modules-extra
```

`%post` should also enable the kernel via `systemctl enable ...`. The
patched kickstarts (`*-local.ks`) already include this; if you’re
copying an unpatched one, you’ll hit this.

## `livecd-creator` fails with "No space left on device"

The container is writing to the bind-mounted host path
(`build/repo/iso-out/`) and that’s where your disk lives. Make sure the
host has at least **8 GiB free** for the live root + squashfs, plus a
few GiB for the ISO image itself.

```
$ df -h /
```

If you’re near 100% full, free some space or mount a separate drive at
`build/iso-out/`.

## "File not found: .../usr/bin/synthex-..." during RPM packaging

The spec’s `%files` lists a file that `%install` never created. Common
causes:

- `%install` uses `%meson_install` but you removed `%build` and the
  binary wasn’t produced.
- `%install` uses `cp -r src/...` but the tarball doesn’t have that
  path (regenerate with `build/scripts/make-srctars.sh`).
- The spec references `%{SOURCE1}` etc. without declaring them in the
  header.

Fix: edit `%files` to match what `%install` actually creates, or fix
`%install` to create what `%files` declares.

## Bodhi returns "no-data" for a tracked package

Bodhi tracks updates through its own pipeline. Some packages are in
Fedora base + updates but never go through Bodhi — `nvtop` is an example.
In that case Bodhi returns empty (which the orchestrator treats as
“n/a”). The package still works; it just doesn’t show an “update
available” signal. This is normal and not a bug.

If you want to track a non-Bodhi package, fetch its version from the
primary Fedora repodata instead — but the current `upstream_latest`
function uses Bodhi. Extending it is left as a future exercise; the
current behavior is honest (it says “n/a”).

## "Permission denied: /var/lib/synthex/update-state.json"

The state file is owned by root and the update-sync was run as your
user. Either run with `sudo`, or export `SYNTHX_STATE` to a path your
user can write:

```bash
SYNTHX_STATE=/tmp/synthex-state.json synthex-update-sync apply
```

The state, stage, repo, and snap paths are all env-overridable
(`SYNTHX_CFG`, `SYNTHX_STAGE`, `SYNTHX_STATE`, `SYNTHX_REPO`,
`SYNTHX_SNAP`) — see `docs/UPDATER.md#configuration-via-env`.

## "No such file or directory" while building the daemon specs

The daemon specs (`synthex-stored`, `synthex-system-daemon`, …) need a
**prebuilt** release binary at `target/release/<name>`. Run:

```bash
cargo build --workspace --release
```

This produces 42 binaries in `target/release/`. The daemon specs detect
those and skip the in-rpmbuild cargo compile.

If you see the error **after** running the build, the spec might have
a typo for the binary name (e.g. `synthex-kernel-manager-rs` installs
`target/release/synthex-kernel` which we copy from the actual binary
`target/release/synthex-kernel-manager`). The wiring in `synthex-aios`
or in the spec itself fixes this — see the patched daemons in
`packages/spec-files/synthex-*.spec`.

## "Docker daemon not running"

```bash
sudo systemctl start docker
# or, if systemctl can't:
sudo nohup dockerd --iptables=false >/tmp/dockerd.log 2>&1 &
```

## Building many specs is slow

Use the timeout-aware helper:

```bash
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-brain.spec ...
```

It runs each spec with a 90-second timeout (so a broken spec doesn’t
hang forever) and prints OK/FAIL per spec.

## `docker pull fedora:41` hangs / fails

```
$ sudo docker pull fedora:41
```

If you see TLS or DNS errors, the host may be behind a firewall. Try
pointing Docker at a mirror via `/etc/docker/daemon.json`:

```json
{
  "registry-mirrors": ["https://mirror.gcr.io"]
}
```

Then `sudo systemctl restart docker`.

## "livecd-creator: No such file or directory: '/usr/sbin/synthex-snapshot'"

The AIOS layer is supposed to install `synthex-snapshot`, but the
`%post` of `synthex-aios` runs `systemctl ... 2>/dev/null` for units
that don’t exist — including `synthex-snapshot.service`. This is
expected; the unit is only created if `synthex-snapshot` is actually
shipped. Once you have a real `synthex-snapshot` binary in
`/usr/sbin/`, enable the unit and the warning goes away.

If you actually need the warning gone right now, just `touch
/usr/sbin/synthex-snapshot && chmod +x /usr/sbin/synthex-snapshot` —
it’s a stub that returns 0 and is enough to keep the post-install
quiet.
