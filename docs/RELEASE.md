# Release & Configuration Notes

## Versioning

- `VERSION` file at repo root (default `2026.10`).
- Codename for 2026.10: **Ignition**.
- Specs use `%{version}`-derived tarballs (`synthex-repo-<VERSION>.tar.gz`).

## `build/scripts/release.sh`

```bash
./build/scripts/release.sh [VERSION=2026.10] [CODENAME=Ignition] [EDITION]
```

Preflight: requires `cargo`, the kickstart files, and running from repo
root.

Produces `build/release/<VERSION>/`:

- the ISO(s) for the requested edition,
- `SHA256SUMS` file,
- a manifest / changelog snippet,
- (when `--sign`) detached GPG signatures.

## The build steps that release.sh performs

```
1. Pre-flight: cargo, kickstart files present, repo root.
2. package build via the container (local-repo) → build/repo.
3. ISO build(s) via build-iso / build-all.
4. validate each ISO (validate-iso.sh).
5. checksum (SHA256SUMS) + (optionally) sign.
6. write build/release/<VERSION>/ + changelog.
```

## Checksums

The release writes:

- `SHA256SUMS` — checksums for every iso + `.sig` file.
- `*.torrent` + `.magnet` (if `transmission-cli` present) for the
  gaming edition (fun-to-ship).

## GPG

- If you pass `--sign` (or run `build-iso.sh --sign`), a key is needed.
- If none found, a **build key** is generated (`build@getsynthex.org`)
  and stored in `%{_gnupg_home}` (default `~/.gnupg`).
- The detached signature is written as `.sig`; `isohybrid --uefi`
  embeds one on the ISO (grub2-utils / xorriso).

## Changelog policy

- `docs/CHANGELOG.md` and `docs/RELEASE-NOTES-2026.10.md` track the
  human changelog.
- Each spec's `%changelog` tracks the package-level changes.

## The "Solus" leftover

Currently `kernel/config-x86_64`, `kernel/cmdline.default`, and
`kernel/configs/synthex-x86_64-defconfig` still contain the string
**"Solus"** and `CONFIG_LOCALVERSION="-solus"`. The project was renamed
from "Solus" to "SynthOS"/"Synthex". This is a **leftover that should
be renamed** (and, because we ship the **Fedora** kernel anyway, these
files are documentation/reference only). See `docs/KERNEL-CONFIG.md`.

## Artifact naming

- ISO: `Synthex-<Edition>-<VERSION>-x86_64.iso`
  (e.g. `Synthex-Hyprland-2026.10-x86_64.iso`).
- Vol ID: `SYNTHEX_HYPRLAND_2026_10`.
- Repo: `build/repo/{noarch,x86_64}` + `synthex-local.repo`.

## What’s NOT finalized

- The ISO is built inside the Fedora 41 container; it is not executed on
  this host.
- `release.sh --push` (rsync to a server) is a stub with a placeholder
  host. Not wired for production.