# Solus Gaming Control Center — Specification Document

## Overview

The **Solus Gaming Control Center** is a native GUI application for managing all aspects of the gaming experience on Solus Linux. It provides a unified interface for driver management, performance tuning, game library management, and system monitoring — eliminating the need to manually edit config files or use multiple CLI tools.

---

## 1. Architecture

### 1.1 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | **Rust** | Memory-safe, performance-critical, strong ecosystem for system tools |
| GUI Toolkit | **GTK4 + libadwaita** | Native GNOME/Budgie integration, responsive design, HIG-compliant |
| Build System | **Meson + Cargo** | Meson for the overall project, Cargo for Rust sub-components |
| IPC | **D-Bus (zbus)** | System bus for daemon communication, session bus for UI ↔ daemon |
| Backend Service | **systemd user service** | `solus-gaming-daemon` runs as a user service, activated on demand |
| Privileged Ops | **polkit** | For operations requiring root (driver install, sysctl, CPU governor) |
| Notifications | **libnotify** | Desktop notifications for profile changes, HDR toggle, etc. |

### 1.2 Process Architecture

```
┌─────────────────────────────────────────────────────┐
│                Gaming Control Center (GUI)           │
│                     (GTK4 App)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Dashboard│ │ Game Lib │ │Settings  │ │ Drivers│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
│       │             │            │            │       │
│       └─────────────┼────────────┼────────────┘       │
│                     │            │                     │
│              ┌──────┴────────────┴──────┐              │
│              │  D-Bus Client (zbus)     │              │
│              └──────────┬───────────────┘              │
└─────────────────────────┼──────────────────────────────┘
                          │ D-Bus (session bus)
┌─────────────────────────┼──────────────────────────────┐
│              ┌──────────┴───────────────┐              │
│              │  solus-gaming-daemon      │              │
│              │  (systemd --user service) │              │
│  ┌───────────┴───────────┐              │              │
│  │ Profile Manager       │              │              │
│  │ Game Config Store     │              │              │
│  │ Driver Manager (IPC)  │              │              │
│  │ Monitor Collector     │              │              │
│  └───────────┬───────────┘              │              │
│              │                          │              │
│         ┌────┴────┐                     │              │
│         │ polkit  │ (for privileged    │              │
│         │ agent   │  operations)       │              │
│         └─────────┘                     │              │
└─────────────────────────────────────────┘              │
                          │ D-Bus (system bus) / sudo via polkit
┌─────────────────────────┼──────────────────────────────┐
│  System Components      │                              │
│  ┌──────────┐ ┌─────────┴──────┐ ┌─────────────────┐  │
│  │cpupower  │ │ /sys/class/drm │ │ gpu-driver-     │  │
│  │          │ │ /sys/class/hwmon│ │ manager         │  │
│  └──────────┘ └────────────────┘ └─────────────────┘  │
│  ┌──────────┐ ┌────────────────┐ ┌─────────────────┐  │
│  │gamemoded │ │ mangohud config│ │ Steam/Lutris DB │  │
│  └──────────┘ └────────────────┘ └─────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### 1.3 Directory Layout

```
/usr/
├── bin/
│   └── solus-gaming-center          # GUI launcher
├── libexec/
│   ├── solus-gaming-daemon           # Background daemon
│   └── solus-gaming-polkit-helper    # Privileged helper
├── share/
│   ├── solus-gaming-center/
│   │   ├── ui/                       # GTK UI definitions (Blueprints)
│   │   ├── icons/                    # App icons
│   │   ├── schemas/                  # GSettings schemas
│   │   └── style/                    # CSS styling
│   ├── applications/
│   │   └── solus-gaming-center.desktop
│   ├── polkit-1/
│   │   └── actions/
│   │       └── com.solus.gaming.policy
│   └── dbus-1/
│       └── services/
│           └── com.solus.GamingDaemon.service
└── lib/systemd/user/
    └── solus-gaming-daemon.service

~/.config/solus-gaming-center/
├── config.toml                       # User preferences
├── games/                            # Per-game profiles
│   ├── 730.conf                      # CS2
│   ├── 1551360.conf                  # Forza Horizon 5
│   └── ...
├── profiles/                         # Performance profiles
│   ├── default.toml
│   ├── performance.toml
│   └── turbo.toml
└── mangohud/                         # MangoHUD presets
    ├── default.conf
    └── competitive.conf
```

---

## 2. Feature Specifications

### 2.1 Dashboard

The Dashboard is the default view when opening the Gaming Control Center.

#### Elements

```
┌──────────────────────────────────────────────────────────┐
│ 🎮 Solus Gaming Control Center                    _ □ X │
├──────────┬───────────────────────────────────────────────┤
│          │ ┌─ Performance Profile ────────────────────┐ │
│ Dashboard│ │ ● Balanced ○ Performance ○ Turbo        │ │
│          │ │ ○ Power Saver                            │ │
│ Game Lib │ └──────────────────────────────────────────┘ │
│          │ ┌─ System Health ──────────────────────────┐ │
│ Drivers  │ │ CPU: 45°C  ████████░░ 2.4GHz             │ │
│ Settings │ │ GPU: 52°C  ██████░░░░ 1.8GHz  85% load  │ │
│          │ │ VRAM: 6.2/8.0 GB  ████████░░            │ │
│          │ └──────────────────────────────────────────┘ │
│          │ ┌─ Recent Performance ─────────────────────┐ │
│          │ │ Last session: Cyberpunk 2077             │ │
│          │ │ Avg: 87 FPS  |  1%: 62  |  0.1%: 48    │ │
│          │ └──────────────────────────────────────────┘ │
│          │ ┌─ Quick Actions ──────────────────────────┐ │
│          │ │ [🎬 Record Replay] [📸 Screenshot]      │ │
│          │ │ [📊 Toggle HUD] [🌙 HDR On]             │ │
│          │ └──────────────────────────────────────────┘ │
└──────────┴───────────────────────────────────────────────┘
```

#### Data Sources

| Metric | Source | Update Rate |
|--------|--------|-------------|
| CPU temp/usage/clock | `/sys/class/thermal/`, `cpupower`, `sensors` | 1s |
| GPU temp/usage/clock | `/sys/class/drm/`, `nvidia-smi`, `amdgpu` sysfs | 1s |
| VRAM usage | `nvidia-smi`, `amdgpu` sysfs, `intel_gpu_top` | 2s |
| Frame rate | MangoHUD shared memory | Real-time |
| Game detection | `pidof` + `/proc` scanning | 5s |

### 2.2 Game Library

Scans and manages game installations across all launchers.

#### Supported Sources

| Source | Detection Method | Notes |
|--------|-----------------|-------|
| Steam | `~/.steam/root/steamapps/*.acf` | Native Steam only (not Flatpak) |
| Lutris | `~/.config/lutris/games/*.yml` | Reads game configs and runners |
| Heroic | `~/.config/heroic/games-config/*.json` | Epic, GOG, Amazon |
| Custom | `~/.config/solus-gaming-center/games/*.conf` | Manual entries |

#### Game Profile Editor

Each game can have a comprehensive profile:

```
┌─ Game: Cyberpunk 2077 ──────────────────────────────────┐
│                                                          │
│  Launch Options                                          │
│  ☑ Gamescope     ☑ Gamemode     ☑ HDR     ☑ FSR        │
│  Resolution: [1920] x [1080] @ [144] Hz                 │
│  FPS Limit: [144]   FSR Strength: [2]                   │
│                                                          │
│  Wine/Proton Settings                                    │
│  Runner: [GE-Proton9-25        ▾]                       │
│  ☑ Fsync     ☑ Futex2     ☑ DXVK Async                 │
│  DXVK Version: [2.5.1 ▾]  VKD3D: [2.14 ▾]              │
│                                                          │
│  Graphics Tuning                                         │
│  GPU Profile: [3D Fullscreen ▾]                         │
│  GPU Clock Min: [1500] MHz   Max: [2800] MHz            │
│  VRAM Clock:   [1000] MHz                                │
│                                                          │
│  HUD / Overlay                                           │
│  [📊 Configure MangoHUD...]  [🎨 Configure vkBasalt...] │
│                                                          │
│  Environment Variables                                   │
│  [RADV_PERFTEST=sam...................................]  │
│  [DXVK_HUD=0....................................  +/-]  │
│                                                          │
│  [Save]  [Save as Preset...]  [Reset to Default]        │
└──────────────────────────────────────────────────────────┘
```

### 2.3 Driver Management

#### UI Layout

```
┌─ GPU Drivers ───────────────────────────────────────────┐
│                                                          │
│  Detected Hardware:                                      │
│  🖥 NVIDIA GeForce RTX 4070 (proprietary driver)        │
│  🖥 AMD Ryzen 7 7800X3D (integrated RDNA 3)             │
│                                                          │
│  [🔄 Auto-Detect & Install]                              │
│                                                          │
│  ── NVIDIA RTX 4070 ──                                   │
│  Current Driver: 550.120 (proprietary)                   │
│  Driver Version: ● 550.120 (latest) ◯ 545.84            │
│  [Switch to Nouveau (open source)]                       │
│  Status: ✅ Loaded | ✅ VRR | ✅ HDR | ✅ CUDA          │
│                                                          │
│  [Advanced: Kernel Parameters...]                        │
│                                                          │
│  ── AMD RDNA 3 (integrated) ──                           │
│  Driver: Mesa 24.3.3 (RADV + radeonsi)                   │
│  Status: ✅ Loaded | ✅ VRR | ✅ HDR | ✅ VA-API        │
│                                                          │
│  [Rebuild Initramfs] [Reinstall Drivers] [Restart GPU]  │
└──────────────────────────────────────────────────────────┘
```

#### Operations

- **Auto-detect** — Scans PCI bus via `lspci` and `/sys` for GPU vendor/model
- **Driver install** — Calls `gpu-driver-manager auto-install` with polkit escalation
- **NVIDIA switch** — Calls `gpu-driver-manager switch-nvidia proprietary|nouveau` with confirmation dialog noting that a reboot is required
- **Version rollback** — Lists available NVIDIA/Mesa versions from repository and allows switching

### 2.4 Performance Profiles

Four built-in profiles with the ability to create custom ones.

#### Profile Editor

```
┌─ Performance Profile Editor ────────────────────────────┐
│                                                          │
│  Profile Name: [Custom - High FPS        ▾              │
│                                                          │
│  ── CPU Settings ──                                      │
│  Governor:       [performance         ▾]                │
│  C-State Limit:  [C1 (deepest disabled)  ▾]             │
│  Min Frequency:  [3000] MHz                             │
│  Max Frequency:  [5050] MHz                             │
│                                                          │
│  ── GPU Settings ──                                      │
│  Power Profile:   [high                ▾]               │
│  Min Clock:       [1500] MHz                            │
│  Max Clock:       [2800] MHz                            │
│  Voltage Offset:  [0] mV                                │
│  Fan Curve:       [Aggressive ▾]                        │
│                                                          │
│  ── Display Settings ──                                  │
│  VRR:  [Auto ▾]    HDR: [Keep current ▾]               │
│                                                          │
│  ── System Settings ──                                   │
│  I/O Scheduler:   [none (NVMe) ▾]                      │
│  Swappiness:      [10]                                  │
│  Transparent HugePages: [always ▾]                      │
│                                                          │
│  [Save as New]  [Apply Now]  [Delete]                   │
└──────────────────────────────────────────────────────────┘
```

#### Profile Application Mechanism

1. User selects profile in GUI (or via tray icon)
2. Daemon receives D-Bus call `SetProfile("performance")`
3. Daemon applies settings sequentially:
   - CPU governor via `cpupower frequency-set -g performance`
   - C-state limits via `/sys/module/{intel_idle,processor}/parameters/max_cstate`
   - GPU power profile via `/sys/class/drm/card*/device/pp_power_profile_mode`
   - GPU clock limits via `/sys/class/drm/card*/device/pp_od_clk_voltage`
   - VRR state via `drm` sysfs or compositor D-Bus
   - I/O scheduler via `/sys/block/*/queue/scheduler`
4. OSD notification: "Performance profile activated"
5. Profile persists until changed or system reboot

### 2.5 MangoHUD Configurator

Visual editor for MangoHUD configuration files.

#### Features

- **Drag-and-drop layout editor** — Position HUD elements on a virtual screen
- **Preset system** — Pre-made layouts (Default, Competitive, Streamer, Debug)
- **Real-time preview** — HUD changes apply immediately (via MangoHUD shared memory)
- **Per-game presets** — Each game can have its own HUD layout

#### Configuration Parameters

| Category | Parameters |
|----------|-----------|
| Performance | fps, frametime, gpu_stats, cpu_stats, vram, ram, engine_version, wine |
| Hardware | gpu_temp, cpu_temp, gpu_core_clock, gpu_mem_clock, cpu_clock, fan_speed |
| Visualization | graph (frametime), histogram, text, bar, line_chart |
| Display | position, background_alpha, font_size, font_color, no_display, toggle_hotkey |
| Advanced | output_file, log_duration, read_cpu_power, read_gpu_power, control |

### 2.6 Shader Cache Manager

Manages shader compilation caches for reduced stutter.

#### Features

- **Cache overview** — Shows size, last used date, and game for each cache
- **Pre-warm** — Download known-good caches from community repositories
- **Manual clear** — Clear individual game caches
- **Auto-purge** — Remove caches for games not played in 30+ days
- **Size limits** — Set per-game and global cache size limits

### 2.7 Controller Test Pad

Visual controller testing utility.

#### Features

- **Real-time input display** — Button presses, analog stick positions, trigger axes
- **Force feedback test** — Test rumble motors
- **Gyro visualization** — 3D orientation display for gyro-enabled controllers
- **Battery level** — Display for supported controllers (DS4, DualSense, Switch Pro)
- **Mapping verification** — Confirm button mapping matches game expectations
- **Supported controllers:** Xbox, DualShock 3/4, DualSense, Switch Pro, Joy-Con, Steam Controller, generic HID

### 2.8 Benchmark Runner

Built-in benchmarking utility.

#### Features

- **Frame time capture** — Records frame times to a CSV file
- **Statistics** — Average FPS, 1% and 0.1% lows, frame time variance, percentiles
- **Overlay** — Run benchmark with MangoHUD overlay and capture metrics
- **Compare** — Compare results across different profiles/settings
- **Export** — Export results as CSV, JSON, or shareable screenshot

---

## 3. D-Bus API

### 3.1 Daemon Interface (`com.solus.GamingDaemon`)

```
interface com.solus.GamingDaemon {
    // Profile management
    method GetCurrentProfile() → (s profile_name)
    method SetProfile(s profile_name) → (b success)
    method ListProfiles() → (as profile_names)
    method CreateProfile(s name, a{sv} settings) → (b success)
    method DeleteProfile(s name) → (b success)
    
    // Game management
    method ScanGames() → (aa{sv} games)
    method GetGameProfile(s app_id) → (a{sv} profile)
    method SetGameProfile(s app_id, a{sv} profile) → (b success)
    method LaunchGame(s app_id) → (b success)
    
    // Driver management
    method DetectGPUs() → (aa{sv} gpus)
    method InstallDrivers(s vendor) → (b success)
    method SwitchNvidiaDriver(s target) → (b success)
    method GetDriverStatus() → (a{sv} status)
    
    // System monitoring
    method GetSystemMetrics() → (a{sv} metrics)
    method GetFPS() → (d fps)
    
    // Shader cache
    method GetShaderCacheInfo() → (aa{sv} caches)
    method ClearShaderCache(s game_id) → (b success)
    method PrewarmShaderCache(s game_id) → (b success)
    
    // Signals
    signal ProfileChanged(s profile_name)
    signal MetricsUpdated(a{sv} metrics)
    signal DriverStatusChanged(a{sv} status)
    signal GameLaunched(s app_id)
    signal GameStopped(s app_id)
};
```

### 3.2 Polkit Actions

```xml
<!-- /usr/share/polkit-1/actions/com.solus.gaming.policy -->
<policyconfig>
  <action id="com.solus.gaming.set-cpu-governor">
    <description>Change CPU governor</description>
    <message>Authentication is required to change the CPU governor for gaming.</message>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
  </action>
  
  <action id="com.solus.gaming.install-drivers">
    <description>Install or switch GPU drivers</description>
    <message>Authentication is required to install or switch GPU drivers.</message>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
  
  <action id="com.solus.gaming.set-gpu-clocks">
    <description>Adjust GPU clock speeds</description>
    <message>Authentication is required to adjust GPU clock speeds.</message>
    <defaults>
      <allow_any>auth_admin_keep</allow_any>
      <allow_inactive>auth_admin_keep</allow_inactive>
      <allow_active>yes</allow_active>
    </defaults>
  </action>
</policyconfig>
```

---

## 4. GTK4 UI Architecture

### 4.1 Window Structure

```
AdwApplicationWindow
├── AdwHeaderBar
│   ├── AdwWindowTitle (dynamic: "Dashboard" / "Game Library" / etc.)
│   ├── GtkMenuButton (hamburger menu: About, Help, Quit)
│   └── GtkToggleButton (tray pin toggle)
└── AdwNavigationSplitView
    ├── GtkStackSidebar (left)
    │   ├── "Dashboard"
    │   ├── "Game Library"
    │   ├── "Drivers"
    │   ├── "Performance Profiles"
    │   └── "Settings"
    └── GtkStack (right content area)
```

### 4.2 UI Components

| Widget | Source File | Description |
|--------|------------|-------------|
| `DashboardView` | `src/ui/dashboard.rs` | Main dashboard with health, FPS, quick actions |
| `GameLibraryView` | `src/ui/games.rs` | Game list, search, per-game editor |
| `GameProfileEditor` | `src/ui/game_editor.rs` | Detailed per-game settings |
| `DriverView` | `src/ui/drivers.rs` | GPU detection, driver install/switch |
| `ProfileEditor` | `src/ui/profiles.rs` | Performance profile creation/editing |
| `MangohudEditor` | `src/ui/mangohud.rs` | Visual MangoHUD configurator |
| `ControllerTestPad` | `src/ui/controller.rs` | Game controller input visualizer |
| `ShaderCacheView` | `src/ui/shaders.rs` | Shader cache management |
| `BenchmarkView` | `src/ui/benchmark.rs` | Benchmark runner and results |
| `SettingsView` | `src/ui/settings.rs` | Application settings |
| `TrayIcon` | `src/ui/tray.rs` | System tray quick switcher |

### 4.3 Theme Support

- **Adwaita** (light/dark) — Default, system theme
- **Custom CSS** — Overrides in `~/.config/solus-gaming-center/style.css`
- **Gaming accent color** — Configurable accent color (default: green `#2ecc71`)
- **Transparency** — Optional translucent window effect

---

## 5. Data Storage

### 5.1 Configuration File (`config.toml`)

```toml
[general]
theme = "system"
accent_color = "#2ecc71"
start_minimized = true
close_to_tray = true
check_updates = true

[performance]
default_profile = "balanced"
auto_profile_on_game = true
revert_on_game_exit = true

[overlay]
default_hud_preset = "default"
enable_mangohud = true
enable_vkbasalt = false
mangohud_toggle_key = "Shift+F12"

[drivers]
auto_update = false
nvidia_preference = "proprietary"
check_firmware = true

[shader_cache]
auto_purge_days = 30
max_cache_size_gb = 20
prewarm_enabled = true
```

### 5.2 Game Profile Format

Each game is stored as a TOML file in `~/.config/solus-gaming-center/games/<appid>.conf`.

```toml
[game]
name = "Cyberpunk 2077"
app_id = "1091500"
runner = "proton"
launcher = "steam"

[launch]
gamescope = true
gamemode = true
resolution = "1920x1080"
refresh_rate = 144
fps_limit = 144
hdr = true
fsr = true
fsr_strength = 2

[wine]
proton_version = "GE-Proton9-25"
dxvk_version = "2.5.1"
vkd3d_version = "2.14.1"
fsync = true
futex2 = true

[gpu]
power_profile = "3d_fullscreen"
clock_min_mhz = 1500
clock_max_mhz = 2800
vram_clock_mhz = 1000
voltage_offset_mv = 0

[env]
RADV_PERFTEST = "sam"
DXVK_HUD = "0"
MANGOHUD_CONFIG = "position=top-right,fps,gpu_temp,cpu_temp,vram"

[mangohud]
preset = "gaming"
no_display = false
toggle_hotkey = "Shift+F12"
```

### 5.3 Performance Profile Format

```toml
[name]
label = "Turbo"
description = "Maximum performance for benchmarking"
icon = "media-optical"

[cpu]
governor = "performance"
cstate_limit = 1
min_frequency_mhz = 3000
max_frequency_mhz = 5050
energy_perf_bias = 0

[gpu]
power_profile = "high"
clock_min_mhz = 2000
clock_max_mhz = 2800
vram_clock_mhz = 1250
fan_curve = "aggressive"

[display]
vrr = "on"
hdr = "keep"

[system]
io_scheduler = "none"
swappiness = 10
transparent_hugepages = "always"
nmi_watchdog = false
split_lock_mitigate = false
```

---

## 6. Implementation Roadmap

### Phase 1: Core Framework (v0.1.0)
- [x] Project scaffolding (Cargo + Meson)
- [x] GTK4 window with navigation
- [ ] D-Bus daemon skeleton
- [ ] System monitoring (CPU/GPU metrics)
- [ ] Dashboard view
- [ ] Performance profile switching
- [ ] System tray icon

### Phase 2: Game Management (v0.2.0)
- [ ] Steam library scanning
- [ ] Lutris library scanning
- [ ] Heroic library scanning
- [ ] Per-game profile editor
- [ ] Launch integration (steam-wrapper)

### Phase 3: Drivers & Hardware (v0.3.0)
- [ ] GPU detection UI
- [ ] Driver installation (polkit)
- [ ] NVIDIA driver switching
- [ ] GPU clock/fan control
- [ ] HDR/VRR toggles

### Phase 4: Advanced Features (v0.4.0)
- [ ] MangoHUD configurator
- [ ] vkBasalt configurator
- [ ] Shader cache manager
- [ ] Controller test pad
- [ ] Benchmark runner

### Phase 5: Polish (v1.0.0)
- [ ] Notifications and OSD
- [ ] Multi-language support
- [ ] Accessibility (a11y)
- [ ] Performance optimization
- [ ] Flatpak packaging

---

## 7. Package Dependencies

### Build Dependencies
- `rust` (≥1.75) + `cargo`
- `meson` (≥1.3) + `ninja-build`
- `gtk4-devel` (≥4.12)
- `libadwaita-devel` (≥1.4)
- `libayatana-appindicator-devel` (or `libdbusmenu-gtk3-devel`)
- `glib2-devel`
- `blueprint-compiler` (for GTK UI templates)
- `gettext` (for translations)

### Runtime Dependencies
- `gtk4` (≥4.12)
- `libadwaita` (≥1.4)
- `libnotify`
- `polkit`
- `systemd`
- `gamemode`
- `mangohud`
- `gamescope`
- `gpu-driver-manager` (solus-gpu-drivers package)
- `steam-optimizer` (solus-steam-optimizer package)

---

## 8. Testing Plan

| Test Type | Tools | Coverage |
|-----------|-------|----------|
| Unit tests | `cargo test` | All Rust modules |
| Integration | `cargo test --test integration` | D-Bus API, profile switching |
| GUI tests | `gtk4-test` / dogtail | UI interactions |
| System tests | Manual test matrix | Hardware combinations (AMD/NVIDIA/Intel) |
| Performance | Custom benchmark script | Startup time, memory usage, polling overhead |
| Accessibility | `a11y-tools` | Screen reader, keyboard navigation |

---

## 9. Security Considerations

1. **Privilege separation** — Daemon runs as user; privileged operations go through polkit
2. **Input validation** — All D-Bus method arguments validated (no shell injection)
3. **No setuid binaries** — All root operations use polkit
4. **Config file permissions** — Game profiles are user-owned (0600) to avoid leaking game config
5. **D-Bus security** — Daemon only listens on session bus, not system bus
6. **Tray icon** — No elevated privileges for tray operations

---

## 10. Mockups & Wireframes

*(Textual descriptions sufficient for initial implementation.)*

### Dashboard Layout
```
┌──────────────────────────────────────────────────────────────────┐
│ 🎮 Solus Gaming Control Center                            _ □ X │
├────────────┬─────────────────────────────────────────────────────┤
│  Dashboard │  Performance Profile                                │
│  Game Lib  │  ● Balanced  ○ Performance  ○ Turbo  ○ Power Saver │
│  Drivers   │  ┌─────────────────────────────────────────────────┐│
│  Profiles  │  │ System Health                          ┌─────┐ ││
│  Settings  │  │ CPU: ████████████████░░░ 45°C  2.4GHz  │🔄 5s│ ││
│            │  │ GPU: ██████████████░░░░░ 52°C  1.8GHz  └─────┘ ││
│            │  │ RAM: ████████████░░░░░░░ 8.2/16 GB              ││
│            │  │ VRAM: █████████████░░░░░░ 6.2/8 GB              ││
│            │  └─────────────────────────────────────────────────┘│
│            │  ┌─────────────────────────────────────────────────┐│
│            │  │ Recent Performance                              ││
│            │  │ Cyberpunk 2077             87 FPS  ┌──────┐    ││
│            │  │ ╱‾‾‾‾‾‾‾╲                                 │    ││
│            │  │ ╱         ╲_____________╱╲___╱╲___           │    ││
│            │  │ ╲___╱╲___/                  ╲__/              │    ││
│            │  │ └──────┘                                     ││
│            │  └─────────────────────────────────────────────────┘│
│            │  [🎬 Record] [📸 Screenshot] [📊 HUD] [🌙 HDR]  │
└────────────┴─────────────────────────────────────────────────────┘
```
