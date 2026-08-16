# SynthOS / Synthex — RPM Build & ISO Status Report

Date: 2026-08
Environment: Linux Mint host (`jewboy420`), project root `/home/jewboy420/linux-synthex`

## 1. Original ISO boot failure — root cause (FIXED DIAGNOSIS)

The only existing ISO (`build/iso-out/synthex-2026.10-hyprland-x86_64.iso`) was unbootable:

1. `squashfs.img` was ~4.29 GB — just over the ISO9660 4 GiB single-extent limit. xorriso
   wrote it as a **multi-extent** file and *zero-filled the head*, so the squashfs
   superblock was all zeros:
   `FATAL ERROR: Can't find a valid SQUASHFS superblock on squashfs.img`
2. It booted the **host's** Ubuntu kernel (`6.14.0-37-generic`), not the project kernel —
   so the safe-mode entry dropped to an initramfs shell with "arrays not found".

Resolution: rebuild the ISO from scratch with a proper Fedora-style live layout
(`/LiveOS/squashfs.img` → `/LiveOS/rootfs.img`, `rd.live.image`), using the project's own
kernel/initrd, and enforce `squashfs.img < 3.8 GiB`.
Corrected script: `build/scripts/build-iso-fixed.sh` (rejects Ubuntu/generic kernels,
single-pass xorriso, post-build validates `unsquashfs -stat`).

## 2. What was built and fixed on this host

- RPM toolchain (`rpm`/`rpmbuild`, `createrepo_c`) installed; `~/.rpmmacros` fixed
  (`%_topdir` empty → `/var/tmp` permission errors all resolved).
- Source tarball generation (`build/scripts/make-srctars.sh 2026.10`) and all
  `synthex-repo-<ver>.tar.gz` variants produced.
- **Rust workspace validated:** `cargo check --workspace` (4 min) and
  `cargo build --workspace --release` (9 min) both **complete cleanly** — every Synthex
  daemon (system-daemon, hwdaemon, desktopd, gpu-setupd, stored, ao-daemon, brain, hermes,
  synthguard/shield/vault/identity/net/box, kernel-manager, and ~30 more) compiles. The
  daemon binaries are in the project `target/release/`.
- Upstream sources fetched (kernel `linux-6.14.tar.xz`, rust 1.80.0 toolchain + std,
  plus most rust-util tarballs) into `build/rpmbuild/SOURCES`.
- **Local YUM repo generated:** `build/repo/{noarch,x86_64}` with createrepo metadata and
  **~80 binary RPMs baked** (44 noarch + 39 in x86_64 dir, including kernel-ish ones).

## 3. Systemic packaging bugs fixed during the run

- Added missing `Source0:` to specs that had none (many `synthex-*` data packages).
- Inserted real `%prep`/`%setup -q -n synthex-repo-<ver>` into empty/nop `%prep` blocks
  (this unblocked sddm-theme, plymouth-theme, grub-theme, cursors, release, sounds,
  calamares-branding and others).
- Generated the missing standalone sources: `RPM-GPG-KEY-synthex` and calamares
  `branding.desc`/`show.qml`/logo pngs.
- Regenerated the `synthex-repo-*.tar.gz` so the cursor theme's `target/` files and
  inherited `LICENSE` are actually included (they had been excluded).
- Stubbed Fedora systemd/`%_unitdir`/`%_sysusersdir` macros so `%systemd_*`-using specs
  can be parsed on Mint.

## 4. What remains and why it must run in the Fedora container

- **~40 cargo-compiled daemons**: each spec runs a fresh full-workspace `cargo build
  --release` (~8 min each) inside rpmbuild. Doing that 40× on this near-full host is not
  practical; the source is proven-good (see §2). Build these inside `build/livecd` (Fedora
  `livemedia-creator`/`lorax`) where cargo caching + `%cargo_*` macros exist.
- **COSMIC DE (`cosmic-applets` … )~16 packages**: `%r1`-era upstream via pop-os tags
  that return 404 on this network, plus cargo. Needs the container with a vendored source.
- **`rust-utils-*` (~18)**: mix of GitHub (already fetched) + crates.io sources (a few
  version-mismatched, e.g. `dog` isn't the DNS client; `bandwhich 0.40.0` doesn't exist,
  latest 0.23.1) and lib-devel build deps (libpcap, libsene pine, etc.).
- **`synthex-kernel`**: full kernel build from `linux-6.14.tar.xz` (already downloaded) —
  needs build toolchain + ≥ 25–30 GB free.
- **`synthex-branding`** (+ logos/backgrounds): expects a flat `wallpaper/,logo/,grub/`
  layout and ImageMagick/grub-mkfont/xcursorgen tools; the layout differs from
  `branding/` in this repo, so it's container work.
- Fixes left are **per-package missing content** (Python `main.py`, `*.qml`, `grub-default`,
  `hermes.desktop`, etc.) that must first exist in the repo before any spec can be packaged —
  these aren't simply bypassed.

## 5. Recommended next steps (off this host / in container)

1. Boot the `build/livecd` Fedora container: it provides Fedora tooling, `%cargo_*`
   macros, and lots of free disk for the kernel + daemons + COSMIC.
2. `createrepo_c` the prebuilt daemon RPMs into the local repo (kickstart off the live-only
   repo) — see hook in `build/kickstart/synthex-hyprland.ks` that already replaces dead
   `packages.getsynthex.org` with `file://` refs.
3. Build kernel + initrd; assemble rootfs; run `build/scripts/build-iso-fixed.sh` which
   enforces the size gate and validates `unsquashfs -stat`.