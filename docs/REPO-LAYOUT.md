# Repo Layout

A map of every directory the host-side and ISO-side tooling actually
uses, with the role of each.

```
linux-synthex/
├── Cargo.toml            # project metadata (not used by builds yet)
├── Cargo.lock
├── README.md             # (legacy) pre-aios overview
├── REPORT.md             # one-page build report (generated earlier)
├── build/
│   ├── iso-out/          # where build/run-iso-build.sh drops the .iso
│   ├── kernel/           # kernel policy (see docs/KERNEL.md)
│   ├── kickstart/        # 5 editions of kickstarts:
│   │   ├── synthex-hyprland.ks
│   │   ├── synthex-hyprland-local.ks   ← patched, used by runner
│   │   ├── synthex-plasma.ks
│   │   ├── synthex-plasma-local.ks
│   │   ├── synthex-gnome.ks
│   │   ├── synthex-gnome-local.ks
│   │   ├── synthex-gaming.ks
│   │   ├── synthex-gaming-local.ks
│   │   ├── synthex-minimal.ks
│   │   ├── synthex-minimal-local.ks
│   │   └── synthex-gaming-packages.ksinc
│   ├── livecd/           # the Fedora 41 builder container
│   │   ├── Dockerfile    #   the full Qt/KDE build image (heavy)
│   │   └── build-iso.sh  #   the original Fedora-side ISO build
│   ├── repo/             # the LOCAL RPM REPO consumed by the kickstart
│   │   ├── noarch/       #   noarch packages (synthex-aios, configs, themes, …)
│   │   └── x86_64/       #   x86_64 packages (kernel, mesa, nvidia, …)
│   ├── output/           # (legacy) build output dir
│   ├── build-work/       # (legacy) livecd-creator working dir
│   ├── rpmbuild/         # rpmbuild working tree
│   │   ├── BUILD/        #   extracted sources per-build (clean between runs)
│   │   ├── BUILDROOT/    #   staged install roots per-build
│   │   ├── RPMS/         #   built .rpm files (noarch/, x86_64/)
│   │   ├── SRPMS/        #   source RPMs
│   │   ├── SOURCES/       #   source tarballs, presets, standalone sources
│   │   ├── SPECS/        #   the .spec files (synced from packages/spec-files/)
│   │   ├── tmp/          #   rpmbuild temp files
│   │   ├── SPECS.bak/    #   (legacy) backups of pre-patch specs
│   │   └── SPECS.bak2/
│   └── scripts/          # build helpers
│       ├── build-all.sh
│       ├── build-iso-fixed.sh          ← the ISO assembler (with gates)
│       ├── build-iso.sh
│       ├── build-synthex-kernel.sh     ← legacy kernel build wrapper
│       ├── gen-grub-assets.sh
│       ├── hardware-detect.sh
│       ├── local-repo.sh
│       ├── make-srctars.sh              ← packs sources into synthex-repo-*.tar.gz
│       ├── post-install.sh
│       ├── prepare-kickstart.sh
│       ├── release.sh
│       └── validate-iso.sh
├── build_batch.sh                   ← timeout-aware per-spec helper (in repo root)
├── run-iso-build.sh                 ← one-shot ISO runner (Docker + livecd-creator)
├── configs/                         # the AIOS layer + performance + tests
│   ├── aios/                        #   the assistant console layer
│   │   ├── synthex                  ← CLI /usr/bin/synthex
│   │   ├── synthex-doctor           ← /usr/sbin/synthex-doctor
│   │   ├── synthex-persona          ← /usr/sbin/synthex-persona
│   │   ├── synthex-install          ← /usr/sbin/synthex-install
│   │   ├── synthex-defaults         ← /usr/sbin/synthex-defaults
│   │   ├── synthex-defaults.service ← first-boot unit
│   │   ├── synthex-sync-updates.{timer,service}  ← upstream tracker
│   │   ├── install.sh               ← bakes the layer into an image root
│   │   └── post-install.sh          ← kickstart %post snippet
│   ├── upstream/                    #   the Mint/Bazzite-style tracker
│   │   ├── synthex-update-sync.py   ← main orchestrator
│   │   └── synth-pkgs.conf          ← tracked-packages config
│   ├── performance/                 #   safe perf defaults
│   │   ├── sysctl.d/{00-synthex-vm.conf,00-synthex-network.conf}
│   │   ├── synthex-gov               ← governor switcher
│   │   ├── zram-setup, zram.service
│   │   ├── gamemode.ini
│   │   ├── synthex-game-session      ← gamescope wrapper
│   │   ├── install.sh                ← bakes perf into an image root
│   │   └── grub-synthex.cmdline      ← doc only
│   └── tests/                       #   the verification harness
│       └── verify.sh                  ← 17/17 PASS
├── docs/                            # ← the documentation index lives at docs/README.md
├── kernel/                          # kernel policy + synthex-kernel spec
├── packages/                        # the source-of-truth spec files
│   └── spec-files/                  #   172 specs (some still aspirational)
├── src/                             # the project source tree (Rust + Python)
│   ├── synthex-system-daemon/
│   ├── synthex-brain/
│   ├── synthex-hermes/
│   ├── synthex-agent/
│   ├── synthex-predictive/
│   └── …                             #   (see `cargo metadata` for the full list)
└── …                               #   many other project files (data/, branding/, etc.)
```

## Where to put new things

| You want to… | Put it under… |
|---|---|
| Add a new system service | `src/<service>/` (Cargo) **and** `packages/spec-files/` (RPM) |
| Add a new AI-OS CLI tool | `configs/aios/<tool>` and `configs/aios/install.sh` to bake it |
| Add a new tracked package | `configs/upstream/synth-pkgs.conf` |
| Add a new sysctl value | `configs/performance/sysctl.d/…` |
| Add a new persona | `configs/aios/synthex-persona` (modify the case statement) |
| Add a new kickstart edition | `build/kickstart/synthex-<edition>.ks` and `<edition>-local.ks` |
| Add a new ISO gate | `build/scripts/build-iso-fixed.sh` |
| Add a test for the harness | `configs/tests/verify.sh` |

## What is NOT in the repo

- `.venv/`, `__pycache__/`, `target/` — excluded by tar rules.
- Built `.rpm` files live under `build/rpmbuild/RPMS/`; copies of the
  *finished* repo under `build/repo/`.
- The vendored **Fedora kernel** rpms and the live ISO are produced
  by the runner script and the Fedora builder container.
