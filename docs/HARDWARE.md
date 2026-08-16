# Hardware & Driver Matrix

This is the driver/packaging matrix for what SynthOS does on different
hardware — CPU, GPU, audio, wireless, controllers. It’s about **which
packages/drivers the environment loads** and which repo they come from.
Everything is reversible: changing the driver (or the GPU mode) never
flashes the BIOS / vBIOS, never overclocks, and never disables
mitigations.

## CPU

| CPU family | Driver mechanism (kernel pstate) | Enabled by default? |
|---|---|---|
| Intel (SandyBridge+) | `intel_pstate` (active) | yes |
| AMD (Zen+) | `amd-pstate` + CPPC | yes |
| Both | fallback governor = `schedutil` | yes |

`amd-pstate` / `intel_pstate` ships in the **Fedora kernel** (vendored)
as `CONFIG_X86_AMD_PSTATE_CPPC=y` / `CONFIG_X86_INTEL_PSTATE=y`.

Governor is **`schedutil`** by default (safe). User can opt-in to
`performance` with `synthex-gov max`. We never force `performance`
system-wide.

## GPU

### Driver choice by vendor

| Vendor | Mesa open driver | Vulkan ICD | Notes |
|---|---|---|---|
| AMD | `mesa-dri-drivers` | `vulkan-radeon` | default; prime recommended |
| Intel | `mesa-dri-drivers` | `vulkan-intel` | default |
| NVIDIA | `nvidia-driver` (DKMS) | `vulkan` (from nvidia) | DKMS only; never `.run` script |
| Older (pre-2010) own Radeon | `radeonkms` | Mesa | Mesa’s older branch |

The default is always **Mesa for AMD/Intel**. NVIDIA machines get
`nvidia-driver` through the DKMS/rpmfusion path (see
`docs/PACKAGING.md#nvidia-dkms` and `docs/PERFORMANCE.md`).

### GPU switching / power modes

- `synthex-gpu-switch` toggles between `integrated` (low power, save
  battery) and `discrete` (full power). It only writes to
  `pcie_address_busdev_...`/`amdgpu`/`nvidia` knobs in `/sys` — no vBIOS.
- For hybrid laptops (Intel iGPU + discrete), the recommended default is
  `integrated` for battery and `discrete` for gaming.

### `synthex-gpu-setupd`

At boot, `synthex-gpu-setupd.service`:

1. Detects the primary GPU vendor (`/sys/class/drm/…/uevent`).
2. Loads the matching kernel modules (`amdgpu`, `i915`, `nouveau` /
   `nvidia`).
3. Writes a hint to `/run/synthex/gpu-driver.conf` (so the persona
   layer knows which driver to prefer).
4. Ships the correct Vulkan ICD down to `synthex-gpu-setup` (if the driver
   was chosen).

Nothing here changes BIOS/firmware.

---

## Audio

- **PipeWire** is the audio server (the kickstart installs
  `pipewire`, `pipewire-pulseaudio`, `wireplumber`, `pavucontrol`).
- **No vendor binary audio driver needed**; PipeWire drives everything.

---

## Wireless / Ethernet

- `NetworkManager` (`NetworkManager`, `NetworkManager-wifi`,
  `NetworkManager-tui`) is default.
- `iwd`/`wpa_supplicant` both can be used as backends.
- `bluetooth` stacks: `bluez`, `blueman`.

---

## Controllers / input

- Standard: `synthex-input-remapper` for gamepads.
- `steam-devices` package from RPM Fusion for Steam Controller/Deck.
- udev rules are installed by the `synthex-safety` spec
  (`udev/69-synthex-firmware.rules`, `70-synthex-*-rules`, `72`).

---

## Firmware / microcode

- `fwupd` for firmware updates (LVFS).
- `mirror` microcode (`intel-microcode` / `amd-microcode`) — updated via
  the normal package path, not flashed here.

---

## Audio

PipeWire handles PulseAudio/JACK/Wayland audio. No extra kernel driver
is needed on modern hardware (Realtek `snd-hda-intel` is built-in).

---

## Recognized driver matrix (packages we may install)

| Product | Driver | Package | Source |
|---|---|---|---|
| AMD Vulkan | (mesa) | `vulkan-radeon` | Fedora |
| Intel Vulkan | (mesa) | `vulkan-intel` | Fedora |
| NVIDIA proprietary | proprietary | `nvidia-driver` (DKMS) | rpmfusion-nonfree |
| NVIDIA open (kmod-open) | nvidia-open | `nvidia-driver` (kmod-open variants) | rpmfusion |
| Gamescope compat | (mesa) | `gamescope` | Fedora |
| gamepad mapper | `synthex-input-remapper` | `synthex-input-remapper` | local repo |
| Steam Patch | (mesa) | `steam-devices` | rpmfusion |
| Valve / Steam deck | udev rules | `steam-devices` | Fedora/rpmfusion |

---

## The `synthex install` driver presets (map to the above)

```bash
synthex install nvidia   # nvidia-driver + nvidia-modprobe
synthex install amd      # mesa-vulkan-drivers vulkan-radeon libva
synthex install intel    # mesa-vulkan-drivers vulkan-intel intel-media-driver
synthex install mesa     # mesa-vulkan-drivers mesa-va-drivers
synthex install steam    # steam
synthex install codecs   # ffmpeg gstreamer1-plugins-bad-free-extras
```

Each is **snapshot-guarded**: `synthex install --yes` snapshots first
and rolls back on failure (see `docs/AIOS.md#synthex-install`).

---

## Verifying on a machine

```bash
synthex-doctor                       # GPU/vulkan/ICD section
lspci -nnk | grep -iA3 vga          # actual GPU
vulkaninfo --summary | grep -i gpuName
pid upower -i /org/freedesktop/UPower   # battery (optional)
pid
# MD-specific:
sudo dkms status                       # driver modules
```

---

## Anti-brick policy (repeated for emphasis)

- No `BIOS`/`UEFI` flashing in SynthOS. `fwupd` is optional and user-initiated.
- No `XMP`/`EXPO`/OC from the OS.
- NVIDIA driver only via the DKMS/rpmfusion repo (the `.run` NVIDIA
  installer is **never** run because it can break boot).
- All driver switches in `synthex-gpu-switch` and `synthex-gpu-setupd`
  write only to `sysfs`. They never touch firmware.
- `synthex-gov balanced` restores `schedutil` (safe default).