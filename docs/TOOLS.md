# Build Tools & Scripts Reference

Every shell script used to **build, stage, validate, and release** the
SynthOS repo — what it does, how to invoke it, and its inputs/outputs.

> Runtime tools (built for userland) are covered in `docs/REFERENCE.md`
> and `docs/AIOS.md`. The Fedora ISO builder is in `docs/ISO.md` and
> `docs/livecd`. This file is for the **host build toolchain**.

---

## `build/scripts/make-srctars.sh`

Packs all the `Source0:` inputs the specs need, straight from the repo,
**no network, reproducible**.

```
Usage: build/scripts/make-srctars.sh [VERSION] [OUTDIR]
  VERSION default = VERSION file (or 2026.10)
  OUTDIR  default = ~/rpmbuild/SOURCES
```

Outputs:
1. `synthex-repo-<VERSION>.tar.gz` — monorepo tarball (topdir
   `synthex-repo-<VERSION>`). Every first-party spec uses it as
   `Source0` with `%setup -q -n synthex-repo-%{version}`.
2. **Single-file sources** — bare `Source0` basenames copied verbatim:
   `ujust`, `synthex-welcome`, `synthex-service-manager`,
   `synthex-log-viewer`, `synthex-locale-setup`, `synthex-kernel-manager`,
   `synthex-nvidia-installer`, `synthex.repo`, `limits.conf`,
   `sysctl.conf`, `auditd.rules`, `security-deploy.sh`,
   `dracut-synthex.conf`, `apply-nobara-fixes.sh`,
   `apply-cachy-tuning.sh`.

Excludes: `.git`, `target`, `.venv`, `.claude`, `__pycache__`, `*.pyc`,
`build/out`, `build/rpms`, `build/repo`, `build/srpms`,
`build/rpmbuild`, `*.log`.

Packs: `Cargo.toml Cargo.lock VERSION Makefile Justfile src aether
desktop branding configs systemd services safety security dbus docs
installer kernel udev etc packages/groups`.

---

## `build/scripts/local-repo.sh`

Builds all SynthOS RPMs and assembles a local yum repo.

```
Run INSIDE the Fedora build container (or host rpmbuild).
build/scripts/make-srctars.sh && build/scripts/local-repo.sh
```

Outputs:
- `build/rpms/**/*.rpm` — built packages.
- `build/repo/` — `createrepo_c` metadata + `synthex-local.repo`.
- `build/rpmbuild/build-<name>.log` — per-spec logs.

Behavior:
- Iterates `packages/spec-files/*.spec`.
- Skips by default (set `HEAVY=1` to attempt): `synthex-kernel`,
  `rust-toolchain`, `cosmic-*`, `xdg-desktop-portal-cosmic`,
  `synthex-kernel-meta`.
- Detects specs whose `Source0` is external (cosmic-*/rust-utils-*) and
  skips them if offline.
- Prints a summary: `built / skipped(external) / failed`.

---

## `build/scripts/build_batch.sh` (repo root)

Timeout-aware per-spec builder. Each spec gets **90 seconds**; a slow
or hanging spec fails gracefully.

```bash
/home/jewboy420/build_batch.sh synthex-stored.spec synthex-system-daemon.spec ...
```

Output: `OK <name>` / `FAIL <name>` per spec, then a count. Logs in
`/tmp/rb_<name>.log`.

---

## `build/scripts/gen-grub-assets.sh`

Generates GRUB theme PNG assets from SVG sources.

```bash
build/scripts/gen-grub-assets.sh
```

- Uses `rsvg-convert` (`librsvg`) if available, else `convert`
  (ImageMagick).
- Writes `background.png`, selection highlight bars, etc. into
  `branding/grub/themes/synthex/`.
- Skips (warns) if neither tool is installed — non-fatal.

---

## `build/scripts/hardware-detect.sh`

Detects hardware (CPU, GPU, audio, network, disks, controllers,
vebes; Bluetooth). Heavily scripted (~764 lines). Used by the installer
and post-install.

```
Usage: ./hardware-detect.sh [options/format]
```

Writes a hardware profile that later steps (driver manager, GPU setup,
persona) consume.

---

## `build/scripts/post-install.sh`

The **kickstart %post** script that runs in the installed image (and, in
stages, on live). It:

- configures /etc defaults,
- wires the AIOS layer (enables `synthex-defaults`,
  `synthex-predictive`, etc.),
- enables zram / snapper / fstrim timers,
- calls `hardware-detect.sh` and sets the GPU driver,
- installs Synthex shell configs into `/etc/skel` (fish, starship,
  kitty, fastfetch, wofi, mako),
- writes `/etc/yum.repos.d/synthex.repo` to the local accessible repo,
- configures greetd → Hyprland, and adds the default Hyprland config.

Over 630 lines. The `-local.ks` files call this.

---

## `build/scripts/prepare-kickstart.sh`

Validates, patches, and stages kickstart files for livemedia-creator.

```bash
./prepare-kickstart.sh [EDITION] [--validate-only] [--output DIR]
  EDITION = all (default) | plasma | gaming | gnome | hyprland | minimal
```

- Validates each kickstart: required sections, valid `%packages`,
  no dead repo URLs, kernel packages present.
- Patches urls/repos as needed.
- Stages into `build/out/kickstart/`.

---

## `build/scripts/validate-iso.sh`

Validates a built ISO for completeness, structure, and integrity.

```bash
./validate-iso.sh [ISO_PATH] [--strict]
```

Checks (summary):
- ISO is present and readable.
- `vmlinuz` / `initrd.img` present.
- `LiveOS/squashfs.img` present and `unsquashfs -stat` clean.
- No Ubuntu/generic kernel.
- GRUB config present.
- (strict) all the above are **required**, not warnings.

---

## `build/scripts/build-iso.sh`

The main ISO build pipeline (the original; iterates editions).

```bash
./build-iso.sh plasma | hyprland | gnome | gaming | minimal  [options]
```

Variables: `VERSION`, `VARIANT` (v3 default), `EDITION`, `PROFILES`,
`OUTPUT_DIR`, `WORK_DIR`, `KS_DIR`, `LIVECD_DIR`. This is the bigger,
more option-rich ISO path; `build-iso-fixed.sh` is the corrected single
edition assembler.

---

## `build/scripts/build-iso-fixed.sh`

The **corrected** ISO assembler that fixes the original boot bug.

```bash
sudo ./build-scripts/build-iso-fixed.sh /path/to/rootfs-dir [-o out.iso]
```

Guarantees:
1. Rejects Ubuntu/generic kernels (`strings vmlinuz` regex).
2. Refuses `squashfs.img ≥ 3.8 GiB` (ISO9660 4 GiB ext limit).
3. Validates the squashfs superblock after assembly.
4. Single-pass `xorriso`.

See `docs/ISO.md` for the full design.

---

## `build/scripts/release.sh`

Tags the repo, generates checksums, and creates the full release
artifact set.

```bash
./build/scripts/release.sh [VERSION=2026.10] [CODENAME=Ignition] [EDITION]
```

Preflight requires `cargo`, the kickstart files, and root. Produces
`build/release/<VERSION>/` with ISOs + checksums. See `docs/RELEASE.md`.

---

## `build/scripts/build-all.sh`

Builds every ISO edition in sequence (or parallel).

```bash
./build-all.sh [--parallel] [--editions "plasma gaming gnome hyprland minimal"]
               [--version 2026.10] [--sign] [--upload]
```

---

## `build/run-iso-build.sh`

The one-shot runner used for the "fast iteration" ISO build (slim
Docker builder). See `docs/ISO.md`.

---

## `kernel/build.sh`

The kernel builder wrapper (Fedora-side). It downloads the kernel source
(6.14.2), applies patches, configures with `kernel/config-x86_64`, runs
`make`, and packages via `synthex-kernel.spec`. Note: we **ship the
Fedora kernel**, not this build; see `docs/KERNEL.md`.

---

## Cross-cutting

- **Logging**: every script writes to a predictable log (e.g.
  `build/rpmbuild/build-*.log`, `/tmp/rb_*.log`, `build/out/logs/`).
- **Colors**: consistent `GREEN/YELLOW/RED/BOLD` helpers.
- **Exit codes**: build scripts exit non-zero on failure; the verify
  harness (`configs/tests/verify.sh`) is the single gate for the AIOS
  layer and exits non-zero on any check failure.