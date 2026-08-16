# Security

SynthOS takes a layered approach to security. The intent is: **harden
the default, give the user simple toggles, never brick the box.**

## What is in this repo (security-relevant)

| Component | Role |
|---|---|
| `synthex-aios` (umbrella RPM) | Installs the AI-OS layer, the perf defaults, the systemd units, and a `synthex-defaults.service` first-boot unit. |
| `synthex-safety` | Stub: pre-install safety policy (protected-packages list, auto-snapshot before updates, controller/RGB udev rules, zram tuning). |
| `synthex-firewall` (in `synthex-safety` spec) | nftables/firewalld preset, enabled by default. |
| `synthex-security-dashboard` | Stub: security posture dashboard (GTK4/libadwaita app, DBus gatherer). |
| `synthex-system-config` | Btrfs-snapshot config (`NUMBER_CLEANUP`), journald tuning, sysctl hardening. |
| `synthex-privatelabel` / `synthex-privacy` | Stub: `synthex privacy on|off` switch (planned). |

## What is **not** in this repo (and why)

- **A custom hardening fork of any daemon.** Boring is better than
  clever for security — we ship Fedora defaults, tuned.
- **Mandatory sandboxing of every app.** Flatpak+Flathub is already
  wired in the kickstart; we don’t add another layer.
- **Anti-virus / EDR.** Out of scope for the AI-OS.
- **Disabling Spectre/Meltdown mitigations.** We ship with them ON.
  `docs/PERFORMANCE.md` is explicit about this.

## The default security posture

After a clean install + `synthex-defaults enable-all`:

| Setting | Value | Source |
|---|---|---|
| Firewall (firewalld) | default zone active | `synthex-safety` |
| Snapper timeline snapshots | daily + weekly | `synthex-defaults` |
| Boot health check | `synthex-safety-check.sh` (cron-like timer) | `synthex-safety` |
| Protected-packages list | `/etc/synthex/protected-packages.conf` | `synthex-safety` |
| ZRAM swap | enabled | `synthex-zram.service` |
| Journald | 500M cap, persistent | `synthex-system-config` |
| Spectre/Meltdown mitigations | enabled | kernel cmdline (no `nopti`) |
| NVIDIA driver | DKMS via rpmfusion only | `synthex-nvidia-installer` |
| Auto-update + snapshot-before | yes (via `synthex-update-sync apply`) | `synthex-aios` |

## The `synthex privacy` switch (planned)

A single command that toggles:

- Disable telemetry endpoints on the AI daemons (via the firewall).
- Kill the DBus security gatherer (`synthex-security-gatherer`).
- Block outbound for `synthex-hermes`, `synthex-brain` (if they phone home).

Not implemented yet. Tracked under `synthex-aios.spec` TODO.

## Verifying your security posture

```bash
synthex-doctor              # one-shot report (see docs/AIOS.md)
synthex privacy            # (planned) toggle
systemctl status synthex-defaults
firewall-cmd --list-all
snapper -c root list
```

## Failure modes

- **No btrfs** → no snapshots → no rollback. `synthex-update-sync apply`
  and `synthex install` will gracefully warn and skip the snapshot
  step. Install btrfs (Fedora’s default) to enable rollback.
- **No `synthex-snapshot`** → the orchestrators still work, they just
  can’t roll back. Install the `synthex-snapshot` package (or just put
  any binary at `/usr/sbin/synthex-snapshot` that understands
  `create <desc>` / `rollback`).
- **No snapper** → `synthex-defaults` skips timeline snapshots.

## See also

- `docs/AIOS.md` — the assistant console + persona + doctor.
- `docs/PERFORMANCE.md` — what *isn’t* changed (mitigations stay on,
  governor default is `schedutil`).
- `docs/UPDATER.md` — auto-snapshot before every update.
- `docs/EXTENDING.md` — how to add a new security feature.
