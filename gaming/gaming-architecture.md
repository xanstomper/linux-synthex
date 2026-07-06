# Solus Linux Gaming Platform Architecture

## Gaming Vision and Philosophy

Solus Gaming Platform aims to deliver a **zero-friction, high-performance gaming experience** on Linux by integrating the entire gaming software stack — from the kernel to the compositor to the launcher — into a cohesive, well-tested ecosystem.

### Core Tenets

1. **Performance First** — Every component is tuned for minimal overhead, low latency, and maximum frame throughput. No bloat, no unnecessary abstraction layers.
2. **Out-of-the-Box** — Install the gaming meta-package, reboot, and play. Automatic GPU detection, driver installation, and Proton configuration.
3. **Freedom to Choose** — AMD (open-source), NVIDIA (open-source Nouveau or proprietary), and Intel are all first-class citizens. The platform detects your hardware and picks the optimal stack.
4. **Upstream Collaboration** — Patches and improvements flow back to Mesa, Wine, Proton, Gamescope, and the Linux kernel. Solus doesn't fork; it integrates.
5. **User Sovereignty** — Every optimization can be disabled. Per-game profiles let you override global settings. The Gaming Control Center puts all knobs in one GUI.

---

## GPU Stack

### AMD (Radeon) — Open-Source First

| Component | Stack | Notes |
|-----------|-------|-------|
| Kernel driver | `amdgpu` (in-tree) | Included in Linux kernel ≥5.7, backported for LTS |
| Firmware | `linux-firmware` (amdgpu/) | Signed microcode for all GCN/RDNA GPUs |
| Mesa | Latest Mesa 3D (radeonsi/RADV) | OpenGL and Vulkan drivers |
| Vulkan driver | `radv` (RADV) | Community-developed, feature-complete Vulkan |
| OpenGL driver | `radeonsi` (Gallium3D) | State-of-the-art OpenGL 4.6 |
| Video encode/decode | `amdgpu` VCN | VA-API / VDPAU via Mesa |

**Supported GPUs:** GCN 1.0 (HD 7000) through RDNA 4 (RX 9000 series)

### NVIDIA — Hybrid Choice (Nouveau Open-Source / Proprietary)

**Option A: Nouveau (Open-Source)**

| Component | Stack | Notes |
|-----------|-------|-------|
| Kernel driver | `nouveau` (in-tree) | Display, modesetting, basic 3D |
| Mesa | `nouveau` (Gallium3D) | OpenGL via nvc0, Vulkan via NVK |
| Vulkan driver | `nvk` (NVK) | Nouveau Vulkan — improving rapidly |
| Limitations | No reclocking (all GPUs), no GSP on some | Performance ~50-70% of proprietary |

**Option B: Proprietary (nvidia.ko)**

| Component | Stack | Notes |
|-----------|-------|-------|
| Kernel driver | `nvidia.ko`, `nvidia-drm.ko` | DKMS modules, rebuilt on kernel update |
| OpenGL | NVIDIA GLX/EGL libraries | Drop-in Mesa replacement |
| Vulkan | `nvidia_vulkan` (Vulkan ICD) | Full Vulkan 1.3 support |
| Wayland | `nvidia-drm` modesetting + EGLDevice | Requires `nvidia-drm.modeset=1` |
| GSP firmware | Included in driver package | Supports firmware-loaded GSP on Turing+ |

**Driver Switcher:** The `solus-gpu-drivers` package ships a `gpu-driver-manager` that can switch between Nouveau and proprietary at boot via kernel cmdline + initramfs rebuild.

### Intel — Open-Source Native

| Component | Stack | Notes |
|-----------|-------|-------|
| Kernel driver | `i915` (in-tree) | Full modesetting, GEM, scheduler |
| Firmware | `linux-firmware` (i915/) | GuC/HuC microcode |
| Mesa | `iris` (Gallium3D) | OpenGL 4.6, Vulkan 1.3 |
| Vulkan driver | `anv` (ANV) | Intel's official open-source Vulkan |
| Compute | `intel-compute-runtime` | Level Zero, OpenCL via Neo |
| Video encode/decode | `i915` media engine | VA-API via `intel-media-driver` |

---

## Graphics Stack

### Mesa 3D (24.x+)

The core of the graphics stack on Solus. Built with:

```
-Dgallium-drivers=radeonsi,r600,nouveau,iris,zink,virgl,panfrost
-Dvulkan-drivers=amd,intel,intel_hasvk,swrast,virtio,nouveau
-Dvideo-codecs=all
-Degl=enabled
-Dgbm=enabled
-Dgles1=enabled
-Dgles2=enabled
-Dosmesa=classic
-Dtools=glslang
```

### Vulkan Layer Stack

- **Vulkan Loader** (`libvulkan.so`) — ICD discovery and dispatch
- **Vulkan Validation Layers** (`VK_LAYER_KHRONOS_validation`) — Debug builds only
- **Vulkan Memory Allocator** — For games/engines using VMA

### VKD3D-Proton

DirectX 12 → Vulkan translation. Solus ships `vkd3d-proton` built from the Proton fork:

- Feature level 12_1+ support
- DXR (Raytracing) 1.0/1.1 via Vulkan ray tracing extensions
- Work graphs (DX12 Ultimate)
- Mesh shaders
- Sampler feedback

### DXVK

DirectX 9/10/11 → Vulkan translation:

- DXBC → SPIR-V compilation
- State cache for reduced stutter
- Async pipeline compilation (optional, via `DXVK_ASYNC=1`)
- HDR support via Vulkan HDR extensions
- DXVK_NVAPI for DLSS/Reflex on NVIDIA

---

## Proton Architecture

Solus ships **Proton GE** (GloriousEggroll's Proton builds) as the default, alongside upstream Valve Proton.

### Proton GE vs Upstream Proton

| Feature | Upstream Proton | Proton GE |
|---------|----------------|-----------|
| Wine patches | Valve-maintained | Upstream + community |
| Media Foundation | Basic | Full (MF-Media) |
| FSR 1.0/2.0 | FSR 1.0 | FSR 1.0 + 2.0 |
| VKD3D | Valve fork | Latest Proton fork |
| DXVK | Valve fork | Latest upstream + patches |
| NVAPI/DLSS | Supported | Supported |
| Fsync | Supported | Supported |
| Futex2 | Supported | Supported |
| Raw Mouse Input | Yes | Yes + raw mouse toggle |
| Game-specific fixes | Common titles | Extended compatibility DB |

### Custom Build Pipeline

See `proton/proton-ge-build.sh` for the full automated build from source.

```
Sources:
  - https://github.com/ValveSoftware/Proton
  - https://github.com/GloriousEggroll/proton-wine
  - https://github.com/doitsujin/dxvk
  - https://github.com/HansKristian-Work/vkd3d-proton
  - https://github.com/Kise1e/wine-proton (MF-Media patches)

Build outputs:
  - proton-ge-custom.tar.xz (~300MB compressed)
  - Installed to ~/.steam/root/compatibilitytools.d/
```

---

## Wine Integration

Solus Gaming provides Wine 9.x+ with the following patchsets:

- **Staging patches** — Full Wine-Staging
- **Wayland driver** — Native Wayland support (no XWayland needed)
- **HDR patches** — HDR output via Wayland color management protocol
- **Fsync** — Fast synchronization primitives (kernel futex)
- **Futex2** — Updated futex2 syscall interface
- **Vulkan support** — WineD3D → Vulkan via VKD3D/Fossilize
- **ARM64EC** — x64 emulation on ARM via FEX

### Wine Binary Structure

```
/usr/lib/wine/
├── wine/
│   ├── wine64-preloader
│   ├── wine64
│   ├── wineserver
│   └── winebuild/
├── wine-wayland.so
├── wine-vulkan.so
├── libwine.so.1
└── dlls/
    ├── win32/
    └── win64/
```

---

## Steam Integration

### Native Steam Client

- Steam installed via Solus repository (`steam` package) or Flatpak
- Runtime: `steam-runtime` (Valve's container) or Solus-native runtime
- Steam Play enabled by default
- Proton GE auto-detected in `compatibilitytools.d/`

### Steam Optimization (`steam-optimizations.sh`)

- **Preload Steam** via `preload` daemon for faster launch
- **CPU governor** set to `performance` while Steam is running
- **schedtool** — Steam and game processes get `SCHED_ISO` (SCHED_ISO-like via SCHED_RR with low priority) or `SCHED_BATCH`
- **Inotify limits** bumped to 524288 for shader compilation watchers
- **Vm.max_map_count** set to 16777216 for memory-mapped shader caches
- **Shader cache** pre-warmed and updated in background via `steam-shader-cache-manager`
- **TCP/443 optimization** — `tcp_congestion_control=bbr` + `net.core.default_qdisc=fq` for update downloads
- **Disable Steam overlay** per-game (optional, reduces input latency)
- **nanokms** — Kernel modeset latency reduction

### Steam Wrapper (`steam-wrapper.sh`)

```
steam-wrapper [--gamescope] [--gamemode] [--hdr] [--fsr] [game]
```

A launch wrapper that optionally:
1. Launches Steam (or a Steam game) inside **Gamescope** (micro-compositor)
2. Enables **Gamemode** (via libgamemode)
3. Configures **HDR** output parameters
4. Applies **FSR** upscaling if enabled
5. Sets environment variables per game (from per-game profile)

---

## Gamescope Integration

**Gamescope** is the micro-compositor from Valve that wraps games in their own sandboxed display environment.

### Features Enabled in Solus

- **NIS/FSR upscaling** — Built-in AMD FidelityFX Super Resolution 1.0 + NVIDIA Image Scaling
- **HDR support** — HDR → SDR conversion, real HDR output on HDR displays (Wayland)
- **VRS** — Variable Rate Shading via Vulkan extensions
- **Frame rate limit** — Per-game FPS cap without external tools
- **Async reprojection** — For VR-like smoothness
- **Borderless fullscreen** — True borderless fullscreen with tearing control
- **Adaptive sync** — VRR via Wayland protocols

### Gamescope Command Template

```bash
gamescope -W 1920 -H 1080 -r 144 -F fsr --hdr-enabled --adaptive-sync \
  --fsr-filter-strength 2 --fps-limit 144 --expose-wayland \
  -- steam -bigpicture
```

---

## MangoHUD + GOverlay

### MangoHUD

Performance overlay with real-time metrics:

- **CPU/GPU usage, clock speeds, temperatures, voltage** — From hardware monitoring
- **Frame timing** — Frame time graph, 1% and 0.1% lows
- **Vulkan/OpenGL** — Captures via hooking `vkQueuePresentKHR` / `SwapBuffers`
- **Gamepad battery** — Display controller battery level
- **Custom layout** — User-configurable via `~/.config/MangoHud/MangoHud.conf`

### GOverlay

GUI frontend for MangoHUD, vkBasalt, and Replay — no manual config editing needed.

```
/usr/bin/goverlay
Packaged with: libadwaita, gtk4
Supports: Per-game profiles, preset import/export, layout designer
```

---

## vkBasalt

Post-processing layer for Vulkan games:

- **CAS** (Contrast-Adaptive Sharpening) — AMD FidelityFX CAS via compute shader
- **Denoise** — Spatio-temporal denoising
- **Tonemap** — Custom tonemapping for HDR/SDR
- **Technicolor** — Color grading presets
- **SMAA** — Subpixel Morphological Anti-Aliasing
- **FXAA** — Fast Approximate Anti-Aliasing
- **Deband** — Banding reduction

Enabled via `VK_LAYER_vkBasalt_32.json` / `VK_LAYER_vkBasalt_64.json` in the Vulkan layer path.

---

## Gamemode Configuration

**gamemoded** runs at system level, adjusting kernel parameters on demand.

### Default Configuration

```ini
# /etc/gamemode.ini
[general]
desiredgov=performance
softrealtime=auto
renice=10
ioprio=4
inhibit_screensaver=1
disable_splitlock=1

[gpu]
apply_gpu_optimisations=accept-responsibility
gpu_device=0
amd_performance_level=high
nvidia_powermizer_mode=1
nvidia_dynamic_power=1
nv_sync_sw=0
nv_ignore_display=1

[cpu]
park_cores=0            # Don't park cores on modern CPUs
pin_cores=auto           # Auto-pin to physical cores
```

---

## Lutris + Heroic Launcher

### Lutris (Game Manager)

- **Runner system** — Wine, Proton, Steam, RetroArch, MAME, DosBox, ScummVM, and more
- **Script-based installers** — Community-maintained install scripts
- **Custom Wine builds** — Lutris-wine builds (optimized for specific games)
- **Per-game settings** — Environment variables, runner version, DXVK/VKD3D toggles

### Heroic Games Launcher

- **Epic Games Store** integration via Legendary
- **GOG Galaxy** integration via gogdl
- **Amazon Games** support
- **Cloud saves** — Sync with Epic/GOG cloud
- **Per-game Wine/Proton configuration**
- **DXVK/VKD3D version management**
- **Silent mode** — Minimal resource usage when minimized to tray

---

## Shader Cache Management

Solus includes a **Shader Cache Manager** daemon that:

1. **Pre-warms caches** — Background download of known shader caches for popular games
2. **Monitors new game launches** — Watches `~/.cache/mesa_shader_cache_db/` and `~/.steam/root/steamapps/shadercache/`
3. **Compresses idle caches** — Periodically compresses shader caches with zstd for space savings
4. **Synchronizes DXVK caches** — Downloads community DXVK state caches from `github.com/SolusOS/dxvk-caches`
5. **Auto-purges stale caches** — Removes caches for uninstalled games after 30 days

### Key Environment Variables

```bash
export __GL_SHADER_DISK_CACHE_SKIP_CLEANUP=1  # NVIDIA - keep entire disk cache
export MESA_SHADER_CACHE_DIR="$HOME/.cache/mesa_shader_cache_db"
export MESA_SHADER_CACHE_SIZE=4096              # 4GB max per game
export DXVK_STATE_CACHE_PATH="$HOME/.cache/dxvk-state-cache"
export DXVK_ENABLE_STATE_CACHE=1
export RADV_DEBUG=nocache               # Disable when debugging shader issues
```

---

## Fsync / Futex2 Support

### Fsync (Fast Synchronization)

Implemented via the Linux `futex` syscall with `FUTEX_WAIT_BITSET`/`FUTEX_WAKE_BITSET`.

```
Kernel requirement: CONFIG_FUTEX=y (default on all Solus kernels)
Enabled in Wine/Proton: WINEFSYNC=1 (default on Solus)
```

### Futex2

Next-generation futex interface enabling:

- `FUTEX2_SIZE_U32` / `FUTEX2_SIZE_U64` — Variable-size futex operations
- `FUTEX2_WAITV` — Wait on multiple futexes simultaneously
- Lower overhead for heavily contested locks (games with many threads)

```
Kernel requirement: CONFIG_FUTEX2=y (enabled in Solus kernel ≥6.6)
Enabled in Wine/Proton: WINEFSYNC_FUTEX2=1
```

---

## HDR Support (Wayland)

Solus Gaming delivers **end-to-end HDR** via:

### Display Server

- **Wayland compositor:** Solus Budgie/KDE/GNOME with Wayland session
- **Color management protocol:** `wp-color-management-v1` (merged in wayland-protocols)
- **HDR output:** Enabled via `wlr-gamma-control-unstable-v1` or `kde-hdr-metadata` protocol

### Application Layer

- **Gamescope:** HDR capability advertisement, HDR → SDR tone mapping, real HDR output
- **VKD3D-Proton:** DX12 HDR (DXGI_FORMAT_R16G16B16A16_FLOAT) → Vulkan HDR
- **DXVK:** HDR10 signaling via Vulkan extensions (VK_EXT_hdr_metadata, VK_EXT_swapchain_colorspace)
- **Wine:** Color space metadata forwarded to Wayland

### Verification

```bash
# Check HDR support
cat /sys/class/drm/card*-HDMI*/hdr_sink_metadata
# Enable HDR in Gamescope
gamescope --hdr-enabled
# Check HDR status
hdr-ctl status
```

---

## Variable Refresh Rate (VRR)

| Component | VRR Support | Notes |
|-----------|------------|-------|
| Wayland | Full (via wp-vrr-v1) | Requires compositor support (Budgie/KDE/GNOME) |
| Gamescope | Full (`--adaptive-sync`) | Works with any compositor |
| X11 | Limited | Only works with single monitor/compositor |
| AMD | Freesync/Freesync Premium | All DisplayPort, select HDMI |
| NVIDIA | G-Sync / G-Sync Compatible | Via `nvidia-drm.modeset=1` |
| Intel | Adaptive Sync | DP and HDMI 2.1+ |

### VRR Configuration

```bash
# Wayland (generic)
gsettings set org.gnome.mutter experimental-features "['variable-refresh-rate']"
# KDE Wayland
kwriteconfig5 --file kwinrc --group Wayland --key EnableVariableRefreshRate true
# Gamescope
gamescope --adaptive-sync
```

---

## Latency Reduction Pipeline

Solus Gaming implements a complete latency reduction chain:

```
Game Engine → Wine/Proton → Vulkan/OpenGL → Kernel → Hardware
                   ↓               ↓           ↓          ↓
              Fsync/Futex2   Async shaders   GFX_SCHED   Radeon Anti-Lag
              MS-Safe hooks  VKD3D: DX12     Low-latency  NVIDIA Reflex
              Raw mouse      Pre-compiled    USB polling  Null clocks
                             caches          IRQ balance
```

### Components

1. **Wine latency:**
   - `WINEDLLOVERRIDES=nvapi,nvapi64=b` — Disable NVIDIA API hooks if not needed
   - `WINEDEBUG=-all` — No debug output
   - `STAGING_SHARED_MEMORY=1` — Shared memory sync primitives
   - `WINEFSYNC=1` — Fsync enabled
   - `WINEFSYNC_FUTEX2=1` — Futex2 where available

2. **Vulkan latency:**
   - `VK_LOADER_LAYERS_DISABLE=` — Only layers you need
   - `RADV_PERFTEST=sam` — Enable shader app lazy load on AMD
   - `MESA_VK_WSI_PRESENT_MODE=mailbox` — Tearing-free low latency (or `immediate` for zero latency)

3. **Kernel/tuning:**
   - `kernel.split_lock_mitigate=0` — No split-lock penalty
   - `kernel.nmi_watchdog=0` — Disable NMI watchdog (frees CPU time)
   - `processor.max_cstate=1` — Prevent deep C-states during gaming
   - `intel_idle.max_cstate=0` — Same for Intel
   - IRQ balance pinned to efficiency cores
   - `udev` rules for USB polling rate (1000 Hz on game controllers)

4. **Input latency:**
   - Raw mouse input via `SDL_MOUSE_RELATIVE_SCALING=0`
   - `SDL_JOYSTICK_HIDAPI=1` — HIDAPI for controller input
   - `RADV_DEBUG=noirq` — Avoid polluting GPU timestamps with IRQ latency

---

## Controller Support

| Controller | Driver | Kernel Module | Features |
|-----------|--------|---------------|----------|
| Xbox (wired) | xpad | `xpad` | All generations |
| Xbox (wireless) | xpad | `xpad` | Via Microsoft adapter |
| Xbox One/Series BT | xpad | `xpad` | Bluetooth LE |
| Xbox Elite | xpad | `xpad` | Full paddle support |
| Nintendo Switch Pro | hid-nintendo | `hid-nintendo` | Gyro, rumble, BT |
| Nintendo Joy-Con | hid-nintendo | `hid-nintendo` | Per-joycon, pairing |
| Nintendo Switch Online | hid-nintendo | `hid-nintendo` | NES/SNES/N64 controllers |
| DualShock 3/4 | hid-sony | `hid-sony` | DS3/DS4 wired+BT |
| DualShock 4 | ds4 | `hid-sony` | Touchpad, gyro, lightbar |
| DualSense (PS5) | hid-playstation | `hid-playstation` | Haptic, adaptive triggers |
| DualSense Edge | hid-playstation | `hid-playstation` | Full Edge features |
| Steam Controller | hid-steam | `hid-steam` | Touchpads, gyro |
| Generic HID | hid-generic | `hid-generic` | Basic USB HID |

**Additional userspace:** `sdg` (Sony DS4/DualSense), `ds4drv` (DS4 BT pairing), `joycond` (Joy-Con pairing daemon)

### udev Rules

Solus includes `60-game-controllers.rules` with correct permissions (`MODE="0660"`, `GROUP="games"`) and default polling rates (1000 Hz for all supported controllers).

---

## Performance Profiles

The Gaming Control Center ships with four built-in performance profiles:

| Profile | CPU Governor | GPU Power | Screen VRR | Fan Curve | Use Case |
|---------|-------------|-----------|------------|-----------|----------|
| **Power Saver** | powersave | low/auto | Off | Quiet | Desktop / light gaming |
| **Balanced** | ondemand | auto | Auto | Auto | General gaming |
| **Performance** | performance | high | On | Aggressive | AAA titles, VR |
| **Turbo** | performance | max | On | Max | Benchmarking, latency-critical |

Each profile controls:

- **cpufreq governor** (via `cpupower` or `sysfs`)
- **GPU power profile** (via `amdgpu_power_profile`, `nvidia-settings`, or `intel_gpu_top`)
- **GPU clock limits** (min/max for core and memory)
- **DRM VRR state**
- **CPU C-state limit**
- **Thermal/throttle thresholds**
- **I/O scheduler** (e.g., `none` for NVMe)
- **Transparent HugePages** (always madvise)

Profiles can be extended by the user (per-game overrides).

---

## Per-Game Optimization

Each game can have a profile stored in:

```
~/.config/solus-gaming-center/games/<game-id>.conf
```

### Profile Contents

```ini
[game]
name="Cyberpunk 2077"
runner=proton
proton_version=GE-Proton9-25

[launch]
options="--gamescope --gamemode --hdr"
env="RADV_PERFTEST=sam"
env="DXVK_HUD=0"
env="MANGOHUD_CONFIG=position=top-right,fps,gpu_temp,cpu_temp,vram"

[gpu]
radeon_power_profile=high
nvidia_power_mizer=1
gpu_clock_min=1500
gpu_clock_max=2800
vram_clock_min=1000

[cpu]
governor=performance
cstate_limit=1
pin_cores=auto

[compatibility]
dxvk_version=2.5
vkd3d_version=2.14
wine_version=GE-Proton9-25
fsync=1
futex2=1

[display]
resolution=1920x1080
refresh_rate=144
hdr=1
vrr=1
fsr=1
fsr_strength=2
scaling=gamescope
```

---

## Gaming Control Center Design

See the full specification in `gaming-control-center-spec.md`.

High-level summary:

- **Language:** Rust + GTK4 (libadwaita)
- **Backend:** D-Bus systemd service (`solus-gaming-daemon`)
- **Features:**
  - Performance profile switcher (tray icon + UI)
  - Game library scan (Steam, Lutris, Heroic, custom)
  - Per-game settings editor
  - Driver status and switcher (open vs proprietary NVIDIA)
  - Proton version manager (download, build, switch)
  - Shader cache management
  - MangoHUD overlay configurator
  - System health dashboard (temps, clocks, frame rate)
  - HDR/VRR toggle
  - Controller test pad
  - Benchmark runner (with frame-time capture)
- **Integration:** Notifications via `libnotify`, OSD via `gnome-bg` / `kde-osd`, polkit for privileged operations

---

## Package Layout Summary

```
solus-gaming-platform        # Meta-package (depends on all below)
├── solus-gpu-drivers        # GPU detection, driver installation, switcher
├── solus-gaming-control-center  # GUI application
├── solus-gaming-tools       # CLI tools (gamemode, mangohud, etc.)
└── solus-steam-optimizer    # Steam scripts and service files
```

See the RPM spec files in `packages/spec-files/` for complete dependency trees.
