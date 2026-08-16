# Kickstarts — Editions & Reference

The ISO images are built from **kickstart files** (`build/kickstart/`).
Each edition has an **original** (`synthex-<ed>.ks`) and a **patched**
(`synthex-<ed>-local.ks`) that points at the local repo + Fedora kernel
set instead of the dead upstream domain.

```
build/kickstart/
  synthex-hyprland.ks      synthex-hyprland-local.ks   ← used by runner
  synthex-plasma.ks        synthex-plasma-local.ks
  synthex-gnome.ks         synthex-gnome-local.ks
  synthex-gaming.ks        synthex-gaming-local.ks
  synthex-minimal.ks       synthex-minimal-local.ks
  synthex-gaming-packages.ksinc   (included packages for gaming)
```

## Edition table

| Edition | Lines | DE / focus |
|---|---|---|
| **plasma** | 401 | KDE Plasma 6 (most complete). |
| **hyprland** | 359 | Hyprland Wayland compositor (the one the runner uses). |
| **gaming** | 296 | Gaming-first (Steam/gamespope/gamemode focus). |
| **gnome** | 242 | GNOME. |
| **minimal** | 160 | Minimal base, no desktop shell. |

All editions share the same root (Fedora 42 base + RPM Fusion + local
repo), differ in `%packages` and `%post`.

## Common `%packages` (all editions)

- `@core @hardware-support @fonts @multimedia @networkmanager-submodules`
- The DE / session (Hyprland pub Hypr, or Plasma, or GNOME).
- Terminal / file manager / media / screenshot / Wayland basics.
- **Fedora kernel set**: `kernel kernel-core kernel-modules
  kernel-modules-core kernel-modules-extra` (patched editions).
- `synthex-*` packages referenced by `%packages` (e.g. `synthex-aios`,
  `synthex-core`, `synthex-system-daemon`, etc.).

## The patch differences in `-local.ks`

The `-local.ks` files were created from the originals by `sed`:

1. `url --mirrorlist=...fedora-42...` → explicit base URL
   `https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/42/Everything/x86_64/os/`
   (with the mirrorlist kept as a redundant source).
2. `repo synthesizer` / `repo synthesizer-updates` → `file:///home/jewboy420/linux-synthex/build/repo/x86_64`.
3. `%packages` `synthex-kernel` → the Fedora kernel set.
4. Rewrote the in-file `baseurl=https://packages.getsynthex.org/...` lines
   in `%post` to `file://...`.

Result: **no `packages.getsynthex.org` references** remain in the patched
files. `verify.sh`/`prepare-kickstart.sh` enforce this.

## The `%post` block (shared)

Each `%post` does broadly:

- Installs SynthOS shell configs into `/etc/skel` (fish, starship,
  kitty, fastfetch, wofi, mako).
- Writes `/etc/yum.repos.d/synthex.repo` pointing at the local repo.
- `flatpak remote-add flathub ...` (Flathub).
- Configures greetd (Hyprland) or SDDM (Plasma) for autostart.
- Writes the default DE config (Hyprland/Plasma/GNOME skeleton).
- Enables NetworkManager/greetd/chronyd/auditd/fstrim; disables
  lvm2-monitor.
- Creates `liveuser`, enables `synthex-firstboot.service`.
- Touches `/etc/synthex/live-mode` then enables
  `synthex-live-setup.service` (live, gated by `ConditionPathExists`).
- Optionally enables the AIOS first-boot unit.

The heavy lifting for the AIOS layer is actually in
`build/scripts/post-install.sh` (630 lines). The kickstart just calls it.

## Selection & build

- `build/run-iso-build.sh` uses `synthex-hyprland-local.ks`.
- `build/scripts/build-all.sh` loops the editions (plasma, gaming,
  gnome, hyprland, minimal).
- `build/scripts/prepare-kickstart.sh` validates and stages them.

## How to add an edition

See `docs/EXTENDING.md#adding-a-new-kickstart-edition`.

## Validation

`build/scripts/prepare-kickstart.sh --validate-only` checks each file
for: required sections, valid `%packages`, no dead repo URLs, kernel
packages present. `grep -c 'packages.getsynthex' *.ks` should return 0.