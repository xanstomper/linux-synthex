# Pending / Not-yet-built Packages

Of the **173 specs**, **125 build locally**; the remaining **48** fall
into a few well-defined groups that need the **Fedora builder container**
(or a dedicated environment) rather than the generic Mint host. This is
the honest inventory — nothing here is "broken"; it just can't build on
THIS host for the reason given.

## 1. COSMIC Desktop Environment (16 specs)

```
cosmic-app-library        cosmic-applets            cosmic-bg
cosmic-comp               cosmic-epoch              cosmic-files
cosmic-notifications      cosmic-osd                cosmic-panel
cosmic-randr              cosmic-screenshot         cosmic-settings
cosmic-term               cosmic-text-editor        cosmic-workspaces
xdg-desktop-portal-cosmic
```

**Why not built here**: these are **upstream pop-os / System76 Rust
apps** whose exact release tarballs (v24.04.0) returned **404 on this
host’s network** at `archives.fedoraproject.org`/GitHub. They need:

- The actual upstream source tarballs (correct tag names), fetched in
  the Fedora builder where reachable.
- A Cargo / target build at the exact pinned version.

**Status:** tracked as COSMIC DE; would be the "modern desktop" spin.
Until the vendor tar URLs resolve + the cargo build works, they don't
build.

## 2. rust-utils (the extra CLI toolkit) — 19 packages

```
rust-toolchain
rust-utils-atuin  rust-utils-bandwhich  rust-utils-bat
rust-utils-bottom rust-utils-delta     rust-utils-dog
rust-utils-dua-cli rust-utils-dust    rust-utils-eza
rust-utils-fd      rust-utils-gping    rust-utils-helix
rust-utils-hyperfine rust-utils-just  rust-utils-nushell
rust-utils-ouch    rust-utils-procs    rust-utils-ripgrep
rust-utils-sd      rust-utils-starship rust-utils-tealdeer
rust-utils-zellij  rust-utils-zoxide
```

**Why not built here:**
- Some are Fedora-less (the `dog` package in the spec is the wrong
  crate — the real `dog` DNS client isn't a `crates.io` crate).
- `bandwhich`'s spec pins version 0.40.0 which doesn't exist (newest is
  0.23.1).
- The rest need `rust-toolchain` rebuild (heavy).
- Build-time deps (libpcap, zlib-devel) not present on the host.

**How:** build these inside the Fedora builder (they're small Rust
binaries; the source tarballs mostly exist already in
`build/rpmbuild/SOURCES/`).

## 3. Kernel toolchain / future kernel build

- `rust-toolchain` — a from-scratch Rust compiler build (hours). Not
  something you build casually on Mint.
- `synthex-kernel` (+ subpackages) — **we ship the Fedora kernel** and
  intentionally do NOT build our own (see `docs/KERNEL.md`).

## 4. Remaining Synthex-only Python/QML/GUI packages

| Spec | Missing |
|---|---|
| `synthex-branding` | expects a flat `wallpaper/` layout + heavy build tools (ImageMagick, grub-mkfont, xcursorgen) and dep slack `synthex-logos`/`synthex-backgrounds`. The branding dir is `branding/`, not flat. |
| `synthex-(ai-hub|ai-platform)` GUI | Python apps; the `ai-platform` needs build-id + a preset (we added a stub, but tiered front-ends still pending). |
| `synthex-gaming-control-center` | a gaming control-center UI not in the release workspace. |
| `synthex-safety` (parts) | ongoing; many pieces now build (udev, sysctl), the "fully working" SELinux module is pending. |

These are **not broken**; they're **unfinished**. Each needs real
(not-stub) source content in the repo and/or a Fedora build env.

## Why "pending" != "bug"

The repo is intentionally scope-limited for the **host build**:

- The `verify.sh` harness only gates **what we implemented and can
  prove** — it never pretends the pending ones are done.
- The 48 pending are all in the `build/repo` **absent** because they
  need either a network the Fedora builder can reach, a cargo build at a
  pinned version, or the rest of the desktop (`cosmic-*`) which isn't
  in the release canon.

## What happens when the network/build allows

In the Fedora builder container (lorax/livemedia-creator available):

```bash
HEAVY=1 build/scripts/local-repo.sh
```

which attempts the COSMIC/rust/kernel packages. Those that are
Source-external get skipped if offline; the rest build. Then the
kickstarts get `synthex-<ed>-local.ks` (already prepared) and
`build/run-iso-build.sh` builds the ISO with the local repo.