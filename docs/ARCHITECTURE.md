# Architecture

## Layered design

```
┌─────────────────────────────────────────────────────────────┐
│  ISO image  (kickstart + Fedora builder container)            │
│  ├── bootloader (GRUB)                                       │
│  ├── vmlinuz + initramfs  (Fedora 41 kernel — vendored)       │
│  └── LiveOS/squashfs.img                                   │
│        └── rootfs.img (ext4)                                  │
│             ├── Fedora 42 base                               │
│             ├── RPM Fusion (free + nonfree)                   │
│             ├── local repo: build/repo/{noarch,x86_64}        │
│             │     ├── synthex-* RPMs (daemons, apps, AI)     │
│             │     ├── synthex-aios  ← the AIOS layer (this)  │
│             │     └── kernel/kernel-core/kernel-modules*     │
│             └── /usr/bin/synthex  (assistant console)        │
└─────────────────────────────────────────────────────────────┘
                        ▲                                          ▲
                        │ installed by kickstart %post            │ consumes
                        │                                          │
┌────────────────────────┴──────────────────┐  ┌─────────────────┴──────────┐
│  configs/aios/  (this repo, in-tree)        │  │  Fedora 41 builder       │
│  ├── synthex            (CLI)             │  │  container (Docker)        │
│  ├── synthex-doctor     (one-shot health) │  │  ├── lorax                 │
│  ├── synthex-persona    (profile picker)  │  │  ├── livemedia-creator     │
│  ├── synthex-install    (guarded install) │  │  ├── pykickstart            │
│  ├── synthex-defaults   (first-boot on)   │  │  └── xorriso               │
│  ├── synthex-game-session (gamescope)      │  └─────────────────────────────┘
│  └── /usr/share/synthex/aios/post-install.sh
│                                            │
│  configs/upstream/                         │
│  ├── synthex-update-sync.py (real Bodhi)   │
│  └── synth-pkgs.conf (tracked packages)    │
│                                            │
│  configs/performance/                       │
│  ├── synthex-gov (governor switch)         │
│  ├── zram-setup, zram.service              │
│  ├── gamemode.ini                           │
│  ├── sysctl.d/00-synthex-vm.conf           │
│  ├── sysctl.d/00-synthex-network.conf      │
│  └── grub-synthex.cmdline                  │
└────────────────────────────────────────────┘
                        ▲
                        │ built into a single noarch RPM
                        │
            ┌───────────┴────────────┐
            │  packages/spec-files/  │
            │  synthex-aios.spec     │
            └────────────────────────┘
                        ▲
                        │ built by
                        │
       ┌────────────────┴─────────────────────┐
       │  build/                              │
       │  ├── SPECS/synthex-aios.spec          │
       │  ├── SOURCES/synthex-aios-*.tar.gz    │
       │  ├── RPMS/noarch/synthex-aios.rpm     │
       │  └── BUILDROOT/, tmp/ (working)       │
       └─────────────────────────────────────────┘
```

## The three guarantees the design upholds

1. **Never bricks a user machine.**
   Every feature that can modify the system (install, update apply, persona
   switch) takes a **btrfs snapshot first** via `synthex-snapshot` (or, in
   its absence, snaps back via `snapper rollback`). The orchestrator is
   correct *and* honest — `synthex-update-sync apply` does **not** claim a
   rebuild happened; it records a real `queue.jsonl` for the container.

2. **No fake claims.**
   `synthex-update-sync`’s `apply` used to write log lines that lied
   ("rebuilt+imported"). That has been removed. The current behavior is:
   snapshot → record → write queue → done. The actual fetch and rebuild
   happens in the Fedora builder container.

3. **Honest sandbox testing.**
   `configs/tests/verify.sh` proves every shipped tool works against a
   real sandbox (a tmp dir, not your real `/var`). It runs in <10 seconds
   and exits 0 on success.

## What lives where (high level)

| Path | Purpose |
|---|---|
| `configs/aios/` | The AIOS layer: `synthex`, doctor, persona, install, defaults, services |
| `configs/upstream/` | The Mint/Bazzite-style upstream tracker |
| `configs/performance/` | Safe gaming/perf defaults |
| `configs/tests/` | The verification harness |
| `packages/spec-files/` | All RPM `.spec` files (172 of them) |
| `build/rpmbuild/` | rpmbuild working tree (SPECS, SOURCES, RPMS, BUILDROOT, BUILD) |
| `build/repo/` | The local YUM/DNF repo consumed by the kickstart (`createrepo_c` indexed) |
| `build/scripts/build-iso-fixed.sh` | The corrected ISO assembler (3.8 GiB squashfs gate, anti-Ubuntu-kernel gate, validation) |
| `build/run-iso-build.sh` | One-shot runner: builds a slim Fedora 41 builder image, runs livecd-creator inside Docker, outputs the ISO |
| `build/kickstart/synthex-*-local.ks` | Patched kickstarts (5 editions) with dead-repo replaced by `file://.../build/repo/x86_64` |
| `build/livecd/Dockerfile` | The Fedora 41 builder image (lorax, livemedia-creator, xorriso, grub2) |
| `kernel/` | The kernel policy (vendored Fedora, custom spec kept as aspirational) |
| `docs/` | This documentation |

## The data flow

The host (Mint) builds RPMs via `rpmbuild -ba`. The local repo at
`build/repo/` is `createrepo_c`-indexed. The kickstart file in
`build/kickstart/synthex-*-local.ks` points at that repo (`file://...`),
so the livecd-creator inside the Fedora container installs both the
**Fedora base + RPM Fusion** and our **local SynthOS packages** into the
rootfs. The runner script `build/run-iso-build.sh` is the one command
that orchestrates the entire container build.
