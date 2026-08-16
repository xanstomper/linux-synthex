# Config Files Reference

Every configuration file that the SynthOS distribution ships or generates,
with its path (in the installed image), its format, and its contents.

These are the **runtime** config files — they ship in the RPMs and are
read by the system at runtime. The **build-time** ones (`.spec`,
kickstarts) are documented in `docs/PACKAGING.md` and `docs/ISO.md`.
The **source-level** files in `configs/` are documented in
`docs/REFERENCE.md`.

---

## Systemd unit configs (the AIOS umbrella RPM)

Installed under `/usr/lib/systemd/system/`.

### `synthex-defaults.service`

```
[Unit]
Description=SynthOS first-boot defaults (predictive, snapshots, zram)
After=local-fs.target
ConditionPathExists=/etc/synthex/live-mode
Before=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/synthex-defaults enable-all
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Runs once on first boot (when `/etc/synthex/live-mode` exists) to enable
the differentiator units. See `docs/AIOS.md#synthex-defaults`.

### `synthex-zram.service`

```
[Unit]
Description=SynthOS zram swap (low-pressure RAM compression)
After=local-fs.target
Before=swap.target
ConditionVirtualization=!container

[Service]
Type=oneshot
ExecStart=/usr/lib/synthex/zram-setup

[Install]
WantedBy=swap.target
```

Calls the zram setup script (`configs/performance/zram-setup`, installed
as `/usr/lib/synthex/zram-setup`).

### `synthex-sync-updates.service` + `synthex-sync-updates.timer`

```
[Unit]
Description=SynthOS upstream update sync (repackage hook)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/synthex-update-sync stage
Nice=10

[Install]
WantedBy=multi-user.target
```

Timer:

```
[Unit]
Description=Check upstream (Fedora/Nobara) package updates for SynthOS

[Timer]
OnCalendar=*-*-* 04:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Daily at 04:00, runs `synthex-update-sync stage`. See
`docs/UPDATER.md`.

---

## Sysctl — `/etc/sysctl.d/00-synthex-vm.conf`

```
vm.swappiness=10
vm.vfs_cache_pressure=160
vm.dirty_ratio=15
vm.dirty_background_ratio=5
vm.overcommit_memory=1
kernel.nmi_watchdog=0
kernel.sched_autogroup_enabled=0
vm.max_map_count=2097152
```

Applied at boot by `systemd-sysctl`. See `docs/PERFORMANCE.md`.

---

## Sysctl — `/etc/sysctl.d/00-synthex-network.conf`

```
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.core.netdev_max_backlog=16384
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 655360 16777216
net.ipv4.tcp_adv_win_scale=1
```

---

## `/etc/gamemode.ini`

Ke the default Feral `gamemode` config (see `docs/PERFORMANCE.md#gamemodeini`).

```
gamemode=quiet
[general]
renice=10
desiredgov=performance
softrealtime=auto
reap_children=yes
[gpu]
apply_gpu_optimisations=accept-responsibility=yes
gpu_device=0
nv_powermizer_change=1
[cpu]
park_cores=no
enable_cgroups=no
```

Only active while a game holds the gamemode token. Reverted on exit.

---

## `/etc/snapper/configs/root`

The starter btrfs snapshot config. Created by the AIOS umbrella RPM and
by `configs/aios/install.sh`:

```
SUBVOLUME="/"
FSTYPE=btrfs
TIMELINE_CREATE="yes"
NUMBER_CLEANUP="yes"
TIMELINE_LIMIT_DAILY="5"
TIMELINE_LIMIT_WEEKLY="0"
```

Used by `snapper -c root` for timeline + rollback. Only relevant on btrfs.

---

## `/etc/synthex/upstream/synth-pkgs.conf`

The tracked-packages + repos config for the upstream tracker. Owned by
the `synthex-aios` RPM; the tracker loads it (comment-tolerant JSON):
see `docs/UPDATER.md` for the schema and the shipped default.

---

## `/etc/synthex/` marker — `/etc/synthex/live-mode`

Created by the kickstart `%post` (`touch /etc/synthex/live-mode`) so
`synthex-defaults` knows whether the machine is a **live** session
(and thus whether to run its first-boot fan of enabling units).

---

## `/etc/synthex/synthex-default.governor` (optional, runtime)

Written by `synthex-gov` (`/run/synthex/governor`) as a marker so a
restore-on-boot unit can reapply `performance` if the user selected it.
Not shipped by default.

---

## Sysconfig / udev — `configs/performance/`, `configs/safety`

The udev rules and driver configs are shipped by `synthex-safety` and
`configs/performance`:

| Path | Owner | Purpose |
|---|---|---|
| `/usr/libexec/sent/synthex/gpu-setup` | `synthex-gpu-setupd` | GPU vendor config (`/run/synthex/gpu-driver.conf`) |
| `/usr/lib/udev/rules.d/69-synthex-firmware.rules` | `synthex-safety` | firmware udev |
| `/usr/lib/udev/rules.d/70-synthex-controllers.rules` | `synthex-safety` | controller udev |
| `/usr/lib/udev/rules.d/71-synthex-rgb.rules` | `synthex-safety` | RGB udev |
| `/usr/lib/udev/rules.d/72-synthex-handheld,rules` | `synthex-safety` | handheld udev |

---

## `/usr/share/synthex/` — data shipped by the umbrella

| Path | Contents |
|---|---|
| `/usr/share/synthex/aios/post-install.sh` | `%post` snippet |
| `/usr/share/synthex/performance/zram-setup` | executable zram script |
| `/usr/share/synthex/performance/synthex-game-session` | → `/usr/bin` |

---

## Runtime state files (not shipped — generated)

| Path | Who writes | Purpose |
|---|---|---|
| `/var/lib/synthex/update-state.json` | `synthex-update-sync apply` | last queue + snapshot info |
| `/var/cache/synthex/updates/<pkg>/candidate.json` | `synthex-update-sync stage` | latest candidate |
| `/var/lib/synthex/repo/queue.jsonl` | `synthex-update-sync apply` | the build queue for the container |
| `/run/synthex/governor` | `synthex-gov` | last governor choice |
| `/run/synthex/gpu-driver.conf` | `synthex-gpu-setupd` | detected GPU vendor/driver |

These are **runtime** state; they persist across runs where appropriate
(`update-state.json`, `queue.jsonl`) and are lost on reboot where a tmp
(`/run`) location is used.

---

## Validation

- Sysctl files: parseable by `systemd-sysctl`.
- `synth-pkgs.conf`: comment-tolerant JSON (`verify.sh` asserts this).
- `.service`/`.timer` files: parseable by systemd.
- `gamemode.ini`: parseable by `gamemode`.
- udev rules: parseable by `udevadm`.

Every one of these is **reversible**: remove the file (or the package)
and the relevant system behavior reverts to the Fedora default.