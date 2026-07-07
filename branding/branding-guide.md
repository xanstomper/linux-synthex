# Linux Synthex — Brand Identity Guidelines

> Version 1.0 | July 2026  
> "Illuminate Your Desktop"

---

## 1. Brand Overview

### 1.1 Brand Name
**Synthex**  
Latin for *"alone/only"* — recontextualised to represent **"Solar"**: radiant, powerful, self-contained.  
The name evokes the sun as a self-luminous, self-sustaining source of energy — exactly what Synthex aims to be for the desktop Linux ecosystem.

### 1.2 Tagline
**"Illuminate Your Desktop"**  
Short, confident, and evocative. The tagline speaks to both the visual radiance of the brand and the clarity Synthex brings to the user experience.

### 1.3 Brand Promise
*Synthex delivers a refined, self-contained Linux desktop experience that is powerful enough for professionals, beautiful enough for creatives, and approachable enough for everyone.*

---

## 2. Brand Architecture

```
Linux Synthex (Umbrella)
├── Synthex Plasma    — Flagship desktop (KDE Plasma) — full-featured, polished
├── Synthex Hyprland  — Power-user edition (Hyprland WM) — tiling, minimal, fast
└── Synthex GNOME     — Minimalist edition (GNOME) — clean, modern, accessible
```

Each edition shares the core Synthex brand equity while expressing its own personality through the accent colour system (see §3.2).

| Edition     | Primary Accent    | Hex       | Personality              |
|-------------|-------------------|-----------|--------------------------|
| Synthex       | Amber (default)   | `#FFB300` | Warm, energetic, premium |
| Synthex Plasma| Amber             | `#FFB300` | Polished, capable         |
| Synthex Hyprland| Deep Purple     | `#6A1B9A` | Power, sophistication     |
| Synthex GNOME | Teal              | `#00897B` | Clean, calm, accessible   |

---

## 3. Colour Palette

### 3.1 Primary Palette

| Token            | Hex       | Preview   | Usage                        |
|------------------|-----------|-----------|------------------------------|
| Synthex Amber      | `#FFB300` | 🟡 Amber | Primary brand colour, CTAs, highlights |
| Synthex Deep Blue  | `#1565C0` | 🔵 Blue  | Trust element, links, secondary UI  |
| Synthex Deep Purple| `#6A1B9A` | 🟣 Purple| Accent gradient partner, Hyprland   |
| Synthex Teal       | `#00897B` | 🌊 Teal  | GNOME edition accent                |

### 3.2 Accent Gradient
The signature Synthex gradient used in hero sections, loading screens, and premium surfaces:

```
Amber (#FFB300) → Deep Purple (#6A1B9A)
Direction: 135° (top-left to bottom-right)
```

### 3.3 Dark Theme

| Token        | Hex       | Usage                |
|--------------|-----------|----------------------|
| Base         | `#1A1A2E` | Main background      |
| Surface      | `#16213E` | Cards, sidebars      |
| Elevated     | `#0F3460` | Modals, popovers     |
| On-Base      | `#E8E8F0` | Primary text         |
| On-Surface   | `#C0C0D0` | Secondary text       |
| Muted        | `#707090` | Disabled, captions   |

### 3.4 Light Theme

| Token        | Hex       | Usage                |
|--------------|-----------|----------------------|
| Base         | `#FAFAFA` | Main background      |
| Surface      | `#F5F5F5` | Cards, sidebars      |
| Elevated     | `#E0E0E0` | Modals, popovers     |
| On-Base      | `#212121` | Primary text         |
| On-Surface   | `#616161` | Secondary text       |
| Muted        | `#9E9E9E` | Disabled, captions   |

### 3.5 Semantic Palette

| Purpose      | Hex       | Usage                  |
|--------------|-----------|------------------------|
| Success      | `#4CAF50` | Confirmations, good    |
| Error        | `#F44336` | Destructive actions    |
| Info         | `#2196F3` | Notifications          |
| Warning      | `#FF9800` | Caution states         |

### 3.6 Usage Rules
- **Amber** must dominate — it is the primary differentiator.
- **Deep Blue** is the secondary; never replace Amber with Blue as primary.
- **Gradient** (Amber → Purple) is reserved for hero/splash/premium surfaces only.
- **Dark theme** is the *default* — light theme is opt-in.
- Semantic colours must never substitute primary brand colours.

---

## 4. Typography

### 4.1 Primary — Inter
```
Family: Inter
Weights: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-Bold), 700 (Bold)
Styles: Normal, Italic
Usage: UI text, headings, body copy, marketing materials
License: SIL Open Font License
Source: https://rsms.me/inter/
```

### 4.2 Secondary — JetBrains Mono
```
Family: JetBrains Mono
Weights: 400 (Regular), 500 (Medium), 700 (Bold)
Styles: Normal, Italic (cursive variants)
Usage: Code blocks, terminal, technical documentation
License: SIL Open Font License
Source: https://www.jetbrains.com/lp/mono/
```

### 4.3 System Fallback — Noto Sans
```
Family: Noto Sans
Usage: When primary fonts are not installed (live ISO, minimal installs)
License: SIL Open Font License
Source: https://fonts.google.com/noto
```

### 4.4 Type Scale

| Level      | Size   | Weight | Line Height | Font          |
|------------|--------|--------|-------------|---------------|
| Display    | 48px   | 700    | 1.1         | Inter         |
| H1         | 36px   | 700    | 1.2         | Inter         |
| H2         | 28px   | 600    | 1.25        | Inter         |
| H3         | 22px   | 600    | 1.3         | Inter         |
| H4         | 18px   | 500    | 1.35        | Inter         |
| Body       | 16px   | 400    | 1.5         | Inter         |
| Small      | 14px   | 400    | 1.5         | Inter         |
| Caption    | 12px   | 400    | 1.4         | Inter         |
| Code       | 14px   | 400    | 1.5         | JetBrains Mono|

### 4.5 Typography Rules
- Never use bold weights for full paragraphs — reserve for headings and emphasis.
- Code blocks must use JetBrains Mono at 14px.
- Minimum body text size: 14px (small), 16px (preferred).
- Line length: 60–80 characters per line for optimal readability.

---

## 5. Logo Specifications

### 5.1 Logo Marks

Three logo variants exist:

| Variant     | Description                           | Primary Use            |
|-------------|---------------------------------------|------------------------|
| Icon Mark   | Stylised sun/gear/hexagon hybrid      | Favicon, app icon, avatar |
| Wordmark    | "Synthex" in custom wordmark typography | Headers, banners       |
| Lockup      | Icon + Wordmark combined              | Official brand representation |

### 5.2 Icon Mark Design
The Synthex icon is a **stylised sun transitioning into a hexagonal gear** — representing the warmth of the open-source community (sun) combined with the precision of engineering (gear).

- **Geometry**: Built on a 24×24 unit grid, centred in a 32×32 artboard.
- **Sun rays**: 8 primary rays radiating outward from the core.
- **Gear teeth**: The outer ring is formed by 8 gear-like notches.
- **Core**: A central hexagon representing stability and community.
- **Open circle centre**: Symbolises the open-source nature of the OS.

### 5.3 Logo Clear Space
Minimum clear space = 1× the height of the wordmark "S" on all sides.  
No other elements (text, graphics, edges) may intrude into this space.

### 5.4 Logo Minimum Sizes
- **Lockup** (digital): 64px wide minimum  
- **Lockup** (print): 0.5 in / 12 mm wide  
- **Icon Mark**: 24px / 6 mm minimum

### 5.5 Prohibited Uses
- ❌ Do not stretch or distort the logo
- ❌ Do not change the logo colours outside the approved palette
- ❌ Do not place the logo on busy backgrounds without sufficient contrast
- ❌ Do not rotate the icon mark independently of the wordmark
- ❌ Do not replace "Synthex" type with a different font
- ❌ Do not add outlines, shadows, or effects not in the original artwork
- ❌ Do not rearrange elements of the lockup

---

## 6. Icon Style — Glassmorphism 3D

| Property            | Value                          |
|---------------------|--------------------------------|
| Style               | Glassmorphism + 3D isometric   |
| Background          | Dark gradient (see §3.3)       |
| Glass fill          | `rgba(255, 255, 255, 0.08)`    |
| Glass border        | `rgba(255, 255, 255, 0.15)`, 1px   |
| Backdrop blur       | 12–16px                        |
| Shadow              | Soft drop shadow, y-offset 4px |
| Accent              | Colour-coded by edition        |
| Icon perspective    | Isometric (30° tilt)           |
| Highlight           | Top-left corner white gleam    |

### 6.1 Application Icons
All first-party Synthex applications (Synthex Store, Synthex Settings, Synthex Welcome) must follow the glassmorphism 3D style with the edition-appropriate accent colour.

---

## 7. Photography & Imagery Style

### 7.1 Product Shots
- **Style**: Dark themed, gradient-lit with amber/purple fills
- **Lighting**: Key light from upper left (warm), fill light from lower right (cool purple)
- **Background**: Deep dark blue-to-black gradient (see §3.3)
- **Post-processing**: Clean, minimal retouching; subtle glow effects
- **Devices**: Always show Synthex desktop running in context (laptop, desktop, tablet)

### 7.2 Abstract / Hero Imagery
- Use the Synthex gradient (Amber → Purple) as a primary background treatment
- Overlay geometric patterns derived from the hexagon/gear logo geometry
- Incorporate subtle noise/grain texture for depth
- Never use stock photography without heavy colour grading toward the Synthex palette

---

## 8. Voice & Tone

### 8.1 Brand Voice
| Attribute     | Description                                   |
|---------------|-----------------------------------------------|
| Confident     | We know what we're building and why.          |
| Warm          | Community-first, approachable, inclusive.     |
| Professional  | Polished documentation, clean communication.  |
| Capable       | Synthex handles real work — we show, not tell.  |

### 8.2 Tone by Context

| Context       | Tone                                        |
|---------------|----------------------------------------------|
| Marketing     | Aspirational, energetic, benefit-focused     |
| Documentation | Clear, precise, patient, well-structured     |
| Community     | Warm, collaborative, celebratory             |
| Error/Alert   | Direct, helpful, minimising blame            |
| Social Media  | Short, punchy, visually-led                  |

### 8.3 Language Guidelines
- Use active voice: *"Synthex delivers…"* not *"…is delivered by Synthex"*
- Prefer contractions: *"don't"*, *"you'll"*, *"it's"* — feels approachable
- Avoid superlatives: *"best"*, *"perfect"*, *"ultimate"* — let the work speak
- Use inclusive language: *"everyone"*, *"you"*, *"we"* — not *"guys"*, *"power users"* as default
- Keep sentences under 25 words where possible

---

## 9. Application to Touchpoints

### 9.1 Website
- Dark theme default with amber CTAs
- Hero section uses the signature gradient
- Download buttons: Amber (#FFB300) with Inter Semi-Bold

### 9.2 Desktop (OS)
- **GRUB**: Dark background with Synthex logo and amber accents
- **Plymouth**: Boot splash with animated Synthex icon and gradient
- **SDDM/KDM**: Login screen with Synthex branding and edition colour
- **Plasma Theme**: Synthex colour scheme, custom window decorations
- **Wallpapers**: Dark gradient-based with subtle brand patterns

### 9.3 Social Media
- Profile pictures: Synthex icon mark on dark circle
- Banner: Synthex lockup on gradient hero with tagline
- Post style: Dark cards with amber CTAs, Inter typeface

### 9.4 Merchandise
- T-shirts: Front = icon mark (small, left chest), Back = lockup (large, centred)
- Stickers: Icon mark only, die-cut, amber on dark or white
- Laptop skins: Dark with Synthex gradient strip

---

## 10. Brand Governance

### 10.1 Review Process
All external-facing materials must be reviewed against these guidelines before publishing. Major deviations require brand team approval.

### 10.2 Versioning
This document follows semantic versioning. Updates that change brand colours, logo geometry, or typography are major version bumps.

### 10.3 Questions
For brand usage questions, contact: **brand@synthex-os.org**

---

*© 2026 Linux Synthex Project. All rights reserved.*  
*"Synthex" and the Synthex logo are trademarks of the Linux Synthex Project.*  
*"Illuminate Your Desktop" is a tagline of the Linux Synthex Project.*
