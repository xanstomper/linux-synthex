# Building the Local RPM Repo on This Host

This document describes the **host-side** build (what runs on Linux Mint
where the repo was bootstrapped). For the **container-side** ISO build see
`docs/ISO.md`.

## What you need on the host

```bash
# Build toolchain
sudo apt-get install -y --no-install-recommends \
    build-essential rpm python3 python3-build libelf-dev libssl-dev \
    libncurses-dev dwarves pahole openssl perl python3-dev bison flex \
    kmod lz4 zstd m4 diffutils bc createrepo-c xorriso squashfs-tools \
    librsvg2-bin coreutils
```

## One-time setup

1. **Create the rpmmacros.** `~/.rpmmacros` (kept in this repo, see
   `docs/PACKAGING.md` for its full contents). The macros add the Fedora
   systemd/udev/userunit dirs (Ubuntu rpm doesn’t define them) and stub
   `%meson`/`%py3_build`/`%py3_install`.

2. **Generate source tarballs** (if you’ve added new repo dirs):
   ```bash
   build/scripts/make-srctars.sh 2026.10
   ```
   This packs `Cargo.toml src aether desktop branding configs systemd
   services etc kernel installer scripts dbus safety main.py Main.qml
   system_bridge.py udev security synthex-blueprint synthex-studio
   blueprint.py share.py presets ui drivers synthex-bootctl.sh wallpaper
   data selinux conf libexec` into
   `build/rpmbuild/SOURCES/synthex-repo-<version>.tar.gz` for every
   version listed in the spec.

## Build everything

The simplest, safest pattern:

```bash
# Sync specs from packages/ → build/rpmbuild/SPECS
cp packages/spec-files/*.spec build/rpmbuild/SPECS/

# Build one
cd build/rpmbuild/SPECS
rpmbuild -ba --nodeps synthex-aios.spec

# Build many with the timeout-aware helper
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-system-daemon.spec ...
```

`build_batch.sh` runs each spec with a 90 s timeout and reports OK/FAIL.

## Re-index the local repo

After any new RPM is built:

```bash
cd build/repo
cp ../rpmbuild/RPMS/noarch/*.rpm noarch/
cp ../rpmbuild/RPMS/x86_64/*.rpm x86_64/
createrepo_c noarch
createrepo_c x86_64
```

## Run the verification harness

This is the single command that proves everything works:

```bash
configs/tests/verify.sh; echo "result=$?"
```

Expected: `RESULT: 17 passed, 0 failed` and `exit 0`.

## Cleaning up

```bash
# Remove all stale build directories and start fresh
rm -rf build/rpmbuild/BUILD/* build/rpmbuild/BUILDROOT/*

# Wipe the cache used by the verify harness
rm -rf /var/cache/synthex/updates /var/lib/synthex
```
