# Solus Hyprland — Desktop Design Overview

## Edition Identity
**Edition Name:** Solus Hyprland  
**Design Language:** "Solus Dynamic Tiling"  
**Tagline:** *Power. Performance. Precision.*  
**Target Audience:** Power users, developers, tiling WM enthusiasts, lightweight-focused users

---

## 1. Design Philosophy — Solus Dynamic Tiling

Solus Hyprland merges three design pillars:

| Pillar | Source | Applied To |
|--------|--------|------------|
| **Dynamic Tiling** | Hyprland/ dwm | Automatic window management, master-stack layouts |
| **Material You** | Google/M3 | Color extraction from wallpaper, rounded corners, elevation |
| **Solus Minimal** | Solus Design Team | Reduced chrome, keyboard-first, information-dense |

**Core Tenets:**
1. **Keyboard-first, mouse-optional** — every action has a keybind
2. **Automatic layout** — windows manage themselves, you manage tasks
3. **Performance everywhere** — no compositor lag on integrated GPUs
4. **Aesthetic restraint** — borderless glass, minimal chrome, maximum content
5. **Workspaces as workflows** — one workspace per task group

---

## 2. Workspace and Layout System

### 2.1 Default Workspace Layout

| Workspace | Name | Default Layout | Purpose |
|-----------|------|---------------|---------|
| 1 | Main | Master (70/30) | Primary work (browser + editor) |
| 2 | Communication | Dwindle | Chat, mail, meetings |
| 3 | Terminal | Master (50/50) | Terminal windows, SSH sessions |
| 4 | Media | Dwindle | Music, video, images |
| 5 | Code | Dwindle | IDE, dev tools |
| 6 | Scratch | Master (60/40) | Temporary windows |

### 2.2 Layouts

| Layout | Behavior | Bind |
|--------|----------|------|
| **Master** | One large master area + slave stack on side | `Super+Ctrl+M` |
| **Dwindle** | Recursive split — each new window splits the focused one | `Super+Ctrl+D` |
| **Center** | Windows open centered, floating by default | `Super+Ctrl+C` |
| **Float** | All windows floating, manual placement | `Super+Ctrl+F` |

### 2.3 Layout Parameters

- Master layout split ratio: 0.70 (default)
- Gaps: interior 8px, exterior 10px, between monitors 20px
- Disable gaps for maximized: true
- Smart gaps (only when >1 window): true

---

## 3. Visual Design

### 3.1 Window Borders & Corners

| Element | Value |
|---------|-------|
| Active border | 2px (accent color, current wallpaper palette) |
| Inactive border | 1px (SurfaceVariant, 40% opacity) |
| Corner radius | 12px (active), 8px (inactive) |
| Shadow | 10px spread, 10px offset, 35% opacity black |
| No titlebar | Enabled by default (window title in Waybar) |

### 3.2 Color System

**Primary palette** extracted dynamically from wallpaper (via `hyprpicker` + `pywal` integration).  
**Fallback palette** (no wallpaper extraction):

| Token | Light Theme | Dark Theme | Used For |
|-------|-------------|------------|----------|
| Background | #F8F9FA | #0F0F1A | Wallpaper background |
| Surface | #FFFFFF | #1A1A2E | Windows |
| SurfaceVariant | #F0F0F5 | #242438 | Waybar, notifications |
| Primary | #3B82F6 | #60A5FA | Active borders, accent |
| OnSurface | #1F2937 | #E4E4E7 | Text |
| OnSurfaceVariant | #6B7280 | #9CA3AF | Dim text, labels |
| Error | #EF4444 | #F87171 | Errors |

### 3.3 Blur & Transparency

| Element | Blur Amount | Opacity |
|---------|-------------|---------|
| Waybar | 20px | 85% |
| Notifications (mako) | 25px | 90% |
| Wofi launcher | 25px | 90% |
| Floating windows | 10px (background only) | 95% |
| Terminal (kitty) | 15px | 90% |

### 3.4 Animations

| Property | Duration | Curve | Style |
|----------|----------|-------|-------|
| Window open | 150ms | bezier(0.05, 0.7, 0.1, 1.0) | Slide up + fade |
| Window close | 100ms | bezier(0.3, 0.0, 0.8, 0.15) | Slide down + fade |
| Window move | 200ms | bezier(0.4, 0.0, 0.2, 1.0) | Smooth translate |
| Workspace switch | 250ms | bezier(0.4, 0.0, 0.2, 1.0) | Slide horizontal |
| Border highlight | 80ms | bezier(0.0, 0.0, 0.2, 1.0) | Instant fade |
| Gaps change | 300ms | bezier(0.25, 0.1, 0.25, 1.0) | Smooth resize |

---

## 4. Waybar Panel Design

### 4.1 Layout

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│  ▸ 1 ●  2 ○  3 ○  4 ○  5 ○  6 ○  |  Firefox  •  Code  •  Terminal  |  15:30  Mon 14 Apr │
│  [Workspaces]                          [Active Window]                          [Clock]  │
│                                            🔊 75%  📶 ████  🔋 98%                 │
│                                            [System Tray]                            │
└───────────────────────────────────────────────────────────────────────────────────┘
```

**Specs:**
- Position: Top edge
- Height: 36px (default) / 32px (compact) / 40px (cozy)
- Width: 100%
- Background: SurfaceVariant with 20px blur, 85% opacity
- Corner radius: 0px (full width) or 12px (floating, with 8px margin)
- Font: Inter 13px, Medium weight
- Module spacing: 12px

### 4.2 Modules (Left to Right)

1. **Workspaces** — Active highlighted by accent, urgent pulsing red
2. **Active Window** — Truncated title of focused window
3. **Custom Media** — Now playing metadata (artist — track) when music playing
4. **System Tray** — Network, Bluetooth, Volume, Battery (percentage)
5. **Clock** — Custom format: `HH:mm  Day DD Mon`
6. **Power** — Logout/lock/shutdown menu (click)

---

## 5. Application Launcher — Wofi

### 5.1 Design

```
┌─────────────────────────────────────────────────┐
│  🔍  Search apps, commands, files…              │
├─────────────────────────────────────────────────┤
│  ◉  Firefox                                      │
│  ◉  Code - OSS                                   │
│  ◉  Terminal (kitty)                             │
│  ◉  Files (Thunar)                               │
│  ◉  Solus Settings                               │
│  ◉  Discord                                      │
│  ◉  Spotify                                      │
│  …                                               │
├─────────────────────────────────────────────────┤
│  9 results  (13 hidden)                          │
└─────────────────────────────────────────────────┘
```

**Specs:**
- Width: 600px
- Max visible items: 10
- Border radius: 16px
- Background: Surface with 25px blur, 90% opacity
- Entry: 50px height, 12px icon + text
- Selected: Primary color background, white text
- Keybind: `Super+Space` or `Super+D`

### 5.2 Categories

- Applications (default)
- File search (type `:f <filename>`)
- Calculator (type math expression)
- Web search (type `:w <query>`)

---

## 6. Notification System — Mako

### 6.1 Design

```
┌──────────────────────────────────────┐
│ 🔔 Discord                            │
│ @user: Hey, check this out            │
│ 2 min ago                [✕]         │
├──────────────────────────────────────┤
│ 🔋 Battery Low                        │
│ 15% remaining — plug in soon          │
│ [Dismiss] [Snooze 10m]               │
└──────────────────────────────────────┘
```

**Specs:**
- Position: Top-right
- Width: 360px
- Max notifications: 5 (grouped by app)
- Border radius: 12px
- Background: Surface with 25px blur, 90% opacity
- Border left: 3px accent color strip
- Font: Inter 13px (body), 12px (title)
- Dismiss: Click body, `Super+Shift+N` clears all
- Do Not Disturb: Toggle in Waybar

---

## 7. Lock Screen

### 7.1 Swaylock Configuration
- Background: Current wallpaper with 15px blur + 25% dark overlay
- Indicator: Card (320px wide, 16px radius, acrylic)
- Clock: 32px, bold, white
- Date: 14px, medium, 80% white
- User avatar: 64px circle with accent border
- Input: Inline password field
- Unlock: Enter key or fingerprint

---

## 8. Default Applications

| Purpose | Application | Reason |
|---------|-------------|--------|
| Terminal | Kitty (GPU-accelerated) | Best Wayland support, ligatures, split panes |
| File Manager | Thunar | Lightweight, GTK4, Wayland-native |
| Text Editor | VSCode / Helix | Developer preference |
| Browser | Firefox (Wayland) | Best Wayland support, privacy |
| Image Viewer | imv | Minimal, Wayland-native |
| PDF Reader | Zathura | Vim-like, minimal |
| Music | Spotify / mpd + ncmpcpp | Choice of streaming or local |
| Screenshot | grim + slurp | Wayland-native, composable |

---

## 9. Keybind Reference

### 9.1 Window Management

| Keybind | Action |
|---------|--------|
| `Super+Enter` | Open terminal (kitty) |
| `Super+Q` | Close focused window |
| `Super+D` / `Super+Space` | Application launcher (wofi) |
| `Super+F` | Toggle fullscreen |
| `Super+Shift+F` | Toggle float |
| `Super+J` | Focus next window |
| `Super+K` | Focus previous window |
| `Super+Tab` | Cycle to next workspace |
| `Super+Shift+Tab` | Cycle to previous workspace |
| `Super+1-6` | Switch to workspace 1-6 |
| `Super+Shift+1-6` | Move window to workspace 1-6 |
| `Super+H` | Resize window left (master ratio) |
| `Super+L` | Resize window right (master ratio) |

### 9.2 Layout Controls

| Keybind | Action |
|---------|--------|
| `Super+Ctrl+M` | Master layout |
| `Super+Ctrl+D` | Dwindle layout |
| `Super+Ctrl+C` | Center layout |
| `Super+Ctrl+F` | Float all |
| `Super+Shift+Space` | Toggle floating for focused window |

### 9.3 System

| Keybind | Action |
|---------|--------|
| `Super+Escape` | Lock screen |
| `Super+Shift+E` | Logout menu (wofi power menu) |
| `Super+Shift+S` | Screenshot region (grim + slurp) |
| `Super+PrtSc` | Screenshot full screen |
| `Super+V` | Clipboard manager (cliphist) |
| `Super+N` | Notifications toggle |
| `Super+Shift+N` | Clear all notifications |
| `Print` | Screenshot region (immediate) |

---

## 10. Screen Edges & Hot Corners

| Corner | Action |
|--------|--------|
| Top-left | Open overview (workspace grid) |
| Top-right | Notification center |
| Bottom-left | Show desktop |
| Bottom-right | Application launcher |

---

## 11. OOBE (First Boot)

1. **Welcome** — Language, keyboard layout
2. **Network** — Wi-Fi or Ethernet connection
3. **Account** — Create user + password
4. **Desktop Style** — Choose between "Tiling" (default) or "Floating" (beginner mode)
5. **Color Generation** — Pick wallpaper for pywal palette generation
6. **Keybinding Tour** — Interactive keybind learning mini-app
7. **Done** — "Welcome to Solus Hyprland"

---

## 12. Accessibility

- **Sticky Keys** via `keyd`
- **Font scaling** in kitty configuration
- **High contrast mode** toggles border-only window decorations
- **Reduce motion** disables all animations (set animation duration to 0)
- **Screen reader:** Orca (pre-configured keybind: `Super+Alt+S`)
- **On-screen keyboard:** wvkbd (auto-show on input focus)

---

## Appendix A: Package Dependencies

```
hyprland
waybar
wofi
mako
kitty
thunar
swaylock-effects
swayidle
grim
slurp
cliphist
wl-clipboard
hyprpicker
pywal
networkmanager-dmenu
brightnessctl
pavucontrol
polkit-gnome
xdg-desktop-portal-hyprland
```

---

*Design Language Version: 1.0.0*  
*Last Updated: 2026-07-04*  
*Maintainer: Solus Desktop Team*
