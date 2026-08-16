# Cheat Sheet

Fast reference. Execute from `linux-synthex/`.

## Build & package

```bash
# build one rpm
cp packages/spec-files/<spec>.spec build/rpmbuild/SPECS/
rpmbuild -ba --nodeps --define "_topdir build/rpmbuild" build/rpmbuild/SPECS/<spec>.spec   # or cd there and drop --define

# build many (timeout-guarded)
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-system-daemon.spec ...

# refresh source tarballs after adding files
build/scripts/make-srctars.sh 2026.10

# sync the local yum repo + reindex
cp build/rpmbuild/RPMS/noarch/*.rpm  build/repo/noarch/
cp build/rpmbuild/RPMS/x86_64/*.rpm  build/repo/x86_64/
( cd build/repo/noarch && createrepo_c . )
( cd build/repo/x86_64  && createrepo_c . )
```

## Verify

```bash
configs/tests/verify.sh; echo $?
# → "RESULT: 17 passed, 0 failed" + exit 0
```

## The assistant console

```bash
synthex status
synthex ask "what is synthos"
synthex think "…"
synthex memory
synthex verbs
synthex doctor
synthex persona gamer|creator|developer|privacy|minimal
synthex update status|check|stage|apply|rollback
synthex install nvidia|amd|intel|mesa|steam|codecs|<pkg> [--yes]
```

## Performance

```bash
synthex-gov max         # CPU governor → performance
synthex-gov balanced    # → schedutil (default)
synthex-game-session steam   # run a game under gamescope
```

## Updater (Mint/Bazzite-style)

```bash
synthex-update-sync status
synthex-update-sync check
synthex-update-sync stage
synthex-update-sync apply
synthex-update-sync rollback
```

Config: `/etc/synthex/upstream/synth-pkgs.conf`
Sandbox env: `SYNTHX_CFG SYNTHX_STAGE SYNTHX_STATE SYNTHX_REPO SYNTHX_SNAP SYNTHX_QUEUE`

## ISO

```bash
build/run-iso-build.sh
# → build/iso-out/Synthex-Hyprland-2026.10-x86_64.iso
```

## Docs to read first

1. `docs/README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/REFERENCE.md` (every file)
4. `docs/RUNBOOK.md` (step-by-step):
5. then the per-feature docs:
   - `docs/AIOS.md`, `docs/PERFORMANCE.md`, `docs/UPDATER.md`,
     `docs/SECURITY.md`, `docs/KERNEL.md`, `docs/HARDWARE.md`,
     `docs/DAEMONS.md`
   - `docs/INSTALLER.md`, `docs/ISICO.md`, `docs/PACKAGING.md`,
     `docs/BUILD.md`, `docs/EXTENDING.md`, `docs/TROUBLESHOOTING.md`,
     `docs/REPO-LAYOUT.md`

## Quick file map

| Path | Purpose |
|---|---|
| `configs/aios/synthex` | `/usr/bin/synthex` console |
| `configs/aios/synthex-doctor` | `/usr/sbin/synthex-doctor` |
| `configs/aios/synthex-persona` | `/usr/sbin/synthex-persona` |
| `configs/aios/synthex-install` | `/usr/sbin/synthex-install` |
| `configs/aios/synthex-defaults` | `/usr/sbin/synthex-defaults` |
| `configs/upstream/synthex-update-sync.py` | `/usr/sbin/synthex-update-sync` |
| `configs/performance/…` | the perf layer |
| `configs/tests/verify.sh` | the harness |
| `packages/spec-files/synthex-aios.spec` | the AIOS umbrella RPM |
| `build/repo/` | the local YUM repo |
| `build/kickstart/*-local.ks` | patched kickstarts |
| `build/run-iso-build.sh` | ISO runner |
| `build/scripts/build-iso-fixed.sh` | the ISO assembler (gates) |
| `kernel/` | kernel policy (Fedora kernel) |