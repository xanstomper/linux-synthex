# Config Files Register — `configs/`

A complete inventory of **every** configuration file that the repo ships,
grouped by subsystem. This is the "grey pages" of all config; the *why*
and *runtime* references live in `docs/CONFIG-FILES.md` and
`docs/REFERENCE.md`.

Legend: `★` = functionally important default, `◦` = supplementary.

---

## `configs/agent-policies/`
The per-agent policy asked by `synthex-hermes` / the Agent Runtime.

| File | Purpose |
|---|---|
| `default.toml` | Default agent policy (capabilities, isolation). |
| `cline.toml` | Agent policy scoped to the "cline" line-assistant profile. |

## `configs/aios/` — the AIOS layer (see `docs/REFERENCE.md`)
## `configs/performance/` — the perf layer (see `docs/REFERENCE.md`)
## `configs/upstream/` — the tracker (see `docs/REFERENCE.md`)
## `configs/tests/` — the harness (`verify.sh`, see `docs/README.md`)

---

## `configs/btrfs/` — btrfs maintenance

| File | Purpose | Runtime |
|---|---|---|
| `btrfs-scrub-timer.conf` | Systemd timer override for `btrfs-scrub@` (`OnCalendar=weekly`). | `synthex-defaults` enables `btrfs-scrub@-.timer` |
| `synthex-btrfs-balance` | Cron/service wrapper that runs `btrfs balance start -dusage=30 /`. | `synthex-safety` and the cron. |

## `configs/calamares-branding/` — installer branding

| File | Purpose |
|---|---|
| `show.qml` | The QML slideshow shown during install. |
| (`branding.desc`, pngs are generated/stubbed in `build/rpmbuild/SOURCES`). | product info, sidebar colors. |

## `configs/crypttab/` + `configs/disk-encryption/`

| File | Purpose |
|---|---|
| `crypttab` / `crypttab` | LUKS `crypttab` entries (LUKS by default). |
| disk-encryption/ | (empty) placeholder — future: full-disk-encryption notes. |

## `configs/dnf/` — package manager tuning

| File | Purpose |
|---|---|
| `synthex-dnf.conf` | DNF defaults (parallel downloads, `lazy` etc.). |
| `dnf-automatic.conf` | `dnf-automatic` (auto-check, auto-download). |

## `configs/dracut/` — initramfs

| File | Purpose |
|---|---|
| `dracut-synthex.conf` | Dracut settings; installed to `/etc/dracut.conf.d/synthex.conf`. |

## `configs/firewalld/` — firewall zones

| File | Purpose |
|---|---|
| `synthex.xml` | Default firewall zone. |
| `synthex-gaming.xml` | Gaming zone (relaxed for multiplayer). |

## `configs/flatpak/` — flatpak remotes

| File | Purpose |
|---|---|
| `flathub.flatpakrepo` | Flathub remote definition. |
| `synthex.flatpakrepo` | (placeholder) SynthOS remote. |

## `configs/gaming/` — gaming defaults

| File | Purpose |
|---|---|
| `environment-gaming.conf` | Game env vars (MANGOHUD, etc.). |
| `game-profiles.json` | Per-game compile. |
| `limits.conf` | ulimits for gaming. |

## `configs/grub/` — GRUB

| File | Purpose |
|---|---|
| `40_synthex` | GRUB snippet (btrfs + snapshot entries). |
| `grub-default` | GRUB defaults (`GRUB_TIMEOUT=5`, etc.). |
| (`grub-synthex.cmdline` → see `configs/performance/`) | cmdline docs. |

## `configs/input-remapper/`

| File | Purpose |
|---|---|
| `controller-presets.json` | Gamepad → keyboard/mouse presets. |

## `configs/journald/`, `configs/timesyncd/`, `configs/oomd/`

| File | Purpose |
|---|---|
| `journald-synthex.conf` | Journald (500M cap, persistent). |
| `timesyncd-synthex.conf` | systemd-timesyncd NTP=yes. |
| `oomd-synthex.conf` | systemd-oomd memory pressure policy. |

## `configs/live/` — the live session

| File | Purpose |
|---|---|
| `live-setup.sh` | On-boot live setup hook. |
| `install-synthex.desktop` | "Install SynthOS" desktop entry. |
| `synthex-live-setup.service` | systemd unit that runs live-setup.sh on live. |

## `configs/locale/`

| File | Purpose |
|---|---|
| `locale.conf` | `LANG=en_US.UTF-8`. |
| `vconsole.conf` | `FONT=lat0-16`. |
| `synthex-locale-gen` | Locale generation helper. |

## `configs/modprobe/`

| File | Purpose |
|---|---|
| `synthex-security.conf` | Modprobe security blacklists. |
| `synthex-thinkpad.conf` | ThinkPad module options. |
| `synthex-audio.conf` | Audio module options. |
| (`synthex-nvidia.conf`, others) | GPU module options (built by `synthex-safety`). |

## `configs/networkmanager/`

| File | Purpose |
|---|---|
| `nm-synthex.conf` | NetworkManager options (wifi, IPv6). |

## `configs/plasma/`

| File | Purpose |
|---|---|
| `kde-defaults.conf` | KDE Plasma defaults. |
| `synthex-oobe-defaults.conf` | OOBE (first-run) defaults. |

## `configs/plymouth/`

| File | Purpose |
|---|---|
| `plymouthd-synthex.conf` | Ply Tower config. |
| `synthex-plymouth.conf` | Splash theme reference. |

## `configs/polkit/`

| File | Purpose |
|---|---|
| `49-synthex-nopasswd.rules` | Polkit rule (sudoers-nopass-like for user). |

## `configs/sddm/`

| File | Purpose |
|---|---|
| `sddm-synthex.conf` | `/etc/sddm.conf.d/synthex.conf` (`Current=synthex`). |
| `sddm-synthex-theme.conf` | SDDM theme env. |

## `configs/secureboot/`

| File | Purpose |
|---|---|
| `synthex-shim.conf` | Secure Boot / shim config hint. |

## `configs/snapper/`

| File | Purpose |
|---|---|
| `snapper-root.conf` | Snapper root config (`TIMELINE_CREATE=yes` etc.). |

## `configs/sudoers/`

| File | Purpose |
|---|---|
| `synthex-sudoers` | `/etc/sudoers.d/synthex` (`%wheel ALL=(ALL) ALL`). |

## `configs/terminal/`

| File | Purpose |
|---|---|
| `synthex-rice .*` | Terminal "rice" (prompt/ls config). |
| (`kitty.conf`, `fish/30-synthex.fish`, `starship.toml`, `fastfetch/config.jsonc`) | the Nova shell stack (installed to `/etc/skel`). |

## `configs/vpn/`

| File | Purpose |
|---|---|
| `synthex-vpn-helper` | VPN helper CLI. |
| `wireguard-client.conf` | WireGuard client example. |

## `configs/workspace-presets.json`

Top-level `configs/workspace-presets.json` — creator/gamer presets for
work/$HOME layouts.

---

## How these are installed

They are **not runtime files in the repo**; they are **sources** that the
specs (esp. `synthex-aios`, `synthex-safety`, `synthex-system-config`,
`synthex-grub-theme`) copy into the buildroot. Mapping:

```
configs/performance/*      → synthex-aios.spec
configs/safety…            → synthex-safety.spec
configs/* (grub, plymouth, sddm, journald, modprobe, …) → the matching
                            synthex-*config / theme specs
configs/aios/, upstream/   → synthex-aios.spec
```

Regenerate the monorepo tarball after touching any `configs/*/	`
file so it lands in `synthex-repo-<version>.tar.gz`:

```bash
build/scripts/make-srctars.sh 2026.10
```

## Validation

- All files under `configs/` are picked up by `make-srctars.sh`.
- `verify.sh` only gates the `configs/aios|upstream|performance` runtime
  behavior.
- Install intent is checked per spec (`%files` must mirror `%install`).