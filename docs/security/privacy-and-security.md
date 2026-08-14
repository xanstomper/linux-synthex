# SynthOS Security & Privacy Guide

> **Promise:** SynthOS collects **no** telemetry, analytics, crash reports, or
> usage data. This document explains how that is enforced and where the
> (opt-in, off-by-default) network-dependent features live.

---

## 1. Telemetry & analytics — none, by design

SynthOS ships **no** analytics or telemetry SDK. There is no Sentry, Amplitude,
Mixpanel, PostHog, Glean, or equivalent anywhere in the image, and there is no
configuration knob to "turn telemetry on" because there is nothing to turn on.

What we *do* disable proactively (so upstream components cannot phone home):

| Component | Disabled via |
|-----------|--------------|
| KDE Activity Manager telemetry | `kactivitymanagerdrc → telemetryEnabled = false` |
| KDE global feedback level | `kdeglobals → FeedbackLevel = 0` |
| Discover (Plasma Software Center) feedback | `discoverrc → FeedbackLevel = 0` |
| Baloo file indexer (privacy + power) | `baloofilerc → Indexing-Enabled = false` |
| KRunner web-search suggestions | `krunnerrc → Plugins.* Enabled = false` |
| SynthOS AI agent telemetry flag | `settings → telemetry = False` |

See [`desktop/plasma/synthex-desktop-config.sh`](../../desktop/plasma/synthex-desktop-config.sh)
for the authoritative list.

---

## 2. Network-dependent features (all OFF by default)

A few features *can* make outbound requests, purely to deliver their function.
Every one of them is **opt-in** and **off by default**. The single source of
truth is `/etc/synthex/privacy.conf`:

```ini
weather_fetch       = false   # temporal daemon: live weather from wttr.in
integration_engine  = false   # maintainer tool: polls upstream release APIs
telemetry           = false   # hard-off, not configurable
```

### `synthex-temporal` (ambient / time-aware theming)
Drives day/night wallpaper rotation, Plasma color-scheme switching, and ambient
audio. **Default mode is fully offline:** it derives a day/night + season
heuristic from the local clock and makes **zero** network requests. To opt into
live weather (which contacts `wttr.in`), set `weather_fetch = true` or
`SYNTHEX_TEMPORAL_WEATHER=1`.

### `synthex-integration-engine` (upstream change monitor)
A **maintainer / contributor** tool that polls GitHub, kernel.org, and
archlinux.org release APIs to surface candidate upstream changes. It is
**disabled on the daemon path by default** — running it requires
`SYNTHEX_INTEGRATION_ENGINE=1`. End users never need it.

### Legitimate network use (not telemetry)
Package management (`dnf`, `flatpak`), Flathub/RPM Fusion repo metadata, the AI
agent (user-chosen provider), and NTP (`chronyd`) all make outbound requests in
the normal course of their function. These are **your** actions, not tracking.

---

## 3. Hardening posture

- **SELinux:** enforcing by default.
- **Firewall:** `firewalld` enabled, `public` zone, SSH off by default.
- **CPU mitigations:** ON (`mitigations=auto`) on all editions. The gaming
  session may opt into `mitigations=off` *per-session* via `synthex-gaming-mode`,
  but the base image never ships with them disabled.
- **Encryption:** LUKS2 (Argon2id) supported for full-disk encryption.
- **DNS:** DoH-capable; NextDNS profile optional.
- **systemd services:** every `.service` ships with hardening directives
  (`NoNewPrivileges`, `ProtectSystem`, `PrivateTmp`, `ProtectKernelTunables`,
  `ProtectControlGroups`, `SystemCallArchitectures`).
- **Live USB user:** `liveuser`, password **locked** — reachable only via SDDM
  autologin on the live USB, never on an installed system.

---

## 4. Verifying it yourself

```bash
# Confirm the privacy policy on an installed system
cat /etc/synthex/privacy.conf

# Confirm no analytics binaries are installed
rpm -qa | grep -iE 'sentry|amplitude|mixpanel|posthog|glean' || echo "clean"

# Watch for any unexpected outbound connections
ss -tnp state established
```

If you find anything that phones home unexpectedly, that is a bug — please open
an issue at <https://github.com/synthex-linux/issues>.
