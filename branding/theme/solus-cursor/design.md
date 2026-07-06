# Solus Cursor Theme — Design Specification

> Version 1.0 | July 2026  
> Part of the Linux Solus Brand Identity

---

## 1. Overview

The Solus cursor theme provides a polished, modern cursor set consistent with the Solus brand aesthetic. The design blends subtle amber accents into the cursor core while maintaining high visibility and comfort.

---

## 2. Design Philosophy

- **Modern but familiar**: Based on the Breeze cursor silhouette (KDE default) — users won't feel disoriented
- **Brand-consistent**: Subtle Solus brand colours integrated into core cursors (amber highlight, deep blue outline)
- **High visibility**: 2px outline ensures contrast on any background
- **Smooth animation**: 60fps animation for busy/waiting cursors
- **Scalable**: SVG source → rendered at multiple PNG sizes (24×24, 32×32, 48×48, 64×64)

---

## 3. Colour Palette

| Token         | Hex       | Usage                              |
|---------------|-----------|------------------------------------|
| Fill          | `#FFFFFF` | Primary cursor body                |
| Outline       | `#1A1A2E` | Dark outline for contrast          |
| Accent        | `#FFB300` | Brand accent (dot, edge highlight) |
| Accent Outline| `#E6A000` | Darker accent for contrast         |
| Shadow        | `#000000` | Drop shadow at 30% opacity         |
| Wait Fill     | `#1A1A2E` | Busy cursor fill                   |
| Wait Accent   | `#FFB300` | Busy cursor animated element       |

---

## 4. Cursor Sizes

| Size    | Use Case                    |
|---------|-----------------------------|
| 24×24   | Small displays (< 1366×768) |
| 32×32   | Standard (1080p default)    |
| 48×48   | High-DPI (1440p)            |
| 64×64   | HiDPI (4K with scaling)     |

---

## 5. Cursor Catalog

### 5.1 Standard Cursors

| Cursor Name            | SVG Base         | Description                        |
|------------------------|------------------|------------------------------------|
| `left_ptr`             | arrow            | Standard arrow pointer             |
| `right_ptr`            | arrow-right      | Right-pointing arrow               |
| `hand` / `hand2`       | hand             | Link pointer (open hand)           |
| `hand1`                | hand-pointing    | Pointing finger                    |
| `ibeam`                | text             | Text selection (I-beam)            |
| `xterm`                | text-thick       | Thick text cursor                  |
| `cross`                | cross            | Crosshair                          |
| `crosshair`            | crosshair        | Precision crosshair                |
| `move`                 | move             | Quad-arrow move cursor             |
| `all-scroll`           | move             | Same as move (GNOME compat)        |
| `resize-n`             | up-arrow         | Resize north                       |
| `resize-s`             | down-arrow       | Resize south                       |
| `resize-e`             | right-arrow      | Resize east                        |
| `resize-w`             | left-arrow       | Resize west                        |
| `resize-ne`            | ne-resize        | Resize north-east                  |
| `resize-nw`            | nw-resize        | Resize north-west                  |
| `resize-se`            | se-resize        | Resize south-east                  |
| `resize-sw`            | sw-resize        | Resize south-west                  |
| `ns-resize` / `size_ver`| v-resize        | Vertical resize                    |
| `ew-resize` / `size_hor`| h-resize        | Horizontal resize                  |
| `nesw-resize`          | bd-resize        | Diagonal (NE/SW)                   |
| `nwse-resize`          | fd-resize        | Diagonal (NW/SE)                   |

### 5.2 Animated Cursors

| Cursor Name            | SVG Base         | Frames | Loop | Description            |
|------------------------|------------------|--------|------|------------------------|
| `wait`                 | wait             | 60     | yes  | Clock/hourglass        |
| `watch`                | watch            | 60     | yes  | Spinning indicator     |
| `progress`             | progress         | 30     | yes  | Arrow + spinner        |
| `busy`                 | busy             | 30     | yes  | Spinning ring          |

### 5.3 Special Cursors

| Cursor Name            | Description                        |
|------------------------|------------------------------------|
| `pencil`               | Precision drawing                  |
| `copy`                 | Copy indicator (arrow + + sign)    |
| `alias`                | Link/alias indicator               |
| `context-menu`         | Menu indicator                     |
| `dnd-none`             | Drag-and-drop not allowed          |
| `dnd-copy`             | Drag-and-drop copy                 |
| `dnd-move`             | Drag-and-drop move                 |
| `dnd-link`             | Drag-and-drop link                 |
| `grabbing`             | Active drag (closed hand)          |
| `zoom-in`              | Magnifying glass with +            |
| `zoom-out`             | Magnifying glass with -            |
| `help`                 | Question mark (help support)       |
| `no-drop` / `circle`   | Prohibited/unavailable             |

---

## 6. Cursor Design Details

### 6.1 Arrow (left_ptr)
```
     ┌───┐
     │ W │  ← White fill (#FFFFFF)
     │ W │
    ┌┘ W └┐
    │  W   │
    │  W   │
   ┌┘  W   └┐
   │   W    │
 ┌─┘   W    └─┐
 │    A A     │  ← Amber accent corner (#FFB300)
 │    A A     │
 │    W W     │
 └────┘ └────┘
Outline: #1A1A2E, 1.5px
Accent: bottom-right corner wedge in #FFB300
Shadow: 1px right/down, #000000 20%
```

### 6.2 Text (ibeam)
```
     ┌────┐
     │ W  │
     │ W  │
 ────┘ A  └────   ← Amber accent at top/bottom
     │ W  │
     │ W  │
     │ W  │
     │ W  │
 ────┐ A  ┌────   ← Amber accent at top/bottom
     │ W  │
     │ W  │
     └────┘
Outline: #1A1A2E, 1.5px
Width: 4px (standard), 6px (xterm thick)
```

### 6.3 Watch (wait) - Animated
```
Frame 1-30:  Ring rotates clockwise
             Outer ring: #1A1A2E outline
             Inner arc: #FFB300, sweeping 0°→360°
Frame 31-60: Arc completes, fades out
             New arc appears, rotates 180° offset
Pattern: Continuous smooth rotation at 60fps
```

---

## 7. File Structure

```
solus-cursor/
├── design.md                # This design specification
├── cursors/                 # Symlink farm pointing to PNG files
│   ├── left_ptr          → ../build/24/left_ptr.png
│   ├── hand2             → ../build/24/hand.png
│   ├── ... symlinks for all $X_CURSOR names
│   └── default           → left_ptr
├── svg/                     # Source SVG files for each cursor
│   ├── arrow.svg
│   ├── hand.svg
│   ├── text.svg
│   ├── cross.svg
│   ├── move.svg
│   ├── resize-h.svg
│   ├── resize-v.svg
│   ├── resize-ne.svg
│   ├── resize-nw.svg
│   ├── wait.svg
│   ├── progress.svg
│   └── ...
├── build/                   # Generated PNG files
│   ├── 24/
│   ├── 32/
│   ├── 48/
│   └── 64/
├── theme.conf               # XCursor theme configuration
└── Makefile                 # Build script (SVG → PNG → xcursor)
```

### theme.conf
```
[Icon Theme]
Name=Solus Cursors
Comment=Solus branded cursor theme with amber accents
Inherits=breeze_cursors
Example=left_ptr
```

---

## 8. Build Process

```bash
# Requirements: inkscape, xcursorgen, python3
make all

# Generates:
# - PNG files at 24/32/48/64px from SVGs
# - XCursor file with all size variants
# - Symlink farm in cursors/

# Install:
sudo make install
# Installs to /usr/share/icons/Solus-Cursors/
```

---

## 9. Installation

```bash
# System-wide
sudo cp -r solus-cursor /usr/share/icons/Solus-Cursors

# Per-user
cp -r solus-cursor ~/.local/share/icons/Solus-Cursors

# Activate (KDE Plasma):
# System Settings → Appearance → Cursors → Solus Cursors

# Activate (GNOME):
gsettings set org.gnome.desktop.interface cursor-theme 'Solus-Cursors'

# Activate (Hyprland):
# exec-once = hyprctl setcursor Solus-Cursors 24

# Activate (i3/Sway):
# exec_always xsetroot -cursor_name left_ptr
# And set in config: set $cursor-theme Solus-Cursors
```

---

## 10. Compatibility

- **X11**: Full support via XCursor format
- **Wayland**: Supported (tested on KWin/Wayland, Hyprland, Sway)
- **GTK**: Inherits system cursor theme
- **Qt**: Inherits system cursor theme

---

*© 2026 Linux Solus Project. Licensed under GPL-3.0+.*
