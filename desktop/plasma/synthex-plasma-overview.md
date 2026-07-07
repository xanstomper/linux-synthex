# Synthex Plasma — Desktop Design Overview

## Edition Identity
**Edition Name:** Synthex Plasma  
**Design Language:** "Synthex Fluent Material"  
**Tagline:** *Familiar. Fluid. Flawless.*  
**Target Audience:** Migrants from Windows/macOS, general desktop users, gamers

---

## 1. Design Philosophy — Synthex Fluent Material

Synthex Plasma is a **fusion design language** that blends three pillars:

| Pillar | Source | Applied To |
|--------|--------|------------|
| **Fluent Design** | Microsoft | Acrylic/glass effects, reveal lighting, depth layers, motion |
| **Material Design 3 (M3)** | Google | Color system (dynamic color via KDE `AccentColor`), rounded corners (12dp), elevation via shadows, typography scale |
| **KDE Plasma Native** | KDE | Breeze framework, KWin compositor, Kirigami, Qt Quick Controls |

**Core Tenets:**
1. **Clarity over clutter** — every element has purpose. No redundant chrome.
2. **Depth with restraint** — elevation indicates hierarchy, not decoration.
3. **Motion with meaning** — animations communicate spatial relationships.
4. **Consistency without monotony** — unified design language that adapts to context.
5. **Migration-first** — Windows/macOS users should feel immediately at home.

---

## 2. Component Design System

### 2.1 Buttons

| Type | Height | Border Radius | Elevation | Use Case |
|------|--------|---------------|-----------|----------|
| **Filled** (Primary) | 40px | 8px | 1dp | Primary actions |
| **Filled** (Tonal) | 40px | 8px | 0dp | Secondary actions |
| **Outlined** | 40px | 8px | 0dp | Tertiary / low-emphasis |
| **Text** | 36px | 8px | 0dp | Subtle actions |
| **Icon only** | 40×40px | 8px | — | Toolbar, panel |
| **Chip** | 32px | 16px | — | Filter, tag, choice |

- Hover state: opacity overlay (8% white in dark, 8% black in light)
- Press state: ripple animation (400ms duration, Material Easing)
- Disabled: 38% opacity

### 2.2 Cards

| Variant | Padding | Border Radius | Elevation |
|---------|---------|---------------|-----------|
| **Elevated** | 16px | 12dp | 1dp (hover: 3dp) |
| **Filled** | 16px | 12dp | 0dp |
| **Outlined** | 16px | 12dp | 0dp |

Cards use:
- Full-bleed header images (16:9 aspect ratio, radius matches card top)
- Consistent 8px grid spacing for content
- Optional trailing actions aligned to bottom-right
- No border on elevated variant; 1px border on outlined variant (`Alpha 12%`)

### 2.3 Dialogs

| Component | Spec |
|-----------|------|
| Width | 560px (600px max for full-width) |
| Border radius | 16dp (top), matches window |
| Title | H5, 20px, bold |
| Body | Body 1, 16px, regular |
| Actions | Right-aligned, 8px gap |
| Scrim | 60% opacity black |
| Entry animation | Scale 0.95 → 1.0 + opacity 0→1, 200ms |
| Dismiss | Tap scrim OR Escape |

### 2.4 Input Fields

- Height: 56px (filled) / 48px (dense)
- Border radius: 8dp (outlined) / 4dp top (filled)
- Label: floating label (M3 style, 12px when active)
- Active indicator: 2px underline (accent color)
- Error state: red underline + helper text below
- Helper text: 12px, 8px below field

### 2.5 Navigation

- **Sidebar:** 280px wide, icons + labels, active indicator (4px accent bar on left)
- **Top bar:** 48px height, centered window controls, centered app title
- **Breadcrumbs:** 14px, slash separator, last item bold
- **Tabs:** 48px height, underline indicator (2px, accent color), scrollable

---

## 3. Color System

### 3.1 Accent Colors

Synthex Plasma uses a **6-color accent palette** that users can choose from in System Settings. Default accent: **Synthex Blue**.

| Name | Light Hex | Dark Hex | Role |
|------|-----------|----------|------|
| **Synthex Blue** | #3B82F6 | #60A5FA | Primary / accent |
| **Synthex Green** | #10B981 | #34D399 | Success, positivity |
| **Synthex Amber** | #F59E0B | #FBBF24 | Warning |
| **Synthex Red** | #EF4444 | #F87171 | Error, danger |
| **Synthex Purple** | #8B5CF6 | #A78BFA | Creative / optional |
| **Synthex Teal** | #14B8A6 | #2DD4BF | Info / optional |

All accents meet WCAG AA contrast on both surfaces (light: #FFFFFF, dark: #1E1E2E).

### 3.2 Semantic Colors

| Token | Light | Dark | Purpose |
|-------|-------|------|---------|
| `Surface` | #FFFFFF | #1E1E2E | Window backgrounds |
| `SurfaceVariant` | #F3F4F6 | #2A2A3C | Card, sidebar |
| `SurfaceDim` | #E5E7EB | #16162A | Dropdown, menus |
| `OnSurface` | #1F2937 | #E4E4E7 | Primary text |
| `OnSurfaceVariant` | #6B7280 | #9CA3AF | Secondary text |
| `Outline` | #D1D5DB | #3F3F5C | Borders, dividers |
| `Scrim` | #000000 40% | #000000 60% | Overlay |
| `Error` | #DC2626 | #EF4444 | Errors |
| `Success` | #16A34A | #22C55E | Success states |

### 3.3 Dark / Light Mode

- Automatic switching via KDE `Night Color` integration
- Dark mode active: sunset to sunrise
- User can override per-app in System Settings
- Transition: 500ms crossfade on all color tokens (requires Qt 6.7+)

---

## 4. Typography

### 4.1 Family Stack

| Role | Primary Font | Fallback | Weight Range |
|------|-------------|----------|-------------|
| UI (labels, body) | Inter | Noto Sans, system-ui | 400–700 |
| Display (headers) | Inter | Noto Sans Display | 500–800 |
| Monospace | JetBrains Mono | Noto Sans Mono, monospace | 400–700 |

### 4.2 Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Used For |
|-------|------|--------|-------------|----------------|----------|
| Display L | 57px | 700 | 64px | -0.25px | Wallpaper quotes, OOBE |
| Display M | 45px | 700 | 52px | 0 | Welcome header |
| Display S | 36px | 600 | 44px | 0 | Page titles |
| Headline L | 32px | 600 | 40px | 0 | Section headers |
| Headline M | 28px | 600 | 36px | 0 | Dialog titles |
| Headline S | 24px | 600 | 32px | 0 | Card titles |
| Title L | 22px | 500 | 28px | 0 | App launcher items |
| Title M | 16px | 500 | 24px | 0.15px | List titles |
| Title S | 14px | 500 | 20px | 0.1px | Small list titles |
| Body L | 16px | 400 | 24px | 0.5px | Reading content |
| Body M | 14px | 400 | 20px | 0.25px | Default UI text |
| Body S | 12px | 400 | 16px | 0.4px | Captions, helper |
| Label L | 14px | 500 | 20px | 0.1px | Button text |
| Label M | 12px | 500 | 16px | 0.5px | Tab labels |
| Label S | 11px | 500 | 16px | 0.5px | Badges, overline |

### 4.3 Font Rendering

- Hinting: `slight` (Inter) / `full` (Noto Sans CJK)
- Subpixel: `rgb` (LCD) / `grayscale` (OLED)
- DPI: 96 (default), auto-detect on HiDPI

---

## 5. Iconography

### 5.1 Synthex Icon Pack

**Base:** Tela-circle (adapted and curated for Synthex)
**Format:** SVG + PNG (16×16, 22×22, 24×24, 32×32, 48×48, 64×64, 128×128, 256×256)
**Style:** 

- **Filled** outlines for active states
- **Line-art** (2px stroke) for default states
- **Rounded** corners (cap: round, join: round)
- **Accent-aware** — monochrome icons use current color, multi-color use accent palette

### 5.2 Icon Categories

| Category | Folder | Example |
|----------|--------|---------|
| Applications | `apps/` | Firefox, Nautilus, Terminal |
| Actions | `actions/` | Open, Save, Delete, Share |
| Devices | `devices/` | Monitor, Keyboard, Harddisk |
| Emblems | `emblems/` | Important, Favorite, Read-only |
| Mime Types | `mimetypes/` | Text, Image, PDF, Archive |
| Places | `places/` | Home, Desktop, Downloads, Trash |
| Status | `status/` | Battery, Bluetooth, Network, Volume |

### 5.3 Icon Theme Inheritance

```
Synthex → Tela-circle → Tela → Papirus → Breeze → Adwaita → hicolor
```

---

## 6. Spacing and Grid System

### 6.1 Base Unit: 8px

All spacing is a multiple of 8px: 4, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96.

| Token | Value | Use |
|-------|-------|-----|
| `spacing-xs` | 4px | Icon-to-text inside button |
| `spacing-sm` | 8px | Grid gap, list item padding |
| `spacing-md` | 16px | Card padding, section margins |
| `spacing-lg` | 24px | Panel spacing, modal padding |
| `spacing-xl` | 32px | Section grouping |
| `spacing-2xl` | 48px | Major layout sections |
| `spacing-3xl` | 64px | Page margins (wide) |

### 6.2 Layout Grid

- **Content max-width:** 1200px (centered)
- **Column grid:** 12 columns (72px each + 24px gutter)
- **Sidebar:** 280px fixed
- **Detail pane:** min 400px, fills remaining

---

## 7. Animation Guidelines

### 7.1 Bezier Curves

| Curve Name | Bézier Values | Used For |
|------------|--------------|----------|
| **Material Emphasized** | `cubic-bezier(0.2, 0.0, 0.0, 1.0)` | Enter / exit transitions |
| **Material Emphasized Decel** | `cubic-bezier(0.05, 0.7, 0.1, 1.0)` | Enter (decelerate) |
| **Material Emphasized Accel** | `cubic-bezier(0.3, 0.0, 0.8, 0.15)` | Exit (accelerate) |
| **Standard** | `cubic-bezier(0.4, 0.0, 0.2, 1.0)` | Hover, press, focus |
| **Linear** | `cubic-bezier(1, 1, 0, 0)` | Color transitions only |

### 7.2 Durations

| Context | Duration | Curve |
|---------|----------|-------|
| Window open | 200ms | Emphasized Decel |
| Window close | 150ms | Emphasized Accel |
| Page transition | 300ms | Emphasized Decel |
| Hover state | 100ms | Standard |
| Press ripple | 400ms | Standard |
| Color swap (dark mode) | 500ms | Linear |
| Panel auto-hide | 250ms | Standard |

---

## 8. Glass / Acrylic Effects

### 8.1 Material Types

| Material | Blur | Tint Opacity | Used On |
|----------|------|-------------|---------|
| **Acrylic (base)** | 30px | 80% Surface | Panels, sidebars |
| **Acrylic (thick)** | 60px | 90% Surface | Notifications, flyouts |
| **Mica** | 15px | 70% Wallpaper | Window titlebar (optional) |
| **Smoke** | 0px | 95% Surface + thin border | Dialog backdrop |

### 8.2 Implementation

- KWin blur effect required (`kwin-effect-blur`)
- Acrylic surfaces use `Color` → `Blur` → `Noise` shader stack
- Performance fallback: solid color with 1px outline (when compositor blur disabled)

---

## 9. Panel Design

### 9.1 Default Layout (Windows 11 Inspired)

```
┌──────────────────────────────────────────────────────────────────┐
│  ☰ Apps |  🌐 Firefox |  📁 Files |  …  |    🔍     │ 🕐 │ 🔊 │ 🌐 │ 🔋 │ ⋯ │ 👤 │
│  [Launcher]  [Pinned Apps]        [Search]     [System Tray]     │
└──────────────────────────────────────────────────────────────────┘
```

**Panel Spec:**
- Position: Bottom edge, centered
- Height: 48px (dense) / 52px (default) / 56px (large)
- Width: 96% of screen (max 1600px)
- Corner radius: 8dp (rounded panel)
- Margin: 8px from each screen edge
- Background: Acrylic (30px blur, 80% opacity)
- Opacity: 100%

### 9.2 Widgets (Left to Right)

1. **Application Launcher** — Synthex-branded kickoff replacement (48×48px icon)
2. **Pinned Apps** — Firefox, Files (Dolphin), Terminal (Konsole), System Settings
3. **Running Apps Indicator** — Underline (2px, accent) for active, dot for background
4. **Spacer** (elastic)
5. **Search / KRunner** — Click to open, compact icon (24×24px)
6. **System Tray:**
   - Clock (custom: "Mon 14 Apr — 15:30" format)
   - Volume (systray)
   - Network (systray)
   - Bluetooth (systray)
   - Battery (systray with percentage)
   - User avatar (24×24px circle)
   - Application menu (⋮) → Desktop pager, Lock, Logout, Settings

### 9.3 macOS Style Alternative

- Panel positioned at top
- Apple-style global menu (left-aligned)
- Dock at bottom (auto-hide) with magnification
- Configurable in First Boot Wizard

---

## 10. Application Launcher

### 10.1 Design

**Style:** Sidebar + full-height grid (Synthex-specific fork of Kicker)

```
┌──────────────────────────────────────────────────────────────┐
│ 🔍 Search apps, settings, files…                    │ ✕ │
├───────┬──────────────────────────────────────────────────────┤
│       │                                                      │
│  ◉ All │  [Grid of app icons — 6 columns × 5 rows]          │
│  📁 Apps│                                                      │
│  ⚙️ Settings│  Firefox  Files  Terminal  Settings  Help        │
│  📂 Files│  GIMP    VLC    Steam    Discord  OBS            │
│  🔌 Devices│  …                                                │
│       │                                                      │
│       │                                                      │
│       │  [Power] [Lock] [Logout] [Sleep]      👤 username    │
├───────┴──────────────────────────────────────────────────────┤
│  Recently used:  Chrome  |  VSCode  |  Calculator            │
└──────────────────────────────────────────────────────────────┘
```

**Dimensions:**
- Width: 750px (scales to 70% screen width on small displays)
- Height: 80% of screen height
- Border radius: 16dp
- Background: Acrylic (30px blur)
- Entry animation: Bottom slide-up + fade (200ms, Emphasized Decel)

### 10.2 Behavior

- **Search:** Instant filtering, fuzzy match, category headers shown inline
- **Categories:** Pinned sidebar with icons, scrollable
- **Keyboard navigation:** Arrow keys, type to search, Enter to launch
- **Right-click:** Add to desktop, Add to panel, Pin to launcher, Open with…
- **Recently used:** Last 10 unique apps (scrollable row at bottom)

---

## 11. System Settings Organization

### 11.1 Categories (Top Level)

```
⚙️ Settings  ───────────────────────────────────────────────
├── 🖥️  Appearance         → Theme, Colors, Fonts, Icons, Cursor
├── 🎨 Personalization    → Wallpaper, Lock Screen, Splash Screen
├── 🔗 Network            → Wi-Fi, Ethernet, VPN, Proxy
├── 🎮 Hardware           → Display, Audio, Input, Printing, Bluetooth
├── 🕒 System             → Date/Time, Region, Users, Power Management
├── 📱 Applications       → Default Apps, Notifications, File Associations
├── 🛡️ Privacy & Security → Firewall, Auth, KDE Wallet, Location
├── 🌐 Online Accounts    → Google, Microsoft, Nextcloud, ownCloud
├── 🎯 Desktop            → Virtual Desktops, Screen Edges, Window Rules
└── ❓ Help & About       → System Info, Updates, Support
```

### 11.2 Design

- **Two-pane layout:** Category list (240px) + Content pane
- **Content pane:** Uses Kirigami Cards pattern
- **Search:** Always visible top bar, searches across all settings
- **Breadcrumb:** Category > Subcategory in toolbar area

---

## 12. Window Decoration Design

### 12.1 Titlebar (Synthex Aurorae Theme)

| Element | Spec |
|---------|------|
| Height | 36px (dense) / 40px (default) |
| Corner radius | 12dp (rounded top corners) |
| Background | Acrylic (15px blur with Mica) OR SurfaceVariant |
| Active title | 13px SemiBold, OnSurface |
| Inactive title | 13px SemiBold, OnSurfaceVariant 60% |
| Buttons | macOS-style traffic light: 🟢 🟡 🔴 (left-aligned) |
| Button style | Filled circle (24px), hover expands to 28px |
| Customization | Can switch to Windows-style (right-aligned) in Settings |

### 12.2 Window Controls

- **Close:** Red (#EF4444) filled circle
- **Minimize:** Amber (#F59E0B) filled circle
- **Maximize:** Green (#10B981) filled circle
- On hover: circles scale up 1.15×, tooltip appears to right
- Double-click titlebar: maximize/restore (configurable)
- Snap: Drag to top edge = maximize, left/right = half-screen, corner = quarter

---

## 13. Notification Center

### 13.1 Design

```
┌──────────────────────────────┐
│  Notifications  ⋮  ✕  │
│  ────────────────────────  │
│  │ 📧 Thunderbird        │  │
│  │ New email: "Meeting…" │  │
│  │ 2 min ago       [✕] │  │
│  ├────────────────────────┤  │
│  │ 🔄 System Update      │  │
│  │ 12 updates available  │  │
│  │ [Restart Later] [Update]│ │
│  ├────────────────────────┤  │
│  │ ▶️ Media Player       │  │
│  │ Song — Artist          │  │
│  │ [⏮] [⏸] [⏭]           │  │
│  └──────────────────────────────┘
```

**Specs:**
- Width: 380px
- Max height: 70% of screen
- Trigger: Panel notification icon OR Super+N
- Background: Acrylic (30px blur)
- Border radius: 12dp (left side)
- Notification max width: 360px
- Groups by app, expandable

### 13.2 Interactive Actions

- Each notification: icon + title + body + timestamp + dismiss (✕)
- Inline reply for messaging apps
- Media controls persistent at bottom when media playing
- "Do Not Disturb" toggle in header
- Clear all button

---

## 14. Lock Screen / Login Screen (SDDM)

### 14.1 Lock Screen Design

```
┌─────────────────────────────────────────────┐
│                                             │
│          ╭─────────────────────╮            │
│          │                     │            │
│          │   👤 User Avatar    │            │
│          │                     │            │
│          ├─────────────────────┤            │
│          │  John Doe           │            │
│          │  john@synthex.local   │            │
│          ├─────────────────────┤            │
│          │  [ ● ● ● ● ● ● ● ] │            │
│          │  Enter password     │            │
│          ├─────────────────────┤            │
│          │  [Unlock] [Switch…] │            │
│          ╰─────────────────────╯            │
│                                             │
│  🔋 98%   |   📶 Wi-Fi   |   🕐 15:30      │
│  Wed 14 Apr 2026                            │
└─────────────────────────────────────────────┘
```

**Specs:**
- Background: Wallpaper with 20px blur overlay + 30% dark tint
- Card: Acrylic (30px blur), 16dp border radius, 400px wide
- Avatar: 96×96px circle with 2px accent border
- Clock: Display S (36px), centered
- Date: Body L, OnSurfaceVariant
- Multi-user: Avatar carousel (horizontal scroll)
- Media controls: Music artwork + playback controls (compact, below card)

### 14.2 Login Screen (SDDM Synthex Theme)

- Same card layout as lock screen
- User list (vertical, scrollable) on left side
- Session selector (Plasma/Hyprland/GNOME) on right
- Accessibility button (bottom-left): screen reader, zoom, sticky keys
- Power button (bottom-right): Shut down, Restart

---

## 15. OOBE (Out of Box Experience)

### 15.1 First Boot Wizard Flow

```
1. Welcome         → Language, Keyboard Layout, Region
2. Network         → Connect to Wi-Fi / Ethernet (skip optional)
3. Privacy         → Location services, Crash reporting, Usage stats
4. Account         → Create user account + password
5. Desktop Style   → Choose layout: Windows 11 style / macOS style / Classic
6. Accent Color    → Pick from 6 accent colors
7. Dark Mode       → Light / Dark / Auto
8. Software        → Optional: Install recommended apps (browser, codec, office)
9. Tour            → Optional: Interactive desktop walkthrough
10. Done           → "Welcome to Synthex Plasma!"
```

### 15.2 Design

- Full-screen progressive wizard
- Background: Animated gradient wallpaper (Synthex brand colors)
- Card: Centered, 640px width, acrylic background
- Step indicator: Dots at bottom (current step highlighted)
- Navigation: Back / Next buttons, keyboard arrows
- Each step preserves state if user navigates back

---

## 16. Accessibility Guidelines

### 16.1 Visual

- **High Contrast:** Built-in KDE High Contrast theme, WCAG AAA target
- **Font Scaling:** 100%–200% in 10% increments
- **Cursor:** Synthex Large cursor variant (48px) included
- **Reduce Motion:** Disable animations, reduce blur
- **Color Filters:** Deuteranopia, protanopia, tritanopia presets

### 16.2 Motor

- **Sticky Keys:** Toggle with Shift 5×
- **Slow Keys:** Delay before key acceptance (configurable: 0.3–2.0s)
- **Mouse Keys:** Numeric keypad controls pointer
- **Click Assist:** Hover-to-click, dwell clicking (configurable dwell time)
- **On-screen Keyboard:** KDE Plasma's built-in OSK

### 16.3 Hearing

- **Visual Alerts:** Screen flash for audio alerts
- **Captions:** System-wide captions toggle (where supported)

### 16.4 Cognitive

- **Notification cooldown:** Prevent notification flood
- **Focus mode:** Disable non-critical popups for X minutes
- **Simplified layout:** Option for reduced UI density

---

## 17. Consistency with Windows / macOS for Migration

| Feature | Windows Equivalent | macOS Equivalent | Synthex Plasma |
|---------|-------------------|-------------------|--------------|
| Taskbar | Taskbar | Dock | Bottom panel with acrylic |
| Start Menu | Start Menu | Launchpad | Synthex app launcher (sidebar + grid) |
| File Explorer | File Explorer | Finder | Dolphin (custom Synthex theme) |
| Settings | Settings | System Settings | System Settings (categorized) |
| Notification Center | Action Center | Notification Center | Custom notification panel |
| Spotlight | Search | Spotlight | KRunner (search + calculator + web) |
| Snap Layouts | Snap Layouts | Window Manager | KWin snap (top/corner drag) |
| Alt+Tab | Alt+Tab | Cmd+Tab | KDE task switcher (thumbnail grid) |
| Virtual Desktops | Task View | Mission Control | KDE Virtual Desktops (grid overview) |
| Control Panel | Control Panel | System Settings | System Settings |
| Widgets | Widgets Board | Dashboard (F12) | Plasma widgets (sidebar + desktop) |

---

## Appendix A: Design Tokens Reference

Tokens defined as JSON for developer consumption (stored in `/usr/share/synthex/plasma/tokens/`):

- `color-tokens.json` — Full color palette (light + dark)
- `type-tokens.json` — Type scale with font families
- `elevation-tokens.json` — Shadow definitions
- `spacing-tokens.json` — Spacing scale
- `motion-tokens.json` — Animation curves and durations

---

*Design Language Version: 1.0.0*  
*Last Updated: 2026-07-04*  
*Maintainer: Synthex Desktop Team*
