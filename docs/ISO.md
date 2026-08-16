# ISO Assembly

The bootable ISO is built **inside a Fedora 41 builder container** with
`lorax` and `livecd-creator` (livemedia-creator). The host side does
**not** produce the ISO directly — it only produces the local RPM repo
and the patched kickstart files. This document explains both halves.

## Two-stage pipeline

```
HOST (Linux Mint)                              BUILDER (Fedora 41 container)
─────────────────────                         ─────────────────────────────
build/repo/{noarch,x86_64}  ─────bind mount────▶  /repo
build/kickstart/*.local.ks  ─────bind mount────▶  /ks/synthex-*.ks
                                              run livecd-creator
                                                       │
                                                       ▼
build/iso-out/Synthex-Hyprland-...iso ◀──────────  (in container, copied back)
```

The container reads the **kickstart file**, resolves packages from the
local repo + Fedora base + RPM Fusion, runs all `%post` scripts
(including the AIOS layer via `synthex-aios` package, which installs
`/usr/bin/synthex`, etc.), and assembles the result into the canonical
Fedora live layout (`/LiveOS/squashfs.img` containing `/LiveOS/rootfs.img`).

## The original boot bug and the fix

The original ISO (`build/iso-out/synthex-2026.10-hyprland-x86_64.iso`)
was unbootable for **two reasons**:

1. **Wrong kernel.** It booted the **host’s Ubuntu kernel**
   (`6.14.0-37-generic`) because the build fell back to `/boot` on the
   Mint box. The Fedora live initramfs then couldn’t find its expected
   dracut layout → dropped to initramfs shell.

2. **Corrupt squashfs.** `squashfs.img` was 4.29 GB — **just over the
   ISO9660 4 GiB single-extent limit**. `xorriso` wrote it as a
   multi-extent file and zero-filled the head, so `unsquashfs` saw an
   empty superblock and aborted.

`build/scripts/build-iso-fixed.sh` fixes both:

- Hard-rejects Ubuntu/generic kernels (`strings vmlinuz | grep "Linux
  version"`).
- Refuses to ship any `squashfs.img ≥ 3.8 GiB`.
- Verifies the squashfs superblock is readable **after** assembly.
- Uses a **single-pass `xorriso`** (no appends, no multi-extent).

## Runner: `build/run-iso-build.sh`

One command:

```bash
build/run-iso-build.sh
```

What it does:

1. Builds a slim `synthex-builder` Docker image from `fedora:41`,
   installing only `lorax livemedia-creator pykickstart xorriso
   squashfs-tools grub2 dnf-utils createrepo_c rpm-build` (not the full
   KDE / Qt / KF6 stack in `build/livecd/Dockerfile` — that full image
   is intentionally heavy for completeness, the slim one is what we
   use here for fast iteration).

2. Runs the builder with `--privileged` (livecd-creator needs loop
   devices and systemd-nspawn) and bind-mounts the project tree.

3. Inside the container, executes:
   ```
   livecd-creator --verbose \
     --config=/ks/synthex-hyprland-local.ks \
     --releasever=42 \
     --title="SynthOS" --product="SynthOS" \
     --volid="SYNTHEX_HYPRLAND_2026_10" \
     --compression-type=zstd \
     --keep-image \
     -o /repo/Synthex-Hyprland-2026.10-x86_64.iso
   ```

   This pulls:
   - The **Fedora 42 base** from `mirrors.fedoraproject.org`.
   - The **RPM Fusion free + nonfree** from `mirrors.rpmfusion.org`.
   - The **local repo** at `file:///home/jewboy420/linux-synthex/build/repo/x86_64`.

4. Validates the ISO.

## Patched kickstarts

`build/kickstart/synthex-hyprland-local.ks` is the **patched** kickstart
that the runner uses. The patches (applied to all 5 editions:

`build/kickstart/synthex-plasma-local.ks`,
`build/kickstart/synthex-gnome-local.ks`,
`build/kickstart/synthex-minimal-local.ks`,
`build/kickstart/synthex-gaming-local.ks`,
`build/kickstart/synthex-hyprland-local.ks`:

- **`url` is now an explicit Fedora 42 base URL** (and `mirrors.fedoraproject.org` mirrorlist for redundancy).
- **`repo synthex` and `repo synthex-updates`** now point at the local
  `build/repo/x86_64` (`file://...`).
- **All `synthex-kernel` references are replaced with the Fedora kernel set**
  (`kernel kernel-core kernel-modules kernel-modules-core
  kernel-modules-extra`) — so the image uses the **Fedora 41 kernel**
  (6.11.4-301.fc41), which is vendored in `build/repo/x86_64/`.

The dead `packages.getsynthex.org` URLs are **gone** — no build will fail
on DNS for that domain.

## What lives in the image

The image ends up containing (approximately):

- A **GRUB 2 bootloader** (BIOS + EFI) referencing `vmlinuz` and
  `initrd.img` in the ISO root.
- `vmlinuz` = `kernel-core-6.11.4-301.fc41.x86_64` (the Fedora kernel
  we vendored).
- `initrd.img` = Fedora dracut with `rd.live.image`.
- `/LiveOS/squashfs.img` = the root filesystem, built by livecd-creator
  from:
  - Fedora 42 base packages.
  - RPM Fusion free + nonfree.
  - All `synthex-*` packages from `build/repo/`, including:
    - `synthex-aios` → installs `/usr/bin/synthex`, `synthex-doctor`,
      `synthex-persona`, `synthex-install`, `synthex-update-sync`,
      and the systemd units.
    - `synthex-brain`, `synthex-hermes` → AI daemons.
    - All other Synthex-specific RPMs (~120 distinct packages).

## Verifying the squashfs is valid (inside the runner)

```bash
unsquashfs -stat build/iso-out/Synthex-Hyprland-2026.10-x86_64.iso
```

If this fails, the runner refused to ship the ISO.

## Caveats

- The full livecd-creator build is a **long, network-heavy operation**
  (multiple GB of Fedora + RPM Fusion downloads, plus the local repo).
  It is intended to be run as a monitored job.
- The full `build/livecd/Dockerfile` image (with Qt / KF6 etc.) is
  intentionally heavier — it builds a more complete dev environment.
  The slim builder is what `build/run-iso-build.sh` uses for ISO builds.
- `nobara` packages are not yet followed by the live build (see
  `docs/UPDATER.md` and `docs/AIOS.md#synthex-update-sync`); flipping
  `enabled: true` in `synth-pkgs.conf` once your infrastructure can
  reach Nobara is the next step.
