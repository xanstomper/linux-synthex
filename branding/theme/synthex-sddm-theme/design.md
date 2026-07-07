# Synthex SDDM Theme — Design Specification

> Version 1.0 | July 2026  
> Part of the Linux Synthex Brand Identity

---

## 1. Overview

The Synthex SDDM login theme provides a branded, modern lock/login screen consistent with the Synthex identity. Dark, polished, with a subtle animated background gradient.

---

## 2. Visual Design

### 2.1 Layout

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│                                                       │
│                                                       │
│                    Synthex Icon Mark                     │
│                    (64×64, amber glow)                 │
│                                                       │
│                    Welcome back.                       │
│                                                       │
│                    ┌─────────────────┐                 │
│                    │  username        │                 │
│                    └─────────────────┘                 │
│                                                       │
│                    ┌─────────────────┐                 │
│                    │  ••••••••••••   │                 │
│                    └─────────────────┘                 │
│                                                       │
│                    [◉  Log In]                        │
│                                                       │
│            ┌──────┐  ┌──────┐  ┌──────┐               │
│            │Plasma│  │Hyprld│  │GNOME │               │
│            └──────┘  └──────┘  └──────┘               │
│                 Desktop session selector                │
│                                                       │
│            [Suspend] [Restart] [Shutdown]              │
│                                                       │
│                        v1.0                            │
└─────────────────────────────────────────────────────┘
```

### 2.2 Colour Scheme

| Element              | Hex       | Usage                    |
|----------------------|-----------|--------------------------|
| Background           | `#1A1A2E` | Full-screen background   |
| Card background      | `#16213E` | Login form container     |
| Card border          | `#0F3460` | Form border              |
| Input background     | `#0F3460` | Username/password fields |
| Input text           | `#E8E8F0` | Input text               |
| Input placeholder    | `#707090` | Placeholder text         |
| Input focus border   | `#FFB300` | Active input border      |
| Button bg            | `#FFB300` | Login button             |
| Button text          | `#1A1A2E` | Login button text        |
| Button hover bg      | `#FFC107` | Hover state              |
| Session pill         | `#0F3460` | Session selector pill    |
| Session pill active  | `#FFB300` | Active session pill      |
| Power icon           | `#C0C0D0` | Suspend/restart/shutdown |
| Power icon hover     | `#FFB300` | Hover state              |

### 2.3 Typography

| Element           | Font              | Size  | Weight   |
|-------------------|-------------------|-------|----------|
| Greeting          | Inter Light       | 28px  | 300      |
| Username display  | Inter Semi-Bold   | 20px  | 600      |
| Input fields      | Inter Regular     | 16px  | 400      |
| Login button      | Inter Semi-Bold   | 16px  | 600      |
| Session pill      | Inter Medium      | 12px  | 500      |
| Version text      | JetBrains Mono    | 10px  | 400      |

### 2.4 Dimensions

| Element              | Size            |
|----------------------|-----------------|
| Card width           | 380px           |
| Card padding         | 32px            |
| Card radius          | 12px            |
| Input height         | 44px            |
| Input radius         | 8px             |
| Button height        | 44px            |
| Icon mark            | 64×64px         |
| Icon top margin      | 25% from top    |

---

## 3. Animation & Effects

### 3.1 Background
- **Animated gradient**: Slow horizontal sweep (12-second loop)
  - Start: `#1A1A2E` left, `#16213E` right
  - Mid: `#16213E` left, `#1A1A2E` right
  - End: returns to start
- Implementation: CSS keyframes or QML `PropertyAnimation`

### 3.2 Icon Glow
- The Synthex icon has a subtle pulsing amber glow
- Cycle: 4-second sine wave
- Opacity: 0.6 → 1.0 → 0.6

### 3.3 Input Focus Transition
- Border colour transition: 200ms ease-in-out
- Placeholder slides up on focus (floating label style)

### 3.4 Button Hover
- Background lightens slightly (`#FFB300` → `#FFC107`)
- Shadow deepens (y-offset increases 2px)

---

## 4. Background Image Options

The SDDM theme supports multiple background modes:

| Mode        | Description                            |
|-------------|----------------------------------------|
| Gradient    | Animated amber-blue dark gradient      |
| Wallpaper   | Static Synthex branded wallpaper image   |
| Blur        | User-selected image with 20px blur     |
| Custom      | Admin-specified background image       |

Default mode: **Gradient** (no external image required).

---

## 5. Session Switching

The session selector displays edition pills:

| Session     | Pill Colour | Hex       |
|-------------|-------------|-----------|
| Synthex Plasma| Amber       | `#FFB300` |
| Synthex Hyprland| Purple   | `#6A1B9A` |
| Synthex GNOME | Teal        | `#00897B` |

---

## 6. Components

### 6.1 QML File Structure

```
synthex-sddm-theme/
├── design.md                   # This design specification
├── metadata.desktop            # SDDM theme metadata
├── Main.qml                    # Main QML entry point
├── LoginForm.qml               # Login form component
├── SessionSelector.qml         # Desktop session picker
├── PowerButtons.qml            # Suspend/restart/shutdown
├── UserAvatar.qml              # User avatar display
├── ClockDisplay.qml            # Clock/date widget
└── components/
    ├── SynthexButton.qml         # Styled button component
    ├── SynthexInput.qml          # Styled text input
    └── SynthexIcon.qml           # Synthex icon mark component
```

### 6.2 metadata.desktop

```
[Desktop Entry]
Type=X-SDDM-Theme
Name=Synthex SDDM
Name[de]=Synthex SDDM
Name[es]=Synthex SDDM
Name[fr]=Synthex SDDM
Name[it]=Synthex SDDM
Name[pt]=Synthex SDDM
Name[ru]=Synthex SDDM
Name[zh_CN]=Synthex SDDM
Comment=Synthex-branded SDDM login theme with amber accents
Comment[de]=Synthex-SDDM-Anmeldetheme mit bernsteinfarbenen Akzenten
Comment[es]=Tema de inicio de sesión SDDM con la marca Synthex y acentos ámbar
Comment[fr]=Thème de connexion SDDM de la marque Synthex avec accents ambrés
Comment[it]=Tema di accesso SDDM con marchio Synthex e accenti ambrati
Comment[pt]=Tema de login SDDM com a marca Synthex e acentos âmbar
Comment[ru]=Тема входа SDDM с брендом Synthex и янтарными акцентами
Comment[zh_CN]=Synthex品牌SDDM登录主题，带有琥珀色强调色
X-KDE-PluginInfo-Author=Linux Synthex Project
X-KDE-PluginInfo-Email=brand@synthex-os.org
X-KDE-PluginInfo-Version=1.0
X-KDE-PluginInfo-Website=https://synthex-os.org
X-KDE-PluginInfo-License=GPL-3.0+
```

---

## 7. Installation

```bash
# Copy theme to SDDM themes directory
sudo cp -r synthex-sddm-theme /usr/share/sddm/themes/synthex

# Edit /etc/sddm.conf or create /etc/sddm.conf.d/synthex.conf:
# [Theme]
# Current=synthex

# Restart SDDM
sudo systemctl restart sddm
```

---

## 8. Dependencies

- **SDDM 0.19+**
- **Qt 5.15+ / Qt 6.x** with QML support
- **QtGraphicalEffects** for blur and glow

---

## 9. Accessibility

- Tab navigation through all elements
- Visual focus indicators (amber border on focused elements)
- High-contrast colour pairs pass WCAG AA
- On-screen keyboard support (optional)
- Screen reader support via proper QML accessibility attributes

---

*© 2026 Linux Synthex Project. Licensed under GPL-3.0+.*
