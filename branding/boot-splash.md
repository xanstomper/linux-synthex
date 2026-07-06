# Solus Plymouth Boot Splash — Design Specification

> Version 1.0 | July 2026  
> Part of the Linux Solus Brand Identity

---

## 1. Overview

The Solus Plymouth boot splash provides a branded, smooth boot animation displayed during system startup. It combines the Solus icon mark with the signature amber→purple gradient on a dark background.

---

## 2. Visual Design

### 2.1 Layout

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│                                                       │
│                                                       │
│                                                       │
│                                                       │
│                    ┌─────────────┐                     │
│                    │  █████████  │                     │
│                    │  ██ ○ ██   │  ← Solus icon        │
│                    │  █████████  │     animated         │
│                    └─────────────┘                     │
│                                                       │
│                    ○○○○○○●○○○○○                       │
│                    Progress bar                        │
│                    (amber, pulsing)                    │
│                                                       │
│                    Solus                               │
│                    Illuminate Your Desktop             │
│                                                       │
│                                                       │
│                    ◇  Plasma ◇                         │
│                    Edition indicator                   │
│                                                       │
│                    [■■■■■■■■□□□□]                     │
│                    [■■■■■■■■■■■■]                     │
│                    Actual progress                     │
│                    (dual bar)                          │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 Colour Scheme

| Element              | Hex       | Usage                            |
|----------------------|-----------|----------------------------------|
| Background           | `#1A1A2E` | Full-screen background           |
| Background accent    | `#16213E` | Subtle radial vignette           |
| Icon fill            | `#FFB300` | Icon mark primary                |
| Icon accent          | `#1565C0` | Icon mark hexagon fill           |
| Icon glow            | `#FFB300` | Icon ambient glow (50% opacity)  |
| Progress bar fill    | `#FFB300` | Active progress                  |
| Progress bar track   | `#0F3460` | Inactive progress                |
| Title text           | `#E8E8F0` | "Solus" wordmark                 |
| Tagline text         | `#C0C0D0` | "Illuminate Your Desktop"        |
| Edition indicator    | `#707090` | Edition name                     |
| Dot markers          | `#0F3460` | Inactive dots                    |
| Dot marker active    | `#FFB300` | Active dot                       |

### 2.3 Typography

| Element           | Font              | Size  | Weight | Colour    |
|-------------------|-------------------|-------|--------|-----------|
| "Solus"           | Inter Bold        | 36px  | 700    | `#E8E8F0` |
| Tagline           | Inter Regular     | 16px  | 400    | `#C0C0D0` |
| Edition           | Inter Medium      | 12px  | 500    | `#707090` |

---

## 3. Animation Sequence

### Phase 1: Logo Fade-In (0–1.5s)
- Background fades from black to `#1A1A2E`
- Solus icon mark fades in (opacity: 0 → 1) at centre
- Subtle radial glow expands from centre

### Phase 2: Icon Pulse (1.5s → continuous)
- Icon mark pulses gently (1.05× scale → 1.0× scale → 1.05×)
- Cycle: 3 seconds
- Rotation: icon mark rotates slightly (0° → 5° → 0°) over 6-second loop
- Glow halo pulses in sync (radius: 60% → 80% of icon)

### Phase 3: Progress (continuous until done)
- Dual progress bar:
  - **Top bar**: Estimated time progress (pulsing amber arc)
  - **Bottom bar**: Actual kernel/initrd progress (solid amber fill)
- Dot markers light up in sequence as boot stages complete
- During long operations, secondary gradient particles float upward

### Phase 4: Handoff (300ms)
- Icon mark brightens (scale: 1.0 → 1.1, opacity flash)
- Progress bars complete to 100%
- Brief white flash (200ms) as Plymouth transitions to display manager
- Smooth handoff to SDDM (no abrupt cut)

---

## 4. Progress Dot Sequence

6 dots representing boot stages:

| Dot | Stage               | Description                |
|-----|----------------------|----------------------------|
| 1   | BIOS/UEFI → Kernel   | Kernel loading             |
| 2   | Kernel init          | Driver init, modules       |
| 3   | Root filesystem      | Root mount, fsck           |
| 4   | System services      | systemd basic.target       |
| 5   | Display manager      | SDDM/graphical.target      |
| 6   | Desktop ready        | Welcome screen             |

---

## 5. Component Details

### 5.1 Icon Mark Animation
- Base: Solus icon mark in amber with deep blue hexagon
- Scale pulse: 1.0 → 1.05 → 1.0 (3s sine wave)
- Rotation: 0° → +5° CW → 0° → -5° CCW → 0° (6s loop)
- Glow: Radial gradient behind icon, opacity 0.3 → 0.6 → 0.3 (3s)
- Particles: 3 tiny amber dots floating upward from icon at random intervals

### 5.2 Progress Bars
```
Top bar (time estimate):
  ┌──────────────────────────────────────────┐
  │ ████████████████████░░░░░░░░░░░░░░░░░░ │  ← Amber #FFB300 on #0F3460
  │    Smooth continuous fill, pulsing       │
  └──────────────────────────────────────────┘

Bottom bar (actual progress):
  ┌──────────────────────────────────────────┐
  │ ████████████████░░░░░░░░░░░░░           │  ← Solid fill
  │    Block-level updates, no animation     │  ← Actual init progress
  └──────────────────────────────────────────┘
```

### 5.3 Particle Effects
- Small amber circles (r=3px) floating upward from icon centre
- Speed: 20px/s, random x-offset ±15px
- Opacity: 0.6 → 0 (fade out over 2s)
- Frequency: ~1 particle every 400ms
- Maximum: 8 particles on screen at once

---

## 6. Themes

The Plymouth theme supports all Solus editions:

| Edition  | Icon Colour       | Progress Colour   | Edition Text |
|----------|-------------------|-------------------|--------------|
| Default  | `#FFB300` Amber   | `#FFB300` Amber   | —            |
| Plasma   | `#FFB300` Amber   | `#FFB300` Amber   | Plasma       |
| Hyprland | `#6A1B9A` Purple  | `#6A1B9A` Purple  | Hyprland     |
| GNOME    | `#00897B` Teal    | `#00897B` Teal    | GNOME        |

---

## 7. File Structure

```
boot-splash/
├── boot-splash.md              # This design specification
├── solus/                      # Plymouth theme directory
│   ├── solus.plymouth          # Theme metadata file
│   ├── solus.script            # Plymouth script file
│   ├── logo.png                # Solus icon mark (128×128, amber)
│   ├── logo-16.png             # Solus icon (16×16, fallback)
│   ├── box.png                 # Progress bar background
│   ├── box-inactive.png        # Inactive progress bar
│   ├── bullet.png              # Active dot marker
│   ├── bullet-inactive.png     # Inactive dot marker
│   ├── throbber-*.png          # Throbber frames (01–60, 128×128)
│   └── progress-*.png          # Progress bar frames (01–10)
└── README.md                   # Build and install instructions
```

### solus.plymouth
```
[Plymouth Theme]
Name=Solus
Description=Solus branded boot splash with amber accents
ModuleName=script
```

---

## 8. Build Dependencies

- **plymouth** (>= 22.0)
- **ImageMagick** (for rendering PNG frames from SVG)
- **plymouth-plugin-script** (for the script engine)

---

## 9. Installation

```bash
# Copy theme
sudo cp -r solus /usr/share/plymouth/themes/solus

# Install theme
sudo plymouth-set-default-theme solus

# Regenerate initramfs
sudo update-initramfs -u

# Test
sudo plymouth --show-splash
# or for a simulation:
sudo plymouthd
sudo plymouth --show-splash
sleep 5
sudo plymouth --quit
```

---

## 10. Compatibility

| Distro Family | Initramfs Command                |
|---------------|----------------------------------|
| Debian/Ubuntu | `sudo update-initramfs -u`       |
| Fedora/RHEL   | `sudo dracut -f`                 |
| Arch Linux    | `sudo mkinitcpio -p linux`       |
| openSUSE      | `sudo mkinitrd`                  |

---

## 11. Accessibility

- High contrast icon and text
- Progress bars provide visual indication of boot progress
- No fast-flashing animations (all ≥ 3s cycles)
- Respects `plymouth --hide-splash` for serial console access

---

*© 2026 Linux Solus Project. Licensed under GPL-3.0+.*
