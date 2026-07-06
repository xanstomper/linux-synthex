# Solus GRUB Theme — Design Specification

> Version 1.0 | July 2026  
> Part of the Linux Solus Brand Identity

---

## 1. Overview

The Solus GRUB theme provides a branded boot menu experience consistent with the Solus identity. Dark, minimal, with warm amber highlights.

---

## 2. Visual Design

### 2.1 Layout

```
┌─────────────────────────────────────────────────────┐
│                         ██                           │
│                       ██  ██                         │
│                       ██  ██                         │
│                     ██      ██                       │
│                 Solus Icon Mark (centre)              │
│                                                       │
│               ╔═══════════════════╗                   │
│               ║  Solus            ║  ← Selected      │
│               ║  Advanced options  ║  ← Entry         │
│               ║  Windows 11       ║  ← Entry         │
│               ║  System setup     ║  ← Entry         │
│               ╚═══════════════════╝                   │
│                                                       │
│               [Boot]  [Settings]                      │
│                                                       │
│                  ─── Timeline bar ───                 │
│                                                       │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐│
│  │  Plasma     │   │  Hyprland   │   │  GNOME      ││
│  └─────────────┘   └─────────────┘   └─────────────┘│
│                   Edition selector                    │
└─────────────────────────────────────────────────────┘
```

### 2.2 Colour Scheme

| Element              | Hex       | Usage                           |
|----------------------|-----------|---------------------------------|
| Background           | `#1A1A2E` | Full-screen background          |
| Menu box bg          | `#16213E` | Boot entry container            |
| Menu box border      | `#0F3460` | Subtle border around menu       |
| Selected bg          | `#FFB300` | Currently highlighted entry     |
| Selected text        | `#1A1A2E` | Text on selected entry          |
| Normal text          | `#E8E8F0` | Unselected entry text            |
| Scroll indicator     | `#FFB300` | Scrollbar/indicator             |
| Edition badges       | See below | Edition-specific pill badges    |
| Timeline bar         | `#FFB300` | Auto-boot countdown bar         |

### 2.3 Edition Badge Colours

| Edition  | Hex       |
|----------|-----------|
| Plasma   | `#FFB300` |
| Hyprland | `#6A1B9A` |
| GNOME    | `#00897B` |

### 2.4 Typography

- **Menu entries**: Inter Regular, 16px, letter-spacing: 1px
- **Selected entry**: Inter Bold, 16px
- **Edition badges**: Inter Semi-Bold, 11px, uppercase
- **Version info**: JetBrains Mono Light, 10px

### 2.5 Dimensions

| Element              | Size             |
|----------------------|------------------|
| Menu width           | 480px (centred)  |
| Menu top margin      | 55% from top     |
| Entry height         | 40px             |
| Entry padding        | 8px 16px        |
| Icon mark            | 64×64px          |
| Icon top margin      | 20% from top     |
| Timeline bar height  | 3px              |
| Timeline bar width   | 180px            |

### 2.6 Icon
The Solus icon mark (see `logo/solus-icon.svg`) is displayed above the menu, rendered at 64×64px in Solus Amber (`#FFB300`) on the dark background.

---

## 3. Components

### 3.1 Background
- Full-screen background: deep gradient `#1A1A2E` → `#16213E`
- Optional: very subtle (3% opacity) hexagonal pattern overlay
- Solus wordmark (faint, 15% opacity) in bottom-right corner

### 3.2 Menu Box
- Rounded rectangle (radius: 8px)
- Background: `#16213E`
- Border: 1px `#0F3460`
- Box shadow: 0px 8px 32px rgba(0,0,0,0.4)

### 3.3 Entry States

| State    | Background       | Text Colour  | Left Border       |
|----------|------------------|--------------|-------------------|
| Normal   | Transparent      | `#E8E8F0`   | None              |
| Selected | `#FFB300`        | `#1A1A2E`   | None (full fill)  |
| Hover    | `#0F3460`        | `#FFB300`    | `#FFB300`, 3px    |

### 3.4 Auto-Boot Timeline
A horizontal progress bar at the bottom of the menu showing the auto-boot countdown:
- Colour: `#FFB300`
- Height: 3px
- Background track: `#0F3460`

### 3.5 Edition Selector Tabs
Small pill-shaped tabs below the menu for edition selection:
- Normal: `#0F3460` bg, `#C0C0D0` text
- Active: edition accent colour bg, `#FFFFFF` text
- Spacing: 8px between tabs

---

## 4. File Structure

```
grub/
├── grub-solus.cfg             # GRUB configuration with Solus branding
├── solus-grub-theme.md        # This design specification
├── theme/
│   ├── theme.txt              # GRUB theme definition
│   ├── background.png         # Background image (1920×1080)
│   ├── icons/                 # GRUB icons (drive, OS, etc.)
│   ├── Icons/
│   │   ├── solus.png          # Solus OS icon (48×48)
│   │   ├── solus-selected.png # Solus OS icon (selected state)
│   │   ├── ubuntu.png         # Ubuntu compatibility icon
│   │   └── windows.png        # Windows dual-boot icon
│   └── fonts/                 # Bundled fonts
│       ├── inter-regular-16.pf2
│       └── inter-bold-16.pf2
```

### 4.1 theme.txt Example

```
# Solus GRUB Theme
title-text: ""
title-color: "#FFB300"
title-font: "Inter Bold 18"
desktop-image: "background.png"
desktop-color: "#1A1A2E"
terminal-font: "Inter Regular 16"
terminal-left: 30%
terminal-top: 40%
terminal-width: 40%
terminal-height: 30%
terminal-border: 0
+ boot_menu {
    left = 30%
    top = 40%
    width = 40%
    height = 30%
    item_color = "#E8E8F0"
    item_height = 40
    item_spacing = 4
    item_padding = 8
    selected_item_color = "#1A1A2E"
    selected_item_bg = "#FFB300"
    item_pixmap_style = "menu-box.png"
    selected_item_pixmap_style = "menu-box-selected.png"
    scrollbar = true
    scrollbar_width = 4
    scrollbar_bg = "#0F3460"
    scrollbar_fg = "#FFB300"
}
+ progress_bar {
    id = "__timeout__"
    width = 400
    height = 3
    fg_color = "#FFB300"
    bg_color = "#0F3460"
    alignment = "center"
    x = 30%
    y = 75%
}
```

---

## 5. Installation

```bash
# Clone or copy the theme to GRUB's theme directory
sudo cp -r solus-grub /boot/grub/themes/solus

# Add to /etc/default/grub:
# GRUB_THEME="/boot/grub/themes/solus/theme.txt"
# GRUB_TIMEOUT=10
# GRUB_TIMEOUT_STYLE=menu

# Update GRUB
sudo update-grub
```

---

## 6. Dependencies

- **GRUB 2.04+** (for theme support)
- **grub-mkfont** (to generate .pf2 fonts if using custom fonts)
- **ImageMagick** (to convert SVG icons to PNG at build time)

---

## 7. Accessibility

- High contrast between selected/normal entries (amber on dark)
- Minimum text size: 16px (readable at 1080p+)
- Auto-boot progress visible via timeline bar
- Keyboard navigation fully supported (arrow keys + Enter)

---

*© 2026 Linux Solus Project. Licensed under GPL-3.0+.*
