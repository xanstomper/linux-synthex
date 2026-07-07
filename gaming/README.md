# SynthOS Gaming Platform

**Zero-friction, high-performance gaming on SynthOS.**

The Synthex Gaming Platform delivers a complete, integrated gaming environment for SynthOS — from automatic GPU driver detection to per-game optimization profiles. Install the meta-package, reboot, and play.

---

## Quick Start

### Install

```bash
# Full gaming platform (recommended)
sudo eopkg install synthex-gaming-platform

# Or individual components
sudo eopkg install synthex-gpu-drivers
sudo eopkg install synthex-gaming-control-center
sudo eopkg install synthex-gaming-tools
sudo eopkg install synthex-steam-optimizer
```

### First Launch

1. **Reboot** after driver installation (NVIDIA switching requires it)
2. Open **Synthex Gaming Control Center** from the application menu
3. The dashboard shows your GPU status, system health, and performance profile
4. Click **Auto-Detect & Install** under Drivers if GPU isn't recognized
5. Launch Steam, Lutris, or Heroic — games run with optimal settings automatically

---

## Features

| Feature | Description |
|---------|-------------|
| **GPU Auto-Detect** | Detects AMD, NVIDIA, or Intel GPUs and installs the correct drivers |
| **NVIDIA Driver Switch** | Switch between open-source Nouveau and proprietary NVIDIA easily |
| **Proton GE** | Custom Proton builds with Media Foundation, FSR 2, and more fixes |
| **Gamescope** | Micro-compositor for low-latency, sandboxed gaming with HDR/VRR |
| **MangoHUD** | Real-time performance overlay (FPS, temps, clocks, frame times) |
| **Gamemode** | Automatic system tuning when games launch |
| **Steam Optimizer** | System-level tuning (CPU governor, TCP, shader cache) for Steam |
| **Gaming Control Center** | Full GUI for all gaming settings, profiles, and monitoring |
| **HDR (Wayland)** | End-to-end HDR support on compatible displays |
| **VRR / Adaptive Sync** | Tear-free gaming with variable refresh rate |
| **Shader Cache Manager** | Automatic pre-warming and management to reduce stutter |
| **Per-Game Profiles** | Fine-tune every game individually (GPU clocks, FSR, env vars) |

---

## Directory Structure

```
/usr/
├── bin/
│   ├── steam-wrapper                    # Gamescope/gamemode Steam launcher
│   └── synthex-gaming-center              # Gaming Control Center GUI
├── sbin/
│   └── gpu-driver-manager               # GPU driver detection/installation
├── libexec/
│   ├── synthex-gaming-daemon              # Background daemon
│   └── synthex-gaming-polkit-helper       # Privileged operations
├── share/
│   └── synthex-gaming/
│       ├── steam/
│       │   └── steam-optimizations.sh   # System tuning script
│       ├── proton/
│       │   └── proton-ge-build.sh       # Proton GE build from source
│       └── ...
├── lib/systemd/user/
│   └── synthex-gaming-daemon.service
└── etc/
    ├── default/
    │   ├── amdgpu                       # AMD GPU configuration
    │   ├── nvidia                       # NVIDIA GPU configuration
    │   └── intel-gpu                    # Intel GPU configuration
    ├── modprobe.d/                      # Auto-generated kernel module options
    └── udev/rules.d/                    # GPU device permissions
```

---

## Components

### synthex-gpu-drivers
Automatic GPU detection, driver installation, and configuration. Manages modprobe options, udev rules, and initramfs integration. Supports switching between proprietary NVIDIA and Nouveau drivers.

### synthex-gaming-control-center
Native GUI application (Rust + GTK4/libadwaita) for:
- Dashboard with real-time system monitoring
- Performance profile switching (Power Saver ↔ Turbo)
- Game library scanning and per-game profiles
- GPU driver management
- MangoHUD visual configurator
- Shader cache management
- Controller test pad
- Benchmark runner

### synthex-gaming-tools
CLI gaming tools including Proton GE builder, MangoHUD utilities, and diagnostic scripts.

### synthex-steam-optimizer
Steam integration scripts that apply system tuning (CPU governor, kernel parameters, network optimization, shader cache setup) while Steam is running and revert on exit.

---

## Requirements

- **OS:** SynthOS (or any rpm-based distribution with adaptations)
- **Kernel:** Linux ≥6.6 (for futex2, amdgpu DC, i915 GuC/HuC)
- **Display Server:** Wayland recommended (X11 supported with reduced features)
- **RAM:** 8 GB minimum, 16 GB recommended
- **Storage:** 5 GB for platform + Steam, additional for games
- **GPU:** Any AMD, NVIDIA, or Intel GPU from ~2012 onwards

---

## Documentation

| File | Description |
|------|-------------|
| [gaming-architecture.md](gaming-architecture.md) | Complete platform architecture documentation |
| [gaming-control-center-spec.md](gaming-control-center-spec.md) | Gaming Control Center specification |
| [drivers/amdgpu-config](drivers/amdgpu-config) | AMD GPU configuration reference |
| [drivers/nvidia-config](drivers/nvidia-config) | NVIDIA GPU configuration reference |
| [drivers/intel-config](drivers/intel-config) | Intel GPU configuration reference |
| [drivers/gpu-driver-manager.sh](drivers/gpu-driver-manager.sh) | GPU driver manager script |
| [steam/steam-optimizations.sh](steam/steam-optimizations.sh) | Steam system optimization script |
| [steam/steam-wrapper.sh](steam/steam-wrapper.sh) | Steam launcher wrapper |
| [proton/proton-ge-build.sh](proton/proton-ge-build.sh) | Proton GE build script |

---

## Building from Source

```bash
# Build Proton GE
./proton/proton-ge-build.sh all

# Package for distribution
./proton/proton-ge-build.sh package
./proton/proton-ge-build.sh install
```

RPM spec files for building platform packages:
```
packages/spec-files/
├── synthex-gaming-platform.spec
├── synthex-gpu-drivers.spec
└── synthex-gaming-control-center.spec
```

Kickstart inclusion for ISO builds:
```
build/kickstart/synthex-gaming-packages.ksinc
```

---

## License

MIT License. See `LICENSE` for details.

---

## Contributing

The Synthex Gaming Platform is developed at [github.com/getsynthex/synthex-gaming](https://github.com/getsynthex/synthex-gaming). Issues and pull requests welcome.

---

*Made for gamers, by gamers. Synthex Gaming Team.*
