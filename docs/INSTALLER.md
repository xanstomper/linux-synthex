# Installer (Calamares)

SynthOS ships a **Calamares-based** installer for the live ISO. The
spec is `synthex-installer` and it is included in the local RPM repo.

This document is short because the heavy lifting lives in
`docs/ISO.md` (image assembly) and `docs/PACKAGING.md` (RPM
packaging). What’s specific to the installer:

## Where it lives

```
packages/spec-files/synthex-installer.spec
build/rpmbuild/SOURCES/synthex-installer-<version>.tar.gz
```

The spec is intentionally minimal right now: it ships module config
stubs (so livecd-creator finds the `%packages` entry without erroring).
The full Calamares configuration (modules, branding, slideshow,
theme, post-install hooks) is in development.

## What is shipped today

When the ISO boots and the user picks “Install”:

1. Calamares launches.
2. It walks the user through partition, user creation, summary.
3. At the end, the user clicks Install and Calamares writes the root
   filesystem from the live squashfs to the target disk.

The `synthex-installer` package contributes the `installer/config/modules/*.conf`
files that livecd-creator copies into `/etc/calamares/modules/`. The
actual Calamares modules (`synthexprofile`, `synthexpostinstall`,
`synthexgpusetup`, `synthexhardwaredetect`, …) ship in source form
under `installer/modules/` and are configured when the
image is built.

## How to extend

To add a new Calamares module:

1. Add the module sources under `installer/modules/<name>/` (Python
   module + `module.desc`).
2. Add a `<name>.conf` under `installer/config/modules/` (Calamares
   configuration referencing the module + its `main.py`).
3. Rebuild the tarball: `build/scripts/make-srctars.sh 2026.10`.
4. Rebuild `synthex-installer` RPM and re-sync the repo.
5. Re-run `build/run-iso-build.sh` to bake the new module into the
   ISO.

When the user installs with Calamares, your module runs at the
appropriate phase (you choose the phase in `module.desc`).

## Honest state

The full Calamares configuration is in progress. Right now the spec
ships the minimal stubs so the ISO **does not fail** to install. The
user experience is functional (partition → user → write to disk →
reboot) but not yet polished. The framework is in place to drop in
real modules.

## See also

- `docs/ISO.md` — how the ISO is assembled.
- `docs/PACKAGING.md` — RPM conventions for the installer spec.
- `docs/EXTENDING.md` — how to add modules.
