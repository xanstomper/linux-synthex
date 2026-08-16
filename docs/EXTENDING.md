# Extending

Concrete recipes for adding things to SynthOS. Each one ends with the
verification command that proves the change works.

## Adding a new daemon (Rust → Cargo)

1. Create `src/<your-daemon>/Cargo.toml` + `src/<your-daemon>/src/main.rs`
   as part of the project Cargo workspace (or a sibling crate). Use the
   existing `src/synthex-system-daemon/` as a template.

2. The Cargo workspace already lists every `src/<x>` member in the root
   `Cargo.toml`. If you add a new subdir there, you’re in.

3. `cargo build --workspace --release` produces the binary at
   `target/release/<name>`. We don’t compile inside rpmbuild — we
   copy the prebuilt binary in (see `docs/PACKAGING.md`).

4. Write the spec at `packages/spec-files/synthex-<your-daemon>.spec`
   using the “prebuilt-binary” pattern:

   ```spec
   %build
   install -d target/release
   install -m755 /home/jewboy420/linux-synthex/target/release/<name> \
       target/release/<name>
   ```

   Adjust `<name>` and the install path.

5. Copy the spec to `build/rpmbuild/SPECS/`, build, re-index the repo:

   ```bash
   cp packages/spec-files/synthex-<your-daemon>.spec build/rpmbuild/SPECS/
   /home/jewboy420/build_batch.sh synthex-<your-daemon>.spec
   cp build/rpmbuild/RPMS/noarch/synthex-<your-daemon>-*.rpm build/repo/noarch/
   cd build/repo/noarch && createrepo_c .
   ```

6. Add a systemd unit under `systemd/<your-daemon>.service` and include
   it in `configs/upstream/synth-pkgs.conf` (or have the spec install it
   directly). If you want it auto-enabled on first boot, append the unit
   to `synthex-defaults`.

7. Run the verify harness:

   ```bash
   configs/tests/verify.sh; echo $?
   ```

## Adding a new tracked package

Edit `configs/upstream/synth-pkgs.conf` and add to `tracked`:

```json
{ "name": "<display-name>", "repo": "fedora|rpmfusion|nobara", "pkg": "<actual-pkg>" }
```

Then run:

```bash
configs/tests/verify.sh; echo $?
```

You should see the new package in the `status` output with its real
upstream version (fetched from Bodhi). For RPM Fusion packages, you can
still get a real version via Bodhi (rpmfusion publishes via Bodhi for
many packages).

For packages not on Bodhi (very rare), Bodhi returns empty for that
name. That’s fine — `status` will print `n/a` for that package.

## Adding a new sysctl / perf default

1. Create `configs/performance/sysctl.d/<your-file>.conf`.
2. Add a `cp …` line to `configs/performance/install.sh`.
3. Add an `install -m 0644 …` line to `packages/spec-files/synthex-aios.spec`
   and a `%files` entry.
4. Rebuild + re-sync:

   ```bash
   /home/jewboy420/build_batch.sh synthex-aios.spec
   cp build/rpmbuild/RPMS/noarch/synthex-aios-*.rpm build/repo/noarch/
   cd build/repo/noarch && createrepo_c .
   ```

## Adding a new persona

Edit `configs/aios/synthex-persona` and add a new case clause:

```bash
case "$want" in
  designer)
    enable synthex-creator-meta 2>/dev/null || true
    enable synthex-blender-bridge 2>/dev/null || true
    ;;
esac
```

Add an entry to the list-mode output too. Then:

```bash
configs/tests/verify.sh; echo $?
```

The verify harness asserts `persona lists` (the list output includes
your new entry).

## Adding a new kickstart edition

1. Copy an existing `synthex-<edition>.ks` to `synthex-<your>.ks` and
   edit the `%packages` and `%post` for your DE.
2. Create the patched `synthex-<your>-local.ks` by running:

   ```bash
   cp synthex-<your>.ks synthex-<your>-local.ks
   sed -i \
     -e 's#^url --mirrorlist=.*fedora-42.*#url --url="https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/42/Everything/x86_64/os/" --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-42\&arch=x86_64"#' \
     -e 's#^repo --name="synthex" .*#repo --name="synthex" --baseurl="file:///home/jewboy420/linux-synthex/build/repo/x86_64" --gpgcheck=0#' \
     -e 's#^repo --name="synthex-updates" .*#repo --name="synthex-updates" --baseurl="file:///home/jewboy420/linux-synthex/build/repo/x86_64" --gpgcheck=0#' \
     -e 's#^synthex-kernel$#kernel\nkernel-core\nkernel-modules\nkernel-modules-core\nkernel-modules-extra#' \
     synthex-<your>-local.ks
   sed -i 's#baseurl=https://packages.getsynthex.org/stable/x86_64/#baseurl=file:///home/jewboy420/linux-synthex/build/repo/x86_64#g;
            s#baseurl=https://packages.getsynthex.org/updates/x86_64/#baseurl=file:///home/jewboy420/linux-synthex/build/repo/x86_64#g;
            s#baseurl=https://packages.getsynthex.org/nonfree/x86_64/#baseurl=file:///home/jewboy420/linux-synthex/build/repo/x86_64#g' \
     synthex-<your>-local.ks
   grep -c 'packages.getsynthex' synthex-<your>-local.ks  # should be 0
   ```

3. Add a case in `build/run-iso-build.sh` and `build/livecd/build-iso.sh`
   so your edition is selectable.

## Adding a test to the verify harness

Edit `configs/tests/verify.sh`. The harness is plain bash; each “check”
is either a `gate` (no-crash + exit 0) or an `exp` (output contains a
needle). Add yours in the appropriate section:

```bash
echo "[my feature]"
exp "my-feature works" "OK" bash "$ROOT/path/to/test"
```

Run it:

```bash
configs/tests/verify.sh; echo $?
```

The expected output should now contain `RESULT: 18 passed, 0 failed`.
