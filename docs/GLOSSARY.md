# Glossary

Definitions of every term / acronym used in the SynthOS docs. Sorted
alphabetically.

| Term | Meaning |
|---|---|
| **AETHER** | The older "OS-level AI consciousness" daemon design (memory graph + capability broker). Exposes a JSON-line TCP API on `127.0.0.1:8787`. The `synthex` console can probe it. |
| **Bodhi** | Fedora's build/update-tracking API used by `synthex-update-sync` to find the latest published update of a package. |
| **`build/`** | The build tree (`build/rpmbuild`, `build/repo`, `build/kickstart`, `build/scripts`). |
| **`configs/`** | The AIOS + performance + upstream-tracker source layer (in-repo, packaged as `synthex-aios`). |
| **`createrepo_c`** | Tool that generates YUM/DNF repo metadata (`repodata/`); used to build the local RPM repo. |
| **DKMS** | Dynamic Kernel Module Support — the safe way to install out-of-tree drivers (e.g. NVIDIA) via rpmfusion, never the `.run` script. |
| **Fedora 41** | The base image the Fedora **builder container** is `FROM`. |
| **Fedora 42** | The release `livecd-creator` assembles into the target rootfs. Base packages come from the Fedora 42 archives + RPM Fusion. |
| **Fedora kernel** | The official, signed Fedora 41 kernel (`6.11.4-301.fc41`) vendored in `build/repo/x86_64`. What the ISO boots. |
| **Flathub** | The Flatpak app store, wired into the kickstart `%post`. |
| **gamemode** | Feral's tool that temporarily raises performance while a game holds its token; config in `/etc/gamemode.ini`. |
| **gamescope** | A Valve Wayland compositor used to fly games with low latency; `synthex-game-session` wraps it. |
| **`LiveOS`** | The Fedora dracut live-layout: `/LiveOS/squashfs.img` → `/LiveOS/rootfs.img`. |
| **`livecd-creator`** | The lorax tool that assembles a rootfs + squashfs + ISO from a kickstart. |
| **`lorax`** | The Fedora anaconda/liveimg library used by `livecd-creator`. |
| **Mint/Bazzite-styleupdater** | `synthex-update-sync` — the "follow the upstream, never brick" coordinator. |
| **noarch** | An RPM architecture tag for packages with no compiled (architecture-specific) binaries. |
| **persona** | One of `gamer / creator / developer / privacy / minimal` — a profile that pre-installs packages + toggles units. |
| **`queue.jsonl`** | The real build queue the updater writes; the Fedora builder consumes each line. |
| **RPM Fusion** | The third-party Fedora repos (free + nonfree) for media/codecs/gaming. |
| **snapper** | Btrfs snapshot management used for timeline + rollback. |
| **`SYNTHX_*` env vars** | Runtime knobs for the update-sync (CFG/STAGE/STATE/REPO/SNAP/QUEUE). |
| **`synthex`** | The assistant console (`/usr/bin/synthex`). |
| **`synthex-aios`** | The umbrella RPM packaging the AI-OS layer + perf defaults. |
| **`synthex-defaults`** | First-boot enabler of the "differentiator" units. |
| **`synthex-doctor`** | One-shot health report. |
| **`synthex-install`** | Snapshot-guarded, `--yes`-gated app/driver installer. |
| **`synthex-persona`** | Profile picker. |
| **`synthex-update-sync`** | The upstream tracker / Mint-Bazzitte-style updater. |
| **`verify.sh`** | The single harness (`configs/tests/verify.sh`) that proofs the AIOS layer runs. |
| **v3/v4** | `x86-64-v3` / `x86-64-v4` microarchitecture baseline in the aspirational kernel spec. |

## Short glossary by layer

- **AIOS layer**: `synthex`, `synthex-doctor`, `synthex-persona`,
  `synthex-install`, `synthex-update-sync`, `synthex-defaults`.
- **Performance**: `synthex-gov` (governor), `zram`, `gamescalope`,
  `gamemode`, sysctl.
- **Builder**: `rpmbuild`, `rpm`, `createrepo_c`, `xorriso`,
  `lorax`, `livecd-creator`, `isomd5sum`, `mksquashfs`.
- **Distro base**: Fedora, RPM Fusion, Flatpak/Flathub, `dnf`.