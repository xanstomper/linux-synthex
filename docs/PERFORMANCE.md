# Performance Layer — Safe Gaming & Desktop Tuning

`configs/performance/` contains the safe performance defaults. Everything
is **reversible**: changes go into `/etc/sysctl.d/`, a single
`governor` switcher, and unit files that can be enabled/disabled per
user. Nothing here overclocks, modifies the BIOS, or disables
security mitigations.

This document explains **what each file does** and **why it’s safe**.

## Files at a glance

| File | Installed as | Effect |
|---|---|---|
| `sysctl.d/00-synthex-vm.conf` | `/etc/sysctl.d/00-synthex-vm.conf` | VM, I/O scheduler, kernel tuning |
| `sysctl.d/00-synthex-network.conf` | `/etc/sysctl.d/00-synthex-network.conf` | TCP socket buffers, queueing |
| `synthex-gov` | `/usr/bin/synthex-gov` | CLI: `synthex-gov max|balanced` |
| `zram-setup` | `/usr/share/synthex/performance/zram-setup` | Called by the zram service |
| `zram.service` | `/usr/lib/systemd/system/synthex-zram.service` | Enables zram on boot |
| `gamemode.ini` | `/etc/gamemode.ini` | gamemode CPU/GPU tuning when a game holds the token |
| `synthex-game-session` | `/usr/bin/synthex-game-session` | Wrapper that runs Steam/games under gamescope |
| `grub-synthex.cmdline` | documentation only | Suggested GRUB cmdline additions |

## `sysctl.d/00-synthex-vm.conf`

```
vm.swappiness=10                 # prefer RAM over disk (good default for desktop with zram)
vm.vfs_cache_pressure=160        # keep dentries/inodes hot
vm.dirty_ratio=15                # background flush at 5%, full at 15%
vm.dirty_background_ratio=5
vm.overcommit_memory=1           # heuristic overcommit (safe with 8+ GiB)
kernel.nmi_watchdog=0            # disable NMI watchdog (small CPU savings on desktop)
kernel.sched_autogroup_enabled=0 # better interactivity under load
vm.max_map_count=2097152         # raise for games (SteamVR, Chromium)
```

**Why safe**: every value is a **common desktop recommendation** and well
within Linux’s normal operating range. `overcommit_memory=1` is the
default on most distros. `nmi_watchdog=0` saves a small amount of CPU
that would otherwise be used for hardware-watchdog polling (useful for
servers, marginal for desktops).

## `sysctl.d/00-synthex-network.conf`

```
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.core.netdev_max_backlog=16384
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 655360 16777216
net.ipv4.tcp_adv_win_scale=1
```

**Why safe**: increases socket buffers so big TCP transfers (game
downloads, NFS) don’t stall. `tcp_adv_win_scale=1` is the modern
default. No flags changed.

## `synthex-gov`

```bash
synthex-gov max       # sets /sys/.../scaling_governor = performance
synthex-gov balanced # sets it to schedutil (default)
```

Writes to `/sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor`.
Idempotent. If the user has no `cpufreq` driver, the script silently
does nothing. Reversible: `synthex-gov balanced` returns to defaults.

**Important**: we ship **schedutil** as the system default. `performance`
is opt-in. We do not enable `performance` automatically — on laptops
that drains battery and increases heat.

## `zram.service` + `zram-setup`

A small systemd oneshot that, on boot:

1. `modprobe zram`
2. Picks lz4 compression (fast, modern).
3. Sizes zram0 to **half of RAM, capped at 8 GiB**.
4. Creates `/dev/zram0` swap with priority 100.

**Why safe**: zram is compressed RAM, not disk. It does not destroy
disk swap (it adds to it). On systems with no `modprobe zram` available,
the service silently exits 0.

The full disk swap (if any) is preserved as fallback.

## `gamemode.ini`

The default config for Feral’s `gamemode` (the `gamemode` package).

```
[general]
renice=10              # de-prioritize the game process slightly
desiredgov=performance # ask CPU governor to switch when game holds the token
softrealtime=auto      # SCHED_RESET_ON_FORK
reap_children=yes      # clean up zombies

[gpu]
apply_gpu_optimisations=accept-responsibility=yes
nv_powermizer_change=1 # NVIDIA power-mizer: prefer max performance

[cpu]
park_cores=no          # don't park cores (keep all cores available)
enable_cgroups=no
```

**Why safe**: gamemode only acts while a game holds its token. As soon
as the game exits, gamemode reverses every change.

## `synthex-game-session`

```bash
synthex-game-session steam
```

A one-liner:

```bash
exec gamescope --adaptive-sync --rt -f -- "$@"
```

What this gives you:

- `--adaptive-sync` enables VRR on supported monitors.
- `--rt` reduces compositor latency (game stream stays close to the
  frame presentation).
- `-f` forces fullscreen so the game owns the output.

**Why safe**: `gamescope` is just another Wayland compositor; it does
not modify drivers or hardware. Exiting `gamescope` returns you to your
desktop session.

## Suggested GRUB cmdline (documentation only)

`grub-synthex.cmdline` is a comment file showing the **append-only**
defaults that pair well with the layer:

```
quiet splash loglevel=rate_limit
transparent_hugepage=never
# IMPORTANT: mitigations intentionally left ENABLED (no npti/nosmep)
```

We do **not** append this to GRUB automatically. `transparent_hugepage=never`
is a desktop recommendation (THP sometimes hurts gaming latency). The
mitigations line is a comment to remind you **not to disable them**.

## Safety guarantees

1. **Nothing here is one-way.** Every change lives in `/etc/sysctl.d/`,
   a unit file, or `/sys`. Edit the unit, `systemctl disable`, or
   `synthex-gov balanced`.
2. **No overclock / no XMP / no vBIOS flash.**
3. **ZRAM, not zswap.** Compressed RAM swap, disk swap preserved.
4. **Governor default is `schedutil`, not `performance`.** Battery / thermals
   unaffected out of the box.
5. **NVIDIA via DKMS / rpmfusion only.** Never the `.run` installer.
6. **Mitigations left enabled** (Spectre, Meltdown, etc).

## Extending

If you want to add a new default (e.g. a sysctl value):

1. Create `configs/performance/sysctl.d/99-synthex-<feature>.conf`.
2. Append an entry in `configs/performance/install.sh` to `cp` it.
3. Add it to the `synthex-aios.spec` `%install` and `%files`.
4. Rebuild + re-sync the repo.
5. Re-run `configs/tests/verify.sh`.

The verify harness doesn’t currently assert sysctl values, but the
`install.sh` round-trip is validated implicitly by the synthex-aios RPM
being installed.
