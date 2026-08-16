# Spec Patterns — How Each Kind of Package is Built

Every `.spec` in `packages/spec-files/` follows one of a small set of
patterns. This is the "shape" of the whole spec tree — useful when you
open a new spec and want to know what it will do without reading 170+.

## The patterns (in rough priority)

### 1. Pure-data / noarch (config, sysctl, themes)

- `BuildArch: noarch`.
- `%build: true`.
- `%install`: `install -d …` + `cp`/`install` from the monorepo
  tarball (`synthex-repo-<version>` via `%setup -n`).

Representative specs: `synthex-grub-theme`, `synthex-sddm-theme`,
`synthex-sounds`, `synthex-cursors`, `synthex-system-config`,
`synthex-branding-part` (not built), `synthex-aios` (umbrella).

### 2. Python app → launcher (noarch)

The spec copies a `src/<name>/` dir into `/usr/libexec/synthex/` and
writes a `/usr/bin/<name>` launcher that calls `python3 main.py`.

Representative: `synthex-tray`, `synthex-disk-health`,
`synthex-workspace`, `synthex-webapp-engine`, `synthex-widgets`.

### 3. Rust daemon → prebuilt binary copy

`%build` copies a prebuilt binary from the project `target/release/`
into the spec, and `%install` puts it in `%{_bindir}`.

Representative: `synthex-stored`, `synthex-system-daemon`,
`synthex-hwdaemon`, `synthex-brain`, `synthex-hermes`, all `synth*`.

```
%build
install -d target/release
install -m755 /home/jewboy420/linux-synthex/target/release/%{name} target/release/%{name}
```

This is why the Rust daemons build fast — we don't compile in rpmbuild.

### 4. Shell-tool single-file source

Specs whose `Source0` is a **single file** (in `build/rpmbuild/SOURCES`)
instead of the monorepo tarball. `make-srctars.sh` copies these.

Representative: `synthex-ujust` (→ `ujust`), `synthex-service-manager`
(single binary), `synthex-locale-setup`, `synthex-nvidia-installer`.

### 5. COSMIC DE (pending)

`cosmic-*` specs fetch pop-os upstream tarballs (Cargo). Not built on
host (see `docs/PENDING.md`).

### 6. rust-utils (pending)

`rust-utils-*` — external Rust CLI tools fetched from crates.io/GitHub.
Not built on host.

### 7. Meta + group packages

`@`, `synthex-meta-*`, `synthex-gaming-platform`, `synthex-core`,
`kernel-meta` — mostly `Requires:`/`Obsoletes:` aggregates, no content.

Representative: `synthex-meta-gaming`, `synthex-meta-minimal`,
`synthex-core`.

## The three header things that matter (and their common bugs)

| Field | Correct value | Bug it avoids |
|---|---|---|
| `Source0:` | `synthex-repo-%{version}.tar.gz` | needs the tarball in `SOURCES` |
| `Source1:` | declared if `%install` references `%{SOURCE1}` | undefined-Source crash |
| `%prep` | `%setup -q -n synthex-repo-%{version}` | `%setup -c -T` doesn't extract; default `-n` gives wrong dir |
| `BuildArch:` | `noarch` for no-compile pkgs | arch flakiness |

## %files must mirror %install

Every spec's `%files` **must** list exactly what `%install` created
(otherwise rpm errors "File not found"). When fixing a failing spec,
the first: compare `%install` and `%files`.

## Adding a spec in this tree

Follow `docs/EXTENDING.md#adding-a-new-spec` for the exact recipe.

## The umbrella spec (synthex-aios)

The AI-OS layer is shipped as one spec that bundles `configs/aios/`,
`configs/upstream/`, and `configs/performance/`. It is:
- `BuildArch: noarch`.
- `%prep %setup -q -n synthex-aios-%{version}` (its own tarball
  `synthex-aios-<version>.tar.gz`).
- installs the CLI, doctor, persona, install, update-sync, defaults,
  and the systemd units + sysctl + config.
- `Requires: synthex-brain synthex-hermes systemd`.

See `docs/PACKAGING.md` for the full macros and error table.