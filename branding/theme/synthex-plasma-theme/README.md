# Synthex Plasma Theme

A modern, dark-themed KDE Plasma desktop theme built for **Synthex**, with warm amber accents and deep blue/purple undertones.

---

## Directory Structure

```
synthex-plasma-theme/
├── metadata.desktop          # Theme metadata (KWin/Style)
├── colors                    # KDE color scheme (Synthex)
├── README.md                 # This file
│
├── aurorae/                  # Window decorations (Aurorae)
│   └── Synthex/                # Synthex window decoration theme
│       ├── metadata.desktop
│       ├── Synthex.svg         # Decoration SVG
│       └── decoration.svg    # Button layout
│
├── plasma/                   # Plasma theme components
│   ├── dialogs/              # Dialog backgrounds
│   ├── icons/                # Plasma-specific icons
│   ├── widgets/              # Widget styling SVGs
│   ├── panels/               # Panel backgrounds
│   ├── background.svg        # Desktop background
│   └── metadata.desktop      # Plasma theme metadata
│
├── look-and-feel/            # Look-and-Feel package
│   └── org.synthex.plasma.desktop/
│       ├── metadata.desktop
│       └── contents/
│           ├── defaults/     # Default configuration
│           └── splash/       # Splash screen
│
└── wallpaper/                # Synthex branded wallpapers
    └── synthex-*.png
```

## Installation

### System-wide
```bash
sudo cp -r synthex-plasma-theme /usr/share/plasma/desktoptheme/synthex-plasma
sudo cp colors /usr/share/color-schemes/Synthex.colors
```

### User-only
```bash
mkdir -p ~/.local/share/plasma/desktoptheme/
cp -r synthex-plasma-theme ~/.local/share/plasma/desktoptheme/synthex-plasma
mkdir -p ~/.local/share/color-schemes/
cp colors ~/.local/share/color-schemes/Synthex.colors
```

### Activate
1. Open **System Settings → Appearance → Plasma Style**
2. Select **Synthex Plasma**
3. Open **System Settings → Colors**
4. Select **Synthex** color scheme
5. (Optional) Apply Synthex window decorations and SDDM theme

## Theme Architecture

This theme follows the standard KDE Plasma theme structure for Plasma 6.x:

| Component            | Location                        | Description                      |
|----------------------|---------------------------------|----------------------------------|
| Plasma style         | `plasma/`                       | Panel, widget, dialog styling    |
| Color scheme         | `colors`                        | Complete KDE color palette       |
| Window decorations   | `aurorae/Synthex/`                | Titlebar buttons, borders        |
| Look-and-Feel        | `look-and-feel/`                | Splash screen, cursor, sounds    |
| Wallpaper            | `wallpaper/`                    | Default desktop backgrounds      |

## Color Palette

| Token             | Hex       | Role                            |
|-------------------|-----------|---------------------------------|
| Base              | `#1A1A2E` | Main background                 |
| Surface           | `#16213E` | Cards, panels, sidebars         |
| Elevated          | `#0F3460` | Modals, popovers, tooltips      |
| Synthex Amber       | `#FFB300` | Accent, highlights, selection   |
| Synthex Deep Blue   | `#1565C0` | Links, secondary elements       |
| Text Primary      | `#E8E8F0` | Main text                       |
| Text Secondary    | `#C0C0D0` | Supporting text                 |
| Text Muted        | `#707090` | Disabled, placeholder           |

## Dependencies

- **KDE Plasma 6.x** (tested on 6.0+)
- **KWin** window manager
- **Aurorae** window decoration engine (for Synthex window decorations)

## Branding

This theme is part of the Synthex brand ecosystem. See the [Brand Identity Guidelines](../../branding-guide.md) for full details.

---

*© 2026 Linux Synthex Project. Licensed under GPL-3.0+.*
