# Solus Plasma Theme

A modern, dark-themed KDE Plasma desktop theme built for **Solus**, with warm amber accents and deep blue/purple undertones.

---

## Directory Structure

```
solus-plasma-theme/
├── metadata.desktop          # Theme metadata (KWin/Style)
├── colors                    # KDE color scheme (Solus)
├── README.md                 # This file
│
├── aurorae/                  # Window decorations (Aurorae)
│   └── Solus/                # Solus window decoration theme
│       ├── metadata.desktop
│       ├── Solus.svg         # Decoration SVG
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
│   └── org.solus.plasma.desktop/
│       ├── metadata.desktop
│       └── contents/
│           ├── defaults/     # Default configuration
│           └── splash/       # Splash screen
│
└── wallpaper/                # Solus branded wallpapers
    └── solus-*.png
```

## Installation

### System-wide
```bash
sudo cp -r solus-plasma-theme /usr/share/plasma/desktoptheme/solus-plasma
sudo cp colors /usr/share/color-schemes/Solus.colors
```

### User-only
```bash
mkdir -p ~/.local/share/plasma/desktoptheme/
cp -r solus-plasma-theme ~/.local/share/plasma/desktoptheme/solus-plasma
mkdir -p ~/.local/share/color-schemes/
cp colors ~/.local/share/color-schemes/Solus.colors
```

### Activate
1. Open **System Settings → Appearance → Plasma Style**
2. Select **Solus Plasma**
3. Open **System Settings → Colors**
4. Select **Solus** color scheme
5. (Optional) Apply Solus window decorations and SDDM theme

## Theme Architecture

This theme follows the standard KDE Plasma theme structure for Plasma 6.x:

| Component            | Location                        | Description                      |
|----------------------|---------------------------------|----------------------------------|
| Plasma style         | `plasma/`                       | Panel, widget, dialog styling    |
| Color scheme         | `colors`                        | Complete KDE color palette       |
| Window decorations   | `aurorae/Solus/`                | Titlebar buttons, borders        |
| Look-and-Feel        | `look-and-feel/`                | Splash screen, cursor, sounds    |
| Wallpaper            | `wallpaper/`                    | Default desktop backgrounds      |

## Color Palette

| Token             | Hex       | Role                            |
|-------------------|-----------|---------------------------------|
| Base              | `#1A1A2E` | Main background                 |
| Surface           | `#16213E` | Cards, panels, sidebars         |
| Elevated          | `#0F3460` | Modals, popovers, tooltips      |
| Solus Amber       | `#FFB300` | Accent, highlights, selection   |
| Solus Deep Blue   | `#1565C0` | Links, secondary elements       |
| Text Primary      | `#E8E8F0` | Main text                       |
| Text Secondary    | `#C0C0D0` | Supporting text                 |
| Text Muted        | `#707090` | Disabled, placeholder           |

## Dependencies

- **KDE Plasma 6.x** (tested on 6.0+)
- **KWin** window manager
- **Aurorae** window decoration engine (for Solus window decorations)

## Branding

This theme is part of the Solus brand ecosystem. See the [Brand Identity Guidelines](../../branding-guide.md) for full details.

---

*© 2026 Linux Solus Project. Licensed under GPL-3.0+.*
