# Solus GNOME — Desktop Design Overview

## Edition Identity
**Edition Name:** Solus GNOME  
**Design Language:** "Solus Refined"  
**Tagline:** *Simple. Beautiful. Yours.*  
**Target Audience:** Migrants from macOS, design-conscious users, touch/convertible users, simplicity-seekers

---

## 1. Design Philosophy — Solus Refined

Solus GNOME is a **curated GNOME experience** that balances GNOME's upstream vision with Solus's focus on usability and aesthetic polish:

| Pillar | Source | Applied To |
|--------|--------|------------|
| **GNOME Core UX** | GNOME Project | Workflow, shell, Activities overview |
| **Material Rounded** | Google M3 | Corner radius system, color, elevation |
| **Solus Curation** | Solus Design Team | Selective extensions, app theming, default layout |

**Core Tenets:**
1. **Simplicity is the ultimate sophistication** — distill to essentials
2. **Content is the interface** — chrome fades, content shines
3. **Gesture-native** — touchpad gestures are primary navigation
4. **Curated, not bloated** — every extension earns its place
5. **Migration-friendly** — macOS users feel at home instantly

---

## 2. Desktop Layout

### 2.1 Default Layout (macOS Inspired)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Activities  │  Firefox  │  Files  │  Terminal  │     🔍    🔊  🔋  │
│  [Top Bar — Global Menu Style]                  [System Indicators]  │
│                                                                      │
│                                                                      │
│     ┌───┐ ┌───┐ ┌───┐                                               │
│     │   │ │   │ │   │                    Desktop                     │
│     │ F │ │ C │ │ T │                    (Clean, no icons)           │
│     │ i │ │ o │ │ e │                                               │
│     │ r │ │ d │ │ r │                                               │
│     │ e │ │ e │ │ m │                                               │
│     │ f │ │   │ │   │                                               │
│     │ o │ │   │ │   │                                               │
│     │ x │ │   │ │   │                                               │
│     └───┘ └───┘ └───┘                                               │
│     [Dock — Auto-hide, bottom center]                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Top Bar

| Element | Spec |
|---------|------|
| Height | 32px |
| Background | Transparent (acrylic on desktop, solid in maximized apps) |
| Font | Inter 13px, Medium weight |
| Corners | Rounded (matches screen corners) |
| Opacity (acrylic) | 75% when on desktop, 100% in overview |

**Left side:**
- **Activities button** — Solus logo (16px), click opens overview, hover shows hot corner hint
- **App Menu** — Current application name + menu items (global menu style)

**Right side:**
- **System Indicators** — Network, Bluetooth, Volume, Battery (percentage)
- **Clock** — Format: `HH:mm` (click → calendar + notifications)
- **Quick Settings** — Toggle panel (Wi-Fi, Bluetooth, Dark Mode, Do Not Disturb)
- **User Menu** — Avatar, Settings, Lock, Logout, Suspend, Power Off

### 2.3 Dock (Dash to Dock — Curated)

| Element | Spec |
|---------|------|
| Position | Bottom, centered |
| Height | 56px |
| Width | Fits content (max 80% screen width) |
| Corner radius | 16px |
| Background | Acrylic (30px blur, 80% opacity) |
| Margin | 12px from bottom screen edge |
| Icon size | 40px |
| Icon padding | 8px |
| Hover effect | Icon lift + scale 1.1× |
| Active indicator | 2px dot below icon (accent color) |
| Auto-hide | Enable (default: off, user option in Settings) |

**Default dock items:**
1. Firefox
2. Files (Nautilus)
3. Terminal (GNOME Console)
4. Solus Software Center
5. System Settings
6. Trash (at far right, separator)

---

## 3. Shell Modifications — Solus GNOME Shell

### 3.1 GNOME Shell Theme (solus-shell.css)

- **Complete upstream GNOME Shell CSS re-theme** (see `solus-shell.css`)
- Unified corner radius: 12px (windows), 16px (shell dialogs), 24px (overview)
- Custom notification / quick settings styling
- Redesigned calendar popup
- Custom OSD styling (volume, brightness)
- Search entry styling in overview

### 3.2 Included Extensions

| Extension | Purpose | Solus Default Config |
|-----------|---------|---------------------|
| **Dash to Dock** | macOS-style dock | Bottom, centered, acrylic |
| **Blur My Shell** | Acrylic/blur effects for top bar, overview, and app grid | 30px blur, 80% opacity |
| **User Themes** | Load custom shell theme | Enabled, loads Solus theme |
| **AppIndicator and KStatusNotifierItem Support** | Systray icons (Discord, Slack, etc.) | Enabled |
| **GSConnect** | KDE Connect integration for GNOME | Enabled, auto-start |
| **Just Perfection** | UI tweaks (disable unwanted UI elements) | Disable downtimed reminders, disable workspace popup |
| **Sound Input & Output Device Chooser** | Quick audio device switching | Enabled in top bar |
| **Vitals** | System monitor (CPU, RAM, temp) | Added to top bar right side |
| **Tiling Assistant** | Window snap/tiling (mouse-driven) | Enable quarter tiling, snap assist |
| **Alphabetical App Grid** | Sort app grid alphabetically | Enabled |

### 3.3 Gesture Support

| Gesture | Action |
|---------|--------|
| Three-finger swipe up | Activities overview |
| Three-finger swipe down | Show desktop |
| Three-finger swipe left/right | Switch workspace |
| Four-finger pinch | Application grid |
| Two-finger swipe from right edge | Quick settings |
| Two-finger swipe from left edge | Notification center (future) |
| Edge drag (bottom) | Show dock (when auto-hide enabled) |

---

## 4. Color System

### 4.1 Adwaita-based with Solus Modifications

| Token | Light | Dark | Used For |
|-------|-------|------|----------|
| `@bg` | #FFFFFF | #1A1A2E | Windows, shell backgrounds |
| `@bg-secondary` | #F3F4F6 | #24243A | Sidebars, cards |
| `@bg-hover` | #E5E7EB | #2E2E46 | Hover state backgrounds |
| `@fg` | #1F2937 | #E4E4E7 | Primary text |
| `@fg-secondary` | #6B7280 | #9CA3AF | Secondary text |
| `@accent` | #3B82F6 | #60A5FA | Accent, primary actions |
| `@accent-hover` | #2563EB | #3B82F6 | Accent hover |
| `@border` | #D1D5DB | #3F3F5C | Borders, dividers |
| `@error` | #DC2626 | #EF4444 | Errors |
| `@success` | #16A34A | #22C55E | Success |
| `@warning` | #D97706 | #F59E0B | Warnings |

### 4.2 Accent Color Selection

Same 6-color palette as Solus Plasma (Solus Blue is default).  
Dynamic accent from wallpaper through `adw-gtk3` + Solus color extraction service.

---

## 5. Typography

- **Primary font:** Inter (UI), Noto Sans (fallback)
- **Monospace:** JetBrains Mono
- **Scale:** Follows GNOME upstream scale, with Inter substitutions
- **Font sizes:** GTK default 11pt (scales to 12pt Solus default)
- **Hinting:** Slight (Inter), Full (CJK)

---

## 6. Application Suite

### 6.1 Default Apps

| Purpose | Application | Notes |
|---------|-------------|-------|
| Web Browser | Firefox (Wayland) | Default search: DuckDuckGo, Solus homepage |
| File Manager | Nautilus | List view default, search always visible |
| Terminal | GNOME Console (kgx) | Simple, modern, adaptive |
| Text Editor | GNOME Text Editor | GTK4, adaptive |
| Settings | GNOME Control Center | Curated settings, Solus branding |
| Software | GNOME Software + Solus Plugin | Solus repository + Flatpak |
| Calendar | GNOME Calendar | Connected to Online Accounts |
| Music | GNOME Music / Spotify | Local + streaming |
| Videos | GNOME Videos (Totem) | Simple video player |
| Photos | Loupe (GNOME Image Viewer) | GTK4, fast |

### 6.2 Third-Party Recommended

- **VSCode** — Development
- **Discord** — Communication
- **Steam** — Gaming
- **Bitwarden** — Password manager
- **OBS Studio** — Recording/streaming

---

## 7. System Settings Organization

### 7.1 GNOME Control Center Panels

```
Settings ─────────────────────────────────┬─────────
├── 🌐 Network                            │ Quick toggle:
├── 🎨 Appearance                         │ • Dark Mode
│   ├── Wallpaper & Background            │ • Night Light
│   ├── Style (Light/Dark/ Auto)          │ • Location
│   ├── Accent Color                      │ • Bluetooth
│   └── Fonts                             │ • Do Not Disturb
├── 🔒 Privacy & Security                 │
├── 🖥️ Display & Monitor                  │
├── 🔊 Sound                              │
├── 🔋 Power & Battery                    │
├── 🎮 Mouse & Touchpad                   │
├── ⌨️ Keyboard                           │
├── 🖨️ Printers                           │
├── 📱 Removable Media                    │
├── 🔗 Online Accounts                    │
├── 🕐 Date & Time                        │
├── 🌍 Region & Language                  │
├── ♿ Accessibility                       │
├── 📦 Applications                       │
│   ├── Default Applications              │
│   ├── Removable Media                   │
│   └── Suspend & Power Buttons           │
├── 🛠️ About                              │
├── 🔄 Software Updates                   │
└── 🔧 Solus Extras                      │
    ├── Desktop Icons                     │
    ├── Dock Settings (Dash to Dock)      │
    └── Extensions Manager                │
```

### 7.2 Solus Extras Panel

Custom settings panel (installed via `solus-gnome-settings` package):
- **Dock settings** — Position, size, auto-hide, behavior
- **Extensions** — Enable/disable with descriptions
- **Desktop Icons** — Toggle visibility
- **Hot Corners** — Configure top-left corner action
- **Gesture** — Enable/disable specific gestures
- **Solus Branding** — About Solus version, links

---

## 8. Lock Screen & Login Screen (GDM)

### 8.1 Lock Screen Design

```
┌─────────────────────────────────────────────┐
│                                             │
│          🕐  15:30                           │
│          Wed 14 Apr 2026                    │
│                                             │
│          ╭─────────────────────╮            │
│          │  👤   John Doe      │            │
│          │  [ ● ● ● ● ● ● ● ] │            │
│          │  Enter password     │            │
│          ╰─────────────────────╯            │
│                                             │
│          [🔌 Suspend]  [🔒 Lock]  [⏻ Off]  │
│                                             │
│          📶 Wi-Fi    🔊 75%    🔋 98%       │
│                                             │
└─────────────────────────────────────────────┘
```

- Background: Wallpaper with 25px blur + 20% dark overlay
- Clock: 64px, light weight, centered
- Date: 14px, secondary text
- Card: 360px wide, 16px radius, acrylic with 30px blur
- Password entry: Inline, show last-chars on press
- Media controls: Album art + playback when media active
- Bottom bar: Status indicators (same as top bar)

### 8.2 GDM Theme (Solus GDM Theme)

- Solus-branded GDM login screen
- User list with avatars (horizontal carousel)
- Session selector: GNOME (default), GNOME Classic, GNOME on Xorg
- Accessibility icon in top-right (screen reader, zoom, on-screen keyboard)
- Power menu in top-right (Restart, Shut Down)

---

## 9. OOBE (GNOME Initial Setup)

### 9.1 Modified gnome-initial-setup Flow

1. **Welcome** — Language, keyboard, region
2. **Privacy** — Location services, crash reports
3. **Connectivity** — Join Wi-Fi network
4. **Account** — Create user, optional Online Accounts (Google)
5. **Appearance** — Light/Dark/Auto mode, accent color picker
6. **Desktop** — Dock position (bottom/left/right/auto-hide), toggle desktop icons
7. **Tour** — Gesture tutorial for trackpad users (3-finger swipe, workspace overview)
8. **Done** — "Welcome to Solus GNOME"

### 9.2 Tour Highlights

- 5-screen interactive gesture tutorial
- Demonstrates: Activities overview, workspace switching, app grid
- Touchscreen and trackpad variants
- Option to skip or replay from Help menu

---

## 10. Accessibility

### 10.1 Built-in GNOME Accessibility

| Feature | Activation | Notes |
|---------|-----------|-------|
| **Zoom** | Super+Alt+8 | 1×–10× magnification, mouse tracking |
| **Screen Reader** | Super+Alt+S | Orca screen reader |
| **High Contrast** | Super+Alt+H | Adwaita High Contrast theme |
| **Large Text** | Settings → Accessibility | 1.25× font scale |
| **Reduced Animation** | Settings → Accessibility | Disables shell animations |
| **Sticky Keys** | Settings → Accessibility | Shift 5× press enable |
| **Slow Keys** | Settings → Accessibility | Configurable delay |
| **On-screen Keyboard** | Settings → Accessibility | Auto-show on text focus |
| **Sound Keys** | Settings → Accessibility | Toggle sounds on caps/num lock |
| **Visual Alerts** | Settings → Accessibility | Flash screen for alerts |

### 10.2 Solus Extras

- **Cursor size:** Solus Large variant included by default
- **Dock accessibility:** Tab-navigable dock items
- **High contrast shell theme:** Variant of solus-shell.css with WCAG AAA contrast
- **Descriptive extension labels:** Each extension has plain-English explanation

---

## 11. Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Boot to desktop | < 5s | NVMe SSD, no network wait |
| Shell responsiveness | 60 FPS | Intel UHD 620+, smooth animations |
| RAM usage (idle) | < 800 MB | Clean boot, no cached apps |
| App launch (cold) | < 2s | Native apps, 1s Flatpak |
| Suspend/resume | < 2s | Modern hardware |

---

## 12. Consistency with macOS

| macOS Feature | Solus GNOME Equivalent |
|--------------|----------------------|
| Dock | Dash to Dock (bottom, auto-hide) |
| Menu Bar | Top bar + app menu |
| Spotlight | Overview search (Super key) |
| Mission Control | Activities overview (3-finger up) |
| Spaces | Workspaces (3-finger swipe) |
| Launchpad | Application grid (4-finger pinch) |
| Notification Center | Notification panel (top right click) |
| Control Center | Quick settings (top right) |
| System Settings | GNOME Control Center |
| Finder | Nautilus |
| Safari | Firefox |
| Terminal | GNOME Console |

---

## Appendix A: Package Dependencies

```
gnome-shell
gnome-console
gnome-control-center
gnome-software
gnome-calendar
gnome-music
gnome-totem
nautilus
loupe
firefox
dash-to-dock-gnome
blur-my-shell-gnome
gsconnect
just-perfection-gnome
vitals-gnome
tiling-assistant-gnome
sound-output-device-chooser
adw-gtk3
gnome-browser-connector
```

---

*Design Language Version: 1.0.0*  
*Last Updated: 2026-07-04*  
*Maintainer: Solus Desktop Team*
