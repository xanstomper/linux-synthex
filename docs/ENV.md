# Environment & Macro Reference

The complete list of environment variables, rpmbuild macros, and config
keys that control the SynthOS build and runtime. Keep this page updated
whenever you add a knob.

---

## Environment variables (AIOS runtime)

| Variable | Default | Tool | Meaning |
|---|---|---|---|
| `SYNTHEX_AETHER_HOST` | `127.0.0.1` | `synthex` CLI | where to probe the AETHER broker |
| `SYNTHEX_AETHER_PORT` | `8787` | `synthex` CLI | AETHER TCP port |
| `SYNTHEX_CFG` | `/etc/synthex/upstream/synth-pkgs.conf` | `synthex-update-sync` | tracked-packages config |
| `SYNTHEX_STAGE` | `/var/cache/synthex/updates` | `synthex-update-sync` | where `stage` writes candidates |
| `SYNTHEX_STATE` | `/var/lib/synthex/update-state.json` | `synthex-update-sync` | apply state (for rollback) |
| `SYNTHEX_REPO` | `/var/lib/synthex/repo` | `synthex-update-sync` | where `apply` writes `queue.jsonl` |
| `SYNTHEX_SNAPPT` | `/usr/sbin/synthex-snapshot` | `synthex-update-sync` | snapshot helper path |
| `SYNTHEX_QUEUE` | `${SYNTHEX_REPO}/queue.jsonl` | `synthex-update-sync` | override queue path |

> Note: the runtime `SYNTHEX_*` vars are **read** by
> `synthex-update-sync.py`. The CLI uses `SYNTHEX_AETHER_HOST` and
> `SYNTHEX_AETHER_PORT`.

## 2. Build-time macros (`~/.rpmmacros`)

These must exist for Ubuntu’s `rpm` to understand Fedora systemd/udev
and build macros.

```rpmacros
%_topdir /home/jewboy420/linux-synthex/build/rpmbuild
%_tmppath %{_topdir}/tmp
%_sourcedir %{_topdir}/SOURCES
%_rpmdir %{_topdir}/RPMS
%_builddir %{_topdir}/BUILD
%_unitdir /usr/lib/systemd/system
%_userunitdir /usr/lib/systemd/user
%_udevrulesdir /usr/lib/udev/rules.d
%_sysconfdir /etc
%_datadir /usr/share
%_bindir /usr/bin
%_sbindir /usr/sbin
%_libexecdir /usr/libexec
%_libdir /usr/lib
%__meson meson
%meson_build %__meson %{?_smp_mflags}
%meson_install %__meson install -C build --destdir %{buildroot}
%py3_build %{__python3} setup.py build
%py3_install %{__python3} setup.py install --root=%{buildroot}
```

These are the Fedora systemd/udev macros that Ubuntu’s `rpm` is missing.

## 3. Config keys (`synth-pkgs.conf`)

Top-level:

- `name` (string) — human name of this tracker.
- `enabled` (bool) — master toggle.
- `tracked` (array) — list of `{name, repo, pkg}`.
- `repos` (object) — `{fedora, rpmfusion, nobara}`; `nobara` has
  `{enabled, baseurl, note}`.

`tracked[].repo` must be one of `fedora`, `rpmfusion`, `nobara`, else
`repo_url` returns `""` and the entry is skipped.

## 4. Shell env for the build batch helper

No env. `build_batch.sh` runs each spec with a 90 s timeout and writes
`/tmp/rb_<name>.log`.

## 5. Macro/`%`-prefixed values used by the specs

The # alongside packages specs use:

| Macro | Meaning | Example |
|---|---|---|
| `%{version}` | the spec's `Version:` | `synthex-repo-%{version}.tar.gz` |
| `%{release}` | the spec's `Release:` | `1%{?dist}` |
| `%{name}` | the spec's `Name:` | used in `-n %{name}-%{version}` (sometimes wrong — use `synthex-repo-%{version}`) |
| `%{_unitdir}` | systemd unit dir | `/usr/lib/systemd/system` |
| `%{_userunitdir}` | systemd user unit dir | `/usr/lib/systemd/user` |
| `%{_udevrulesdir}` | udev rules dir | `/usr/lib/udev/rules.d` |
| `%{_libexecdir}` | libexec dir | `/usr/libexec` |
| `%{_prefix}` | prefix | `/usr` |
| `%{_sysconfdir}` | config dir | `/etc` |
| `%{_datadir}` | data dir | `/usr/share` |
| `%{_bindir}` | binaries dir | `/usr/bin` |
| `%{_sbindir}` | system binaries | `/usr/sbin` |
| `%{_dIsnt}` | distro str | `%{?dist}` (harmless) |
| `%{python3_sitelib}` | python site dir | not always defined (was the ai-hub bug) |

## 6. The `GRUB_CMDLINE_*` keys in the kickstart `%post`

These come from `grub-synthex.cmdline` (documentation). The install
script appends `transparent_hugepage=never` etc. to
`GRUB_CMDLINE_LINUX_DEFAULT`. Safe (append-only) and reversible.

## 7. Validation

- `docs/REFERENCE.md` — every env/var hook.
- `configs/tests/verify.sh` — asserts the config JSON parses and the
  runtime steps run in a sandbox.
- `grep -R "SYN*" configs src` gives the exact usage sites.

Keep this file current whenever you add a new VAR/macro/config key.