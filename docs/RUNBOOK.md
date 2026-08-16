# Runbook — Step-by-Step Operations

This is the **operational cookbook**. Each procedure is a concrete
sequence of commands with expected outputs. If something is unclear in
the other docs, it’s clarified here.

---

## Procedure 0 — first time on a new host

```bash
# 1. apt deps (build toolchain + RPM helpers)
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    build-essential rpm python3 python3-build libelf-dev libssl-dev \
    libncurses-dev dwarves pahole openssl perl python3-dev bison flex \
    kmod lz4 zstd m4 diffutils bc createrepo-c xorriso squashfs-tools \
    librsvg2-bin coreutils curl docker.io

# 2. install the rpmmacros (see docs/PACKAGING.md#macro-conventions)
cat > ~/.rpmmacros <<'EOF'
%_topdir /home/jewboy420/linux-synthex/build/rpmbuild
%_tmppath %{_topdir}/tmp
%_sourcedir %{_topdir}/SOURCES
%_rpmdir %{_topdir}/RPMS
%_builddir %{_topdir}/BUILD
%_unitdir /usr/lib/systemd/system
%_userunitdir /usr/lib/systemd/user
%_udevrulesdir /usr/lib/udev/rules.d
%__meson meson
%meson_build %__meson %{?_smp_mflags}
%meson_install %__meson install -C build --destdir %{buildroot}
%py3_build %{__python3} setup.py build
%py3_install %{__python3} setup.py install --root=%{buildroot}
EOF

# 3. start docker for the ISO build
sudo systemctl enable --now docker

# 4. verify the verify harness (sanity check)
cd linux-synthex
bash configs/tests/verify.sh; echo "result=$?"
# expected: "RESULT: 17 passed, 0 failed", exit 0
```

Expected output:

```
RESULT: 17 passed, 0 failed
result=0
```

If it returns non-zero, see `docs/TROUBLESHOOTING.md`.

---

## Procedure 1 — build a single RPM

```bash
cd linux-synthex
cp packages/spec-files/<spec>.spec build/rpmbuild/SPECS/
cd build/rpmbuild/SPECS
rpmbuild -ba --nodeps <spec>.spec
ls -lh ../RPMS/noarch/<spec>-*.rpm ../RPMS/x86_64/<spec>-*.rpm 2>/dev/null
```

If the spec references a top-level source that lives in the repo tree
(e.g. `synthex-repo-<version>.tar.gz`), make sure the tarball exists:

```bash
ls build/rpmbuild/SOURCES/synthex-repo-2026.10.tar.gz
```

If it does not exist:

```bash
build/scripts/make-srctars.sh 2026.10
```

The spec must have its `Source0:` declaration match a real file under
`build/rpmbuild/SOURCES/`.

---

## Procedure 2 — build many RPMs with timeouts

```bash
cd linux-synthex
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-system-daemon.spec \
    synthex-hermes.spec synthex-brain.spec
```

Output format:

```
OK   synthex-stored
OK   synthex-system-daemon
FAIL synthex-hermes
OK   synthex-brain
```

For each `FAIL`, the log is at `/tmp/rb_<name>.log`. Investigate:

```bash
grep -E 'error: ' /tmp/rb_synthex-hermes.log | head
```

---

## Procedure 3 — sync the local YUM repo

```bash
cd linux-synthex
# copy freshly built rpms
cp build/rpmbuild/RPMS/noarch/*.rpm   build/repo/noarch/
cp build/rpmbuild/RPMS/x86_64/*.rpm   build/repo/x86_64/

# re-index
( cd build/repo/noarch && createrepo_c . )
( cd build/repo/x86_64  && createrepo_c . )
```

Verify the repo can be consumed:

```bash
dnf --disablerepo='*' --enablerepo='synthex' \
    --repofrompath='synthex,file:///home/jewboy420/linux-synthex/build/repo/x86_64' \
    list available 2>/dev/null | head
```

Expected: you see `kernel` (the vendored Fedora kernel) and a long list
of `synthex-*` packages.

---

## Procedure 4 — refresh the source tarballs (after adding files)

If you’ve added files in the repo that need to land in the tarballs:

```bash
cd linux-synthex
build/scripts/make-srctars.sh 2026.10
```

This regenerates `synthex-repo-<version>.tar.gz` for every version
(0.1.0, 1.0.0, 2.0.0, 2026.1, 2026.10, 2026.10.0).

It packs:

```
Cargo.toml Cargo.lock Makefile LICENSE README.md LICENSE-MIT LICENSE-APACHE
src aether desktop branding configs systemd services etc kernel installer
scripts dbus safety main.py Main.qml system_bridge.py udev security
synthex-blueprint synthex-studio blueprint.py share.py presets ui
drivers synthex-bootctl.sh wallpaper data selinux conf libexec
```

Excludes: `.git`, `.venv`, `__pycache__`, `*.pyc`, `src/*/target`,
`aether/*/target`.

If you add a new top-level source file (e.g. `synthex-ai-platform.preset`),
also drop it in `build/rpmbuild/SOURCES/` so the spec’s `%{SOURCE1}`
resolves.

---

## Procedure 5 — exercise the AIOS layer

```bash
synthex status                 # real brain status
synthex ask "what is synthex"  # recall from brain
synthex memory                 # brain memory-graph report
synthex persona                # list profiles
synthex doctor                 # health report
```

If you want to test against a clean state:

```bash
unset SYNTHEX_AETHER_HOST SYNTHEX_AETHER_PORT
```

If you want to test against AETHER specifically:

```bash
SYNTHEX_AETHER_HOST=192.168.1.42 SYNTHEX_AETHER_PORT=8787 synthex ask "..."
```

---

## Procedure 6 — track a new upstream package

1. Edit `configs/upstream/synth-pkgs.conf` and add:

   ```json
   { "name": "<display-name>", "repo": "fedora|rpmfusion|nobara", "pkg": "<actual>" }
   ```

2. Run the verify harness to confirm Bodhi has the package:

   ```bash
   SYNTHX_CFG=linux-synthex/configs/upstream/synth-pkgs.conf \
       bash linux-synthex/configs/tests/verify.sh; echo $?
   ```

3. Manual check:

   ```bash
   /usr/sbin/synthex-update-sync status | grep <display-name>
   ```

   Expected: a line with `<name>  local=<version>  fedora-latest=<upstream-title>`.

   If Bodhi returns nothing for your package (e.g. it ships only in
   Fedora base + updates without going through Bodhi), the title shows
   `n/a`. That’s expected — not a bug.

---

## Procedure 7 — apply an upstream update (with snapshot)

```bash
# 1. dry-run to see what would happen
synthex update check

# 2. (optional) inspect the candidates
ls /var/cache/synthex/updates/*/candidate.json

# 3. apply: snapshots then writes a real queue.jsonl
synthex update apply
```

Output:

```
synthex:   tracked gamescope: latest upstream = gamescope-3.16.25-1.fc44
...
synthex: queued 5 rebuild job(s) for the Fedora builder -> queue.jsonl
```

State file is written to `/var/lib/synthex/update-state.json`:

```json
{"queued": 5, "at": 1779123456.0, "rollback": "snapper", "snapshot": "pre-update"}
```

You can now hand the `queue.jsonl` to the Fedora builder container (or
run `build/run-iso-build.sh` after feeding the queue through a real
build agent).

---

## Procedure 8 — roll back a bad apply

If the latest apply broke something (you installed an update and the
new build is bad):

```bash
synthex update rollback
```

This invokes `synthex-snapshot rollback` or `snapper -c root rollback`,
restoring the pre-update snapshot. Use **immediately** — the next
`apply` will overwrite the snapshot reference in `update-state.json`.

---

## Procedure 9 — adopt a persona

```bash
synthex persona                  # list
synthex persona gamer            # gamer profile
```

The persona picks a meta-package and toggles units. It does not
modify the user’s data. Reversible by picking another persona, or by
running `systemctl enable/disable` manually.

---

## Procedure 10 — install a driver/app with snapshot

```bash
# 1. dry-run first
synthex install nvidia

# 2. when ready
synthex install nvidia --yes
```

This:
1. Calls `synthex-snapshot create pre-nvidia` (if present).
2. Runs `dnf install -y nvidia-driver nvidia-modprobe`.
3. If `dnf` succeeded → calls `synthex-doctor`.
4. If anything failed → `synthex-snapshot rollback`.

On a host without `dnf` (Mint), the step simulates and exits 0 — useful
for CI.

---

## Procedure 11 — build the ISO

```bash
build/run-iso-build.sh
```

This:
1. Builds a slim `synthex-builder` Docker image from `fedora:41`,
   installing `lorax livemedia-creator pykickstart xorriso
   squashfs-tools grub2 dnf-utils createrepo_c rpm-build`.
2. Mounts `build/repo/` and `build/kickstart/synthex-hyprland-local.ks`
   into the container.
3. Runs:
   ```
   livecd-creator --verbose --config=$KS --releasever=42 \
     --title="SynthOS" --product="SynthOS" \
     --volid="SYNTHEX_HYPRLAND_2026_10" \
     --compression-type=zstd --keep-image \
     -o $OUT/Synthex-Hyprland-2026.10-x86_64.iso
   ```
4. Validates the resulting ISO.

Expected duration: 20–60 minutes depending on network.

After it finishes:

```bash
ls -lh build/iso-out/Synthex-Hyprland-2026.10-x86_64.iso
# verify it boots
unsquashfs -stat build/iso-out/Synthex-Hyprland-2026.10-x86_64.iso
# mount and inspect (optional)
mkdir -p /mnt/iso && sudo mount -o loop,ro build/iso-out/Synthex-Hyprland-2026.10-x86_64.iso /mnt/iso
ls /mnt/iso/LiveOS/ /mnt/iso/boot/
sudo umount /mnt/iso
```

---

## Procedure 12 — write a unit test for a new feature

```bash
# add a test to configs/tests/verify.sh
```

Pattern:

```bash
echo "[my feature]"
exp "my-feature works" "OK" bash "$ROOT/path/to/test"
```

`gate` checks that the command exits 0; `exp` additionally requires a
needle in stdout. Both print PASS/FAIL.

Re-run:

```bash
bash configs/tests/verify.sh; echo $?
```

The expected `RESULT:` line should grow by 1. Anything below it
should still be PASS.

---

## Procedure 13 — clean up

```bash
# clear build directories
rm -rf build/rpmbuild/BUILD/* build/rpmbuild/BUILDROOT/*

# clear the upstream-tracker cache
rm -rf /var/cache/synthex/updates /var/lib/synthex

# clear repo (nuclear)
rm -rf build/repo
# then re-create and re-index:
mkdir -p build/repo/noarch build/repo/x86_64
# copy fresh rpms back
cp build/rpmbuild/RPMS/noarch/*.rpm build/repo/noarch/
cp build/rpmbuild/RPMS/x86_64/*.rpm build/repo/x86_64/
( cd build/repo/noarch && createrepo_c . )
( cd build/repo/x86_64  && createrepo_c . )
```

---

## Procedure 14 — debug a failing RPM build

```bash
# 1. Reproduce
cd linux-synthex/build/rpmbuild/SPECS
rpmbuild -ba --nodeps --short-circuit <spec>.spec
# the --short-circuit builds %prep only; useful to isolate which
# section fails.

# 2. Inspect the build script
cat /tmp/rpm-tmp.* | head -50
# the latest /tmp/rpm-tmp.* is the most recent attempt.

# 3. Inspect the extracted tree
ls -la /home/jewboy420/linux-synthex/build/rpmbuild/BUILD/
# the extracted dir is BUILD/<name>-<version>/; inspect files there.

# 4. Look at the buildroot (what %install staged)
ls -la /home/jewboy420/linux-synthex/build/rpmbuild/BUILDROOT/<name>-<version>-<release>.<arch>/

# 5. Read the build log
cat /tmp/rb_<name>.log | tail -40
```
